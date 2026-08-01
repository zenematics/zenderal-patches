# Combat

What a combat overhaul collides with in Enderal, and what transfers unchanged from Skyrim. This is
the reference for the **modern combat** pillar.

## What transfers, and what doesn't

The good news first: Enderal kept Bethesda's **keyword taxonomy** intact. **[verified]** The base
game's 693 keywords still include the full vanilla set with vanilla FormIDs —
`ArmorHeavy`, `ArmorLight`, `ArmorCuirass`, `ArmorMaterialSteel`, `ArmorMaterialDaedric`,
`ArmorMaterialElven`, `WeapMaterial*`, `WeapType*` and so on.

| Surface | Transfers? | Notes |
|---|---|---|
| Armor/weapon **keywords** | **Yes** | Vanilla names and FormIDs retained |
| Crafting **bench keywords** | **Yes** | `CraftingSmithingForge` is still `088105`, etc. |
| Animation / behaviour files | **Yes** | Same engine, same skeleton |
| Combat **AI (CombatStyle records)** | Partly | 121 base + 7 FS styles, all Enderal's own content |
| **Perks / progression** | **No** | Enderal's own trees and UI — see below |
| **Brawl / intimidate** | **No** | Deliberately removed (stubbed scripts) |
| Vanilla **XP / skill-use advancement** | **No** | Enderal has its own XP curve |
| Vanilla **weapon/armor records** | **No** | 316 weapons, 993 armors — all Enderal's |

## The progression collision — read this first

A combat mod that adds perks to vanilla perk trees **does nothing visible in Enderal**. Enderal never
draws the vanilla tree; the player has no way to see or buy the perk. **[verified]** — see
[`progression-and-classes.md`](progression-and-classes.md).

Your options, in descending order of safety:

1. **Attach behaviour to keywords.** The vanilla keyword set is intact, so a mod keyed on
   `ArmorHeavy` or a weapon material keyword works as designed. This is the cheapest path.
2. **Add the perk to an Enderal memory tree's `*Perks` FormList.** It then becomes buyable. Requires
   overriding that FormList — a conflict point with anything else touching it.
3. **Grant the perk directly** via a MGEF `PerkToApply`, a script `AddPerk`, or an affinity ability
   spell. Bypasses the UI entirely; document it so nobody looks for it in the menu.
4. **Don't ship the perk.** Often the right answer for a ported Skyrim mod whose perks duplicate an
   Enderal talent.

## Combat styles

**121 CombatStyle records in base Enderal, 7 in Forgotten Stories.** **[verified]** The FS ones are
all class machinery:

```
_00E_Phasmalist_CombatStyleBalanced   _00E_Phasmalist_CombatStyleMagic
_00E_Phasmalist_CombatStyleMelee      _00E_Phasmalist_CombatStyleMissile
_00E_Phasmalist_CombatStyleTank       _00E_Phasmalist_CombatStyleWerewolf
_00E_FS_csTharael
```

The Phasmalist's summoned apparition takes a combat style from
`_00E_Phasmalist_ChooseableCombatStyles` (`01E94B:Enderal - Forgotten Stories.esm`), with
`_00E_Phasmalist_CombatStyleWerewolfList` (`02F1AF`) for the werewolf case. **[verified]**

> **Patch note.** If you rebalance combat styles wholesale, the six Phasmalist styles are
> *player-facing* — they are what the player's summon fights like. Treat them as player abilities,
> not as NPC AI, and expect the FS class to feel different if you retune them.

## The brawl system is gone

Enderal ships `dgintimidateplayerscript.psc` and `dgintimidatealiasscript.psc` as explicit
`; DUMMY, DO NOTHING` stubs — 4 lines where vanilla has 59. **[verified]**

Consequences:

- Any mod that hooks brawl start/end, or expects `DGIntimidateQuest` to run, is hooking nothing.
- **If you compile a script against vanilla's copy of these**, you link in brawl logic Enderal
  deleted. It compiles clean and misbehaves at runtime. Get the import order right.

## Races

**117 race records in base Enderal, 51 more in FS.** **[verified]** Enderal's bestiary is its own —
do not assume a Skyrim creature record exists, and do not assume `ActorTypeNPC`-style assumptions
from Skyrim mods hold for Enderal's creatures.

FS adds `ActorTypeWerewolf` and `ActorTypeElementalWolf` keywords for the Theriantrophist class.
**[verified]**

## Damage and combat globals

Enderal-specific combat globals worth knowing **[verified]**:

| Global | Purpose |
|---|---|
| `_00E_CombatLevelUps` | combat-driven levelling hook |
| `EldritchDamageDivider`, `_00E_EldritchDamageBlockerConc` | the Eldritch damage type |
| `MagicSpellEldritchDamage` (keyword) | tags Eldritch-damage spells |
| `DamageLetKnowTierII` (keyword) | damage-tier tagging |

Enderal has a **custom damage type (Eldritch)** with its own divider global and keyword. A damage
overhaul that only knows about fire/frost/shock will not scale it.

## Class-specific combat systems (Forgotten Stories)

Both FS classes add combat mechanics that a combat overhaul can collide with:

- **Theriantrophist** — werewolf transformation, the `_00E_Theriantrophist_Claws` **Weapon** record
  (tagged by the `_00E_FS_Theriantrophist_Claws` keyword), and a *Chymikum* buff family keyed on `_00E_Theriantrophist_Chymikum{Armor,Damage,Fire,Frost,Shock,Life,Speed,Stamina,Effect}`
  keywords. **[verified]** A mod that rescales armour or elemental damage should check these.
- **Phasmalist** — summoned apparitions with their own spell lists
  (`_00E_PhasmalistApparition_Spells` `00DB61`, `_00E_PhasmalistApparition_SpellBooks` `00DB60`) and
  the combat styles above. **[verified]**

## Checklist for a combat patch

- [ ] Does it add perks? If so, how does the player reach them? (§ progression collision)
- [ ] Does it hook brawl/intimidate? That system is stubbed out.
- [ ] Does it assume vanilla weapon/armor **records**? Those are Enderal's. Keywords are fine.
- [ ] Does it rescale damage? Check the Eldritch type and the Chymikum keywords.
- [ ] Does it retune combat styles? Six of them are the Phasmalist's summon — player-facing.
- [ ] Does it ship a `.pex` whose name collides with one of Enderal's 55 overridden scripts?
- [ ] Is every SKSE `.dll` it depends on a **1.5.97** build?
- [ ] Tested with **and** without Forgotten Stories?
