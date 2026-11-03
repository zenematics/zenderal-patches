# FittingRoom

- **Source:** `src/FittingRoom/` — the SPID config (`spid/`), and the rebuilt DLL's source patch
  (`patches/0001-ae-1-7-99-tint-list-offset.patch`, applied to maartenharms/fitting-room `v1.2.0` = `8717ae7`,
  GPL-3.0, `LICENSE` copied here; `build.cmd`; working clone = the gitignored `lib/rebuilds/FittingRoom`)
- **Ships:** `Zenderal - Fitting Room_DISTR.ini` + `SKSE/Plugins/FittingRoom.dll` (1.2.0-zen1, the rebuild) in one
  MO2 mod that must outrank `Fitting Room - ESO Style Transmog`
- **FormID block:** _(none — SPID config + a DLL, no plugin)_
- **Status:** built 2026-11-02 (`compiled/FittingRoom.dll` 5,803,520 bytes, SHA-256
  `98f8faaef71825b745d75e8ce515d97d2ee32de9319600774ddebbde8b37f531`, logs as `Fitting Room v1.2.0-zen1`;
  upstream's is 5,804,032 bytes), deployed to the MO2 mod `Zenderal - Fitting Room`, **unverified in game**

## What it does

[Fitting Room - ESO Style Transmog](https://www.nexusmods.com/skyrimspecialedition/mods/185342)
(maartenharms, 1.2.0, GPL-3.0, source at `github.com/maartenharms/fitting-room`) is an SKSE
transmog/dye/outfit editor drawn on FLICK. It was added to the list on 2026-11-02 together with its
requirements FLICK 1.7.3 NG, Show Player In Inventory 2.4.0 and Menu Studio 1.1.3.

The mod itself is engine-level and loads cleanly on 1.7.104 — its own log reads `runtime 1-7-104-0
(AE) … Address Library (format 5) … self-check PASSED … Fitting Room loaded.` **[verified
2026-11-02, four sessions]** — but the shipped 1.2.0 DLL then **crashes on every save load** on
1.7.104 (next section; fixed by the rebuilt DLL this release ships). The SPID half fixes the one
piece of it that is Skyrim-bound by FormID: the Seamstone.

## Fitting Room 1.2.0 crashes on every save load on 1.7.104 — the rebuilt DLL (2026-11-02)

With Fitting Room on, both launches at 02:23 and 02:24 died ~0.5 s after the save finished loading:
`crash-2026-11-02-02-24-07.log` and `crash-2026-11-02-02-25-15.log`, the same site both times —
`EXCEPTION_ACCESS_VIOLATION at FittingRoom.dll+0x167D64  mov rdx,[rax]`, `rax = 0x24`, called from
Fitting Room's own `kPostLoadGame` handler (frames: `FittingRoom.dll+0x2AAEA7` ← `skse64_1_7_104.dll`
messaging ← the game's `LoadGame`). `FittingRoom.log` ends with `RuleStore: save loaded with 0 rule(s)`
and `Makeup: the tint overlay list is back`, both from that handler.

`dumpbin /DISASM` of the DLL puts the faulting function at `0x167D00`: `PlayerCharacter::GetSingleton`,
the `PlayerFor` comparison, a call to `LiveList` (`0x1694A0`), then `mov rdx,[rax]` on what LiveList
returned — that is `CollectMasks` in `src/MakeupApi.cpp` dereferencing `ListData(LiveList(player))`.
`LiveList` returns the **overlay tint list** pointer read at `ListRoot + 0x18`, and `ListRoot` is a
hand-measured offset: `player + (IsAE() ? 0xB18 : 0xB10)` (the comment in `MakeupApi.h` records it was
measured on AE 1.6.1170; it deliberately does not trust CommonLib's published `tintMasks` member).

**On AE 1.7.99+ every PlayerCharacter runtime-data member moved 8 bytes** — the build added a base class,
and CommonLibSSE-NG models it as `kAE1799ShiftBytes = 0x8` with `GetPlayerRuntimeData` based at
`VersionShift(0x3E0, 8, RUNTIME_SSE_1_7_99)` (`extern/CommonLibSSE-NG/include/RE/P/PlayerCharacter.h`,
present in the exact NG 7.5.4 commit `c542446` Fitting Room is built on, so its own CommonLib-side
`GetRaceData()` etc. are right; only this hand-coded offset is not). So on 1.7.104 the list sits at
`0xB20` and its overlay pointer at `0xB38`; reading `0xB18 + 0x18 = 0xB30` lands on the shifted
array's **size** field — `0x24` = 36 layers, which is also the `36 race slots` the census logged — and
the code dereferences 36. At the main menu the size is 0, so the overlay read as "gone" and nothing
crashed; the first loaded save made it non-zero. Everything in the two logs fits this exactly
**[verified: disassembly + NG header + the crash register]**.

**The fix is one offset** (`patches/0001-ae-1-7-99-tint-list-offset.patch`): `ListRoot` returns
`base + 0xB20` when `REL::Module::IsAtLeast(SKSE::RUNTIME_SSE_1_7_99)`, else the old values; the
`MakeupApi.h` table gains the 1.7.99 row; `kVersion` reads `1.2.0-zen1` so the log names the rebuilt
copy. Nothing else in the source hand-codes a PlayerCharacter offset (grep for `IsAE() ?`, `0xB1`,
`0xB3`: only `MakeupApi.cpp`). Upstream knows: GitHub issues #5/#6 (suamor, 2026-10-04, "multiple CTDs
found with 1.7") and the Nexus bugs "game crashes upon loading the save" / "CtD on either new game or
loading save" (both 1.2.0). suamor's `1_7_Fix` branch keeps the wrong `0xB18` and instead probes whether
the pointer "looks valid" (`TintListState.usable`), which stops the crash by switching the makeup features
off; the offset fix keeps them working. No fix is on upstream `main` (HEAD = `v1.2.0`, 2026-09-18).

**Rebuild** (`src/FittingRoom/build.cmd`, the AirborneGetUpFix shape: VS 2026 Build Tools' bundled
CMake/Ninja/vcpkg, upstream's own `vcpkg.json` baseline `fab1c6dc` and `cmake/x64-windows-static-md`
triplet; upstream's `release` preset is spelled out because it hardcodes a VS Community Ninja path).
If the clone is lost:

```bash
git clone --branch v1.2.0 --recurse-submodules --shallow-submodules https://github.com/maartenharms/fitting-room lib/rebuilds/FittingRoom
git -C lib/rebuilds/FittingRoom apply ../../../src/FittingRoom/patches/0001-ae-1-7-99-tint-list-offset.patch
```

then `src\FittingRoom\build.cmd`; the DLL lands in `lib/rebuilds/FittingRoom/build/release/FittingRoom.dll`,
copy it to `compiled/`. Regenerate the patch with `git -C lib/rebuilds/FittingRoom diff`. Redo this per
Fitting Room update (and drop it once upstream carries a 1.7.99 offset). The MO2 mod
`Zenderal - Fitting Room` must sit **above** `Fitting Room - ESO Style Transmog` in the left pane so its
`SKSE/Plugins/FittingRoom.dll` wins; the original mod stays enabled for everything else it ships.

`FittingRoomLore.esp` (ESL, HEDR 1.70, masters `Skyrim.esm`) holds two new records — `OS_Seamstone`
MISC `0x805` (The Seamstone, `VendorItemSoulGem 0937A3`) and a retired note BOOK `0x801` the DLL
reclaims from saves. **Nothing in the plugin places or sells the stone.** `src/LoreModule.cpp`
stocks it at runtime onto Skyrim's Farengar: `kFarengarNPCID 0x00013BBB`, his placed ACHR
`0x0001A67E`, fallback faction `0x000ABB43`, resolved with `LookupByID`. None of those exist in
Enderal's `Skyrim.esm` (no file for `013BBB` under `Npcs/`, none for `0ABB43` under `Factions/`,
and `01A67E` is not a placed reference in any `Cells/`/`Worldspaces/` file of `Skyrim` or
`EnderalFS`) **[verified against `reference/base/`]**, so every arm of the stocking code fails
closed — `Farengar's reference not found`, `merchant chest has no container form` — and the stone
is unobtainable. Nothing is mis-stocked either: the typed lookups return null rather than some
other Enderal record.

The stone matters in Freeform mode too (the installer choice this list took: `iCostMode=0`,
`bRequireSeamstone=0`): "using" it opens the editor through the equip sink, which is how **Wheeler**
users open Fitting Room from a wheel without the keyboard hotkey, and it becomes the key item and
the currency if the player switches to Lore-friendly in the FLICK settings panel (`iCostMode=2`
spends the stone's charge; filled soul gems refill it — Enderal has those).

The ini gives one Seamstone each to Enderal's two magic merchants whose vendor faction lists
accept `VendorItemSoulGem` (the only lists that do are `VendorItemsAlchAndMagic 118053`,
`VendorItemsSpells 0937A1`, `VendorMagicStuff 0E7621`):

| NPC | EditorID / FormKey | Faction → VEND list | Why |
|---|---|---|---|
| Gabrielle Emberlord | `_00E_CapitalCity_GabrielleFunkenfrst 0A1A2C:Skyrim.esm` | `ArkGabriellesWarenhausFaction 0A1A07` → `VendorItemsSpells` | Ark's magic shop (`CapitalCityMagierkram 09710D`; its chest REFR `118206` is the KataFixes "Funkentanz" CONT `102AD5`) — the Farengar analogue |
| Tarhutie Leklerk | `_00E_Flusshaim_Merchant_Tarhutie 0151C8:Skyrim.esm` | `Merchant_Flusshaim_Tarhutie 05BCF5` → `VendorMagicStuff` | Riverville, the first magic vendor after the prologue |

The other candidates (Mirella Godshand, Ora Stonehand, the Sun Temple alchemists, FS's three Wild
Mages) were left out to keep the stone a single-purchase lore item; add a line if another seller
is wanted.

```
Item = 0x805~FittingRoomLore.esp|NONE|0xA1A2C~Skyrim.esm|NONE|NONE|1|100
Item = 0x805~FittingRoomLore.esp|NONE|0x151C8~Skyrim.esm|NONE|NONE|1|100
```

Form filters, not EditorID strings: an `NPC_` EditorID filter goes through po3_Tweaks' hook
(present, but one more thing to be silently absent), and the two forms are unambiguous.

## Why SPID and not a chest override

- **Gabrielle's chest is owned.** Her merchant container base is `102AD5`, one of the three
  contested magic-vendor chests `KataFixes` merges and owns alone (CLAUDE.md "one owner per
  record"). Adding the stone there would mean Kata Fixes mastering `FittingRoomLore.esp` — a hard
  dependency on an optional mod — or a second override that wipes the merge.
- **A chest entry sells forever.** A merchant chest respawns from its base list, so a stone in the
  list restocks every 48 h. Fitting Room's own "take it off the list once the player has one"
  sync (`SyncBaseStock`) only runs for Farengar's faction.
- **SPID `Item =` goes to the NPC base, every session, not to the actor.** That is exactly the
  right shape here: the base shows one stone; when the player buys it the actor's inventory delta
  records the removal, and the next session's re-add nets to zero again. One stone per vendor per
  save. (The same mechanism keeps [`NpcPotions`](NpcPotions.md) from piling up.) Vendor NPCs sell
  their own inventory through the same VEND-list filter as the chest, which is why the list
  check above matters.
- No plugin, no masters, no forwarding, nothing baked into a save.

Check SPID's log after a launch: `po3_SpellPerkItemDistributor.log` must list
`Data\Zenderal - Fitting Room_DISTR.ini` and its `Registered X/Y Items` line must read `X == Y`
(the count is across all configs; NPC Potions alone contributes 15). With the lore plugin
disabled the config costs one `[Zenderal - Fitting Room_DISTR.ini] … SKIP` line and nothing else.

## Menu Studio 1.1.3 kills the game at SKSE load on 1.7.104 (2026-11-02)

Both launches on 2026-11-02 (01:38 and 01:41) died inside SKSE's plugin loading: `skse64.log`
ends at `loading plugin "MenuStudio"` both times (15,947 bytes, identical), no plugin
alphabetically after it wrote a log that session (MfgFix, OAR, po3_Tweaks, Precision, Show Player
In Inventory, SmoothCam, TrueHUD, Wheeler all still carried 01:08 logs), `MenuStudio.log` was
never created, and there is no `crash-*.log` — a fail-fast before the logger opens, which no crash
logger sees. **Menu Studio 1.1.3 (DLL built 2026-08-29) predates 1.7.104**; its strings show the
older CommonLibSSE-NG that opens `version-{}.bin` for a runtime it calls SE and
`report_and_fail`s when the file is missing — the same failure
[`ShatterveilAE`](ShatterveilAE.md) byte-patched. Fitting Room 1.2.0 (2026-09-16) carries the
format-5 reader and loads.

**Fix: update Menu Studio to 1.2.0** (Nexus 185362, 17 Sep 2026, "AE 1.7 should work as well, but
not personally tested"; same `VersionCheck.cpp` as Fitting Room's, which passes here). Fitting
Room only *uses* Menu Studio (camera framing, backdrops) — `MenuStudioApi::CanBeFramed` answers
true without it — so if 1.2.0 still refuses (`MenuStudio.log`: `Address self-check FAILED …
Not loading` is the clean refusal, not a crash) Menu Studio can simply be disabled. The author's
file page also warns that current Show Player In Inventory (the list has 2.4.0) broke Menu Studio
("please use older SPII version 1.61"); Fitting Room recommends SPII, so if Menu Studio and SPII
2.4.0 fight, SPII wins and Menu Studio goes.

Menu Studio is GPL-3.0 (`github.com/maartenharms/menu-studio`, tag v1.2.0) — a 1.7.104 rebuild
the way [`CompassNavigationOverhaulFork`](CompassNavigationOverhaulFork.md) was done is possible
if 1.2.0 turns out to load-and-do-nothing, but not worth doing blind.

## What else in Fitting Room is Skyrim-bound, and why it is left alone

- **Dye unlocks** (`Unlocks/lore.json`, `skyrim.json`, `eso.json`) gate colours on Skyrim quests,
  locations (`plugin|formId` via `LookupForm`) and `Game.QueryStat` counters. The rules are
  fail-closed and would lock those colours forever here — but the list runs `bDyeUnlocks=0`, so
  nothing is gated. Earned dyes on Enderal would need an `Unlocks/zenderal.json` re-keying every
  Skyrim rule to Enderal quests/locations (the merge is later-file-wins per colour key). Not done.
- **`Presets/OutfitSlots - Nightingale Sample.json`** names Skyrim armor `0FCC0F`/`0FCC11`/`0FCC0D`,
  absent in Enderal's `Skyrim.esm`, so the sample preset is dead. Cosmetic.
- **Requip aura** defaults `SoulTrapFXShader 0506D7` + `SoulTrapTargetEffects 0506D6`, and the
  keywords/sounds the plugin uses (`ActorTypeNPC 013794`, `ActorTypeCreature 013795`,
  `VendorItemBook 0937A2`, `VendorItemSoulGem 0937A3`, `ITMNoteUp 0C7A54`, `Gold001 00000F`) all
  exist in Enderal's `Skyrim.esm` **[verified by filename in `reference/base/Skyrim/`]**.
- **Controllers:** no pad navigation at all, deliberately (`src/ControllerSupport.h`,
  `kEnabled = false`, four models tried and rejected 2026-08-15). The editor is mouse-driven;
  the Seamstone-in-Wheeler route above is the pad-friendly way *in*.

## Load / install

Install as its own MO2 mod (`Zenderal - Fitting Room`, the ini at the mod root — SPID's `Data\`
scan is non-recursive) or drop the ini into the Patch Collection next to
`Zenderal - NPC Potions_DISTR.ini`. Position is irrelevant. Needs `FittingRoomLore.esp` enabled.
