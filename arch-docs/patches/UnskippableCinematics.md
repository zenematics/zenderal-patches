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
fork (its own folder first on the import path) and SureAI's unmodified source the same way and requires identical
string tables, then compares with the shipped `.pex` from Enderal's BSAs: equal apart from optimizer `::temp` names,
script-name case and, in `MQ18b`, an unused temp's type name (`float`). Strings cannot see a flipped bool, so since
2026-11-14 it also reads `PlayBink`'s bool literal from the bytecode (string literal = type byte 2 + u16 index, bool =
type byte 5 + one byte) and asserts 1 in the shipped and rebuilt `.pex`, 0 in ours. Nothing else in the list ships
these scripts (loose or BSA scan, 2026-10-25).
To skip videos on purpose, Enderal's MCM "Skip videos" (`_00E_VideoSkip 02E985:FS`) still works.

## Why (2026-10-25)

Reported as "the opening cutscene after Daddy is just a black screen". The intro opens with a full sentence of
narration over black; pressing a key there ended it and the game went to the ship (logs: ~30 s from Daddy's last
line to MQP02's load). Theo's Render Pipeline, CS Upscaling and CS Effects11 were A/B'd first and were innocent
(see [`modlist/mod-gotchas.md`](../modlist/mod-gotchas.md)). With the intro non-interruptible the video played in full
(verified in game); the curator then chose to keep every cinematic unskippable. **Credit SureAI.**

## Status

**Rebuilt 2026-11-14; unverified in game.**

**Postmortem (2026-11-14): every committed and shipped build until then did nothing.** The generator compiled with
`-i="<Enderal>;…"` and no fork folder first. The compiler finds a script by *name* through `-i` (first wins) even when
given a full path, so it compiled **SureAI's** copy of each script and said `1 succeeded`. The fork-vs-rebuild check
compared two compiles of the same SureAI file, and a flipped bool adds no strings, so every check passed. Read from
the bytecode: all seven `.pex` committed on 2026-11-01 (`ef1db439`, the only committed version) and Patch
Collection's copies (byte-identical) still passed `true`. Found while building
[`MQ16YuslanKneelFix`](MQ16YuslanKneelFix.md), whose first build hit the same trap; see
[`papyrus.md`](../workspace/papyrus.md).

The intro test of 2026-10-25 used a first build (`MQP01` only) that was never committed, so whether it held the
fork is unknown. Treat the intro as unverified.

Rebuilt with the fork's folder first and the bytecode assertion; all seven read `false`, in `Scripts/compiled/` and
in Patch Collection (deployed 2026-11-14). Test: start a new game, press a key during the intro's narration over
black; the video must keep playing.
