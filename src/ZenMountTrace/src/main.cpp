#include "pch.h"

#include <Windows.h>
#include <TlHelp32.h>
#include <atomic>
#include <thread>

#include <chrono>
#include <cmath>
#include <ctime>

// Testing tool, not part of the list (2026-11-12). A player report: Father Shadow (the Shadow of Transience mount,
// NPC 0450F9, race HorseFluteWolfMountRace 0450F7, vanilla WolfProject.hkx graph) only runs straight when ridden and
// cannot turn. Its graph, skeleton and race match stock Enderal, and TDM gives mount input back to vanilla, so this
// logs what the engine actually does while the player rides ANY mount (ride a horse too, for comparison):
//   SAMPLE  10 Hz: mount heading (deg) and its change since the last sample, the mount's AI rotation speed, its speed,
//           the turn/locomotion graph variables ("-" = the graph has no such variable), the player's move/look input,
//           the camera state id and (horse camera state) horseCurrentDirection / freeRotation;
//   IN/OUT  every event sent into the mount's graph (accepted or not) and every event it sends back, footsteps left out.
// Log: My Games/Skyrim Special Edition/SKSE/ZenMountTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 5, 0, 0 },
	.Name = "ZenMountTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr std::int64_t kSampleEveryMs = 100;
	constexpr std::array   kFloats{ "Speed"sv, "Direction"sv, "TurnDelta"sv, "TurnDeltaDamped"sv, "SpeedSampled"sv,
		  "SpeedDamped"sv, "TurnMin"sv, "TurnMax"sv, "iTurnDelta"sv };
	constexpr std::array   kBools{ "bAnimationDriven"sv, "bMotionDriven"sv, "bAllowRotation"sv, "IsMoving"sv,
		  "bHeadTrackSpine"sv, "bIsSynced"sv, "IsAttackReady"sv };
	constexpr std::array   kInts{ "iState"sv, "iSyncTurnState"sv, "iSyncIdleLocomotion"sv };
	constexpr std::array   kQuietOut{ "FootLeft"sv, "FootRight"sv, "FootFront"sv, "FootBack"sv, "FootSprintLeft"sv,
		  "FootSprintRight"sv, "FootScuffLeft"sv, "FootScuffRight"sv };

	const std::chrono::steady_clock::time_point g_start = std::chrono::steady_clock::now();
	std::int64_t                                g_lastSample{ 0 };
	RE::FormID                                  g_lastMount{ 0 };
	float                                       g_lastHeading{ 0.0f };
	std::atomic<std::uint32_t> g_bypassed{ 0 };
	std::atomic<std::uint32_t> g_bypassedNonzero{ 0 };

	std::int64_t NowMs();

	// ---- 1.2.0: hardware watch. On RIDE start DR0/DR1 watch reads+writes of the horse camera's freeRotation.x
	// (+0xD4) and freeRotationEnabled (+0xDC), DR2 writes of the mount's heading (data.angle.z), on every thread,
	// for kWatchMs. Each distinct instruction that touches one is kept once (module+RVA, ID, and its call stack) and
	// counted; logged from the game thread.
	constexpr std::int64_t kWatchMs = 15000;
	constexpr int          kMaxHits = 96;
	constexpr int          kFrames = 10;

	struct Hit
	{
		std::atomic<bool>          used{ false };
		std::atomic<bool>          ready{ false };
		bool                       logged{ false };
		int                        reg{ 0 };
		void*                      rip{ nullptr };
		std::atomic<std::uint32_t> count{ 0 };
		std::uint16_t              n{ 0 };
		void*                      frames[kFrames]{};
		std::atomic<std::uint32_t> nonzero{ 0 };
		float                      lastValue{ 0.0f };
	};

	std::array<Hit, kMaxHits>            g_hits;
	std::array<std::uintptr_t, 3>        g_watch{};
	std::array<int, 3>                   g_watchLen{ 4, 4, 4 };
	std::array<bool, 3>                  g_watchRW{ false, false, false };
	bool                                 g_handlerAdded{ false };
	bool                                 g_armed{ false };
	bool                                 g_watchDone{ false };
	std::int64_t                         g_armedAt{ 0 };
	std::vector<REL::IDDB::mapping_t>    g_offsets;
	// 1.3.0: the camera's own fields are read only by camera code (1.2.0 log), so the watch moved to what steering
	// should consume: the player's move input and the camera's world yaw.
	// 1.4.0: steering input is consumed (1.3.0 log: the player-controls movement agent, ID 42162, outputs a desired
	// heading); the mount's AI rotationSpeed stays 0, so watch who writes it (and the player's own), with the value.
	constexpr std::array<const char*, 3> kWatchName{ "mount.rotationSpeed.z write", "player.rotationSpeed.z write",
		"mount.heading(angle.z) write" };

	LONG CALLBACK WatchHandler(EXCEPTION_POINTERS* a_info)
	{
		if (a_info->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) {
			return EXCEPTION_CONTINUE_SEARCH;
		}
		auto*      ctx = a_info->ContextRecord;
		const auto dr6 = ctx->Dr6;
		if (!(dr6 & 0x7)) {
			return EXCEPTION_CONTINUE_SEARCH;
		}
		for (int r = 0; r < 3; ++r) {
			if (!(dr6 & (1ull << r))) {
				continue;
			}
			void* rip = reinterpret_cast<void*>(ctx->Rip);
			bool  found = false;
			for (auto& h : g_hits) {
				if (!h.used.load(std::memory_order_acquire)) {
					break;
				}
				if (h.ready.load(std::memory_order_acquire) && h.rip == rip && h.reg == r) {
					h.count.fetch_add(1);
					h.lastValue = *reinterpret_cast<const float*>(g_watch[r]);
					if (h.lastValue != 0.0f) {
						h.nonzero.fetch_add(1);
					}
					found = true;
					break;
				}
			}
			if (found) {
				continue;
			}
			for (auto& h : g_hits) {
				bool expected = false;
				if (h.used.compare_exchange_strong(expected, true)) {
					h.reg = r;
					h.rip = rip;
					h.count = 1;
					h.lastValue = *reinterpret_cast<const float*>(g_watch[r]);
					h.nonzero = h.lastValue != 0.0f ? 1 : 0;
					h.n = RtlCaptureStackBackTrace(0, kFrames, h.frames, nullptr);
					h.ready.store(true, std::memory_order_release);
					break;
				}
			}
		}
		ctx->Dr6 = 0;
		return EXCEPTION_CONTINUE_EXECUTION;
	}

	// DR7: L0/L1/L2 enable bits 0/2/4; RW at 16/20/24 (01 write, 11 read+write); LEN at 18/22/26 (00 1 byte, 11 4 bytes).
	void SetWatch(bool a_on)
	{
		std::thread([a_on] {
			const DWORD helper = GetCurrentThreadId();
			const DWORD pid = GetCurrentProcessId();
			HANDLE      snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
			if (snap == INVALID_HANDLE_VALUE) {
				return;
			}
			THREADENTRY32 te{};
			te.dwSize = sizeof(te);
			for (BOOL ok = Thread32First(snap, &te); ok; ok = Thread32Next(snap, &te)) {
				if (te.th32OwnerProcessID != pid || te.th32ThreadID == helper) {
					continue;
				}
				HANDLE th = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, te.th32ThreadID);
				if (!th) {
					continue;
				}
				if (SuspendThread(th) != static_cast<DWORD>(-1)) {
					CONTEXT ctx{};
					ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
					if (GetThreadContext(th, &ctx)) {
						ctx.Dr7 &= ~0x0FFF003Full;
						ctx.Dr0 = ctx.Dr1 = ctx.Dr2 = 0;
						if (a_on) {
							DWORD64* regs[3]{ &ctx.Dr0, &ctx.Dr1, &ctx.Dr2 };
							for (int r = 0; r < 3; ++r) {
								if (!g_watch[r]) {
									continue;
								}
								*regs[r] = g_watch[r];
								const std::uint64_t rw = g_watchRW[r] ? 0x3 : 0x1;
								const std::uint64_t len = g_watchLen[r] == 4 ? 0x3 : 0x0;
								ctx.Dr7 |= (1ull << (2 * r)) | (rw << (16 + 4 * r)) | (len << (18 + 4 * r));
							}
						}
						SetThreadContext(th, &ctx);
					}
					ResumeThread(th);
				}
				CloseHandle(th);
			}
			CloseHandle(snap);
		}).join();
	}

	std::string Where(const void* a_addr)
	{
		HMODULE mod{ nullptr };
		if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
				static_cast<LPCWSTR>(a_addr), &mod) || !mod) {
			return std::format("{}", a_addr);
		}
		char path[MAX_PATH]{};
		GetModuleFileNameA(mod, path, MAX_PATH);
		const char* name = std::strrchr(path, '\\');
		name = name ? name + 1 : path;
		const auto  rva = reinterpret_cast<std::uintptr_t>(a_addr) - reinterpret_cast<std::uintptr_t>(mod);
		std::string out = std::format("{}+{:X}", name, rva);
		if (mod == GetModuleHandleW(nullptr) && !g_offsets.empty()) {
			auto it = std::ranges::upper_bound(g_offsets, rva, {}, &REL::IDDB::mapping_t::offset);
			if (it != g_offsets.begin()) {
				--it;
				out += std::format(" (ID {} +{:X})", it->id, rva - it->offset);
			}
		}
		return out;
	}

	void Arm(RE::Actor* a_mount)
	{
		auto* cam = RE::PlayerCamera::GetSingleton();
		if (!cam || !cam->currentState || cam->currentState->id != RE::CameraState::kMount) {
			SKSE::log::info("WATCH not armed: the camera is not in the mount state yet");
			return;
		}
		if (!g_handlerAdded) {
			AddVectoredExceptionHandler(1, WatchHandler);
			g_handlerAdded = true;
		}
		auto rotZ = [](RE::Actor* a) -> std::uintptr_t {
			auto* proc = a ? a->GetActorRuntimeData().currentProcess : nullptr;
			return proc && proc->middleHigh ? reinterpret_cast<std::uintptr_t>(&proc->middleHigh->rotationSpeed.z) : 0;
		};
		g_watch = { rotZ(a_mount), rotZ(RE::PlayerCharacter::GetSingleton()),
			reinterpret_cast<std::uintptr_t>(&a_mount->data.angle.z) };
		SetWatch(true);
		g_armed = true;
		g_armedAt = NowMs();
		SKSE::log::info("WATCH armed for {} s: DR0 {} @{:X}, DR1 {} @{:X}, DR2 {} @{:X}", kWatchMs / 1000, kWatchName[0],
			g_watch[0], kWatchName[1], g_watch[1], kWatchName[2], g_watch[2]);
	}

	void FlushHits(bool a_final)
	{
		for (auto& h : g_hits) {
			if (!h.used.load(std::memory_order_acquire)) {
				break;
			}
			if (!h.ready.load(std::memory_order_acquire) || h.logged) {
				continue;
			}
			h.logged = true;
			std::string stack;
			for (int i = 1; i < h.n; ++i) {
				stack += "\n      " + Where(h.frames[i]);
			}
			SKSE::log::info("WATCH new {} by {} value={:.4f}{}", kWatchName[h.reg], Where(h.rip), h.lastValue, stack);
		}
		if (a_final) {
			for (auto& h : g_hits) {
				if (!h.used.load(std::memory_order_acquire)) {
					break;
				}
				SKSE::log::info("WATCH count {:6} nonzero {:6} last={:.4f} {} by {}", h.count.load(), h.nonzero.load(), h.lastValue,
					kWatchName[h.reg], Where(h.rip));
			}
		}
	}

	void Disarm(std::string_view a_why)
	{
		if (!g_armed) {
			return;
		}
		SetWatch(false);
		g_armed = false;
		FlushHits(true);
		SKSE::log::info("WATCH off ({})", a_why);
	}

	std::int64_t NowMs()
	{
		return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - g_start).count();
	}

	std::string Clock()
	{
		const auto        now = std::chrono::system_clock::now();
		const std::time_t t = std::chrono::system_clock::to_time_t(now);
		std::tm           tm{};
		localtime_s(&tm, &t);
		const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count() % 1000;
		return std::format("{:02}:{:02}:{:02}.{:03}", tm.tm_hour, tm.tm_min, tm.tm_sec, ms);
	}

	float Deg(float a_rad) { return a_rad * 57.29578f; }

	RE::Actor* RiddenMount()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return nullptr;
		}
		RE::NiPointer<RE::Actor> mount;
		return player->GetMount(mount) ? mount.get() : nullptr;
	}

	bool IsRiddenMount(RE::Actor* a_actor)
	{
		auto* mount = RiddenMount();
		return mount && mount == a_actor;
	}

	std::string Who(RE::Actor* a_actor)
	{
		auto* base = a_actor->GetActorBase();
		auto* race = a_actor->GetRace();
		return std::format("[{:08X} {} race {}]", a_actor->GetFormID(), a_actor->GetDisplayFullName(),
			race && race->GetFormEditorID() && *race->GetFormEditorID() ? race->GetFormEditorID() :
			race ? std::format("{:08X}", race->GetFormID()) : "?"s) + (base ? "" : "");
	}

	std::string GraphVars(RE::Actor* a_actor)
	{
		std::string out;
		for (auto n : kFloats) {
			float v{};
			out += a_actor->GetGraphVariableFloat(RE::BSFixedString{ n }, v) ? std::format(" {}={:.2f}", n, v) : std::format(" {}=-", n);
		}
		for (auto n : kBools) {
			bool v{};
			out += a_actor->GetGraphVariableBool(RE::BSFixedString{ n }, v) ? std::format(" {}={}", n, v ? 1 : 0) : std::format(" {}=-", n);
		}
		for (auto n : kInts) {
			std::int32_t v{};
			out += a_actor->GetGraphVariableInt(RE::BSFixedString{ n }, v) ? std::format(" {}={}", n, v) : std::format(" {}=-", n);
		}
		return out;
	}

	std::string Controls()
	{
		std::string out;
		if (auto* pc = RE::PlayerControls::GetSingleton()) {
			const auto& d = pc->data;
			out += std::format(" move=({:.2f},{:.2f}) look=({:.3f},{:.3f}) autoMove={} running={}", d.moveInputVec.x,
				d.moveInputVec.y, d.lookInputVec.x, d.lookInputVec.y, d.autoMove ? 1 : 0, d.running ? 1 : 0);
		}
		if (auto* cam = RE::PlayerCamera::GetSingleton(); cam && cam->currentState) {
			auto* state = cam->currentState.get();
			out += std::format(" cam={}", std::to_underlying(state->id));
			if (state->id == RE::CameraState::kMount) {
				auto* horse = static_cast<RE::HorseCameraState*>(state);
				out += std::format(" horseDir={:.1f} freeRot=({:.1f},{:.1f}) freeRotOn={}", Deg(horse->horseCurrentDirection),
					Deg(horse->freeRotation.x), Deg(horse->freeRotation.y), horse->freeRotationEnabled ? 1 : 0);
			}
		}
		return out;
	}

	// SEH needs a function without C++ objects to unwind (C2712), so the byte reads live here.
	std::uintptr_t JumpTarget(std::uintptr_t a_addr)
	{
		const auto*    b = reinterpret_cast<const std::uint8_t*>(a_addr);
		std::uintptr_t target = 0;
		__try {
			if (b[0] == 0xE9) {
				target = a_addr + 5 + *reinterpret_cast<const std::int32_t*>(b + 1);
			} else if (b[0] == 0xFF && b[1] == 0x25) {
				target = *reinterpret_cast<const std::uintptr_t*>(a_addr + 6 + *reinterpret_cast<const std::int32_t*>(b + 2));
			} else if (b[0] == 0x48 && b[1] == 0xB8 && b[10] == 0xFF && b[11] == 0xE0) {
				target = *reinterpret_cast<const std::uintptr_t*>(b + 2);
			}
		} __except (EXCEPTION_EXECUTE_HANDLER) {
			target = 0;
		}
		return target;
	}

	// Who owns a code address: "module+RVA". If it is in SkyrimSE.exe and starts with a jump (E9 rel32, FF25 [rip],
	// or 48 B8 imm64 + FF E0), the jump's target is followed once, so an inline detour shows its owner too.
	std::string Owner(std::uintptr_t a_addr)
	{
		auto name = [](std::uintptr_t a) {
			HMODULE mod{};
			if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
					reinterpret_cast<LPCWSTR>(a), &mod)) {
				return std::format("?{:X}", a);
			}
			char path[MAX_PATH]{};
			GetModuleFileNameA(mod, path, MAX_PATH);
			std::string_view p{ path };
			auto             slash = p.find_last_of("\\/");
			return std::format("{}+{:X}", p.substr(slash == std::string_view::npos ? 0 : slash + 1), a - reinterpret_cast<std::uintptr_t>(mod));
		};
		std::string out = name(a_addr);
		const std::uintptr_t target = JumpTarget(a_addr);
		if (target) {
			out += " -> " + name(target);
		}
		return out;
	}

	void DumpVtable(std::string_view a_label, std::uintptr_t a_vtbl, std::size_t a_count)
	{
		if (!a_vtbl) {
			return;
		}
		std::string line;
		for (std::size_t i = 0; i < a_count; ++i) {
			const auto fn = reinterpret_cast<const std::uintptr_t*>(a_vtbl)[i];
			line += std::format("\n    [{:02X}] {}", i, Owner(fn));
		}
		SKSE::log::info("OWNERS {} (vtable {}):{}", a_label, Owner(a_vtbl), line);
	}

	void DumpOwners()
	{
		if (auto* cam = RE::PlayerCamera::GetSingleton(); cam && cam->currentState) {
			DumpVtable("current camera state", *reinterpret_cast<const std::uintptr_t*>(cam->currentState.get()), 0x10);
		}
		DumpVtable("HorseCameraState[0]", REL::Relocation<std::uintptr_t>{ RE::VTABLE_HorseCameraState[0] }.address(), 0x10);
		DumpVtable("HorseCameraState[1]", REL::Relocation<std::uintptr_t>{ RE::VTABLE_HorseCameraState[1] }.address(), 0x6);
		DumpVtable("ThirdPersonState[0]", REL::Relocation<std::uintptr_t>{ RE::VTABLE_ThirdPersonState[0] }.address(), 0x10);
		DumpVtable("MovementHandler", REL::Relocation<std::uintptr_t>{ RE::VTABLE_MovementHandler[0] }.address(), 0x6);
		for (int i = 0; i < 3; ++i) {
			DumpVtable(std::format("MovementHandlerAgentPlayerControls[{}]", i),
				REL::Relocation<std::uintptr_t>{ RE::VTABLE_MovementHandlerAgentPlayerControls[i] }.address(), 0x10);
		}
		for (int i = 0; i < 7; ++i) {
			DumpVtable(std::format("MovementControllerNPC[{}]", i),
				REL::Relocation<std::uintptr_t>{ RE::VTABLE_MovementControllerNPC[i] }.address(), 0x10);
		}
		DumpVtable("LookHandler", REL::Relocation<std::uintptr_t>{ RE::VTABLE_LookHandler[0] }.address(), 0x6);
		DumpVtable("PlayerCharacter[0] (0xA0-0xB0)", REL::Relocation<std::uintptr_t>{ RE::VTABLE_PlayerCharacter[0] }.address() + 0xA0 * 8, 0x11);
		DumpVtable("Character[0] (0xA0-0xB0)", REL::Relocation<std::uintptr_t>{ RE::VTABLE_Character[0] }.address() + 0xA0 * 8, 0x11);
	}

	void Sample(RE::Actor* a_mount)
	{
		const auto now = NowMs();
		const bool fresh = a_mount->GetFormID() != g_lastMount;
		if (!fresh && now - g_lastSample < kSampleEveryMs) {
			return;
		}
		g_lastSample = now;
		const float heading = a_mount->GetAngleZ();
		if (fresh) {
			g_lastMount = a_mount->GetFormID();
			g_lastHeading = heading;
			auto* race = a_mount->GetRace();
			SKSE::log::info("{} {} RIDE start: angularAccel={:.2f} angularTol={:.2f} accel={:.2f} graph={}", Clock(),
				Who(a_mount), race ? race->data.angleAccelerate : -1.0f, race ? race->data.angleTolerance : -1.0f,
				race ? race->data.accelerate : -1.0f,
				std::string{ race ? race->behaviorGraphs[0].model.c_str() : "?" });
			DumpOwners();
		}
		float d = Deg(heading - g_lastHeading);
		while (d > 180.0f) d -= 360.0f;
		while (d < -180.0f) d += 360.0f;
		g_lastHeading = heading;

		if (!g_armed && !g_watchDone) {
			Arm(a_mount);
		} else if (g_armed && now - g_armedAt > kWatchMs) {
			g_watchDone = true;
			Disarm("time up");
		}
		FlushHits(false);

		std::string rot = " rotSpeed=?";
		if (auto* proc = a_mount->GetActorRuntimeData().currentProcess; proc && proc->middleHigh) {
			const auto& r = proc->middleHigh->rotationSpeed;
			rot = std::format(" rotSpeed=({:.2f},{:.2f},{:.2f})", r.x, r.y, r.z);
		}
		if (auto* pp = RE::PlayerCharacter::GetSingleton()->GetActorRuntimeData().currentProcess; pp && pp->middleHigh) {
			rot += std::format(" playerRotSpeedZ={:.3f} fixWrites={} fixNonzero={}", pp->middleHigh->rotationSpeed.z,
				g_bypassed.load(), g_bypassedNonzero.load());
		}
		SKSE::log::info("{} SAMPLE heading={:.1f} dHeading={:+.1f}{} moveSpeed={:.1f} moving={}{} |{}", Clock(), Deg(heading), d,
			rot, a_mount->DoGetMovementSpeed(), a_mount->IsMoving() ? 1 : 0, GraphVars(a_mount), Controls());
	}

	// ---- 1.5.0 fix candidate. TDM hooks the two AIProcess::SetRotationSpeedZ calls in the actor movement update
	// (ID 37356 +0x3EF / +0x632) and drops the call for the PLAYER's process while its free camera flag is set.
	// If vanilla steers a ridden mount through the rider's rotation speed, that drop is the whole bug. While the
	// player is mounted, this chains in front of TDM's hook and does the game's own write (= SetRotationSpeedZ:
	// middleHigh->rotationSpeed.z = value) for the player's process; everything else goes on to TDM.

	bool PlayerMounted()
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		RE::NiPointer<RE::Actor> mount;
		return player && player->GetMount(mount) && mount;
	}

	template <int N>
	struct SetRotationSpeedZ
	{
		static void thunk(RE::AIProcess* a_process, float a_speed)
		{
			auto* player = RE::PlayerCharacter::GetSingleton();
			if (a_process && player && a_process == player->GetActorRuntimeData().currentProcess && PlayerMounted()) {
				if (a_process->middleHigh) {
					a_process->middleHigh->rotationSpeed.z = a_speed;
				}
				g_bypassed.fetch_add(1);
				if (a_speed != 0.0f) {
					g_bypassedNonzero.fetch_add(1);
				}
				return;
			}
			next(a_process, a_speed);
		}
		static inline REL::Relocation<void(RE::AIProcess*, float)> next;
	};

	template <int N>
	void HookRotationSite(std::uintptr_t a_offset)
	{
		const auto  site = REL::ID(37356).address() + a_offset;
		const auto* code = reinterpret_cast<const std::uint8_t*>(site);
		if (code[0] != 0xE8) {
			SKSE::log::error("FIX rotation-speed call +{:X} not found (byte {:02X}); not hooked", a_offset, code[0]);
			return;
		}
		const auto current = site + 5 + *reinterpret_cast<const std::int32_t*>(site + 1);
		SetRotationSpeedZ<N>::next = SKSE::GetTrampoline().write_call<5>(site, SetRotationSpeedZ<N>::thunk);
		SKSE::log::info("FIX hooked ID 37356 +{:X}; it led to {}", a_offset, Owner(current));
	}

	struct NotifyAnimationGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool result = func(a_this, a_eventName);
			auto*      actor = static_cast<RE::TESObjectREFR*>(a_this)->As<RE::Actor>();
			if (actor && IsRiddenMount(actor)) {
				SKSE::log::info("{} IN    {}{}", Clock(), a_eventName.c_str() ? a_eventName.c_str() : "", result ? "" : "  (NOT ACCEPTED)");
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
				if (actor && IsRiddenMount(actor)) {
					const std::string_view tag{ a_event->tag.c_str() ? a_event->tag.c_str() : "" };
					if (std::ranges::none_of(kQuietOut, [&](std::string_view q) { return tag == q; })) {
						SKSE::log::info("{} OUT   {} {}", Clock(), tag, a_event->payload.c_str() ? a_event->payload.c_str() : "");
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
			if (IsRiddenMount(a_this)) {
				Sample(a_this);
			} else if (g_lastMount == a_this->GetFormID() && !RiddenMount()) {
				SKSE::log::info("{} RIDE end", Clock());
				Disarm("ride end");
				g_watchDone = false;
				g_lastMount = 0;
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenMountTrace 1.5.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::log::info("camera ids: 0 first person, 9 third person, 10 mount (horse camera), 11 bleedout, 12 dragon");

	// Character's vtables: [0] TESForm/Actor, [2] BSTEventSink<BSAnimationGraphEvent>, [3] IAnimationGraphManagerHolder.
	REL::Relocation<std::uintptr_t> actorVtbl{ RE::VTABLE_Character[0] };
	CharacterUpdate::func = actorVtbl.write_vfunc(0xAD, CharacterUpdate::thunk);
	REL::Relocation<std::uintptr_t> sinkVtbl{ RE::VTABLE_Character[2] };
	GraphEventSink::func = sinkVtbl.write_vfunc(0x1, GraphEventSink::thunk);
	REL::Relocation<std::uintptr_t> graphVtbl{ RE::VTABLE_Character[3] };
	NotifyAnimationGraph::func = graphVtbl.write_vfunc(0x1, NotifyAnimationGraph::thunk);
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		if (a_msg->type == SKSE::MessagingInterface::kDataLoaded) {
			REL::Offset2ID o2i;
			g_offsets.assign(o2i.begin(), o2i.end());
			std::ranges::sort(g_offsets, {}, &REL::IDDB::mapping_t::offset);
			SKSE::log::info("address library: {} IDs", g_offsets.size());
			SKSE::AllocTrampoline(28);
			HookRotationSite<1>(0x3EF);
			HookRotationSite<2>(0x632);
		}
	});
	SKSE::log::info("Character Update, graph event sink and NotifyAnimationGraph hooked");
	return true;
}
