# UnresolvedRefsCleanup

- **Source:** `src/UnresolvedRefsCleanup/` (generated: `tools/00a-serialize-all.py` → `00b-find-unresolved.py` → `01-build-unresolved-cleanup.py`)
- **Ships:** `Zenderal - Unresolved References Cleanup.esp` (ESL), loaded **last**
- **FormID block:** none (overrides only)
- **Status:** built and round-trip clean. With it loaded, a whole-load-order scan finds **0** unresolved
  references in winning records. Deployed 2026-10-21; DynDOLOD not yet re-run.

## Why

DynDOLOD stopped on 2026-10-21 with *"Unresolved FormID [000A2738] … Apocalypse - Magic of Skyrim.esp
WB_Dreamscape_Container"*. DynDOLOD and xEdit stop on the first such error. So instead of fixing one per run,
every enabled plugin in `Ultra` was serialized (tools/00a, ~20 min for 391 plugins) and every reference in a
**winning** record was checked against an index of all records the load order defines (tools/00b).

That found **529 references in 219 winning records** (534 in 222 after the Iron Golem cleaned copy was added on 2026-10-21). Nearly all are vanilla Skyrim / DLC forms left in mods
ported from Skyrim:

| Winning plugin | Refs | Winning plugin | Refs |
|---|---|---|---|
| Apocalypse - Magic of Skyrim (Enderal patch build) | 187 | DAR Rifles | 19 |
| Dynamic Impact - Slash Effects X | 60 | PG_1 (copies of upstream records) | 17 |
| Deflection | 40 | EVGAnimatedTraversal (its test cell `EVGMotionCourse`) | 16 |
| Audio Overhaul Skyrim | 35 | Wendigo creature mod | 13 |
| TaberuAnimation | 26 | 26 more plugins | 1–11 each |
| JS Knapsacks SE | 20 | | |

In game such references already resolve to None, so removing them changes no behaviour.

Not counted: engine-hardcoded IDs below `0x800` (for example PlayerRef `000014`), which Spriggit labels with
the referencing plugin's own name. They are resolved whenever the ID exists as a Skyrim.esm form.

## The fix

Each winning record is copied verbatim, and only the dead references go (tools/01):

| Reference shape | Action |
|---|---|
| bare list entry `- XXXXXX:File` (keywords, form-list items, outfit items, race lists) | entry dropped |
| reference on the first line of a list item, or inside one (container item, leveled entry, impact, alternate texture, perk, faction, spell effect, faction relation, recipe component) | whole item dropped (incl. its `Rank`/`Data`/`Count` lines) |
| scalar field (weapon/armour template, ingredient, sounds, music, image spaces, hit shader, explosion, …) | field cleared |
| placed object `Base` missing (EVG's test cell) | `Base` → `XMarker 000034` (invisible, valid) |
| key whose list/mapping became empty | key dropped (Spriggit rejects an empty sequence) |

A list item that is a record (`- MutagenObjectType`) is never dropped, and the generator refuses to proceed
if a removal would touch one. For cells, only the cell header and the affected placed objects are written,
with the `Cells/` group scaffolding. Exterior cells would be refused; none are affected.

Notable effects: Apocalypse's test-area NPC `WB_Kyrgar_Actor` loses 8 Skyrim perks and a Skyrim item.
`WB_ConjureAvengingWraith_Hood` keeps no armour addon, since all three were Skyrim ARMAs. One Apocalypse
leveled list (`WB_OathboundGuardian_Litem_Outfit`) is left empty. COBJ recipes whose component was a
missing Skyrim item lose that component. All of these were already broken in game.

Masters: Skyrim, Update, FS and the 37 other plugins the records reference or win from, in load order.

**Caveat:** 7 plugins failed Spriggit's post-serialize self-check, though their YAML was written and scanned:
EAM Apothecarii Monastery, HotKeySkill, Ark Bridge Overhaul + its EPPI patch, UndercityCutContent,
TempleCutContent and UndercityHome. If DynDOLOD flags one of them, check that plugin by hand.

## Regenerating

**Re-run whenever any winning plugin changes, and always after the other generated last-loaders.**

1. `python src/UnresolvedRefsCleanup/tools/00a-serialize-all.py <scratch>/all`
2. Copy this plugin's current YAML into `<scratch>/all/ZenderalUnresolvedReferencesCleanupesp`, or leave it
   out to regenerate from scratch.
3. `python src/UnresolvedRefsCleanup/tools/00b-find-unresolved.py <scratch>/all <scratch>/unresolved.json`
4. `python src/UnresolvedRefsCleanup/tools/01-build-unresolved-cleanup.py <scratch>/all <scratch>/unresolved.json`
5. Rebuild `RecordData.yaml`'s masters from the output's FormKeys and the winners, then deserialize.
