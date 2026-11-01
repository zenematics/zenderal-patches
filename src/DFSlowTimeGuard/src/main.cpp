#include "pch.h"

// Dismembering Framework's player slow-motion (dfplayerdismembereffectscript: SetGlobalTimeMultiplier(factor), Wait,
// SetGlobalTimeMultiplier(1.0)) goes through its Papyrus native DismemberingFramework.SetGlobalTimeMultiplier. DF's own
// native (src/Papyrus.hpp) skips a value below 1.0 while the player has a SlowTime-archetype effect, but always lets
// the reset to 1.0 through. A dismember during Seismic Stomp's SlowTime (Zenderal - Prophecy, world at 30% for 10 s)
// therefore snapped time back to normal speed halfway through.
//
// This re-registers that one native after data load, so it replaces DF's binding: while the player has a
// SlowTime-archetype effect DF may not change time at all, in either direction; otherwise it does exactly what DF's
// native does (BSTimer::SetGlobalTimeMultiplier(value, false)). Nothing in DF is edited.
// Log: My Games/Skyrim Special Edition/SKSE/ZenDFSlowTimeGuard.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenDFSlowTimeGuard"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	bool PlayerInSlowTime()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* target = player ? player->AsMagicTarget() : nullptr;
		return target && target->HasEffectWithArchetype(RE::EffectArchetypes::ArchetypeID::kSlowTime);
	}

	void SetGlobalTimeMultiplier(RE::StaticFunctionTag*, float a_multiplier)
	{
		if (PlayerInSlowTime()) {
			SKSE::log::info("DF time multiplier {:.2f} ignored: the player has a SlowTime effect", a_multiplier);
			return;
		}
		if (auto* timer = RE::BSTimer::GetSingleton()) {
			timer->SetGlobalTimeMultiplier(a_multiplier, false);
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenDFSlowTimeGuard 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		// After every plugin's Papyrus registration callback, so this binding replaces DF's.
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			if (auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton()) {
				vm->RegisterFunction("SetGlobalTimeMultiplier"sv, "DismemberingFramework"sv, SetGlobalTimeMultiplier);
				SKSE::log::info("DismemberingFramework.SetGlobalTimeMultiplier re-registered");
			}
		}
	});
	return true;
}
