# ShatterveilAE

- **Source:** `src/ShatterveilAE/tools/01-patch-dll.py` (a byte patch + a converter; no source of Shatterveil exists)
- **Ships:** MO2 mod *Shatterveil - 1.7.104 Patch (Zenderal)*, directly **above** *Shatterveil* in the left pane:
  `SKSE/Plugins/Shatterveil.dll` (patched copy) + `SKSE/Plugins/versionsvl-1-7-104-0.bin` (generated, not committed)
- **FormID block:** _(none)_

## Why (2026-10-28)

Shatterveil 1.3.1 (Wollecss, Nexus 193420, closed source; page: "1.5.97, AE 1.6 untested") stopped the game at load
on 1.7.104 with `REL/Relocation.h(1104): failed to open address library file`. Prophecy's Sorcery tree uses it.

Its CommonLibSSE-NG picks the runtime from the game version's minor number (disassembly at `0x180030911`:
`cmp ax, 4` → VR; `cmp ax, 6; setne al; inc al` → AE = 1, else SE = 2). 1.**7**.104 counts as SE, so it opens
`version-1-7-104-0.bin`, which does not exist. As AE it would open `versionlib-1-7-104-0.bin`, but that file is
**format 5** (dense `uint32` offsets after a 96-byte header) and this NG reads only formats 1/2.

## The patch

1. `66 83 F8 06` → `66 83 F8 07` (file `0x2FD11`): 1.7 is AE. This copy no longer runs on 1.6.
2. `Data/SKSE/Plugins/versionlib-{}.bin` → `versionsvl-{}.bin` (same length, file `0x137208`): it reads only its own
   converted library, never the real one.
3. `versionsvl-1-7-104-0.bin`: the format-5 library re-encoded as format 2 (header: format, version, name, pointer
   size, count; every entry type byte `0x77` = `u32` id + `u32` offset), 435,162 ids. Checked by decoding it back and
   against Casting Bar AE's verified `14220 → 0x1D74A0`.

4. **The logger's game-folder lookup.** With 1–3 the DLL loaded, but SKSE disabled it: "fatal error occurred while
   loading plugin", no `Shatterveil.log`. [`ZenExceptionTrace`](ZenExceptionTrace.md) caught a null read at
   `Shatterveil.dll+0x11793D` inside `SKSEPlugin_Load`. The old NG's `log_directory()` reads the "My Games" folder name
   through `RELOCATION_ID(508778, 380738)`, and **1.7.104 has no AE ID 380738** (newer NG builds the path from
   `steam_api64.dll` instead). The 42 bytes from the lookup to the dereference (`0x117916–0x11793F`) are now `lea rax,
   [rip+2]; jmp 0x117940` + `"Skyrim Special Edition\0"`; no jump from outside lands in that range.
   A scan of the DLL's other `RELOCATION_ID` pairs (91, from the stores before its three resolver calls) found every
   other AE ID present in 1.7.104 (the scan's raw output pairs some IDs the wrong way round; checked by hand against
   CommonLibNG: `11141`, `105544`, `400503`, `400508` all resolve). IDs reached another way are not covered.

The NG's shared mapping is `CommonLibSSEOffsets-v2-1-7-104-0`. Our CommonLibNG maps format-5 files directly, so the two
never share it.

Source SHA-256 of the 1.3.1 DLL: `6598a111a5565d8225566be21b398f91125acabc423bda12f0eab4f7e955233a`. The script refuses a
DLL whose switch bytes are not where expected; rerun it (and re-find `CMP_VA`) after a Shatterveil update, or retire
this patch when the author ships a 1.7 build.

**Risk:** it loads, but it was never built against 1.7's layouts. An AE ID that 1.7.104 dropped shows as a fatal
`Failed to find the id within the address library` box; a moved struct field or vtable slot (as TK Dodge's input
handler, see `workspace/enderal-update-migration.md`) shows as a crash or a dead feature. Unverified in game.
Personal-use patch of a closed mod: ask the author before shipping it in the public list.

## In game (2026-10-28)

- **Effigies 3 s late:** every decoy hit the "not fully dressed" fallback. Patch 5 shortens it to 0.4 s (logs now
  ~480 ms). The dressed count still never matches on 1.7.104; the cause is not found.
- **Veil Wyrm slow time:** the probe (`ZenExceptionTrace` 1.1.0) showed Shatterveil's slow-time spell `F26` with
  **0 effects** in game: its effect is vanilla `VoiceSlowTime 048ACD`, which Enderal does not have. Not a DLL bug -
  Prophecy overrides `F26` onto Enderal's `_00E_Game_SlowTimeME 13FB41` (`WYRM_SLOW`). The only other vanilla forms
  Shatterveil names that Enderal lacks are two faction relations of `shvl_DecoyFaction` (`05C84E`, `084D1B`).
- **Veil Wyrm silent (open):** every shout sound record resolves (probe), its files exist (Shatterveil's own `.wav`s;
  the roars in `Skyrim - Sounds.bsa`), and `PlaySoundAt` builds, positions and `Play()`s them at volume 1.0 without
  an error line. Not yet known whether all Shatterveil sounds are silent on 1.7.104 or only the dragon's.
- **Wyrm sounds (still open):** `ZenExceptionTrace` 1.2.0 hooked the 6 call sites of Shatterveil's sound wrapper:
  every wyrm sound (form, roar, resonance, dust, the Thu'um lines) returns `playing (valid=true, positioned=true)` on the
  player at volume 1.0, and is not heard. Workaround: Prophecy gives the shout's word effects a Release sound of
  its own (`0xAE0`). 1.3.0's F9/F10 test keys played the form sound and roar outside a shout, through CommonLib and
  through Shatterveil's wrapper: **both heard** (curator, 2026-10-28). So the records, files and wrapper work; something
  during the shout itself silences them (suspect: the shout camera, `iShoutCamera`). Keys removed again in 1.3.1.
