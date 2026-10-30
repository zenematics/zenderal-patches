#include "pch.h"

// Hit Where You Aim (Tossapon, GPL-3) hooks the call in ID 37356 (+0xC3A in 1.7.104) that sets the player's
// aim pitch (ID 39880, the angle the 3rd-person aiming pose uses). While a bow, crossbow or musket is drawn
// and the attack state is between kBowDraw and kBowFollowThrough, its PlayerGetAimPitch (Hooks.cpp:358) reads
// player->GetCurrentAmmo()->...data.projectile with no null check. Firing the last arrow or bullet unequips
// the ammo while the attack state is still in that range, so it read address 0x110 and the game crashed
// (Crash Logger 2026-10-30, HitWhereYouAim.dll+0x2551C).
//
// This plugin hooks the same call after HWYA (kPostLoad, so HWYA's hook is already in place) and chains to
// it, except in exactly that case: the player's process, weapon drawn, attack state in HWYA's range and no
// ammo equipped. Those frames get the game's own function, as before HWYA was installed.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenHWYAEmptyAmmo"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	int g_skipped{ 0 };  // empty-ammo frames given the game's function (first 10 logged)

	bool HwyaWouldReadNullAmmo(RE::AIProcess* a_process)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || a_process != player->GetActorRuntimeData().currentProcess || player->GetCurrentAmmo()) {
			return false;
		}
		const auto* state = player->AsActorState();
		const auto  attack = state->GetAttackState();
		return state->IsWeaponDrawn() && attack >= RE::ATTACK_STATE_ENUM::kBowDraw && attack <= RE::ATTACK_STATE_ENUM::kBowFollowThrough;
	}

	struct SetAimPitch
	{
		using func_t = void(RE::AIProcess*, float);

		static void thunk(RE::AIProcess* a_process, float a_pitch)
		{
			if (HwyaWouldReadNullAmmo(a_process)) {
				static REL::Relocation<func_t> vanilla{ REL::ID(39880) };
				if (g_skipped < 10) {
					++g_skipped;
					SKSE::log::info("no ammo equipped in attack state {}: game aim pitch kept ({:.3f})",
						static_cast<std::uint32_t>(RE::PlayerCharacter::GetSingleton()->AsActorState()->GetAttackState()), a_pitch);
				}
				return vanilla(a_process, a_pitch);
			}
			return next(a_process, a_pitch);
		}
		static inline REL::Relocation<func_t> next;
	};

	void Install()
	{
		const auto site = REL::ID(37356).address() + 0xC3A;
		const auto* code = reinterpret_cast<const std::uint8_t*>(site);
		if (code[0] != 0xE8) {
			SKSE::log::error("aim-pitch call not found at {:X} (byte {:02X}); not hooked", site, code[0]);
			return;
		}
		const auto current = site + 5 + *reinterpret_cast<const std::int32_t*>(site + 1);
		const auto vanilla = REL::ID(39880).address();
		SKSE::AllocTrampoline(14);
		SetAimPitch::next = SKSE::GetTrampoline().write_call<5>(site, SetAimPitch::thunk);
		SKSE::log::info("aim-pitch call hooked; it led to {} ({:X})", current == vanilla ? "the game's function: HWYA not installed" : "another hook (HWYA)", current);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenHWYAEmptyAmmo 1.0.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			Install();
		}
	});
	return true;
}
