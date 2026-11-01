#include "pch.h"

#include <chrono>
#include <mutex>
#include <unordered_map>

// Testing tool, not part of the list. Creatures (Lost One skeletons, Wood Elementals) knocked into the air sometimes
// hang there alive and rigid. The behaviour graphs alone did not explain it (see arch-docs/patches/CreatureRagdollFix.md),
// so this logs what actually happens, for every non-player actor (the Character vtable; the player is a
// PlayerCharacter and is skipped):
//   IN   every event sent into the actor's behaviour graph (IAnimationGraphManagerHolder::NotifyAnimationGraph),
//        with whether the graph accepted it;
//   OUT  every event the graph sends back to the actor (its BSTEventSink<BSAnimationGraphEvent>): clip triggers and
//        state enter/exit notify events such as RemoveCharacterControllerFromWorld / AddCharacterControllerToWorld;
//   STATE a 4 Hz sample from Actor::Update: knock state, IsInRagdollState, dead, character controller present,
//        the reference's z and the pelvis bone's world z (a rigid hang shows as pelvis z not changing).
// An actor is traced for kTraceWindowMs after any event whose name contains one of kTriggerWords.
// Log: My Games/Skyrim Special Edition/SKSE/ZenRagdollTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "ZenRagdollTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr std::int64_t kTraceWindowMs = 20000;
	constexpr std::int64_t kSampleEveryMs = 250;
	constexpr std::array   kTriggerWords{ "ragdoll"sv, "getup"sv, "death"sv, "charactercontroller"sv, "reanimat"sv };

	struct Trace
	{
		std::int64_t lastTriggerMs{ 0 };
		std::int64_t lastSampleMs{ 0 };
	};

	std::mutex                                  g_lock;
	std::unordered_map<RE::FormID, Trace>       g_traces;
	const std::chrono::steady_clock::time_point g_start = std::chrono::steady_clock::now();

	std::int64_t NowMs()
	{
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - g_start).count();
	}

	bool IsTrigger(std::string_view a_name)
	{
		std::string lower{ a_name };
		std::ranges::transform(lower, lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
		return std::ranges::any_of(kTriggerWords, [&](std::string_view w) { return lower.find(w) != std::string::npos; });
	}

	std::string Describe(const RE::Actor* a_actor)
	{
		const auto* base = a_actor->GetActorBase();
		const auto* race = a_actor->GetRace();
		return std::format("{:08X} '{}' base {:08X} race {:08X} '{}'", a_actor->GetFormID(), a_actor->GetName(),
			base ? base->GetFormID() : 0, race ? race->GetFormID() : 0, race ? race->GetName() : "");
	}

	// Returns true when the actor is (now) traced; a trigger event starts or extends the window.
	bool Touch(const RE::Actor* a_actor, std::string_view a_event, std::int64_t a_now)
	{
		const bool trigger = IsTrigger(a_event);
		std::scoped_lock l{ g_lock };
		auto it = g_traces.find(a_actor->GetFormID());
		if (it == g_traces.end()) {
			if (!trigger) {
				return false;
			}
			it = g_traces.emplace(a_actor->GetFormID(), Trace{}).first;
			SKSE::log::info("{:>8} TRACE start {}", a_now, Describe(a_actor));
		} else if (a_now - it->second.lastTriggerMs > kTraceWindowMs) {
			if (!trigger) {
				return false;
			}
			SKSE::log::info("{:>8} TRACE start {}", a_now, Describe(a_actor));
		}
		if (trigger) {
			it->second.lastTriggerMs = a_now;
		}
		return true;
	}

	struct NotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool result = func(a_this, a_eventName);
			auto*      actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
			const std::string_view name{ a_eventName.c_str() ? a_eventName.c_str() : "" };
			if (actor) {
				const auto now = NowMs();
				if (Touch(actor, name, now)) {
					SKSE::log::info("{:>8} {:08X} IN    {}{}", now, actor->GetFormID(), name, result ? "" : "  (not accepted)");
				}
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct GraphEventSink
	{
		static RE::BSEventNotifyControl thunk(RE::BSTEventSink<RE::BSAnimationGraphEvent>* a_this,
			const RE::BSAnimationGraphEvent* a_event, RE::BSTEventSource<RE::BSAnimationGraphEvent>* a_source)
		{
			if (a_event) {
				auto* actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
				const std::string_view tag{ a_event->tag.c_str() ? a_event->tag.c_str() : "" };
				if (actor) {
					const auto now = NowMs();
					if (Touch(actor, tag, now)) {
						const std::string_view payload{ a_event->payload.c_str() ? a_event->payload.c_str() : "" };
						SKSE::log::info("{:>8} {:08X} OUT   {}{}{}", now, actor->GetFormID(), tag, payload.empty() ? "" : " ", payload);
					}
				}
			}
			return func(a_this, a_event, a_source);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct CharacterUpdate
	{
		static void thunk(RE::Character* a_this, float a_delta)
		{
			func(a_this, a_delta);
			const auto now = NowMs();
			{
				std::scoped_lock l{ g_lock };
				auto it = g_traces.find(a_this->GetFormID());
				if (it == g_traces.end() || now - it->second.lastTriggerMs > kTraceWindowMs ||
					now - it->second.lastSampleMs < kSampleEveryMs) {
					return;
				}
				it->second.lastSampleMs = now;
			}
			float pelvisZ = 0.0f;
			bool  hasPelvis = false;
			if (auto* root = a_this->Get3D()) {
				if (auto* pelvis = root->GetObjectByName("NPC Pelvis [Pelv]"sv)) {
					pelvisZ = pelvis->world.translate.z;
					hasPelvis = true;
				}
			}
			bool animDriven = false;
			a_this->GetGraphVariableBool("bAnimationDriven"sv, animDriven);
			SKSE::log::info("{:>8} {:08X} STATE knock={} ragdoll={} dead={} charCtrl={} animDriven={} z={:.1f} pelvisZ={}",
				now, a_this->GetFormID(), std::to_underlying(a_this->AsActorState()->GetKnockState()),
				a_this->IsInRagdollState(), a_this->IsDead(), a_this->GetCharController() != nullptr, animDriven,
				a_this->GetPosition().z, hasPelvis ? std::format("{:.1f}", pelvisZ) : "none"s);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// 1.1.0: dead bodies vanishing on the killing blow (sometimes gone, sometimes back after a few seconds, sometimes
	// flung). Every death starts a DEATH trace sampled from the player's update, so it keeps going while the corpse's
	// own update stops or its 3D is gone: 20 Hz for kDeathFastMs, then 4 Hz until kDeathTraceMs.
	constexpr std::int64_t kDeathTraceMs = 15000;
	constexpr std::int64_t kDeathFastMs = 4000;

	struct DeathTrace
	{
		std::int64_t   startMs{ 0 };
		std::int64_t   lastSampleMs{ 0 };
		RE::NiPoint3   startPos{};
		std::uintptr_t last3D{ 0 };
	};

	std::unordered_map<RE::FormID, DeathTrace> g_deaths;

	void CountGeometry(RE::NiAVObject* a_obj, bool a_culledAbove, int& a_total, int& a_hidden)
	{
		if (!a_obj) {
			return;
		}
		const bool culled = a_culledAbove || a_obj->GetAppCulled();
		if (a_obj->AsGeometry()) {
			++a_total;
			if (culled) {
				++a_hidden;
			}
		}
		if (auto* node = a_obj->AsNode()) {
			for (auto& child : node->GetChildren()) {
				CountGeometry(child.get(), culled, a_total, a_hidden);
			}
		}
	}

	void SampleDeath(RE::FormID a_id, DeathTrace& a_trace, std::int64_t a_now)
	{
		auto* actor = RE::TESForm::LookupByID<RE::Actor>(a_id);
		if (!actor) {
			SKSE::log::info("{:>8} {:08X} DEATH form gone", a_now, a_id);
			return;
		}
		auto*      root = actor->Get3D();
		const auto ptr = reinterpret_cast<std::uintptr_t>(root);
		const auto pos = actor->GetPosition();
		int        total = 0, hidden = 0;
		CountGeometry(root, false, total, hidden);
		std::string pelvis = "none";
		if (root) {
			if (auto* p = root->GetObjectByName("NPC Pelvis [Pelv]"sv)) {
				pelvis = std::format("{:.0f},{:.0f},{:.0f}", p->world.translate.x, p->world.translate.y, p->world.translate.z);
			} else {
				pelvis = std::format("root {:.0f},{:.0f},{:.0f}", root->world.translate.x, root->world.translate.y, root->world.translate.z);
			}
		}
		auto* player = RE::PlayerCharacter::GetSingleton();
		SKSE::log::info("{:>8} {:08X} DEATH 3D={}{} rootCulled={} geom={}/{} hidden disabled={} deleted={} alpha={:.2f} "
						"ragdoll={} knock={} pos={:.0f},{:.0f},{:.0f} moved={:.0f} pelvis={} distPlayer={:.0f} cell={:08X}",
			a_now, a_id, root ? "yes" : "NO", ptr != a_trace.last3D && a_trace.last3D ? " (NEW 3D)" : "",
			root ? root->GetAppCulled() : false, hidden, total, actor->IsDisabled(), actor->IsMarkedForDeletion(),
			actor->GetAlpha(), actor->IsInRagdollState(), std::to_underlying(actor->AsActorState()->GetKnockState()),
			pos.x, pos.y, pos.z, pos.GetDistance(a_trace.startPos), pelvis,
			player ? pos.GetDistance(player->GetPosition()) : -1.0f, actor->GetParentCell() ? actor->GetParentCell()->GetFormID() : 0);
		a_trace.last3D = ptr;
	}

	struct DeathSink : RE::BSTEventSink<RE::TESDeathEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* a_event, RE::BSTEventSource<RE::TESDeathEvent>*) override
		{
			if (!a_event || !a_event->actorDying) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto* actor = a_event->actorDying->As<RE::Actor>();
			if (!actor || actor->IsPlayerRef()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const auto now = NowMs();
			auto*      killer = a_event->actorKiller.get();
			SKSE::log::info("{:>8} {:08X} DEATH event {} {} killer {:08X}", now, actor->GetFormID(),
				a_event->dead ? "dead" : "dying", Describe(actor), killer ? killer->GetFormID() : 0);
			std::scoped_lock l{ g_lock };
			auto [it, fresh] = g_deaths.try_emplace(actor->GetFormID());
			if (fresh || now - it->second.startMs > kDeathTraceMs) {
				it->second = DeathTrace{ now, 0, actor->GetPosition(), reinterpret_cast<std::uintptr_t>(actor->Get3D()) };
			}
			SampleDeath(actor->GetFormID(), it->second, now);
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			const auto      now = NowMs();
			std::scoped_lock l{ g_lock };
			for (auto it = g_deaths.begin(); it != g_deaths.end();) {
				auto& t = it->second;
				const auto age = now - t.startMs;
				if (age > kDeathTraceMs) {
					SKSE::log::info("{:>8} {:08X} DEATH trace end", now, it->first);
					it = g_deaths.erase(it);
					continue;
				}
				if (now - t.lastSampleMs >= (age < kDeathFastMs ? 50 : 250)) {
					t.lastSampleMs = now;
					SampleDeath(it->first, t, now);
				}
				++it;
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenRagdollTrace 1.1.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::log::info("knock: 0 normal, 1 explode, 2 explodeLeadIn, 3 out, 4 outLeadIn, 5 queued, 6 getUp, 7 down");

	// Character's vtables: [0] TESForm/Actor, [2] BSTEventSink<BSAnimationGraphEvent>, [3] IAnimationGraphManagerHolder.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_Character[2] };
	GraphEventSink::func = sinkVtbl.write_vfunc(0x1, GraphEventSink::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::log::info("Character Update, graph event sink and NotifyAnimationGraph hooked");

	REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = playerVtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			static DeathSink sink;
			RE::ScriptEventSourceHolder::GetSingleton()->AddEventSink<RE::TESDeathEvent>(&sink);
			SKSE::log::info("death event sink registered; DEATH lines: 3D, culled, visible geometry, position, pelvis");
		}
	});
	return true;
}
