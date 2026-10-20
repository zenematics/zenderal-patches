# DBVOPlayerLipSync

- **Source:** `src/DBVOPlayerLipSync/` (C++ in `src/`, build with `build.cmd`; `tools/lipdump.py`)
- **Ships:** **no plugin** — `SKSE/Plugins/ZenDBVOLipSync.dll` + `ZenDBVOLipSync.ini`, and CCC's
  `SKSE/Plugins/SD_user.ini`. MO2 mod `Zenderal - DBVO Player Lip Sync`
- **FormID block:** none

## What it does

The player's mouth plays the voice line's real `.lip` track while DBVO speaks it.
Cinematic Conversation Camera's (CCC, `SceneDirector.dll` 1.5.0) Lip Sync Fallback is turned off.

## Why

Two facts from CCC's own diagnostics in `SceneDirector.log` (2026-10-17) **[verified]**:

1. **Nothing reaches the player's mouth from DBVO 2.0.2.2.** During a conversation, before the
   player's first line: `NOTHING wrote the player's viseme track this conversation (0 slots, peak
   0.000)`. Slots light only once CCC logs `LipSync: driving the player's mouth`. DBVO.dll does have
   `[lip] prepared/attached` code, but it does not show on the face here. CCC's `SpeakSound` watch
   never logged a player line, because DBVO does not go through the console command (the string
   `SpeakSound` is absent from `DBVO.dll`).
2. **CCC's fallback guesses.** It builds mouth "positions" from the subtitle's a–z letters, spaces
   them evenly, and uses its own length estimate. "I'm new in the city…" was logged as `67 positions
   over 3.76s`, but the recording decodes to 4.37 s and its `.lip` speech ends at 4.47 s. The mouth
   was running about 15% fast, on shapes that weren't timed to the syllables.

The DLL replaces the fallback, and `SD_user.ini` turns it off. Both together, or two writers fight
over one mouth.

### Trap: CCC's key is in `[Performance]`

`bSynthLipSync` sits under **`[Performance]`** in `SD.ini`, not `[Direction]` (the comment block
above it reads as if it belonged to the camera section). The first build of this patch wrote it
under `[Direction]`, and CCC kept `synthesis ENABLED`. Check the log line `LipSync: synthesis ...`
after any change.

## How the DLL works

- **Line start:** one of the player's two `HighProcessData::soundHandles` starts playing (engine
  `IsPlaying()`) while `MenuTopicManager::menuOpen`. The text is `lastSelectedDialogue->topicText`.
- **File:** `Sound\DBVO\<pack>\<XXH64(text), seed 0, upper hex>.fuz`. All 6 lines from the CCC log
  matched **[verified]**, including Enderal's `>> ` prefix kept verbatim. Every folder under
  `Data/Sound/DBVO` is searched (the two installed packs share no filenames), or only
  `VoicePack=` when it is set. A self-check of two real hashes is logged at startup.
- **Playback:** linear interpolation between 30 fps frames, written to the player's
  `BSFaceGenAnimationData::phenomeKeyFrame` (the channel the `mfg phoneme` console command uses)
  under its lock. Zeroed when the track ends, the handle stops (a skipped line), the menu closes or
  the next line starts.
- **INI** (`ZenDBVOLipSync.ini`): `OffsetMs` (positive = mouth later), `Strength` (%), `FrameRate`
  (raise it if DBVO's dialogue pitch is above 100), `VoicePack`, `Log`.
- **Log:** `My Games\Skyrim Special Edition\SKSE\ZenDBVOLipSync.log` gets one line per player line:
  the frames and file found, or why nothing was played.

**Built clean; not yet verified in game.** Things to check first if it does nothing:

- The log has no line at all when you speak → the player's sound handles never showed DBVO's voice.
  The start trigger needs another source.
- `no ….fuz` → the prompt text differs from what DBVO hashed (DBVO also logs a `raw=` variant).

## The `.lip` format

Reverse-engineered from the pack. `tools/lipdump.py` decodes every one of the 3551 files and asserts
the sizes.

- `.fuz` = `FUZE` | u32 1 | u32 lipSize | lip | xWMA RIFF audio
- `.lip` = u32 1 | u32 decodedSize | u32 13 | body. The body is zero-run compressed: `00 <u16 n>` is
  n zero bytes, and any other byte is a literal.
- The decoded body is u32 frames | i32 (unknown, −12..0) | u32 16 | frames × 33 float32.
  `decodedSize == len(decoded) + 16` in every file.
- Each frame holds 16 phoneme weights in the engine's `BSFaceGenKeyframeMultiple::Phoneme` order
  (Aah BigAah BMP ChJSh DST Eee Eh FV I K N Oh OohQ R Th W), then the 17 modifiers in `Modifier` order
  (blink L/R, brow down/in/up L/R, look ×4, squint L/R, head pitch/roll/yaw). The order is confirmed
  by "Is there any news?", which decodes to Eh/Eee → Th/DST → Eh → Eee+N → N→OohQ → DST.
- Frames run at **30 fps**: frames = 30.56 × audio seconds + 10 across the pack, and speech ends
  within about 0.1 s of the decoded audio length.

## Side finding

`Fix Lip Sync` (Nexus 75951) is a **32-bit Skyrim LE** DLL (PE machine `0x14c`, built against SKSE
1.7.3). `skse64.log`: `couldn't load plugin LipSyncFix.dll (Error 193)`. It does nothing in this list.
