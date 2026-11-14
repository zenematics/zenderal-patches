# EnemyThreat

- **Source:** `src/EnemyThreat/` (generated: `tools/01-build-enemy-threat.py`, reader `tools/_npcs.py`, check
  `tools/02-verify.py`; scripts `Scripts/source/ZET_BossEffect.psc`, `ZET_StaggerWatchEffect.psc`; SPID config
  `spid/Zenderal - Enemy Threat_DISTR.ini`; the boss → add table it picked: `tools/boss-adds.json`)
- **Ships:** `Zenderal - Enemy Threat.esp` (ESL, HEDR 1.7) + 2 scripts + `Zenderal - Enemy Threat_DISTR.ini` at the
  archive root. Masters Skyrim, Update, FS, **EGO** and **Zenderal - Prophecy.esp**: load after both. Deployed
  2026-11-13 as its own MO2 mod `Zenderal - Enemy Threat` (Wabbajack `NoMatchInclude`); **not ticked yet**.
- **FormID block:** `0x800–0x80E`
- **Owns:** EGO's `XionStagger 001D16` (the stagger every player power-attack hit casts, via `XionPowerStagger
  001DBD`): EGO's record verbatim + one condition.
- **Needs from Prophecy:** keyword `ZP_StaggerLockout 0xB4C` and the guard on its 10 Stagger effects
  (`guard_staggers` in Prophecy's `tools/01`, 2026-11-13); and `ZP_ProphecyPointsEarned 0x809`.
- **Status:** built, round-tripped through Spriggit, `02-verify` clean (152 FormKeys resolve, 11 stagger effects
  guarded, 77-entry add table). **Unverified in game.**

## Why

Curator, 2026-11-13: *"Because of the power boost the Prophecy tree provides, I think we need to add more difficulty
to the mid and endgame"*, then *"bosses should be way more threatening"*. Chosen in the session (all four boss
options, scaling that follows Prophecy points, at 30 points +25% damage dealt / −30% damage taken).

Why the world falls behind: **nothing in Enderal scales to the player** (0 LVLN, every NPC a fixed level, 2 ECZN with
no level; [`../enderal/bestiary.md`](../enderal/bestiary.md)). Prophecy adds a point every 3 levels on top of
Enderal's talents (10 at level 30, 15 at 45, 30 at 90). EGO's difficulty only multiplies damage to the player (the
list ships Normal, ×1.6). Bosses had nothing of their own: a humanoid boss had a bandit's poise (Chocolate Poise's
pool is per race, `DefaultRace` 1.0), and Prophecy's staggers (Seismic Stomp's 1 s chain on uniques, the Utility
Droid every 6 s, Point Blank, Stunning Blows) plus EGO's stagger on every power-attack hit chained on them.

## 1. Scaling with Prophecy points (`ZET_ScalingPerk 0x800`, every NPC)

SPID: `Perk = 0x800~Zenderal - Enemy Threat.esp` (no filter; SPID never targets the player). 40 entries, 10 steps of
3 points earned (`ZP_ProphecyPointsEarned`, Prophecy's ledger, never lowered by a respec):

| Points earned (≈ level) | Enemy damage dealt | Enemy damage taken |
|---|---|---|
| 0–2 (to 8) | ×1 | ×1 |
| 3–5 (9–17) | ×1.025 | ×0.97 |
| 15–17 (45–53) | ×1.125 | ×0.85 |
| 30 (90) | ×1.25 | ×0.70 |

- Weapons: `ModAttackDamage` (owner = attacker) / `ModIncomingDamage` (owner = victim).
- Spells: `ModSpellMagnitude` / `ModIncomingSpellMagnitude`, only for spells with a damage keyword
  (`EPMagic_SpellHasKeyword`, as EGO's `XionMagicDamage 001DC8`): fire/frost/shock, `EldritchDamage 0164B1`,
  `DamageDrainLife 0164B2`, FS `MagicSpellEldritchDamage 02F286`, EGO poison/light/psionic, Prophecy's
  poison/sun/bleed/unspecific. A damage spell without one of these (some mod spells, scripted `DamageActorValue`) is
  not scaled.
- Owner conditions on every entry: (`IsHostileToActor` PlayerRef **or** `IsInCombat`) and not `GetPlayerTeammate`
  and not `IsCommandedActor`. So companions and summons are untouched; a guard fighting bandits next to the player
  is scaled too, symmetrically with the bandits. `IsHostileToActor` PlayerRef on a perk is Enderal's own usage
  (`_00E_SE_ShadowDancerAddToken 01596A`).
- Applies everywhere, Fog Wood arena included.

## 2. Bosses (`ZET_BossPerk 0x801` + `ZET_BossAbility 0x802`, every `ActorTypeBoss`)

SPID: `Perk = 0x801~…|ActorTypeBoss`, `Spell = 0x802~…|ActorTypeBoss`. **91 bosses** in Enderal 2.1.4.4 + EGO + the
undead overriders + our NPC patches, every one with the keyword on its own record (none inherit it by template, so
SPID's keyword filter sees all of them). Undead Creatures Replacer drops the keyword from Zu-Sherath, Krustis
Darkhand and Ea; our [`UndeadCreaturesReplacerEGO`](UndeadCreaturesReplacerEGO.md) loads after it and keeps it. The
`BossesFaction`-only NPCs are companions (Jespar, Calia, Natara) and are not bosses.

| Rule | How |
|---|---|
| Half damage taken (~2× health) | perk `ModIncomingDamage` ×0.5, `ModIncomingSpellMagnitude` ×0.5 (damage keywords) |
| +30% damage dealt | `ModAttackDamage` ×1.3, `ModSpellMagnitude` ×1.3 (damage keywords) |
| 3× poise | `ModIncomingStagger` ×⅓. Chocolate Poise Reforged sets every hit's vanilla stagger to 0 and multiplies its poise damage by the attacker's entry point 34 (ModTargetStagger) and the **target's 33 (ModIncomingStagger)** (`PoiseAV.cpp`, `HitEventHandler.cpp`, `ActiveEffectHandler.cpp` on GitHub `BlessingS91/Chocolate-Poise-Reforged`) |
| Not stun-lockable | `ZET_BossAbility`'s second effect `ZET_StaggerWatchEffect 0x804` has the condition `IsStaggered == 1`; each time it turns on it casts `ZET_StaggerLockout 0x805` (5 s of `0x806`, keyword `ZP_StaggerLockout`). While it lasts: `ModIncomingStagger` ×0 (no Chocolate Poise break), and every Prophecy Stagger effect and EGO's `XionStagger 001D16` refuse the target (`HasMagicEffectKeyword ZP_StaggerLockout == 0`, put FIRST so it ANDs with any OR group) |
| Phase 2 at half health, once | `ZET_BossEffect 0x803` (`ZET_BossEffect.psc`, `OnHit`, guarded against overlapping hits): rank 1 in `ZET_BossPhaseFaction 0x80C`, then enrage + roar + adds. Later hits only renew an expired enrage |
| Enrage | `ZET_Enrage 0x807`: 600 s of `ZET_EnrageEffect 0x808`, SpeedMult +25 with Enderal's own `_00E_UpdateSpeedmult` (the shape of `_00E_A1_QyraiStanceSpeedMEHidden 067247`), Enderal's Rage-class `_00E_FuryFXShader 07FA6E`; the perk adds ×1.2 damage while it is on (`HasMagicEffect`) |
| Roar | `ZET_RoarExplosion 0x80B` = Enderal's `_00E_A2_PrimalForceExp 066898` (Rage class) without its enchantment, screen effect (no screen flashes, curator's taste) or force; then `ZET_RoarStagger 0x809` (a copy of `StaggerAttackFFContact 07809B`, magnitude 0.75) on the player and PO3 `GetPlayerFollowers()` within 600 units |
| Adds | 2 of `ZET_AddBases[i]` where `ZET_AddBosses[i]` is the boss's base, `PlaceAtMe` at the boss, `StartCombat` on its target. Skipped inside the Fog Wood arena (`ZFW_ArenaFaction 0x806` looked up at runtime: the arena tracks and sweeps only its own spawns) |

Script constants (`EnrageAt` 0.5, `RoarRadius` 600, `AddCount` 2) are `AutoReadOnly`: a save keeps `Auto` values.
Logs `[ZET boss] <name> enraged at …` and `… called 2x …` to the Papyrus log.

### How adds are picked (`pick_adds`)

77 of 91 bosses have one. For each boss: its "family" factions (self-Ally factions, `Creature_*` first; never
`AnimalFaction`, voice factions, `PlayerEnemyFaction` and the like); the add is the generic tier enemy in that faction
whose level is nearest 70% of the boss's (never above it), preferring the boss's race. A candidate must:
- pay kill EP (`_00E_EPOnDeath`) and carry no other script, not be Unique/Essential/Protected, not be a boss;
- have a tier EditorID `_NNE_…` with NN ≠ 00 (`_00E_` is Enderal's quest/town namespace) and none of
  Ambush/Summon/Sit/Dead/Uni/Boss/Patrol/quest stems. First version picked `_Dunkel_33_SabatDunkelhand`, a named
  Darkhand sibling, for four Darkhands, and `_00E_PulverkippeKurek` for bandit bosses;
- have a race from Skyrim/Update/FS/EGO/Undead Creatures Replacer (never Mihail's skeleton race that Lost Ones
  Revised moves some undead onto: two IED crashes in [`EnemyDensity`](EnemyDensity.md)'s hordes), not an
  atronach/elemental (Fog Wood: musket hits on an elite Ice Elemental mostly missed);
- have no package with an `InterruptOverride` (Fog Wood's Vagrant stood still in its sit package).
Another race only when both are people (race keyword `ActorTypeNPC`) or the faction is a creature family
(`Creature_*`, `UndeadFaction`, `SpiderFaction`).

No adds: scripted quest kills without kill EP (Oorbâya, Adila, Rynéus, Avatar of the Black Stone, Andrasta,
Mutated Perversion), and bosses with no family to draw from (Dragon, Black Myrad, Y'gnrok, Triceratops, Horst,
Colossus, Crystal Widow, Aura Thief). They still get everything else.

## Stacking

At 30 points a boss takes ×0.5 × 0.7 = **×0.35** damage and deals ×1.3 × 1.25 = ×1.63 (×1.95 enraged), on top of
EGO's Normal ×1.6 to the player. That is the chosen strength; tune the constants at the top of `tools/01`.

## Not covered (by design or open)

- Stagger effects from other mods (Apocalypse/Triumvirate/Kittytails spells, shouts) are not guarded. Only Prophecy's
  and EGO's power-attack stagger chain.
- `IsStaggered` is re-checked by the engine about once a second, so a very short stagger can end before the lockout
  starts. The 3× poise still applies.
- Paralysis: Ice Shot's freeze already skips uniques and higher-level enemies (Prophecy).
- `XionStagger 001D16`: no other plugin in `reference/mods` overrides it; plugins not serialized there were not
  checked. If one does and loads after this patch, power attacks chain again.

## Testing checklist

1. Tick `Zenderal - Enemy Threat` in MO2; plugin after `Zenderal - Prophecy.esp` (Patch Collection) and EGO.
2. `po3_SpellPerkItemDistributor.log`: `ZET_ScalingPerk` registered; `ZET_BossPerk` and `ZET_BossAbility` on ~91
   bases (the boss lines).
3. A mid-game boss (e.g. a Darkhand, level 33–37): at half health the Fury shader, the roar (player staggers), two
   Lost Ones; Papyrus log `[ZET boss]`. Repeated Seismic Stomp / power attacks: one stagger, then ~4 s steady.
4. `help ZET_` / `GetGlobalValue` on `ZP_ProphecyPointsEarned` to read the step a save is on.

## Regenerate

Rerun `tools/01` then `tools/02-verify.py` after EGO, Undead Creatures Replacer, Lost Ones Revised (+ EGO patch)
or our NPC patches change, and after Prophecy gains a Stagger effect (Prophecy's `STAGGER_MGEFS` assertion fails
first: raise it there, rerun Prophecy, then this).
