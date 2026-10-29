#include "pch.h"

#include <detours/detours.h>

// Testing tool, read-only. Logs every projectile the player launches and where it hits, next to the camera and
// crosshair, to find why a third-person spell (Prophecy's Consecrate Dead, an aimed Beam) lands just past the
// crosshair while Missile spells and first person are fine.
//
// Per launch (Projectile::Launch, Detours): base projectile + type, spell, LaunchData origin/angles/flags, the
// player's angles, both magic nodes, the camera root, and the engine's crosshair pick (target + collision
// point), with the angle between the launch direction and the direction from the origin to each of those.
// After launch: the projectile's own position/angle for its first updates (UpdateImpl), and each AddImpact.
// Nothing is written back.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 0, 0, 0 },
	.Name = "ZenSpellAimTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr float kPi = 3.14159265358979f;

	float Degrees(float a_rad) { return a_rad * 180.0f / kPi; }

	// Skyrim angles: x = pitch (positive looks down), z = heading (0 = +Y, clockwise).
	RE::NiPoint3 DirFromAngles(float a_x, float a_z)
	{
		return { std::sin(a_z) * std::cos(a_x), std::cos(a_z) * std::cos(a_x), -std::sin(a_x) };
	}

	float AngleBetween(const RE::NiPoint3& a, const RE::NiPoint3& b)
	{
		const float la = a.Length();
		const float lb = b.Length();
		if (la < 1e-4f || lb < 1e-4f) {
			return -1.0f;
		}
		return Degrees(std::acos(std::clamp(a.Dot(b) / (la * lb), -1.0f, 1.0f)));
	}

	std::string P3(const RE::NiPoint3& p) { return fmt::format("({:.1f}, {:.1f}, {:.1f})", p.x, p.y, p.z); }

	std::string Dir(const RE::NiPoint3& d)
	{
		const float len = d.Length();
		if (len < 1e-4f) {
			return "(none)";
		}
		const auto n = d / len;
		return fmt::format("pitch {:+.2f} yaw {:+.2f}", Degrees(-std::asin(n.z)), Degrees(std::atan2(n.x, n.y)));
	}

	const char* TypeName(RE::Projectile* a_proj)
	{
		if (a_proj->Is(RE::FormType::ProjectileBeam)) return "Beam";
		if (a_proj->Is(RE::FormType::ProjectileMissile)) return "Missile";
		if (a_proj->Is(RE::FormType::ProjectileCone)) return "Cone";
		if (a_proj->Is(RE::FormType::ProjectileFlame)) return "Flame";
		if (a_proj->Is(RE::FormType::ProjectileArrow)) return "Arrow";
		if (a_proj->Is(RE::FormType::ProjectileBarrier)) return "Barrier";
		if (a_proj->Is(RE::FormType::ProjectileGrenade)) return "Grenade";
		return "?";
	}

	bool FromPlayer(RE::Projectile* a_proj)
	{
		auto& rd = a_proj->GetProjectileRuntimeData();
		const auto shooter = rd.shooter.get();
		return shooter && shooter->IsPlayerRef();
	}

	std::string RefName(RE::TESObjectREFR* a_ref)
	{
		if (!a_ref) {
			return "none";
		}
		const auto* base = a_ref->GetBaseObject();
		return fmt::format("{:08X} '{}' {}{}", a_ref->GetFormID(), a_ref->GetDisplayFullName(), base ? fmt::format("base {:08X}", base->GetFormID()) : "",
			a_ref->IsDead() ? " DEAD" : "");
	}

	// Projectiles the player launched, by pointer, with how many updates have been logged.
	std::mutex                                       g_lock;
	std::unordered_map<RE::Projectile*, std::uint32_t> g_tracked;
	constexpr std::uint32_t                          kUpdatesToLog = 4;

	void LogContext(const RE::NiPoint3& a_origin, const RE::NiPoint3& a_dir)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		SKSE::log::info("  player pos {} angle x {:+.2f} z {:+.2f} (dir {})", P3(player->GetPosition()), Degrees(player->data.angle.x), Degrees(player->data.angle.z),
			Dir(DirFromAngles(player->data.angle.x, player->data.angle.z)));
		SKSE::log::info("  launch vs player aim: {:.2f} deg", AngleBetween(a_dir, DirFromAngles(player->data.angle.x, player->data.angle.z)));

		for (const auto* name : { "NPC L MagicNode [LMag]", "NPC R MagicNode [RMag]" }) {
			if (auto* node = player->GetNodeByName(name)) {
				SKSE::log::info("  {} at {} (origin offset {:.1f})", name, P3(node->world.translate), (node->world.translate - a_origin).Length());
			}
		}

		if (auto* camera = RE::PlayerCamera::GetSingleton(); camera && camera->cameraRoot) {
			const auto& w = camera->cameraRoot->world;
			const RE::NiPoint3 fwd{ w.rotate.entry[0][1], w.rotate.entry[1][1], w.rotate.entry[2][1] };
			const auto* state = camera->currentState.get();
			SKSE::log::info("  camera state {} root {} forward {} | launch vs camera forward {:.2f} deg", state ? static_cast<int>(state->id) : -1, P3(w.translate), Dir(fwd),
				AngleBetween(a_dir, fwd));
		}

		if (auto* pick = RE::CrosshairPickData::GetSingleton()) {
			const auto target = pick->target.get();
			const auto targetActor = pick->targetActor.get();
			SKSE::log::info("  crosshair pick: target {} actor {} collisionPoint {}", RefName(target.get()), RefName(targetActor.get()), P3(pick->collisionPoint));
			const auto toPick = pick->collisionPoint - a_origin;
			SKSE::log::info("  origin -> pick point: {} dist {:.1f} | launch off it by {:.2f} deg", Dir(toPick), toPick.Length(), AngleBetween(a_dir, toPick));
			if (target) {
				const auto toTarget = target->GetPosition() - a_origin;
				SKSE::log::info("  origin -> pick target pos {}: {} | launch off it by {:.2f} deg", P3(target->GetPosition()), Dir(toTarget), AngleBetween(a_dir, toTarget));
			}
		}
	}

	using Launch_t = RE::ProjectileHandle* (*)(RE::ProjectileHandle*, RE::Projectile::LaunchData&);
	Launch_t g_launch{ nullptr };

	RE::ProjectileHandle* LaunchHook(RE::ProjectileHandle* a_result, RE::Projectile::LaunchData& a_data)
	{
		const bool fromPlayer = a_data.shooter && a_data.shooter->IsPlayerRef();
		RE::NiPoint3 dir{};
		if (fromPlayer) {
			dir = DirFromAngles(a_data.angleX, a_data.angleZ);
			SKSE::log::info("LAUNCH base {:08X} '{}' spell {:08X} '{}' source {}", a_data.projectileBase ? a_data.projectileBase->GetFormID() : 0,
				a_data.projectileBase ? a_data.projectileBase->GetFormEditorID() : "", a_data.spell ? a_data.spell->GetFormID() : 0, a_data.spell ? a_data.spell->GetName() : "",
				static_cast<int>(a_data.castingSource));
			SKSE::log::info("  data origin {} angleX {:+.2f} angleZ {:+.2f} (dir {}) desiredTarget {} autoAim {} useOrigin {} alwaysHit {} forceCone {} unk60 {:.2f} unk64 {:.2f}",
				P3(a_data.origin), Degrees(a_data.angleX), Degrees(a_data.angleZ), Dir(dir), RefName(a_data.desiredTarget), a_data.autoAim, a_data.useOrigin, a_data.alwaysHit,
				a_data.forceConeOfFire, a_data.unk60, a_data.unk64);
			LogContext(a_data.origin, dir);
		}

		auto* result = g_launch(a_result, a_data);

		if (fromPlayer && result) {
			if (auto proj = result->get()) {
				auto& rd = proj->GetProjectileRuntimeData();
				SKSE::log::info("  -> {} {:08X} pos {} angle x {:+.2f} z {:+.2f} (dir {}) velocity {} | dir vs data {:.2f} deg", TypeName(proj.get()), proj->GetFormID(),
					P3(proj->GetPosition()), Degrees(proj->data.angle.x), Degrees(proj->data.angle.z), Dir(DirFromAngles(proj->data.angle.x, proj->data.angle.z)), Dir(rd.velocity),
					AngleBetween(DirFromAngles(proj->data.angle.x, proj->data.angle.z), dir));
				std::scoped_lock l{ g_lock };
				g_tracked[proj.get()] = 0;
			}
		}
		return result;
	}

	template <class T>
	struct UpdateHook
	{
		static void thunk(RE::Projectile* a_this, float a_delta)
		{
			func(a_this, a_delta);
			std::uint32_t n;
			{
				std::scoped_lock l{ g_lock };
				const auto it = g_tracked.find(a_this);
				if (it == g_tracked.end() || it->second >= kUpdatesToLog) {
					return;
				}
				n = ++it->second;
			}
			auto& rd = a_this->GetProjectileRuntimeData();
			SKSE::log::info("  update {} {:08X}: pos {} angle x {:+.2f} z {:+.2f} (dir {}) velocity {} desiredTarget {}", n, a_this->GetFormID(), P3(a_this->GetPosition()),
				Degrees(a_this->data.angle.x), Degrees(a_this->data.angle.z), Dir(DirFromAngles(a_this->data.angle.x, a_this->data.angle.z)), Dir(rd.velocity),
				RefName(rd.desiredTarget.get().get()));
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	template <class T>
	struct ImpactHook
	{
		static void thunk(RE::Projectile* a_this, RE::TESObjectREFR* a_ref, const RE::NiPoint3& a_loc, const RE::NiPoint3& a_velocity, RE::hkpCollidable* a_collidable,
			std::int32_t a_arg6, std::uint32_t a_arg7)
		{
			bool tracked;
			{
				std::scoped_lock l{ g_lock };
				tracked = g_tracked.contains(a_this);
			}
			if (tracked) {
				const auto layer = a_collidable ? static_cast<int>(a_collidable->GetCollisionLayer()) : -1;
				SKSE::log::info("  IMPACT {} {:08X}: ref {} at {} (dist from launch pos {:.1f}) layer {} velocity {}", TypeName(a_this), a_this->GetFormID(), RefName(a_ref), P3(a_loc),
					(a_loc - a_this->GetPosition()).Length(), layer, Dir(a_velocity));
			}
			func(a_this, a_ref, a_loc, a_velocity, a_collidable, a_arg6, a_arg7);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	template <class T>
	void HookProjectileType()
	{
		REL::Relocation<std::uintptr_t> vtbl{ T::VTABLE[0] };
		UpdateHook<T>::func = vtbl.write_vfunc(0xAB, UpdateHook<T>::thunk);
		ImpactHook<T>::func = vtbl.write_vfunc(0xBD, ImpactHook<T>::thunk);
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenSpellAimTrace 1.0.0 loading, runtime {}", REL::Module::get().version().string());

	g_launch = reinterpret_cast<Launch_t>(REL::Relocation<std::uintptr_t>{ RELOCATION_ID(42928, 44108) }.address());
	DetourTransactionBegin();
	DetourUpdateThread(GetCurrentThread());
	DetourAttach(reinterpret_cast<PVOID*>(&g_launch), reinterpret_cast<PVOID>(&LaunchHook));
	const auto err = DetourTransactionCommit();
	SKSE::log::info("Projectile::Launch detour: {}", err == NO_ERROR ? "ok" : fmt::format("FAILED {}", err));

	HookProjectileType<RE::BeamProjectile>();
	HookProjectileType<RE::MissileProjectile>();
	HookProjectileType<RE::ConeProjectile>();
	SKSE::log::info("Beam/Missile/Cone UpdateImpl + AddImpact hooked");
	return true;
}
