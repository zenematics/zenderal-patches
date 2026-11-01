#include "pch.h"

// Improved Camera SE 1.1.2.4228, ImprovedCameraSE::TranslateCamera():
//
//     auto upDisplacement = (sneaking ? 0.0f : eyeBoneNode->local.translate.z) + HighHeelsOffset;
//     if (playerState->IsWeaponDrawn())
//         upDisplacement = 0.0f;
//
// so the first-person camera sits higher whenever the weapon is away, and moves in a single
// frame when the weapon state flips - the snap at the end of every sheathe. The inlined
// IsWeaponDrawn() check ends in `jne +4` then `xorps xmm11, xmm11` (upDisplacement = 0):
//   Mode=always : NOP the xorps  -> the raise applies with the weapon drawn too
//   Mode=never  : NOP the jne    -> every path falls into the xorps, no raise at all
//   Mode=off    : leave Improved Camera alone
// The bytes around it are verified first, so any other Improved Camera build is left alone.
//
// Debug=1 logs camera / eye-bone / head heights for 90 frames after every weapon-state change.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 1, 0, 0 },
	.Name = "ZenICSheatheFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto           kIniPath = L"Data/SKSE/Plugins/ZenICSheatheFix.ini";
	constexpr auto           kModule = L"ImprovedCameraSE.dll";
	constexpr std::uintptr_t kCheckRVA = 0x78276;
	constexpr std::uintptr_t kJneRVA = 0x78280;
	constexpr std::uintptr_t kXorpsRVA = 0x78282;

	// je; sub eax,1; je; cmp eax,1; jne +4;  xorps xmm11,xmm11  ; lea rdx,[rsp+0E8h]
	constexpr std::array<std::uint8_t, 24> kExpected{
		0x74, 0x0A, 0x83, 0xE8, 0x01, 0x74, 0x05, 0x83, 0xF8, 0x01, 0x75, 0x04,
		0x45, 0x0F, 0x57, 0xDB,
		0x48, 0x8D, 0x94, 0x24, 0xE8, 0x00, 0x00, 0x00
	};
	constexpr std::array<std::uint8_t, 4> kNop4{ 0x0F, 0x1F, 0x40, 0x00 };  // nop dword ptr [rax+0]
	constexpr std::array<std::uint8_t, 2> kNop2{ 0x66, 0x90 };              // xchg ax,ax

	// ImprovedCameraSE::GetHeadRotation(), weapon-drawn branch:
	//     if (Headbob().bCombat) { *rotation = fRotationCombat; return false; }  // "Disabled to figure out why weapon node is acting wonky."
	// i.e. head bob never follows the head with a weapon out, so enabling head bob makes the camera
	// switch from fixed to head-following the frame a sheathe ends. CombatHeadbob=1 replaces the
	// branch (20 bytes, up to the shared `return false` tail at +792A0) with a jump to a stub that
	// returns true when bCombat is set.
	constexpr std::uintptr_t kDrawnBranchRVA = 0x7928C;
	constexpr std::uintptr_t kReturnTrueTailRVA = 0x79281;   // mov rbx,[rsp+40h]; add rsp,30h; pop rdi; ret  (al already 1)
	constexpr std::uintptr_t kReturnFalseTailRVA = 0x792A0;  // mov rbx,[rsp+40h]; xor al,al; ...; ret
	constexpr std::array<std::uint8_t, 27> kDrawnBranch{
		0x48, 0x8B, 0x07,                                // mov rax,[rdi]            (m_pluginConfig)
		0x80, 0xB8, 0xA8, 0x02, 0x00, 0x00, 0x00,        // cmp byte [rax+2A8h],0    (Headbob().bCombat)
		0x74, 0x08,                                      // je  +792A0
		0x8B, 0x80, 0xBC, 0x02, 0x00, 0x00,              // mov eax,[rax+2BCh]       (fRotationCombat)
		0x89, 0x03,                                      // mov [rbx],eax
		0x48, 0x8B, 0x5C, 0x24, 0x40, 0x32, 0xC0         // +792A0: mov rbx,[rsp+40h]; xor al,al
	};
	constexpr std::array<std::uint8_t, 13> kReturnTrueTail{
		0xB0, 0x01, 0x48, 0x8B, 0x5C, 0x24, 0x40, 0x48, 0x83, 0xC4, 0x30, 0x5F, 0xC3  // +7927F: mov al,1; ...; ret
	};

	bool g_debug{ false };

	void AppendAbsJmp(std::vector<std::uint8_t>& a_code, std::uintptr_t a_target)
	{
		a_code.insert(a_code.end(), { 0xFF, 0x25, 0x00, 0x00, 0x00, 0x00 });  // jmp [rip+0]
		for (int i = 0; i < 8; ++i) {
			a_code.push_back(static_cast<std::uint8_t>(a_target >> (i * 8)));
		}
	}

	void PatchCombatHeadbob(std::uintptr_t a_module);

	bool Write(std::uintptr_t a_addr, const std::uint8_t* a_bytes, std::size_t a_size)
	{
		auto* target = reinterpret_cast<void*>(a_addr);
		DWORD oldProtect{};
		if (!::VirtualProtect(target, a_size, PAGE_EXECUTE_READWRITE, &oldProtect)) {
			SKSE::log::error("VirtualProtect failed ({}) - NOT patched", ::GetLastError());
			return false;
		}
		std::memcpy(target, a_bytes, a_size);
		::VirtualProtect(target, a_size, oldProtect, &oldProtect);
		::FlushInstructionCache(::GetCurrentProcess(), target, a_size);
		return true;
	}

	void Patch()
	{
		wchar_t modeBuf[16]{};
		::GetPrivateProfileStringW(L"General", L"Mode", L"always", modeBuf, 16, kIniPath);
		std::wstring mode{ modeBuf };
		std::ranges::transform(mode, mode.begin(), ::towlower);
		g_debug = ::GetPrivateProfileIntW(L"General", L"Debug", 0, kIniPath) != 0;
		SKSE::log::info("Mode={} Debug={}", mode == L"never" ? "never" : mode == L"off" ? "off" : "always", g_debug);

		if (mode == L"off") {
			return;
		}

		const auto module = reinterpret_cast<std::uintptr_t>(::GetModuleHandleW(kModule));
		if (!module) {
			SKSE::log::info("ImprovedCameraSE.dll not loaded - nothing to do");
			return;
		}
		if (std::memcmp(reinterpret_cast<const void*>(module + kCheckRVA), kExpected.data(), kExpected.size()) != 0) {
			SKSE::log::warn("ImprovedCameraSE.dll bytes at RVA {:X} do not match build 1.1.2.4228 - NOT patched", kCheckRVA);
			return;
		}

		if (mode == L"never") {
			if (Write(module + kJneRVA, kNop2.data(), kNop2.size())) {
				SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: camera eye-height raise never applies", kJneRVA);
			}
		} else if (Write(module + kXorpsRVA, kNop4.data(), kNop4.size())) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: camera eye-height raise now also applies with the weapon drawn", kXorpsRVA);
		}

		if (::GetPrivateProfileIntW(L"General", L"CombatHeadbob", 0, kIniPath) != 0) {
			PatchCombatHeadbob(module);
		}
	}

	void PatchCombatHeadbob(std::uintptr_t a_module)
	{
		if (std::memcmp(reinterpret_cast<const void*>(a_module + kDrawnBranchRVA), kDrawnBranch.data(), kDrawnBranch.size()) != 0 ||
			std::memcmp(reinterpret_cast<const void*>(a_module + kReturnTrueTailRVA - 2), kReturnTrueTail.data(), kReturnTrueTail.size()) != 0) {
			SKSE::log::warn("GetHeadRotation bytes do not match build 1.1.2.4228 - combat head bob NOT patched");
			return;
		}

		// stub: if (!bCombat) return false; *rotation = fRotationCombat; return true;
		std::vector<std::uint8_t> stub{
			0x48, 0x8B, 0x07,                          // mov rax,[rdi]
			0x80, 0xB8, 0xA8, 0x02, 0x00, 0x00, 0x00,  // cmp byte [rax+2A8h],0
			0x74, 0x00,                                // je  false  (patched below)
			0x8B, 0x80, 0xBC, 0x02, 0x00, 0x00,        // mov eax,[rax+2BCh]
			0x89, 0x03,                                // mov [rbx],eax
			0xB0, 0x01                                 // mov al,1
		};
		AppendAbsJmp(stub, a_module + kReturnTrueTailRVA);
		stub[11] = static_cast<std::uint8_t>(stub.size() - 12);
		AppendAbsJmp(stub, a_module + kReturnFalseTailRVA);

		auto* mem = static_cast<std::uint8_t*>(::VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
		if (!mem) {
			SKSE::log::error("VirtualAlloc failed ({}) - combat head bob NOT patched", ::GetLastError());
			return;
		}
		std::memcpy(mem, stub.data(), stub.size());
		::FlushInstructionCache(::GetCurrentProcess(), mem, stub.size());

		// 20 bytes up to +792A0: 14-byte absolute jmp + 6 int3 padding (never reached)
		std::vector<std::uint8_t> site;
		AppendAbsJmp(site, reinterpret_cast<std::uintptr_t>(mem));
		site.resize(kReturnFalseTailRVA - kDrawnBranchRVA, 0xCC);
		if (Write(a_module + kDrawnBranchRVA, site.data(), site.size())) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: head bob now follows the head with the weapon drawn when Combat is enabled", kDrawnBranchRVA);
		}
	}

	// ---------------------------------------------------------------- debug trace

	RE::NiAVObject* Find(RE::NiAVObject* a_root, std::string_view a_name)
	{
		return a_root ? a_root->GetObjectByName(a_name) : nullptr;
	}

	void Trace()
	{
		static int           s_framesLeft{ 0 };
		static int           s_frame{ 0 };
		static std::uint32_t s_lastState{ 0xFF };

		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* camera = RE::PlayerCamera::GetSingleton();
		if (!player || !camera || !camera->IsInFirstPerson() || !camera->cameraRoot) {
			return;
		}

		const auto state = static_cast<std::uint32_t>(player->AsActorState()->GetWeaponState());
		if (state != s_lastState) {
			SKSE::log::info("---- weapon state {} -> {}", s_lastState, state);
			s_lastState = state;
			s_framesLeft = 90;
			s_frame = 0;
		}
		if (s_framesLeft <= 0) {
			return;
		}
		--s_framesLeft;

		auto* fp = player->Get3D(true);
		auto* tp = player->Get3D(false);
		auto* eye1 = Find(fp, "NPCEyeBone"sv);
		auto* cam1 = Find(fp, "Camera1st [Cam1]"sv);
		auto* head3 = Find(tp, "NPC Head [Head]"sv);
		const float playerZ = player->GetPositionZ();

		SKSE::log::info(
			"f{:02} st{} camRoot.z={:.2f} eye1.local.z={:.2f} cam1.z={:.2f} head3.z={:.2f} fpRoot.z={:.2f} tpRoot.z={:.2f} fpScale={:.3f}",
			s_frame++, state,
			camera->cameraRoot->world.translate.z - playerZ,
			eye1 ? eye1->local.translate.z : -999.0f,
			cam1 ? cam1->world.translate.z - playerZ : -999.0f,
			head3 ? head3->world.translate.z - playerZ : -999.0f,
			fp ? fp->world.translate.z - playerZ : -999.0f,
			tp ? tp->world.translate.z - playerZ : -999.0f,
			fp ? fp->local.scale : 0.0f);
	}

	// Logs one line whenever any camera FOV / state / control value changes - for the "zoomed-in
	// first person after leaving meditation" bug. Change-only, so a meditation round trip is short.
	void TraceCameraState()
	{
		static std::string s_last;

		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* camera = RE::PlayerCamera::GetSingleton();
		auto* controls = RE::PlayerControls::GetSingleton();
		auto* controlMap = RE::ControlMap::GetSingleton();
		if (!player || !camera || !camera->currentState || !controls || !controlMap) {
			return;
		}

		auto& cam2 = camera->GetRuntimeData2();
		float nearDist = -1.0f;
		float frustumW = -1.0f;
		if (camera->cameraRoot && camera->cameraRoot->children.size() > 0) {
			if (auto* ni = netimmerse_cast<RE::NiCamera*>(camera->cameraRoot->children[0].get())) {
				auto& f = ni->GetRuntimeData2().viewFrustum;
				nearDist = f.fNear;
				frustumW = f.fRight - f.fLeft;
			}
		}
		static REL::Relocation<float*> fDefaultWorldFOV{ REL::RelocationID(512129, 388785) };

		auto line = std::format(
			"cam={} worldFOV={:.2f} fpFOV={:.2f} defFOV={:.2f} near={:.2f} frustumW={:.4f} bowZoom={} povScript={} move={} look={} fight={} drawn={} alpha={:.2f}",
			static_cast<std::uint32_t>(camera->currentState->id), cam2.worldFOV, cam2.firstPersonFOV, *fDefaultWorldFOV,
			nearDist, frustumW, cam2.bowZoomedIn, controls->data.povScriptMode,
			controlMap->IsMovementControlsEnabled(), controlMap->IsLookingControlsEnabled(), controlMap->IsFightingControlsEnabled(),
			player->AsActorState()->IsWeaponDrawn(), player->GetAlpha());
		if (line != s_last) {
			SKSE::log::info("[cam] {}", line);
			s_last = std::move(line);
		}
	}

	// HUDMenu::AdvanceMovie runs once per frame; used only as a per-frame tick for the trace.
	struct HUDAdvanceMovie
	{
		static void thunk(RE::HUDMenu* a_this, float a_interval, std::uint32_t a_currentTime)
		{
			func(a_this, a_interval, a_currentTime);
			Trace();
			TraceCameraState();
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			Patch();
			if (g_debug) {
				REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_HUDMenu[0] };
				HUDAdvanceMovie::func = vtbl.write_vfunc(0x05, HUDAdvanceMovie::thunk);
				SKSE::log::info("Debug trace installed");
			}
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenICSheatheFix 1.1.0 loading, runtime {}", REL::Module::get().version().string());
	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);
	return true;
}
