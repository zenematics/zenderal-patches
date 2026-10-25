# UnskippableCinematics

- **Source:** `src/UnskippableCinematics/` (generated: `tools/01-build-unskippable-cinematics.py`, from SureAI's
  2.1.4.4 source in `papyrus-source/enderal-2.1.4.4`), compiled `.pex` committed
- **Ships:** *(no plugin — 7 recompiled scripts, MO2 mod `Zenderal - Unskippable Cinematics`)*
- **FormID block:** none

## What it does

Curator's taste: Enderal's Bink cinematics play through. Every `Game.PlayBink` in SureAI's scripts passes
`abInterruptible = true`, so any key press, click or the console key ends the video at once.

| Script | Video |
|---|---|
| `_00E_MQP01_Functions` (`PlayIntroAndMovePlayerToShip`, after Daddy) | `EnderalIntro.bik` |
| `_00E_MQP03_Functions`, `_00E_MQ101_QuickStart` | `MQP03NearDeathExperience.bik` |
| `_00E_MQ17_Functions` | `MQ17BlackGuardian.bik` |
| `_00E_MQ18a_Functions`, `_00E_MQ18b_Functions`, `_00E_FS_MQ18c_Functions` | `Enderal_Credits.bik` |

Each fork changes exactly that argument (asserted once per script) plus a `; ZP` comment. The generator compiles the
fork and SureAI's unmodified source the same way and requires identical string tables, then compares with the
shipped `.pex` from Enderal's BSAs: equal apart from optimizer `::temp` names, script-name case and, in `MQ18b`, an
unused temp's type name (`float`). Nothing else in the list ships these scripts (loose or BSA scan, 2026-10-25).
To skip videos on purpose, Enderal's MCM "Skip videos" (`_00E_VideoSkip 02E985:FS`) still works.

## Why (2026-10-25)

Reported as "the opening cutscene after Daddy is just a black screen". The intro opens with a full sentence of
narration over black; pressing a key there ended it and the game went to the ship (logs: ~30 s from Daddy's last
line to MQP02's load). Theo's Render Pipeline, CS Upscaling and CS Effects11 were A/B'd first and were innocent
(see [`modlist/mod-gotchas.md`](../modlist/mod-gotchas.md)). With the intro non-interruptible the video played in full
(verified in game); the curator then chose to keep every cinematic unskippable. **Credit SureAI.**

## Status

Intro verified in game 2026-10-25 (the first build, `MQP01` only). The other six unverified in game.
