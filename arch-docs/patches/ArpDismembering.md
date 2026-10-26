# ArpDismembering

- **Source:** `src/ArpDismembering/` (generated: `tools/01-build-arp-limbs.py` → `tools/arp-limbs.json` →
  `tools/02-build-arp-data.py` → `ArpDismemberingESP/` + `SKSE/DismemberingFramework/`)
- **Ships:** MO2 mod `Zenderal - Arp Dismembering`, containing:
  - `Zenderal - Arp Dismembering.esp` (ESL, HEDR 1.7; masters Skyrim, Update, FS, `Dismembering Framework.esm`,
    `DF - Official Creature Pack.esp`)
  - `SKSE/DismemberingFramework/Zenderal_Arps_LIMBS.json`
  - `SKSE/DismemberingFramework/OfficialCreaturePack_Falmer_DATA.json` (a same-path copy of DF's file)
  - 25 generated limb meshes at `meshes/DismemberingFramework/Zenderal/Arps/` (not committed)
- **FormID block:** `0x800–0x818` (25 limb MiscItems)

## Why

Reported in game 2026-10-26, with a screenshot and a recording: a severed Arp head was a pale, blind Skyrim Falmer
head, while living Arps have dark grey skin, red eyes and green dreadlocks.

- Arps are `FalmerRace`. DF's official Falmer limbs are cut from Skyrim's Falmer bodies.
- The list's `Enderal Arp` mod (`Enderal - Arp.esp`, Nexus 36, v2.12) overrides all seven Falmer body ARMAs with
  Enderal's swamp-race meshes **[verified]**:

  | ARMA | Body |
  |---|---|
  | `NakedFalmerAA` `020E24` | `swamp_hunter.nif` |
  | `NakedFalmerAA01` `050F2F` | `swamp_warrior.nif` |
  | `NakedFalmerAA02` `050F31` | `swamp_warrior_v2.nif` |
  | `NakedFalmerAA03` `050F33` | `swamp_warrior_v3.nif` |
  | `NakedFalmerAA04` `050F35` | `enderal\actors\swamp race\swamp_shaman.nif` |
  | `NakedFalmerAA05` `050F37` | `swamp_hunter.nif` |
  | `NakedFalmerAA06` `050F39` | `swamp_warrior_v4.nif` |

- DF also picks limbs by skin armor and only knew Skyrim's `SkinFalmer01`–`06`. Enderal's Arp skins
  (`_00E_Arp1`–`4`, `_00E_SkinArpShaman`) fell through to its naked fallback.
- Its helmeted head needs Skyrim's helmet item `052381`, which Enderal doesn't have.

A first attempt (the same day, in LostOnesDismembering) only re-pointed the Arp skins at DF's matching Falmer
limbs. That could never match the swamp bodies and has been removed.

## What it does

- **`tools/01`** reads the body models from `Enderal - Arp.esp` itself. It parses the plugin and asserts that
  all seven ARMA overrides are there, and that the mod and plugin are enabled. Each ARMO's ARMA list comes from
  `reference/base/Skyrim`; EGO and FS don't override these records.
- Each skin's meshes are resolved through the Ultra profile's MO2 order. The winners are PG Patcher Output's
  `swamp_hunter`, ETATU - CM Meshes' `swamp_warrior`, `_v2` and `_v4`, and Enderal Arp's `swamp_shaman`.
- The meshes are cut exactly as the Goblins limbs are (shared helpers in
  `src/LostOnesDismembering/tools/limbmesh.py`). Each limb is cut by dominant bone in the Falmer skeleton
  (Creature Collision Fix's copy) and placed in DF's naked male Falmer limb nif.
- That gives 25 meshes: five per distinct body. `_00E_Arp1`, `_00E_Arp3` and the race skin share
  `swamp_hunter`. Heads carry the eyes and hair shapes.
- Skins covered:
  - `_00E_Arp1 0B526C`, `_00E_Arp2 0B526D`, `_00E_Arp3 0B526E`, `_00E_Arp4 0B526F`
  - `_00E_SkinArpShaman 01848C`
  - `SkinFalmer01 050F30` (five Arp NPCs wear it)
  - the race skin `SkinFalmer 016EE7`, which is also DF's `ANY`
- **`tools/02`** copies DF's naked male Falmer limb items (`000844`–`000848`, `DFDefaultLimbRefScript`) as one
  MiscItem per mesh. It writes the LIMBS JSON with DF's Falmer base-data and actor-addon templates, so stump
  caps are still DF's Falmer caps.
- It then rebuilds `FalmerRace` in DF's own DATA file:
  - each skin gets its five limbs, for both sexes;
  - DF's Dawnguard entries are kept;
  - the flesh construct `_00E_SkinFleshconstruct 149709`, also FalmerRace, keeps DF's own limbs.
- **Load order:** the MO2 mod must outrank `DF - Official Creature Asset Pack`, so its DATA copy wins. The plugin
  must load after `DF - Official Creature Pack.esp`.

## Status

Built and deployed 2026-10-26: the meshes and JSON are in the MO2 mod, and the plugin deserialized cleanly.
**Verified in game 2026-10-26:** a severed leg and a severed head look like the Arp (dark skin, red eyes, dreadlocks). One crash happened exactly as an Arp's head was cut (12:44). Its log is
lost: the minidump stalled Crash Logger, leaving a 0-byte log and a dump with no stream directory. A second head
cut (13:4x) did not crash. The head meshes match the working goblin head's structure, and their shaders and
textures are copied unchanged from the live bodies, so nothing points at them. **Watch Arp head cuts for
another crash**, and get its text log. Open questions:

- The stump caps' skin ring is still DF's pale Falmer texture. If that shows, retexture the caps the way the
  Goblins patch does (its `tools/05`).
- The shaman's limbs are cut from shapes named `drum*` and `giant_heavy_cloth*`; check that the pieces look right.

Rerun `tools/01` then `02`, then rebuild the plugin, after Enderal Arp, PG Patcher, ETATU - CM Meshes or DF's
creature pack changes.
