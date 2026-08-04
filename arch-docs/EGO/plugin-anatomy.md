# EGO — plugin anatomy

Structural facts about `Enderal SE - Gameplay Overhaul.esp` that shape how you patch it. All
**[verified]** against `reference/mods/EGO/esp/` on 2026-08-04.

## Header

```yaml
ModKey: Enderal SE - Gameplay Overhaul.esp
GameRelease: EnderalSE
ModHeader:
  Stats:
    Version: 1.7
  Author: Ixion XVII aka Reltilie
  MasterReferences:
  - Master: Skyrim.esm
  - Master: Update.esm
  - Master: Enderal - Forgotten Stories.esm
  INTV: 1
```

Three observations that matter:

- **No `Flags:` block at all.** EGO is a plain ESP — not ESM-flagged, not ESL-flagged, and **not
  `Localized`**. It occupies a full plugin slot in the 254-plugin budget.
- **Masters are exactly the three Enderal base plugins.** No DLC masters (correct — Enderal's DLC
  ESMs are empty stubs; see CLAUDE.md). Load-order index 2 is the FS ESM, so a patch that also
  masters EGO will see EGO at index 3.
- `INTV: 1` — one internal version tag; nothing to interpret.

## Record census

| | Count |
|---|---|
| Total records | **7177** |
| Overrides of existing master records | **6203** |
| New records (`:Enderal SE - Gameplay Overhaul.esp`) | **974** |
| — of which are *injected* into a master's FormID space | 61 (counted in the 6203, see below) |
| YAML files in the serialized tree | 7328 (the extra are Spriggit group files) |

Where the overrides land, by defining master:

| Suffix | Overrides | Means |
|---|---|---|
| `:Skyrim.esm` | 5061 | base Enderal |
| `:Enderal - Forgotten Stories.esm` | 1137 | the FS expansion |
| `:Update.esm` | 5 | vanilla Update |

Per-type counts are in [`conflict-index.md`](conflict-index.md); the ten biggest are NPCs (1106),
ConstructibleObjects (655), Spells (593), MagicEffects (360), Containers (319), Weapons (313),
Armors (295), ObjectEffects (269), Ingestibles (253) and MiscItems (246).

## New-record FormID map

EGO's own FormIDs run **`0x000800` – `0x01DCFE`** — far outside the ESL window, which is why it can
never be ESL-flagged. The allocation is clustered by development era rather than by feature, but the
clusters are readable:

| Block | New records | Dominant content |
|---|---|---|
| `0x000800–0x0008D8` | 125 | early balance pass: potions/food, fire-nova + mana perks, armour/stamina ability spells |
| `0x000D62–0x000D63`, `0x0058FE–0x0058FF`, `0x007EA2–0x007EA7`, `0x01DCFA–0x01DCFE` | 13 | **new GMST records** (reach, crime, sneak, bounty) |
| `0x0012C4` | 1 | `iAEmptyInt` global |
| `0x001CAA–0x001FDB` | **641** | the main body — perks, keywords, spells, magic effects, leveled lists, recipes, creature abilities |
| `0x002C3C–0x002C9F` | 94 | **integrated *Enderal SE - Crossbows*** — bolts, crossbow idles/sounds/impacts, 1st-person statics |
| `0x00390D–0x003912`, `0x004580`, `0x00775D–0x00775E` | 9 | later spot fixes |
| `0x005E5D–0x005E76` | 26 | Nordic/Stalhrim 1st-person statics, weapon-master + attack-speed fix spells |
| `0x006AE4–0x006AEE` | 9 | sweeping blow, lycanthrope, double-enchant |
| `0x0083D0–0x00840B` | 56 | the "mystical/utility spell" pass — Banish, Stable Spellwork, Transmute Self, Circle, Blindness |

The full list is [`new-records.md`](new-records.md).

> **Naming.** EGO's own records are overwhelmingly prefixed **`Xion`** (the author's handle), with
> `_60E_Xion…` for mystical-tier spells and `NPCXion…` for NPC-only casts. A `DUPLICATE00n` suffix
> means the record was made with the CK's *Duplicate* command and never renamed — it is not a
> defect, but it does mean the EditorID tells you nothing. Several EditorIDs are German
> (`XionMagierlicht4`, `_02E_16Silberschlachtaxt`) because Enderal's own content is.

## Injected records

**61 records carry a master's FormID suffix for a FormID that master does not define.** **[verified]**
— 60 in `Skyrim.esm` and 1 in `Enderal - Forgotten Stories.esm`. They were spot-checked by hand:
`Skyrim.esm` defines `03AD56 ChaurusEggs` but nothing at `03AD57`, and `058F67 _00E_PowerBashPerk`
but nothing at `058F68` — yet EGO ships `ChaurusChitin 03AD57:Skyrim.esm` and
`DeflectArrows 058F68:Skyrim.esm`.

They include content Enderal genuinely lacks — `DeflectArrows` and `SilverPerk`-adjacent perks, the
Dragon Priest mask armours (`061CA5`, `061CAB`, `061CB9`, `061CC0`, `061CC2`, `061CC9`), the silver
axe weapons, `NPCMageArmor2/3`, several `DeathItem*` leveled lists, and two
`_00E_CraftingPlan_03ESilver*Forged` blueprints.

Consequences for a patch:

- In xEdit they display as overrides with **no green master record**. That is expected, not a bug.
- **Reference them by EGO's FormKey, not by the master's.** A patch that declares only
  `Skyrim.esm` and points at `03AD57:Skyrim.esm` compiles fine and resolves to nothing at runtime
  when EGO is absent or loaded after you.
- Do not "clean" them. `QuickAutoClean` on **EGO itself** would be wrong; on your own patch it is
  fine, because your patch should not be carrying them in the first place.

The complete list is at the top of [`conflict-index.md`](conflict-index.md).

## Localisation is stripped

Enderal's masters are `Localized` (strings live in `.STRINGS` files, and Spriggit serializes them as
a `Values:` list of per-language entries). **EGO is not localized**, so every string it touches
serializes as a single `Value:`. Example — `_00E_BoundWeaponBattleaxe1 058F5E:Skyrim.esm`
**[verified]**:

```diff
 Name:
   TargetLanguage: English
-  Values:
-  - Language: English
-    String: Mystical Battleaxe
-  - Language: Chinese
-    String: 神秘巨斧
-  - Language: Korean
-    String: 신비한 전투도끼
+  Value: Mystical Battleaxe
```

This is why `Name` and `Description` appear as "changed" on essentially *every* overridden item
record in the field histograms — 310/310 weapons, 287/287 armours, 251/252 ingestibles, 208/208
books. Most of those are not balance edits; the string simply lost its non-English variants.

What it means in practice:

- **A German/Chinese/Korean/Russian player running EGO gets English text for ~2000 records.** That
  is EGO's design choice, not something a Zenderal patch should try to undo wholesale.
- **When you override a record EGO also overrides, copy EGO's file and edit it** — do not copy the
  FS/Skyrim version, or you will re-add the `Values:` block and it will read as your patch
  reverting EGO's (English-only) name and description.
- The corollary: a diff that shows only `Name`, `Description` and `Version2` changing is a
  *serialisation* difference, not a gameplay one. Filter it out before drawing conclusions.

`Version2` is the record's form-version field and differs on most records for the same reason —
treat `['Name', 'Description', 'Version2']` as the null diff.

## Shipped assets

Beyond the plugin, the mod folder contains:

```
Enderal SE - Gameplay Overhaul.esp
Enderal SE - Gameplay Overhaul.ini
scripts/            7 .pex  (loose, override the BSA)
scripts/source/    14 .psc
```

### The INI

`Enderal SE - Gameplay Overhaul.ini` is a plugin-named INI, which SSE loads for the active plugin.
It zeroes every fade timer **[verified]**:

```ini
[General]
fAutoDoorFadeSecs=0.0001
fFastTravelFadeSecs=0.0001
fLoadGameFadeSecs=0.0001
fNormalDoorFadeSecs=0.0001
fNormalDoorFadeWait=0.0001

[Interface]
fFadeToBlackFadeSeconds=0.0001
fMinSecondsForLoadFadeIn=0.0001
fSleepFaderTime=0.0001
```

Note the tension with SureAI's own warning (quoted in CLAUDE.md) that ENB presets *"may deactivate
fadeouts in cutscenes, leading to visual bugs"*. EGO removes those fades globally by INI. If a
Zenderal visuals patch chases a cutscene-fade bug, this file is a suspect — and because it is an
INI, xEdit will never show it to you.

### The scripts

See [`scripts.md`](scripts.md). In short: 7 compiled scripts, 6 of which override Enderal's own
`_00E_*` scripts and are resolved by **MO2 file priority**, not plugin load order.

The `source/` folder also carries seven `_syc*.psc` files (`_sycMainQuestScript`,
`_sycmaintenancerefaliasscript`, `- Copy` variants of both, `_sycccobookscript`) that have **no
matching `.pex`** and no matching record anywhere in the plugin. They are dead files left in the
package; ignore them.
