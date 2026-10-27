# PrecisionFork

> **REINSTATED 2026-10-16 — turning hit impulse off is NOT enough.** From 2026-10-13 the list ran the
> official Precision with `bApplyImpulseOnHit = 0` (in `Zenderal - Settings/MCM/Settings/Precision.ini`)
> instead of this fork. On 2026-10-16 Ice Elementals **and crystal elementals** rose off the ground on
> hits again, while `Precision.log` showed that ini being read and nothing in the list had changed
> Precision. **[verified]** So the float is the active-ragdoll pose offset on `bhkRigidBodyT` bodies, which
> Precision drives on every hit whether or not it applies an impulse. The impulse-off test of
> 2026-10-12 was too short to catch it. Crystal elementals (`_20E/_40E_CrystallElemental`) use
> `AtronachFrostRace 0131F6`, and the Crystal Golems replacer's `skeletoncrystalgolem.nif` also has
> `bhkRigidBodyT` limb bodies, so the same fix covers them. `src/PrecisionFork/` was restored from
> `7b63d3a`, byte-identical to the deployed DLL. Redeployed the same day as MO2 mod
> `Zenderal - Precision Fork`, directly above `Precision`. **Verified in game 2026-10-16: neither
> creature floats any more.** Hit impulse stays off. The fork also fixed the float with impulse on
> (2026-10-12), so turning impulse back on is now just a matter of taste.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/PrecisionFork/`
- **Ships:** *(rebuilt `Precision.dll` + `Precision_ZenderalFixes.ini`, MO2 mod `Zenderal - Precision Fork`, sorted directly ABOVE `Precision`)*
- **FormID block:** _(none)_

Earlier failed routes: [`PrecisionLiftFix.md`](PrecisionLiftFix.md).

> **2026-10-27: `0001` re-ported to 1.7.104. Floating ice/crystal elementals were back** because the hooks
> never installed after the 1.7.104 update (log below). Not hit impulse: the winning `Precision.ini`
> (`Zenderal - Settings`) still has `bApplyImpulseOnHit = 0`, and `Precision.log` reads it. **[verified]**
> The 1.7.104 `SkyrimSE.exe` on disk is **not** encrypted, so the sites were read straight from it (Address
> Library format 5 + capstone). The compiled code matches 1.5.97, so each site is the same offset into the same function.
> **[verified]**
>
> | Hook | 1.5.97 site → target | 1.7.104 site → target | How found |
> |---|---|---|---|
> | write | `9EC0B5` → `B12210` | `AC8055` → `BF0FE0` | driveToPose = the call Precision hooks at ID 63562 `+0x256` (→ `AC6FB0`); `+0x10A5`, `rcx=[rsi+0x98]`, stack arg 0 |
> | read | `B16228` → `A70CE0` | `BF4FF8` → `B4F5A0` | `add rcx,0x150` at function `+0x48`; function `BF4FB0` (controller `+0x3FD0`, same distance as SE) |
> | bones | `9ED4B5` → `B0DCD0` | `AC9455` → `BECAA0` | ID 58304 (`AC9350`) `+0x105`, stack arg `2` |
>
> `NiRTTI_bhkRigidBodyT` (ID 411581 → `33377F8`) checked: its initializer at `ECC47` loads the `"bhkRigidBodyT"` string.
> Not checked: the `bhkRigidBodyT +0x40/+0x50` field offsets on AE (assumed unchanged, like the rest of the bhk layout).
> `Install()` picks the 1.5.97 or 1.7.104 table and logs anything else. Rebuilt with `build.cmd`, deployed to **both**
> `Zenderal - Patch Collection` (the copy that wins: `Zenderal - Precision Fork` is disabled in `Ultra`) and the
> fork mod. Previous DLLs are in `E:/Zenderal-backups/2026-10-27-precision-fork-ae-hooks/`. **Verified in game
> 2026-10-27: frost atronachs no longer lift off the floor when hit (curator).** At
> load, `Precision.log` must show `ZenRagdollFixes: driveToPose (rigidBodyT write) hooked at AC8055` and
> `… approxTransformAt (rigidBodyT read) hooked at BF4FF8`.
>
> **2026-10-22 (superseded): the `0001` hooks are inactive on 1.7.104.** `Precision.log` says *"ZenRagdollFixes: runtime 1-7-104-0
> is not 1.5.97 - addresses unknown, nothing patched"*. The fork still loads as plain Precision, but the frost-atronach
> fix needs its three call sites re-found in the 1.7.104 executable. Ice/crystal elementals may float again.
>
> **Ruled out the same day:** enemies frozen rigid mid-air after Seismic Stomp. Precision's `RemoveRagdollFromWorld`
> keyframes ragdoll bodies when `CanRemoveRagdollFromWorld` is false. A patch skipping that for actors in
> `IsInRagdollState()` was built, did not fix it in game, and was rolled back (DLL restored byte-identical from
> `E:/Zenderal-backups/2026-10-22-precision-fork-pre-ragdoll-fix/`). The curator narrowed it to Seismic Stomp +
> dismemberment: see [`LostOnesDismembering.md`](LostOnesDismembering.md).

## Frozen mid-air ragdolls (2026-10-22, patch `0002`, ROLLED BACK)

> **Rolled back the same day: `0002` did not fix the freeze in game.** The real cause is the engine starting a
> get-up mid-air after a hit, plus staggers on ragdolled actors: see [`AirborneGetUpFix.md`](AirborneGetUpFix.md).
> Kept below as the record of a ruled-out route; the shipped fork has `0001` only.

**Symptom:** enemies knocked into a ragdoll (Seismic Stomp's launch, but any knockdown does it) and then hit while
airborne stayed rigid in the air and never fell. Seen on skeletons and Wood Elementals (spriggans).

**Cause, read in Precision 2.0.6's source:** each frame, `HavokHooks` (Hooks.cpp around line 438) queues an actor's
active ragdoll for removal when `IsRagdollAdded && !IsRagdollAddedToWorld`, which is exactly the moment the engine
swaps in its own knockdown ragdoll. `RemoveRagdollFromWorld` then asks `CanRemoveRagdollFromWorld`, which is false
for any actor in `IsInRagdollState()` (and for furniture users and `AllowRagdollCollision` races), and in that
branch calls `Utils::SetBonesKeyframed`. That sets every ragdoll body to `hkpMotion::kKeyframed`, so the engine's
dynamic knockdown ragdoll stops simulating and holds its pose wherever it is. Our patch `0001` hooks (bhkRigidBodyT
only) are not involved: the winning skeleton meshes for draugr/skeletons and spriggans have no T-bodies.

**Fix:** patch `0002-zenderal-keep-engine-ragdolls-dynamic.patch` keyframes only when the actor is **not** in a
ragdoll state. Furniture users and ragdoll-collision races keep Precision's behaviour. Apply after `0001`.
Rebuilt with `build.cmd` (SE + AE), and the previous DLL is in
`E:/Zenderal-backups/2026-10-22-precision-fork-pre-ragdoll-fix/`. **Unverified in game.** Enemies already frozen
in a save are fixed by selecting them in the console and running `disable`, then `enable`.

## What it does

**Fixes the floating Ice Elementals** (see `PrecisionLiftFix` for the four failed routes). ersh1/Precision **2.0.6** (`9ef45e0d8d`, 2026-09-01 — same version/timestamp as the installed Nexus archive) built from source by `src/PrecisionFork/build.cmd` (clone `upstream/`, gitignored) against **CommonLibSSE-NG `8339e6d`** (alandtse/CommonLibVR, 2026-09-02 02:09:16) in `lib/` (gitignored): the parent of `231543d`, which added Havok types (`hkbGeneratorOutput`, `bhkRigidBodyCinfo`, …) that clash with Precision's own `Havok.h`; `d27f409` on the same branch is libxse-style and lacks NG APIs Precision uses (`REL::VariantOffset`, `SKSE::RUNTIME_SSE_1_7_99`). Unmodified build verified in game first (same exports/deps/version; behaves like the official DLL). **Our change** (`patches/0001-zenderal-frost-atronach-ragdoll-fixes.patch`, apply to `upstream/` at `9ef45e0d8d`; new `src/ZenRagdollFixes.{h,cpp}` + 7 `// ZP` lines): PLANCK's three frost-atronach active-ragdoll hooks ported to SSE 1.5.97, each call site byte-verified before `write_call<5>`: write `0x9EC0B5` (in `hkbRagdollDriver::driveToPose 0x9EB010`, → `hkaRagdollRigidBodyController::driveToPose 0xB12210`, `this` = driver `+0x98`, stress arg 0) — apply each `bhkRigidBodyT`'s offset (`+0x40` rotation, `+0x50` translation) to the bone's target; read `0xB16228` (in `hkaRagdollInstance::getApproxWorldFromBoneTransformAt 0xB161E0`, → `hkpMotion::approxTransformAt 0xA70CE0`, rcx = body `+0x150`) — remove it; bones `0x9ED4B5` (in `mapHighResPoseLocalToLowResPoseLocal 0x9ED3B0`, → `hkaSkeletonMapper::mapPose 0xB0DCD0`, source arg 2) — `NO_CONSTRAINTS` (0). Write and bone fixes act only on ragdolls containing a `bhkRigidBodyT` body; the read fix only touches T bodies. **SSE `SkyrimSE.exe` is DRM-encrypted on disk** — the addresses came from a decrypted image written by the throwaway SKSE plugin `src/PrecisionFork/tools/memdump` (must sort before `Precision.dll` alphabetically: `000_ZenMemDump.dll`, or Precision's hooks hide the original call targets). Switches in the ini. **Verified in game 2026-10-12: write + read alone fix it — Ice Elementals no longer float on Precision hits**, other enemies unchanged, no crash; log `ZenRagdollFixes: … hooked at 9EC0B5` / `… at B16228`. Bone-length fix not needed, shipped `false`. There is no death ragdoll to check: frost atronachs shatter on death (`AbFXAtronachFrost`'s `atronachfrostscript` `deathExplosion`) instead of leaving a ragdoll corpse, so the fix only ever affects the live hit reaction. GPL-3.0: publish source + patch, credit ersh1 (Precision) and adamhynek (PLANCK). Rebuild for every Precision update.
