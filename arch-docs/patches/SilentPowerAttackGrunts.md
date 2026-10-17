# SilentPowerAttackGrunts

- **Source:** `src/SilentPowerAttackGrunts/`
- **Ships:** *(no plugin — 8 loose `.fuz`, MO2 mod `Zenderal - Silent Power Attack Grunts`)*
- **FormID block:** _(none)_

## What it does

Silences the female player's loud power-attack yells and leaves every other combat sound alone: normal
attack grunts, hit, death and breath sounds still play. This is the curator's taste, not a bug fix.

## Mechanism

- Player combat sounds are `PlayerDialogue` responses, voiced from the race's **default female voice
  type**: `FemaleEvenToned 013ADD` (Nord, Imperial, Breton) and `FemaleElfHaughty 013AF1` (High Elf and
  Half Starling's `WoodElfRace`). None of the list's race mods change either one. **[verified]**
- The files live in `L - Voices.bsa` under `sound\voice\skyrim.esm\<voicetype>\playerdial_playerdialogue__<INFO>_1.fuz`.
  Enderal kept vanilla's INFO FormIDs, so the names match vanilla Skyrim's. **[verified]**
- Power attack = `PlayerDialogue_PowerAttack 0F8590`: INFOs `0F85A3`, `0F85A4`, `0F85A5`, `1295B4`.
  The others, for reference: Attack `12959E–1295A2`, Hit `1295A5–1295A9`, Death `12959B/C`,
  OutOfBreath `0F85A9`, LeaveWater `046F21`. Silence more by adding IDs to `SILENCE` in the script.
- The silent file is SureAI's own: a 0.19 s placeholder in the same BSA
  (`vt_male_priest\genericdia_generic_priest__00111e1b_1.fuz`, peak 1/32768, lip size 0), copied
  verbatim. Nothing is encoded, and nothing is committed.

## How the loud ones were identified (2026-10-15)

The user's recording (`1st person Dagger and Pistol.mp4`, 38.7 s) was decoded to mono 44.1 kHz and
cross-correlated against all 22 decoded player grunts. Matches: power attack at 8.42, 11.29, 13.37,
16.00, 24.99 and 29.61 s (NCC 0.52–0.63) and normal attacks at 2.87 and 3.57 s (NCC 0.32–0.50). All
eight sat at the same −9 dB playback gain, so they are real matches and not noise. Source loudness, loudest
100 ms window: power attack −6.9 to −11.3 dB over 1.2–1.6 s; normal attack −13.6 to −21.4 dB over
about 0.45 s. Loud *and* long is what makes power attacks stand out.

The four `Shout`/`TalentScream` files fail to decode in ffmpeg 7.1 (wmav2 block-length errors). They
were not measured.

## Rebuild

```
python src/SilentPowerAttackGrunts/tools/01-build-silent-grunts.py [<mods dir>]
```

No other mod in the list ships these folders, so MO2 priority does not matter. Loose files beat the BSA.
Built 2026-10-15. Not yet verified in game.
