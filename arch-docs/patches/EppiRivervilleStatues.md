# EppiRivervilleStatues

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/EppiRivervilleStatues/`
- **Ships:** `Zenderal - EPPI Riverville Statues Patch.esp`
- **FormID block:** none (overrides only)

## What it does

Floating bust in the Riverville Mayor's House (`FlusshaimHouseMayor 055DB5`). `man_DaedricShrines_Enderal.esp` (Mandragorasprouts' Statues, load 90 in Alpha 0.5) disables Enderal's statue `12537E` and places `man_sheogorath_Bust` ref `000813` at the desk's ORIGINAL spot; `EPPIriverville.esp` (84) moved that table `12537B` (and `12537E`) by (-314.19, +20.09, +25.39), same rotation. One REFR override moving the bust by that exact offset (computed from the binary floats). Cell header forwarded from the winner, House Cats of Enderal (91), mastered to force load-after. Found by a binary scan of every active plugin for the cell/ref FormIDs. Built 2026-10-08, not yet verified in game.
