# LevelUpSound

- **Source:** `src/LevelUpSound/` (`tools/01-build-level-up-sound.py` builds the sound file)
- **Ships:** `Zenderal - Level Up Sound.esp` (ESL, HEDR 1.7, one override) + 1 loose `.wav` (not committed)
- **FormID block:** none
- **Pillar:** curator's taste

## What it does

Enderal's level-up runs `_00E_EPUpdateFunctions` (on the player, `Player 000007`), which plays its `UILevelUp`
property: sound marker `UILevelUp 057B45:Skyrim.esm`, descriptor `UILevelUpSD 057B44:Skyrim.esm` **[verified from
SureAI's source and the records; EGO's Player keeps the same property]**. Base Enderal's descriptor plays
`Sound\FX\Enderal\Music\Enderal - Levelup.wav`. *Rumble - UI.esp* (Rumble Additions) overrides it with Skyrim's
`Sound\FX\UI\UI_LevelUp.wav` plus `RumbleValues 255`, so the list was already not playing Enderal's sound.

The override is Rumble - UI's record verbatim (keeps its rumble) with only `SoundFiles` changed to
`Data\Sound\FX\Zenderal\ZEN_LevelUp_HolySpellCast.wav`. That file is the curator's Motion Array SFX
`MA_Warp-Efx_Holy_Spell_Cast_4.wav` (licensed, not committed), converted to 16-bit / 44.1 kHz stereo (4.19 s, peak
-4.0 dBFS, no gain change) by `tools/01`, which reuses [`BloodyCritSound`](BloodyCritSound.md)'s converter.
Rumble - UI is the only other list plugin touching `057B44` (2026-10-26), and it is not mastered.

## Load order

**Owns** `057B44`. The plugin loads right after `Rumble - UI.esp` (Ultra `plugins.txt`, 2026-10-26).

## Rebuilding

`python src/LevelUpSound/tools/01-build-level-up-sound.py <source.wav>` writes the MO2 mod's `.wav`; build the
plugin from `LevelUpSoundESP/` as usual.

## Status

Built 2026-10-26: round trip identical apart from the header description's wrapping. Deployed as the MO2 mod
`Zenderal - Level Up Sound` and enabled in Ultra. **Unverified in game.**
