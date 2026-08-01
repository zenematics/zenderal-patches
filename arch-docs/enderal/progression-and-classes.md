# Progression, memory trees and classes

Enderal replaces Skyrim's progression wholesale. Nothing here is vanilla behaviour with different
numbers — it is a different system implemented in Papyrus on top of the same engine.

**Primary source:** `_00E_Game_SkillmenuSC` (`_00e_game_skillmenusc.psc`, 1082 lines),
`_00E_EPUpdateFunctions` (`_00e_epupdatefunctions.psc`), `_00E_TalentLibrary`. All **[verified]**.

## No learning by doing

Skills do not rise from use. Enderal runs its own XP curve and hands out points you spend manually.

`_00E_EPUpdateFunctions` owns it, via these globals **[verified]**:

| Global | Meaning |
|---|---|
| `PlayerExp` | current experience |
| `PlayerLevel` | current level |
| `PlayerNeededExp` | XP required for the next level |
| `EXPMult`, `EXPMultSlope` | curve shape, fed to `ComputeNeededExp(CurrentLevel, Slope, Mult)` |

```papyrus
float Function ComputeNeededExp(int CurrentLevel, float Slope, float Mult)
```

> **Patch note.** Anything that grants vanilla XP, or expects `Game.IncrementSkillBy` / skill-use
> advancement to matter, does nothing useful in Enderal. If a combat mod rewards "skill increases",
> it is rewarding a currency Enderal doesn't spend.

## Three separate point currencies

This is the part most often got wrong. They are **not** interchangeable and they are spent in
different places. **[verified]**

| Currency | Global | Spent on |
|---|---|---|
| **Learning Points** | `Lernpunkte` | raising *skills* (One-Handed, Alchemy, …) |
| **Crafting Points** | `Handwerkspunkte` | raising *crafting* skills |
| **Memory Points** | `TalentPoints` | buying *perks* in the memory trees |

The German names are the real property names in the source — `Lernpunkte` is Learning Points,
`Handwerkspunkte` is Crafting Points. Do not "fix" them.

### Memory Points are mirrored into a vanilla ActorValue

```papyrus
TalentPoints.SetValue(TalentPoints.GetValueInt() + 1)
Game.GetPlayer().SetAV("dragonsouls", TalentPoints.GetValueInt())
```

**[verified]**, appears in `_00e_class_perkscript.psc`, `_00e_erinnerungslehrbuch.psc`,
`_00e_lehrbuch_plus1memorypointsc.psc` and others. `TalentPoints` is authoritative; `DragonSouls` is
a display mirror. **If you grant memory points, you must update both** or the UI desyncs from the
real total. See [`scripting-and-actorvalues.md`](scripting-and-actorvalues.md) for the full list of
repurposed ActorValues.

## The memory trees

There are **11 perk trees** plus index 0 reserved for "no class". Registration, in order, from
`_00E_Game_SkillmenuSC.InitAffinitySystem()` **[verified]**:

| Index | Tree (code name) | Perk FormList | Perks |
|---:|---|---|---:|
| 0 | *(no class)* | `None` | — |
| 1 | Bastion | `BastionPerks` `06686B:Skyrim.esm` | 22 |
| 2 | Derwish *(Bladedancer)* | `DerwishPerks` `06686D:Skyrim.esm` | 22 |
| 3 | Elementalism | `ElementalismPerks` `066875:Skyrim.esm` | — |
| 4 | Espionage *(Infiltrator)* | `EspionagePerks` `066889:Skyrim.esm` | 20 |
| 5 | LifeAndDeath *(Sinistrope)* | `LifeAndDeathPerks` `066873:Skyrim.esm` | 23 |
| 6 | Manipulation *(Thaumaturge)* | `ManipulationPerks` `06686A:Skyrim.esm` | 21 |
| 7 | Rage *(Vandal)* | `RagePerks` `066887:Skyrim.esm` | 22 |
| 8 | Trickery *(Rogue)* | `TrickeryPerks` `06687F:Skyrim.esm` | 21 |
| 9 | Vagabond *(Vagrant)* | `VagabondPerks` `066877:Skyrim.esm` | 23 |
| 10 | Phasmalist **(FS only)** | `FS_PhasmalistPerks` `044EEA:Skyrim.esm` | — |
| 11 | Theriantrophist **(FS only)** | `FS_TheriantrophistPerks` `02EE04:Enderal - Forgotten Stories.esm` | — |

Trees 10 and 11 are registered **only when Forgotten Stories is active**
(`_00E_FS_IsForgottenStoriesActivated == 1`); otherwise their indices are set but no FormList is
bound. **[verified]**

Each tree also has parallel **Talents** and **Words** FormLists — e.g. `ElementalismTalents`
`06686F:Skyrim.esm`, `ElementalismWords` `06687E:Skyrim.esm`. **[verified]** All nine base trees have
the full triple.

> **To add a perk to a tree, you must add it to that tree's FormList.** A Perk record that is not in
> a `*Perks` FormList is invisible to the menu — `GetPerkDistribution()` counts points by walking
> those FormLists. Creating the Perk alone does nothing, and nothing warns you.

## Affinities (hybrid classes)

Once you have invested enough in two trees, you unlock an **affinity** — a hybrid class granted as an
ability **Spell** (`_00E_Affinity_Ab*`). There are 21 affinity slots.

### The unlock rule, exactly

```papyrus
Function TryUnlockAffinity(Int[] PerkDistribution, Int iAffinity, int iMainPerk, \
                           int iSecondaryPerk1, int iSecondaryPerk2 = 0, int iSecondaryPerk3 = 0)
    If PerkDistribution[iMainPerk] >= 10 && Affinity_Spells[iAffinity]
        If PerkDistribution[iSecondaryPerk1] >= 10 || PerkDistribution[iSecondaryPerk2] >= 10 \
           || PerkDistribution[iSecondaryPerk3] >= 10
            affinitiesUnlocked[iAffinity] = True
```

**≥10 points in the main tree AND ≥10 in at least one listed secondary tree.** **[verified]**

### The affinity table

Straight from `UpdateUnlockedAffinities()` **[verified]**. "Main" is the required tree; any one
"secondary" satisfies the second condition.

| Affinity | Main tree | Secondary (any one) |
|---|---|---|
| Battlemage | Elementalism | Derwish / Rage / Bastion |
| Cleric | Manipulation | Bastion / Rage |
| Assassin | Espionage | Derwish |
| Wayfarer | Vagabond | Trickery |
| Black Mage | LifeAndDeath | Elementalism |
| Dark Keeper | LifeAndDeath | Bastion |
| Fencer *(Blademaster)* | Derwish | Rage |
| Bladebreaker | Derwish | Bastion |
| Shadowdancer | Espionage | LifeAndDeath |
| Wandering Mage | Vagabond | Elementalism / Manipulation |
| Arcane Archer | Trickery | Elementalism / Manipulation / LifeAndDeath |
| Ritualist *(Spectralist)* | Phasmalist | LifeAndDeath |
| Spectral Warrior | Phasmalist | Rage / Bastion / Derwish |
| Ghostblade | Phasmalist | Espionage / Trickery |
| Brute | Theriantrophist | Derwish / Rage |
| Drifter | Theriantrophist | Vagabond |
| Druid | Theriantrophist | Elementalism |
| Nightwolf | Theriantrophist | Espionage |
| Ravager | Theriantrophist | LifeAndDeath |

The source comments carry the German names (`Klingentänzer`, `Schwarzmagier`, `Vielgereister`, …) —
useful when matching against in-game German text. Wandering Mage is marked
*"currently not implemented"* in the source. **[verified]**

When more than one affinity is available the player is asked to choose
(`AskForAffinityFS` / `AskForAffinityOld`, branching on
`_00E_FS_IsForgottenStoriesActivated`). **[verified]**

## Talents are three-tier perk + WordOfPower sets

`_00E_TalentLibrary` is the read-back helper **[verified]**:

```papyrus
int Function GetPlayerTalentLevel(Perk Perk01, Perk Perk02, Perk Perk03) Global
    if Player.HasPerk(Perk03)
        return 3
    ElseIf ((Player.HasPerk(Perk02)) && !(Player.HasPerk(Perk03)))
        return 2
    ...

int Function GetTalentLevel(WordOfPower Word01, WordOfPower Word02, WordOfPower Word03) Global
    if Game.IsWordUnlocked(Word03)
        return 3
    ...
```

So a talent is **three Perk records plus three WordOfPower records**, and its "level" is derived by
asking which tier the player has. The naming convention makes them easy to find:
`_00E_Class_Phasmalist_P03_Talent_SummonApparation_01/_02/_03` paired with
`_00E_A3_Phasmalist_SummonApparation1/2/3`. **[verified]**

Enderal SE ships 41 Shouts and 85 WordsOfPower in base, 15 and 42 more in FS — talents are delivered
through the **shout/word machinery**, not through a bespoke system.

## The character menu is drawn by Papyrus

`_00E_Game_SkillmenuSC` extends **ReferenceAlias**, registers for `"Journal Menu"`, and listens on
`OnKeyDown` with configurable keycodes (`iExitHeroMenuKeycode1 = 15` TAB,
`iExitHeroMenuKeycode2 = 1` ESC). **[verified]**

Consequences for patching:

1. **Perks added to vanilla Skyrim perk trees are unreachable.** Enderal never draws the vanilla
   tree. The player cannot see or buy them. This is the single most common way a ported Skyrim
   combat mod silently does nothing.
2. **To be buyable, a perk must be in a `*Perks` FormList** bound to a registered tree.
3. **To be granted without being bought**, hang it off a MGEF `PerkToApply`, a script `AddPerk`, or
   an affinity ability spell instead — and say so in the patch's notes.
4. The class shown to the player comes from `GetPlayerClassName()`: the affinity name if one is
   active, otherwise `Major / Minor` tree names. **[verified]**

## Where points come from

Beyond levelling: skill books and quest rewards. Examples **[verified]**:

| Script | Effect |
|---|---|
| `_00E_Lehrbuch_Plus1MemoryPointSC` | +1 Memory Point |
| `_00E_Lehrbuch_Plus2SkillPointsScript` | +2 Learning Points |
| `_00E_Erinnerungslehrbuch` | memory-book grant |
| `_00E_Handwerksbuch*` (Speechcraft 25/50/75/100) | crafting/skill books at thresholds |
| `_00E_FS_A3_TalentBookSC`, `_00E_FS_NQR05_TharaelTalentBookSC` | FS talent books |

`_00E_TalentBookAchievementUnlocked` (`02ED7B:Enderal - Forgotten Stories.esm`) tracks the related
achievement. **[verified]**

## Checklist for a progression-touching patch

- [ ] Does the perk exist in a `*Perks` FormList bound to a registered tree? If not, how does the
      player get it?
- [ ] If you grant Memory Points, do you set **both** `TalentPoints` and the `DragonSouls` AV?
- [ ] Are you changing affinity thresholds? They are hardcoded at `>= 10` in
      `_00E_Game_SkillmenuSC` — a data-only patch cannot change them.
- [ ] Does your change assume vanilla XP or learn-by-doing? It won't fire.
- [ ] Have you tested with **and** without Forgotten Stories active? Trees 10/11 register
      conditionally.
