# SkeletonRagdollFix

- **Source:** `src/SkeletonRagdollFix/tools/01-build-rig.py` (generator; `tools/bsa.py` extracts BSA copies)
- **Ships:** a generated loose `meshes/actors/draugr/character assets/skeletons.hkx` (not committed), deployed as the
  MO2 mod `Zenderal - Skeleton Ragdoll Fix`. It must win over XP32 Maximum Skeleton Special Extended, which ships its
  own loose copy.
- **Status:** built 2026-10-22. **Verified in game 2026-10-22:** skeletons ragdoll (limbs bend). Mod sits at priority line 5 of the Ultra `modlist.txt`, above XPMSE (line 908).
- **Rerun** whenever XPMSE (or anything else shipping `skeletons.hkx`) updates: the output is a patch of the winning
  copy.

## The bug

Skeletons (Lost Ones on Mihail's `mihailancientskeletonrace`, the vanilla `Skeleton` race, anything on the
`DraugrSkeletonProject` / `SkeletonS.HKX` rig) flew and fell as a **rigid A-pose**. They had a ragdoll, but it
never bent (user report: "A-pose while in the air, before I hit them").

## Cause [verified from the rig files]

`skeletons.hkx` (Bethesda's, Enderal's `E - Meshes.bsa` copy and XPMSE's alike) welds every limb:
- **14 limb hinges** (thighs, calves, feet, upper arms, forearms, hands, head, jaw) limited to **±1°**, and each
  hinge's axis runs **along its bone** (calf axis (0, −0.18, −0.98)), so even a wider limit would only spin the bone
  around its own length;
- **neck** ragdoll joint: twist ±1°, cone 1°, planes 0;
- only the three spine joints bend (±30°).
- The right foot hinge's two frames also disagree by ~67° at bind pose (Bethesda data), so a locked right foot would
  snap when the ragdoll starts.

The draugr rig (`skeleton.hkx`) has real joints: calves −110..0°, feet −11..+45°, forearms 0..90°, hands about ±20°,
and free ragdoll joints at hips, shoulders and head. The skeleton's bind pose matches the draugr's almost exactly
(calf direction (1, −7, −39) vs (1, −7, −37)).

## Fix

The winning `skeletons.hkx` is **patched in place**, not rebuilt. An XML round trip through hkxconv/HKX2 loses
precision (8,885 bytes changed on a no-op; `FLT_MAX` and sub-1e-6 values move). Only these floats change, in both
copies of each joint the file carries (physics system and ragdoll instance):

| Joint | New hinge axis (world) | Range | + means |
|---|---|---|---|
| Calves, feet, forearms, hands | the draugr's same-side hinge axis | the draugr's | as on draugr (knee flexion is −) |
| Thighs | X (forward/back swing) | −25..+60° | leg forward |
| Upper arms | X | −40..+70° | arm forward |
| Head | X | −30..+20° | − nods forward |
| Jaw | X | −15..0° | − opens |
| Neck (ragdoll joint) | unchanged | twist ±5°, cone 5°, planes ±30° (draugr's) | |

Each hinge's frame A and frame B rotations are rebuilt from the same world (axis, perp, axis × perp) mapped into each
body's bind-pose frame, so the bind pose still reads 0°. Pivots (frame translations) are untouched. Joint blocks are
named through the packfile's own fixups (constraint instance → data pointer), because left and right forearms/hands
have byte-identical data. Convention checks (the generator asserts them): frames are column-major with entities
(A, B), and both frames' axes coincide on every vanilla hinge (except the misaligned right foot). On the draugr rig,
+angle swings the calf's foot forward, so −110..0 is knee flexion.

Verified on the output (22:44 build from XPMSE): same size, 2,192 bytes changed, all inside joint fields; parses with
hkxconv; all 14 hinges' frames agree with 0.0° at bind; ranges as above.

## Which Lost Ones use this rig (survey 2026-10-23, winning records by the Ultra load order)

| Race | Behaviour project | NPCs named "Lost…" | Ragdoll rig |
|---|---|---|---|
| `mihailancientskeletonrace 000800:mihailancientskeletons.esp` | `DraugrSkeletonProject` | 13: Awoken Lost Archer/One/Soldier, Fleshless Lost Archer/Guardian/One/Soldier/Warrior | `SkeletonS.HKX`: this fix |
| `SkeletonRace 0B7998` (EGO's record) | `DraugrSkeletonProject` (female: `DraugrProject`) | 12: Decayed Lost One, Fleshless Lost Hunter/Miner/One, Fleshless Bowman, Awoken Lost Archer, Rotting Lost One | `SkeletonS.HKX`: this fix |
| UCR `LostOneTemplateRace 00398C` | `DraugrProject` | 28 (Lost Archer, Knight, Mage, Warrior, Lords…) | draugr rig, real joints |
| `DraugrRace 000D53` | `DraugrProject` | 23 (Lost One, Sere, Rotting, Fleshmaggot Sufferer, KataPUMB's) | draugr rig, real joints |
| Giant / Elder / Dragon Priest | own projects | 9 (Grotesque, Wild Mage, Lich) | not skeletons |

Mihail's race and `SkeletonRace` share skeleton `SkeletonS.nif`/`SkeletonF.nif`, body-part data `048C13` and the male
behaviour project. They differ only in flags (`SkeletonRace` has `NoKnockdowns`, Mihail's has `CanDualWield`). All six
Mihail meshes (`mihailancientskeleton0–5.nif`, skins `000802`/`00080A`/`00080B`) have the same 52 bones, matching the
rig except the left foot's name (`[Lft ]` vs `[LLft ]`). User report 2026-10-23: Fleshless Lost Warriors and
Archers still looked stiff in flight. Not this rig: they died from the stomp and a stagger then pinned the corpse;
fixed in [`AirborneGetUpFix`](AirborneGetUpFix.md) 1.1.1.

## Conflict check (2026-10-23, all 829 enabled mods / 409 active plugins, Ultra)

- **Loose files** under `meshes/actors/draugr` that could override or bypass the rig: only XPMSE's `skeletons.hkx`
  (priority 780, below this mod at 3). No mod replaces `DraugrSkeletonProject.hkx`, `characterskeleton/
  Draugr_Skeleton.hkx` or `characters/*`, so skeletons still load the `SkeletonS.HKX` rig. `skeletons.nif` (XPMSE) has
  vanilla physics. Pandora's `DraugrBehavior.hkx` is the behaviour graph, not the rig.
- **Mod BSAs:** none contains a draugr skeleton rig, character file or project.
- **Stock Game `Data` and MO2 `overwrite`:** no loose copies.
- **Plugins** carrying RACE records on this rig (records scanned, compressed ones inflated): EGO's `SkeletonRace`,
  Lost Ones Revised's `mihailancientskeletonrace` and Apocalypse's `WB_ConjureDeadeyeCaptain_Race`. All point at
  `SkeletonS.nif` + `DraugrSkeletonProject`; nothing later overrides them.
- Scan scripts: a filesystem/BSA walk (`tools/bsa.py` is importable since 2026-10-23) and a plugin record grep.

## Not covered / risks

- Hips, shoulders and head stay **hinges** (one swing axis), not the draugr's cone joints. Converting the constraint
  type would change object sizes, which an in-place patch can't do.
- A ragdoll that can now bend may tangle differently with Precision's hit impulses or Dismembering Framework's limb
  removal on skeletons. Check both in game.

## Regenerate

```
python tools/bsa.py "<Stock Game>/Data/E - Meshes.bsa" "*actors\draugr\character assets\skeleton*.hkx" <out>   # only if XPMSE is gone
hkxconv <winning skeletons.hkx> skeletons.xml
hkxconv <winning skeleton.hkx> draugr.xml
python tools/01-build-rig.py <winning skeletons.hkx> skeletons.xml draugr.xml <mod>/meshes/actors/draugr/character assets/skeletons.hkx
```
