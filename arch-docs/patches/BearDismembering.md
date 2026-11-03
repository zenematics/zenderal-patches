# BearDismembering

- **Source:** `src/BearDismembering/` (generated: `tools/01-build-bear-limbs.py` → `tools/bear-limbs.json` →
  `tools/02-build-bear-data.py` → `BearDismemberingESP/` + `SKSE/DismemberingFramework/`)
- **Ships:** MO2 mod `Zenderal - Bear Dismembering`, built locally and not in `build/manifest.json` (the meshes are
  cut from other authors' work on the user's install):
  - `Zenderal - Bear Dismembering.esp` (ESL, HEDR 1.7; masters Skyrim, Update, FS, `Dismembering Framework.esm`,
    `DF - Official Creature Pack.esp`)
  - `SKSE/DismemberingFramework/Zenderal_Bears_{TEMPLATES,LIMBS,DATA}.json`
  - 15 limb meshes + 5 blood-fx meshes at `meshes/DismemberingFramework/Zenderal/Bears/` (not committed)
- **FormID block:** `0x800–0x804` stump blood ArtObjects, `0x805–0x813` limb MiscItems

## Why

Asked for 2026-11-01. Bears were never dismembered. DF's packs and Xtudo's patches cover only draugr, falmer, trolls
and wolves, and no DF bear patch exists on Nexus (searched 2026-10-11: Xtudo's 34 files, a Nexus title search).

## What it does

Enderal's bears are the four vanilla bear races, each on its race skin. No bear NPC has its own `WornArmor`
except FS's summonable panda. Winners come from a master-aware scan of the Ultra load order (2026-11-01):

| Race | Skin | Body ARMA (winner) | Mesh |
|---|---|---|---|
| `BearBrownRace 0131E7` | `SkinBearBrown 0868FD` | `0868FB` (EGO SE - Bears of the North) | `BOTN_bear.nif` |
| `BearBrownRaceHoher 0EAA5A` | `SkinBearBrownHoher 0EAA5B` | `0868FB` (EGO BotN adds the race) | `BOTN_bear.nif` |
| `BearBlackRace 0131E8` | `SkinBearCave 0187FE` | `018800` (Bears of the North) | `BOTN_cavebear.nif` |
| `BearSnowRace 0131E9` | `SkinBearWhite 0187FD` | `0187FF` (Bears of the North) | `BOTN_polarbear.nif` |

- **`tools/01`** cuts the head and four legs from each body. It cuts the base shape plus its five fur shells, by
  dominant bone, with the shared `src/LostOnesDismembering/tools/limbmesh.py`. The bear skeleton is XPMSE's and
  uses `NPC` bone names. The cuts are:

  | Limb | DATA node (severed) | RefNode |
  |---|---|---|
  | Front legs | `NPC LArm2` / `NPC RArm2` | same |
  | Back legs | `NPC LLeg2` / `NPC RLeg2` | same |
  | Head | `NPC Neck2` | `NPC Head` |

  Each piece goes into DF's wolf limb nif for the same limb. The wolf Translation is kept, so the container's
  `Origin` node marks the bear joint. The collision hull is re-fitted (`fit_hull`), because the bear bones run along
  +X, not along the canine axes. Brown and Hoher bears share a mesh, which makes 15 limbs (≈5k triangles per leg,
  19k per head with shells). Checked offline: every limb starts at its joint and runs out along the bone, and left
  and right mirror.
- **Meat cap on the severed limb (added 2026-11-01, after an in-game screenshot):** the first build showed the head's
  hollow inside, because DF's wolf files bring their own `Gore`/`Bone` cap shapes and those are wolf-shaped, so we
  detach them. `01` now closes each cut itself:
  - **`cut_loops`** finds the open edge on the skin shape, i.e. edges with one kept and one dropped triangle. It
    welds vertices by position first, so UV seams don't break the ring.
  - It walks the edge both ways, then joins chains end to end. Branch vertices had split the head's ring into two
    open chains.
  - **`gore_caps`** fills that ring with a fan from its centroid, in both windings. It uses planar UVs and the wolf
    container's own `Gore` shader (DF's `DismemberedLimbGore.dds`).
  - The run asserts exactly one closed ring per limb: 17–19 edges per leg, 47 on the head.
  - **The body side is still open.** Covering that needs a stump cap, which is off on purpose (see below).
- **Stump blood:** DF's wolf stump sprays attach through a `NiStringsExtraData` `NamedNode&Canine_*`, which a bear
  doesn't have. `01` copies each wolf `BloodFX_<limb>.nif` with only that string renamed to the bear's severed
  node and the block size updated. The spray direction is still the wolf's, in the bear bone's frame.
- **`tools/02`** writes the records and our own JSON. No other DF file defines a bear race, so no same-path copy is
  needed:
  - **ArtObjects** are DF's wolf stump arts with the new model.
  - **MiscItems** are DF's wolf Default limb items with the new model.
  - **Templates:** each limb names the bear RefNode, DF's wolf flying-limb blood `0x8A4`, the wolf Translation and
    an explicit `BipedSlot`.
  - **No `ActorArmorAddon`** (stump cap). DF's wolf caps are race-locked to wolves and render nothing on a bear.
    Equipping one is also the suspect in the open `0FDDB2D` crash ([`LostOnesDismembering`](LostOnesDismembering.md),
    stump caps off).
  - **`BipedSlot` is required.** DF hides that body slot on a cut, and a missing one defaults to slot 30. Every bear
    body ARMA is slot 30 (Head) only, so without it the whole bear would vanish (the spider lesson). We set 37 on
    the legs and 31 on the head; neither is used on a bear.
  - **DATA** keys each race to its skin, `Male|Female`, with no `ANY`. FS's panda (`BearBlackRace`, skin `02E3AE`)
    therefore gets nothing, rather than cave-bear limbs. The ghostly summonable black bear wears the cave skin and
    gets ordinary cave-bear limbs.

## Load order

The plugin must load after `DF - Official Creature Pack.esp` (it is a master). The MO2 mod position doesn't matter:
no other mod ships these paths.

## Status

Built 2026-11-01: the Spriggit round trip is identical, it is ESL with HEDR 1.7, and the meshes and JSON are deployed.
**Not enabled yet (MO2 was open), not run in game.** Test: `player.placeatme 04D9C6` (brown), `0672D2` (black/cave),
`0D9404` (snow), `0EAA4F` (Hoher, MQ09), then cut a leg and the head. Watch for:
- whether the stump spray points the right way;
- whether the severed head clips the fur shells at the neck;
- crashes on cuts, since bears share the stump-cap-free setup that the `0FDDB2D` test is about.

Rerun `tools/01` then `02`, then rebuild the plugin, after Bears of the North, its EGO patch, XPMSE or DF's creature
pack changes. `01` needs PyNifly (`$Tools.pynifly`; re-downloaded V29.1.0 to `E:/Zen Tools/PyNifly V29.1.0` on
2026-11-01).
