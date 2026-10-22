# LostOnesDismembering

- **Source:** `src/LostOnesDismembering/`
- **Ships:** MO2 mod `Zenderal - Lost Ones Dismembering`, built locally and not in `build/manifest.json`:
  `Zenderal - Lost Ones Dismembering.esp` (ESL), `SKSE\DismemberingFramework\Zenderal_LostOnes_{LIMBS,DATA}.json`,
  and generated meshes under `meshes\DismemberingFramework\Zenderal\{LostOnesSkeleton,Minotaurs}\` (not committed)
- **FormID block:** `0x800–0x804` skeleton limb MiscItems, `0x805–0x832` minotaur limb MiscItems (`0x833–0x83A` reserved for the shelved spider legs)

## What it does

**Every Lost One can be dismembered: the draugr-bodied ones drop DF's draugr limbs, the skeletons drop
skeleton limbs.** Dismembering Framework (DF) picks severed-limb meshes by the actor's race **EditorID**,
then skin, then sex. Its Official Creature Asset Pack only lists `DraugrRace` (Enderal's is
`000D53:Skyrim.esm`). **[verified 2026-10-19]** Winning race per Lost One across UCR → our UCR×EGO patch →
`mihailancientskeletons.esp` → `Lost Ones Revised - EGO Patch.esp` (loads last):

| Race | NPCs | Before | Now |
|---|---|---|---|
| `LostOneTemplateRace` `00398C:Undead Creatures Replacer.esp` | 72 | never dismembered | DF's naked draugr limbs + body caps |
| `mihailancientskeletonrace` `000800:mihailancientskeletons.esp` | 37 | never dismembered | skeleton limbs |
| `SkeletonRace` `0B7998:Skyrim.esm` | 11 | never dismembered | skeleton limbs |
| `DraugrRace` | 9 | DF's draugr limbs | unchanged |

### How DF is built (what the patch plugs into)

- **Flying limb** = a MiscItem (`DFDefaultLimbRefScript` + five DF globals, keyword `000802:Dismembering Framework.esm`)
  whose model is a rigid limb nif: every shape is skinned to one `Root` node whose skin-to-bone rotation
  is the real limb bone's bind rotation, and the vertices are the body's own bind-space vertices
  (DF's draugr forearm matches the vanilla draugr body to a median 0.0 units).
- **Body cap** = an ARMO/ARMA pair. One `Dismembered_Addons.nif` holds every stump (`AA:<Limb>:Bone/Gore/Skin`).
  The ARMAs are **race-locked to `DraugrRace`**, so on any other race the cap renders nothing.
- **JSON**: `*_TEMPLATES.json` (RefNode, BipedSlot, blood art object, Translation; actor addon ARMO + art),
  `*_LIMBS.json` (template list + `LimbFormID`), `*_DATA.json` (race → skin → sex → node → limb IDs). DF
  parses every TEMPLATES file, then every LIMBS file, then every DATA file (`DismemberingFramework.log`), so
  our files can reference the pack's templates and IDs.
- DF hides the cut part on the body by bone, not by mesh partition. The vanilla draugr body has only
  partitions 30/32/33 and DF's draugr calves still work; the UCR and Mihail bodies have only 32 (+33).

### The three generators (run in order; all assert what they write)

1. `tools/01-build-lost-ones-data.py`: writes both JSON files. `LostOneTemplateRace` gets the pack's
   `DraugrRace → ANY` entries verbatim (forearms, calves, 18 male / 6 female head variants). That race is
   a draugr in all but name: same `Skeleton.nif`, `DraugrProject.hkx`, body part data `048C13`, bodies
   on vanilla `draugr.dds`. The two skeleton races get five `Zenderal - Skeleton - *` limbs on both sexes.
   Each reuses the pack's **male** draugr base-data and actor-addon templates, because the meshes are
   built inside the male draugr limb nifs.
2. `tools/02-build-records.py`: from `reference/mods/DFOfficialCreaturePack` (serialize
   `DF - Official Creature Pack.esp` with the spriggit-decompile-reference skill):
   - five MiscItems `0x800–0x804`, each DF's naked male draugr limb item copied verbatim with a new
     EditorID and model;
   - DF's five draugr body-cap ARMAs `000805–000809` overridden with `AdditionalRaces: 00398C`, so the
     flesh Lost Ones get their stump caps.

   The skeleton races are deliberately left off: a bare skeleton needs no flesh cap, and the
   race-locked ARMA renders nothing on it.
3. `tools/03-build-skeleton-limbs.py <pynifly dir>`: opens each DF draugr limb nif (collision, BloodFX/Origin
   nodes and `Root` transform kept). It adds the triangles of Lost Ones Revised's `mihailancientskeleton2.nif`
   `skeleton` shape whose three vertices are all dominated by the limb's bones (calf+foot+toe,
   forearm+hand+fingers, head+jaw), skinned rigidly to `Root` with DF's own transforms and Mihail's
   shader/textures. It then detaches DF's flesh shapes (Skin, Gore, Bone, eyes). Mihail's skeleton shares
   the draugr bind pose (skin-to-bone rotations equal, translations within 0.07; asserted). **Variant 2 is
   the source because it is bare-handed:** in 0, 3, 4 and 5 a hand is an `armor.dds` gauntlet and the
   skeleton stops at the wrist (144 forearm tris instead of 794). Output: calves 498 tris, forearms 794,
   head 1124, each inside the matching DF draugr limb's bounds.

Build and deploy (no manifest entry: the meshes are other authors' work, generated from the user's install):

```
python src/LostOnesDismembering/tools/01-build-lost-ones-data.py
python src/LostOnesDismembering/tools/02-build-records.py
python src/LostOnesDismembering/tools/03-build-skeleton-limbs.py "<$Tools.pynifly>"
spriggit deserialize src/LostOnesDismembering/LostOnesDismemberingESP -> <mod>/Zenderal - Lost Ones Dismembering.esp
copy src/LostOnesDismembering/SKSE/DismemberingFramework/*.json -> <mod>/SKSE/DismemberingFramework/
```

The plugin masters Skyrim, Update, FS, `Dismembering Framework.esm`, `DF - Official Creature Pack.esp`,
`Undead Creatures Replacer.esp` and `DF - Xtudo Creature Pack - Canidae - A Wolf Replacer.esp`. It loads
after those and **before** `Fluffworks - Dismembering Framework Patch.esp`, and it must be the only one of
our plugins overriding DF's draugr and wolf ARMAs. Built 2026-10-19: Spriggit round trip identical, ESL, HEDR 1.7.
Enabled in Alpha 0.6 (mod above `DF - Official Creature Asset Pack`, plugin right after UCR). Ultra
must be ticked in MO2 (mod + plugin). In Alpha 0.6 the skeleton races don't exist, and DF only skips them.
**Not checked in xEdit.** Lost Ones (draugr-bodied and skeleton), wolves and minotaurs **verified in
game 2026-10-19**. Rebuild CRDW after deploying.

## Wolves (added 2026-10-19)

**Most Enderal wolves were never dismembered, because DF's wolf data only lists `WolfRace`.** Enderal
moved its common wolves onto its own races. **[verified 2026-10-19]** Winning race per wolf NPC
(base → FS → EGO):
- `WolfRaceSmall` `0133EF:FS`: the Coastprawlers `047C3C`, `01A4E0`, `07FA85` and `1377B6`.
- `WolfRaceLarge` `0133E3:FS`: `_10E_Wolf` `07B30B`.
- `WolfHoheRace` `117FCC`: `_00E_MQ09Wolf` `0EAB9F`.
- 14 others stay on `WolfRace` (hungry/snow/elemental wolves) and already worked.

All four races share `Actors\Canine\Character Assets Wolf\skeleton.nif` and skin `04E886`. Canidae's
replacement skeleton keeps every bone DF's wolf templates name (`Canine_Head`, `Canine_*Leg2`, `Canine_Tail1`).
Enderal wolves do wear DF's two skin-specific sets: black `SkinWolfBlack 0C02FB` (5 NPCs) and
"red" `SkinWolfSummon 0C02F8` (`_10E_Wolf`).

- `01` copies the pack's whole `WolfRace` entry (black, red, `ANY`) onto
  `WolfRaceLarge|WolfRaceSmall|WolfHoheRace`. With the Fluffworks DF patch enabled, its LIMBS/TEMPLATES
  redefine the black/red IDs by name, and the copy follows them.
- `02` forwards DF's 18 wolf body-cap ARMAs (Default `000868/86F–872/874`, Black `000880–883`,
  Red `000884–88B`) from their winner, `DF - Xtudo Creature Pack - Canidae - A Wolf Replacer.esp` (now a
  master, so the plugin loads after it), with those three races added. Source:
  `reference/mods/DFXtudoCanidae`. The plugin **owns** these 18 ARMAs.
- **Fluffworks DF patch (on in Ultra, off in Alpha 0.6):** it overrides `000880` with ~100 alternate fur
  textures and points the black/red ARMOs at its own new ARMAs. **Load this plugin before
  `Fluffworks - Dismembering Framework Patch.esp`**, or `000880` loses Fluffworks' textures. With it on,
  black/red stump caps don't show on the three Enderal races; their limbs still drop.

Test spawns: `player.placeatme 07B30B` (Large, red skin), `047C3C` (Small), `0FE4B3` (`WolfRace`, control).

## Minotaurs (added 2026-10-19)

**Minotaurs had no DF data at all.** Minotaurs SE (`1Minotaurs.esp`; the Enderal build in
`4thUnknown Minotaurs In Enderal` wins in MO2) and `MinotaursInEnderal.esp` (loads after it; overrides
the NPCs/ARMAs and adds Celtic/Forsworn/Ancient/Half-Minotaur skins whose meshes come from the
`Forsworn Minotaurs` mod) use two races:

- **`MinotaurRace` `00A81E`**: human-style `1mino\1minotaur\skeleton.nif` + `DefaultMale.hkx`. Its race
  skin is human `SkinNaked` `000D64`, which has no ARMA for it, so **a minotaur is drawn entirely from its
  NPC skin (`WornArmor`)**. That ARMO is a whole outfit: body ("cuirass" incl. fur), gauntlets, boots and
  the bull-head "helmet". 14 skins are worn across the two plugins.
- **`FeralMinotaurRace` `00A810`**: one `wildmino.nif` on `1mino\1wildminotaur\skeleton.nif`
  (vampire-brute graph).

Both skeletons use the standard `NPC …` bone names. `tools/04-build-minotaur-limbs.py` merges the two
plugins' records (MinotaursInEnderal wins) and resolves meshes through Ultra's MO2 mod order. For every
skin and limb it cuts each shape of each ARMA model by dominant bone: the limb bone plus all its
descendants in the race skeleton, so jaw, horns and fingers come along. Each piece moves into the RefNode
bone's local space via the shape's own skin-to-bone and is added (shader, 9 textures, alpha) to a DF
container nif, whose own shapes are then detached. Containers:
- forearms/calves: DF humanoid naked male limbs, from `DF - Official Humanoid Pack.bsa`, with the
  humanoid male templates;
- head: DF draugr naked male head, with the draugr head template. The humanoid head is
  `Method: Decapitate`, not a mesh.

Each piece is skinned rigidly to `Root` with skin-to-bone = (identity, template `Translation`). Limbs
with identical geometry are shared. **46 meshes, MiscItems `0x805–0x832`**, plan in
`tools/minotaur-limbs.json` (committed; `01` and `02` read it). Each race also gets an `ANY` fallback
(Cuirass1 `00A818` / the feral skin).

Placement verified in Root space: every limb starts at the template's stump offset, where DF's own bone
stub sits, and extends toward the hand/foot/head.

Traps the generator handles:
- `helmet_2`'s horn shape `fesf` is bound at skin-to-bone **scale 30.2**: positions use scale·R, normals R.
- Some body shapes (`torso`) carry forearm descendants but not the forearm bone. Those are chained
  through another shape of the same outfit rigged to both. The race `skeleton.nif` bind differs from the
  meshes' by up to 1.6 units, so it is not used.
- `ArmorMinotaurCuirassForsworn` `000826` is worn by no NPC and gets no entry (`ANY` covers it).

Test: `help EncMinotaur 4` in the console lists the NPC IDs, then `player.placeatme <id>`.

## Spiders: SHELVED 2026-10-19 (not shipped)

**Current state:** `SPIDERS = False` in `01` and `02`. The plugin carries no spider items, the DATA no spider
races, and no `Zenderal_LostOnes_TEMPLATES.json` ships. `05-build-spider-limbs.py`, its plan and
`limbmesh`'s hull fitting are kept. **Why shelved:** every leg cut made DF rebuild the spider corpse's 3D,
and Spider SE's 25.8 MB body stayed invisible for ~8 s before reappearing in place (video,
2026-10-19). DF's DLL shows: a missing `BipedSlot` defaults to 0 (`mov [rsi+0xA0], eax` after
`xor eax, eax`). After a cut it resizes the node and, guarded by a per-limb flag, makes an actor virtual
call (vtable slot 0x4F) that could not be named without 1.5.97 symbols. Ruled out on the way, in order:
missing BipedSlot (vanished for good), the borrowed wolf hull, the number of collapsed ragdoll bodies,
`CollisionNode`, and the body-cap ARMO equip. Re-enabling needs a fix for the rebuild: an SKSE DLL that
stops DF's refresh for spiders, or keeps the body model cached. DF 1.2.3 is a dual SE+AE DLL, so such a
fix would only need the same CommonLib rebuild as our other DLLs in the AE migration.
**[FrostSpiderMotherFix](FrostSpiderMotherFix.md) is separate and still ships.**

What was built, kept for re-enabling:


**DF has no spider data.** Enderal's spiders are the four vanilla frostbite spider races:
- `FrostbiteSpiderRace`, `…Large` and `…Hoher` on skin `03636F`;
- `…Giant` on skin `02C180`.

Both skins render `FrostbiteSpider.nif`, here Spider SE's replacement. The winning `skeleton.nif` is
Creature Collision Fix's, whose leg chains match Spider SE's. Each leg is a chain
`Leg_<L|R>[n0]…[n4]` (n = 0–3) plus a toe bone.

`tools/05-build-spider-limbs.py` cuts all **eight legs at `[n2]`**, as DF cuts wolf legs at `Leg2`, via
`limbmesh.cut_shape`. The leg pieces go into DF's wolf front-leg nifs (collision kept), skinned to `Root`
with `Translation` 0, so `Root` is the `[n2]` bone frame. Result: 2.2k–5.5k tris per leg from 4 shapes,
toes included. MiscItems `0x833–0x83A`, plan in `tools/spider-limbs.json`.

`01` writes our own `Zenderal_LostOnes_TEMPLATES.json`: per leg, RefNode `Leg_<side>[n2]`,
**`BipedSlot` 37**, DF's wolf leg blood art `0x8A4`, Translation 0.

**`BipedSlot` is the actor body slot DF hides when the limb is cut** (DF's own values: 33 forearm =
gloves, 37 calf = boots, 31 head). The first build left it out, as DF's wolf templates do. Then every
dismembered spider vanished whole (reported in game 2026-10-19): the default evidently hid slot 30, and
the spider's single body ARMA `NakedFrostbiteSpiderAA` covers Head (30) + Body (32). Wolves never
showed it because their skin ARMA is Body only. 37 is unused on a spider. **Rule for any new race:**
set an explicit `BipedSlot` that the race's skin ARMAs do not cover.

**That was not the whole story: the corpse still vanished on cut hits, never on a console `kill`**
(tested in game 2026-10-19). DF's detailed log (`iVerboseMode = 2`) showed clean data and a normal
`Severed limb node : "Leg_R[02]"`. The real cause was the severed leg's **collision**. DF limb nifs
carry one `bhkConvexVerticesShape` on the root, in Root space (the wolf hull × 69.99 matches the wolf leg
mesh exactly). The borrowed wolf front-leg hull runs along Z, −17…13, a 30-unit slab across the joint,
while a spider leg runs about 72 units along +X. The spawned leg's hull overlapped the spider body, and
Havok separated them violently enough to fling the corpse away. The skeleton and minotaur limbs never
hit this because their containers' hulls already run along their limbs.

Fix: `limbmesh.build_nif(..., fit_hull=True)` replaces the hull with an oriented bounding box (PCA) of
the new geometry: 8 vertices, 6 planes, n·v + w ≤ 0 inside, Havok units. The rewrite is binary
(`rewrite_hull`), because PyNifly's `setCollConvexVerts` *appends* to an existing shape (it left 24
verts / 18 planes). Verified: every leg vertex is inside its box. **Rule for any new creature: if the
limb doesn't lie along the container limb's axis, fit the hull.**

**Still not it: the next retest showed the corpse disappears and reappears a few seconds later**
(2026-10-19). That is a 3D rebuild, not physics. An experiment that cut each leg pair differently
(`[n2]`, `[n3]` 2 bodies, `[n4]` 1 body, `[n2]` + `CollisionNode`) changed nothing. The suspected trigger:
DF equips the template's `ActorArmorAddon` (the body-cap ARMO) on every cut, which rebuilds the actor's
3D. Spider SE's body nif is 25.8 MB (the Canidae wolf's is 3.4 MB), so the reload is visible. The spider
legs therefore get their own actor-addon templates with **only `ActorArtObject`** (wolf blood art
`0x87E`/`0x87F`) and no `ActorArmorAddon`. A spider never needed the cap: it is race-locked to wolves and
renders nothing. **Pending in-game retest**, including that DF accepts a template without the key. Actor addons reuse the wolf front-leg templates. Their cap ARMOs
are slot 58 and race-locked to wolves, so nothing renders on a spider (the spider skin is slots 30/32).
DATA maps all four races, `ANY` skin, both sexes, to the eight leg nodes. The pedipalps, fangs and
abdomen are not dismembered. Dwemer spiders (`DwarvenSpiderRace`) are not covered.

Test spawns: `player.placeatme 013FEF` (`_00E_Spider`), `016C6B` (`_05E_Mooskrabbler`), `0E430A`
(`_26E_Frostkrabblermutter`). Legs came off in game; the corpse blinked (above).

## Related

- Purple severed draugr limbs were a different bug: `DF - Creatures by Xtudo - Draugrs` without its
  retexture. See [`mod-gotchas.md`](../modlist/mod-gotchas.md).
- The list has only Lost Ones Revised's 11.6 MB "Fleshless Lost Ones (Skeletons) - Vanilla AI" file,
  not its 336 MB "Lost Ones (Draugrs)" main file (a replacement `Undead Creatures Replacer.esp`, a 382 MB
  BSA, plated/armored meshes). `Lost Ones Revised - EGO Patch.esp` references seven skins (`0083F3`,
  `00A95F`, `00DB22`, `00DB29`, `00DB31`, `00DB44`, `00E7B5` `:Undead Creatures Replacer.esp`) that the
  installed UCR 1.2 lacks. If that file is ever installed, rerun all three generators.

## Frozen mid-air corpses: stump-cap test (2026-10-22, closed: not DF)

**Resolved elsewhere, not DF:** a hit on an airborne ragdoll makes the engine start the get-up mid-air, and a stagger
pulls the graph out of ragdoll; see [`AirborneGetUpFix.md`](AirborneGetUpFix.md) (measured with
[`ZenRagdollTrace`](ZenRagdollTrace.md)). The contact-listener theory in [`CreatureRagdollFix.md`](CreatureRagdollFix.md)
was wrong for creatures. The deployed JSON was restored to the repo copy the same day.

**Symptom:** an enemy ragdolled into the air (Seismic Stomp), killed by a hit while airborne and dismembered, goes
rigid in mid-air and never falls. Seen on skeletons (and reported for spriggans).

**Lead, from DF 1.2.3's source** (Seb263/SkyrimSE_DismemberingFramework `eacedd8`, `Main.cpp`): for each limb cut
DF runs `CutLimb`, `DropTargetItem`, `ToggleCollisionLayers` (dead target), `ToggleNode`, then
**`EquipArmorAddon`**, which calls `ActorEquipManager::EquipObject` on the dying actor. That equips the stump cap,
from the official packs' "Actor addons data" templates (`ActorArmorAddon`), which every limb uses, ours included.
Equipping rebuilds the actor's worn 3D. On a live mid-air ragdoll, the suspicion is that this freezes the body in
its current pose. **Not proven.**

**Test deployed (not in the repo):** the deployed `Zenderal_LostOnes_LIMBS.json` has the "Actor addons data"
template removed from the five `Zenderal - Skeleton - *` limbs. Skeletons still lose limbs, without a stump cap.
Original in `E:/Zenderal-backups/2026-10-22-df-skeleton-cap-test/`; the repo copy and `tools/01` are unchanged.
If skeletons stop freezing, the stump-cap equip is the cause. The fix then belongs in DF (defer the equip until the
ragdoll has settled), or in our data (no caps on airborne-prone races).
