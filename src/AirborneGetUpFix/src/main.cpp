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
// Log: My Games/Skyrim Special Edition/SKSE/ZenAirborneGetUpFix.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 1, 0 },
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
					const auto heldFor = now - r.heldAt;
					const bool settled = Settled(r);
					if (settled || heldFor >= kTimeout) {
						SKSE::log::info("{:08X} '{}': GetUpBegin sent after {:.2f} s ({}), pelvis z {:.0f} -> {:.0f}",
							a_this->GetFormID(), a_this->GetName(), Seconds(heldFor), settled ? "settled" : "timeout", r.heldAtZ, *z);
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
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenAirborneGetUpFix 1.1.1 loading, runtime {}", REL::Module::get().version().string());

	// Character's vtables: [0] TESForm/Actor, [3] IAnimationGraphManagerHolder. The player (PlayerCharacter) is not touched.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::log::info("Character Update and NotifyAnimationGraph hooked; window {} ms, settle range {}, timeout {} ms",
		kWindow.count(), kSettleRange, kTimeout.count());
	return true;
}
