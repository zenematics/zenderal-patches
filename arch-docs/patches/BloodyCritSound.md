# BloodyCritSound

- **Source:** `src/BloodyCritSound/`
- **Ships:** `Zenderal - Bloody Crit Sound.esp` (ESL, HEDR 1.7, masters `Skyrim.esm` only) + 1 loose
  `.wav`, MO2 mod `Zenderal - Bloody Crit Sound`. The `.wav` is not committed.
- **FormID block:** _(none — one override)_

## What it does

Replaces the critical-hit sound with a hard, bloody sword cut. This is the curator's taste, not a bug fix.
The mod stands alone: it plays its own file, so it works with or without Impactful Crits and in any MO2 order.

## Mechanism

- The crit sound is `UISneakAttack 0C06CE:Skyrim.esm`, a one-file SNDR. In stock Enderal 2.1.4.4 it
  plays `Data\Sound\FX\UI\UI_SneakAttack_01.wav`. **[verified]**
- The patch points `SoundFiles` at `Data\Sound\FX\Zenderal\ZEN_CritBloodyCut_01.wav`. Impactful Crits
  still replaces `UI_SneakAttack_01.wav`, but nothing plays that file any more. Disable Impactful Crits
  or keep it; either way it does nothing.
- **Owns `0C06CE`.** A byte scan of all 517 plugins in the installed list (2026-10-21) found one
  other override: `Rumble - UI.esp` (Rumble Additions), which adds `RumbleValues: 255`. The patch
  copies Rumble's record verbatim and changes only `SoundFiles`, so crits still rumble.
  Rumble is not mastered, because it masters `Dawnguard.esm`. That makes load order the only thing
  keeping this patch ahead: **it must load after `Rumble - UI.esp`** (placed directly after it in
  `Ultra/plugins.txt` and `loadorder.txt`). **[verified]**
- Sound source: Motion Array SFX `MA_Asak SFX_SwordKnifeBloodyCut_sword_hard_bloody.wav` (24-bit /
  48 kHz stereo, 1.41 s, peak −0.5 dBFS). It is licensed, so neither the source nor the output is
  committed. `tools/01-build-crit-sound.py` writes 16-bit / 44.1 kHz stereo PCM (windowed-sinc
  resample, dither, no gain change) to the path the SNDR names.

## Rebuild

```
python src/BloodyCritSound/tools/01-build-crit-sound.py "<source.wav>" [<mods dir>]
```

The `.esp` is built from `BloodyCritSoundESP/` by `build/build.ps1` and needs copying into the same MO2
mod. If you change the file path, change it in both the SNDR and the tool's `REL`.

## History

- 2026-10-21: first shipped as a loose replacement of `UI_SneakAttack_01.wav`, sorted above Impactful
  Crits. The same day it became the standalone ESL + own-path version described above.

Built and round-tripped 2026-10-21 (records identical). Not yet verified in game.
