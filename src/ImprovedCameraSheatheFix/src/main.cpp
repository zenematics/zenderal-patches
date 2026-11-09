#include "pch.h"

#include <TlHelp32.h>
#define SMOOTHCAM_API_COMMONLIB
#include "SmoothCamAPI.h"
#include <atomic>
#include <cmath>
#include <span>
#include <thread>

// ---------------------------------------------------------------------------------------------
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
//   Mode=off    : leave Improved Camera alone (every build, every patch below)
// The bytes around it are verified first, so any other Improved Camera build is left alone.
//
// ---------------------------------------------------------------------------------------------
// Improved Camera SE 2.0.0.2226 (TimeDateStamp 6ADFE470), CAMERA::Manager::UpdateFOV() (RVA 36700),
// called every frame from CAMERA::Manager::Update():
//
//   it lerps PlayerCamera::worldFOV toward the active profile's FOV for Improved Camera's OWN camera
//   state (manager+1B8h) and writes it into the camera, in every state but two hard-coded ones that
//   take a hands-off path (the current FOV written back unchanged): Free (3) and Cinematic (1Dh).
//   ThirdPerson (9) is not one of them, so in third person SmoothCam's FOV offsets are overwritten
//   each frame (traced 2026-11-08: 94 vs the SmoothCam preset's 69). 2.0 has no setting for it; a
//   FOV table value <= 0 makes the code chase a stale value, not stop.
//
//     367DC  83 F8 03  0F 84 E6 02 00 00   cmp eax,3   ; je 36ACB  (hands-off)
//     367E5  83 F8 1D  0F 84 DD 02 00 00   cmp eax,1Dh ; je 36ACB
//     367EE  F3 0F 10 83 64 02 00 00       movss xmm0,[rbx+264h]  (normal path: lerp + write)
//
//   Those 18 bytes become a jump into a stub that compares eax with 3, 1Dh and every state listed
//   in [ImprovedCamera2] HandsOffFOVStates (default 9 = ThirdPerson) and jumps to 36ACB on a match,
//   else back to 367EE. Nothing else branches into the window (checked in the disassembly). The 24
//   bytes at 367DC are verified first. Re-derive the RVAs from IC's shipped .pdb with
//   `dumpbin /disasm` (symbol ?UpdateFOV@Manager@CAMERA@@) after any Improved Camera update.
//
// Improved Camera SE 2.0.0.2226, CAMERA::Manager::SetMode() (RVA 34A30):
//
//   UpdateCameraState turns Improved Camera's body action into its camera state through a jump table
//   (RVA 34404): Animation, Bathing, BoatRide, CartRide, Fish, Sit, Sleep and View all become the
//   Animation state (0Dh). For that state SetMode forces the camera into first person whenever it is
//   not already there and IC's internal camera lock (manager+18h, RaceMenu / intro cart only) is 0 -
//   nothing in the profile gates it (bEnableFakeFirstPerson = General byte +2 only ADDS forcing for the
//   other third-person states). So Immersive Interactions' "Force 3rd Person" (Game.ForceThirdPerson)
//   is undone within a frame, and sitting is first person with or without No Furniture Camera.
//
//     34B46  8B 43 38             mov eax,[rbx+38h]        (IC camera state)
//     34B49  83 F8 0D  0F 85 ..   cmp eax,0Dh ; jne        (not Animation -> generic branches)
//     34B52  83 7B 18 00  75 7E   cmp [rbx+18h],0 ; jne    (camera lock held -> generic branches)
//     34B58  48 8B CE  E8 ..      mov rcx,rsi ; call PlayerCamera::IsInFirstPerson
//     34B60  84 C0  75 08         test al,al ; jne 34B6C
//     34B64  48 8B CE  E8 ..      mov rcx,rsi ; call PlayerCamera::ForceFirstPerson   <- 5-byte NOP
//     34B6C  C6 83 35 02 00 00 00 mov byte [rbx+235h],0
//
//   ForceFirstPersonAnimations=0 (default) verifies the 45 bytes above and replaces `mov rcx,rsi ; call
//   ForceFirstPerson` with `jmp 34CFB` (= `mov eax,3`: Improved Camera not in control) + nop: in the
//   Animation state with the camera already third person IC steps aside; in first person the branch
//   runs as before (clears [235h], returns CartRide ? 1 : 0), so first-person animations are unchanged.
//   1.3.0 only NOPed the call, which left IC in mode 0 on a third-person camera. Pair it with Animation
//   (13) in HandsOffFOVStates, else IC lerps its fAnimation FOV over SmoothCam's during one.
//
// Improved Camera SE 2.0.0.2226, HOOK::MISC::ForceThirdPerson::func (RVA B3EB0) - the hook IC puts on
// the engine's PlayerCamera::ForceThirdPerson (Papyrus Game.ForceThirdPerson, furniture):
//
//     B3EC3  E8 ..                call REX::Singleton<CAMERA::Manager>::GetSingleton
//     B3EC8  48 8B D8             mov rbx,rax
//     B3ECB  E8 ..                call REX::Singleton<DLLMAIN::Plugin>::GetSingleton
//     B3ED0  48 8B 88 A8 01 00 00 mov rcx,[rax+1A8h]       (General section)
//     B3ED7  80 39 00  74 07      cmp byte [rcx],0 ; je B3EE3   (bEnableBody off -> skip)   <- je becomes jmp
//     B3EDC  C6 83 35 02 00 00 01 mov byte [rbx+235h],1    (pending third-person body)
//     B3EE3  48 83 C4 20 5B C3    add rsp,20h ; pop rbx ; ret
//
//   [235h] is set nowhere else. SetMode reads it: `if ([235h] && [B8h] == 0) { [235h] = 0; [30h] = 1;
//   thirdPerson = true; zoom offsets = -0.275 }` and UpdateCameraState locks the state to ThirdPerson (9)
//   while it is set - that is how every forced third person (a chair, Immersive Interactions' "Force 3rd
//   Person") became IC's head-camera view (mode 2; traced 2026-11-08: cam=9, ic=Animation, icMode=2).
//   TakeOverForcedThirdPerson=0 (default) turns the je into jmp after verifying the 38 bytes from B3EC3,
//   so a forced third person is a plain third person to IC, like the POV key's. The engine call itself
//   still runs.
//
// Improved Camera SE 2.0.0.2226 - the path that actually puts the head camera on a chair (found with the
// 1.4.2 hardware write watch, 2026-11-08; the hook / pending-flag paths above never ran for furniture):
//
//   The Manager embeds a Modifier struct at +20h; its byte +10h (= manager+30h) is "third-person body".
//   Every IC CameraState writes it from OnUpdate(PlayerCamera*, Modifier&) / OnExit(Modifier&) - the
//   folded OnUpdate shared by Furniture, Horse, Dragon... (`mov byte [r8+10h],1`, 3824E), FurnitureState
//   ::OnExit (39695), AnimationState::OnUpdate (3D0C1, from its own byte +8 set in OnEnter). Capture-
//   CameraState passes that byte to SetMode as r8b (`movzx ebp,r8b`, 34A48), and with it set SetMode
//   takes the third-person branch and returns mode 2 once the state's OnEnter has zoomed the third-
//   person camera to -0.275: FurnitureState::OnEnter (395FB) and AnimationState::OnEnter (3CFD3, 3D07C,
//   the latter after a ForceThirdPerson at 3D077 when the vanilla camera was first person; 3CF71 forces
//   third person for Bathing/CartRide/Dialogue/Fish/Swim/View).
//
//   ThirdPersonBody=0 (default): `movzx ebp,r8b` -> `xor ebp,ebp` so SetMode never honours the request
//   (FirstPerson state keeps mode 0/1, every other state returns 3 = IC not in control), and the five
//   zoom / force sites above become NOPs so the vanilla camera is left where the game and SmoothCam put
//   it. HandsOffFOVStates defaults to every IC state but FirstPerson for the same reason.
//
// Improved Camera SE 2.0.0.2226 - where the head camera (mode 2) sits, and its first frame (1.7.0, 2026-11-08):
//
//   CAMERA::ThirdPersonState::OnUpdate (39B60) feeds the profile's Camera/Firstperson {forward, up, right} (or its
//   Combat set with a weapon drawn; ProfileCamera at Plugin+220h) into the Manager's Modifier, and CAMERA::Manager::
//   BasePosition (35EC0) places the camera at SmoothHeadAnchor(head node) + scale * ((forward + 8) * bodyForward +
//   right * bodyRight + (up + 1) * bodyUp). The vanilla first-person camera sits on the root's axis ~120.5 up; the
//   head camera therefore starts ~10 units ahead of it (measured 8.7-10.9 with [campos]), which is the position cut a
//   bite showed. Zen.json's Camera/Firstperson/forward = -10 (main + Combat) puts the two on top of each other; the
//   same offsets reach IC's first-person state only in mode 1 (head bob), which the profile has off.
//
//   Frame order of a scripted forced third person (traced with [campos]): N - IC's Papyrus-side hook raises the
//   pending flag after the camera update, the engine is already ThirdPerson, the camera root still holds the
//   first-person transform; N+1 - IC's update consumes the flag (mode 2, ThirdPersonState entered) but writes no
//   position yet, so the vanilla ThirdPersonState's transform renders: ONE frame from behind the player; N+2 on -
//   the head camera. HoldCameraOnHeadCameraEntry=1 restores the previous frame's camera-root transform in
//   PlayerCharacter::Update (after the camera update) on exactly that frame.
//
// Improved Camera SE 2.0.0.2226 - the near plane in the head camera (1.8.0, 2026-11-09):
//
//   CAMERA::Manager::UpdateNearDistance (36BD0) sets the camera's near plane every frame. In a third-person state
//   not zoomed onto the head it writes fNearDistanceDefault (15). In IC's first-person state, and in a third-person
//   state zoomed to <= -0.27 (the head camera), it follows the profile's pitch rule instead: fNearDistanceMax (15)
//   while the camera looks less than fNearDistanceStartAngle (15 deg) down, lerping to fNearDistanceMin (4) at
//   fNearDistanceEndAngle (50 deg down); Combat set with a weapon drawn; 2.0 for the Sex camera. The smoothed
//   value (lerp 0.15/frame) goes into the NiCamera's fNear and the game's fNearDistance whenever it is more than
//   0.05 off. In the head camera the mouth is ~10 units ahead of the camera, so looking ahead the near plane at 15
//   cuts away the food and the hand for most of a bite (recording 2026-11-08 23:59). HeadCameraNearDistance caps
//   the plane at its value (default 4 = IC's own minimum) while IC's mode is 2, written after IC's update; IC's rule
//   takes the plane back the frame the head camera ends. Plain first person keeps IC's rule.
//
// Debug=1 logs camera / eye-bone / head heights for 90 frames after every weapon-state change, and
// one line whenever the vanilla camera state / FOV changes - on 2.0 with Improved Camera's own
// state and mode (manager+1B8h / +1C0h, read through REX::Singleton<CAMERA::Manager>::GetSingleton),
// plus entry loggers, a byte read-back and a hardware write watch on manager+30h / +235h.

SKSEPluginInfo(
	.Version = REL::Version{ 1, 8, 0, 0 },
	.Name = "ZenICSheatheFix"sv,
	.Author = "Zenderal"sv,
	.StructCompatibility = SKSE::StructCompatibility::Independent,
	.RuntimeCompatibility = SKSE::VersionIndependence::AddressLibrary)

namespace
{
	constexpr auto kIniPath = L"Data/SKSE/Plugins/ZenICSheatheFix.ini";
	constexpr auto kModule = L"ImprovedCameraSE.dll";

	// ------------------------------------------------------------- Improved Camera SE 1.1.2.4228
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

	// ------------------------------------------------------------- Improved Camera SE 2.0.0.2226
	constexpr std::uintptr_t kFovSiteRVA = 0x367DC;         // cmp eax,3 / je / cmp eax,1Dh / je   (18 bytes)
	constexpr std::uintptr_t kFovNormalRVA = 0x367EE;       // fall-through: lerp toward the profile FOV, write it
	constexpr std::uintptr_t kFovHandsOffRVA = 0x36ACB;     // write the current FOV back unchanged
	constexpr std::uintptr_t kManagerGetterRVA = 0x2E9C0;   // REX::Singleton<CAMERA::Manager>::GetSingleton()
	constexpr std::size_t    kFovSiteSize = 18;
	constexpr std::array<std::uint8_t, 24> kFovExpected{
		0x83, 0xF8, 0x03, 0x0F, 0x84, 0xE6, 0x02, 0x00, 0x00,  // cmp eax,3   ; je +2E6 -> 36ACB
		0x83, 0xF8, 0x1D, 0x0F, 0x84, 0xDD, 0x02, 0x00, 0x00,  // cmp eax,1Dh ; je +2DD -> 36ACB
		0xF3, 0x0F, 0x10, 0x83, 0x64, 0x02                     // movss xmm0,dword ptr [rbx+264h]
	};
	// CAMERA::Manager::SetMode, Animation-state branch (see the header comment)
	constexpr std::uintptr_t kAnimBranchRVA = 0x34B46;
	constexpr std::uintptr_t kForceFirstPersonCallRVA = 0x34B67;
	constexpr std::array<std::uint8_t, 45> kAnimBranch{
		0x8B, 0x43, 0x38,                          // mov eax,[rbx+38h]
		0x83, 0xF8, 0x0D, 0x0F, 0x85, 0x84, 0x00, 0x00, 0x00,  // cmp eax,0Dh ; jne 34BD6
		0x83, 0x7B, 0x18, 0x00, 0x75, 0x7E,        // cmp dword ptr [rbx+18h],0 ; jne 34BD6
		0x48, 0x8B, 0xCE, 0xE8, 0x40, 0xCB, 0x0E, 0x00,  // mov rcx,rsi ; call IsInFirstPerson (1216A0)
		0x84, 0xC0, 0x75, 0x08,                    // test al,al ; jne 34B6C
		0x48, 0x8B, 0xCE, 0xE8, 0xB4, 0xC9, 0x0E, 0x00,  // mov rcx,rsi ; call ForceFirstPerson (121520)
		0xC6, 0x83, 0x35, 0x02, 0x00, 0x00, 0x00   // mov byte ptr [rbx+235h],0
	};
	constexpr std::uintptr_t kAnimForceRVA = 0x34B64;  // mov rcx,rsi ; call ForceFirstPerson  (8 bytes)
	constexpr std::array<std::uint8_t, 8> kAnimReturn3{
		0xE9, 0x92, 0x01, 0x00, 0x00,  // jmp 34CFB  (mov eax,3 ; epilogue)   34CFB - 34B69 = 192h
		0x0F, 0x1F, 0x00               // nop dword ptr [rax]
	};

	// HOOK::MISC::ForceThirdPerson::func, from the Manager getter to the ret (see the header comment)
	constexpr std::uintptr_t kForceThirdPersonHookRVA = 0xB3EC3;
	constexpr std::uintptr_t kForceThirdPersonJeRVA = 0xB3EDA;
	constexpr std::array<std::uint8_t, 38> kForceThirdPersonHook{
		0xE8, 0xF8, 0xAA, 0xF7, 0xFF,              // call Singleton<CAMERA::Manager>::GetSingleton
		0x48, 0x8B, 0xD8,                          // mov rbx,rax
		0xE8, 0xA0, 0xE6, 0xF4, 0xFF,              // call Singleton<DLLMAIN::Plugin>::GetSingleton
		0x48, 0x8B, 0x88, 0xA8, 0x01, 0x00, 0x00,  // mov rcx,[rax+1A8h]
		0x80, 0x39, 0x00, 0x74, 0x07,              // cmp byte ptr [rcx],0 ; je B3EE3
		0xC6, 0x83, 0x35, 0x02, 0x00, 0x00, 0x01,  // mov byte ptr [rbx+235h],1
		0x48, 0x83, 0xC4, 0x20, 0x5B, 0xC3         // add rsp,20h ; pop rbx ; ret
	};
	constexpr std::uint8_t kJmpShort = 0xEB;

	// SetMode's consumer of the pending flag (1.4.1): `if ([235h]) { if ([B8h] == 0) { [235h]=0; [30h]=1; thirdPerson=true;
	// zoom=-0.275 } ... }`. IgnorePendingThirdPerson=1 turns the first je into jmp, so SetMode never enters third-person
	// body mode from a forced third person, whoever raised the flag.
	constexpr std::uintptr_t kPendingBlockRVA = 0x34A9F;
	constexpr std::uintptr_t kPendingJeRVA = 0x34AA6;
	constexpr std::array<std::uint8_t, 18> kPendingBlock{
		0x80, 0xBB, 0x35, 0x02, 0x00, 0x00, 0x00,  // cmp byte ptr [rbx+235h],0
		0x74, 0x3B,                                // je 34AE3
		0x83, 0xBB, 0xB8, 0x00, 0x00, 0x00, 0x00,  // cmp dword ptr [rbx+0B8h],0
		0x75, 0x1C                                 // jne 34ACD
	};

	// ThirdPersonBody=0 (1.5.0): the request and the five zoom / force sites (see the header comment)
	struct Site
	{
		std::uintptr_t                   contextRVA;
		std::span<const std::uint8_t>    context;
		std::uintptr_t                   patchRVA;
		std::span<const std::uint8_t>    patch;
		const char*                      what;
	};
	constexpr std::array<std::uint8_t, 10> kSetModeArg{ 0x41, 0x0F, 0xB6, 0xE8, 0x48, 0x8B, 0xF2, 0x48, 0x8B, 0xD9 };  // movzx ebp,r8b ; mov rsi,rdx ; mov rbx,rcx
	constexpr std::array<std::uint8_t, 4>  kXorEbp{ 0x31, 0xED, 0x66, 0x90 };                                         // xor ebp,ebp ; nop
	constexpr std::array<std::uint8_t, 24> kFurnitureEnter{
		0x48, 0x8B, 0x04, 0x03,                     // mov rax,[rbx+rax]           (the ThirdPersonState)
		0xC7, 0x40, 0x78, 0xCD, 0xCC, 0x8C, 0xBE,   // mov dword ptr [rax+78h],-0.275
		0xC7, 0x40, 0x74, 0xCD, 0xCC, 0x8C, 0xBE,   // mov dword ptr [rax+74h],-0.275
		0x48, 0x83, 0xC4, 0x20, 0x5B, 0xC3          // add rsp,20h ; pop rbx ; ret
	};
	constexpr std::array<std::uint8_t, 14> kAnimEnterBitmask{
		0x0F, 0x2F, 0x46, 0x74,                     // comiss xmm0,[rsi+74h]
		0x72, 0x08,                                 // jb +8
		0x48, 0x8B, 0xCF, 0xE8, 0x6A, 0x46, 0x0E, 0x00  // mov rcx,rdi ; call ForceThirdPerson
	};
	constexpr std::array<std::uint8_t, 19> kAnimEnterCartRide{
		0x83, 0xFB, 0x05, 0x75, 0x2D,               // cmp ebx,5 ; jne
		0xC7, 0x46, 0x78, 0xCD, 0xCC, 0x8C, 0xBE,   // mov dword ptr [rsi+78h],-0.275
		0xC7, 0x46, 0x74, 0xCD, 0xCC, 0x8C, 0xBE    // mov dword ptr [rsi+74h],-0.275
	};
	constexpr std::array<std::uint8_t, 30> kAnimEnterFromFirstPerson{
		0x84, 0xDB, 0x74, 0x16,                     // test bl,bl ; je +16h
		0x48, 0x8B, 0xCF, 0xE8, 0x64, 0x45, 0x0E, 0x00,  // mov rcx,rdi ; call ForceThirdPerson
		0xC7, 0x46, 0x78, 0xCD, 0xCC, 0x8C, 0xBE,   // mov dword ptr [rsi+78h],-0.275
		0xC7, 0x46, 0x74, 0xCD, 0xCC, 0x8C, 0xBE,   // mov dword ptr [rsi+74h],-0.275
		0xC6, 0x45, 0x08, 0x01                      // mov byte ptr [rbp+8],1
	};
	constexpr std::array<std::uint8_t, 5>  kNop5{ 0x0F, 0x1F, 0x44, 0x00, 0x00 };
	constexpr std::array<std::uint8_t, 14> kNop14{ 0x0F, 0x1F, 0x80, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x1F, 0x80, 0x00, 0x00, 0x00, 0x00 };
	constexpr std::array<std::uint8_t, 19> kNop19{ 0x0F, 0x1F, 0x44, 0x00, 0x00, 0x0F, 0x1F, 0x80, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x1F, 0x80, 0x00, 0x00, 0x00, 0x00 };
	// 1.5.2: the `movzx ebp,r8b` -> `xor ebp,ebp` site (kSetModeArg / kXorEbp) is no longer applied. With it, the
	// request persisted by SetMode's pending block was dropped on every later frame, so a scripted forced third
	// person got IC's head camera for one frame only (traced 2026-11-08 21:28). The head camera needs the -0.275
	// zoom these four sites used to write, so with them NOPed the states' request alone never yields mode 2:
	// chairs, beds and mounts stay vanilla while the scripted path (hook + pending block, which zooms itself) works.
	constexpr std::array<Site, 4> kThirdPersonBodySites{ {
		{ 0x395F7, kFurnitureEnter, 0x395FB, kNop14, "FurnitureState::OnEnter no longer zooms the third-person camera to the head" },
		{ 0x3CF68, kAnimEnterBitmask, 0x3CF71, kNop5, "AnimationState::OnEnter no longer forces third person when coming from Free/Furniture/TweenMenu/ThirdPerson/HorseDismounting/MapMenu" },
		{ 0x3CFCE, kAnimEnterCartRide, 0x3CFD3, kNop14, "AnimationState::OnEnter no longer zooms for the cart ride" },
		{ 0x3D070, kAnimEnterFromFirstPerson, 0x3D077, kNop19, "AnimationState::OnEnter no longer forces third person + zooms when entered from first person" },
	} };

	// UpdateFOV's hands-off path (1.5.2): `if ([264h] > 0) { fov = [264h]; [264h] = 0 }` applies the FOV that
	// TransitionCameraState queued for the new state once per state change, even where the state is hands-off -
	// the furniture camera / head camera then sat at IC's stale lerp (91..95 instead of 100, traced). The
	// `movaps xmm6,xmm1` becomes a nop, so the path writes the camera's current FOV back and nothing else.
	constexpr std::uintptr_t kFovPendingRVA = 0x36ACB;
	constexpr std::uintptr_t kFovPendingMovRVA = 0x36ADD;
	constexpr std::array<std::uint8_t, 34> kFovPending{
		0xF3, 0x0F, 0x10, 0x8B, 0x64, 0x02, 0x00, 0x00,  // movss xmm1,[rbx+264h]
		0x0F, 0x57, 0xC0,                                // xorps xmm0,xmm0
		0x33, 0xF6,                                      // xor esi,esi
		0x0F, 0x2F, 0xC8,                                // comiss xmm1,xmm0
		0x76, 0x09,                                      // jbe 36AE6
		0x0F, 0x28, 0xF1,                                // movaps xmm6,xmm1          <- nop
		0x89, 0xB3, 0x64, 0x02, 0x00, 0x00,              // mov [rbx+264h],esi
		0x40, 0x88, 0xB3, 0x36, 0x02, 0x00, 0x00         // mov byte ptr [rbx+236h],sil
	};
	constexpr std::array<std::uint8_t, 3> kNop3{ 0x0F, 0x1F, 0x00 };

	// CameraFOV=0 (1.5.4): UpdateFOV's two stores into PlayerCamera::worldFOV. The first-person-state store writes
	// IC's lagging lerp every first-person frame; the First Person FOV mod overwrites it a moment later, so it is
	// invisible until the frame the camera leaves first person (chair, scripted third person), when nothing follows
	// and the stale value sticks (traced 2026-11-08: 100 -> 90.96 on a bench, 100 -> 91.82 on a bite; the camera-
	// FOV write watch saw no other writer). With both stores NOPed Improved Camera never writes the camera FOV.
	constexpr std::uintptr_t kFovStoreNormalRVA = 0x368F6;    // mov edi,158h ; movss [rdi+rbp],xmm6 ; mov [rbx+240h],esi
	constexpr std::uintptr_t kFovStoreHandsOffRVA = 0x36B5E;  // same shape at the end of the hands-off path
	constexpr std::array<std::uint8_t, 16> kFovStoreCtx{
		0xBF, 0x58, 0x01, 0x00, 0x00,              // mov edi,158h   (VR offset; SE/AE keep 13Ch in edi)
		0xF3, 0x0F, 0x11, 0x34, 0x2F,              // movss dword ptr [rdi+rbp],xmm6   <- nop
		0x89, 0xB3, 0x40, 0x02, 0x00, 0x00         // mov dword ptr [rbx+240h],esi
	};

	// Debug=1 entry loggers (1.4.1): the first instructions of IC's ForceThirdPerson hook and of SetMode
	constexpr std::uintptr_t kPluginGetterRVA = 0x2570;    // REX::Singleton<DLLMAIN::Plugin>::GetSingleton()
	constexpr std::uintptr_t kFuncEntryRVA = 0xB3EB0;      // HOOK::MISC::ForceThirdPerson::func
	constexpr std::array<std::uint8_t, 6> kFuncEntry{ 0x40, 0x53, 0x48, 0x83, 0xEC, 0x20 };  // push rbx ; sub rsp,20h
	constexpr std::uintptr_t kSetModeEntryRVA = 0x34A30;   // CAMERA::Manager::SetMode
	constexpr std::array<std::uint8_t, 5> kSetModeEntry{ 0x48, 0x89, 0x5C, 0x24, 0x08 };     // mov [rsp+8],rbx

	// CAMERA::Manager fields (read by the trace only)
	constexpr std::ptrdiff_t kMgrLock = 0x18;        // uint32: internal camera lock (0 none, 9 ThirdPerson, 22h released)
	constexpr std::ptrdiff_t kMgrThirdPerson = 0x30; // bool: third-person body mode requested (SetMode's argument)
	constexpr std::ptrdiff_t kMgrPending3P = 0x235;  // bool: set by the ForceThirdPerson hook, consumed by SetMode
	constexpr std::ptrdiff_t kMgrTargetFOV = 0x1A0;  // float: the state's profile FOV, set by TransitionCameraState
	constexpr std::ptrdiff_t kMgrState = 0x1B8;      // CAMERA::CameraState id (ToString table below)
	constexpr std::ptrdiff_t kMgrMode = 0x1C0;       // CAMERA::CameraMode from SetMode (3 = Improved Camera not in control)
	constexpr std::ptrdiff_t kMgrLerpFOV = 0x23C;    // float: UpdateFOV's current lerp value

	// CAMERA::CameraState::ToString's jump table, 2.0.0.2226 (RVA 31F20)
	constexpr std::array<const char*, 35> kStateNames{
		"FirstPerson", "Vanity", "VATS", "Free", "IronSight", "Furniture", "Transition", "TweenMenu",
		"Animated", "ThirdPerson", "Horse", "Bleedout", "Dragon", "Animation", "Crafting", "Dead",
		"Dialogue", "DragonDismounting", "DragonMounting", "Gathering", "HorseDismounting", "HorseMounting",
		"MapMenu", "RaceMenu", "Spectator", "VampirelordTransition", "Vampirelord", "WerewolfTransition",
		"Werewolf", "Cinematic", "LichTransition", "Lich", "Sex", "SexTFC", "Unknown"
	};

	bool           g_debug{ false };
	bool           g_thirdPersonBody{ false };  // ThirdPersonBody=1: IC's head camera on furniture / mounts too
	std::uintptr_t g_ic2Module{ 0 };  // ImprovedCameraSE.dll base once the 2.0.0.2226 bytes matched

	const char* StateName(std::uint32_t a_state)
	{
		return a_state < kStateNames.size() ? kStateNames[a_state] : "?";
	}

	void AppendAbsJmp(std::vector<std::uint8_t>& a_code, std::uintptr_t a_target)
	{
		a_code.insert(a_code.end(), { 0xFF, 0x25, 0x00, 0x00, 0x00, 0x00 });  // jmp [rip+0]
		for (int i = 0; i < 8; ++i) {
			a_code.push_back(static_cast<std::uint8_t>(a_target >> (i * 8)));
		}
	}

	void PatchCombatHeadbob(std::uintptr_t a_module);
	void PatchThirdPersonFOV(std::uintptr_t a_module);
	void PatchAnimationForceFirstPerson(std::uintptr_t a_module);
	void PatchForcedThirdPerson(std::uintptr_t a_module);
	void PatchIgnorePendingThirdPerson(std::uintptr_t a_module);
	void PatchThirdPersonBody(std::uintptr_t a_module);
	void InstallEntryLoggers(std::uintptr_t a_module);

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

		if (std::memcmp(reinterpret_cast<const void*>(module + kFovSiteRVA), kFovExpected.data(), kFovExpected.size()) == 0) {
			SKSE::log::info("ImprovedCameraSE.dll is build 2.0.0.2226 - the 1.1.2 sheathe / head-bob patches do not apply");
			g_ic2Module = module;
			PatchThirdPersonFOV(module);
			PatchAnimationForceFirstPerson(module);
			PatchForcedThirdPerson(module);
			PatchIgnorePendingThirdPerson(module);
			PatchThirdPersonBody(module);
			return;
		}

		if (std::memcmp(reinterpret_cast<const void*>(module + kCheckRVA), kExpected.data(), kExpected.size()) != 0) {
			SKSE::log::warn("ImprovedCameraSE.dll bytes at RVA {:X} / {:X} match neither build 1.1.2.4228 nor 2.0.0.2226 - NOT patched", kCheckRVA, kFovSiteRVA);
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

	// [ImprovedCamera2] HandsOffFOVStates: Improved Camera state ids (decimal or 0x hex, separated by
	// commas / semicolons / spaces) whose FOV UpdateFOV must leave alone. 3 and 1Dh are always in.
	std::vector<std::uint32_t> ReadHandsOffStates()
	{
		std::vector<std::uint32_t> states{ 3, 0x1D };
		wchar_t buf[512]{};
		::GetPrivateProfileStringW(L"ImprovedCamera2", L"HandsOffFOVStates",
			L"1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34", buf, 512, kIniPath);
		std::wstring_view text{ buf };
		std::size_t pos = 0;
		while (pos < text.size()) {
			const auto end = text.find_first_of(L",; \t", pos);
			const auto tok = text.substr(pos, end == std::wstring_view::npos ? std::wstring_view::npos : end - pos);
			pos = end == std::wstring_view::npos ? text.size() : end + 1;
			if (tok.empty()) {
				continue;
			}
			std::wstring tokStr{ tok };
			wchar_t* parseEnd = nullptr;
			const auto value = std::wcstoul(tokStr.c_str(), &parseEnd, 0);
			if (parseEnd == tokStr.c_str() || *parseEnd != L'\0' || value >= kStateNames.size()) {
				SKSE::log::warn("HandsOffFOVStates: '{}' is not an Improved Camera state id (0-34) - ignored", SKSE::stl::utf16_to_utf8(tokStr).value_or("?"));
				continue;
			}
			if (std::ranges::find(states, static_cast<std::uint32_t>(value)) == states.end()) {
				states.push_back(static_cast<std::uint32_t>(value));
			}
		}
		return states;
	}

	void PatchThirdPersonFOV(std::uintptr_t a_module)
	{
		const auto states = ReadHandsOffStates();
		if (states.size() == 2) {
			SKSE::log::info("HandsOffFOVStates is empty - Improved Camera's FOV left as it is");
			return;
		}

		// stub:  cmp eax,<state> ; je hands_off   (x N)  ; jmp 367EE ; hands_off: jmp 36ACB
		// eax = manager->cameraState; nothing after 367EE or at 36ACB consumes the flags.
		std::vector<std::uint8_t> stub;
		for (const auto state : states) {
			stub.push_back(0x3D);  // cmp eax,imm32
			for (int i = 0; i < 4; ++i) {
				stub.push_back(static_cast<std::uint8_t>(state >> (i * 8)));
			}
			stub.insert(stub.end(), { 0x0F, 0x84, 0x00, 0x00, 0x00, 0x00 });  // je rel32 (filled below)
		}
		AppendAbsJmp(stub, a_module + kFovNormalRVA);
		const auto handsOff = stub.size();
		AppendAbsJmp(stub, a_module + kFovHandsOffRVA);
		for (std::size_t i = 0; i < states.size(); ++i) {
			const auto next = 11 * i + 11;  // first byte after this entry's je
			const auto rel = static_cast<std::int32_t>(handsOff - next);
			for (int b = 0; b < 4; ++b) {
				stub[11 * i + 7 + b] = static_cast<std::uint8_t>(static_cast<std::uint32_t>(rel) >> (b * 8));
			}
		}

		auto* mem = static_cast<std::uint8_t*>(::VirtualAlloc(nullptr, stub.size(), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
		if (!mem) {
			SKSE::log::error("VirtualAlloc failed ({}) - third-person FOV NOT patched", ::GetLastError());
			return;
		}
		std::memcpy(mem, stub.data(), stub.size());
		::FlushInstructionCache(::GetCurrentProcess(), mem, stub.size());

		// 18 bytes at 367DC: 14-byte absolute jmp + 4 int3 padding (never reached)
		std::vector<std::uint8_t> site;
		AppendAbsJmp(site, reinterpret_cast<std::uintptr_t>(mem));
		site.resize(kFovSiteSize, 0xCC);
		if (!Write(a_module + kFovSiteRVA, site.data(), site.size())) {
			return;
		}

		std::string names;
		for (const auto state : states) {
			if (!names.empty()) {
				names += ", ";
			}
			names += std::format("{} ({})", StateName(state), state);
		}
		SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: UpdateFOV leaves the camera FOV alone in {}", kFovSiteRVA, names);

		if (std::memcmp(reinterpret_cast<const void*>(a_module + kFovPendingRVA), kFovPending.data(), kFovPending.size()) != 0) {
			SKSE::log::warn("UpdateFOV hands-off bytes at RVA {:X} do not match build 2.0.0.2226 - pending FOV NOT patched", kFovPendingRVA);
		} else if (Write(a_module + kFovPendingMovRVA, kNop3.data(), kNop3.size())) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: the hands-off path no longer applies IC's queued FOV on a state change", kFovPendingMovRVA);
		}

		if (::GetPrivateProfileIntW(L"ImprovedCamera2", L"CameraFOV", 0, kIniPath) != 0) {
			SKSE::log::info("CameraFOV=1 - Improved Camera keeps writing the camera FOV in its first-person state");
			return;
		}
		for (const auto rva : { kFovStoreNormalRVA, kFovStoreHandsOffRVA }) {
			if (std::memcmp(reinterpret_cast<const void*>(a_module + rva), kFovStoreCtx.data(), kFovStoreCtx.size()) != 0) {
				SKSE::log::warn("UpdateFOV store bytes at RVA {:X} do not match build 2.0.0.2226 - NOT patched", rva);
			} else if (Write(a_module + rva + 5, kNop5.data(), kNop5.size())) {
				SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: UpdateFOV no longer writes PlayerCamera::worldFOV here", rva + 5);
			}
		}
	}

	// [ImprovedCamera2] ForceFirstPersonAnimations=0: in IC's Animation state (scripted idles, sitting,
	// sleeping, bathing, fishing, boat/cart rides, view) with the camera already third person, SetMode
	// returns 3 (not in control) instead of forcing first person.
	void PatchAnimationForceFirstPerson(std::uintptr_t a_module)
	{
		if (::GetPrivateProfileIntW(L"ImprovedCamera2", L"ForceFirstPersonAnimations", 0, kIniPath) != 0) {
			SKSE::log::info("ForceFirstPersonAnimations=1 - Improved Camera keeps forcing first person in its Animation state");
			return;
		}
		if (std::memcmp(reinterpret_cast<const void*>(a_module + kAnimBranchRVA), kAnimBranch.data(), kAnimBranch.size()) != 0) {
			SKSE::log::warn("SetMode bytes at RVA {:X} do not match build 2.0.0.2226 - Animation-state first person NOT patched", kAnimBranchRVA);
			return;
		}
		if (Write(a_module + kAnimForceRVA, kAnimReturn3.data(), kAnimReturn3.size())) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: SetMode steps aside instead of forcing first person in the Animation state (sit, sleep, scripted idles...)", kAnimForceRVA);
		}
	}

	// [ImprovedCamera2] TakeOverForcedThirdPerson=0: IC's ForceThirdPerson hook no longer flags a scripted
	// or furniture ForceThirdPerson as a request for its head-camera view.
	void PatchForcedThirdPerson(std::uintptr_t a_module)
	{
		if (::GetPrivateProfileIntW(L"ImprovedCamera2", L"TakeOverForcedThirdPerson", 1, kIniPath) != 0) {
			SKSE::log::info("TakeOverForcedThirdPerson=1 - a scripted forced third person (eating, Immersive Interactions) becomes Improved Camera's first-person-look head camera");
			return;
		}
		if (std::memcmp(reinterpret_cast<const void*>(a_module + kForceThirdPersonHookRVA), kForceThirdPersonHook.data(), kForceThirdPersonHook.size()) != 0) {
			SKSE::log::warn("ForceThirdPerson hook bytes at RVA {:X} do not match build 2.0.0.2226 - NOT patched", kForceThirdPersonHookRVA);
			return;
		}
		if (Write(a_module + kForceThirdPersonJeRVA, &kJmpShort, 1)) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: a forced third person (furniture, Game.ForceThirdPerson) stays a plain third person", kForceThirdPersonJeRVA);
		}
	}

	// [ImprovedCamera2] IgnorePendingThirdPerson=1: SetMode never consumes the pending-third-person flag.
	void PatchIgnorePendingThirdPerson(std::uintptr_t a_module)
	{
		if (::GetPrivateProfileIntW(L"ImprovedCamera2", L"IgnorePendingThirdPerson", 0, kIniPath) == 0) {
			SKSE::log::info("IgnorePendingThirdPerson=0 - SetMode enters its head-camera mode from a scripted forced third person");
			return;
		}
		if (std::memcmp(reinterpret_cast<const void*>(a_module + kPendingBlockRVA), kPendingBlock.data(), kPendingBlock.size()) != 0) {
			SKSE::log::warn("SetMode pending-flag bytes at RVA {:X} do not match build 2.0.0.2226 - NOT patched", kPendingBlockRVA);
			return;
		}
		if (Write(a_module + kPendingJeRVA, &kJmpShort, 1)) {
			SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: SetMode ignores the pending-third-person flag", kPendingJeRVA);
		}
	}

	// [ImprovedCamera2] ThirdPersonBody=0: IC never operates on a third-person camera - SetMode ignores the
	// states' request, and the Furniture / Animation entry handlers neither zoom it to the head nor force it.
	void PatchThirdPersonBody(std::uintptr_t a_module)
	{
		g_thirdPersonBody = ::GetPrivateProfileIntW(L"ImprovedCamera2", L"ThirdPersonBody", 0, kIniPath) != 0;
		if (g_thirdPersonBody) {
			SKSE::log::info("ThirdPersonBody=1 - Improved Camera keeps its head camera on furniture and mounts");
			return;
		}
		for (const auto& site : kThirdPersonBodySites) {
			if (std::memcmp(reinterpret_cast<const void*>(a_module + site.contextRVA), site.context.data(), site.context.size()) != 0) {
				SKSE::log::warn("bytes at RVA {:X} do not match build 2.0.0.2226 - NOT patched: {}", site.contextRVA, site.what);
				continue;
			}
			if (Write(a_module + site.patchRVA, site.patch.data(), site.patch.size())) {
				SKSE::log::info("Patched ImprovedCameraSE.dll+{:X}: {}", site.patchRVA, site.what);
			}
		}
	}

	// ---------------------------------------------------------------- SmoothCam hold during IC's head camera (1.5.5)
	// IC 2.0's head camera (mode 2) runs on the vanilla ThirdPersonState, which SmoothCam drives: SmoothCam keeps
	// applying its per-state FOV offset (standing -15 in the list's preset) to a camera that now sits on the eyes,
	// so a scripted first-person-look animation (eating) reads as a zoom. IC registers with SmoothCam's API but
	// never takes the camera there (traced 2026-11-08). While IC's mode is 2 this plugin holds SmoothCam's camera
	// control, which stops SmoothCam's update, and releases it the frame the mode changes. Main thread only.

	SmoothCamAPI::IVSmoothCam1* g_scApi{ nullptr };
	bool                        g_scHolding{ false };
	bool                        g_scTakenReported{ false };
	bool                        g_scHoldEnabled{ true };
	std::uint8_t*               g_scManager{ nullptr };
	bool                        g_holdEntryFrame{ true };  // HoldCameraOnHeadCameraEntry=1 (1.7.0)
	float                       g_headCamNear{ 4.0f };     // HeadCameraNearDistance (1.8.0); 0 = leave IC's rule

	void SmoothCamHold()
	{
		const auto result = g_scApi->RequestCameraControl(SKSE::GetPluginHandle());
		switch (result) {
		case SmoothCamAPI::APIResult::OK:
		case SmoothCamAPI::APIResult::AlreadyGiven:
			g_scHolding = true;
			g_scTakenReported = false;
			SKSE::log::info("Holding SmoothCam's camera while Improved Camera's head camera is up");
			return;
		case SmoothCamAPI::APIResult::AlreadyTaken:
			if (!std::exchange(g_scTakenReported, true)) {
				SKSE::log::info("SmoothCam's camera is held by plugin {} during the head camera; leaving it", static_cast<std::uint32_t>(g_scApi->GetCameraOwner()));
			}
			return;
		default:
			if (!std::exchange(g_scTakenReported, true)) {
				SKSE::log::warn("SmoothCam refused camera control (result {})", static_cast<std::uint32_t>(result));
			}
			return;
		}
	}

	void SmoothCamRelease()
	{
		const auto result = g_scApi->ReleaseCameraControl(SKSE::GetPluginHandle());
		g_scHolding = false;
		SKSE::log::info("Released SmoothCam's camera (result {}); the head camera ended", static_cast<std::uint32_t>(result));
	}

	// Decided BEFORE the camera updates (1.5.8): hooked on PlayerCamera::Update (TESCamera vfunc 02) at kDataLoaded,
	// after SmoothCam and IC installed theirs, so this runs first in the chain. 1.5.5-1.5.7 decided it in
	// PlayerCharacter::Update, which the trace showed runs after the camera update: on a bite SmoothCam's offset
	// still landed for one frame (`frustumW=2.4054`) before the hold took effect. IC's hook raises the pending flag
	// on the Papyrus thread earlier in the frame, where SmoothCam refuses requests, so it is read here instead.
	void DecideSmoothCamHold()
	{
		if (!g_scApi || !g_scManager) {
			return;
		}
		bool headCamera = *reinterpret_cast<std::uint32_t*>(g_scManager + kMgrMode) == 2 || g_scManager[kMgrPending3P] != 0;
		// With IC's head camera on furniture there is no pending flag to be early on; the actor's sit/sleep
		// state changes before the camera does, so it is the early signal there (and for mounting).
		if (!headCamera && g_thirdPersonBody) {
			if (auto* player = RE::PlayerCharacter::GetSingleton()) {
				if (auto* state = player->AsActorState(); state && state->GetSitSleepState() != RE::SIT_SLEEP_STATE::kNormal) {
					headCamera = true;
				}
			}
		}
		if (headCamera && !g_scHolding) {
			SmoothCamHold();
		} else if (!headCamera && g_scHolding) {
			SmoothCamRelease();
		}
	}

	// ---------------------------------------------------------------- the head camera's entry frame (1.7.0)
	// A scripted forced third person (a bite) takes three frames (traced 2026-11-08, `[campos]`): frame N - IC's hook
	// raises the pending flag on the Papyrus thread after the camera update; the engine's state is already ThirdPerson
	// but the camera root still sits where the first-person camera was. Frame N+1 - IC's update consumes the flag
	// (SetMode -> mode 2, its ThirdPersonState entered) but IC's own position write only starts the frame after, so
	// the vanilla ThirdPersonState's position is what this frame renders: one frame from behind the player (fwd -170 /
	// up +205 in one bite, -81 / +129 in the other). Frame N+2 on - the head camera. This runs after the camera update
	// (PlayerCharacter::Update) and puts the camera root back on the previous frame's transform for exactly that one
	// frame, so the view goes first-person camera -> head camera with no third-person flash in between.
	void HoldHeadCameraEntryFrame()
	{
		static RE::NiTransform s_prev{};
		static bool            s_havePrev{ false };
		static std::uint32_t   s_prevIcState{ 0xFF };

		auto* camera = RE::PlayerCamera::GetSingleton();
		if (!g_scManager || !camera || !camera->cameraRoot || !camera->currentState) {
			s_havePrev = false;
			return;
		}
		const auto icState = *reinterpret_cast<std::uint32_t*>(g_scManager + kMgrState);
		const auto icMode = *reinterpret_cast<std::uint32_t*>(g_scManager + kMgrMode);
		const bool entry = s_havePrev && s_prevIcState == 0 /* FirstPerson */ && icState == 9 /* ThirdPerson */ &&
		                   icMode == 2 && static_cast<std::uint32_t>(camera->currentState->id) == 9 /* kThirdPerson */;
		if (entry) {
			camera->cameraRoot->local = s_prev;
			RE::NiUpdateData updateData{};
			camera->cameraRoot->Update(updateData);
			SKSE::log::info("Head camera entered: the camera root kept the previous frame's transform for this one frame");
		}
		s_prev = camera->cameraRoot->local;
		s_havePrev = true;
		s_prevIcState = icState;
	}

	// ---------------------------------------------------------------- the near plane in the head camera (1.8.0)
	// IC's UpdateNearDistance (see the header) runs the first-person pitch rule in the head camera: 15 units while
	// looking less than 15 deg down. The mouth is ~10 units ahead of the camera there, so a bite's food and hand were
	// cut away by the near plane (recording 2026-11-08 23:59). Runs after the camera update, caps the plane while IC's
	// mode is 2; IC rewrites its own value the frame the mode changes (it writes whenever the plane is > 0.05 off).
	void ApplyHeadCameraNearDistance()
	{
		auto* camera = RE::PlayerCamera::GetSingleton();
		if (!g_scManager || !camera || !camera->cameraRoot) {
			return;
		}
		if (*reinterpret_cast<std::uint32_t*>(g_scManager + kMgrMode) != 2) {
			return;
		}
		RE::NiCamera* niCamera = nullptr;
		for (auto& child : camera->cameraRoot->children) {
			if (child && (niCamera = netimmerse_cast<RE::NiCamera*>(child.get()))) {
				break;
			}
		}
		if (!niCamera) {
			return;
		}
		auto& frustum = niCamera->GetRuntimeData2().viewFrustum;
		if (frustum.fNear <= g_headCamNear) {
			return;
		}
		static RE::Setting* s_nearSetting = [] {
			auto* prefs = RE::INIPrefSettingCollection::GetSingleton();
			auto* setting = prefs ? prefs->GetSetting("fNearDistance:Display") : nullptr;
			if (!setting) {
				auto* ini = RE::INISettingCollection::GetSingleton();
				setting = ini ? ini->GetSetting("fNearDistance:Display") : nullptr;
			}
			return setting;
		}();
		static bool s_logged = false;
		if (!std::exchange(s_logged, true)) {
			SKSE::log::info("Head camera: near plane {:.2f} -> {:.1f} (fNearDistance setting {})", frustum.fNear, g_headCamNear, s_nearSetting ? "found" : "not found");
		}
		frustum.fNear = g_headCamNear;
		if (s_nearSetting) {
			s_nearSetting->data.f = g_headCamNear;
		}
	}

	// 1.5.9: back on PlayerCharacter::Update (vfunc 0xAD), the hook verified in 1.5.5 and 1.5.7. 1.5.8 put the
	// decision on the PlayerCamera vtable's Update slot, which the game never calls for the player camera (the hold
	// never fired; SmoothCam's offset was back for whole bites and sits). The one-frame offset at a bite's first
	// frame comes with this hook; the sit-state signal keeps chairs clean from the first frame.
	struct PlayerUpdate
	{
		static void thunk(RE::PlayerCharacter* a_player, float a_delta)
		{
			func(a_player, a_delta);
			if (g_scHoldEnabled) {
				DecideSmoothCamHold();
			}
			if (g_holdEntryFrame) {
				HoldHeadCameraEntryFrame();
			}
			if (g_headCamNear > 0.0f) {
				ApplyHeadCameraNearDistance();
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	// ---------------------------------------------------------------- Debug=1 entry loggers

	std::uint8_t* Manager()
	{
		using Getter = std::uint8_t* (*)();
		return g_ic2Module ? reinterpret_cast<Getter>(g_ic2Module + kManagerGetterRVA)() : nullptr;
	}

	std::string Hex(std::uintptr_t a_addr, std::size_t a_len)
	{
		std::string s;
		for (std::size_t i = 0; i < a_len; ++i) {
			s += std::format("{:02X} ", *reinterpret_cast<const std::uint8_t*>(a_addr + i));
		}
		return s;
	}

	std::string ManagerFlags(const std::uint8_t* a_mgr)
	{
		return std::format("pend={} tp={} state38={} state1B8={} lock={} b8={} mode40={}",
			a_mgr[kMgrPending3P], a_mgr[kMgrThirdPerson],
			*reinterpret_cast<const std::uint32_t*>(a_mgr + 0x38), *reinterpret_cast<const std::uint32_t*>(a_mgr + kMgrState),
			*reinterpret_cast<const std::uint32_t*>(a_mgr + kMgrLock), *reinterpret_cast<const std::uint32_t*>(a_mgr + 0xB8),
			*reinterpret_cast<const std::uint32_t*>(a_mgr + 0x40));
	}

	void LogForceThirdPersonHook(void*)
	{
		static int s_count = 0;
		if (auto* mgr = Manager()) {
			SKSE::log::info("[IC hook] ForceThirdPerson #{}: {} | byte at +B3EDA = {:02X}", ++s_count, ManagerFlags(mgr), *reinterpret_cast<std::uint8_t*>(g_ic2Module + kForceThirdPersonJeRVA));
		}
	}

	void LogSetMode(void* a_this)
	{
		static std::uint8_t s_lastPend = 0xFF;
		static std::uint8_t s_lastTp = 0xFF;
		auto* mgr = static_cast<std::uint8_t*>(a_this);
		if (!mgr) {
			return;
		}
		const auto pend = mgr[kMgrPending3P];
		const auto tp = mgr[kMgrThirdPerson];
		if (pend != 0 || pend != s_lastPend || tp != s_lastTp) {
			SKSE::log::info("[SetMode in] {}", ManagerFlags(mgr));
			s_lastPend = pend;
			s_lastTp = tp;
		}
	}

	std::uint8_t* AllocNear(std::uintptr_t a_near, std::size_t a_size)
	{
		SYSTEM_INFO si{};
		::GetSystemInfo(&si);
		const std::uintptr_t gran = si.dwAllocationGranularity;
		for (std::uintptr_t delta = gran; delta < 0x40000000; delta += gran) {
			for (const int sign : { -1, 1 }) {
				const auto addr = sign < 0 ? a_near - delta : a_near + delta;
				if (auto* p = ::VirtualAlloc(reinterpret_cast<void*>(addr), a_size, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE)) {
					return static_cast<std::uint8_t*>(p);
				}
			}
		}
		return nullptr;
	}

	// Overwrites the first a_len bytes of the function at a_entryRVA (whole instructions, no rip-relative
	// operands) with `jmp stub`; the stub saves the argument registers, calls a_logger(rcx), restores them,
	// runs the displaced instructions and jumps back.
	void InstallEntryLogger(std::uintptr_t a_module, std::uintptr_t a_entryRVA, const std::uint8_t* a_expected, std::size_t a_len, void (*a_logger)(void*), const char* a_name)
	{
		const auto entry = a_module + a_entryRVA;
		if (std::memcmp(reinterpret_cast<const void*>(entry), a_expected, a_len) != 0) {
			SKSE::log::warn("{} entry bytes at RVA {:X} do not match - logger NOT installed", a_name, a_entryRVA);
			return;
		}
		auto* stub = AllocNear(a_module, 256);
		if (!stub) {
			SKSE::log::error("no memory within 1 GB of ImprovedCameraSE.dll - {} logger NOT installed", a_name);
			return;
		}
		std::vector<std::uint8_t> code{
			0x51,                    // push rcx
			0x52,                    // push rdx
			0x41, 0x50,              // push r8
			0x41, 0x51,              // push r9
			0x48, 0x83, 0xEC, 0x28,  // sub rsp,28h   (entry rsp = 8 mod 16; 4 pushes keep it; -28h -> 0 mod 16 before the call)
			0x48, 0xB8               // mov rax,imm64
		};
		const auto logger = reinterpret_cast<std::uintptr_t>(a_logger);
		for (int i = 0; i < 8; ++i) {
			code.push_back(static_cast<std::uint8_t>(logger >> (i * 8)));
		}
		code.insert(code.end(), { 0xFF, 0xD0 });                                                  // call rax
		code.insert(code.end(), { 0x48, 0x83, 0xC4, 0x28, 0x41, 0x59, 0x41, 0x58, 0x5A, 0x59 });  // add rsp,28h ; pop r9 ; pop r8 ; pop rdx ; pop rcx
		code.insert(code.end(), a_expected, a_expected + a_len);                                  // the displaced instructions
		AppendAbsJmp(code, entry + a_len);
		std::memcpy(stub, code.data(), code.size());
		::FlushInstructionCache(::GetCurrentProcess(), stub, code.size());

		const auto rel = static_cast<std::int64_t>(reinterpret_cast<std::uintptr_t>(stub)) - static_cast<std::int64_t>(entry + 5);
		if (rel < INT32_MIN || rel > INT32_MAX) {
			SKSE::log::error("{} stub out of rel32 range - logger NOT installed", a_name);
			return;
		}
		std::vector<std::uint8_t> site{ 0xE9 };
		const auto rel32 = static_cast<std::int32_t>(rel);
		for (int i = 0; i < 4; ++i) {
			site.push_back(static_cast<std::uint8_t>(static_cast<std::uint32_t>(rel32) >> (i * 8)));
		}
		site.resize(a_len, 0xCC);
		if (Write(entry, site.data(), site.size())) {
			SKSE::log::info("Debug: {} entry logger installed (stub {:X})", a_name, reinterpret_cast<std::uintptr_t>(stub));
		}
	}

	void InstallEntryLoggers(std::uintptr_t a_module)
	{
		InstallEntryLogger(a_module, kFuncEntryRVA, kFuncEntry.data(), kFuncEntry.size(), LogForceThirdPersonHook, "IC ForceThirdPerson hook");
		InstallEntryLogger(a_module, kSetModeEntryRVA, kSetModeEntry.data(), kSetModeEntry.size(), LogSetMode, "IC SetMode");
	}

	// Once, from the first traced frame (after every plugin installed its hooks): what the patched sites
	// hold now, where the engine's ForceThirdPerson really jumps, and IC's General bytes.
	void LogReadBack()
	{
		SKSE::log::info("[verify] +B3EDA {}| +34B64 {}| +367DC {}| +34AA6 {}",
			Hex(g_ic2Module + kForceThirdPersonJeRVA, 2), Hex(g_ic2Module + kAnimForceRVA, 8),
			Hex(g_ic2Module + kFovSiteRVA, 14), Hex(g_ic2Module + kPendingJeRVA, 2));
		for (const auto& site : kThirdPersonBodySites) {
			SKSE::log::info("[verify] +{:X} {}", site.patchRVA, Hex(g_ic2Module + site.patchRVA, site.patch.size()));
		}
		REL::Relocation<std::uintptr_t> ftp{ REL::RelocationID(49863, 50796) };
		SKSE::log::info("[verify] engine ForceThirdPerson {:X}: {}", ftp.address(), Hex(ftp.address(), 12));
		const auto* b = reinterpret_cast<const std::uint8_t*>(ftp.address());
		if (b[0] == 0x48 && b[1] == 0xB8) {
			std::uint64_t target{};
			std::memcpy(&target, b + 2, 8);
			SKSE::log::info("[verify]   -> jumps to {:X} = ImprovedCameraSE.dll+{:X} (hook func is +B3EB0)", target, target - g_ic2Module);
		}
		using Getter = std::uint8_t* (*)();
		if (auto* plugin = reinterpret_cast<Getter>(g_ic2Module + kPluginGetterRVA)()) {
			if (auto* general = *reinterpret_cast<std::uint8_t**>(plugin + 0x1A8)) {
				SKSE::log::info("[verify] General bytes (bEnableBody, bEnableBodyConsole, bEnableFakeFirstPerson, bEnableHead, ...): {}", Hex(reinterpret_cast<std::uintptr_t>(general), 8));
			}
		}
	}

	// ---------------------------------------------------------------- Debug=1 hardware write watch (1.4.2)
	// DR0 on manager+30h (third-person body flag), DR1 on manager+235h (pending flag): every write is caught
	// as a single-step trap and logged with the writer (RIP = the instruction after the store) and its stack.
	// Same mechanism as ZenBoneTrace's node-flag watch.

	constexpr int kWatchFrames = 10;
	constexpr int kMaxWatchHits = 64;

	// 1.5.3: the two slots are 4-byte floats now - DR0 = PlayerCamera::worldFOV, DR1 = manager+264h (IC's queued
	// FOV). Writes that leave the value unchanged, IC's own first-person lerp store (+368FB) and the First Person
	// FOV mod's per-frame write are not recorded, so what remains is whatever else moves the camera FOV.
	struct WatchHit
	{
		std::atomic<bool> ready{ false };
		int               slot{ 0 };
		float             before{ 0 };
		float             after{ 0 };
		DWORD             tid{ 0 };
		void*             rip{ nullptr };
		USHORT            n{ 0 };
		void*             frames[kWatchFrames]{};
	};

	std::array<std::uint8_t*, 2>              g_watched{};
	std::array<std::atomic<std::uint32_t>, 2> g_lastValue{};
	std::array<WatchHit, kMaxWatchHits>       g_hits{};
	std::atomic<int>                          g_hitCount{ 0 };
	int                                       g_flushed{ 0 };
	bool                                      g_watchArmed{ false };
	std::uintptr_t                            g_skipRip{ 0 };        // IC's normal-path store, instruction after it
	std::uintptr_t                            g_skipModBegin{ 0 };   // FirstPersonFOV.dll range
	std::uintptr_t                            g_skipModEnd{ 0 };

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
			std::uint32_t afterBits{};
			std::memcpy(&afterBits, g_watched[i], 4);
			const std::uint32_t beforeBits = g_lastValue[i].exchange(afterBits);
			float before{}, after{};
			std::memcpy(&before, &beforeBits, 4);
			std::memcpy(&after, &afterBits, 4);
			if (i == 0) {
				const auto rip = ctx->Rip;
				if (std::fabs(after - before) < 0.05f || rip == g_skipRip || (rip >= g_skipModBegin && rip < g_skipModEnd)) {
					continue;
				}
			}
			const int slot = g_hitCount.fetch_add(1);
			if (slot >= kMaxWatchHits) {
				continue;
			}
			auto& h = g_hits[slot];
			h.slot = i;
			h.before = before;
			h.after = after;
			h.tid = GetCurrentThreadId();
			h.rip = reinterpret_cast<void*>(ctx->Rip);
			h.n = RtlCaptureStackBackTrace(0, kWatchFrames, h.frames, nullptr);
			h.ready.store(true, std::memory_order_release);
		}
		ctx->Dr6 = 0;
		return EXCEPTION_CONTINUE_EXECUTION;
	}

	// "SkyrimSE.exe+0x1234" / "ImprovedCameraSE.dll+0x1234"
	std::string Where(const void* a_addr)
	{
		HMODULE mod{ nullptr };
		if (!::GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
				static_cast<LPCWSTR>(a_addr), &mod) || !mod) {
			return std::format("{}", a_addr);
		}
		char path[MAX_PATH]{};
		::GetModuleFileNameA(mod, path, MAX_PATH);
		const char* name = std::strrchr(path, '\\');
		name = name ? name + 1 : path;
		return std::format("{}+0x{:X}", name, reinterpret_cast<std::uintptr_t>(a_addr) - reinterpret_cast<std::uintptr_t>(mod));
	}

	// Sets (or clears) DR0 / DR1 on every thread of the process from a helper thread, one thread suspended at
	// a time. The caller blocks in join() and is set like the others.
	void SetWatch(bool a_on)
	{
		std::thread([a_on] {
			const DWORD helper = ::GetCurrentThreadId();
			const DWORD pid = ::GetCurrentProcessId();
			HANDLE      snap = ::CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
			if (snap == INVALID_HANDLE_VALUE) {
				return;
			}
			THREADENTRY32 te{};
			te.dwSize = sizeof(te);
			for (BOOL ok = ::Thread32First(snap, &te); ok; ok = ::Thread32Next(snap, &te)) {
				if (te.th32OwnerProcessID != pid || te.th32ThreadID == helper) {
					continue;
				}
				HANDLE th = ::OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, te.th32ThreadID);
				if (!th) {
					continue;
				}
				if (::SuspendThread(th) != static_cast<DWORD>(-1)) {
					CONTEXT ctx{};
					ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
					if (::GetThreadContext(th, &ctx)) {
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
						::SetThreadContext(th, &ctx);
					}
					::ResumeThread(th);
				}
				::CloseHandle(th);
			}
			::CloseHandle(snap);
		}).join();
	}

	void ArmWatch(std::uint8_t* a_mgr)
	{
		auto* camera = RE::PlayerCamera::GetSingleton();
		if (!camera) {
			return;
		}
		g_watched = { reinterpret_cast<std::uint8_t*>(std::addressof(camera->GetRuntimeData2().worldFOV)), a_mgr + 0x264 };
		for (int i = 0; i < 2; ++i) {
			std::uint32_t bits{};
			std::memcpy(&bits, g_watched[i], 4);
			g_lastValue[i] = bits;
		}
		g_skipRip = g_ic2Module + 0x36900;  // after `movss [rdi+rbp],xmm6` in UpdateFOV's normal path
		if (auto fovMod = ::GetModuleHandleW(L"FirstPersonFOV.dll")) {
			const auto base = reinterpret_cast<std::uintptr_t>(fovMod);
			const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
			const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS*>(base + dos->e_lfanew);
			g_skipModBegin = base;
			g_skipModEnd = base + nt->OptionalHeader.SizeOfImage;
		}
		::AddVectoredExceptionHandler(1, WatchHandler);
		SetWatch(true);
		g_watchArmed = true;
		SKSE::log::info("Debug: hardware write watch armed on PlayerCamera::worldFOV ({:X}) and manager+264 (queued FOV); skipping IC's 1P lerp store and FirstPersonFOV.dll {:X}-{:X}",
			reinterpret_cast<std::uintptr_t>(g_watched[0]), g_skipModBegin, g_skipModEnd);
	}

	void FlushWatchHits()
	{
		const int count = std::min(g_hitCount.load(), kMaxWatchHits);
		for (; g_flushed < count; ++g_flushed) {
			auto& h = g_hits[g_flushed];
			if (!h.ready.load(std::memory_order_acquire)) {
				break;
			}
			std::string stack;
			for (USHORT i = 1; i < h.n && i < 8; ++i) {
				stack += Where(h.frames[i]) + " < ";
			}
			SKSE::log::info("[watch] {} {:.2f} -> {:.2f} written just before {} (tid {}) | callers: {}",
				h.slot == 0 ? "worldFOV" : "manager+264", h.before, h.after, Where(h.rip), h.tid, stack);
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

	// Improved Camera 2.0's own camera state / mode / FOV lerp; "" on other builds.
	std::string TraceImprovedCamera()
	{
		if (!g_ic2Module) {
			return {};
		}
		static bool s_readBack = false;
		if (!s_readBack) {
			s_readBack = true;
			LogReadBack();
		}
		auto* mgr = Manager();
		if (!mgr) {
			return " ic=null";
		}
		if (!g_watchArmed) {
			ArmWatch(mgr);
		}
		FlushWatchHits();
		const auto state = *reinterpret_cast<std::uint32_t*>(mgr + kMgrState);
		return std::format(" ic={}({}) icMode={} lock={} tp={} pend={} icTarget={:.2f} icLerp={:.2f}",
			StateName(state), state,
			*reinterpret_cast<std::uint32_t*>(mgr + kMgrMode),
			*reinterpret_cast<std::uint32_t*>(mgr + kMgrLock),
			*reinterpret_cast<std::uint8_t*>(mgr + kMgrThirdPerson),
			*reinterpret_cast<std::uint8_t*>(mgr + kMgrPending3P),
			*reinterpret_cast<float*>(mgr + kMgrTargetFOV),
			*reinterpret_cast<float*>(mgr + kMgrLerpFOV));
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
			"cam={} worldFOV={:.2f} fpFOV={:.2f} defFOV={:.2f} near={:.2f} frustumW={:.4f} bowZoom={} povScript={} move={} look={} fight={} drawn={} alpha={:.2f}{}",
			static_cast<std::uint32_t>(camera->currentState->id), cam2.worldFOV, cam2.firstPersonFOV, *fDefaultWorldFOV,
			nearDist, frustumW, cam2.bowZoomedIn, controls->data.povScriptMode,
			controlMap->IsMovementControlsEnabled(), controlMap->IsLookingControlsEnabled(), controlMap->IsFightingControlsEnabled(),
			player->AsActorState()->IsWeaponDrawn(), player->GetAlpha(), TraceImprovedCamera());
		if (line != s_last) {
			SKSE::log::info("[cam] {}", line);
			s_last = std::move(line);
		}

		// Camera position around every camera-state change (4 frames), to measure the cut into IC's head camera:
		// camera root relative to the player, in the player's frame (forward / right / up), plus the near plane.
		static std::string s_lastKey;
		static int         s_posFrames{ 0 };
		std::string        key = std::format("{}/{}", static_cast<std::uint32_t>(camera->currentState->id), TraceImprovedCamera().substr(0, 24));
		if (key != s_lastKey) {
			s_lastKey = key;
			s_posFrames = 4;
		}
		if (s_posFrames > 0 && camera->cameraRoot) {
			--s_posFrames;
			const auto  cam = camera->cameraRoot->world.translate;
			const auto  pos = player->GetPosition();
			const float yaw = player->GetAngleZ();
			const float dx = cam.x - pos.x, dy = cam.y - pos.y;
			const float fwd = dx * std::sin(yaw) + dy * std::cos(yaw);
			const float right = dx * std::cos(yaw) - dy * std::sin(yaw);
			SKSE::log::info("[campos] cam={} {} fwd={:.2f} right={:.2f} up={:.2f} near={:.2f}",
				static_cast<std::uint32_t>(camera->currentState->id), TraceImprovedCamera().substr(0, 24), fwd, right, cam.z - pos.z, nearDist);
		}
	}

	// HUDMenu::AdvanceMovie runs once per frame, late in it (after the camera update and after the Papyrus
	// update): the traces showed it already sees IC's pending flag and the engine's camera-state change in the
	// frame BEFORE IC's camera update consumes them, so deciding the SmoothCam hold here (1.6.0) puts the hold
	// ahead of SmoothCam's next update - the PlayerCharacter::Update hook alone was one frame late on a bite.
	struct HUDAdvanceMovie
	{
		static void thunk(RE::HUDMenu* a_this, float a_interval, std::uint32_t a_currentTime)
		{
			func(a_this, a_interval, a_currentTime);
			if (g_scHoldEnabled) {
				DecideSmoothCamHold();
			}
			if (g_debug) {
				Trace();
				TraceCameraState();
			}
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		if (a_msg->type == SKSE::MessagingInterface::kPostPostLoad) {
			if (g_ic2Module && g_scHoldEnabled && !SmoothCamAPI::RequestInterface(SKSE::GetMessagingInterface(), SmoothCamAPI::InterfaceVersion::V2)) {
				SKSE::log::warn("SmoothCam is not loaded; nothing to hold during the head camera");
			}
			return;
		}
		if (a_msg->type == SKSE::MessagingInterface::kPostLoad) {
			Patch();
			g_scHoldEnabled = ::GetPrivateProfileIntW(L"ImprovedCamera2", L"HoldSmoothCamInHeadCamera", 1, kIniPath) != 0;
			g_holdEntryFrame = ::GetPrivateProfileIntW(L"ImprovedCamera2", L"HoldCameraOnHeadCameraEntry", 1, kIniPath) != 0;
			wchar_t nearBuf[32]{};
			::GetPrivateProfileStringW(L"ImprovedCamera2", L"HeadCameraNearDistance", L"4", nearBuf, 32, kIniPath);
			g_headCamNear = static_cast<float>(::_wtof(nearBuf));
			if (g_ic2Module) {
				g_scManager = Manager();
			}
			if (g_ic2Module && (g_scHoldEnabled || g_holdEntryFrame || g_headCamNear > 0.0f)) {
				REL::Relocation<std::uintptr_t> pcVtbl{ RE::VTABLE_PlayerCharacter[0] };
				PlayerUpdate::func = pcVtbl.write_vfunc(0xAD, PlayerUpdate::thunk);
				SKSE::log::info("PlayerCharacter::Update hooked:{}{}{}",
					g_scHoldEnabled ? " SmoothCam's camera is held while Improved Camera's head camera is up;" : "",
					g_holdEntryFrame ? " the head camera's entry frame keeps the previous frame's camera (no third-person flash);" : "",
					g_headCamNear > 0.0f ? std::format(" the head camera's near plane is capped at {:.1f}", g_headCamNear) : std::string{});
			}
			if (g_ic2Module && g_headCamNear <= 0.0f) {
				SKSE::log::info("HeadCameraNearDistance=0 - Improved Camera's pitch rule sets the near plane in the head camera (15 looking ahead)");
			}
			if (g_ic2Module && !g_scHoldEnabled) {
				SKSE::log::info("HoldSmoothCamInHeadCamera=0 - SmoothCam keeps driving (and offsetting the FOV of) Improved Camera's head camera");
			}
			if (g_ic2Module && !g_holdEntryFrame) {
				SKSE::log::info("HoldCameraOnHeadCameraEntry=0 - the head camera's first frame shows the vanilla third-person camera");
			}
			if (g_debug || (g_ic2Module && g_scHoldEnabled)) {
				REL::Relocation<std::uintptr_t> vtbl{ RE::VTABLE_HUDMenu[0] };
				HUDAdvanceMovie::func = vtbl.write_vfunc(0x05, HUDAdvanceMovie::thunk);
				SKSE::log::info("HUDMenu::AdvanceMovie hooked: SmoothCam hold decided late in the frame{}", g_debug ? ", debug trace on" : "");
			}
			if (g_debug && g_ic2Module) {
				InstallEntryLoggers(g_ic2Module);
			}
		}
	}
}

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SKSE::log::info("ZenICSheatheFix 1.8.0 loading, runtime {}", REL::Module::get().version().string());
	const auto* messaging = SKSE::GetMessagingInterface();
	if (!SmoothCamAPI::RegisterInterfaceLoaderCallback(messaging, [](void* a_instance, SmoothCamAPI::InterfaceVersion a_version) {
			g_scApi = reinterpret_cast<SmoothCamAPI::IVSmoothCam1*>(a_instance);  // every version derives from IVSmoothCam1
			SKSE::log::info("SmoothCam interface obtained (V{})", static_cast<int>(a_version) + 1);
		})) {
		SKSE::log::warn("SmoothCam callback registration failed; the head camera will keep SmoothCam's FOV offset");
	}
	messaging->RegisterListener(MessageHandler);
	return true;
}
