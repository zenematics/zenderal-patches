# Voice files for new dialogue (`.fuz`)

A response (INFO) with no voice file plays silent and its subtitle flashes by in a moment: the list has **no Fuz Ro
D'oh** (FLICK, despite the name, is a console kit). A `.fuz` = xWMA audio + FaceFX `.lip`, and with one the line plays
for its length and the mouth moves. Everything needed ships with the Creation Kit install (`tools.json`
`papyrusCompiler`'s `Root/Tools`): `LipGen/LipGenerator/LipGenerator.exe` (+ `FonixData.cdf`), `Audio/xwmaencode.exe`,
`LipGen/LipFuzer/LIPFuzer.exe`. No xVASynth, no ffmpeg on this machine (2026-11-19).

## Where the engine looks **[verified]**

```
Sound\Voice\<plugin file name>\<voice type EditorID>\<quest>_<topic>_<FormID>_<n>.fuz
```

- `<quest>` = the INFO's quest EditorID cut to **10** characters.
- `<topic>` = the topic EditorID cut so that quest + topic make **25** characters (`topic[:25 - len(quest[:10])]`).
  Measured on 219 of Enderal's own files in `L - Voices.bsa`: `BanditDialogue` -> `banditdial_` + 15 topic characters,
  `FS_NQ01` (7) -> 18, `MQ05` (4) -> 21. Not a flat 15.
- `<FormID>` = the INFO's FormID, 8 hex digits, **plugin index as 00** (an ESL's local ID padded likewise).
- `<n>` = the response number inside the INFO (1-based). Case does not matter.
- Keep quest and topic EditorIDs short enough that nothing is cut, or compute the cut exactly as above.

## Recipe (what `src/FogWood/tools/03-install-rogue-voice.py` does)

1. The recording as 44.1 kHz 16-bit mono PCM WAV (the tool converts any PCM WAV with numpy; MP3 is not readable here).
2. `LipGenerator.exe <wav> "<the record's exact text>"` writes `<wav>.lip` beside it (and a `tmp16khz.wav` in the
   working directory). The text must be the INFO's text, or the lip sync drifts.
3. `xwmaencode.exe <wav> <xwm>`.
4. `LIPFuzer.exe -s <dir> -d <dir> --norec` fuzes every `<name>.xwm` + `<name>.lip` in the folder into `<name>.fuz`.
   Its `-i` include filter matched nothing in our runs: give each line its own folder instead.
5. Copy to the path above inside the MO2 mod that ships the plugin (Patch Collection for the Rogue). Audio is not
   committed.

Reusing an NPC's own recordings instead (Clockwork Thunder's Yerai, `src/ClockworkThunder/tools/06`): copy the
existing `.fuz` under the new name and give the INFO the recorded line's exact text.
