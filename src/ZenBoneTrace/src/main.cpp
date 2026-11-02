#include "pch.h"

#include <Windows.h>
#include <TlHelp32.h>
#include <atomic>
#include <chrono>
#include <thread>

// Testing tool, not part of the list. The pistol ramrod reload (src/PistolRamrodReload) played in game with the right
// arm out to the side while its clip, decoded offline, keeps the hand at the muzzle. This logs what the game actually
// poses, so the two can be compared frame by frame:
//   FIRE  each player spell-fire action (SKSE ActionEvent: a pistol shot is a staff release) starts a window;
//   EV    every animation graph event the player's graphs send while the window is open (clip annotations such as
//         AnimObjLoad, the graph's own MLh_ triggers), with its time since the shot;
//   ROOT  every frame: the third-person 3D root's world rotation (row-major entries), translation and scale;
//   BONE  every frame: world position of each bone in kBones, and the local rotation (row-major) of kLocalBones.
//   VAR   every frame (1.1.0): the graph variables in kVars: which hand the two-staff blend favours (`CastBlend`,
//         `CastBlendDamped`, -1 left .. +1 right), the casting flags, the hand types and the reload's arm variables.
//         1.1.0 also logs both arms' and both attach nodes' local rotations, for a reload with a pistol in each hand.
//   VIS   every frame (1.2.0): each child hanging on the attach nodes in kVisNodes (the guns' meshes, the props): name,
//         hidden flag, world scale and distance from the node; and the node's own hidden flag and world scale. The
//         two-pistol reload made the guns vanish in game while every clip track is unit-scale.
//   FP    every frame (1.3.0): the first-person skeleton's hands, attach nodes and AnimObject nodes in its camera's
//         frame (x right, y forward, z up), hidden flags, and the meshes on Weapon / Shield (first person only).
//   WATCH (1.4.0): a hardware write watch (DR0 / DR1 on every thread while the window is open) on the first-person
//         Weapon / Shield nodes' flags. The two-pistol reload's right-gun clip hid both in first person, and nothing in
//         the clips, the patches or Improved Camera's source sets that flag: each write that flips kHidden (and the
//         first 3 writes per node) is logged with the writing code (module + RVA, nearest Address Library ID) and the
//         stack. VAR also logs LeftItemCharge / RightItemCharge (the Flintlock holster drains the tucked gun's).
//   DRY   (1.5.0) the mod event ZP_PistolDryReload (the Flintlock script asks for the reload of an empty gun, played by
//         graph events, no shot) opens the window like a shot, so the graph's response and the first-person arms show.
//   EQUIP (1.5.0) the player equipping or unequipping a weapon opens the window too (a dagger beside a pistol took 2-3
//         equips to show): VIS / FP then show whether its mesh hangs on Weapon / Shield and whether the node is hidden.
//   CAST  (1.6.0) the start of a player spell cast (SKSE ActionEvent kSpellCast) opens the window too, and
//   IN    (1.6.0) every event sent into the player's graphs (IAnimationGraphManagerHolder::NotifyAnimationGraph: the
//         engine's idle/action events and Papyrus' Debug.SendAnimationEvent alike) while the window is open, and whether
//         the graph took it. VAR also logs NotCasting / bWantCastLeft / bWantCastRight: the engine never sends the cast
//         events by name, and the dry reload's graph events left the magic graph's casting state within a frame.
// Log: My Games/Skyrim Special Edition/SKSE/ZenBoneTrace.log

SKSEPluginInfo(
	.Version = REL::Version{ 1, 6, 1, 0 },
	.Name = "ZenBoneTrace"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr double kWindowSeconds = 3.2;
	constexpr std::array kBones{ "NPC Root [Root]"sv, "NPC Pelvis [Pelv]"sv, "NPC Spine2 [Spn2]"sv, "NPC Head [Head]"sv,
		"NPC R Clavicle [RClv]"sv, "NPC R UpperArm [RUar]"sv, "NPC R Forearm [RLar]"sv, "NPC R Hand [RHnd]"sv,
		"AnimObjectR"sv, "Weapon"sv, "NPC L UpperArm [LUar]"sv, "NPC L Forearm [LLar]"sv, "NPC L Hand [LHnd]"sv, "Shield"sv };
	constexpr std::array kLocalBones{ "NPC R Clavicle [RClv]"sv, "NPC R UpperArm [RUar]"sv, "NPC R Forearm [RLar]"sv,
		"NPC R Hand [RHnd]"sv, "NPC R ForearmTwist1 [RLt1]"sv, "Weapon"sv, "NPC L Clavicle [LClv]"sv, "NPC L UpperArm [LUar]"sv,
		"NPC L Forearm [LLar]"sv, "NPC L Hand [LHnd]"sv, "NPC L ForearmTwist1 [LLt1]"sv, "Shield"sv };
	constexpr std::array kFloatVars{ "CastBlend"sv, "CastBlendDamped"sv, "fZenPistolRightArmIdle"sv,
		"fZenPistolLeftArmIdle"sv, "fZenPistolDualReload"sv };
	constexpr std::array kVisNodes{ "Weapon"sv, "Shield"sv, "AnimObjectR"sv, "AnimObjectL"sv };
	constexpr std::array kFirstPersonBones{ "NPC R Hand [RHnd]"sv, "Weapon"sv, "NPC L Hand [LHnd]"sv, "Shield"sv,
		"AnimObjectR"sv, "AnimObjectL"sv };
	constexpr std::array kBoolVars{ "IsCastingLeft"sv, "IsCastingRight"sv, "IsCastingDual"sv, "NotCasting"sv,
		"bWantCastLeft"sv, "bWantCastRight"sv };
	constexpr std::array kIntVars{ "iLeftHandType"sv, "iRightHandType"sv };

	using Clock = std::chrono::steady_clock;
	std::optional<Clock::time_point> g_fire;

	double SinceFire()
	{
		return g_fire ? std::chrono::duration<double>(Clock::now() - *g_fire).count() : -1.0;
	}

	bool Open()
	{
		const double t = SinceFire();
		return t >= 0.0 && t <= kWindowSeconds;
	}

	std::string Rot(const RE::NiMatrix3& m)
	{
		return std::format("{:.5f} {:.5f} {:.5f} {:.5f} {:.5f} {:.5f} {:.5f} {:.5f} {:.5f}", m.entry[0][0], m.entry[0][1],
			m.entry[0][2], m.entry[1][0], m.entry[1][1], m.entry[1][2], m.entry[2][0], m.entry[2][1], m.entry[2][2]);
	}

	// 1.4.0 write watch. The handler only fills g_hits; PlayerUpdate formats and logs them on the main thread.
	constexpr int kMaxHits = 96;
	constexpr int kFrames = 28;

	struct Hit
	{
		std::atomic<bool> ready{ false };
		double            t{ 0.0 };
		int               node{ 0 };
		std::uint32_t     before{ 0 };
		std::uint32_t     after{ 0 };
		DWORD             tid{ 0 };
		void*             rip{ nullptr };
		USHORT            n{ 0 };
		void*             frames[kFrames]{};
	};

	std::array<std::uint32_t*, 2>              g_watched{};  // the first-person Weapon / Shield flags
	std::array<std::atomic<std::uint32_t>, 2> g_lastFlags{};
	std::array<std::atomic<int>, 2>           g_writes{};
	std::array<Hit, kMaxHits>                 g_hits{};
	std::atomic<int>                          g_hitCount{ 0 };
	int                                       g_flushed{ 0 };
	bool                                      g_armed{ false };
	bool                                      g_handlerAdded{ false };
	std::vector<REL::IDDB::mapping_t>         g_offsets;  // Address Library, sorted by offset

	LONG CALLBACK WatchHandler(EXCEPTION_POINTERS* a_info)
	{
		if (a_info->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP) {
			return EXCEPTION_CONTINUE_SEARCH;
		}
		auto*      ctx = a_info->ContextRecord;
		const auto dr6 = ctx->Dr6;
		if (!(dr6 & 0x3)) {
			return EXCEPTION_CONTINUE_SEARCH;
		}
		for (int i = 0; i < 2; ++i) {
			if (!(dr6 & (1ull << i)) || !g_watched[i]) {
				continue;
			}
			const std::uint32_t after = *g_watched[i];
			const std::uint32_t before = g_lastFlags[i].exchange(after);
			if (!((before ^ after) & 1) && g_writes[i].fetch_add(1) >= 3) {
				continue;
			}
			const int slot = g_hitCount.fetch_add(1);
			if (slot >= kMaxHits) {
				continue;
			}
			auto& h = g_hits[slot];
			h.t = SinceFire();
			h.node = i;
			h.before = before;
			h.after = after;
			h.tid = GetCurrentThreadId();
			h.rip = reinterpret_cast<void*>(ctx->Rip);
			h.n = RtlCaptureStackBackTrace(0, kFrames, h.frames, nullptr);
			h.ready.store(true, std::memory_order_release);
		}
		ctx->Dr6 = 0;
		return EXCEPTION_CONTINUE_EXECUTION;
	}

	// "SkyrimSE.exe+0x1234 (ID 5678 +0x10)" / "Some.dll+0x1234"
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
		const auto rva = reinterpret_cast<std::uintptr_t>(a_addr) - reinterpret_cast<std::uintptr_t>(mod);
		std::string out = std::format("{}+0x{:X}", name, rva);
		if (mod == GetModuleHandleW(nullptr) && !g_offsets.empty()) {
			auto it = std::ranges::upper_bound(g_offsets, rva, {}, &REL::IDDB::mapping_t::offset);
			if (it != g_offsets.begin()) {
				--it;
				out += std::format(" (ID {} +0x{:X})", it->id, rva - it->offset);
			}
		}
		return out;
	}

	// Sets (or clears) DR0 / DR1 on every thread of the process from a helper thread, one thread suspended at a time
	// (nothing is allocated while one is). The caller blocks in join() and is set like the others.
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
						ctx.Dr7 &= ~0x00FF000Full;  // L0-G1, RW0/LEN0, RW1/LEN1
						ctx.Dr0 = 0;
						ctx.Dr1 = 0;
						if (a_on && g_watched[0]) {
							ctx.Dr0 = reinterpret_cast<DWORD64>(g_watched[0]);
							ctx.Dr7 |= 0x1ull | (0x1ull << 16) | (0x3ull << 18);  // L0, write, 4 bytes
						}
						if (a_on && g_watched[1]) {
							ctx.Dr1 = reinterpret_cast<DWORD64>(g_watched[1]);
							ctx.Dr7 |= 0x4ull | (0x1ull << 20) | (0x3ull << 22);  // L1, write, 4 bytes
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

	std::uint32_t* FlagsOf(RE::NiAVObject* a_obj)
	{
		return a_obj ? reinterpret_cast<std::uint32_t*>(std::addressof(a_obj->GetFlags())) : nullptr;
	}

	void Arm(RE::NiAVObject* a_fp)
	{
		const std::array want{ FlagsOf(a_fp->GetObjectByName("Weapon"sv)), FlagsOf(a_fp->GetObjectByName("Shield"sv)) };
		if (g_armed && want == g_watched) {
			return;
		}
		if (!g_handlerAdded) {
			AddVectoredExceptionHandler(1, WatchHandler);
			g_handlerAdded = true;
		}
		g_watched = want;
		for (int i = 0; i < 2; ++i) {
			g_lastFlags[i] = g_watched[i] ? *g_watched[i] : 0;
			g_writes[i] = 0;
		}
		for (auto& h : g_hits) {
			h.ready = false;
		}
		g_hitCount = 0;
		g_flushed = 0;
		SetWatch(true);
		g_armed = true;
		SKSE::log::info("WATCH armed: Weapon flags {} = 0x{:X}, Shield flags {} = 0x{:X}", static_cast<void*>(g_watched[0]),
			g_lastFlags[0].load(), static_cast<void*>(g_watched[1]), g_lastFlags[1].load());
	}

	void Disarm()
	{
		if (g_armed) {
			SetWatch(false);
			g_armed = false;
			SKSE::log::info("WATCH disarmed");
		}
	}

	void FlushHits()
	{
		const int count = std::min(g_hitCount.load(), kMaxHits);
		while (g_flushed < count && g_hits[g_flushed].ready.load(std::memory_order_acquire)) {
			const auto& h = g_hits[g_flushed++];
			std::string line = std::format("WATCH {:.4f} {} flags 0x{:X} -> 0x{:X} hidden {} -> {} thread {} at {}", h.t,
				h.node == 0 ? "Weapon" : "Shield", h.before, h.after, h.before & 1, h.after & 1, h.tid, Where(h.rip));
			for (USHORT i = 0; i < h.n; ++i) {
				line += std::format("\n      #{} {}", i, Where(h.frames[i]));
			}
			SKSE::log::info("{}", line);
		}
	}

	struct ActionSink : RE::BSTEventSink<SKSE::ActionEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const SKSE::ActionEvent* a_event, RE::BSTEventSource<SKSE::ActionEvent>*) override
		{
			if (!a_event || !a_event->actor || !a_event->actor->IsPlayerRef()) {
				return RE::BSEventNotifyControl::kContinue;
			}
			const bool fire = a_event->type == SKSE::ActionEvent::Type::kSpellFire;
			if (fire || a_event->type == SKSE::ActionEvent::Type::kSpellCast) {
				g_fire = Clock::now();
				const auto* src = a_event->sourceForm;
				SKSE::log::info("{} slot {} source {:08X} '{}'", fire ? "FIRE" : "CAST", a_event->slot.underlying(),
					src ? src->GetFormID() : 0, src ? src->GetName() : "");
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	struct GraphSink : RE::BSTEventSink<RE::BSAnimationGraphEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const RE::BSAnimationGraphEvent* a_event, RE::BSTEventSource<RE::BSAnimationGraphEvent>*) override
		{
			if (a_event && Open()) {
				SKSE::log::info("EV {:.4f} {} {}", SinceFire(), a_event->tag.c_str() ? a_event->tag.c_str() : "",
					a_event->payload.c_str() ? a_event->payload.c_str() : "");
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	GraphSink g_graphSink;

	// 1.6.0: events into the player's graphs. PlayerCharacter's vtable [3] is IAnimationGraphManagerHolder, slot 1.
	struct NotifyGraph
	{
		static bool thunk(RE::IAnimationGraphManagerHolder* a_this, const RE::BSFixedString& a_eventName)
		{
			const bool result = func(a_this, a_eventName);
			if (Open()) {
				SKSE::log::info("IN {:.4f} {}{}", SinceFire(), a_eventName.c_str() ? a_eventName.c_str() : "",
					result ? "" : "  (not accepted)");
			}
			return result;
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct EquipSink : RE::BSTEventSink<RE::TESEquipEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const RE::TESEquipEvent* a_event, RE::BSTEventSource<RE::TESEquipEvent>*) override
		{
			if (a_event && a_event->actor && a_event->actor->IsPlayerRef()) {
				const auto* form = RE::TESForm::LookupByID(a_event->baseObject);
				if (form && form->IsWeapon()) {
					g_fire = Clock::now();
					SKSE::log::info("EQUIP {} {:08X} '{}'", a_event->equipped ? "on" : "off", a_event->baseObject, form->GetName());
				}
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	struct ModSink : RE::BSTEventSink<SKSE::ModCallbackEvent>
	{
		RE::BSEventNotifyControl ProcessEvent(const SKSE::ModCallbackEvent* a_event, RE::BSTEventSource<SKSE::ModCallbackEvent>*) override
		{
			if (a_event && a_event->eventName == "ZP_PistolDryReload"sv) {
				g_fire = Clock::now();
				SKSE::log::info("DRY hand {} (reload asked for, no shot)", a_event->strArg.c_str() ? a_event->strArg.c_str() : "");
			}
			return RE::BSEventNotifyControl::kContinue;
		}
	};

	void AttachGraphSink()
	{
		if (auto* player = RE::PlayerCharacter::GetSingleton()) {
			player->RemoveAnimationGraphEventSink(&g_graphSink);
			const bool ok = player->AddAnimationGraphEventSink(&g_graphSink);
			SKSE::log::info("graph sink {}", ok ? "attached" : "NOT attached");
		}
	}

	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_this, float a_delta)
		{
			func(a_this, a_delta);
			if (!Open()) {
				if (g_armed) {
					Disarm();
					FlushHits();
				}
				return;
			}
			auto* root = a_this->Get3D(false);
			if (!root) {
				return;
			}
			if (auto* fp1 = a_this->Get3D(true); fp1 && fp1 != root) {
				Arm(fp1);
			}
			FlushHits();
			const double t = SinceFire();
			const auto&  rw = root->world;
			// 1.6.1: the camera's state (Get3D(true) == Get3D(false) was never true, so 1.0-1.6 logged cam1st=false
			// in first person too)
			const auto* cam1 = RE::PlayerCamera::GetSingleton();
			const bool  firstPerson = cam1 && cam1->currentState && cam1->currentState->id == RE::CameraState::kFirstPerson;
			SKSE::log::info("ROOT {:.4f} {} {:.3f} {:.3f} {:.3f} {:.4f} cam1st={}", t, Rot(rw.rotate), rw.translate.x,
				rw.translate.y, rw.translate.z, rw.scale, firstPerson);
			std::string line = std::format("BONE {:.4f}", t);
			for (auto name : kBones) {
				if (auto* obj = root->GetObjectByName(name)) {
					line += std::format(" | {} {:.3f} {:.3f} {:.3f}", name, obj->world.translate.x, obj->world.translate.y,
						obj->world.translate.z);
				}
			}
			SKSE::log::info("{}", line);
			std::string vars = std::format("VAR {:.4f}", t);
			for (auto name : kFloatVars) {
				float v = 0.0f;
				vars += a_this->GetGraphVariableFloat(RE::BSFixedString(name), v) ? std::format(" {}={:.3f}", name, v) :
				                                                                     std::format(" {}=?", name);
			}
			for (auto name : kBoolVars) {
				bool v = false;
				vars += a_this->GetGraphVariableBool(RE::BSFixedString(name), v) ? std::format(" {}={}", name, v ? 1 : 0) :
				                                                                    std::format(" {}=?", name);
			}
			for (auto name : kIntVars) {
				std::int32_t v = 0;
				vars += a_this->GetGraphVariableInt(RE::BSFixedString(name), v) ? std::format(" {}={}", name, v) :
				                                                                   std::format(" {}=?", name);
			}
			auto* avo = a_this->AsActorValueOwner();
			vars += std::format(" LeftItemCharge={:.1f} RightItemCharge={:.1f}", avo->GetActorValue(RE::ActorValue::kLeftItemCharge),
				avo->GetActorValue(RE::ActorValue::kRightItemCharge));
			SKSE::log::info("{}", vars);
			for (auto name : kLocalBones) {
				if (auto* obj = root->GetObjectByName(name)) {
					SKSE::log::info("LOCAL {:.4f} {} {} {:.3f} {:.3f} {:.3f}", t, name, Rot(obj->local.rotate),
						obj->local.translate.x, obj->local.translate.y, obj->local.translate.z);
				}
			}
			std::string vis = std::format("VIS {:.4f}", t);
			for (auto name : kVisNodes) {
				auto* obj = root->GetObjectByName(name);
				if (!obj) {
					continue;
				}
				vis += std::format(" | {} hidden={} scale={:.3f}", name, obj->GetFlags().any(RE::NiAVObject::Flag::kHidden) ? 1 : 0,
					obj->world.scale);
				if (auto* node = obj->AsNode()) {
					for (auto& child : node->GetChildren()) {
						if (!child) {
							continue;
						}
						const auto d = child->world.translate - obj->world.translate;
						vis += std::format(" [{} hidden={} scale={:.3f} dist={:.1f}]", child->name.c_str() ? child->name.c_str() : "",
							child->GetFlags().any(RE::NiAVObject::Flag::kHidden) ? 1 : 0, child->world.scale, d.Length());
					}
				}
			}
			SKSE::log::info("{}", vis);
			// 1.3.0: the first-person skeleton, positions in its camera's frame (x right, y forward, z up)
			auto* fp = a_this->Get3D(true);
			auto* cam = fp && fp != root ? fp->GetObjectByName("Camera1st [Cam1]"sv) : nullptr;
			if (cam) {
				std::string line1 = std::format("FP {:.4f}", t);
				for (auto name : kFirstPersonBones) {
					auto* obj = fp->GetObjectByName(name);
					if (!obj) {
						continue;
					}
					const auto p = cam->world.rotate.Transpose() * (obj->world.translate - cam->world.translate);
					line1 += std::format(" | {} {:.1f} {:.1f} {:.1f} hidden={}", name, p.x, p.y, p.z,
						obj->GetFlags().any(RE::NiAVObject::Flag::kHidden) ? 1 : 0);
					if (auto* node = obj->AsNode(); node && (name == "Weapon"sv || name == "Shield"sv)) {
						for (auto& child : node->GetChildren()) {
							if (child) {
								line1 += std::format(" [{} hidden={} scale={:.3f}]", child->name.c_str() ? child->name.c_str() : "",
									child->GetFlags().any(RE::NiAVObject::Flag::kHidden) ? 1 : 0, child->world.scale);
							}
						}
					}
				}
				SKSE::log::info("{}", line1);
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenBoneTrace 1.6.1 loading, runtime {}", REL::Module::get().version().string());
	REL::Relocation<std::uintptr_t> playerVtbl{ RE::VTABLE_PlayerCharacter[0] };
	PlayerUpdate::func = playerVtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
	REL::Relocation<std::uintptr_t> holderVtbl{ RE::VTABLE_PlayerCharacter[3] };
	NotifyGraph::func = holderVtbl.write_vfunc(0x1, NotifyGraph::thunk);
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* a_msg) {
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			{
				REL::Offset2ID o2i;
				g_offsets.assign(o2i.begin(), o2i.end());
				std::ranges::sort(g_offsets, {}, &REL::IDDB::mapping_t::offset);
				SKSE::log::info("address library: {} IDs", g_offsets.size());
				static EquipSink equips;
				if (auto* holder = RE::ScriptEventSourceHolder::GetSingleton()) {
					holder->AddEventSink<RE::TESEquipEvent>(&equips);
				}
				static ModSink mods;
				if (auto* src = SKSE::GetModCallbackEventSource()) {
					src->AddEventSink(&mods);
				}
				static ActionSink actions;
				if (auto* src = SKSE::GetActionEventSource()) {
					src->AddEventSink(&actions);
					SKSE::log::info("action sink registered");
				}
			}
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			AttachGraphSink();
			break;
		default:
			break;
		}
	});
	return true;
}
