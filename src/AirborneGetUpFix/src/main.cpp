#include "pch.h"

#include <chrono>
#include <deque>
#include <mutex>
#include <unordered_map>

// An actor knocked into the air (Seismic Stomp under its SlowTime, but any ragdoll) and hit while still flying is told
// to get up mid-air: ~55 ms after the hit the engine sends GetUpBegin (knock state -> kQueued), the graph's 0.5 s timer
// answers GetUpStart, and the body turns animation-driven (knock -> kGetUp). With no ragdoll and no character
// controller nothing pulls it down, so it hangs rigid, the get-up never completes (no GetUpEnd /
// AddCharacterControllerToWorld) and the actor stays stuck alive. Measured with ZenRagdollTrace, see
// arch-docs/patches/AirborneGetUpFix.md.
//
// Fix: every non-player actor in ragdoll state keeps a 1 s (wall clock) history of its pelvis bone's world z. A GetUpBegin that
// arrives while that history still spans more than kSettleRange units is held (reported to the caller as accepted, so
// the engine just waits in kQueued) and sent from Actor::Update once the body has settled, or after kTimeout.
// A held event is dropped if the actor dies or leaves ragdoll state on its own. Actors without a pelvis bone pass through.
// Time is the wall clock, not Update's float argument: 1.0.0 summed that argument and no held event was ever released
// (pelvis still to 0.1 units for 10 s, no timeout either), so it is not a usable frame delta for these actors.
// Under SlowTime (30%) a 1 s window is 0.3 s of game time; a body near the top of its arc still moves ~8 units in it.
//
// 1.1.0: a stagger reaching a ragdolled actor freezes it the same way. An Awoken Lost Archer (draugr skeleton graph) got
// staggerStart 0.1 s after Ragdoll; the graph accepted it, left its ragdoll state for the stagger state
// (animation-driven), and the still-ragdolled body hung at a frozen position for 17 s+. The released GetUpBegin was then
// refused (no ragdoll state left to take it). An earlier Wood Elemental's get-up was cut short by a stagger in the same
// way. So while an actor is ragdolled or not in the normal knock state, stagger / recoil / bleed-out start events are
// refused (reported as not accepted, as the graph itself does for events it has no transition for).
// 1.1.1: dead actors too. A Fleshless Lost Archer and Warrior killed by Seismic Stomp itself got Ragdoll already dead,
// then staggerStart 0.08-0.13 s later; 1.1.0 skipped the dead, so the graph took it and the corpse hung stiff mid-air.
// 1.2.0 (2026-11-01): enemies launched by Seismic Stomp lay on the ground for ~4 s (the body kept sliding, so the 1 s /
// 4-unit check failed), and Precision's physical swings passed over a body lying flat: players saw no damage after the
// first hit (ZenRagdollTrace 1.2.0: no player hit in knock state 5, hits again at 6). A held GetUpBegin is now also
// sent once the body has landed: kLandedDrop below its peak since the hold, then still to kLandedRange over kLandedWindow.
// Log: My Games/Skyrim Special Edition/SKSE/ZenAirborneGetUpFix.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 3, 1, 0 },
	.Name = "ZenAirborneGetUpFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	using Clock = std::chrono::steady_clock;

	constexpr auto  kWindow = std::chrono::milliseconds(1000);  // the settle check looks back this far
	constexpr float kSettleRange = 4.0f;                        // pelvis z may vary at most this much over the window
	constexpr auto  kTimeout = std::chrono::milliseconds(8000);  // a held GetUpBegin is sent after this long regardless
	// 1.2.0: landed = dropped at least kLandedDrop below the highest pelvis z seen since the hold began, then within
	// kLandedRange over the last kLandedWindow. Near the top of the arc it has not dropped yet, so the short window is safe there
	constexpr auto  kLandedWindow = std::chrono::milliseconds(400);
	constexpr float kLandedRange = 6.0f;
	constexpr float kLandedDrop = 24.0f;

	struct Sample
	{
		Clock::time_point at;
		float             z;
	};

	struct Ragdoll
	{
		std::deque<Sample> history;
		bool               held{ false };
		Clock::time_point  heldAt{};
		float              heldAtZ{ 0.0f };
		float              peakZ{ 0.0f };      // highest pelvis z since the hold began (1.2.0)
		float              lastDelta{ 0.0f };  // Update's float argument, logged only
	};

	double Seconds(Clock::duration a_d)
	{
		return std::chrono::duration<double>(a_d).count();
	}

	std::mutex                              g_lock;
	std::unordered_map<RE::FormID, Ragdoll> g_ragdolls;
	thread_local bool                       g_sending = false;
	const RE::BSFixedString                 kGetUpBegin{ "GetUpBegin" };
	constexpr std::array                    kBlockedWhileDown{ "stagger"sv, "recoil"sv, "bleedoutstart"sv };  // prefixes, any case

	bool BlockedWhileDown(std::string_view a_name)
	{
		std::string lower{ a_name };
		std::ranges::transform(lower, lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return std::ranges::any_of(kBlockedWhileDown, [&](std::string_view p) { return lower.starts_with(p); });
	}

	std::optional<float> PelvisZ(RE::Actor* a_actor)
	{
		if (auto* root = a_actor->Get3D()) {
			if (auto* pelvis = root->GetObjectByName("NPC Pelvis [Pelv]"sv)) {
				return pelvis->world.translate.z;
			}
		}
		return std::nullopt;
	}

	bool Settled(const Ragdoll& a_ragdoll)
	{
		if (a_ragdoll.history.empty() || a_ragdoll.history.back().at - a_ragdoll.history.front().at < kWindow) {
			return false;
		}
		const auto [lo, hi] = std::ranges::minmax(a_ragdoll.history | std::views::transform(&Sample::z));
		return hi - lo <= kSettleRange;
	}

	bool Landed(const Ragdoll& a_ragdoll)
	{
		if (!a_ragdoll.held || a_ragdoll.history.empty()) {
			return false;
		}
		const auto  now = a_ragdoll.history.back().at;
		const float z = a_ragdoll.history.back().z;
		if (now - a_ragdoll.history.front().at < kLandedWindow || a_ragdoll.peakZ - z < kLandedDrop) {
			return false;
		}
		float lo = z, hi = z;
		for (auto& s : a_ragdoll.history) {
			if (now - s.at <= kLandedWindow) {
				lo = std::min(lo, s.z);
				hi = std::max(hi, s.z);
			}
		}
		return hi - lo <= kLandedRange;
	}

	struct NotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			if (!g_sending && a_eventName.c_str() && BlockedWhileDown(a_eventName.c_str())) {
				if (auto* actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>()) {   // dead ones too (1.1.1)
					const auto knock = actor->AsActorState()->GetKnockState();
					if (actor->IsInRagdollState() || knock != RE::KNOCK_STATE_ENUM::kNormal) {
						SKSE::log::info("{:08X} '{}': {} refused while down (knock {}{})", actor->GetFormID(), actor->GetName(),
							a_eventName.c_str(), std::to_underlying(knock), actor->IsDead() ? ", dead" : "");
						return false;
					}
				}
			}
			if (!g_sending && a_eventName == kGetUpBegin) {
				if (auto* actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>(); actor && !actor->IsDead()) {
					std::scoped_lock l{ g_lock };
					auto it = g_ragdolls.find(actor->GetFormID());
					if (it != g_ragdolls.end() && !it->second.history.empty() && !Settled(it->second)) {
						auto& r = it->second;
						if (!r.held) {
							r.held = true;
							r.heldAt = Clock::now();
							r.heldAtZ = r.history.back().z;
							r.peakZ = std::ranges::max(r.history | std::views::transform(&Sample::z));
							SKSE::log::info("{:08X} '{}': GetUpBegin held, still moving (pelvis z {:.0f}, Update arg {})",
								actor->GetFormID(), actor->GetName(), r.heldAtZ, r.lastDelta);
						}
						return true;
					}
				}
			}
			return func(a_this, a_eventName);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct CharacterUpdate
	{
		static void thunk(RE::Character* a_this, float a_delta)
		{
			func(a_this, a_delta);

			const bool ragdoll = a_this->IsInRagdollState();
			const bool dead = a_this->IsDead();
			bool       send = false;
			{
				std::scoped_lock l{ g_lock };
				auto it = g_ragdolls.find(a_this->GetFormID());
				if (!ragdoll || dead) {
					if (it != g_ragdolls.end()) {
						if (it->second.held) {
							SKSE::log::info("{:08X} '{}': held GetUpBegin dropped ({})", a_this->GetFormID(), a_this->GetName(),
								dead ? "died" : "left ragdoll on its own");
						}
						g_ragdolls.erase(it);
					}
					return;
				}
				const auto z = PelvisZ(a_this);
				if (!z) {
					return;
				}
				if (it == g_ragdolls.end()) {
					it = g_ragdolls.emplace(a_this->GetFormID(), Ragdoll{}).first;
					SKSE::log::info("{:08X} '{}': ragdoll tracked (pelvis z {:.0f}, Update arg {})", a_this->GetFormID(),
						a_this->GetName(), *z, a_delta);
				}
				auto&      r = it->second;
				const auto now = Clock::now();
				r.lastDelta = a_delta;
				r.history.push_back({ now, *z });
				while (r.history.size() > 2 && now - r.history[1].at >= kWindow) {
					r.history.pop_front();  // keep exactly one sample at or beyond the window's start
				}
				if (r.held) {
					r.peakZ = std::max(r.peakZ, *z);
					const auto heldFor = now - r.heldAt;
					const bool settled = Settled(r);
					const bool landed = !settled && Landed(r);
					if (settled || landed || heldFor >= kTimeout) {
						SKSE::log::info("{:08X} '{}': GetUpBegin sent after {:.2f} s ({}), pelvis z {:.0f} -> {:.0f} (peak {:.0f})",
							a_this->GetFormID(), a_this->GetName(), Seconds(heldFor), settled ? "settled" : landed ? "landed" : "timeout",
							r.heldAtZ, *z, r.peakZ);
						r.held = false;
						send = true;
					}
				}
			}
			if (send) {
				g_sending = true;
				const bool accepted = a_this->NotifyAnimationGraph(kGetUpBegin);
				g_sending = false;
				if (!accepted) {
					SKSE::log::warn("{:08X} '{}': the graph refused the released GetUpBegin", a_this->GetFormID(), a_this->GetName());
				}
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// 1.3.0: the engine's hit processing (ID 38586) returns at once - no damage, no hit event - when the target's knock
	// state is kQueued (actorState1 & 0xE000000 == 0xA000000, read at +0x68). The first hit on a flying ragdoll queues a
	// get-up mid-air, so every later melee hit was lost until the actor stood (Seismic Stomp under SlowTime: 7 s on a
	// bear). For the melee path only (DealDamage, ID 38627 +0x4A8), an alive, ragdolled target in kQueued is shown as
	// kExplode - the flying state its hits worked in - for this one call, then put back if nothing else changed it.
	struct ProcessHit
	{
		static std::uintptr_t thunk(RE::Actor* a_target, void* a_hitData)
		{
			auto* state = a_target ? a_target->AsActorState() : nullptr;
			if (!state || state->actorState1.knockState != RE::KNOCK_STATE_ENUM::kQueued || a_target->IsDead() ||
				!a_target->IsInRagdollState()) {
				return func(a_target, a_hitData);
			}
			state->actorState1.knockState = RE::KNOCK_STATE_ENUM::kExplode;
			const auto result = func(a_target, a_hitData);
			if (state->actorState1.knockState == RE::KNOCK_STATE_ENUM::kExplode) {
				state->actorState1.knockState = RE::KNOCK_STATE_ENUM::kQueued;
			}
			static std::atomic<int> logged{ 0 };
			if (logged++ < 50) {
				SKSE::log::info("{:08X} '{}': melee hit let through while queued to get up (knock now {})", a_target->GetFormID(),
					a_target->GetName(), std::to_underlying(state->GetKnockState()));
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void InstallProcessHit()
	{
		const REL::Relocation<std::uintptr_t> site{ REL::ID(38627), 0x4A8 };
		const REL::Relocation<std::uintptr_t> target{ REL::ID(38586) };
		const auto* bytes = reinterpret_cast<const std::uint8_t*>(site.address());
		const auto  dest = site.address() + 5 + *reinterpret_cast<const std::int32_t*>(bytes + 1);
		auto module = [](std::uintptr_t a_addr) {
			HMODULE mod = nullptr;
			char    name[MAX_PATH]{};
			if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
					reinterpret_cast<LPCSTR>(a_addr), &mod) && mod) {
				GetModuleFileNameA(mod, name, MAX_PATH);
			}
			return std::string{ name };
		};
		// 1.3.1: another plugin already hooks this call (1.3.0 required the game's own target and so never installed);
		// any call is chained - ours runs first, then whatever was there, which ends in 38586
		if (bytes[0] != 0xE8) {
			SKSE::log::error("melee hit call at ID 38627 +0x4A8 is not a call ({:02X} {:02X} {:02X} {:02X} {:02X}, {}) - hits on "
							 "actors queued to get up stay blocked",
				bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], module(site.address()));
			return;
		}
		SKSE::AllocTrampoline(14);
		ProcessHit::func = SKSE::GetTrampoline().write_call<5>(site.address(), ProcessHit::thunk);
		SKSE::log::info("melee hit processing hooked (ID 38627 +0x4A8): the call led to {} ({}); hits reach ragdolled actors "
						"queued to get up",
			dest == target.address() ? "the game's 38586"s : std::format("{:X}", dest), module(dest));
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenAirborneGetUpFix 1.3.1 loading, runtime {}", REL::Module::get().version().string());

	// Character's vtables: [0] TESForm/Actor, [3] IAnimationGraphManagerHolder. The player (PlayerCharacter) is not touched.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::log::info("Character Update and NotifyAnimationGraph hooked; window {} ms, settle range {}, timeout {} ms",
		kWindow.count(), kSettleRange, kTimeout.count());
	// at kPostLoad, after every plugin's own load-time hooks (1.3.1)
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			InstallProcessHit();
		}
	});
	return true;
}
