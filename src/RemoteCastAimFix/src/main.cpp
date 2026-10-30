#include "pch.h"

// Hit Where You Aim (Tossapon, GPL-3) hooks the call in the projectile setup (ID 44222 +0x78A) to the projectile's
// initialisation (ID 44184). For every projectile whose shooter is the player it saves the angle before that
// initialisation and writes it back after (its ProjectileInitHook: "TDM overrides the data here"). A RemoteCast
// that blames the player turns its projectile toward the target during that initialisation. Holy Templar's
// _LIP_LightshaftSkyboltActivatorScript (Prophecy's Smite and Wrath of the Heavens) fires 9 such beams from a
// marker above the target at scattered markers, so with HWYA they kept the spawner marker's own angle and
// missed (curator 2026-10-30: "the ones from smite are being misplaced by Hit Where You Aim").
//
// This plugin hooks the same call after HWYA (kPostLoad, so HWYA's hook is in place) and chains to it, except
// for a spell projectile that starts away from the player: no weapon or ammo source, and more than 64 units
// from every player magic node and the head. Those get only the game's initialisation, as before HWYA.
//
// 1.0.0 hooked the launch-angle call (ID 44200 +0x201, HWYA's PlayerProjectileCalculateLaunchAngleHook)
// instead: in game it logged no remote launches (the game only runs that call for auto-aimed launches), and
// the beams stayed misplaced.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "ZenRemoteCastAim"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr float kNodeRadius = 64.0f;  // an own spell starts at a player magic node (traced 0.0 units off)
	int             g_logged{ 0 };        // remote projectiles logged so far (first 30)

	bool NearPlayer(RE::PlayerCharacter* a_player, const RE::NiPoint3& a_pos)
	{
		for (auto src : { RE::MagicSystem::CastingSource::kLeftHand, RE::MagicSystem::CastingSource::kRightHand,
				 RE::MagicSystem::CastingSource::kOther, RE::MagicSystem::CastingSource::kInstant }) {
			auto* caster = a_player->GetMagicCaster(src);
			auto* node = caster ? caster->GetMagicNode() : nullptr;
			if (node && node->world.translate.GetDistance(a_pos) < kNodeRadius) {
				return true;
			}
		}
		for (bool firstPerson : { false, true }) {
			auto* root = a_player->Get3D(firstPerson);
			auto* head = root ? root->GetObjectByName("NPC Head [Head]"sv) : nullptr;
			if (head && head->world.translate.GetDistance(a_pos) < kNodeRadius) {
				return true;
			}
		}
		return false;
	}

	// a spell projectile the player is blamed for that does not start at the player
	bool RemoteSpell(RE::Projectile* a_proj, RE::PlayerCharacter* a_player)
	{
		auto& data = a_proj->GetProjectileRuntimeData();
		if (data.shooter.native_handle() != 0x100000 || !data.spell || data.ammoSource || data.weaponSource) {
			return false;
		}
		return !NearPlayer(a_player, a_proj->GetPosition());
	}

	struct ProjectileInit
	{
		using func_t = void(RE::Projectile*);

		static void thunk(RE::Projectile* a_proj)
		{
			auto* player = RE::PlayerCharacter::GetSingleton();
			if (a_proj && player && RemoteSpell(a_proj, player)) {
				static REL::Relocation<func_t> vanilla{ REL::ID(44184) };
				const auto before = a_proj->data.angle;
				vanilla(a_proj);
				if (g_logged < 30) {
					++g_logged;
					const auto* base = a_proj->GetBaseObject();
					const auto  pos = a_proj->GetPosition();
					SKSE::log::info("remote spell projectile {:08X} ({}) at {:.0f},{:.0f},{:.0f}: game aim kept, angle x {:.3f} z {:.3f} (HWYA would have kept x {:.3f} z {:.3f})",
						base ? base->GetFormID() : 0, base ? base->GetName() : "", pos.x, pos.y, pos.z,
						a_proj->data.angle.x, a_proj->data.angle.z, before.x, before.z);
				}
				return;
			}
			next(a_proj);
		}
		static inline REL::Relocation<func_t> next;
	};

	void Install()
	{
		const auto site = REL::ID(44222).address() + 0x78A;
		const auto* code = reinterpret_cast<const std::uint8_t*>(site);
		if (code[0] != 0xE8) {
			SKSE::log::error("projectile init call not found at {:X} (byte {:02X}); not hooked", site, code[0]);
			return;
		}
		const auto current = site + 5 + *reinterpret_cast<const std::int32_t*>(site + 1);
		const auto vanilla = REL::ID(44184).address();
		SKSE::AllocTrampoline(14);
		ProjectileInit::next = SKSE::GetTrampoline().write_call<5>(site, ProjectileInit::thunk);
		SKSE::log::info("projectile init call hooked; it led to {} ({:X})", current == vanilla ? "the game's function: HWYA not installed" : "another hook (HWYA)", current);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenRemoteCastAim 1.1.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			Install();
		}
	});
	return true;
}
