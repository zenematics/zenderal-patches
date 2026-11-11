# ConvexPlanesFix

- **Source:** `src/ConvexPlanesFix/` (generated: `tools/01-rebuild-convex-planes.py`)
- **Ships:** *(no plugin — 29 generated meshes, MO2 mod `Zenderal - Convex Planes Fix`)*
- **FormID block:** _(none)_

## What it does

**Stops the Ark bank vault crash.** Some third-party meshes ship convex collision hulls whose plane
equations are broken: every normal is `(0, 0, 0)`, and the plane distances fit no face of the hull. A ray
cast against one of those hulls returns a NaN hit distance, and the game's sort of hit points then runs off
the stack. The fix rebuilds each broken hull's planes from its own vertices, which are clean.

Affected (2026-11-03 scan of the Ultra profile, winning copies only): JS Common Cages SE (the 3 long cages),
JS Dwemer Artifacts SE (13 meshes), JS Embalming Tools SE (4), the Sun Temple beacon's dynamo core
(SRP), two Perpetuum Theater clutter meshes, and four flora meshes (Bridges of Enderal, PG Patcher Output).
The JS meshes are the bulk: every convex hull in them is broken, which looks like a fault in their SE
conversion.

## How it was found **[verified 2026-11-03]**

Two crash logs from players, both in the Ark bank:

- **2026-11-03, 1.7.104, Crash Logger 1.25:** `EXCEPTION_STACK_OVERFLOW` at `SkyrimSE.exe+07E98BB`
  (ID 43870+0xAB, `comiss xmm4, [rcx]`), RSI = −16096. The ray came from a city guard's character controller
  and foot IK (`bhkCharRigidBodyController`, `BGSFootIkRaycastInterfaceDB`, `NiPick::Results`). Both guards on the
  stack are in `CapitalCityBankSafe 00990F` ("Ark, Bank", last changed by `Bank of Ark SE.esp`).
- **2026-10-11, 1.5.97, .NET Script Framework:** access violation at `+73CA0A` from
  `PlayerCharacter::PickCrosshairReference`, with the index register at −15954 and XMM0–3 NaN. The stack holds the
  same constants as the newer log (`0x44CF1E0944CD87C3`, `0x3F7FFFFF44E4DA18`, `0x49214F3E49214F3E`), so it is the
  same function on the old engine.

**The crashing function is a quicksort of `hkpRootCdPoint` hits.** It was disassembled from the list's
`SkyrimSE.exe` (MD5 `113faeb71fd8f62b26d0c8627299ab40`, image `+0x7E9810`). Entries are 64 bytes and the key is
the distance at `+0x1C`. The inner loops have no bounds check: `while (pivot < a[j].dist) j--` is
`comiss xmm4, [rcx]; jb`. `comiss` sets CF on an unordered compare, so a NaN pivot keeps the loop going forever. It
walks backwards 64 bytes at a time until it hits the stack guard page, which Windows reports as a stack overflow.
**The cause is any NaN hit distance, not a bad index.**

**Where the NaN comes from.** Bank of Ark places the cage `0084AB` (base `MetalCageLongDouble01 0CE0AD`) in the
vault. It sits about 650 units from guard `044E93`'s spawn, and the guards patrol. Its winning mesh,
`clutter\common\metalcagelongdouble01.nif`, comes from JS Common Cages SE 1.03. All 592 planes in its 48 hulls
have zero normals (the vanilla mesh has no convex hulls at all). Every other mesh placed in the bank cells was
checked first and ruled out:

- MOPP code: the `CollisionMoppFix` walker.
- Compressed-mesh structure (indices, chunks, transforms, NaN floats) and zero-area triangles.
- Box dimensions.

**Plane convention, checked:** outward unit normal, `n·x + w = 0` on the face. 705 of 1299 healthy hulls in
`E - Meshes.bsa` give exactly this computation. The rest are exporter-simplified but still bound every vertex.

## The fix and its checks

`tools/01` resolves the winning copy of every mesh, using `CollisionMoppFix`'s resolver (loose files by MO2
priority, then archives in load order). A hull counts as broken when any stored normal is shorter than 0.5. Its
planes are replaced by the distinct outward faces of the convex hull of its vertices, found by brute force (hulls
have 8–40 vertices). The faces are repeated to fill the stored slot count, which keeps the block size the same.
When the hull has more faces than slots (5 meshes), the block grows and its entry in the header's block-size
array is updated.

Asserted for each mesh:

- every face is a supporting plane touching ≥ 3 vertices;
- the file still parses, and every unedited block is byte-identical;
- the footer is unchanged.

Rerunning the fix on the output finds nothing to do (checked on all 29).

## Keeping it right

- MO2 mod **directly above PG Patcher Output**, next to `Zenderal - Collision MOPP Fix`; there are no shared files
  between the two. PG Patcher Output wins two of the flora meshes, so this mod must outrank it.
- **Rerun `tools/01` after PG Patcher runs, after any mesh mod change, and after a load-order change.**
- The meshes are other authors' work, so they are generated, not committed.

## Status

Built and written to `E:/Zenderal/mods/Zenderal - Convex Planes Fix` 2026-11-03. It is enabled in Ultra directly
above PG Patcher Output. **Unverified in game.** The crash needs a ray to reach the cage, so "no crash" in one visit
proves little. A bank crash with the same stack after this mod is enabled would prove the diagnosis wrong.

**Shipping:** the meshes are generated, so Wabbajack can match them to no download. On 2026-11-05 the mod got an
`Include` rule in `Zenderal.compiler_settings`, next to Collision MOPP Fix's (backup:
`E:/Zenderal-backups/2026-11-05-convex-include/`). Without it, the compile reports the 29 meshes as unmatched.

**Third log (2026-11-04, a player without the fix):** the same fault, `EXCEPTION_STACK_OVERFLOW` at
`SkyrimSE.exe+07E98BB` (43870+0xAB), RSI = −16074, in `CapitalCityBankSafe 00990F`.

- This time the ray was the **player's crosshair pick** (`26127` from Improved Camera's `CrossHairPickData_Pick`
  hook, `40620`). The guards' foot IK is not the only way to reach it: any ray into the vault can.
- The player was on the list release from before 2026-11-03, so this is not evidence against the fix.

**Two more logs (2026-11-09 18:56 and 19:00), outside the bank.** These come from the same player as the 11-04 log, with the same install path. That player is on a list with TRP 0.6.5, so a release built after the 2026-11-05 Include rule.
- **18:56, first person.** The pick came through Improved Camera, as in the bank log (`26127` from `40620`). RSI = −16084. JS Dwemer Artifacts' `clutter\dwemer\dwarvenscrap2.nif` (its fade node, shape and decal node) is on the stack. That mesh is one of the 29 this fix repairs (28 broken hulls).
- **19:00.** SmoothCam's camera cast (`33007` → `43870`). RSI = −15129. The player was in The Hollow Hand (`DesertHohleHand 11F9C5`), next to ref `122475`, a Riften interior floor (`RifRmSmSecondFloor01`). Base Enderal, FS, EGO and Kata Hidden Powers place none of the 29 meshes in that cell (975 refs checked).
- **On the curator's install the fix is in order.** The mod is ticked and sits above PG Patcher Output, JS Dwemer Artifacts and JS Common Cages. Its Include rule is in place. A dry run on 2026-11-11 found exactly the same 29 meshes and nothing new.
- **Both crashes were in The Hollow Hand.** The 18:56 stack's `Cat` `FE041870` is House Cats of Enderal's ref `000870`: object `0x870` in its light-plugin slot `0x041`, and House Cats places it in this cell.
- **The cell's own meshes are clean** (scan 2026-11-11, read-only, in a scratch script):
  - The winning refs come from all 469 enabled plugins. 977 refs: Skyrim.esm 972, FS 3, EGO 2, House Cats 1, Kata 1. None has a non-finite placement or a zero scale.
  - Every winning mesh, plus the four actor skeletons (human male/female from XPMSE, skeever, Mihail's house cat), 237 in all, was checked for NaN/Inf, zero convex normals, zero box/sphere sizes, zero-length capsules, singular transform shapes, compressed-mesh transforms and packed-strip vertices. Nothing turned up.
- **The only bad collision at the scene is the scrap.** `clutter\dwemer\dwarvenscrap2.nif` belongs to two loot MISC items, `DwarvenScrapBent 0C886C` (EGO's record) and `DwarvenScrapBentNoValue 0EEFC2`, never a placed object. So it was a dropped item lying in the cell. It has to have been dropped by the player or by Death Drop Overhaul, whose DLL is on the 19:00 stack.
  - JS Dwemer Artifacts' copy has 28 convex hulls whose normals are all zero; this fix's copy has none.
  - A dynamic body with broken hulls can also turn its own transform to NaN once it collides. After that, any ray near it gets NaN, which fits a second crash in the same room after a reload.
- **Correction, same day: the player probably does have the fix.** The crash log's plugin list dates their release: it holds plugins first built on 2026-11-06 (Myrad Flight Price, Ancient Ruins Water Fix) and 2026-11-09 (Meditation Water Fix, FHR Directional Frequency), so the list was compiled after this mod's Include rule. The current `Zenderal.wabbajack` (0.9.9.1) carries all 29 meshes inline, with the mod ticked above PG Patcher Output and JS Dwemer Artifacts in both shipped profiles. Crash Logger lists plugins and DLLs, never loose meshes, so the log cannot show the mod itself.
- **So the NaN at The Hollow Hand is still unexplained** unless the player changed their MO2 order. Next step: their save from before the crash, loaded on the curator's PC with the fix in place. A crash there can be traced; no crash points back to their install.
