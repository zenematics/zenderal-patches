# DBVOSexDefaults

- **Source:** `src/DBVOSexDefaults/` (C++ in `src/`, build with `build.cmd`)
- **Ships:** **no plugin**: `SKSE/Plugins/ZenDBVOSexDefaults.dll` + `SKSE/Plugins/ZenDBVOSexDefaults/male.json` /
  `female.json`. The list also carries a `SKSE/Plugins/DBVO2/default_options.json` in `Zenderal - Settings`
  (see "Where the writes land"). MO2 mod `Zenderal - DBVO Sex Defaults`
- **FormID block:** none

## What it does

A new character starts with the DBVO voice settings for their sex. Male: the curator's "Gary" settings
(Enderal Final Voice Pack, volume 224, reverb 21, pitch 100). Female: the curator's "Gunslinger"
settings retuned on "Mer" (2026-10-18 18:08, `Save1`): legacy DBVO 1.0 Ciri pack `FearTcbCiri`,
volume 178, reverb 32, pitch 90, NPC response delay 1000 ms, resolve alias dialogue on. To change a profile, edit its JSON. It uses the same keys as DBVO's own
`default_options.json`.

## Why a plugin

DBVO 2.0.2.2 has one `default_options.json` for every new game and no idea of the player's sex. In
Enderal the sex is chosen in the RaceSex menu long after the new game has started, by which time
DBVO has already loaded its defaults. **[verified by disassembly, 2026-10-18]**

## How DBVO stores settings (DBVO.dll 2.0.2.2, TimeDateStamp `0x6AB06DCE`)

- `0x6FB0` registers co-save callbacks for uid `DBVO`: save `0x8830`, load `0x80F0`, revert `0x6FF0`.
- **Revert** (every new game and before every load) calls `0x2AC20` (open `default_options.json` and
  parse it into the live settings via `0x2BAD0`), then `0x2AEF0` (read only `always_use_default_options`).
- **Load** applies the save's `STNG` record. It then re-reads `default_options.json` if the record's
  or the file's `always_use_default_options` is set, in which case the file overrides the save.
- `0x2AC20` and `0x2AEF0` take no arguments.
- `STNG` record v10 layout, confirmed by parsing six real records to the exact byte: `u8 use_legacy_voice_over,
  u8 use_localized_mappings, str legacy_pack, str locale, u32 dialogue_volume, u32 dialogue_reverb,
  u8 hide_dialogue_tree, u8 (internal, 0x161C8F), str current_pack, u32 npc_response_delay,
  u8 resolve_alias_dialogue, u8 force_localized, u8 disable_player_subtitles, u8 always_use_default_options,
  u8 (internal, 0x161C94), u32 dialogue_pitch`. `str` = `u32 length + bytes`. The Gary/Gunslinger values
  were decoded from `Save14` (Gary, 2026-10-17 23:30) and `Save16` (Gunslinger, 2026-10-17 22:20).
  Gunslinger's newer autosaves (2026-10-18) hold DBVO's stock values again.

## Mechanism

On `kNewGame`, and again when the RaceSex menu closes on that new game, a main-thread task reads the
player's sex, copies `male.json` or `female.json` over `Data/SKSE/Plugins/DBVO2/default_options.json`
(only if it differs), and calls DBVO's `0x2AC20`. The `kNewGame` step matters because Enderal's
prologue is played before character creation, as the default male player, and DBVO voices it.

**Postmortem (1.0.0 → 1.1.0, 2026-10-18):** 1.0.0 applied a profile only when the RaceSex menu closed.
Each chargen on the curator's machine rewrote the shipped `default_options.json`, and the compile packed
it holding the *female* profile (the last chargen was a female test character). Users' new games then
ran the prologue on the female voice, reported as "male character with female voice". 1.1.0 also
applies at `kNewGame`, so the shipped file's content no longer decides anything.
**Before every compile, check that `Zenderal - Settings/SKSE/Plugins/DBVO2/default_options.json` is
still `male.json`**: every chargen on this machine overwrites it. The new settings are live at once, and the first save
stores them in DBVO's own record. Any save load disarms the plugin, so later RaceSex visits (e.g.
`showracemenu`) and every existing save are left alone. Player changes in DBVO's menu persist as normal.
`always_use_default_options` stays `false` in both profiles. Setting it would make the file override
every save.

The call is pinned: `DBVO.dll` must have TimeDateStamp `0x6AB06DCE` and the 18 prologue bytes at
`+0x2AC20` must match. On any other build the file is still written, so the *next* new game picks it
up through revert, but nothing is called and the log says so. **Re-check both values after every
DBVO update.**

## Where the writes land

Under MO2 the write goes to whichever mod's `default_options.json` wins. DBVO's own copy belongs to the
Nexus download, and changing it would break the Wabbajack match. So `Zenderal - Settings` (No Match
Include, MO2 row 44, above `Dragonborn Voice Over 2` at row 50) carries a copy that takes the writes.

## Limits

- Saves made with no DBVO record (before DBVO 2 was installed) get whatever profile was written last,
  through revert. Every save made since then has its own record.
- ~~A player who will pick female hears the male profile during the prologue.~~ Since 1.2.0 the
  prologue is silent instead (below).

## 1.2.0: silent until character creation (2026-10-27)

Curator's request: no player voice before the character exists. `kNewGame` now applies `silent.json`
(`male.json` with `dialogue_volume` 0, generated from it — keep the two identical apart from that line)
instead of the male profile, and the RaceSex menu closing applies male or female as before. Volume 0
rather than an empty pack: DBVO keeps running exactly as configured, only inaudible, and the subtitles stay.
A save made before character creation stores the silent settings; on load the plugin is disarmed, so the
RaceSex close also switches when `default_options.json` still holds `silent.json` (the voice was never
switched on). The shipped `default_options.json` stays `male.json`: if the plugin ever fails, players get
the old male default, never a voice stuck at 0. Both copies (Patch Collection, which loads, and the
disabled standalone mod) replaced; backup `E:/Zenderal-backups/2026-10-27-dbvo-silent-prologue/`.
**Unverified in game:** a new game should log `DBVO reloaded its defaults: silent profile is live`, then
`male`/`female profile is live` when the RaceSex menu closes.

**Status:** 1.0.0 worked for a female chargen (curator, 2026-10-18). **1.1.0 (new-game apply) is
unverified in game.** On a new game the log should show `new game: player is male` and
`DBVO reloaded its defaults: male profile is live`. To check, look in `ZenDBVOSexDefaults.log` (`My Games/Skyrim Special
Edition/SKSE/`) for `DBVO reloaded its defaults: female profile is live` after a female chargen.
