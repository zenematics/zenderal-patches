# FHRDirectionalFrequency

- **Source:** `src/FHRDirectionalFrequency/` (generated: `tools/01-build-fhr-directional-frequency.py`)
- **Ships:** inside `Zenderal - Patch Collection` since 1.9 (2026-11-09; was its own MO2 mod
  `Zenderal - FHR Directional Frequency`, which had no Wabbajack rule; no other mod ships these paths, so no winner
  changed). Deploy rebuilds into Patch Collection:
  - `Zenderal - FHR Directional Frequency.esp` (ESL, HEDR 1.7). Masters Skyrim.esm, `For Honor Balance Patch.esp` and
    `Reforged Directional Combat.esp`; load anywhere after `Reforged Directional Combat.esp`.
  - 120 OAR `user.json` overrides, generated straight into the mod and not committed. FHR ships no `user.json` at
    those paths, so the mod's MO2 position doesn't matter.
- **FormID block:** none (four overrides)
- **Owns:** `EmpoweredRightHeavy 801`, `EmpoweredLeftHeavy 802`, `EmpoweredRightLight 804`, `EmpoweredLeftLight 805`
  (all `:Reforged Directional Combat.esp`)
- **Status:** built and round-trip clean 2026-11-08, deployed. Unverified in game.

## Why

Curator's taste (2026-11-08): "I don't ever actually see enemies do these directional attacks".

The mechanic works, but For Honor Reforged makes it rare:
- **Side attacks.** In each of FHR's 30 `* - NPC Addon` movesets, an enemy's light or power attack is a side attack on
  an OAR `Random < 10` roll per side, or `< 30` (light) / `< 50` (power) while it carries that side's arrow. About 1
  light attack in 5 goes to the side.
- **Arrows.** Dynamic Animation Casting casts `EmpoweredDirectionalTrigger 800` on the enemy's attack window
  (`MCO_WinOpen` / `AttackWinStart`). Each arrow effect needs the side marker that the attack's PIE tag (`$RightLight`
  …) just put up, plus `GetRandomPercent <= 10` (light) or `<= 15` (heavy). Only side attacks carry those tags, so an
  enemy charges an arrow about once per 50 attacks.

Evidence that the chain ran:
- DAC's log registers the triggers.
- SPID gives every NPC the perks.
- `ZenParryTrace` (2026-11-02) logged a Vagrant charging Right, then Left arrows. That was 3 arrows in a session of
  about 14 minutes, mostly with the musket.

## The change

| Roll | FHR | Now |
|---|---|---|
| Side light/power attack, per side | 10% | 25% |
| … while carrying that side's arrow (light) | 30% | 50% |
| … while carrying that side's arrow (power) | 50% | 60% |
| Charge a light arrow after a side light | 10% | 30% |
| Charge a heavy arrow after a side power attack | 15% | 40% |

- OAR checks left before right, so about 44% of an enemy's light attacks are now side attacks.
- Back attacks are reactions to the player blocking (50% already) and stay as FHR has them.
- The back arrows have no icon in FHR's SIF set (`Unused/`), so they are untouched too.

The generator asserts every submod's Random shape (one plain roll of 10, one buffed roll in an AND with
`HasMagicEffect`) and each effect's single roll. It stops on anything else.

## Upkeep

After a For Honor Reforged update:
1. Re-serialize `Reforged Directional Combat.esp` into `reference/mods/FHRDirectional`.
2. Run `python -I src/FHRDirectionalFrequency/tools/01-build-fhr-directional-frequency.py`. It rewrites the mod's
   `meshes/` folder.
3. Deserialize and redeploy the `.esp`.

Tune the numbers with the constants at the top of the generator.

## To verify in game

Fight a few humanoid melee enemies (bandits, Vagrants):
- Side swings should be common.
- Arrows should show over them within a fight or two.
- The arrows should still strip as before ([`FHRDirectionalStripFix`](FHRDirectionalStripFix.md)).
