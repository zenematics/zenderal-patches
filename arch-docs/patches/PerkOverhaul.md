# PerkOverhaul

- **Source:** `src/PerkOverhaul/`
- **Ships:** `Zenderal - Perk Overhaul.esp` (ESL; masters `Skyrim.esm`, `Update.esm`, FS, `Enderal SE - Gameplay Overhaul.esp`) + `ZEN_PO_BladeMasterCritHealSC.pex`
- **Requires:** powerofthree's Papyrus Extender (`PO3_Events_AME.RegisterForCriticalHit`)
- **FormID block:** `0x800–0x8FF` reserved for the overhaul; `0x800–0x803` used
- **Status:** built 2026-10-21, Spriggit round trip identical (bar property sort order). **Unverified in game.**

Zenderal's rework of Enderal's class perk trees, on top of EGO. One plugin that grows class by
class; every perk it touches is EGO's winning record copied verbatim with only the reworked values
changed. Before adding a perk, run the live overrider scan (below) — if another list plugin touches
the PERK or its MESG, this plugin must forward it too.

## How Enderal shows a perk

Each class perk is a PERK plus a MESG (`_00E_Message_<Class>_<Perk>`) that the Hero Menu shows as
the description and unlock button. **Change both** — the PERK's own `Description` is not what the
player reads. EGO overrides the MESGs with its own English text (and German PERK names; EGO is not
localized), so copy the MESG from `reference/mods/EGO/Messages/`, not from base.

## Blade Dancer

### Blade Master — `069D52` (PERK) / `069E31` (MESG)

Report (2026-10-21): Blade Dancer feels weak next to two-handed.

| | Base Enderal | EGO | Zenderal |
|---|---|---|---|
| Weapons | one-handed swords (`WeapTypeSword 01E711`) | swords **or** daggers (`+ WeapTypeDagger 01E713`) | EGO's |
| `CalculateMyCriticalHitChance` | +10 | +10 | **+25** |
| On crit | — | — | **+10 Health** (sword/dagger crits only) |

**[verified]** in `reference/base/Skyrim/Perks/` and `reference/mods/EGO/Perks/`. Live scan of the
`Ultra` profile: only EGO overrides `069D52` and `069E31`.

The heal is a perk `Ability` entry → `ZEN_PO_BladeMasterCritHealAb 000800` (SPEL, Ability) →
`ZEN_PO_BladeMasterCritHealME 000801` (MGEF, Script, HideInUI; copied from Enderal's
`_00E_AbEnterBleedout 0F8628`) → `ZEN_PO_BladeMasterCritHealSC`. The script registers for Papyrus
Extender's `OnCriticalHit` on effect start, and on each crit whose aggressor is the perk's owner and
whose weapon carries `WeapTypeSword`/`WeapTypeDagger`, `RestoreActorValue("Health", HealAmount)`
(`HealAmount` = 10, a property on the MGEF). There is no vanilla perk entry point or condition for
"this hit was a crit", which is why this needs PE.

Unverified: whether PE's `CriticalHit` event source fires for NPCs (the engine's `CriticalHit` event
feeds the player's crit stat) — irrelevant here, since the script ignores any aggressor that isn't
the ability's owner.

## Trickster (archery)

### Musket wording on the archery Hero Menu texts (2026-10-22)

Request: the archery perks' text should name muskets. **Text only — every archery perk already
applies to muskets [verified]:** Ordo Legionis' muskets are crossbow-type WEAPs (`AnimationType:
Crossbow`, `GetEquippedItemType` 12) that also carry `WeapTypeBow 01E715`.

| MESG | Perk | Why muskets already count |
|---|---|---|
| `066858` Strong Bowstring | `069CF0`/`085AB5` | `HasKeyword 01E715` |
| `066856` Skilled Hands | `06685F` | Enderal SE - Crossbows' copy: item type 7 **or** 12 |
| `066857` Eagle Eye | `066867` | `HasKeyword 01E715` |
| `069D6F` Concentration | `069CD2` | `HasKeyword 01E715` |
| `05BD2E` Thief Apprentice | `069CD1` | EGO ability `001DAA`: item type 7 or 12 |
| `069D70` Ranger | `069CD4` | `bPerkQuickShot` graph flag (crossbow reload root reads it) |
| `069D71` Rapid Shot | `069CD5` | `PerkAbQuickShot 106642` (Crossbows' copy: 7 or 12) + `bPerkQuickDraw`, which plays the crossbow reload at 1.3× ([`Prophecy.md`](Prophecy.md)) |
| `069D73` Expert Locksmith | `069CD7` | `HasKeyword 01E715` |
| `069D74` Fatal Shot | `069CEA`/`085AB2` | `HasKeyword 01E715` |
| `069D75` Master of the Bowstring | `069CED` | `HasKeyword 01E715`; slow-time ability `103AD8` unconditioned |
| `069D76` Eye of the Storm | `069CEC`… | EGO's spell `03A472`: item type 7 or 12 |
| `069D77` Shadow Player | `069CEE` | `HasKeyword 01E715`; EGO ability `001DEF`: 7 or 12 |
| `069D78` Master Thief | `069CEF` | arrows' stagger: the perk's ability, no weapon check |

Live scan: EGO is the only other plugin on any of these MESGs (base Enderal wins `066857`, `069D70`,
`069D75`). Left out: Flame Shot `069D6E` (owned by [`FlameShot`](FlameShot.md), already says
"flame musket balls") and Replica `069D72` (lockpicking only). Only the MESGs changed — PERK
`Description`s untouched, so no PERK overrides (Skilled Hands' PERK is Crossbows', which this plugin
does not master). Rapid Shot keeps EGO's "20%" although the effect is ×1.3.

Generated: `python -I src/PerkOverhaul/tools/01-build-archery-musket-text.py` (copies the winning
MESG, asserts each replacement matches once). The three base-sourced records keep all their languages
in the YAML; Spriggit writes only English into this non-localized plugin, so a round trip collapses
them — expected.

### Replica — ammo recovery (2026-10-23)

Request: Replica (`069CD6`, base Enderal's: `ModLockpickingKeyRewardChance` 100) also gives a 30% chance
to recover ammo used on a now-dead target.

How the engine already does it: a bow/crossbow projectile that hits an actor is put into the target's
inventory with probability `iArrowInventoryChance 10EAD8` — 33 in base Enderal, **25 under EGO
[verified]** — which is why arrows and musket balls sometimes turn up on corpses. Replica adds a second,
independent roll on the same principle:

`PerkAbilityEffect` → `ZEN_PO_ReplicaAmmoRecoveryAb 000802` (SPEL, Ability) →
`ZEN_PO_ReplicaAmmoRecoveryME 000803` (MGEF, Script, HideInUI) → `ZEN_PO_ReplicaAmmoRecoverySC`.
The script registers for Papyrus Extender's `OnWeaponHit` (fires for hits *by* the effect's owner). On
a hit with a projectile, on an actor, from a weapon carrying `WeapTypeBow 01E715` (bows, crossbows,
muskets, pistols), it rolls `Chance` (30) and adds one of the owner's equipped ammo
(`PO3_SKSEFunctions.GetEquippedAmmo`, skipped if not playable, e.g. bound arrows) to the target's
inventory, silently. Per hit, not per kill — the ammo sits in the target's inventory until it is looted
(a living archer target could in principle shoot it back, as with the engine's own roll).

Hero Menu MESG `069D72` (base Enderal's, no overriders) gets the line through `tools/01`; the PERK's own
English description is hand-edited to match. Unverified in game.

## Regenerating / checking overriders

```
python -I src/PerkOverhaul/tools/00-scan-overriders.py 069D52 069E31   # every enabled plugin touching these Skyrim.esm IDs
```

Same master-aware binary walk as `src/MaceSpeed/tools/00-scan-maces.py`, generalised to any
Skyrim.esm FormID. The records themselves are hand-edited copies of EGO's (no generator yet).

## Compiling

`papyrus-compile`'s recipe failed silently on 2026-10-21 (even on a known-good script). The cause, found
2026-10-24: **any missing `-i` folder** makes the compiler drop its output with no error, and two
`tools.json` import paths had gone stale (see [`papyrus.md`](../workspace/papyrus.md#gotchas)). Fixed in
`tools.json`; the config recipe compiles again.
