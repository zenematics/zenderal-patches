# BakaHeroMenu

> **RETIRED 2026-10-14.** Removed from the list by the curator, so `src/BakaHeroMenu/` and its
> manifest entry were removed. The source is recoverable from commit `fa07b81` (GPL-3.0: if it is
> ever shipped again, the modified source must be published with it). The CommonLibSSE-NG clone it
> used to hold now lives in the gitignored repo-root `lib/CommonLibNG`, shared by the other native
> DLL patches. Everything below is history.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/BakaHeroMenu/`
- **Ships:** *(no plugin — `SKSE/Plugins/BakaHeroMenu.dll`)*
- **FormID block:** _(none)_

## What it does

**The repo's first native SKSE plugin build.** Port of shad0wshayd3's *Baka Hero Menu* (Nexus enderalspecialedition/1121, GPL-3.0 + modding exception — the modified source in `src/BakaHeroMenu/` must stay published with the DLL; credit the author) from libxse CommonLibSSE (Enderal 2.1.x / 1.6.x+ only) to **CommonLibSSE-NG** (`alandtse/CommonLibVR` `ng` branch, SE-only build) for 2.0.12 / 1.5.97: clicking a skill in the Hero Menu spends a Learning/Crafting Point on it. **Toolchain [verified 2026-10-06]:** nothing to install — VS 2026 Build Tools ships CMake 4.3, Ninja and vcpkg (`…/18/BuildTools/VC/vcpkg`); `src/BakaHeroMenu/build.cmd` wires them up (vswhere's `Installer` dir and git `D:\Claude & Tools\Git\cmd` must be on PATH; `SKSE_SUPPORT_PATCH_SAFETY OFF` avoids a git FetchContent of hde64; `VCPKG_APPLOCAL_DEPS=OFF` because the post-link step calls `powershell.exe`, absent from that PATH). Clone NG into `src/BakaHeroMenu/lib/CommonLibNG` first (gitignored). NG's `SKSEPluginInfo` emits the `SKSEPlugin_Query` that SKSE 1.5.97 requires. **Port changes (all `// ZP:`):** (1) **in 2.0.12, `UI.OpenCustomMenu` menus are registered under the SWF NAME — the Hero Menu is `00E_heromenu`, not `CustomMenu`** (found by logging every MenuOpenCloseEvent; the plugin silently did nothing until this was fixed); (2) class/affinity read from `_00E_Game_SkillmenuSC` on `Levelsystem 010AA2` alias `Player` (`iCurrentAffinityIndex`, `MajorClassIndex`/`MinorClassIndex` auto-props — same names and index order as 2.1's `_00E_AffinityControl`, whose quest `01597B:FS` does not exist here); (3) null guards in `ScriptObject::FromForm/FromAlias` — without the mod's `BakaHeroMenu.esp` the MCM quest is null and upstream dereferenced it on save load (crash at `+137D3`, `movzx edx, byte [rsi+0x1A]`); (4) Zenderal defaults with no MCM: no gold cost, no gold readout, prompt shows points only. Vel'dun UI's `00E_heromenu.swf` reskin keeps every clip/function name the plugin drives. Plugin log: `OneDrive\Documents\My Games\Skyrim Special Edition\SKSE\BakaHeroMenu.log` (this machine's Documents is OneDrive-redirected). **Verified in game 2026-10-06:** skills level from the menu.
