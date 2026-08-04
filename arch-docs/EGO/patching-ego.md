# Patching against EGO

The practical guide. Read this before writing any Zenderal patch that could touch combat, loot,
crafting, spells, NPCs or the world — which is most of them.

## Load order

The author's own guidance **[author]**:

```
Enderal SE - Bug Fixes
other mods
EGO - Enderal Gameplay Overhaul
EGO patches
some exceptions like dyndolod etc.
```

**Zenderal's patches go in the "EGO patches" slot — after EGO.** A patch that loads before EGO is
overwritten by it record-for-record and does nothing. There is no configuration in which loading a
gameplay patch above EGO is correct.

## Declaring EGO as a master

EGO is a plain ESP (no ESM flag). Mastering an ESP from an ESP is legal and normal here. In
`RecordData.yaml`, masters go in **load order**:

```yaml
ModHeader:
  MasterReferences:
  - Master: Skyrim.esm
  - Master: Update.esm
  - Master: Enderal - Forgotten Stories.esm
  - Master: Enderal SE - Gameplay Overhaul.esp
```

Your patch can still be ESL-flagged — the ESL constraint is on **your** new FormIDs (`0x800–0xFFF`),
not on your masters, and overrides consume none of them. See CLAUDE.md's FormKey discipline.

Only add EGO as a master if you actually reference one of its 974 new records. If you are merely
overriding a record EGO also overrides (e.g. a Skyrim.esm weapon), you need no new master — you just
need to build your version **from EGO's copy**.

## The five rules

### 1. Copy EGO's record file, never the master's

CLAUDE.md guardrail 5 in its EGO-specific form. For any FormKey listed in
[`conflict-index.md`](conflict-index.md), the winning record before your patch is **EGO's**. Start
from `reference/mods/EGO/esp/<Type>/<EditorID> - <hex>_<master>.yaml`, copy it into your patch's
Spriggit tree, and edit only the fields you mean to change.

Copying the `EnderalFS/` or `Skyrim/` version instead silently reverts EGO for that record —
including its stripped-localisation `Name:`/`Description:` shape, which is the tell-tale sign you
did (see below).

### 2. Never override `Player 000007:Skyrim.esm` casually

It carries **42 EGO perks**, and EGO's whole player ruleset lives on them. If you must touch it,
copy EGO's record. If you only need to *add* something, ask first whether a separate ability spell
or a perk on an existing EGO perk's chain would do instead.

### 3. Treat `['Name', 'Description', 'Version2']` as a null diff

EGO is not localized (see [`plugin-anatomy.md`](plugin-anatomy.md#localisation-is-stripped)), so
those three fields differ from the master on essentially every item record for structural reasons.
When you diff EGO against a master to decide what it changed, filter them out or you will drown.
Conversely, when you diff **your patch** against EGO and see them come back as a `Values:` list,
you copied from the wrong source.

### 4. Injected records must be referenced through EGO

61 records (listed at the top of [`conflict-index.md`](conflict-index.md)) carry a `Skyrim.esm` or
FS suffix for a FormID the master does not define. `ChaurusChitin 03AD57:Skyrim.esm`,
`DeflectArrows 058F68:Skyrim.esm`, the Dragon Priest mask armours and the two
`_00E_CraftingPlan_03ESilver*Forged` blueprints are all EGO's own content wearing a master's
FormID.

Referencing one means depending on EGO, so declare EGO as a master and be explicit about it in the
patch's notes. Do not assume the FormID resolves without EGO — it resolves to nothing.

### 5. Check EditorIDs against EGO, not against Enderal

EGO renames base records. The one that will bite is the keyword
`ImmuneStrongUnrelentingForce 0172AC:Skyrim.esm` → **`XionImmuneStrongForce`**; there are also 326
NPC, 139 weapon, 59 armour, 31 leveled-list, 28 loading-screen, 17 book and 10 combat-style
EditorID changes. A grep for an Enderal EditorID in an EGO load order can come back empty for a
record that is very much present.

## Known collision hot spots

| If your patch… | It will collide with |
|---|---|
| adds a craftable weapon/armour with a blueprint | `_00ETraderCraftingPlansA/B/C` — EGO rewrites all three, sets `ChanceNone 0.4` and drops every entry to `Level 1` |
| adds loot anywhere | 126 overridden leveled lists including every `01E_`–`04E_` loot family and every `DeathItem*` |
| retunes any GMST | 99 GMST overrides + 18 GMSTs EGO **creates**; the engine binds by EditorID, so EGO's record wins |
| touches any NPC | 1106 NPC overrides, 666 of which carry EGO perks |
| touches a talent perk | 122 perk overrides + the 209 Message records that display their text |
| touches weapon or armour stats | 313 WEAP + 295 ARMO overrides |
| adds a container or moves an object | 125 interior cells + 126 exterior cells + 10 worldspaces + 433 placed refs |
| changes creature behaviour | 59 CombatStyles, 58 MovementTypes, 89 Races |
| ships a Papyrus script | check the six names in [`scripts.md`](scripts.md) — that conflict is MO2 file order, not load order |

## Working the conflict index

```bash
# Does EGO touch this record?
grep -n 'CraftingPlansC' arch-docs/EGO/conflict-index.md

# What exactly did EGO change on it?
python arch-docs/EGO/tools/ego_report.py diff 148ABE

# What does EGO change across a whole record type?
python arch-docs/EGO/tools/ego_report.py fields Weapons
python arch-docs/EGO/tools/ego_report.py fields Weapons -v Critical   # per-record, showing one field
```

`diff` prints a unified diff of *the winning master's* record against EGO's, so the `+` side is
exactly what your patch must preserve.

## Finding the German-text defects

72 string fields hold German text in EGO's single English `Value:` slot (23 of them player-facing —
see [`world-npcs-and-loot.md`](world-npcs-and-loot.md#a-known-defect-worth-patching)). To regenerate
the list after an EGO update:

```python
# scan: EGO's English Value == the master's German string
import json, os, yaml
idx = json.load(open('arch-docs/EGO/tools/.ego_index.json'))
T = {"EGO": "reference/mods/EGO/esp", "EnderalFS": "reference/base/EnderalFS",
     "Skyrim": "reference/base/Skyrim", "Update": "reference/base/Update"}

def base_of(fid, m):
    for t in ("EnderalFS", "Update", "Skyrim"):
        r = idx[t].get(fid)
        if r and r[2] == m:
            return t, r[0]
    return None, None

def langs(node):
    v = node.get('Values') if isinstance(node, dict) else None
    return {x['Language']: x['String'] for x in v
            if isinstance(x, dict) and isinstance(x.get('String'), str)} if isinstance(v, list) else {}

for k, (rel, eid, m, _n) in idx['EGO'].items():
    typ = rel.split(os.sep)[0]
    if typ in ('Cells', 'Worldspaces'):
        continue
    bt, brel = base_of(k.split(':')[0], m)
    if not brel:
        continue
    a = yaml.safe_load(open(os.path.join(T[bt], brel), encoding='utf-8', errors='replace')) or {}
    b = yaml.safe_load(open(os.path.join(T['EGO'], rel), encoding='utf-8', errors='replace')) or {}
    for f in ('Description', 'Name', 'BookText', 'ShortName', 'ActivateTextOverride'):
        av, bn = langs(a.get(f)), b.get(f)
        bv = bn.get('Value') if isinstance(bn, dict) else None
        en, de = av.get('English'), av.get('German')
        if isinstance(bv, str) and isinstance(en, str) and isinstance(de, str) \
           and bv.strip() == de.strip() != en.strip():
            print(typ, eid, f)
```

Fixing them is a clean, self-contained patch: copy EGO's record, replace the `Value:` with the
master's English string, change nothing else.

## Pre-ship checklist

- [ ] Patch loads **after** EGO in the list.
- [ ] Every record in the patch was copied from **EGO's** YAML where EGO overrides that FormKey
      (`grep` the FormKey in [`conflict-index.md`](conflict-index.md)).
- [ ] No `Values:` localisation blocks re-introduced on records EGO had collapsed to `Value:`.
- [ ] Masters declared in load order, EGO last; EGO declared **only** if actually referenced.
- [ ] No navmesh (`NavigationMeshes:`) carried on any cell — EGO doesn't, and neither should you.
- [ ] If the patch ships a `.pex` that EGO also ships, its MO2 priority is deliberate and recorded.
- [ ] Built with Spriggit **0.40.0**, deserialized, and opened in xEdit in `-EnderalSE` mode.
- [ ] Guardrail 8: say plainly whether you have established that it *builds* or that it *runs*.
