# WheelerSaveFix → `ZenWheelerSaveFix.dll`

**Ships:** one SKSE plugin, MO2 mod `Zenderal - Wheeler Save Fix`. No plugin file, no edits to WHEELER - Refined's
files. Source `src/WheelerSaveFix/`, built with its `build.cmd` (shares the CommonLibSSE-NG clone in `lib/`).

## Problem (2026-10-30)

Several players: WHEELER - Refined's wheels are empty again after restarting the game, and after a death reload
(BW: "Reset Wheel" every time). The curator saw it too. During play the wheels keep working; only the save is
empty, so it shows at the next load.

## Cause

Wheeler stores its wheels per save in the SKSE co-save (plugin `WHLR`, record `WJSN` version 2: an 8-byte length
then a JSON string). The curator's co-saves:

| Saves | `WJSN` record |
|---|---|
| Save23–Save40 (2026-10-29 22:36 → 10-30 00:08) and their autosaves | **0 bytes** |
| Save41–Save50 (00:25 → 00:53, after rebuilding the wheel) | 371–725 bytes, complete JSON |

Loading a 0-byte record logs `Load: failed to read record data, clearing wheel state`, and the wheels are gone.
Loading Save50 after a restart restored the wheel (`Deserializing parsed data: wheels=1`), so loading works and
the bad records are written at save time.

`SerializationEntry::Save` (wheeler.dll 1.3.4, PE timestamp `6AB24A10`, around `+0x1236C2`):

1. Opens the record (`OpenRecord('WJSN', 2)`, `+0x123736`).
2. Builds the JSON (`Wheeler::SerializeIntoJsonObj`). Every item carries its display name as `missingName`.
3. Calls `basic_json::dump(-1, ' ', false, error_handler_t::strict)` (`+0x1238BD`; the last two arguments are the
   stores at `+0x1238A3`: `mov [rsp+28h], ebx` with ebx = 0 = strict, and `mov byte [rsp+20h], 0`).
4. Only then logs `Serializing record: wheels=N` and writes the length and the string.

Enderal's English strings files are Windows-1252, not UTF-8 (`skyrim_english.strings`: `Kil\xE9an Falcata`,
`Summon Oorb\xE2ya`; ~35,000 high bytes across it and FS's file, including curly quotes and dashes). EGO's
own names are the same (`Kil\xE9an Falcata` in `Enderal SE - Gameplay Overhaul.esp`). Only **weapons and armour**
carry a real name: spells and shouts are saved as `"Unknown"`. So one weapon or armour piece with such a
character on a wheel (Kiléan Falcata/Sarrass, the Rhalâta/Rhalâim armour, Uunil'Yâr's Promise, a player-named
enchanted item) is enough: `dump` throws `type_error 316` ("invalid
UTF-8 byte"). The throw is swallowed, so the game doesn't crash, but the open record stays empty. Every later
save is empty until the item leaves the wheel, and the next load clears everything.

## Fix

At `kPostLoad`, if `wheeler.dll` is loaded, has timestamp `6AB24A10` and holds the 9 original bytes at `+0x1238A3`,
those bytes become a jump to a small stub. The stub sets `error_handler_t::replace` (1) and `ensure_ascii = false`
as before, then jumps back. A bad byte in a saved name becomes U+FFFD and everything else is written unchanged.
The name only matters for an item that has gone missing. The stub sits in a trampoline allocated within 2 GB of
`wheeler.dll`.

Any other Wheeler build is logged in `ZenWheelerSaveFix.log` and left alone.

Saves already written with a 0-byte record can't be recovered: those wheels have to be set up again once.

Upstream fix: pass `error_handler_t::replace` (or convert names to UTF-8) in `SerializationEntry::Save`. Report it
to WHEELER - Refined's author. Retire this plugin when a build does.

**1.0.1 (2026-10-30):** 1.0.0 put the stub in CommonLib's `Trampoline::create(size, module)`. That memory landed
2.8 GB from `wheeler.dll` (`7FF9F12D0000`), so the truncated rel32 jump crashed the first save ("Serializing wheel
into save..." was the last Wheeler line). 1.0.1 commits its own page by walking `VirtualQuery` out from the site in
64 KB steps. It refuses to patch unless both jumps fit in rel32.

## Rerun

Rebuild for a new WHEELER - Refined build: find the dump call in `SerializationEntry::Save` again (the string
`Serializing record: wheels=` is logged right after it). Update `kTimeDateStamp`, `kSite` and `kOriginal`.

## Status

Built and deployed 2026-10-30. **Verified in game 2026-10-30** (1.0.1), on the curator's character with Kiléan
Falcata on a wheel (find its ID with `help falcata 4`; it is not `036A1C` in game):

| Save | Fix | `WJSN` record |
|---|---|---|
| Save54 | off | 0 bytes; log stops at "Serializing wheel into save..." |
| Save53 | on | 855 bytes, `"missingName":"Kil�an Falcata"` (the bad byte replaced) |

The curator's lost wheels (Save22 full at 22:31, every save from Autosave00 at 22:35 empty) fit this: the wheels
stayed in memory for the rest of that session and were gone at the next load.
