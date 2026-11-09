# EnderalTogether

**Testing, shipped as an opt-in from list 0.9.6 (2026-11-09).** Co-op for Zenderal: Skyrim Together Reborn built from source with the
Enderal changes of Frelm's *Enderal Together* fork, plus Zenderal fixes.

- **Source:** `src/EnderalTogether/patches/0001`–`0005`, applied to tiltedphoques/TiltedEvolution `dev` at `8b2b1b0c`
  (2026-11-06, GPL-3.0, `LICENSE` copied here). Working clone: the gitignored `lib/rebuilds/TiltedEvolution`, branch
  `zenderal-enderal`. Also `SkyrimTogetherESP/` (the Enderal-safe `SkyrimTogether.esp`), `Scripts/` (four Enderal
  script patches, compiled from source), `build.cmd`, `compile-scripts.cmd`, `tools/01-package-mo2.py`.
- **Ships:** from list 0.9.6 (2026-11-09) the MO2 mod `Zenderal - Enderal Together (testing)` goes into the compile
  (Wabbajack `Include` + `AlwaysEnabled`, ~379 MB inlined into the `.wabbajack`), and so does the profile
  `Ultra - Co-op (testing)` (`AdditionalProfiles`). The mod is ticked only in that profile, which is Ultra's
  modlist/plugins/load order with the mod ticked and `SkyrimTogether.esp` directly before `DynDOLOD.esp`:
  **rebuild it from Ultra before each compile** (it drifted: 2026-11-09 it lacked 3 of Ultra's mods). Started by MO2
  executable *Enderal Together (co-op test)*. Never ship the server's `SkyrimTogetherReborn/logs/`. GPL-3.0: the
  shipped binaries' source is `src/EnderalTogether/` + upstream `8b2b1b0c`, which must be pushed before a release.
  No manifest entry.
- **FormID block:** none (`SkyrimTogether.esp` is upstream's plugin, its own IDs `0x1824`/`0x1825`/`0x1D89`/`0x3DD0`).

## Why from source

The Nexus release (enderalspecialedition 1158, *Enderal Together*, Frelm, 2026-10-31) was **quarantined** by Nexus
and is closed binary. Its source is public (github.com/Frelm/EnderalTogetherReborn, GPL-3.0), but it is built on a
21–22 Oct playtest branch with a 1.5.97 "legacy" base, behind upstream. **Upstream already targets SE 1.7.104** — the
runtime the list runs (`kSupportedGameVersions` in `Code/client/main.cpp`; `AGENTS.md`: "SE 1.7.104 is the main
target") — and its developers test Enderal's MQ01 Finn/Carbos scene (PRs 854, 928). The fork's Enderal work is small,
so it is applied to upstream `dev` here instead.

## The patches

| Patch | From | What |
|---|---|---|
| `0001` | fork `287f6581` | **Null guards** on the two vanilla globals the client toggles: `KillMove 100F19` exists in Enderal, `WorldEncountersEnabled 0B8EC1` does **not** (absent from `reference/base/`); upstream writes through the null `Cast<TESGlobal>` result (`PlayerService.cpp`). **Quest sync off** when `Enderal - Forgotten Stories.esm` is loaded (`bDisableQuestSync`, default true, from `EnderalTogether.ini` beside the exe; none is shipped, so the defaults hold): every quest advances per player. If sync is ever turned on, `_00E_Player*`/`Level*`/`Perk*`/`Meditation*`/`Skill*`/`Stat*`/`Sys*`/`FS_Player*`/`Weather*`/`GamePlay*`/`Intro*` quests stay local (`bBlacklistSystemQuests`). |
| `0002` | fork `d97f2941`, re-done for upstream | The launcher remembers the chosen exe under `HKCU\Software\TiltedPhoques\TiltedEvolution\Enderal Special Edition` (`TILTED_REGISTRY_NAME`), not Skyrim SE's key. `--exePath` writes that key; the Bethesda key only seeds the file dialog. |
| `0003` | fork `534b7d2a` | Four Enderal scripts with remote-player guards (2.1.4 sources + guards only, diffed): temple column puzzle, dungeon lifts, MQP03 exit door, class menu (only the caster enters the meditation temple). |
| `0004` | Zenderal | `MemoryLayout.cpp`: drops `constinit` on a `reinterpret_cast`, which MSVC 14.51 (VS 2026) rejects (VS 2022, upstream CI, accepted it). |
| `0005` | Zenderal | **Engine Fixes was blocked.** The launcher's DLL greylist checks `EngineFixes.toml` with `^`-anchored line patterns (`^bVerboseLogging\s*=` = EF7) searched over the whole file; MSVC's `std::regex` anchors `^` at the file start only, and the toml opens with `# Engine Fixes 7.0 …`, so neither entry matched and `TP_LdrLoadDll` refused `EngineFixes.dll` (`STATUS_INVALID_IMAGE_HASH`). Now `multiline`. Tested with the same compiler on Enderal's toml: EF7 pattern matches, EF6 pattern still does not. Upstream's EF7 entry needs **no config changes** (memory manager may stay on); the fork's "all six `[MemoryManager]` overrides off" comes from its 1.5.97/EF6 base. |

| `0006` | Zenderal | **Crash on an NPC action without a `BGSAction`** (first online session, 2026-11-09, 11 min in, about 4 min after connecting): `HookPerformAction` (`Code/client/Games/Animation.cpp`) read `apAction->action->formID` unconditionally; Crash Logger: `EXCEPTION_ACCESS_VIOLATION` at `0x180711210`, `mov ecx, [rax+0x14]` with `rax = 0`, actor `Ancestral Spirit 1278C8`, caller ID 37348. The address is inside `SkyrimTogether.exe`'s own `.zdata` (the launcher maps the game at `0x140000000`–`0x180101008`, its own code after it, so Crash Logger names no module); resolved with dbghelp + the build's PDB to `Animation.cpp:36`. Actions with no actor or no action now go to the game unsynced; remote actors' actions stay blocked as upstream does. Why the game sends a null action is not known (the exe's code is SteamStub-encrypted on disk). |

| `0007` | Zenderal | **Overlay UI (Angular, `Code/skyrim_ui`).** Font: `'futura-book'` first in `$-font-default` (`env.scss`), declared by an `@font-face` in `index.html` (the build resolves stylesheet `url()`s and would need the file, which is a commercial font and never committed); `tools/01` copies the list's Futura Book BT (MenuFrameworkFutura's `MainFont.ttf`, shipped in Patch Collection) to `UI/assets/futura-book.ttf`. Without it the UI falls back to upstream's Futura Condensed Medium. Latin only: Cyrillic/CJK fall back. Warning: `COMPONENT.CONNECT.INFO.HELGEN` (key kept) now reads *Do NOT connect to any server during the prologue. Wait until you have woken up at Jespar's camp.* (MQ01 ends with MQ02 waking the player at Jespar's camp, see [SkipPrologue](SkipPrologue.md)); the 14 other languages' Helgen lines are removed so transloco falls back to English. Checked in the browser build (`ng build --configuration=browser`, mock game, F2): `document.fonts` reports `futura-book` loaded and used, connect dialog and Settings without overflow. |

## Zenderal changes outside the patches

- **`SkyrimTogether.esp` without its vanilla overrides** (`SkyrimTogetherESP/`, upstream's four own records
  byte-identical, same header: full plugin, HEDR 1.71, masters `Skyrim.esm` + `Update.esm`). Upstream also overrides
  `03AE9F`/`03AEA2`/`03AEA3` ("Sync visuals of destruction cloak spells", `6671336b`): in Enderal those IDs are
  `_50E_SpellFireCloak` (Fire Cloak Rank II), `_50E_SpellWinterSkin`, `_05E_SpellLightningCowl`, also overridden by
  EGO; upstream's record would put vanilla Flame Cloak (effect `03AE9E`, magnitude 10, no conditions) over them. `T03`
  (`01C48E`) and `MagicOrBowCams` (`000926:Update.esm`) do not exist in Enderal and would be injected. The client only
  looks up `0x1825`/`0x1824` via `ModManager::GetByName("SkyrimTogether.esp")->standardId << 24` (`MagicService.cpp`),
  so **it must stay a full plugin** (133 full plugins in Ultra, room left).
- **`SkyrimTogetherQuestPatches.esp` left out**: its only record is `C02InductionScene 07165F` (College of Winterhold),
  absent in Enderal.
- **`meshes/Interface/logo` left out**: it would replace the main-menu logo.
- **Class-menu script merged** with *Meditation Area v2.1.0 3rd Person POV Unlock* (Nexus 683, f1.01), which also
  replaces `_00e_class_openclassmenuscript.pex`: its source + the fork's 4-line caster guard
  (`Scripts/source/`). The other upstream script overrides are vanilla quests' scripts; the only one Enderal ships,
  `ResourceFurnitureScript`, equals Enderal 2.1.4's apart from upstream's remote-player guard.
- **Steam app ID left at 489830** (Skyrim SE). Decoding Enderal's `SkyrimSE.exe` SteamStub v3.1 header (signature
  `0xC0DEC0DF`) gives AppId **489830**: Enderal's exe is DRM-bound to Skyrim SE's app, so that is the right value.
  Side effect: the launcher writes `steam_appid.txt` (489830) into `Stock game\` on every start. Root Builder (copy
  mode) moved it into `overwrite\Root\` on the first run (2026-11-09), from where it would deploy in **every**
  profile; the mod now ships the same file in its own `Root\` (`tools/01`), so it only deploys with this mod.
- **No sound on the first run: Windows routes by program.** The game runs inside `SkyrimTogether.exe`, which Windows
  had never seen, so it played on the **default** output, *Headphones (Shure MV7+)* (read through
  `IMMDeviceEnumerator::GetDefaultAudioEndpoint`), not the GoXLR output normal launches use. Set
  `SkyrimTogether.exe`'s output once in Windows' volume mixer while it runs; Windows keeps it per program path.

## Using it

1. MO2: profile **`Ultra - Co-op (testing)`** (Ultra + the mod + `SkyrimTogether.esp` at the end of the load order,
   10 newest saves). `Zenderal - Engine Fixes Memory Off (testing)` is listed disabled there: tick it only if the
   game is unstable with Engine Fixes' memory manager on.
2. Host: run `mods\Zenderal - Enderal Together (testing)\SkyrimTogetherReborn\SkyrimTogetherServer.exe` (outside
   MO2 is fine). Internet play: forward **UDP 10578**, or use a virtual LAN.
3. Each player: MO2 executable **Enderal Together (co-op test)** (`SkyrimTogether.exe --exePath "E:\Zenderal\Stock
   game\SkyrimSE.exe"`), load a save, wait a few seconds, **F2** or **Right Ctrl** for the overlay, Connect.
   **Never put a comma in an MO2 executable title**: MO2 stores it with Qt's INI format, which reads an unquoted
   comma as a list, so the first title (`… (co-op, testing)`) came back blank and the game was started with the
   normal SKSE entry instead. Started without the launcher, `SkyrimTogether.esp`'s quest shows *"Skyrim Together is
   not running!"* on the main menu (seen 2026-11-09); the launcher's game runs inside `SkyrimTogether.exe`, never as
   a separate `SkyrimSE.exe` process.
4. Both players need the identical list (Wabbajack gives that) and this mod.

## Rebuild

Toolchain (all under the gitignored `lib/`): `lib/rebuilds/_env.cmd` (VS 2026 Build Tools), **xmake 3.1.0** portable
at `lib/xmake` (official release zip, sha256 `92c32092…bd8bd`), a junction `lib/gitroot` → `D:\Claude & Tools\Git`
(xmake cannot use a git path with `&`), Node.js (pnpm 9 via `npx`). The repo path must have no spaces.

```bash
git clone --recursive --branch dev https://github.com/tiltedphoques/TiltedEvolution.git lib/rebuilds/TiltedEvolution
cd lib/rebuilds/TiltedEvolution && git checkout -b zenderal-enderal 8b2b1b0c && git am ../../../src/EnderalTogether/patches/*.patch
```

Then `src/EnderalTogether/build.cmd` (xmake config + build + install, then the UI), `compile-scripts.cmd`, Spriggit
`deserialize` of `SkyrimTogetherESP/` to any folder, and `python -I src/EnderalTogether/tools/01-package-mo2.py
<that SkyrimTogether.esp>` (replaces the MO2 mod wholesale). Traps met on the first build, all handled in `build.cmd`:
a Git Bash parent makes xmake see an MSYS host (`MSYSTEM`); `NoDefaultCurrentDirectoryInExePath=1` in this shell stops
DirectXTK's package build from running its own `CompileShaders.cmd`; xmake-repo's `directxtk` check needs
`--vs_sdkver=10.0.26100.0`. Packages land in `%LOCALAPPDATA%\.xmake\packages` (CEF 141 included).

## Open

- **First session, 2026-11-09:** the launcher, overlay (F2) and a local server connection work in game
  (`New player 'Lionel' connected with 469 mods`); it crashed about 4 minutes after connecting (patch `0006`, fixed,
  not yet retested). Only one player so far.
- **`TPProcess.exe` (the overlay's browser worker) can outlive a crashed game** and keeps the mod's `chrome_elf.dll`
  locked, so `tools/01` cannot replace the mod folder (it had already deleted part of it). End it in Task Manager
  before repackaging.
- **Resolving a crash address** in Skyrim Together's code: everything from `0x180000000` up in a Crash Logger log
  with no module is `SkyrimTogether.exe` (`.zdata`); load the build's `SkyrimTogether.exe` at `0x140000000` with its
  real `SizeOfImage` in dbghelp (`SymLoadModuleExW`, not deferred) and look up the line.
- **Upstream's mod caveats:** SmoothCam (tracker `tiltedphoques/Mod-Compatibility` #10: 2022 save-load "Fatal Error",
  never explained; SmoothCam's own crash handler is off in our `SmoothCam.json`), Wheeler (#186: crashes were EF's
  memory manager off, which `0005` no longer forces; WHEELER - Refined reported fine), KiLoader (explicitly supported,
  `PathRerouting.cpp`).
- **Animation sync for the list's graph:** `SkyrimTogetherRebornBehaviors/humanoid_Master/` lists variables for
  MCO, TDM, TK Dodge RE, SCAR and others; Zenderal's Pandora graph adds its own (`fZenPistol*` …) that no list covers.
- **Script-spawned content** (Fog Wood waves, Enemy Density respawns) likely runs on each player's game with quest
  sync off; unverified.
- **MO2 executable 14** points into this mod, which ships since 0.9.6, so the path is valid for players.
