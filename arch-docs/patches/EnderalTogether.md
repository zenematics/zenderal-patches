# EnderalTogether

**Testing, shipped as an opt-in from list 0.9.6 (2026-11-09).** Co-op for Zenderal: Skyrim Together Reborn built from source with the
Enderal changes of Frelm's *Enderal Together* fork, plus Zenderal fixes.

- **Source:** `src/EnderalTogether/patches/0001`–`0012`, applied to tiltedphoques/TiltedEvolution `dev` at `8b2b1b0c`
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
| `0005` | Zenderal | **Engine Fixes was blocked.** The launcher's DLL greylist checks `EngineFixes.toml` with `^`-anchored line patterns (`^bVerboseLogging\s*=` = EF7) searched over the whole file; MSVC's `std::regex` anchors `^` at the file start only, and the toml opens with `# Engine Fixes 7.0 …`, so neither entry matched and `TP_LdrLoadDll` refused `EngineFixes.dll` (`STATUS_INVALID_IMAGE_HASH`). Now `multiline`. Tested with the same compiler on Enderal's toml: EF7 pattern matches, EF6 pattern still does not. **Leave Engine Fixes' memory patches ON** (Ultra's `EngineFixes.toml` as shipped). Skyrim Together expects them: `Games/Memory.cpp` re-hooks its actor-size allocator on top of EF's (`Hook_initterm_e`, `IsFormAllocateReplacedByEF`). On 2026-11-09 they were tested **off** (`Zenderal - Engine Fixes Memory Off (testing)`, all six `[MemoryManager]` overrides false), on the theory that EF's `bReplaceImports` (CRT `malloc`/`free` to TBB) clashes with Skyrim Together's mimalloc IAT hooks on the same imports. With them off the game **hung while cells loaded in all three sessions** (23:03, 23:08 offline, 23:17): `tp_client.log` and the Papyrus log stop in the same second, mid script binding of newly loaded refs, nothing after; the same save had loaded and played twice with them on (22:33, 22:44). **But the same hang came back with them on** (2026-11-10 01:11:12, 22 min into a two-player session, `EngineFixes.log`: all memory patches installed): all logs stop in the same second while the client applies a batch of remote actors' inventories (`Received remote actor` / `Setting inventory for actor` for `Zenderal - Goblins.esp` goblins, Papyrus binding errors on their items), no crash log, no dump. So memory-off is not the cause, at most a trigger that makes it come sooner; the hang is open (`hang_watch.py` in the session scratchpad waits for the window to stop responding and dumps the thread stacks). Of the crashes the theory was meant to explain, the "attribute regen" one is `0011` and the two ranged-aiming ones are `0010`; the favorites-menu null lock (22:40) and the NVIDIA driver crash are single samples. The clash theory is unverified. |

| `0006` | Zenderal | **Crash on an NPC action without a `BGSAction`** (first online session, 2026-11-09, 11 min in, about 4 min after connecting): `HookPerformAction` (`Code/client/Games/Animation.cpp`) read `apAction->action->formID` unconditionally; Crash Logger: `EXCEPTION_ACCESS_VIOLATION` at `0x180711210`, `mov ecx, [rax+0x14]` with `rax = 0`, actor `Ancestral Spirit 1278C8`, caller ID 37348. The address is inside `SkyrimTogether.exe`'s own `.zdata` (the launcher maps the game at `0x140000000`–`0x180101008`, its own code after it, so Crash Logger names no module); resolved with dbghelp + the build's PDB to `Animation.cpp:36`. Actions with no actor or no action now go to the game unsynced; remote actors' actions stay blocked as upstream does. Why the game sends a null action is not known (the exe's code is SteamStub-encrypted on disk). |

| `0007` | Zenderal | **Overlay UI (Angular, `Code/skyrim_ui`).** Font: `'futura-book'` first in `$-font-default` (`env.scss`), declared by an `@font-face` in `index.html` (the build resolves stylesheet `url()`s and would need the file, which is a commercial font and never committed); `tools/01` copies the list's Futura Book BT (MenuFrameworkFutura's `MainFont.ttf`, shipped in Patch Collection) to `UI/assets/futura-book.ttf`. Without it the UI falls back to upstream's Futura Condensed Medium. Latin only: Cyrillic/CJK fall back. Warning: `COMPONENT.CONNECT.INFO.HELGEN` (key kept) now reads *Do NOT connect to any server during the prologue. Wait until you have woken up at Jespar's camp.* (MQ01 ends with MQ02 waking the player at Jespar's camp, see [SkipPrologue](SkipPrologue.md)); the 14 other languages' Helgen lines are removed so transloco falls back to English. Checked in the browser build (`ng build --configuration=browser`, mock game, F2): `document.fonts` reports `futura-book` loaded and used, connect dialog and Settings without overflow. |
| `0008` | Zenderal | **Keys moved off F1-F4** (the list's stance keys): overlay Numpad 7 (was F2; Right Ctrl kept), debug view Numpad 8 (was F3, `DebugService.cpp`), reveal players Numpad 9 (was F4, `MagicService.cpp`). The overlay toggle is two places: `InputService.cpp` `IsToggleKey` (raw-input virtual keys) and `TiltedOnlineApp.cpp` `SetToggleKeys` (DirectInput scan codes). Numpad 7 only **opens**: while the overlay is open the numpad types (server addresses contain 7s), so Right Ctrl and Esc close it, and Numpad 8/9 only act while it is closed. F3/F4 were `GetAsyncKeyState` polls, which miss numpad 8/9 with Num Lock off; they are now flags set in `ProcessKeyboard` after its numpad mapping (non-E0 Home/Up/PgUp -> VK_NUMPAD7/8/9), so every key works with Num Lock on or off. No list mod binds numpad 7/8/9 (control maps and hotkey ini/json/toml checked). Builds; unverified in game. |
| `0009` | Zenderal | **Crash on a queued spell cast** (two-player session 2026-11-09, 18:12:59 by `tp_client.log`, 12 min in, in the first update after a batch of actors loaded): `HookSpellCast` (`ActorMagicCaster.cpp`) queued a `SpellCastEvent` holding the raw `ActorMagicCaster*`, read by `MagicService::OnSpellCastEvent` on the next `World::Update` (`TaskQueue::Drain` from `HookVMUpdate`). The caster had been freed and reused by then: Crash Logger `mov rax, [rcx]` at `0x180696BFB` (`MagicService.cpp:65`, the `pCasterActor->GetNiNode()` check), `rax` = the caster, its `pCasterActor` (`+0xB8`) = `0x3E924C40`. The event now carries the caster's form ID, casting source and dual-cast flag, read at cast time, and the actor is looked up again by form ID. Upstream bug: still in `dev` `8b2b1b0c`, no issue or PR found. Builds (rebuilt function checked in the disassembly); deployed as the exe alone (backup `E:/Zenderal-backups/2026-11-09-coop-0009/`). First session on it: 19:29–20:30 with a second player connected most of the time, no crash on this side (one session, not proof). |
| `0010` | Zenderal | **Crash when a ranged combat context ends** (same evening, 19:05:51 and 19:18:46, both Fog Wood, both archers): a null call in the game's `CombatProjectileAimController` destructor (`SkyrimSE.exe+080D627`, ID 44403), releasing its counted node at `+0xA8`, whose memory had been freed and reused. That node comes from ID 37586, called only by ID 33135 (builds the controller for `CombatBehaviorContextRanged`): it returns the AI process's cached weapon bone, a **raw, uncounted** `NiNode*` at `middleProcess + 0x150` (CommonLibSSE-NG `MiddleHighProcessData::weaponBone`; get ID 39825, set ID 39826, only called from 37585/37586), and looks the node up in the actor's 3D (ID 39828 bow, 39834 crossbow) only when the cache is empty. The game clears it only in ID 39811 (beside `GetCurrentWeapon`) and ID 31510 (restores `+0x140`–`+0x150` together), so a launch node freed any other way stays cached. The controller's own refresh (slot `0x0A`, ID 44394) looks up by name and is safe. Hook on 37586 (`Code/client/Games/Skyrim/Combat/WeaponBoneCache.cpp`): clear the cache, call the game's function, so the node always comes from the current 3D; logs `Weapon bone cache of actor … was stale` when the cached pointer differed, which is the test of this explanation. Not covered: the other readers of the raw cache (virtual 37585, launch-point code 38639), and the bow lookup's fallback to the equally raw `+0x148` when the actor has no biped. Builds; deployed as the exe alone after the 0009 session (backup of the 0009 exe `E:/Zenderal-backups/2026-11-09-coop-0010/`); unverified in game. |
| `0011` | Zenderal | **Crash in a cell's water-height check** (`SkyrimSE.exe+02BEE00`, `movzx edx, word ptr [rcx+0x40]`, `rcx = 0x7FFFFFFFFFFFFFFC`; the curator 2026-11-09 22:52 and another player's PC the same day, identical registers, the player in an exterior, under TDM's rotation update; Crash Logger names it `19000+0xB0`, but `0x1402BEE00` is its own function after `int3` padding). Upstream hooks ID 37448 as `RegenAttributes(Actor*, int aId, float aValue)`; 37448 is **`Actor::GetSubmergedLevel(float aZ, TESObjectCELL* apCell)`** (CommonLibSSE-NG `RelocationID(36452, 37448)`). Its code, read from the 22:52 dump: keeps `r8` (the cell) and `xmm1` (a float), compares the cell with `parentCell` (`+0x60`) and calls `0x1402BEE00`, the cell's water-height check (flags `+0x40`, water height `+0x78`). The hook passes the call straight on unless `edx` happens to be 24 (`kHealth`; `rdx = 0x18` in both logs); then its `GetExtension`/`HealthChangeEvent` calls overwrite `r8` and `xmm1`, and the game reads a garbage cell. Both stacks carry the hook's return addresses (`Actor.cpp:1053`, `:268`). The hook is no longer installed (the function is left in the source); health still syncs through the damage/effect hooks and `ActorValueService`'s periodic broadcast, and the "regen" events it sent carried garbage. Upstream bug since the 2022 move to Address Library IDs (`6b2afebc`), still in `dev` `8b2b1b0c`. Builds; deployed as the exe alone 2026-11-09 23:33 (md5 `aa6dfc27…`, backup of the 0010 exe `E:/Zenderal-backups/2026-11-09-coop-0011/`); unverified in game. Only protects the player whose exe has it. |
| `0012` | Zenderal | **A deleted temporary actor is removed for every player** (the host of a four-player session, 2026-11-10: the Fog Wood's corpses stayed, and 89 of them came back as `CharacterSpawnRequest ... dead: true` within seven seconds when the host re-entered the wood; postmortem in [FogWood.md](FogWood.md#postmortem-the-bodies-that-came-back-co-op-2026-11-10)). The client's `OnActorRemoved` runs for every actor that leaves the game, unloaded or deleted alike (`DiscoveryService::VisitForms` drops a form once it is out of the high-process list or has no 3D, so a script's `Disable()` is enough), and `CancelServerAssignment` released an owned one with `RequestOwnershipTransfer{Relinquish}`; the server's `OnOwnershipTransferRequest` then hands it to the next player in range (`TransferToNextOwner`) and removes it only when nobody can take it (a player summon was the one case removed at once). New `OwnershipReleaseReason::Deleted`, appended (a `uint8_t` on the wire, `SerializeRaw`/`DeserializeRaw` copy the byte, nothing range-checks it). **Client:** an owned temporary (`formID >= 0xFF000000`) that is `IsDeleted()` or `IsDisabled()` when the removal scan drops it (the form is still readable there; the arena's `Doom` disables first and deletes a tick later, and the scan fires on the disable) sends `Deleted` and logs `Deleted temporary actor, server id`; an unloaded actor still relinquishes with its cell and position. A temporary deleted while its assignment is still in flight is cancelled as before, now with a `Deleted` flag on `WaitingForAssignmentComponent` (decided at cancel time, the actor is gone when the answer comes): if the answer makes us the owner, `OnAssignCharacter` sends `Deleted` instead of `DeclineGrant`, which would also have handed it on. **Server:** `Deleted` from the current owner (same owner/epoch check) for a temporary (no `FormIdComponent`, not a player) triggers `CharacterRemoveEvent` like the summon case and logs `Removing temporary actor … deleted by its owner` at info (`Character destroyed` is debug, below `STServer.ini`'s level); `OnCharacterRemoveEvent` sends `NotifyRemoveCharacter` to every player, and their `OnRemoveCharacter` already deletes a temporary they do not own (`Deleted actor <FF id>` in their `tp_client.log`; the deleter's entity is already gone, so it ignores the notice). A non-temporary (a plugin-placed actor a quest disabled or deleted) is handed on as before, said in a comment: the clients only `SetRemote(false)` on removal and keep the actor, so removing it would just unsync it. Not covered: a temporary that was handed to another player *before* its deleter deleted it (it had left the deleter's loaded area) stays with that player until they release it; the arena's `SweepCorpses` deletes it once it is local again. Client **and server** change: every player needs the new exe, the host the new server. Builds (`build.cmd`'s C++ build and `xmake install` passed, clone commit `710103ab`; its trailing UI step failed with `'npx' is not recognized`, see Rebuild; the UI is untouched by this patch, so the shipped `dist/UI` stands). The 12-patch series was re-exported and `git am`-tested onto `8b2b1b0c` (same tree hash as the clone). Deployed 2026-11-10 18:17 with the game closed, as the three changed binaries copied into the MO2 mod: `SkyrimTogether.exe` (md5 `634a9977…`), `SkyrimTogetherServer.exe` (`8b6a9721…`), `STServer.dll` (`7db457b3…`); the 0011 copies are in `E:/Zenderal-backups/2026-11-10-coop-0012/`. **Unverified in game**: this machine has one client. The check, with two clients connected: when the arena clears a wave, the host's `tp_client.log` shows `Deleted temporary actor, server id: …` lines, the server console/log `Removing temporary actor … deleted by its owner …` for the same ids, the other client's `tp_client.log` `Deleted actor FF……` for them, and no `CharacterSpawnRequest ... dead: true` burst when the host re-enters the Fog Wood. |

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
   10 newest saves). Engine Fixes stays as Ultra has it, memory patches on: **leave
   `Zenderal - Engine Fixes Memory Off (testing)` unticked** (with it the game hung while loading 3 of 3 times; the
   same hang also happens with it unticked, less often, see `0005`). It is a testing mod with a Wabbajack Ignore rule
   and does not ship.
2. Host: run `mods\Zenderal - Enderal Together (testing)\SkyrimTogetherReborn\SkyrimTogetherServer.exe` (outside
   MO2 is fine). Internet play: forward **UDP 10578**, or use a virtual LAN.
3. Each player: MO2 executable **Enderal Together (co-op test)** (`SkyrimTogether.exe --exePath "E:\Zenderal\Stock
   game\SkyrimSE.exe"`), load a save, wait a few seconds, **Numpad 7** or **Right Ctrl** for the overlay (upstream's
   F2; patch `0008`), Connect. Esc or Right Ctrl closes it; Numpad 8 = debug view, Numpad 9 = reveal players.
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
**The UI step can fail after a good C++ build** (2026-11-10, patch `0012`: `build.cmd` run as `cmd //c` from a Git Bash
session built and installed everything, then ended with `'npx' is not recognized`, although `C:\Program Files\nodejs` is
on that shell's PATH; cause not isolated). `xmake install` has already run by then, so the binaries are good; if the UI
changed, run the two `pnpm` commands in `Code\skyrim_ui` from a shell where `npx` resolves.

## Open

- **First session, 2026-11-09:** the launcher, overlay (F2) and a local server connection work in game
  (`New player 'Lionel' connected with 469 mods`); it crashed about 4 minutes after connecting (patch `0006`).
  **Second session, same day, with `0006` and `0007`:** connected 15:17–15:30 (13 minutes), ended without a crash
  log. The server logged one `Entity is invalid` / `OnHealthChangeBroadcast: SendToPlayersInRange failed` (a health
  update for an actor no longer known to it). Only one player so far.
  **Two-player sessions, evening of 2026-11-09** (four crashes; times from `tp_client.log`, Crash Logger's are ~12 s
  later): 18:12:59 the queued spell cast (patch `0009`). 18:54:27 inside the NVIDIA driver's own worker thread
  (`nvwgf2umx.dll+02F49CC`, null write, driver 617.42, no reset in Windows' event log), in the same millisecond the
  client finished spawning the other player's character (its 13th respawn since 18:29); one sample, and a solo player
  had a driver-thread crash too (11-07). 19:05:51 and 19:18:46, both in **Fog Wood**: a null call in the game's
  `CombatProjectileAimController` destructor (`SkyrimSE.exe+080D627`, ID 44403): the bow AI's counted reference at
  `+0xA8` is a node of the archer's own 3D (set by its slot-0x0A method: the actor's 3D, node by the name at `+0xC8`)
  and that node had already been freed. Archers: a Vagrant owned by this client whose ammo the AI kept swapping
  (15 bolts / 17 arrows every 4-9 s), and a Goblin Archer owned by the other player (inventory applied 61 s before).
  Never seen in a solo log. With quest sync off (`0001`) each player's arena is its own quest, so both games spawn,
  strip and delete their own waves while showing the other's as copies. Explained by a stale raw weapon-bone cache
  and fixed in `0010` (see the table); a `was stale` line in `tp_client.log` would confirm it.
- **`TPProcess.exe` (the overlay's browser worker) can outlive a crashed game** and keeps the mod's `chrome_elf.dll`
  locked, so `tools/01` cannot replace the mod folder (it had already deleted part of it). End it in Task Manager
  before repackaging.
- **Resolving a crash address** in Skyrim Together's code: everything from `0x180000000` up in a Crash Logger log
  with no module is `SkyrimTogether.exe` (`.zdata`); load the build's `SkyrimTogether.exe` at `0x140000000` with its
  real `SizeOfImage` in dbghelp (`SymLoadModuleExW`, not deferred) and look up the line.
- **UI skins must give every SVG a `width`/`height`.** The windows are drawn with CSS `border-image` (`fancy.svg` 26,
  `strip.svg` 7 39, `simple.svg` 5, `single.svg` 3), whose slices are measured against the image's intrinsic size.
  *Vel'dun Skyrim Together Reborn* (2026-11-09) ships Illustrator SVGs with only a `viewBox`: the corner notches
  then scale with each window and cover its text (Settings, chat), in game and in a plain browser alike. Fixed by
  adding `width`/`height` = the `viewBox` size (`scratchpad fix_skin.py` logic; installed locally as MO2 mod
  `Vel'dun Skyrim Together Reborn (fixed)`, above the co-op mod in `Ultra - Co-op (testing)`, ticked there only).
  Ships from 0.9.8 through Wabbajack **Include** + **AlwaysEnabled** (curator's call, 2026-11-10; was Ignore). The
  mod has no source archive, so the compile inlines its files; when rebuilding the co-op profile from Ultra, tick it. The overlay reads its UI and cursor through `Data\SkyrimTogetherReborn`
  (MO2's VFS), so an override mod works and survives `tools/01`. Debug UI changes with the browser build:
  `ng build --configuration=browser`, serve it, F2 in the mock opens the overlay.
- **Upstream's mod caveats:** SmoothCam (tracker `tiltedphoques/Mod-Compatibility` #10: 2022 save-load "Fatal Error",
  never explained; SmoothCam's own crash handler is off in our `SmoothCam.json`), Wheeler (#186: crashes were EF's
  memory manager off, which `0005` no longer forces; WHEELER - Refined reported fine), KiLoader (explicitly supported,
  `PathRerouting.cpp`).
- **Animation sync for the list's graph:** `SkyrimTogetherRebornBehaviors/humanoid_Master/` lists variables for
  MCO, TDM, TK Dodge RE, SCAR and others; Zenderal's Pandora graph adds its own (`fZenPistol*` …) that no list covers.
- **Script-spawned content** (Fog Wood waves, Enemy Density respawns) likely runs on each player's game with quest
  sync off; unverified.
- **MO2 executable 14** points into this mod, which ships since 0.9.6, so the path is valid for players.
- **Deleted temporaries came back as dead spawns** (four-player session 2026-11-10, host's logs): a script's `Delete()` of an owned FF actor was released as `Relinquish` and handed to the next player in range, so the Fog Wood's wave corpses lived on with the other players and the server sent 89 of them back within seven seconds when the host re-entered the wood. Postmortem, with the Papyrus side (local sweep each wave, EP storm):
  [FogWood.md](FogWood.md#postmortem-the-bodies-that-came-back-co-op-2026-11-10). Patch `0012` (table above) makes the server remove such a character for everyone; **unverified with two clients**, the three log lines to look for are in its row.
