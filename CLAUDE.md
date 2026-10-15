# Zenderal Patches — Spriggit Workspace Guide

> **This file is the index a future session reads first.** It holds the rules every session needs and
> points at `arch-docs/` for everything else. When you learn something the hard way, write it in the
> matching `arch-docs/` file (or a new one), and add a one-line pointer here **only** if it is a rule
> every session must know.
>
> Facts marked **[verified]** were checked against this machine's actual Enderal install or toolchain.
> Facts marked **[upstream]** come from Mutagen/Spriggit/SureAI source or documentation. Anything
> unmarked is convention, not measurement — treat it as changeable.

## What this is

**Zenderal** is an Enderal: Forgotten Stories (Special Edition) modlist aiming at three things:
**bug fixes**, **modern combat**, and **modern visuals**. *This repo is not the modlist.* It is the
workspace where the **patch plugins Zenderal ships** are authored, built and released — the
compatibility and bugfix `.esp` files that make the list's third-party mods work together on
Enderal — plus the curation docs that record what the list does and why.

Plugins are decompiled to YAML, edited as text, and re-packed to `.esp`.
**Never hand-edit binary plugins — edit the YAML.**

- Game: **Enderal: Forgotten Stories (Special Edition)**, running on the SkyrimSE engine.
- Spriggit game release: **`EnderalSE`** — *not* `SkyrimSE`. It makes `Enderal - Forgotten Stories.esm`
  an implicit base master. Keep `.spriggit`, `spriggit-meta.json` and `tools.json`'s
  `spriggit.gameRelease` all reading `EnderalSE`. **[verified]**
- Spriggit package/source: `Spriggit.Yaml.Skyrim`
- Spriggit CLI version: **`0.40.0` — deliberately pinned, do not upgrade.** 0.41.0 silently drops
  leveled-list entries that carry COED owner data — exactly the loot/vendor records this list patches.
- CLI path + all tool paths: `.claude/config/tools.json` (gitignored; see Tooling config below).

Detail: [`arch-docs/workspace/spriggit.md`](arch-docs/workspace/spriggit.md).

Every patch in this repo should trace back to one of these pillars. If it doesn't, it probably belongs in a
different repo.

| Pillar | Goal | What patches here typically do |
|---|---|---|
| **Bug fixes** | Ship Enderal as SureAI intended, minus the bugs | Fix broken records, quest blockers, bad navmesh/refs, dangling references; forward community bugfix mods onto Enderal's ESM |
| **Modern combat** | Contemporary combat feel without breaking Enderal's balance | Reconcile combat overhauls with Enderal's talent/perk system, weapon/armor keywords and combat styles |
| **Modern visuals** | Current-generation look, Enderal's art direction intact | Reconcile lighting/weather/ENB-adjacent mods with Enderal's own lighting, and mesh/texture replacers with Enderal's assets |

## Knowledge base (oculory-rag) — search it before answering

If the `oculory-rag` MCP tools are available, use them **before** answering from memory and
before grepping `reference/` by hand:

- **`search`** — the written knowledge base: engine behaviour, record patterns, SPID, Spriggit
  and Mutagen workflow, third-party mod analyses, prior art and design notes.
- **`game_search` / `game_read`** — the decompiled game files themselves: ~331k records and
  ~19k Papyrus scripts, looked up by EditorID, FormID, FormKey or in-game name. Prefer these
  over walking `reference/` by hand; they are indexed and answer in milliseconds.
- Pass `game="enderal"` for this repo. Enderal ships a MODIFIED `Skyrim.esm`, so a
  vanilla-Skyrim answer is often the wrong one.

Cite the doc id or FormKey a claim rests on, and keep the `[verified]` / `[community]` /
`[unverified]` marks honest — retrieved text is evidence, not proof.

These tools are an optional local index. If they are not present, work in this repo exactly as
before: nothing here depends on them.

## Enderal ground truth — the short version

Full detail, with the evidence: [`arch-docs/enderal/install-and-engine.md`](arch-docs/enderal/install-and-engine.md)
and [`plugin-architecture.md`](arch-docs/enderal/plugin-architecture.md).

- **SSE 1.5.97, not 1.6.x.** Every SKSE `.dll` in the list must be a 1.5.97 (pre-AE) build; an AE
  build loads nothing. The commonest "the list doesn't launch" cause. **[verified]**
- **`Skyrim.esm` in Enderal's Data folder IS base Enderal** (author `mcarofano`, no Tamriel — the
  overworld is `Vyn`). A `:Skyrim.esm` suffix means "base Enderal"; a FormID from a Skyrim wiki will
  not resolve to the same record. `Enderal - Forgotten Stories.esm` (FS) masters only `Skyrim.esm` +
  `Update.esm`, and **28.7% of FS's records override base Enderal**. **[verified]**
- **The DLC ESMs are empty stubs** (1–2 records each). Never master them in a patch; the engine loads
  them anyway, so third-party mods that master them load fine. **[verified]**
- **SkyUI is built into Enderal.** Stock `plugins.txt` is just FS + `SkyUI_SE.esp`.
- **HEDR 1.71 plugins are invisible on a BEES-less 1.5.97.** Always author at `Version: 1.7` (Mutagen
  defaults to 1.71). The list ships BEES, which makes 68 third-party 1.71 plugins load — don't make
  our patches depend on it. [`testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md#the-form-version-ceiling-hedr-171-and-bees)
- **No Creation Kit or Papyrus compiler ship with Enderal** — both come from a Skyrim SE install
  (`skyrimSeRoot`), pointed at Enderal's `Data`.

## Tooling config (no hardcoded paths)

All tool paths and per-machine settings live in **`.claude/config/tools.json`** (gitignored;
template at `tools.example.json`). Skills load it via `.claude/config/tools.ps1`, which exposes
`$Tools` (e.g. `$Tools.spriggitCli`, `$Tools.papyrusCompiler`, `$Tools.papyrusSource.enderal`,
`$Tools.xedit`) and an `Assert-Tool` guard. **Never reintroduce a hardcoded path into a skill —
change the config instead.**

Note that `gameRoot` is **Enderal's** folder while `skyrimSeRoot` is the **Skyrim SE** folder. They
are separate installs, and several steps need both.

- **The Zenderal modlist itself** installs a full MO2 instance (Enderal copy + mods + tools) that
  can be hundreds of GB. It is gitignored (`/modlist/`, `/downloads/`). Run the **`modlist-install`**
  skill to install it and auto-discover its tool paths into `tools.json`.
- Without a modlist, fill `tools.json` by hand from `tools.example.json`.

## Workflow (round-trip)

```
.esp/.esm  ──serialize──►  YAML (committed)  ──deserialize──►  .esp/.esm
                 ▲                                                  │
                 └──────────── you edit the YAML ◄──────────────────┘
```

Serialize/deserialize commands: see `README.md`. After editing YAML, deserialize and load the plugin
in xEdit (**in `-EnderalSE` mode, with `-D:"<data dir>"`**) to verify before shipping. Deploy with the
`mod-deploy` skill, never by hand. Testing, crash logs and load-crash bisection:
[`arch-docs/workspace/testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md).

## Folder map

```
src/                       # EVERY patch lives here — one folder per patch
  <PatchName>/
    <PatchName>ESP/        # Spriggit YAML — COMMITTED, source of truth
    Scripts/source/*.psc   # Papyrus source — COMMITTED
    Scripts/compiled/*.pex # COMMITTED via a .gitignore exception (CI can't compile Papyrus)
    tools/*.ps1|*.py       # generators — when a patch has them, never hand-edit what they generate
    spid/*_DISTR.ini       # SPID configs — COMMITTED; shipped via the manifest's "files" key
build/                     # build.ps1 + manifest.json
arch-docs/                 # all knowledge — see "Where the documentation is" below
  workspace/               #   this repo's toolchain: Spriggit, Papyrus, release shapes, testing
  patches/                 #   one doc per src/ patch: mechanism, history, postmortems
  modlist/                 #   list-wide conflict lessons (list-shaped records, EGO, mod gotchas)
  enderal/                 #   how Enderal works; install/engine facts; porting from Skyrim
  EGO/                     #   EGO analysis + conflict index
  magic/                   #   GENERATED magic dataset; /magic-extract regenerates it
  tools/                   #   SPID reference + its Enderal guide
reference/base/            # gitignored — Enderal/vanilla decompiles + script source, LOOKUP ONLY
reference/mods/            # gitignored — third-party list mods, serialized for lookup
modlist/                   # gitignored — the installed Zenderal MO2 instance, hundreds of GB
papyrus-source/            # gitignored — spare slot for unpacked .psc trees (see reference/base)
```

`src/` is the only place patch content goes. Each patch gets its own `src/<PatchName>/` folder, its
own `build/manifest.json` release entry and its own `arch-docs/patches/<PatchName>.md`; the
`/mod-new-plugin` skill sets the first two up. `reference/base/` contents (and the fact that
`reference/base/Skyrim/` cannot be rebuilt) are in [`spriggit.md`](arch-docs/workspace/spriggit.md).

**Release shapes** — details and per-shape rules in
[`arch-docs/workspace/release-shapes.md`](arch-docs/workspace/release-shapes.md):

| Shape | Ships | Key rule |
|---|---|---|
| Patch | small override `.esp` mastering what it fixes | the default; ESL-flagged |
| Replacement | the third-party plugin rebuilt under its own filename | only with author permission; built in the [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) repo, not here |
| Script-only | recompiled loose `.pex`, `"plugins": []` | never add/remove a `Property`; must sort ABOVE the mod in MO2 |
| SPID config | one `Zenderal - *_DISTR.ini`, `"to": ""` | archive root only (SPID is non-recursive); verify via `Registered X/Y` in the SPID log |

Two mutually exclusive upstream builds → two archives of **one** ModKey, not two plugins.

## Guardrails — how to work in this repo

These are distilled from real failures in this workspace's lineage. They cost test cycles to learn.

1. **Ground-truth before claiming.** Do not conclude a patch is or isn't needed, or that a record
   does what its name suggests, from the name alone. Read the serialized record, trace the
   FormKeys, and **show the evidence alongside the verdict**. If a mechanic depends on a third-party
   mod's compiled script, read that script's decompiled source — data-driven parts extend to your
   records, hardcoded index checks do not.
2. **Assume nothing transfers from Skyrim.** Enderal reuses the engine and almost none of the
   design. Progression, crafting, lighting, economy and the perk UI are all Enderal's own (see
   [`arch-docs/enderal/porting-from-skyrim.md`](arch-docs/enderal/porting-from-skyrim.md)). A pattern
   that is correct for Skyrim modding is a *hypothesis* here until you have read Enderal's record or script.
3. **Prefer a proven archetype to an invented mechanism.** Read
   `arch-docs/enderal-record-patterns.md` first. The engine fails silently: an inert record produces
   no error, so an invented mechanism costs a full build-deploy-launch-test cycle to disprove.
4. **Copy records verbatim; never retype hex.** When basing a record on an existing one, copy the
   file and edit the fields that differ. Hand-transcribing `Data:` blobs has produced odd-length hex
   that fails the build, and dropped array entries that fail silently. Prefer a script over
   retyping. Re-check array lengths after any edit.
5. **A patch's job is to forward, not to author.** The commonest patch bug is not a wrong value —
   it is an override that carries *your* change and silently reverts someone else's. Before
   overriding a record, look at every plugin in the list that already touches it and confirm the
   winning version of every field you are not deliberately changing.
6. **Ask for paths; don't hunt for them.** Install locations, modlist names, MO2 folders and mod
   names live in `tools.json` or in the user's head. Read the config or ask — filesystem-searching
   for them wastes time and lands on the wrong candidate.
7. **Verify the deploy target before blaming the records.** A mod in a wrongly-named MO2 folder is
   invisible; the game runs fine and the change simply isn't there. The `mod-deploy` skill checks
   this. Rule out "never loaded" before debugging "loaded but broken" — including a **stale deployed
   file** (check its timestamp against the build).
8. **A clean build is not a working patch.** Deserialize, xEdit and the Papyrus compiler all passing
   proves it *builds*. Only launching Enderal proves it *runs*. Say which of the two you have
   actually established.
9. **Recompile and re-commit `.pex` whenever a `.psc` changes.** CI cannot run the Papyrus
   compiler. `build/build.ps1` fails on a *missing* `.pex` but cannot detect a *stale* one.
10. **PowerShell 5.1 is the target** for build scripts and skills: `Set-StrictMode` is on, there is
    no `&&`/`||`, no ternary, no null-coalescing, and no built-in YAML parser. Write `-Encoding utf8`
    explicitly when a file will be read by other tools. Two further traps when bulk-editing YAML:
    - **The Spriggit YAML is CRLF, so `$` in a multiline regex does not match.** Use `(?=\r?$)` or
      drop the anchor, and always assert the replacement count and throw on zero. **[verified]**
      (Full text: [`testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md#powershell-51-and-bulk-edit-traps-guardrails-10-and-11-in-full).)
    - `Join-Path` takes **two** arguments in 5.1; nest the calls.
    - **Never rewrite a UTF-8 doc with 5.1's `Set-Content -Encoding utf8`** — it double-encodes every
      `—`. Use the Edit tool.
11. **Bulk record edits should be scripted, verified by count, and re-validated after.** Generate
    them from `reference/` with a script that *asserts* what it changed, then re-resolve every
    FormKey the patch emits against the serialized masters. `000014:Skyrim.esm` (PlayerRef) is
    **absent from `reference/base/Skyrim/`** despite being valid — allow-list it. **[verified]**

## FormKey discipline

- **New** records use the patch plugin's own name as the FormKey suffix: `<hex>:<PatchName>.esp`.
- **Overrides keep the defining master's suffix** — that is how you tell at a glance which records
  you invented and which you are modifying:

  | Suffix | Means |
  |---|---|
  | `:Enderal - Forgotten Stories.esm` | a record Enderal itself created — **71%** of its records |
  | `:Skyrim.esm` / `:Update.esm` | a vanilla FormID. May be untouched vanilla, **or Enderal content sitting on an overridden vanilla record** |
  | `:<SomeMod>.esp` | overriding a third-party list mod — check *its* load position |
  | `:<PatchName>.esp` | a record this patch invented |

- **Master order in `RecordData.yaml`** is load order:
  `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then any third-party plugin you
  override, in list order. FS survives as a declared master and may be referenced freely.
- **ESL (`Small`) plugins are constrained to FormIDs `0x800–0xFFF`.** Patches should almost always
  be ESL-flagged — a list carries a lot of them and the 254-plugin limit is real. Note that
  *overrides consume no new FormID*, so an ESL patch can override thousands of records and still
  only need a handful of the 2048 new-record slots.
- Allocate a **contiguous block per feature** for readable diffs.
- ALWAYS grep the whole workspace (your patch folders + `reference/`) for a hex FormID before
  assigning it — use the `formkey-check` skill.
- **Before "injecting" a vanilla FormID Enderal lacks, grep `FormKey: <id>` unanchored** — it may be
  a placed reference inside a cell file (`10CED7` is a REFR in Enderal). **[verified]**

### Allocations in use — and one owner per record

Each patch's own ESL block, plus what it owns. **Whichever Zenderal plugin overrides a contested
record owns it alone** — a second plugin of ours touching it silently wipes the first one's entries.
Full mechanism, history and postmortems per patch in [`arch-docs/patches/`](arch-docs/patches/).

| Patch → ships | Block | One line | 
|---|---|---|
| [`RelentlessSwordPatreon`](arch-docs/patches/RelentlessSwordPatreon.md) → `Zenderal - Relentless Sword.esp` | `0x800–0x831` | johnskyrim's Patreon "Zen" build; filename and `0x800–0x827` kept from the retired six-blade release so saves keep their swords |
| [`MagicPatches`](arch-docs/patches/MagicPatches.md) → `Zenderal - Magic Patches.esp` | none | ALL magic balance: Apocalypse + Triumvirate cost ladders/fever, weapon-enchant ×2; **owns** the four `_00E_SpellBooksLoot*` + `02E_Scrolls 0905A5` LVLIs. Generated — see doc for regeneration order |
| [`KataFixes`](arch-docs/patches/KataFixes.md) → `Zenderal - Kata Fixes.esp` + `.pex` | none | **Owns** vendor chests `102AD5`, `118050`, `05BCD6` (must keep each `*_CustomMerchandise` hook); dedupes Kata spell packs |
| [`SkipPrologue`](arch-docs/patches/SkipPrologue.md) → `Zenderal - Skip The Prologue.esp` | `0x800–0x802` | One `MQ01.SetStage(130)` lands the player at Jespar's camp |
| [`FasterSprint`](arch-docs/patches/FasterSprint.md) → `Zenderal - Faster Sprint.esp` | none | Sprint +92%, drain −50%; must load after EGO **and** `Dynamic Sprint.esp`; armed sprint needs SSMT_Fix `WieldingMovementTypeFixes=true` |
| [`QuieterWaterfalls`](arch-docs/patches/QuieterWaterfalls.md) → `Zenderal - Quieter Waterfalls.esp` | none | 72 SNDR +6 dB attenuation over RAO; coast wind bed `0DB6DD` given an attenuating model so it no longer snaps on near Ark. Generated |
| [`DynamicDodgeNoSway`](arch-docs/patches/DynamicDodgeNoSway.md) → OAR `user.json` only | none | Attack-cancel dodges use the step dodge, not the sway |
| [`DynamicDodgeShotFix`](arch-docs/patches/DynamicDodgeShotFix.md) → `Zenderal - Dynamic Dodge Shot Fix.esp` | none | Re-parents `BowDodge` so it fires |
| [`HalfStarlingDS`](arch-docs/patches/HalfStarlingDS.md) → `Zenderal - Half Starling DS Races.esp` | none | Restores per-race stats on `WoodElfRace 013749` |
| [`RiverBush`](arch-docs/patches/RiverBush.md) → `Zenderal - RiverBush.esp` | `0x800–0x81F` | 32 CK-placed bushes in Riverville; re-apply HEDR 1.70/ESL after any CK edit |
| [`SettingsApplier`](arch-docs/patches/SettingsApplier.md) → `Zenderal - Settings Applier.esp` + `.pex` | `0x800` | Re-applies save-based MCM settings once per save |
| [`FHRParryPoise`](arch-docs/patches/FHRParryPoise.md) → `Zenderal - FHR Parry Poise.esp` | none | FHR parry poise 20/5 → 60/40 so parries stagger |
| [`ChocolatePoiseEnderal`](arch-docs/patches/ChocolatePoiseEnderal.md) → `.esp` + `ZenCPRFactionFix.dll` | `0x800–0x808` | Vanilla-EditorID reference items for CPR + NSF crash fix |
| [`BrawlFixes`](arch-docs/patches/BrawlFixes.md) → two recompiled SureAI scripts | none | Brawls no longer break on magic/framework hits |
| [`NpcPotions`](arch-docs/patches/NpcPotions.md) → `Zenderal - NPC Potions_DISTR.ini` | none | SPID potions to NPCs; depends on NUP corpse-stripping being off |
| [`ControllerTweaks`](arch-docs/patches/ControllerTweaks.md) → controlmap, SkyUI config, `_00E_Game_SkillmenuSC.pex` | none | Gamepad fixes + B+D-pad-Up Hero Menu chord |
| [`OldTempleWeather`](arch-docs/patches/OldTempleWeather.md) → `Zenderal - Old Temple Weather.esp` | none | Intro-beach weather under Obsidian (currently disabled with Obsidian) |
| [`BakaHeroMenu`](arch-docs/patches/BakaHeroMenu.md) | none | **Retired 2026-10-14** — source recoverable from commit `fa07b81`; its CommonLibSSE-NG clone moved to the repo-root `lib/` |
| [`TrueHUDCombatIcons`](arch-docs/patches/TrueHUDCombatIcons.md) → `ZenTrueHUDCombatIcons.dll` | none | FHR status icons inside TrueHUD's info bar |
| [`FrostAtronachSEFix`](arch-docs/patches/FrostAtronachSEFix.md) → converted meshes (not committed) | none | Black Ice Elementals: LE→SE meshes + plain lighting shader |
| [`PrecisionLiftFix`](arch-docs/patches/PrecisionLiftFix.md) | none | **Retired** — record of failed routes; source removed |
| [`PrecisionFork`](arch-docs/patches/PrecisionFork.md) | none | **Retired 2026-10-13** — the list ships Precision's `bApplyImpulseOnHit = 0` instead; fork recoverable from commit `7b63d3a` |
| [`ZenTraitsFixes`](arch-docs/patches/ZenTraitsFixes.md) → one recompiled script | none | Ambrosia reduces Arcane Fever again |
| [`LearningBooks`](arch-docs/patches/LearningBooks.md) | none | **Retired 2026-10-14** with Leveling Redone — books spend points again (EGO's records); source recoverable from commit `9afae18` |
| [`MCODirectionalPowerAttacks`](arch-docs/patches/MCODirectionalPowerAttacks.md) → `.esp` | none | Side/back/sprint power attacks reach FHR's MCO animations |
| [`PrettyArmoryEGO`](arch-docs/patches/PrettyArmoryEGO.md) → `Zenderal - Pretty Armory EGO Patch.esp` | none | 141 Pretty×EGO merges. Generated |
| [`ArkMyradPlatformFix`](arch-docs/patches/ArkMyradPlatformFix.md) → `Zenderal - Ark Myrad Platform Fix.esp` | none | Moves FS marker `02F0B5`; read the FS-override postmortem first |
| [`ArkMarketTreeFix`](arch-docs/patches/ArkMarketTreeFix.md) → `Zenderal - Ark Market Tree Fix.esp` | none | Lowers a floating juniper an addon placed in Ark's market |
| [`EppiRivervilleStatues`](arch-docs/patches/EppiRivervilleStatues.md) → `Zenderal - EPPI Riverville Statues Patch.esp` | none | Moves a statue mod's bust with the desk EPPI moved |
| [`FeverDeathLatchFix`](arch-docs/patches/FeverDeathLatchFix.md) → recompiled `_00E_EPUpdateFunctions` | none | Clears the stuck `isdead` latch that blocks level-ups; forked from SureAI's source |
| [`UndeadCreaturesReplacerEGO`](arch-docs/patches/UndeadCreaturesReplacerEGO.md) → `.esp` | none | UCR visuals on EGO's Lost One NPCs. Generated |
| [`EnderalTextureRestores`](arch-docs/patches/EnderalTextureRestores.md) → extracted textures (not committed) | none | Restores Enderal textures a Skyrim texture mod cut out |
| [`PrettyFemaleMeshRestores`](arch-docs/patches/PrettyFemaleMeshRestores.md) → extracted meshes (not committed) | none | Pretty's BSA meshes over CBBE's loose ones; sort above CBBE |
| [`TerrainTextureSetFix`](arch-docs/patches/TerrainTextureSetFix.md) → `Zenderal - Terrain Texture Set Fix.esp` | none | Drops normal maps from two TXST height slots (ENB streaks); load after DynDOLOD.esp. `src/TerrainParallaxHeights/` is its failed first attempt |
| [`MissingParallaxHeights`](arch-docs/patches/MissingParallaxHeights.md) → generated flat `_p` textures | none | 289 missing parallax heights filled with flat grey |
| [`ArkWallCurbFix`](arch-docs/patches/ArkWallCurbFix.md) → Enderal's original meshes (not committed) | none | Undoes SRP's parallax on Ark wall meshes |
| [`ApocalypseNaviFix`](arch-docs/patches/ApocalypseNaviFix.md) → rebuilt Apocalypse `.esp` (hotfix) | none | Drops the `012FB4` NAVI that deleted a Forgotten Temple floor tile; retire once `enderal-mods` drops it |
| [`Prophecy`](arch-docs/patches/Prophecy.md) → `Zenderal - Prophecy.esp` + scripts + CSF config | `0x800–0x807` | **Prototype**, non-ESL: Ordinator-perk tree via Custom Skills Framework |
| [`ImprovedCameraSheatheFix`](arch-docs/patches/ImprovedCameraSheatheFix.md) → `ZenICSheatheFix.dll` | none | NOPs IC's drawn-weapon camera drop; tied to IC 1.1.2.4228 |
| [`HorseCloakFluffFix`](arch-docs/patches/HorseCloakFluffFix.md) → `.esp` + generated meshes | none | Fluffworks fur trimmed under the Ark guard horses' barding |
| [`DintHairs`](arch-docs/patches/DintHairs.md) → rebuilt Dint999 hair plugins | none | Hairs only, no wigs; +2 full plugin slots |
| [`GuardFalconer`](arch-docs/patches/GuardFalconer.md) → `Zenderal - Guard Falconer Patch.esp` | none | Restores Falconer cuirass/helmet that Pretty Factions reverted |
| [`MoonsteelPretty`](arch-docs/patches/MoonsteelPretty.md) → `.esp` + 2 loose meshes | none | Points EGO's Moonsteel line back at Pretty's meshes. Generated |
| [`FlintlockOverhaul`](arch-docs/patches/FlintlockOverhaul.md) → `.esp` + script + DAR recipes ESL + KID + icons | `0x800–0x813` | Pistols use bullets and reload; 111 NPCs rebuilt over gun mods; load after Enderal SE - Crossbows |
| [`DragonPriestStaffSwap`](arch-docs/patches/DragonPriestStaffSwap.md) → loose meshes (not committed) | none | Curator's taste: Pretty's chain-lightning staff mesh at the Dragon Priest staff paths |
| [`StaffDrawFix`](arch-docs/patches/StaffDrawFix.md) → OAR submod with vanilla clips | none | Staff draw plays again over Smooth Magic Casting's always-true equip |

### Useful FormKey constants

Engine-hardcoded, so Enderal's `Skyrim.esm` keeps them. **Do not extend this table from Skyrim
documentation** — look records up in `reference/base/` and cite the EditorID you found.

| FormKey | Meaning |
|---|---|
| `000014:Skyrim.esm` | PlayerRef |
| `000038:Skyrim.esm` | GameHour global |
| `000039:Skyrim.esm` | GameDaysPassed global |
| `000010:Skyrim.esm` | MapMarker base |
| `000034:Skyrim.esm` | XMarker base |
| `10F63C:Skyrim.esm` | MapMarkerRef LocationRefType (required for discoverability) |
| `013F42:Skyrim.esm` | `RightHand` EquipType |

## Papyrus — the rule that matters

The compiler's `-i` path is **first-wins**, and 55 script names exist in both Enderal's and Skyrim's
trees, so Enderal must come first: **[verified]**

```
-i="<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>;<importDirs...>"
```

Enderal ships real source for its own (`_00E_`) scripts in `ScriptsEnderal.zip` — read that instead
of decompiling. Toolchain, import-dir table, CK and BSA extraction:
[`arch-docs/workspace/papyrus.md`](arch-docs/workspace/papyrus.md). Record any new import dir there.

## Traps that have each cost a full debugging cycle

Read the linked doc before working near any of these.

- **A list-shaped record (container, LVLI, NPC inventory) is replaced wholesale** — a late override
  silently deletes earlier mods' stock. `EGO SE - Leveling Redone.esp` is the big offender. Run
  `python src/KataFixes/tools/00-audit-vendor-conflicts.py`. → [`modlist/list-shaped-records.md`](arch-docs/modlist/list-shaped-records.md)
- **EGO overrides 6203 records** — grep [`arch-docs/EGO/conflict-index.md`](arch-docs/EGO/conflict-index.md)
  before touching any record and build from EGO's YAML. EGO is not Localized; `Player 000007` carries
  its 42 perks. → [`modlist/ego-conflicts.md`](arch-docs/modlist/ego-conflicts.md)
- **FS overrides base Enderal** — grep `reference/base/EnderalFS/` before `Skyrim/`, and in game
  `prid <id>` shows `Ref last changed by:`. → [`patches/ArkMyradPlatformFix.md`](arch-docs/patches/ArkMyradPlatformFix.md)
- **A third mod loading after ours reverts us silently** (Dynamic Sprint vs Faster Sprint). Re-run
  conflict greps whenever a mod's enabled state changes. → [`patches/FasterSprint.md`](arch-docs/patches/FasterSprint.md)
- **A ported mod's distribution is the likeliest thing to be dead** — vanilla leveled lists mostly
  don't exist in Enderal, and a surviving vanilla FormID may be a different record (`00003C` is
  `MQP01Home`, not Tamriel). Delete any ported `NavigationMeshInfoMaps/`: `012FB4` is a floor tile in
  Enderal. → [`enderal/porting-from-skyrim.md`](arch-docs/enderal/porting-from-skyrim.md)
- **`OnHit`'s `akWeapon` is the hit source** — a `Spell` on every combat-framework hit.
  → [`patches/BrawlFixes.md`](arch-docs/patches/BrawlFixes.md)
- **A load crash: bisect the plugin header/masters before the records.**
  → [`workspace/testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md#debugging-a-load-crash)
- **This list's crash logs come from .NET Script Framework**, in `<modlist>\overwrite\NetScriptFramework\Crash\`
  — it ships no Crash Logger DLL. SKSE plugin logs land in `My Games\Skyrim Special Edition\SKSE\`, not the
  Enderal folder. → [`workspace/testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md)
- **Installed asset does nothing? Check the CRDW cache first** — a stale `data_*_.cache` makes newly
  installed files unloadable; rebuild it after every install and Pandora run. → [`modlist/mod-gotchas.md`](arch-docs/modlist/mod-gotchas.md)
- **Exterior-cell refs need 4 scaffolding files** or Spriggit silently drops the tree; YAML comments
  do not survive a re-serialize. → [`workspace/spriggit.md`](arch-docs/workspace/spriggit.md)
- **A clean SPID log does not mean the item reached the player** (NUP stripped corpses).
  → [`patches/NpcPotions.md`](arch-docs/patches/NpcPotions.md)
- **Any SKSE plugin that looks up vanilla EditorIDs is silently dead in Enderal** — grep a DLL's
  strings. → [`patches/ChocolatePoiseEnderal.md`](arch-docs/patches/ChocolatePoiseEnderal.md)
- **Skipping to a main-quest point = find Enderal's own `SetStage`**, don't re-author the transition.
  → [`patches/SkipPrologue.md`](arch-docs/patches/SkipPrologue.md)
- **Enderal's cell EditorIDs are German** (Riverville = `Flusshaim*`, Ark = `CapitalCity*`).
- Before porting any Skyrim mod, use the **`skyrim-to-enderal-porter`** subagent; for magic mods,
  follow with **`enderal-magic-porter`**.

## Where the documentation is

| Read this | For |
|---|---|
| **[`arch-docs/workspace/`](arch-docs/workspace/)** | **This repo's toolchain** — Spriggit pin and recipes, Papyrus, release shapes, testing/debugging |
| **[`arch-docs/patches/`](arch-docs/patches/)** | **One doc per patch** — what it does, why, and the postmortems behind it |
| **[`arch-docs/modlist/`](arch-docs/modlist/)** | **List-wide conflict lessons** — list-shaped records, EGO, third-party mod gotchas |
| **[`arch-docs/enderal/`](arch-docs/enderal/)** | **How Enderal actually works** — start with [`plugin-architecture.md`](arch-docs/enderal/plugin-architecture.md); install facts in [`install-and-engine.md`](arch-docs/enderal/install-and-engine.md); [`porting-from-skyrim.md`](arch-docs/enderal/porting-from-skyrim.md) before assuming a Skyrim mod works |
| **[`arch-docs/EGO/`](arch-docs/EGO/)** | **How EGO works and how to patch around it** — start with [`patching-ego.md`](arch-docs/EGO/patching-ego.md) |
| `arch-docs/enderal-record-patterns.md` | Record shapes that build clean and do nothing in-game — the highest-value read before authoring |
| `arch-docs/zenderal-curation.md` | What is actually in the list and why |
| `arch-docs/zenderal-controller-setup.md` | Controller stack setup |
| **[`arch-docs/magic/`](arch-docs/magic/)** | **The actual in-game value of every magic record** — regenerate with the `magic-extract` skill |
| [`arch-docs/tools/spid.md`](arch-docs/tools/spid.md) | **SPID reference** for 7.3.x |
| **[`arch-docs/tools/spid-in-enderal.md`](arch-docs/tools/spid-in-enderal.md)** | **SPID in Enderal** — read before installing or authoring a `_DISTR.ini` (only 198/318 keyword entries register) |
| [`arch-docs/ordinator/`](arch-docs/ordinator/) | **Ordinator perk overhaul, studied for cherry-picking** — why it can't be installed in Enderal, which of its 469 perks are entry-point-only vs scripted |

Per pillar: combat patches start at [`arch-docs/enderal/combat.md`](arch-docs/enderal/combat.md),
visuals at [`visuals-and-world.md`](arch-docs/enderal/visuals-and-world.md), and anything touching
progression, potions or scripts at
[`progression-and-classes.md`](arch-docs/enderal/progression-and-classes.md) /
[`crafting-alchemy-economy.md`](arch-docs/enderal/crafting-alchemy-economy.md) /
[`scripting-and-actorvalues.md`](arch-docs/enderal/scripting-and-actorvalues.md).

Edit `.psc`/YAML, never the binary `.pex`/`.esp`. Commit source, not build artifacts.
