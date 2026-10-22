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
	.Version = REL::Version{ 1, 0, 0, 0 },
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
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenRagdollTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::log::info("knock: 0 normal, 1 explode, 2 explodeLeadIn, 3 out, 4 outLeadIn, 5 queued, 6 getUp, 7 down");

	// Character's vtables: [0] TESForm/Actor, [2] BSTEventSink<BSAnimationGraphEvent>, [3] IAnimationGraphManagerHolder.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_Character[2] };
	GraphEventSink::func = sinkVtbl.write_vfunc(0x1, GraphEventSink::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::log::info("Character Update, graph event sink and NotifyAnimationGraph hooked");
	return true;
}
