# Third-party mod gotchas

List-wide traps that are not tied to one Zenderal patch.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **TK Dodge under Pandora: install TK Dodge RE's "TK dodge standalone" (`tkds`) FOMOD options, or
  every third-person dodge plays on the spot.** **[verified in game 2026-10-08]** TK Dodge RE's
  "Main files" option installs only the `tkuc` (Ultimate Combat) engine patch, which has no
  `animationdatasinglefile` part. Nemesis used to supply that data from its own bundled `tkuc`;
  Pandora 5.0.0-beta does not (its bundled `tkds` is first-person only and has no `info.ini`, so it
  is never applied), so the step-dodge clips had no motion data and the character shuddered in
  place. Fix: reinstall TK Dodge RE ticking every "Behavior edits for dodge only" box except the
  non-TDM "Allow dodging when stagger", then in Pandora tick **TK Dodge Standalone** and untick
  **TK Dodge RE / Ultimate Combat**. Pandora's author only supports TK motion via AMR annotations
  (Monitor221hz/Pandora-Behaviour-Engine-Plus#28), so the list also runs *TK Dodge Animation
  Pandora Patch* (AMR-annotated default clips) and *TK First Person Fix for Pandora*. **A FOMOD
  reinstall resets `TK Dodge RE.ini`** (dodge key fell back to Left Alt = Jump), so the list's dodge
  settings (Space 57, step dodge, stamina 5) now live in `Zenderal - Settings`. Diagnostic: grep the
  Pandora output's `animationdatasinglefile.txt` for `^TKDodge` - zero lines means no motion data.
- **Keybinds: the list default and the curator's personal layout are two MO2 mods.**
  `Zenderal - Settings` carries the default (`Root/ControlMap_Custom.txt`, Dual Wield Parrying's and
  Wheeler's configs); the optional `Zenderal - Personal Keybinds` overrides it when sorted above it
  and must be disabled before a Wabbajack compile. `ControlMap_Custom.txt` is BINARY: 3 blocks
  (keyboard, mouse, gamepad), each a 3-byte header then 5-byte entries `u8 event, u32 BIG-ENDIAN
  key`, event = index in the live `controlmap.txt` Main Gameplay list (6 Left Attack, 7 Right
  Attack, 0x15 Favorites). Dual Wield Parrying numbers mouse buttons **+257**, not the CK's +256
  (right click 258, Mouse 5 261).

- **A big flat white/grey sheet hanging in a small worldspace is DynDOLOD's TERRAIN UNDERSIDE.** **[verified in-game 2026-10-06]** Ref `MQP03Temple_UNDERSIDE_DynDOLOD_NOLOD` (MSTT `MQP03Temple_UNDERSIDE_DynDOLOD_BASERECORD`, model `meshes/Terrain/MQP03Temple/MQP03Temple_Underside.nif`, both in `DynDOLOD.esp`) was seen floating over the intro beach's rocks. DynDOLOD generates an underside for every worldspace not in `TerrainUndersideIgnoreWorlds` (`Tools/DynDOLOD/Edit Scripts/DynDOLOD/DynDOLOD_SSE.ini`) — this run did `MQP03Temple`, `MQP01Home`, `MQ09Isle`, `MaxKingsPass` and `Vyn` (logs `Tools/DynDOLOD/Logs/LODGen_EnderalSE_*_TerrainUnderside_log.txt`). The `MQP03Temple` one was built from terrain data covering only cells `-2,-3..2,3` of a `-4,-6..6,8` worldspace at `QualityLOD16=10`, i.e. a coarse approximation of the beach terrain, and can sit above real ground in rocky gullies. The underside only exists to hide gaps under DISTANT terrain LOD, which a `SmallWorld` intro area hardly has. Fix at the next DynDOLOD run by adding the small worlds to `TerrainUndersideIgnoreWorlds`; do not patch `DynDOLOD.esp` refs from a plugin — DynDOLOD renumbers them every generation. **Applied 2026-10-06:** `MQP03Temple_Underside.nif` renamed `.mohidden` in `DynDOLOD_Output` (sheet confirmed gone in game), and the four small worlds added to the ignore list (backup `DynDOLOD_SSE.ini.bak-2026-10-06`), so the next DynDOLOD run will not regenerate it.

- **NPCs Use Potions strips every corpse** when re-enabled — see [`patches/NpcPotions.md`](../patches/NpcPotions.md).
