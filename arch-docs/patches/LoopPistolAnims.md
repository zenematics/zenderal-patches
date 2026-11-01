# LoopPistolAnims

- **Source:** `src/LoopPistolAnims/`
- **Ships:** *(no plugin — OAR mod, MO2 mod `Zenderal - Loop Pistol Animations`)*
- **FormID block:** _(none)_

## What it does

**Simple Pistol Shooting Animation by Loop 3.0 (Nexus 44201) never played on the flintlock pistols.** The
mod is a legacy DAR mod: `_CustomConditions/12345` (aim, fire, idle, movement, 40 clips), `12346`
(`staff_idle` while moving), `12347` (standing turns), `12348` (release for its own keyword `0x822`). It fires
on a **left-hand** staff carrying `Pistol_Animation_By_Loop 0x801:Pistol animation by Loop.esp`.

The keyword half worked: the KID ini `AdventurerFlintlockPack_PABL_KID.ini` targets
`AdventurerFlintlockPack.esp`, which is A Gentleman's Flintlock Armoury's plugin, and the KID log
(2026-10-17) reads `Pistol_Animation_By_Loop [0x801~Pistol animation by Loop.esp] added to 8/588`. OAR
loaded the folders as legacy mods with no warnings.

**The priority half lost.** DAR priority 12345 is below every staff submod in the list that replaces the
same clips (enabled-mod scan of profile `Ultra`, 2026-10-17):

| Submod | Priority | Conditions | Takes |
|---|---|---|---|
| Goetia Enchanted Staves `Main` | 68000 | **none** | all `stfmagic_*` aim/release, `staff_idle`, staff turns |
| Goetia Enchanted Staves `Staves blend override` | 68360 | drawn + staff in either hand | all `magcast_*` movement |
| Goetia Enchanted Staves `Shield & Staff` | 68364 | shield left + staff right | n/a for a left pistol |
| Goetia Sneak Magic `68445` | 68445 | sneaking + staff | `stfmagic_*`, `staff_idle` |
| Smooth Moveset `Base - 1hm` | 83030000 | right hand unarmed or one-handed | `magcast_*` movement |
| Smooth Moveset `1hm/Staff` | 999999010 | staff in either hand | `staff_idle` |

**Fix:** `tools/01-build-loop-pistol-anims.py` copies Loop's clips from the installed mod into four OAR
submods at priority `1000000000 + <DAR folder>` (above Smooth Moveset, below RaySense's cover loops at
2110000004+), keeping the folders' relative order. DAR's condition files bind OR tighter than AND, so each
folder reads `drawn AND left staff AND (Vigilant pistol OR Glenmoril keyword OR Loop keyword) [AND direction]`;
Vigilant.esm and Glenmoril.esm are not in the list, so only the Loop keyword is kept. Loop's original folders
stay installed and simply keep losing. The clips are not committed (Loop's assets).

**v1 failed in game (2026-10-17):** OAR's Animation Log showed `StfMagic_Release`, `_ReadyLoop`, `_PreReady`,
`_ChargeLoop`, `_PreCharge` all `[Replaced]` by Goetia Enchanted Staves / `Main`, so v1's conditions (Loop
keyword on a **left-hand** staff, as Loop wrote them) failed. Which half failed was not captured (the trace
was not read). **v2** matches `drawn AND (any of the 8 pistols 816–819/834/838–83A:AdventurerFlintlockPack.esp
by IsEquipped, OR the Loop keyword, either hand)`, so neither the hand nor KID can make it fail. Loop's clips
were authored for the left hand; how they look on a right-hand pistol is untested.

**v2/v3 in game (2026-10-17): the animations play, but the gun droops.** The player held the pistol in the
**left** hand throughout (the right-hand theory in between was a misreading of a screenshot). Six of Loop's clips
(`stfmagic_precharge/chargeloop/preready/readyloop/preaimcon/aimconloop`) are one identical file, the aim pose,
so charge time does not matter.

**The clips are LEFT-hand clips (forward kinematics, 2026-10-17).** Read with PyNifly's `hkx/anim_skyrim.py`
(tracks map 1:1 to XPMSSE `skeleton.hkx` bones; the clips carry no bone names). In `stfmagic_readyloop` the left
arm reaches 36 units forward at shoulder height and the left attach node `Shield` has +Y = (0.03, 1.00, −0.02),
level forward, +X straight down. `stfmagic_release`: level for the shot, then recoils to upright (+80–85°);
`staff_idle`: pistol upright by the shoulder (+75°, seen in game exactly so). So **left hand only** (the left-hand
submods), and the mesh needs its barrel on
the attach node's +Y. The Gentleman's staff meshes have the grip on +Y and the barrel slanting 30° toward +X,
which is the droop: barrel 30° down, butt lying back along the wrist.

**The equipped model is the FirstPersonModel static, in third person too [verified in game 2026-10-17].**
Two rounds of rotated meshes on the WEAP `Model` "changed nothing", and Loop's own `pistol.nif` swapped in
(`tools/02 --test-loop-mesh`) looked the same: 3×-scaled copies at the WEAP Model path stayed normal size,
3× copies at the original paths (used only by the statics `00080A–000811`, `000833–000837`) turned the held
pistol giant. So the Flintlock Overhaul overrides the 8 **statics** to the rotated copies and leaves the WEAP
`Model` (world/dropped model) original, which also keeps dropped pistols' collision matching. First person
draws the same static, so it shows the rotated mesh too — unchecked.

**Mesh rotation (`tools/02-build-pistol-meshes.py`).** Side-view overlays of the vertices: Loop's `pistol.nif`
has the barrel straight along +Y (X −4…+1 from Y 14 to 42) and the grip angled back toward +X; the Gentleman's
pistols have the grip along +Y and the barrel slanting toward +X (FlintlockPistol* 30°, Pistool* 21–26°). Each
of the 8 meshes gets a copy at `meshes\Zenderal\LoopPistols\<family>\<name>.nif` (in this MO2 mod) with its single
NiTriShape rotated about Z (25.8° / 19.6° / 21.4° / 24.0°), which lays the barrel on Loop's and keeps the grip
at the hand. Only the 52-byte transform changes (the meshes are Skyrim LE, BS stream 83; rotation is stored
row-major, checked against Pistool02's own transform). **Coupling:** without this MO2 mod the equipped pistols
have no mesh. **v4 (statics) in game 2026-10-17: aims level**, but the stock rode ~35 px above the wrist (~9 px/unit), so **v5** moves every copy 4 units along the attach node's +X (down; `DROP` in `tools/02`) so the grip sits in the fist. **v5 verified in game 2026-10-17: level aim, grip in the fist (left hand).** Still unchecked: first person (same static, rotated mesh), the Flintlock Overhaul reload after Loop's release clip, NPCs with LeftHand-only pistols.

**Right hand (v6/v7, 2026-10-17).** v6 let the left-hand submods match the right hand too: the right hand still
played the list's staff animations, because a right-hand staff uses **its own files** — vanilla ships
`stfmagicright_*`, `staffright_idle`, `staffmagicright_runarm/walkarm` next to the left-hand set (BSA listing).
**v7** adds four `(right hand)` submods (priority +1000) with **mirrored** copies of Loop's clips
(`tools/mirror_hkx.py`): per frame, FK to model space, reflect across model X, take each bone from its L/R partner
(`Shield` ↔ `Weapon`), rest-pose correction, back to local. The `Weapon` node gets the reflected `Shield` frame
turned 180° about +Y, since the pistol mesh is not mirrored (plain reflection put the grip up). Checked by FK: in
aim, fire and idle the right `Weapon` node equals the left `Shield` node with X negated, grip down; a double
mirror returns the clip within 0.08°. Files: `stfmagic_*` → `stfmagicright_*`, `staff_idle` → `staffright_idle`,
`staffmagic_*arm` → `staffmagicright_*arm`; shared movement/turn files swap left ↔ right (a mirrored left
sidestep is a right sidestep). PyNifly's writer drops `extractedMotion`; Skyrim reads locomotion motion from
the behaviour's animation data by clip name, so this should not matter. The pistols stay EitherHand. Note:
Loop's `stfmagic_release` carries no `Spellfire` annotation (vanilla: 0.33 s), only a credit tag. v7 built
2026-10-17; **v7 in game: aim and idle right, but moving glitched the legs and the body jittered**
(recording 2026-10-17 16:50). Mirroring swaps the feet, so each mirrored stride planted its feet half a stride
off the timing the other locomotion clips/layers are synced to. **v8:** the looping strides (`mag_run*`,
`magcast_run*`, `magcast_walk*`; last frame closes the loop) start half a stride later (`half_cycle` in
`mirror_hkx.py`); FK check: the new clips' foot trajectories follow the originals' frame for frame. Turns, idle
and aim are not shifted. **v8 in game (recording 16:56): still glitchy — legs snapped into splits/crouches while running.**
Other layers (Smooth Moveset base locomotion, TDM) drive the legs on the ORIGINAL clips, so any mirrored lower body
fights them. **v9:** movement and turn clips (`mag_*`, `magcast_*`, `staffmagiccast_turn*`) keep Loop's hips and legs
untouched (same file names, no left/right swap) and mirror only the spine and above, relative to the pelvis
(`upper_only` in `mirror_hkx.py`); in looping strides the upper body comes from half a stride later so the free arm
swings against the opposite leg. FK check: lower-body tracks within 0.04° of Loop's; the right `Weapon` node relative to
the pelvis is the left `Shield`'s with X negated. Aim, fire and idle stay fully mirrored. **v9 in game: still glitched** (recording 20:00 with the OAR Animation Log:
every clip playing was ours — `StfMagicRight_ReadyLoop/ChargeLoop` together with `MagCast_RunForward/WalkForward`;
torso turned sideways, legs hopping, only when running right-handed; the left hand runs clean, aiming or not).
v10 (upper body mirrored relative to the pelvis for every clip) was dropped untested: Loop's aim stance turns the
pelvis 33°, so that swung the right-hand aim ~64° off forward (FK).

**v11 — Bethesda's pattern.** Vanilla's right-hand staff clips (`stfmagicright_readyloop`, `staffright_idle`,
`stfmagicright_release`) have **pelvis, legs and spine identical to the left-hand clips (0.0°)** and differ only in
the arms. So every right-hand clip now keeps Loop's 72 body bones untouched and mirrors only the two clavicle subtrees
(`mirror_arms` in `mirror_hkx.py`): model-space reflected rotations from the partner bone, rest-corrected, own local
translations, `Weapon` turned 180° about +Y; in looping strides the arms come from half a stride later. FK check:
body bones within 0.05° of Loop's; right-hand aim barrel (−0.03, 1.00, −0.02), grip down, gun at the right shoulder
(20.4, 41.9, 93.7). Movement files keep their own names. **v11 in game (recording 20:09): torso fixed, legs still hop** (one leg kicks
up behind while running and aiming right-handed); the OAR log again showed only our clips.

**v12 — the file header.** Every PyNifly-written clip had `blockDuration` = clip length (0.73 s for the run) where
Loop's Havok exports carry the standard `(maxFramesPerBlock − 1) × frameDuration` (8.9 s). The cause was ours:
`mirror_hkx` zeroed `num_blocks`/`block_duration` before writing (copied from the musket aim fix), and PyNifly then
fills in the clip length. Havok's spline decompressor uses blockDuration to locate frames in a block, so the legs of a
multi-frame cycle could sample the wrong frames; the 4-frame aim clips would hide it. v12 keeps the source header: all
46 right-hand clips now match Loop's duration, frames, frameDuration, blocks, blockDuration and blend hint exactly.
**Same latent issue in `src/FlintlockOverhaul/tools/06-build-musket-aim-fix.py`** (zeroes them too). **v12 verified in game 2026-10-17: right-handed running and aiming are clean.** Both hands now work: left = Loop's
clips, right = arms-only mirrors. Still unchecked: first person (rotated static), the reload after Loop's release clip,
NPCs.

**A new OAR folder is invisible until the CRDW cache is rebuilt** (see [`StaffDrawFix`](StaffDrawFix.md)).

Built 2026-10-17. **Not yet verified in game:** confirm with OAR's animation log that `StfMagic_Release`
etc. play from `Zenderal - Loop Pistol Animations`, and that the Flintlock Overhaul reload still fires
(it hooks `OnActorAction` Spell Fire, which comes from the release clip's annotation).

**Reversal Shadow (2026-10-18).** `tools/01` also matches `ZP_ReversalShadow 800:Zenderal - Reversal Shadow.esp` by
form (`EXTRA_PISTOLS`). It carries the Loop keyword `801`, yet in game it did not get these animations with the keyword
condition alone; why is open. Add any further pistol here by form, not by keyword.
