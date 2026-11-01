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
//
// 1.1.0 (2026-11-01, first-person musket aim): arrow-type projectiles (bolts, Ordo's musket balls) are tracked too;
// each launch logs where the first-person rig's `Camera1st [Cam1]` and `Weapon` nodes sit in the rendering
// camera's frame, and each impact logs how far above/right of the launch-time crosshair ray it landed (units and
// degrees), so a constant angle (a tilt) can be told from a constant height (a wrong launch point).
//
// 1.2.0: also traces the auto-aim launch-angle call Hit Where You Aim hooks (ID 44200 +0x201): its launch node,
// origin and the angle before and after HWYA.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 2, 0, 0 },
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

	// The rendering camera's frame: its position and the camera root's axes (x right, y forward, z up).
	struct CameraFrame
	{
		RE::NiPoint3 pos, right, fwd, up;

		RE::NiPoint3 Local(const RE::NiPoint3& a_world) const
		{
			const auto d = a_world - pos;
			return { d.Dot(right), d.Dot(fwd), d.Dot(up) };
		}
	};

	std::optional<CameraFrame> GetCameraFrame()
	{
		auto* camera = RE::PlayerCamera::GetSingleton();
		auto* world = RE::Main::WorldRootCamera();
		if (!camera || !camera->cameraRoot || !world) {
			return std::nullopt;
		}
		const auto& r = camera->cameraRoot->world.rotate;
		return CameraFrame{ world->world.translate, { r.entry[0][0], r.entry[1][0], r.entry[2][0] }, { r.entry[0][1], r.entry[1][1], r.entry[2][1] },
			{ r.entry[0][2], r.entry[1][2], r.entry[2][2] } };
	}

	std::string Local(const RE::NiPoint3& p) { return fmt::format("right {:+.2f} fwd {:+.2f} up {:+.2f}", p.x, p.y, p.z); }

	// Projectiles the player launched, by pointer: how many updates have been logged, and the camera at launch.
	struct Shot
	{
		std::uint32_t              updates{ 0 };
		std::optional<CameraFrame> camera;
	};
	std::mutex                                g_lock;
	std::unordered_map<RE::Projectile*, Shot> g_tracked;
	constexpr std::uint32_t                   kUpdatesToLog = 4;

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

		if (const auto frame = GetCameraFrame()) {
			SKSE::log::info("  render camera at {} | launch origin in camera frame: {}", P3(frame->pos), Local(frame->Local(a_origin)));
			if (auto* fp = player->Get3D(true)) {
				for (const auto* name : { "Camera1st [Cam1]", "Weapon" }) {
					if (auto* node = fp->GetObjectByName(name)) {
						const auto& r = node->world.rotate;
						const RE::NiPoint3 nodeFwd{ r.entry[0][1], r.entry[1][1], r.entry[2][1] };
						SKSE::log::info("  1st-person {} in camera frame: {} | its +Y vs camera forward {:.2f} deg ({})", name, Local(frame->Local(node->world.translate)),
							AngleBetween(nodeFwd, frame->fwd), Dir(nodeFwd));
					}
				}
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
				g_tracked[proj.get()] = Shot{ 0, GetCameraFrame() };
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
				if (it == g_tracked.end() || it->second.updates >= kUpdatesToLog) {
					return;
				}
				n = ++it->second.updates;
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
			std::optional<Shot> shot;
			{
				std::scoped_lock l{ g_lock };
				if (const auto it = g_tracked.find(a_this); it != g_tracked.end()) {
					shot = it->second;
				}
			}
			if (shot) {
				const auto layer = a_collidable ? static_cast<int>(a_collidable->GetCollisionLayer()) : -1;
				SKSE::log::info("  IMPACT {} {:08X}: ref {} at {} (dist from launch pos {:.1f}) layer {} velocity {}", TypeName(a_this), a_this->GetFormID(), RefName(a_ref), P3(a_loc),
					(a_loc - a_this->GetPosition()).Length(), layer, Dir(a_velocity));
				if (shot->camera) {
					const auto l = shot->camera->Local(a_loc);
					SKSE::log::info("  IMPACT vs launch crosshair ray: {:.1f} units out, {:+.2f} units above ({:+.3f} deg), {:+.2f} units right ({:+.3f} deg)", l.y, l.z,
						Degrees(std::atan2(l.z, l.y)), l.x, Degrees(std::atan2(l.x, l.y)));
				}
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

	// 1.2.0: the player's auto-aim launch-angle call (ID 44200 +0x201), which Hit Where You Aim hooks
	// (PlayerProjectileCalculateLaunchAngleHook: calls the game, then aims from `a_origin`, or the launch node when
	// there is none, at the crosshair ray). Chained after HWYA at kPostLoad; logs what goes in and what comes out.
	struct LaunchAngle
	{
		using func_t = void(RE::PlayerCharacter*, RE::Projectile*, RE::NiAVObject*, float*, float*, RE::NiPoint3*, float, float);

		static void thunk(RE::PlayerCharacter* a_player, RE::Projectile* a_proj, RE::NiAVObject* a_node, float* a_yaw, float* a_pitch, RE::NiPoint3* a_origin, float a_7,
			float a_8)
		{
			const float yawIn = a_yaw ? *a_yaw : 0.0f;
			const float pitchIn = a_pitch ? *a_pitch : 0.0f;
			next(a_player, a_proj, a_node, a_yaw, a_pitch, a_origin, a_7, a_8);
			const auto frame = GetCameraFrame();
			if (!frame) {
				return;
			}
			SKSE::log::info("LAUNCH ANGLE call: projectile {:08X} at {} | unk7 {:.3f} unk8 {:.3f}", a_proj ? a_proj->GetFormID() : 0,
				a_proj ? Local(frame->Local(a_proj->GetPosition())) : "-", a_7, a_8);
			SKSE::log::info("  launch node '{}' at {}", a_node ? a_node->name.c_str() : "(null)", a_node ? Local(frame->Local(a_node->world.translate)) : "-");
			SKSE::log::info("  origin arg {}", a_origin ? Local(frame->Local(*a_origin)) : "(null) -> HWYA aims from the launch node");
			if (a_yaw && a_pitch) {
				const auto in = DirFromAngles(pitchIn, yawIn);
				const auto out = DirFromAngles(*a_pitch, *a_yaw);
				const auto li = frame->Local(frame->pos + in);
				const auto lo = frame->Local(frame->pos + out);
				SKSE::log::info("  angle in  x {:+.3f} z {:+.3f}: {:+.3f} deg above, {:+.3f} deg right of camera forward", Degrees(pitchIn), Degrees(yawIn),
					Degrees(std::atan2(li.z, li.y)), Degrees(std::atan2(li.x, li.y)));
				SKSE::log::info("  angle out x {:+.3f} z {:+.3f}: {:+.3f} deg above, {:+.3f} deg right of camera forward", Degrees(*a_pitch), Degrees(*a_yaw),
					Degrees(std::atan2(lo.z, lo.y)), Degrees(std::atan2(lo.x, lo.y)));
			}
		}
		static inline REL::Relocation<func_t> next;
	};

	void InstallLaunchAngle()
	{
		const auto site = REL::ID(44200).address() + 0x201;
		const auto* code = reinterpret_cast<const std::uint8_t*>(site);
		if (code[0] != 0xE8) {
			SKSE::log::error("launch-angle call not found at {:X} (byte {:02X}); not traced", site, code[0]);
			return;
		}
		SKSE::AllocTrampoline(14);
		LaunchAngle::next = SKSE::GetTrampoline().write_call<5>(site, LaunchAngle::thunk);
		SKSE::log::info("launch-angle call (44200 +0x201) traced after whatever hooked it before");
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenSpellAimTrace 1.2.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			InstallLaunchAngle();
		}
	});

	g_launch = reinterpret_cast<Launch_t>(REL::Relocation<std::uintptr_t>{ RELOCATION_ID(42928, 44108) }.address());
	DetourTransactionBegin();
	DetourUpdateThread(GetCurrentThread());
	DetourAttach(reinterpret_cast<PVOID*>(&g_launch), reinterpret_cast<PVOID>(&LaunchHook));
	const auto err = DetourTransactionCommit();
	SKSE::log::info("Projectile::Launch detour: {}", err == NO_ERROR ? "ok" : fmt::format("FAILED {}", err));

	HookProjectileType<RE::BeamProjectile>();
	HookProjectileType<RE::MissileProjectile>();
	HookProjectileType<RE::ConeProjectile>();
	HookProjectileType<RE::ArrowProjectile>();
	SKSE::log::info("Beam/Missile/Cone/Arrow UpdateImpl + AddImpact hooked");
	return true;
}
