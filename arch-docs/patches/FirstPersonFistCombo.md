# FirstPersonFistCombo

- **Source:** `src/FirstPersonFistCombo/Pandora_Engine/mod/zfistcombo/` (`info.xml`, `patches/firstperson~1hm_behavior.xml`);
  `tools/01-verify.py` (checks the patch against Pandora's template and simulates every fist set).
- **Ships:** *(no plugin)* Pandora-native patch `zfistcombo`, MO2 mod `Zenderal - First Person Fist Combo` (manifest
  release of the same name). **Needs a Pandora run with `zfistcombo` ticked.**
- **FormID block:** _(none)_

## What it does

First person, both hands unarmed: left click alone chains right hook → left hook → right hook, in every stance whose
punches mark an attack window (no stance = SIGMA, F1 = JellyFish, F2 = CFPAO; see
[`FirstPersonUnarmedStances`](FirstPersonUnarmedStances.md)). Before it every click threw a fresh right hook (curator,
2026-11-10). It also lets a held fist power attack start during a left hook, as it already could during a right hook.

## Why it was broken

`Attack_MCO.esp`'s `AttackRightH2H 0870D6` (our [`MCODirectionalPowerAttacks`](MCODirectionalPowerAttacks.md) copy adds
only "not sprinting") sends `attackStart` for fists instead of vanilla's `AttackStartH2HRight`. In the first-person
`1HM_AttackBehavior` (template `#4333`), `attackStart` is the one-handed weapons' two-swing alternation:
`AttackRight_State` → `AttackLeft_State` with trigger interval `weaponSwing`→`AttackWinEnd` and initiate interval
`AttackWinStart`→`AttackWinEnd`, and back with `weaponSwing`→`AttackWinEndLeft` / `AttackWinStartLeft`→`AttackWinEndLeft`.
Those states play the fist hooks (`H2H_RightHook`, `H2H_LeftHook`), so the chain exists, but its trigger interval
opens on `weaponSwing`:

- SIGMA's and JellyFish's right hooks (their submods take triggers from the clips only) carry no `weaponSwing`;
- every left hook swings with `weaponLeftSwing`, never `weaponSwing` (the vanilla clip generator's own triggers too);
- CFPAO's clips carry no annotations and keep the vanilla triggers (`weaponSwing` 0.43 s, `AttackWinStart` 0.70 s):
  right → left worked there, left → right did not.

Vanilla itself never chained fists on one button: its `AttackStartH2HRight` self-transitions `AttackRight_State`, so
left hooks came only from the left attack button.

## Mechanism

Appended (Pandora-native patch, priority 1 so they come before the vanilla ones for fists; condition
`(iRightHandType == 0) && (iLeftHandType == 0)`, new node `#zfistcombo$0`; blend `#2590` = the vanilla
`attackComboTransition`). **Verified in game 2026-11-10** (curator: "works well"; F3 Boxing with its marked jabs: "seems to work"):

| From | Event | To | Click accepted | Next punch starts |
|---|---|---|---|---|
| `AttackRight_State` (`#4328`) | `attackStart` | `AttackLeft_State` | `preHitFrame` → `attackStop` | `AttackWinStart` → `attackStop` |
| `AttackLeft_State` (`#3425`) | `attackStart` | `AttackRight_State` | `preHitFrame` → `attackStop` | `AttackWinStartLeft` → `attackStop` |
| `AttackLeft_State` (`#3425`) | `attackPowerStartForwardH2HRightHand` | `H2H_AttackRightPowerForwardRightHand` (18) | any time (as from `AttackRight_State`: blend `#2593`, condition `#3429`) | - |

The next punch starts at the attack window, not at `HitFrame`: JellyFish adds its Precision hand collision at the
`HitFrame` (0.30 s) and removes it at 0.40 s, so a chain there would cut the hit. `tools/01-verify.py` (2026-11-10):
0 problems; chains for SIGMA (next punch from 0.43 / 0.47 s), JellyFish (0.60 / 0.64 s), CFPAO (0.70 s).

## Known gaps / open

- **First-Person Boxing (F3)** could not chain from the graph alone: its 0.67 s jabs carry no annotations and keep the
  vanilla triggers, whose `AttackWinStart(Left)` (0.700 s) lies past the clip's end (`attackStop` 0.567 s right /
  0.617 s left). A graph rule that started the next punch earlier would also have changed CFPAO (same vanilla
  triggers). So [`FirstPersonUnarmedStances`](FirstPersonUnarmedStances.md)' overlay mod carries copies of Boxing's
  two jabs with one annotation each (`AttackWinStart` / `AttackWinStartLeft` at 0.54 s, just after the vanilla
  `HitFrame` 0.533 s; `fpu_sources.CLIP_MARKERS`). Chains in `01-verify` and in game (2026-11-10). The right jab's window is 27 ms (0.54 → 0.567 s): at a very low frame rate a click may still drop.
- Unverified that Havok takes a higher-priority appended transition before the vanilla one on the same event; the
  vanilla one is ineligible for SIGMA/JellyFish anyway (no `weaponSwing`), so only CFPAO's timing depends on it.
- Third person untouched (For Honor Reforged's Brawler combo on MCO).
- **Unverified in game.**

## Install / regenerate

Tick `Zenderal - First Person Fist Combo` in MO2, then run Pandora with *Zenderal - First Person Fist Combo* ticked
(and, as after every Pandora run, move the creature behaviors from `overwrite` into `Pandora Output - Zenderal`).
To re-check after a Pandora update: convert the template
(`hkxconv --meta "<Pandora>/Pandora_Engine/Skyrim/Template/actors/character/_1stperson/behaviors/1hm_behavior.hkx" t.xml`,
hkxconv: `src/EnderalPairedAnims/tools/hkxconv`) and run `python src/FirstPersonFistCombo/tools/01-verify.py t.xml`.
