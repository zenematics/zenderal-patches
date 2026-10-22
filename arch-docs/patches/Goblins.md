# Goblins

- **Source:** `src/Goblins/` (generated: `tools/01` → `01b` → `02` → `03`; dismembering `04` → `05` → `04b` → `06`)
- **Ships:** two MO2 mods, built locally and not in `build/manifest.json` (their meshes are other authors'
  work, generated from the user's install):
  - `Zenderal - Goblins`: `Zenderal - Goblins.esp` (ESL), `Scripts\ZEN_GoblinRespawn.pex`, the four goblin
    bodies at `meshes\Zenderal\Goblins\` and the seven vanilla Falmer bodies at
    `meshes\actors\falmer\character assets\`. **Sort ABOVE `Goblins` in MO2.**
  - `Zenderal - Goblins Dismembering`: `Zenderal - Goblins Dismembering.esp` (ESL),
    `SKSE\DismemberingFramework\Zenderal_Goblins_{TEMPLATES,LIMBS,DATA}.json`, the 20 limb meshes and
    2 cap meshes under `meshes\DismemberingFramework\Zenderal\Goblins\`.
- **Requires:** the `Goblins` mod (Nexus Enderal 238, Viltuska's goblin resource with open permissions),
  for the goblin meshes' source and their textures (`textures\actors\viltuska_goblin\`). It is never edited.
  **And** `Goblins- Mihail Monsters and Animals (SE-AE version)` (Nexus Skyrim SE 24525, v4) for Mihail's
  meshes, textures and sounds, with **its plugin `mihailgoblins.esp` disabled** (see 2b).
- **FormID blocks:** Goblins `0x800` race, `0x801–0x808` skins, `0x810–0x814` NPCs, `0x820` global, `0x821` race ability,
  `0x822–0x823` iron weapon lists, `0x824–0x825` blur-free attack poison, `0x830–0x850` Mihail's copied records, `0x900–0xB29` the 542 placed refs (12 IDs freed by the MQ01 removal stay unused).
  Goblins Dismembering `0x800–0x813` limb items, `0x814–0x827` cap ARMO/ARMA pairs, `0x828–0x836` Mihail limb items.

## What it does

Curator's taste (2026-10-21): **goblins as their own creature, in large weak packs across Vyn, with Arps
still Arps.** The `Goblins` mod replaces every Falmer body nif, so all Arps (vanilla `FalmerRace`
`0131F4`) had turned into goblins. **[verified 2026-10-21]**

### 1. Arps restored, goblins moved (`tools/01-build-creature.py`)

- The vanilla Falmer bodies (`falmer01`–`06`, `falmer_male`) are extracted from `Skyrim - Meshes0.bsa`
  into `Zenderal - Goblins` at the Falmer paths. No other mod ships them, so with this mod above `Goblins`
  the Arps render as Arps. This is the non-invasive route: the `Goblins` mod's own files are untouched.
- The four distinct goblin bodies are copied to `meshes\Zenderal\Goblins\Goblin_{Plain,Scout,Witch,Chief}.nif`
  (`falmer02` loincloth, `falmer01` wraps/cap/bag, `falmer05` witch body, `falmer06` goat-skull helmet).
  `falmer04` = `falmer02` and `falmer03` = `falmer05`, byte for byte.
- **The Goblins mod ships without Viltuska's armor textures.** `falmer06`'s bear-pelt hood/cape
  (`Armor_Variation_01` → `textures\armor\viltuska_goblin_armor\bearpelt.dds`) and `feathers`
  (`darkfeathers.dds`) exist nowhere, so the chieftain showed a white hood and cape in game (2026-10-21);
  Arps on that body were white under the Goblins mod too. `Goblin_Chief.nif` points them at vanilla
  `textures\clutter\wolfpelts\wolfpelt.dds` (+`_n`) and `textures\clutter\ingredients\hagfeathers.dds` (+`_n`)
  (the cape's UVs span the whole square, so a full-frame pelt). `01` now **asserts that every diffuse and
  normal map each goblin mesh names exists** (loose in an enabled Ultra mod or in a game BSA). Run on the
  original `falmer06`, the check flags exactly those four textures.

### 2. The creature (`tools/01-build-creature.py`)

Every record is copied from the winning record. Only EGO overrides FalmerRace and the Arp NPCs (full
Ultra scan, 2026-10-21).

- `ZEN_GoblinRace` `0x800`: EGO's FalmerRace verbatim (skeleton, behaviour graph, attacks, body part
  data) with its own EditorID, so DF keys goblin limbs by race without touching the Arps'. Skin `0x805`.
- Four skins: ARMO `0x805–0x808` / ARMA `0x801–0x804`, copied from `_00E_Arp4`/`Arp3`/`Arp2` and
  `NakedFalmerAA01/02/05/06`, race and model swapped, texture-hash `Data` dropped.
- Five NPCs, each copied from an Arp:

| NPC | Name | From | Skin | Level |
|---|---|---|---|---|
| `ZEN_Goblin` `0x810` | Goblin | `_17E_Arp01` | Plain | 6 |
| `ZEN_GoblinScout` `0x811` | Goblin | `_17E_Arp02` | Scout | 6 |
| `ZEN_GoblinArcher` `0x812` | Goblin Archer | `_17E_Arp03Scheutze` | Scout | 6 |
| `ZEN_GoblinShaman` `0x813` | Goblin Shaman | `_18E_ArpSchamane` (its spells) | Witch | 6 |
| `ZEN_GoblinChief` `0x814` | Goblin Chieftain | `_17E_Arp01` | Chief | 9 |

  Goblins get no health offset, combat skill offsets lowered to 15 (never raised), and 40 EP (chieftain
  80) instead of 150. They keep the Arp faction (via the Arps' `Template`, Factions flag), inventory, AI,
  combat style and the Respawn flag, so goblins and Arps are allies.

**Health and defenses (cut 35% on 2026-10-21; the curator found them "pretty tanky")**
- **The NPC record's `Health` field does nothing here.** These NPCs are not AutoCalcStats, so the game uses
  race Starting Health (100) + HealthOffset. In game the chieftain showed 100, not the 110 written. Mihail's
  goblins *are* AutoCalcStats (race base 50 + level/class). No single record value cuts both by 35%, so
  `ZEN_GoblinRespawn` sets each goblin's base health to **0.65 × the original** the game computed, at
  `OnLoad`. That covers every type and the durzogs. It is idempotent: it remembers the original and
  re-applies after a respawn whether or not `Reset()` restores base health. Our goblins go 100 → 65.
- **Armor** ×0.65: our 4 skins 10 → 7, Mihail's shields 15/20/22 → 10/13/14 (his skins have none).
- **Resistances** ×0.65: the race's `AbFalmer` (magic resist 5, poison resist 40, blindness 25) and
  `_00E_AbMagieres10` (magic resist 10) are replaced by one copy, `ZEN_AbGoblin` `0x821`: magic resist
  15 → 10 and poison 40 → 26. Blindness is unchanged (not a defense). Enderal has no 5% magic-resist ability.
  Mihail's races carry no resistances.
- The EGO NPC perk `XionNPCHumanoid` on our goblins only touches stamina, movement and attack damage.

**No poison blur (curator 2026-10-22: "sometimes when goblins hit me, they apply a blur effect").** The
copied FalmerRace carries the Arps' `crFalmerPoisonedWeapon02` (`109D7E`) on its 8 power attacks. EGO's
effect for it, `crArpPoison` (`0008C9:EGO`, Health poison 0.5 for 30 s), runs `MagicImodOnPlayerHitScript`
with `PoisonHitImod 10E3D2` / `PoisonEndImod 10E3D3`, a screen blur on the player. `01` gives the goblin
race its own copies: `ZEN_GoblinPoisonedWeapon` `0x824` → `ZEN_GoblinPoison` `0x825`, EGO's effect
verbatim minus that script, asserted. Goblins still poison you; the blur is gone. Real Arps keep EGO's
original. Mihail's goblins carry no attack spells, and the durzog's diseases (Ataxia, Rotbone) have no
screen effect.

### 2b. Mihail's goblins and durzogs (`tools/01b-build-mihail.py`, added 2026-10-21)

**`mihailgoblins.esp` must stay disabled: it is a Skyrim plugin that overwrites Enderal records.**
(Porter triage 2026-10-21; the worst case was checked by hand.)
- It places 530 refs in Tamriel `00003C`, which in Enderal is `MQP01Home`, and rewrites that
  worldspace's parent, location and music.
- Its placed goblin `085945` reuses the FormID of the `MQ01Campsite` navmesh (Jespar's camp).
- Six of its CELL records sit on Ark/Riverville REFR FormIDs, and other placed NPCs override Sun Coast and
  Old Dothúlgrad refs.

Its creatures are copied instead: the closure of the 6 goblin types and the Tamed Durzog over records local
to the plugin. That is 33 records: both races, skins, shields, staff, death-item LVLI, the durzog's
disease, loot, impacts and sounds, and the voice dummy. Factions, form lists, cells and worldspaces are
left behind. New FormIDs `0x830–0x850`, EditorID prefix `ZEN_Mihail_`. Fixes, each asserted:

- Every reference to a form Enderal lacks is dropped with its list item. That covers 13 vanilla weapons,
  the Dragonborn/Dawnguard factions, voices and materials, 20 Argonian race presets and 7 death-item
  entries; the script logs each one.
- Broken scalars are replaced: Voice → the Arps' `01F1D2` (goblins) and `CrSkeeverVoice 019FE5` (durzog);
  `InheritsSoundsFrom` → `0ADFA2`, as the Arps.
- Factions: `ZEN_Mihail_mihailgoblin1` gets Template `ZEN_Goblin` (Factions flag). Mihail already chains
  the other types and the durzog to goblin1, so all of them are allied with our goblins and the Arps.
- Each type gets the matching Arp's EGO inventory on top of Mihail's surviving items (his shields, clothes
  and bandit gauntlets/cuirass). Weapons are then replaced by iron, as on our goblins (see "Iron weapons"
  below); the shaman's staff goes too. The shaman's 7 spells (5 missing, 2 resolving to different Enderal spells) become the Arp shaman's
  `NPCLightningBoltLeftHand2` + Invisibility.
- Weak: fixed levels instead of PC level ×1 (2–22). Goblin and Archer 5, Skirmisher 6, Berserker and
  Shaman 7, Warlord 10, Durzog 5. `AutoCalcStats` is kept.
- `_00E_EPOnDeath` (RewardExp 25–80; without it Enderal gives no EP) and `ZEN_GoblinRespawn` are copied
  from `ZEN_Goblin`'s script list.

Writes `mihail-npcs.json` (role → FormID) for `03`. All 987 FormKeys and the 20 mesh/sound paths in the copied
records resolve. Dismembering: see 5. **Unverified in game:** whether the Arp voice suits them. They were
seen in game 2026-10-21 (animating and rendering), but the iron gear and the dismembering are not.

### Iron weapons (`tools/goblin_gear.py`, curator 2026-10-21: "replace all goblin weapons to Iron")

01 and 01b both run `set_weapons` on every armed NPC. It drops EGO's `02E_MOB_RuneWeapon_Arp`, the rune
axe/sword, the oak bow, the old rune arrows and Mihail's goblin staff (asserted: every armed NPC loses at
least one), then adds:

| Roles | Gear |
|---|---|
| Goblin, Scout, Chieftain, Shaman; Mihail Goblin, Skirmisher, Shaman | `ZEN_GoblinIron1H` `0x822`: one of Iron Sword / War Axe / Mace / Dagger |
| Mihail Berserker, Warlord | `ZEN_GoblinIron2H` `0x823`: one of Iron Claymore / Battleaxe / Warhammer |
| Archers (both) | `_01E_02_Longbow` + 20 `_01E_05_IronArrow` + Iron Dagger |

There is no iron bow, and Enderal retired the Hunting Bow (`015C39` is `_00E_HuntingBow_unused`), so archers
get the Longbow, the same `_01E_02` tier as the iron weapons. The Arp loot list (gold, gems, pelts,
ingredients; no weapons) and Mihail's shields stay. The durzog has no weapons.

### 3. Packs (`tools/02-plan-packs.py` → `goblin-packs.json` → `tools/03-build-packs.py`)

Every goblin is a **new** placed NPC; no existing ref is touched. `02` reads base Enderal, FS and every
enabled Ultra plugin in load order (the `src/UnresolvedRefsCleanup/tools/00a` serialization). It takes
the winning cell headers, the winning navmeshes, all live placed refs and the map markers (14,813 cells,
281k refs, 6,155 navmeshes, 25 s with the cache). Rules:

- Members stand on **navmesh triangles**, so they are walkable and at the right height, never inside a rock.
  Water/Door/Preferred (= road) triangles are excluded; sites need slope normal z ≥ 0.9 and members 0.75,
  and everything must be above the cell's water.
- "Makes sense": 1200–4000 units from a wild animal Enderal itself placed (wolves, deer, foxes, hares,
  bears, sabre cats, trolls, spiders, goats, skeevers, spriggans: 756 anchors). A site is also ≥ 1500
  from any placed NPC, so a pack is its own camp.
- Away from people: ≥ 3500 from human/elf NPCs, ≥ 2500 from farm animals. Map-marker clearances are
  City 7000, Town/Settlement 5000, Farm/mills/stable/docks/lighthouse/fort/camp/stronghold 3000, and
  Shack/Shrine/Altar 2000.
- ≥ 700 from roads; ≥ 350 from any object a mod added (its navmesh may not know about it).
- **Off riverbanks and waterfall edges.** The first plan put a pack on the lip of a waterfall at Dual Towers
  (cell −15, −3), seen in game 2026-10-21. That river has **no Water navmesh triangles**; only `FXSplash*`,
  `FXCreek*`, wet rocks, `FXWaterfall*` and `AMBWaterfall*` sound markers mark it. Sites/members now keep
  ≥ 600/250 from Water triangles and ≥ 1200/600 from any placed Static, MoveableStatic, Activator or
  SoundMarker whose EditorID matches waterfall|river|rapid|stream|cascade|splash|creek|wet (2,878 refs).
  The nearest pack to that spot is now over 7,500 units away.
- Excluded regions: **Crystal Forest** (`KristallwaldRegion` `12ECF1`, plus one cell of margin), the
  deserts, Isle of Kor, the tropical idyll, the intro/temple/star-city regions, Ark (`CapitalCity*`) and Fogville.
- Sites ≥ 7000 apart, 80 of them. Each pack has 5–8 goblins within 450 units, ≥ 90 apart. Ours and
  Mihail's are mixed, with Mihail's type winning **75%** of every draw (`MIHAIL_SHARE`, curator
  2026-10-21: "more Mihails in the mix"):
  - 1–2 archers;
  - a shaman in 35% of packs;
  - in packs of 7+, a Chieftain or a Mihail Warlord;
  - the rest drawn from Goblin/Scout or Mihail Goblin/Skirmisher/Berserker;
  - plus 0/1/2 Tamed Durzogs (50/30/20%).

  Fixed seeds, so the plan is deterministic.

**Quest zones (`QUEST_CLEAR`, curator 2026-10-21).** No pack within 10,000 units of MQ01's Finn (`085998`)
or Carbos (`08599A`; he stands in `MQ01Campsite` cell −27,1, Jespar's camp). The two Old Dam Lookout packs
there (cells −26,1 and −28,1; 5 + 7 members) broke the opening dialogue with Finn, Carbos and Jespar. The
zones drop packs *after* composition and never re-roll, and `02` carries every surviving pack's ref FormIDs
over from the previous plan. `03` keeps a site's existing IDs and gives fresh ones only to new sites, so
removing these two left the other 78 packs identical (place, line-up, ref IDs) and goblins in existing
saves are the same refs. Add a ref here for any other scripted encounter a pack disturbs.

Result before the quest zones: 80 packs. **Now 78 packs, 542 refs: 492 goblins + 50 durzogs.** At 80 packs the roles were M-Archer 96,
M-Goblin 91, M-Berserker 81, M-Skirmisher 80, Durzog 50, Goblin 43, Archer 29, Scout 28, M-Warlord 25,
M-Shaman 18, Chieftain 8, Shaman 5.

| Area (nearest settlement) | Packs | Goblins | Durzogs |
|---|---|---|---|
| Northwind (mountains) | 11 | 65 | 10 |
| Riverville | 9 | 58 | 11 |
| Dairy | 8 | 55 | 6 |
| Old Canal | 8 | 48 | 4 |
| Lone House | 7 | 42 | 2 |
| Monastery Westgard | 6 | 39 | 4 |
| Pentas' House | 6 | 38 | 1 |
| Castle Goldenford | 5 | 31 | 4 |
| 10 others | 1–3 each | 128 | 8 |

The closest packs to Ark are 5–7 cells out (Grotto to the Wayside Cross, The Cemetery, Field near the Mill), because Ark's
walls, gate forts and farms keep the nearer ground clear. `goblin-packs.json` lists every pack with its
landmark, cell and ref FormIDs.

`03` writes the refs and forwards, per guardrail 5, the Vyn WRLD header (truncated before `TopCell`) and
each touched cell's header plus block files from their **last overrider before this plugin**. The cell
headers come from FS 13, Skyrim.esm 12, EPPI IPL 10, Seasonal Aspen Winter 10 and 19 others. Masters are
computed from the FormKeys written: Skyrim, Update, FS, EGO.
**Load right after the last Vyn cell editor (Golden Mare Mill SE.esp, 2026-10-21); rerun `02` and `03`
when any Vyn cell editor changes.** DynDOLOD.esp and Occlusion.esp load later and win those cell headers;
that is harmless to the refs.

The WRLD header's last overrider, Golden Mare Mill SE, carries vanilla `LodWater 000018`. It already beat
Water for Enderal CS's `LodWater 000802` in this load order before this mod existed, and is forwarded as-is.

### 4. Respawn (`Scripts/source/ZEN_GoblinRespawn.psc`)

On every goblin NPC (it also does the health cut above; it has no properties beyond the original two, so
instances in existing saves keep working): `OnDeath` stores `GameDaysPassed`. `OnLoad` resets the goblin (alive, at its own
spot, re-equipped) once `ZEN_GoblinRespawnDays` (global `0x820`, default **7**) in-game days have passed.
`OnLoad` fires when the goblin's cell enters the loaded area, usually before the player can see it.
Refs stay temporary: a quest-driven reset over a list would need all 507 persistent. The engine's own
cell reset (Respawn flag, `iHoursToRespawnCell`) still applies too. Compiled against Enderal 2.1.4.4 +
SKSE source; `tools.json`'s `papyrusSource.vanilla` (Nemesis) and the PapyrusUtil import dir no longer exist.

### 5. Dismembering (`Zenderal - Goblins Dismembering.esp`, `tools/04`–`06`)

It is a separate plugin for two reasons. `Zenderal - Goblins` must work without DF. And the cap ARMAs must
name `ZEN_GoblinRace`, while `Zenderal - Lost Ones Dismembering` must load before the Fluffworks DF patch
(slot 398), so it cannot master `Zenderal - Goblins` (slot 407). Lost Ones Dismembering is unchanged; Arps
keep DF's own Falmer limbs.

- `04` cuts each goblin skin's mesh into forearms, calves and head: 20 meshes inside DF's naked male Falmer limb
  nifs, with the Falmer base-data templates. Placement was checked in Root space: the bounds match DF's
  Falmer limbs to about 1 unit (the goblin rides the Falmer skeleton). Shared helpers are in
  `src/LostOnesDismembering/tools/limbmesh.py`.
- `05`: DF's Falmer stump caps fit the goblin's geometry, but their skin ring is `falmerm.dds`. Two variants
  (`goblin.dds`; `goblinwitch.dds` for the witch/chief bodies) rebuild each ring with the goblin shader. Each
  ring is unwelded and takes per-triangle UV islands from the goblin body (max triangle UV span 0.058;
  nearest-vertex transfer smeared 0.4–0.8 across seams).
  **Fixed 2026-10-22: decapitated goblins grew a long spike from the neck** (seen in game). PyNifly's
  `add_bone` resets the skin-to-bone of bones added before it. Setting each bone's transform in the same
  loop left all but the last at identity. In the 3-bone head ring that meant `NPC Spine2` and
  `NPC L Clavicle`, which together cover every vertex. The forearm/calf rings have one bone each, so they
  were unaffected. `05` now adds all bones, then sets every transform, then the weights. It also reads the
  written nif back and asserts each ring's per-bone transform equals DF's. Rule for any multi-bone PyNifly
  rebuild: add bones first, then transforms.
- `04b` (Mihail's goblins, added 2026-10-21) is the minotaur method from
  `src/LostOnesDismembering/tools/04`, which was verified in game. Mihail's race is humanoid: its skeleton
  has standard `NPC … [xxx]` bones, his skins cover only the Body slot, and the head is part of the body
  mesh (2,921 head-weighted vertices). Each of his 3 skins is cut by dominant bone into DF's humanoid naked
  male forearm/calf nifs (`DF - Official Humanoid Pack.bsa`, humanoid male templates) and DF's draugr head
  (draugr head template). That makes 15 meshes, `0x828–0x836`, in `meshes\…\MihailGoblins\`. The bounds
  match DF's human limbs to about 1 unit; calves run a little longer, for bigger feet. BipedSlots 33/37/31
  are free on his race. There are no stump caps: DF's humanoid caps are race-locked to the playable races,
  as on the minotaurs. The **Tamed Durzog is not dismembered**: DF has no creature data close to it (a
  skeever skeleton), and custom creature limbs are what blinked Spider SE's corpses (see
  LostOnesDismembering).
- `06` writes the records and the JSON:
  - our goblins: DF's Falmer limb items and cap ARMO/ARMA copied, race `ZEN_GoblinRace`;
  - Mihail's goblins: DF's draugr limb items copied;
  - 10 actor-addon templates (our cap + DF's blood art) and 35 limbs;
  - DATA: `ZEN_GoblinRace` → 4 skins + `ANY` (Plain), and `ZEN_Mihail_mihailgoblinrace` → 3 skins + `ANY`.

## Build

```
python src/Goblins/tools/01-build-creature.py
python src/Goblins/tools/01b-build-mihail.py
python src/Goblins/tools/02-plan-packs.py <all dir> [<cache.pickle>]
python src/Goblins/tools/03-build-packs.py <all dir>
spriggit deserialize src/Goblins/GoblinsESP -> <mod>/Zenderal - Goblins.esp
python src/Goblins/tools/04-build-dismember-limbs.py "<$Tools.pynifly>"
python src/Goblins/tools/05-build-dismember-caps.py "<$Tools.pynifly>"
python src/Goblins/tools/04b-build-mihail-limbs.py "<$Tools.pynifly>"
python src/Goblins/tools/06-build-dismember-data.py
spriggit deserialize src/Goblins/GoblinsDismemberingESP -> <mod>/Zenderal - Goblins Dismembering.esp
copy src/Goblins/SKSE/DismemberingFramework/*.json -> <mod>/SKSE/DismemberingFramework/
```

Built 2026-10-21. Both Spriggit round trips are equivalent: Goblins differs only in float formatting and
defaulted fields (positions all within 0.01); Dismembering is identical. Both are ESL, HEDR 1.70. All
683 + 50 FormKeys resolve. Deployed to Ultra (profile backup in
`E:\Zenderal-backups\2026-10-21-goblins-profile`). **Not checked in xEdit.** In game 2026-10-21 (first
build): packs spawn and goblins render. The chieftain's white hood/cape and the waterfall-edge pack were
both fixed in the rebuild, and that rebuild is not yet seen in game.

Test: `help Goblin 4` in the console lists the goblin NPCs with their load-order FormIDs (light plugin:
`FE…`), then `player.placeatme <id>`; or walk to a pack site from `goblin-packs.json`. Check that:
- Arps look like Arps again;
- goblins fight beside Arps and are weak;
- cut limbs and stumps are goblin green;
- a killed pack is back after 7 days once its area reloads.
