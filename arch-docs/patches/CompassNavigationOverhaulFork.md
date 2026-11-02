# CompassNavigationOverhaulFork

- **Source:** `src/CompassNavigationOverhaulFork/patches/0001-zenderal-enderal-null-factions-ng11-port.patch`, applied to
  alexsylex/CompassNavigationOverhaul `4055b00` (GitHub, MIT, `LICENSE` copied here). The patch also carries the build
  files (`zen/CMakeLists.txt`, `zen/vcpkg.json`, `zen/vcpkg-configuration.json`, `zen-build.cmd`). The working clone is
  the gitignored `lib/rebuilds/CNO`.
- **Ships:** `SKSE/Plugins/CompassNavigationOverhaul.dll` 2.2.0, copied **into the third-party MO2 mod**
  `Compass Navigation Overhaul - Enderal Patch` over that mod's own DLL. There is no Zenderal mod for it, and no
  `build/manifest.json` entry. `Compass Navigation Overhaul` 2.2.0 still supplies the Interface SWFs. In Wabbajack's
  NoMatchInclude. Committed copy: `compiled/CompassNavigationOverhaul.dll`.
- **FormID block:** none (no plugin)

## Why

On the 1.7.104 update (2026-10-20) SKSE refused the Enderal patch's DLL, and no 1.7 build of it exists. Its source is
upstream CNO plus an Enderal fix, so this rebuilds upstream with that fix. Upstream `4055b00`'s DLL code is identical to
`f39e969`, the namespace-`CNO` + `NND/` layout the Enderal patch was built from; later upstream commits only touch the
SWF sources. Full port notes: the *Compass Navigation Overhaul (Enderal patch DLL)* row of
[`enderal-update-migration.md`](../workspace/enderal-update-migration.md).

- **The Enderal fix (why the Enderal patch existed):** `HUDMarkerManager.h` looked up 5 factions by FormID with
  `LookupByID(...)->As<TESFaction>()`, including Dawnguard's `0x02014217` and `0x02003376`. Enderal's DLC ESMs are
  stubs, so those were null dereferences. Now a null-safe `LookupFaction()`, plus an early-out on a null faction in
  `IsPlayerAllyOfFaction` and `IsPlayerOpponentOfFaction`.
- **NG 11 port:** the old `Offset::` table → the same `RELOCATION_ID`s NG 11 uses (18 `GFxValue::ObjectInterface`,
  `EnsureQuestStarted` 24481/25003, `ResetQuest` 24486/25014); `SKSE::WinAPI` → Win32; `Setting` renames (`kInteger`,
  `GetInteger`, `GetUnsignedInteger`); objectives via `GetPlayerRuntimeData()` (NG 11 handles the 1.7.99 layout shift);
  CNO's duplicate `NiPoint3.cpp` cut down to its own `GetHorizontalAngleTo`; Xbyak on.
- **CoMAP guard:** CNO's MapMarkerFramework compatibility hook pattern-scans CoMAP's DLL. The pattern only exists in
  the old Enderal Map Markers DLL (hidden in the list), not in CoMAP 2.2.1/2.2.2, and a miss wrote a hook at address 6.
  It is now skipped with a warning in CNO's log.

## Rebuild

Needs `lib/CommonLibNG` at v11.0.0 (`94faaed`, alandtse/CommonLibVR) and `lib/rebuilds/_env.cmd` (VS 2026 Build Tools'
`vcvars64.bat` plus its bundled CMake, Ninja and vcpkg as `VCPKG_ROOT`). `zen/CMakeLists.txt` finds CommonLib at
`../../../CommonLibNG`, so the clone must sit at `lib/rebuilds/CNO`. If the clone is lost:

```bash
git clone https://github.com/alexsylex/CompassNavigationOverhaul.git lib/rebuilds/CNO
git -C lib/rebuilds/CNO checkout 4055b00
git -C lib/rebuilds/CNO apply ../../../src/CompassNavigationOverhaulFork/patches/0001-zenderal-enderal-null-factions-ng11-port.patch
```

Then run `lib\rebuilds\CNO\zen-build.cmd`. Output: `build-zen/CompassNavigationOverhaul.dll`. Copy it to `compiled/`
and into the MO2 mod's `SKSE/Plugins/`.

After changing the source in the clone, regenerate the patch from a temporary index. The clone's own index is not
touched, and `build-zen/` and `zen-build.log` stay out:

```bash
cd lib/rebuilds/CNO && GIT_INDEX_FILE=.zen.index sh -c 'git read-tree HEAD && git add -- include source zen zen-build.cmd && git diff --cached --full-index HEAD' > ../../../src/CompassNavigationOverhaulFork/patches/0001-zenderal-enderal-null-factions-ng11-port.patch; rm -f .zen.index
```

**A reinstall or update of `Compass Navigation Overhaul - Enderal Patch` puts its own DLL back**, which SKSE refuses
on 1.7.104. Recopy `compiled/CompassNavigationOverhaul.dll` afterwards.

## Status

Built and deployed 2026-10-20. Source saved here 2026-11-01: the patch applies cleanly to a fresh `4055b00` checkout
and reproduces the clone's tree (same content; a fresh checkout gets CRLF line endings, the clone has LF). No source file
in the clone is newer than the deployed DLL, which is byte-identical to `build-zen/`'s output (SHA-256
`08c2fc8181b1f180…`), so the patch is the source of what ships. **Unverified in game:** check the compass, the quest
list, and whether CoMAP markers show on the compass (the compat hook is skipped, so they probably don't).
