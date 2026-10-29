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
  **Exception (2026-10-21, list now on 1.7.104):** a patch that overrides or references a form with object
  ID **< `0x800` from a 1.71 light plugin** must itself be 1.71. A 1.7 plugin reads every sub-`0x800` ID as
  Skyrim.esm (TexGen: *"does not support form IDs < 0x800"*; FHR Parry Poise silently hit an AVIF).
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
| [`HalfStarlingDS`](arch-docs/patches/HalfStarlingDS.md) → `Zenderal - Half Starling DS Races.esp` | none | Restores per-race stats on `WoodElfRace 013749`. **Owns** the Qyranian racial ability `01EC66`: Half Starling's guard pointed at 2.0's `033898`, so 2.1 Qyranians got no cultural bonus; now `013748` (2026-10-27, unverified in game) |
| [`RiverBush`](arch-docs/patches/RiverBush.md) → `Zenderal - RiverBush.esp` | `0x800–0x81F` | 32 CK-placed bushes in Riverville; re-apply HEDR 1.70/ESL after any CK edit |
| [`SettingsApplier`](arch-docs/patches/SettingsApplier.md) → `Zenderal - Settings Applier.esp` + `.pex` | `0x800` | Re-applies save-based MCM settings once per save |
| [`FHRParryPoise`](arch-docs/patches/FHRParryPoise.md) → `Zenderal - FHR Parry Poise.esp` | none | FHR parry poise 20/5 → 60/40 so parries stagger |
| [`ChocolatePoiseEnderal`](arch-docs/patches/ChocolatePoiseEnderal.md) → `.esp` + `ZenCPRFactionFix.dll` | `0x800–0x808` | Vanilla-EditorID reference items for CPR + NSF crash fix |
| [`BrawlFixes`](arch-docs/patches/BrawlFixes.md) → two recompiled SureAI scripts | none | Brawls no longer break on magic/framework hits |
| [`NpcPotions`](arch-docs/patches/NpcPotions.md) → `Zenderal - NPC Potions_DISTR.ini` | none | SPID potions to NPCs; depends on NUP corpse-stripping being off |
| [`ControllerTweaks`](arch-docs/patches/ControllerTweaks.md) → controlmap, SkyUI config, `_00E_Game_SkillmenuSC.pex` | none | Gamepad fixes + B+D-pad-Up Hero Menu chord; **its `.pex` also carries KataPUMB New Affinities + Amnesia Shrine's edits** — it outranks their BSA copies |
| [`OldTempleWeather`](arch-docs/patches/OldTempleWeather.md) → `Zenderal - Old Temple Weather.esp` | none | Intro-beach weather under Obsidian (currently disabled with Obsidian) |
| [`BakaHeroMenu`](arch-docs/patches/BakaHeroMenu.md) | none | **Retired 2026-10-14** — source recoverable from commit `fa07b81`; its CommonLibSSE-NG clone moved to the repo-root `lib/` |
| [`TrueHUDCombatIcons`](arch-docs/patches/TrueHUDCombatIcons.md) → `ZenTrueHUDCombatIcons.dll` | none | FHR status icons inside TrueHUD's info bar |
| [`FrostAtronachSEFix`](arch-docs/patches/FrostAtronachSEFix.md) → converted meshes (not committed) | none | Black Ice Elementals: LE→SE meshes + plain lighting shader |
| [`PrecisionLiftFix`](arch-docs/patches/PrecisionLiftFix.md) | none | **Retired** — record of failed routes; source removed |
| [`PrecisionFork`](arch-docs/patches/PrecisionFork.md) → rebuilt `Precision.dll` | none | Floating Ice/crystal elementals fixed (PLANCK rigidBodyT hooks); impulse-off alone does NOT fix it; `0001` hooks re-found for 1.7.104 on 2026-10-27 (they had been inactive since the update: why the float came back; verified in game the same day); the winning copy is Patch Collection's; `0002` (keep knockdown ragdolls dynamic) was tried for the mid-air freeze and rolled back; GPL; rebuild per Precision update |
| [`ZenTraitsFixes`](arch-docs/patches/ZenTraitsFixes.md) → one recompiled script | none | Ambrosia reduces Arcane Fever again |
| [`LearningBooks`](arch-docs/patches/LearningBooks.md) | none | **Retired 2026-10-14** with Leveling Redone — books spend points again (EGO's records); source recoverable from commit `9afae18` |
| [`MCODirectionalPowerAttacks`](arch-docs/patches/MCODirectionalPowerAttacks.md) → `.esp` | none | Side/back/sprint power attacks reach FHR's MCO animations; fists sprint-attack too (FHR Brawler): `0F0A3E`/`0EC3CC` accept item type 0, **owns** Attack_MCO's `AttackRightH2H 0870D6` (+ not sprinting). Rebuilt copy ships as its own MO2 mod, sorted above Patch Collection (older copy). Unarmed part unverified in game |
| [`PrettyArmoryEGO`](arch-docs/patches/PrettyArmoryEGO.md) → `Zenderal - Pretty Armory EGO Patch.esp` | none | 141 Pretty×EGO merges. Generated. `tools/03` forwards each NPC's face from its face mod (Tealor `01ADF1` from Malphas' Blessing, which it masters since 2026-10-28) |
| [`ArkMyradPlatformFix`](arch-docs/patches/ArkMyradPlatformFix.md) → `Zenderal - Ark Myrad Platform Fix.esp` | none | Moves FS marker `02F0B5`; read the FS-override postmortem first |
| [`ArkMarketTreeFix`](arch-docs/patches/ArkMarketTreeFix.md) → `Zenderal - Ark Market Tree Fix.esp` | none | Lowers a floating juniper an addon placed in Ark's market |
| [`ArkBridgeOverhaulFixes`](arch-docs/patches/ArkBridgeOverhaulFixes.md) → `Zenderal - Ark Bridge Overhaul Fixes.esp` | `0x800–0x817` | Ark Bridge Overhaul fallout: Kata's Grappling Hook (Tier II) book (its crate was disabled) moved onto ABO's crate; Magical Symbol `037889` + light `03788C` (sealed inside ABO's wall gate) moved out; base curtains + a strip of water tiles hide the river's cell-border edge that ABO's low planks expose. Generated. Water verified in game; book/symbol unverified |
| [`EppiRivervilleStatues`](arch-docs/patches/EppiRivervilleStatues.md) → `Zenderal - EPPI Riverville Statues Patch.esp` | none | Moves a statue mod's bust with the desk EPPI moved |
| [`FeverDeathLatchFix`](arch-docs/patches/FeverDeathLatchFix.md) → recompiled `_00E_EPUpdateFunctions` | none | Clears the stuck `isdead` latch that blocks level-ups; forked from SureAI's source |
| [`UndeadCreaturesReplacerEGO`](arch-docs/patches/UndeadCreaturesReplacerEGO.md) → `.esp` | none | UCR visuals on EGO's Lost One NPCs. Generated |
| [`EnderalTextureRestores`](arch-docs/patches/EnderalTextureRestores.md) → extracted textures (not committed) | none | Restores Enderal textures a Skyrim texture mod cut out |
| [`PrettyFemaleMeshRestores`](arch-docs/patches/PrettyFemaleMeshRestores.md) → extracted meshes (not committed) | none | Pretty's BSA meshes over CBBE's loose ones; sort above CBBE |
| [`TerrainTextureSetFix`](arch-docs/patches/TerrainTextureSetFix.md) → `Zenderal - Terrain Texture Set Fix.esp` | none | Drops normal maps from two TXST height slots (ENB streaks); load after DynDOLOD.esp. `src/TerrainParallaxHeights/` is its failed first attempt |
| [`MissingParallaxHeights`](arch-docs/patches/MissingParallaxHeights.md) → generated flat `_p` textures | none | 289 missing parallax heights filled with flat grey |
| [`ArkWallCurbFix`](arch-docs/patches/ArkWallCurbFix.md) → Enderal's original meshes (not committed) | none | Undoes SRP's parallax on Ark wall meshes |
| [`ApocalypseNaviFix`](arch-docs/patches/ApocalypseNaviFix.md) → rebuilt Apocalypse `.esp` (hotfix) | none | Drops the `012FB4` NAVI that deleted a Forgotten Temple floor tile; retire once `enderal-mods` drops it |
| [`Prophecy`](arch-docs/patches/Prophecy.md) → `Zenderal - Prophecy.esp` + scripts + Ordinator/Subclasses assets | `0x800–0xB0E` (**masters `Aero.esl`, `KittySpellPack01/02.esl`, `Supernova.esl`** since 2026-10-27 - Kittytails' packs, see KittytailsPacksClean - **and `Shatterveil.esp`** since 2026-10-28 (its DLL runs the effigies/wyrm; installed without its SkyPatcher tome list, wyrm songs off in its ini); Druid's Twister `0xA9E`; Sorcerer tree `0xA9F–0xAB8`: their spells renamed for Enderal and repriced by override; Shatterveil's Blink Step is the root, a lesser power costing 35 Mana (`0xAE1`), Twin Effigies (sor6) climbs its tiers with Psionics (`ZP_SpellTierWatch` ability `0xADC–0xADD`; Bursting Effigy's `0xADA–0xADB` retired), Orbit Ward raised while casting (`ZP_CastWardEffect` `0xADE–0xADF`), Gravity Well absorbs 20 Health per enemy (`0xAE2` on Celestial Vortex's hazard spell `000826`), the shout's slow time moved onto Enderal's `13FB41` (Shatterveil's vanilla `048ACD` is missing) and the curator's glass-impact `.wav` as its words' Release sound `0xAE0` (Shatterveil's own wyrm sounds are silent on 1.7.104), Blink Step 20 Mana, Veil Wyrm shout capstone (menu teaches all words) carrying Mana Burn's buff (marker `0xAB6`, restore `0xAD3`, aura `0xAD7`, half-cost perk entry; no fever); Mana Burn's spell/power `0xAB5`, `0xAB7–0xAB8` retired, never reuse; Drowning Orb drain `0xAD4`; Drowning Orb's player regen is a script ability `0xAD5–0xAD6` (the orb hazard never hits its caster); Ice Shot is a shout talent `0xAD8`–`0xAD9` with Flame Shot's 110 s cooldown (menu grants it, takes back the old power); Drowning Orb is Elementalism + frost keyword, 39 Mana; Rage tree `0xAB9–0xAD2`: stacks counted by `ZenProphecyRage.dll` (`src/Prophecy/rage`, TESHitEvent - never ApplyCombatHitSpell, EGO/Enderal already use it), A Dark Warrior's Tale actions by power-attack direction, Vehemence capstone, meter = Oxygen Meter 2's SWF in our own menu; 140 talents, past 128 - `ZP_ProphecyMenu.Refresh` warns in game if the arrays were cut; Shadow tree `0xA6E–0xA81`: Triumvirate's Shadow spells granted by the menu, Shade Veil `0xAE6–0xAE9` (mist + 50% harder to detect while sneaking), Darkness `0xAEA–0xAEC` (`ZenProphecyDarkness.dll`, `src/Prophecy/darkness`: fills in darkness, pays for the Shadow spells instead of Mana, Nightfall = full meter, no fever), Darkness talent `0xAED–0xAF2` (copied Triumvirate Darkness spell with a dark-mist hazard), Nightblade on Darkness `0xAF3–0xAF4` (**owns** Triumvirate's proc `335B4F`: Mana drain off for tree users; dash hits spend half the Darkness, +15 damage a point), Martial Arts' Invoker (was Dragon's Breath) `0xAF5–0xB01` (every 5th unarmed hit, `ZenProphecyRage.dll` 1.1.1 casts a random fireball explosion, Ice Shot freeze or chain lightning on the enemy; Flow State's nova adds chain lightning `0xB02`), Nightfall a 50%-fever power through `ZP_WrathGate`; Druid tree `0xA82–0xA9D`: Triumvirate Druid/Shaman spells, Force of Nature = Horned Lord form + 4 familiars (the player's own SkinNaked is swapped for the form's skin: `ZP_ForceOfNatureEffect.FormSkin`; **owns** the race `000837:Triumvirate` (XPMSE male skeleton) and the 3 totem MGEFs `3BE79E`/`3C89CF`/`35E36C` (Elementalism), and the 14 `TVR_Tomes_Litem_*` LVLIs holding granted spells' tomes (incl. Druidcraft + Force of Nature since 2026-10-29) (taken out: granted spells are not sold)), stat talents hand-placed via `HAND_STATS`; point-gained sound `0x9B0`–`0x9B1`; v3 selection notes `0x9B2`–`0x9C3`; 42 stat talents `0x9C4`–`0xA19`: 6 per tree, a point every 3 levels, 30 max; Kittytails' Holy Templar Magic copied + rebalanced `0xA1A`–`0xA62`, with permission; Faith rework records `0xA63`–`0xA6C`; Chaff `0xA6D`, LATE_NODES) | Utility Droid is thrown (Starling Dummy talent chain copied, `0x9AA–0x9AE`; no navmesh snap: PO3's `MoveToNearestNavmeshLocation` jumps to the nearest navmesh **vertex**) and heals through a spell `0x9AF` for Enderal's heal shimmer. Necromancy (seventh tree, 2026-10-23, `0x992–0x9A9`): Corpse Fever (summon limit +1 per 25% fever, all summon kinds), Dark Effigy (a spell, granted by the menu), A Willing Sacrifice (summons explode for half their base Health, SureAI's Corpse Explosion rule; 15 s cooldown), The Dead Don't Forget, Legion of the Damned (six placed skeletons, 50% fever via `ModAV LastFlattered`). Ice Shot freezes on the arrow's **hit** (watcher ability + hit trigger + target-delivered freeze spell, `0x987–0x98E`): its explosion missed big creatures and its effect ended early. **Masters Triumvirate** (since 2026-10-23: Andrasta's Owl's bird `0x97F` is Triumvirate's raven creature wearing `BarnOwl.nif`, Mihail's owl re-rigged onto its skeleton by `tools/05`; Mihail's Barn Owls itself is only scenery). Arcane Archery (sixth tree, 2026-10-23: Arcane Arsenal, No Distractions casts the list's Spell Ward (Rank II), Ice Shot with Arctic Wind's freeze, Andrasta's Owl (Mihail's Barn Owl mesh re-rigged onto Triumvirate's raven creature by `tools/05`, silent, script-flown, drains Magicka to the player, stays until killed), Arcane Echo (Ordinator's Lion's Arrow, renamed)) allocated after everything else, `0x94E–0x97B`; **bows only** (item type 7). Firearms (was Sharpshooter; Druid → Druidic, Sorcerer → Sorcery, 2026-10-27) is **muskets only** (item type 12; Quick Reload's own ability `0x97C`). Five older trees (Faith, Sharpshooter, Gadgets, Martial Arts: 5 perks; Glory: 5 — 4 at `0x916–0x924`, Seismic Stomp `0x92F–0x939`, Surrounded `0x93A` (was Death or Glory; ability `0x93B`–`0x93C`; late IDs append last, `GLORY_LATE_NODES`); Flow State's Shock Nova explosion + enchantment `0x93D`–`0x93E`; Utility Droid (Gadgets 3, was Bear Traps; perk `0x81C` kept) `0x93F`–`0x947`; Deadeye shares the gun hit spell `0x910` (one `ApplyCombatHitSpell` per hit), with its trigger sound `0x948`–`0x94A` and Bleeding Shot's `0x94B`–`0x94D`; `0x91A–0x91D` retired, never reuse); power sounds `0x927–0x92E`, all `.wav`s not committed: `tools/03-install-sounds.py` from Ordinator + Subclasses of Skyrim 2, bought through Enderal's UIExtensions list menu from the Prophecy lesser power; points at levels 5/10/15/20/30 then every 5 (max 20), each with a flavour-text prompt on level-up (`ZP_ProphecyMenu` listens for `MessageBoxMenu` closing; hand-written quest `ZP_ProphecyLevelWatch 0x80E` hooks it on existing saves at load; a once-per-save ledger repair fixes saves hit by the unbound-counter bug). Quick Reload + Rapid Shot stack via the generated OAR mod `Zenderal - Quick Reload Stack` (`tools/04`, both-perks condition, clips 1.3x shorter). **Not CSF** — Skyrim's perk screen doesn't work in Enderal 2.1. Non-ESL. Generated (`tools/01`). Unverified in game |
| [`ShatterveilAE`](arch-docs/patches/ShatterveilAE.md) → patched `Shatterveil.dll` + generated `versionsvl-1-7-104-0.bin` (not committed) | none | Shatterveil 1.3.1 (closed, 1.5.97-only) on 1.7.104: its NG called minor 7 "SE" (`failed to open address library file`). Byte patch: runtime switch 6→7, versionlib path → `versionsvl`, plus the format-5 library re-encoded as format 2; its old NG logger's missing 1.7 ID `380738` ("My Games" folder name) replaced by an inline string. MO2 mod directly above Shatterveil. Rerun `tools/01` after a Shatterveil update; ask the author before shipping. Unverified in game |
| [`ProphecyV2`](arch-docs/patches/ProphecyV2.md) → same `Zenderal - Prophecy.esp` (second archive) + sanctum | `0xC00–0xD37` (+ v1's) | **A/B test vs v1.** Prophecy power teleports into a walk-in sanctum built from Enderal's meditation (Akropolis) pieces; the four trees hang as constellations of Enderal stars/lines/nodes. Generated from the v1 build. Unverified in game |
| [`ProphecyV3`](arch-docs/patches/ProphecyV3.md) → same `Zenderal - Prophecy.esp` (third archive) + `ZenProphecyUI.dll` | none (v1's) | **A/B test vs v1/v2.** The Prophecy power opens an SKSE Menu Framework window that draws each tree as a website-style constellation (generated symmetrical layout, `tools/01-build-layout.py` → `ZenProphecyUI.json`); learning goes back to v1's `ZP_ProphecyMenu.TryLearn` via mod event `ZP_ProphecyLearn` (the script switches on `SKSE.GetPluginVersion("ZenProphecyUI")`). Unverified in game |
| [`MenuFrameworkFutura`](arch-docs/patches/MenuFrameworkFutura.md) → generated `SKSE/Plugins/Fonts/MainFont.ttf` (not committed) | none | Curator's taste: SKSE Menu Framework windows (Prophecy v3, Local Map Upgrade, its panel) in regular Futura Book BT, converted from Vel'dun UI's `fonts_futura.swf` (SMF reads 0 faces from it). The list's SMF ini already asks for `MainFont.ttf`. Rerun `tools/01` after a Vel'dun update. Unverified in game |
| [`ImprovedCameraSheatheFix`](arch-docs/patches/ImprovedCameraSheatheFix.md) → `ZenICSheatheFix.dll` | none | NOPs IC's drawn-weapon camera drop; tied to IC 1.1.2.4228 |
| [`BlockReleaseFix`](arch-docs/patches/BlockReleaseFix.md) → `ZenBlockReleaseFix.dll` | none | Ends blocks DWP's dropped key-up left stuck on. 1.0.2 decodes gamepad DWP keys (LT = `ParryKey2 280`): 1.0.1 ended LT blocks every 500 ms. Also shipped inside Patch Collection |
| [`OCPASecondKey`](arch-docs/patches/OCPASecondKey.md) → `ZenOCPASecondKey.dll` + ini | none | A second One Click Power Attack key (default RT 281) next to OCPA's own (Mouse 4): on its press, OCPA's rules read from `OCPA.ini` and OCPA's actions (`ActionRightPowerAttack 0x13383` via ID 41557; attack-then-power-attack when jumping/blocking). OCPA untouched (its source is unlicensed). Unverified in game |
| [`CrossbowSprintSwap`](arch-docs/patches/CrossbowSprintSwap.md) → OAR `user.json` + two copied clips | none | Curator's taste: crossbows/muskets get only Tactical Crossbow Movement's sprint, plus Zodd's standing idle |
| [`CrossbowDrawFix`](arch-docs/patches/CrossbowDrawFix.md) → `ZenCrossbowDrawFix.dll` | none | Resets the `kBowAttached` a cut-short crossbow draw leaves (no sprint/sheathe until a shot) |
| [`HorseCloakFluffFix`](arch-docs/patches/HorseCloakFluffFix.md) → `.esp` + generated meshes | none | Fluffworks fur trimmed under the Ark guard horses' barding |
| [`DintHairs`](arch-docs/patches/DintHairs.md) → rebuilt Dint999 hair plugins | none | Hairs only, no wigs; +2 full plugin slots |
| [`GuardFalconer`](arch-docs/patches/GuardFalconer.md) → `Zenderal - Guard Falconer Patch.esp` | none | Restores Falconer cuirass/helmet that Pretty Factions reverted |
| [`MoonsteelPretty`](arch-docs/patches/MoonsteelPretty.md) → `.esp` + 2 loose meshes | none | Points EGO's Moonsteel line back at Pretty's meshes. Generated |
| [`FlintlockOverhaul`](arch-docs/patches/FlintlockOverhaul.md) → `.esp` + script + DAR recipes ESL + KID + icons | `0x800–0x81A` | Pistols use bullets and reload — incl. Loop's 4 Hunter Pistols (his 4 soul-gem Hunter Crossbows' recipes hidden); Silver Musket Balls ride EGO's silver-arrow ghost perks; 111 NPCs rebuilt over gun mods; **owns** the 14 `0?E_Beute*`/`Kampfitems` chest-loot LVLIs (gun ammo added), Loop's 8 gun recipes and trader blueprint list `137A06` (pistol blueprints added, EGO + Crossbows merged); load after Enderal SE - Crossbows |
| [`FlameShot`](arch-docs/patches/FlameShot.md) → `Zenderal - Flame Shot.esp` + recompiled `_00E_A1_FireArrowSC` | `0x800–0x802` | Fire Arrow talent renamed Flame Shot; with a musket it grants exploding Flame Musket Balls and restores the old ammo. Generated |
| [`DragonPriestStaffSwap`](arch-docs/patches/DragonPriestStaffSwap.md) → loose meshes (not committed) | none | Curator's taste: Pretty's chain-lightning staff mesh at the Dragon Priest staff paths |
| [`StaffDrawFix`](arch-docs/patches/StaffDrawFix.md) → OAR submod with vanilla clips | none | Staff draw plays again over Smooth Magic Casting's always-true equip |
| [`LoopPistolAnims`](arch-docs/patches/LoopPistolAnims.md) → OAR mod with Loop's clips (not committed) | none | Loop's pistol anims re-ranked above Goetia Enchanted Staves (unconditional 68000) and Smooth Moveset; matches the 8 pistols by form; ships rotated pistol meshes the Flintlock Overhaul's FirstPersonModel statics point at — the static is the equipped model in 3rd person too (right hand: mirrored clips, `tools/mirror_hkx.py`) |
| [`IchorGooNoGlow`](arch-docs/patches/IchorGooNoGlow.md) → generated meshes (not committed) | none | Curator's taste: JS Ichor puddles without their particle haze + ENB light. Sort above JS in MO2 |
| [`SilentPowerAttackGrunts`](arch-docs/patches/SilentPowerAttackGrunts.md) → 8 loose `.fuz` (not committed) | none | Curator's taste: female player power-attack yells silenced; other grunts kept |
| [`NoScreenFlashes`](arch-docs/patches/NoScreenFlashes.md) → `Zenderal - No Screen Flashes.esp` | none | Curator's taste: drops full-screen blur/white-flash ISMs from enemy abilities (Wood Elemental call `0E41F1`) and the poison blur (`PoisonHitImod`/`PoisonEndImod`) from all 27 winning poison effects (generated, `tools/01`). The standalone mod must be enabled and sort ABOVE `Zenderal - Patch Collection`, which ships an older copy |
| [`EnderalPairedAnims`](arch-docs/patches/EnderalPairedAnims.md) → Pandora-native patch `Pandora_Engine/mod/zpaired` | none | Enderal's 6 FNIS `pa`/`km` scenes (Calia MQ07b, hugs, kisses) re-added to Pandora's 0_master. Generated |
| [`DBVOPlayerLipSync`](arch-docs/patches/DBVOPlayerLipSync.md) → `ZenDBVOLipSync.dll` + CCC `SD_user.ini` | none | Player mouth plays each DBVO line's real `.lip` (file = XXH64 of the prompt); CCC's letter-guessed fallback off (`[Performance]`, not `[Direction]`). Unverified in game |
| [`DBVOSexDefaults`](arch-docs/patches/DBVOSexDefaults.md) → `ZenDBVOSexDefaults.dll` + male/female JSON | none | New game starts with the player voice silent (1.2.0, `silent.json` = male at volume 0); chargen switches to male ("Gary") or female ("Mer"); calls DBVO.dll `+0x2AC20`, pinned to 2.0.2.2 (TimeDateStamp `0x6AB06DCE`). The writable `default_options.json` lives in `Zenderal - Settings`: keep it = male.json before compiling. 1.1.0 unverified in game |
| [`CCCStandDown`](arch-docs/patches/CCCStandDown.md) → `ZenCCCStandDown.dll` | none | CCC stays out of memory scenes (player shrunk/child race/faded: MQP01 Daddy, MQP03 vision) by holding SmoothCam's camera, which CCC then declines to take. Verified in game (MQP01) |
| [`GamepadCombos`](arch-docs/patches/GamepadCombos.md) → `ZenGamepadCombos.dll` | none | 1.5.97 ignores gamepad combo modifiers (CCS: LB sheathed, D-pad Down opened the map); re-picks each press's event from the held buttons using controlmap.txt + ControlMap_Custom.txt. Unverified in game |
| [`Fuse00ArmorRaces`](arch-docs/patches/Fuse00ArmorRaces.md) → `Zenderal - Fuse00 Armor Races.esp` | none | Adventurer armor visible on Half Arazealean/Qyranian (`033899`/`033898`, not vanilla `013746`/`013748`); Helga deliberately not covered (no Helga master). Generated. **Redundant on Enderal 2.1** (playable races moved to `013746`/`013748`) |
| [`EGO21Compat`](arch-docs/patches/EGO21Compat.md) → `Zenderal - EGO 2.1 Compatibility.esp` | none | Enderal 2.1 moved the playable Half Arazealean/Qyranian to `013746`/`013748`; EGO still makes the old `033899`/`033898` playable (duplicate races). **Owns** all four RACEs: DS Unique Races' record on the new ones, minus Playable on the old. Must load after DS Unique Races. **Owns** the 4 EGO-won ARMAs that lost 2.1's races (`145879` Righteous Path boots, `14587A`, `0E35C7`, `14483D`; invisible on the player; `tools/00` scans the load order). EGO's 75 NPC / 1 FLST old-race refs not yet remapped. Generated. Unverified in game |
| [`GrassLightingFix`](arch-docs/patches/GrassLightingFix.md) → generated meshes (not committed) | none | Enderal 2.1.4's own shadow-glow fix (Emissive Multiple 1.0 → 0 on black-emissive grass/flora, = Fixed Mesh Lighting merged) applied to the winning loose grass meshes of Enderal Grass Redone and its requirements (297 meshes). Byte-identical to SureAI's edit on Enderal's meshes. Sort directly above EGR; re-run after any grass mod change. Unverified in game |
| [`TextureRename21Fix`](arch-docs/patches/TextureRename21Fix.md) → generated textures (not committed) | none | Enderal 2.1 renamed 4 TXST normal paths to `_n` (Sand01/02, MossRock, CrystallPlant01); copies a 2.0 retexture's old-name normal to the new name when it outranks the new name's winner (SRP sand + moss rock over ETATU). Sort above all texture mods; re-run after texture mod changes. Unverified in game |
| [`SuraClaymoreFix`](arch-docs/patches/SuraClaymoreFix.md) → `Zenderal - Sura Claymore Fix.esp` | none | **Owns** Sura's chest `05BCD7`; merges SureAI's duplicate Iron Claymore entry (suspected buy-4/sell-crash with Item Stacking Tweaks). Unverified in game |
| [`RaySensePriority`](arch-docs/patches/RaySensePriority.md) → OAR `user.json` only | none | Curator's taste: RaySense Cover (2140000000+) and both wall-lean mods (2130000000+) above every competing OAR set; Sonder's shipped at 7005000 and could never win. Generated. Unverified in game |
| [`ReversalShadow`](arch-docs/patches/ReversalShadow.md) → `Zenderal - Reversal Shadow.esp` + generated meshes/texture | `0x800–0x808` | Black-and-silver Priest's pistol (laser shot sound) whose shot also casts Triumvirate's Witch Bolt; Eldritch Blast +20 on a Witch-Bolted target; one placed on the Old Crosswatch shelf (cell `001F20`). **Owns** `ZP_FlintlockWeapons 000802`, Eldritch Blast `19B465`/`419B32` and cell `001F20`'s header — rerun its `tools/02` after the Flintlock list or Magic Patches changes. Generated. Unverified in game |
| [`PerpetuumTheaterEVGATFix`](arch-docs/patches/PerpetuumTheaterEVGATFix.md) → `Zenderal - Perpetuum Theater EVGAT Fix.esp` | none | Disables EVGAT_Enderal's plank/post `0009CC`/`0009CD` (floating over the rebuilt theater corner) and collision planes `0009CA`/`0009CB` (invisible walls in its courtyard), which the theater's own EVGAT patch skips. Generated. Unverified in game |
| [`EppiRivervilleCobbleRemoval`](arch-docs/patches/EppiRivervilleCobbleRemoval.md) → `Zenderal - EPPI Riverville Cobble Removal.esp` | none | Curator's taste: EPPI Riverville's 98 raised cobble plates (`029B46`) disabled across 7 Riverville cells. Load after Water for Enderal CS. Generated. Unverified in game |
| [`LastWatchTrapdoorFix`](arch-docs/patches/LastWatchTrapdoorFix.md) → `Zenderal - Last Watch Trapdoor Fix.esp` | none | Ark's Last Watch tower top can be climbed down again: Last Watch lowered trapdoor `1043D6`, ladder exit `1042FD` and clutter under EPPI Improved Locations' plank floor `035BE3`; placements back to EPPI/base. Load after Water for Enderal CS. Generated. Unverified in game |
| [`NoLightningFlash`](arch-docs/patches/NoLightningFlash.md) → `Zenderal - No Lightning Flash.esp` | none | Curator's taste: lightning off (thunder fade-in/out 0 + black `LightningColor`) on the 13 weathers True Storms gives lightning; a strike re-aims and tints the sun light, so the sun 'jumped' (intro beach). **Disabled 2026-10-20: True Storms removed instead.** The real cause is True Storms' thunder sounds (each clap fires a strike); colour/fades can't stop it |
| [`Levelsystem21Cleanup`](arch-docs/patches/Levelsystem21Cleanup.md) → `Zenderal - 2.1 Levelsystem Cleanup.esp` | none | Drops refs to 2.1-deleted quest Levelsystem `010AA2` from 92 winning 2.0-era records (EGO, Pretty Unique Sets, Kata Hidden Powers, Castle Bleakstar, house mods…) exactly as base 2.1 did — DynDOLOD's `Unresolved FormID [00010AA2]`. **Load LAST; regenerate when any of its 11 masters changes.** Generated |
| [`QyraIslandEditorIdFix`](arch-docs/patches/QyraIslandEditorIdFix.md) → `Zenderal - Qyra Island EditorID Fix.esp` | none | 2.1 renamed WRLD `00A6A0` to `FSNQ01QyraIsland`; Ships of the First Vassals (2.0) reverts it, which stops DynDOLOD. Ships' header with 2.1's EditorID. Load after Ships. Generated |
| [`UnresolvedRefsCleanup`](arch-docs/patches/UnresolvedRefsCleanup.md) → `Zenderal - Unresolved References Cleanup.esp` | none | Removes 529 refs to forms nothing defines (Skyrim/DLC leftovers in ported mods: Apocalypse, Dynamic Impact, Deflection, AOS…) from 219 winning records, so xEdit/DynDOLOD load clean. **Load LAST; regenerate (tools 00a→00b→01) when a winning plugin changes.** Generated |
| [`IronGolemClean`](arch-docs/patches/IronGolemClean.md) → generated cleaned `mihailirongolem.esp` (not committed) | none | Mihail's Iron Golem (a Skyrim mod) redefines Enderal refs `021EDB`/`091872` as a worldspace/cell (type collision, CTD risk); Steel Warden Replacer - EGO masters it, so a same-name copy minus its 9 Skyrim cell/worldspace records sits above the original in MO2 |
| [`KittytailsPacksClean`](arch-docs/patches/KittytailsPacksClean.md) → generated cleaned `Aero.esl`, `KittySpellPack01.esl`, `Supernova.esl` (not committed) | none | Kittytails' spell packs, installed (not copied) for Prophecy's Druid (Abyssal Wind), Sorcerer (Obscure, Elemental Mastery, Constellation) and Rage (A Dark Warrior's Tale - a full .esp: its quests, dialogue, worldspace, cells and NAVI `012FB4` dropped). Same-name copies, cut at the binary level (Aero's test cell stops Mutagen), each in its own MO2 mod ABOVE its original: Skyrim cells/worldspace and an NPC whose IDs are placed refs in Enderal (Aero `016DF2`; Obscure 7 cells, `00003C` = MQP01Home, NPC `09D257`) and Constellation's `fWeatherTransAccel` 4→16. Install the originals WITHOUT `*_DISTR.ini` and plugin `.ini` (particle limit 22000→9750). Rerun `tools/01` + re-serialize into `reference/mods/` after a pack update. Unverified in game |
| [`RageEffectsRecolor`](arch-docs/patches/RageEffectsRecolor.md) → generated meshes + textures (not committed) | none | Curator's taste: Prophecy's Rage actions (A Dark Warrior's Tale meshes) red/orange instead of pink/purple. Their palette paths repointed `gradients` → `gradientz` (same length) and those 23 palettes recoloured from the winning copies (Glorious Gradients), so vanilla spells keep theirs. Rerun `tools/01` after Glorious Gradients or the pack changes. Unverified in game |
| [`BiggieTraits171`](arch-docs/patches/BiggieTraits171.md) → generated same-name `Biggie Traits.esp` (not committed) | none | Biggie Traits' 148 sub-`0x800` records at HEDR 1.70 stopped DynDOLOD (xEdit reads them as Skyrim.esm forms; in game they worked). Copy = original with only the HEDR float 1.70 → 1.71, in MO2 mod *Biggie Traits - HEDR 1.71 (Zenderal)* above the original. **Every plugin mastering Biggie must be 1.71** (Zen Traits is; Zenderal - Traits rebuilt at 1.71). Rerun `tools/01` after a Biggie update. Unverified in DynDOLOD/game |
| [`KataAffinities21`](arch-docs/patches/KataAffinities21.md) → `Zenderal - KataPUMB Affinities 2.1.esp` + `_00E_AffinityControl.pex` | none | KataPUMB's 24 affinities on Enderal 2.1: ported into 2.1's `_00E_AffinityControl` (`_GetScriptVersion` stays 1); **owns** `AffinityControl 01597B` (FS + 72 Kata properties). Needs the cleaned Kata copy `tools/02` generates (no `010AA2`, no skill-menu `.pex`); `tools/04` checks the Levelsystem popup's triggers. Generated. Unverified in game |
| [`LostOneSalletFix`](arch-docs/patches/LostOneSalletFix.md) → generated mesh (not committed) | none | Plated Lost One's sallet + strap hidden: Lost Ones Revised never shipped their `Plated Lost One` textures (purple). Sort above Lost Ones Revised. Unverified in game |
| [`LostOnesDismembering`](arch-docs/patches/LostOnesDismembering.md) → `Zenderal - Lost Ones Dismembering.esp` + DF JSON + generated limb meshes (not committed) | `0x800–0x832` (`0x833–0x83A` reserved) | DF only knew `DraugrRace`/`WolfRace`: UCR's `LostOneTemplateRace` gets DF's draugr limbs, Lost Ones Revised's skeleton races get skeleton limbs cut from Mihail's mesh, Enderal's `WolfRaceLarge`/`WolfRaceSmall`/`WolfHoheRace` get DF's wolf limbs, both minotaur races get per-skin limbs cut from their outfits (`0x805–0x832`). Spiders shelved (DF rebuilds the Spider SE corpse, ~8 s blink). **Owns** DF's 5 draugr + 18 wolf body-cap ARMAs; load before the Fluffworks DF patch. Generated. Verified in game (Lost Ones, wolves, minotaurs) |
| [`ArpDismembering`](arch-docs/patches/ArpDismembering.md) → `Zenderal - Arp Dismembering.esp` + DF JSON + generated limb meshes (not committed) | `0x800–0x818` | Arps drop limbs cut from the bodies they render: `Enderal Arp` (`Enderal - Arp.esp`) overrides all 7 Falmer body ARMAs with Enderal's swamp-race meshes (dark skin, red eyes, green dreads), so DF's pale Falmer limbs never matched. 25 limbs (5 per body: 2 forearms, 2 calves, head with eyes/hair) from the winning `swamp_hunter`/`_warrior`/`_v2`/`_v4`/`swamp_shaman`, inside DF's naked male Falmer limb nifs; DF's Falmer caps. Ships DF's `OfficialCreaturePack_Falmer_DATA.json` at its own path with FalmerRace rebuilt (7 skins + ANY; flesh construct `149709` keeps DF's limbs): **the MO2 mod must outrank `DF - Official Creature Asset Pack`; plugin loads after `DF - Official Creature Pack.esp`.** Rerun tools 01→02 after Enderal Arp, a mesh override (PG Patcher, ETATU) or DF's pack changes. Generated. Verified in game (leg + head look right); one unexplained crash on a head cut, log lost |
| [`FrostSpiderMotherFix`](arch-docs/patches/FrostSpiderMotherFix.md) → `Zenderal - Frost Spider Mother Fix.esp` | none | Frostkrabblermutter `0E430A` visible again: EGO moved it to `FrostbiteSpiderRaceLarge` but its giant cold skin's ARMA `02C17F` only rendered for Giant; adds Large as an additional race. Unverified in game |
| [`MaceSpeed`](arch-docs/patches/MaceSpeed.md) → `Zenderal - Mace Speed.esp` | none | 1H maces Speed 0.8 → 0.9 (axe parity) on EGO's 22 winning records; other 4 list maces left alone. Rerun `tools/00`+`01` after EGO or a mace mod changes. Generated. Unverified in game |
| [`OldCemeteryCryptFix`](arch-docs/patches/OldCemeteryCryptFix.md) → `Zenderal - Old Cemetery Crypt Fix.esp` | none | Old Cemetery house `016A98` back on `SStyrrsHouse 037F05`: ETATU CM Fixes re-bases it onto `SStyrrsHouse ark`, a mesh no ETATU archive ships, so only the crypt door stood. Masters ETATU CM Fixes. Generated. Verified in game |
| [`Goblins`](arch-docs/patches/Goblins.md) → `Zenderal - Goblins.esp` + respawn `.pex` + generated meshes (not committed); `Zenderal - Goblins Dismembering.esp` + DF JSON + generated limb/cap meshes | `0x800–0xB29`; Dismembering `0x800–0x836` | Curator's taste: goblins as their own creature (`ZEN_GoblinRace`, copy of FalmerRace; **requires** the Goblins mod, never edited) and Arps look like Arps again (vanilla Falmer bodies from `Skyrim - Meshes0.bsa`, mod sorts ABOVE Goblins). 78 packs / 492 weak goblins (78% Mihail's) + 50 durzogs, none near the MQ01 opening (Finn, Carbos, Jespar's camp), all on iron weapons (health, armor and resists cut 35% on 2026-10-21); Mihail's goblins dismember too (humanoid limbs) (ours mixed with Mihail's, copied in from the disabled `mihailgoblins.esp`) placed on navmesh across Vyn, never in the Crystal Forest; back 3 days after death (`ZEN_GoblinRespawn`, global `0x820`). Forwards the WRLD + 80 cell headers from their last overriders: **load right after the last Vyn cell editor (Golden Mare Mill SE, 2026-10-21); rerun tools 02+03 when one changes**. Dismembering plugin loads right after it. Generated. Unverified in game |
| [`EnemyDensity`](arch-docs/patches/EnemyDensity.md) → `Zenderal - Enemy Density.esp` | `0x800–0xD9B` | Curator's taste: 922 extra enemies in 187 groups, built only from creatures Enderal places in each region (or Goblins' goblins): Fogville goblin packs + Arp camps, Whisperwood hordes of weak undead (**never Mihail skeletons**: two IED weapon-attach crashes in the hordes; `02` refuses them), Powder Desert, Crystal Forest, Frostcliff, Thalgard, Goldenforst, Western Cliff. No site within 3000 of quest-named refs, trigger boxes or any persistent placed NPC. Tables = `REGIONS` in `tools/01`. Forwards Goblins' WRLD/cell headers: **load right after Goblins Dismembering; rerun tools 01+02 whenever Goblins' 02+03 are rerun.** Generated. Unverified in game |
| [`MusketHandling`](arch-docs/patches/MusketHandling.md) → `ZenMusketHandling.dll` | none | Muskets slower to use, bows untouched: TK Dodge's `TKDodge*` events dropped for 2.3 s after a musket shot and for as long as the musket is still firing/reloading (cap 5 s) — the list's TK ini allows attack-cancel dodges, so fire → dodge → fire skipped the reload; aiming a musket costs 35 SpeedMult. "Musket" = crossbow-type WEAP from `OrdoLegionisMuskets.esp` (ini). Unverified in game |
| [`TriumvirateSEMeshes`](arch-docs/patches/TriumvirateSEMeshes.md) → converted mesh (not committed) | none | **Retired 2026-10-28, not the cause** (mod moved to `E:/Zenderal-backups`): Triumvirate's Horned Lord body LE → SE through PyNifly. The invisible form was the player's own skin (`SkinNaked`), fixed in Prophecy's `ZP_ForceOfNatureEffect.FormSkin` |
| [`ZarAhTextureFix`](arch-docs/patches/ZarAhTextureFix.md) → copied textures (not committed) | none | Zar'Ah's hair and scars back: Malphas' Blessing's facegen asks for `textures\MB\F\mbZar'ah\`, the mod ships `mbZarah\` (bald head, dark-blue face plate). Sort above Malphas' Blessing. Generated. Unverified in game |
| [`ArkGateSiegeFix`](arch-docs/patches/ArkGateSiegeFix.md) → `Zenderal - Ark Gate Siege Fix.esp` + 2 scripts | `0x800–0x801` | **Enderal 2.0 (old release) only — never ship with 2.1.** Black Light siege: Ark City Gate Consistency Patch rebuilds Castle Quarters gate `09EECD` on 2.1's record, dropping 2.0's `InheritedAndRemoved` on `_00E_ChestAndDoorLockScript`, so the quest's gate says it needs a key. Restores it (new games), plus a hidden perk (SureAI `0493DB`'s shape) that opens `09EECD` with `Activate(player, true)` during MQ12b 5–125, given by a start-game quest, because **saves keep a script removed in a plugin**. Load directly after the gate patch. 2.1 exempts the gate by ref ID in perk `0493DB`. Generated. Unverified in game |
| [`GroundCoverAlphaFix`](arch-docs/patches/GroundCoverAlphaFix.md) → generated meshes (not committed) | none | Tropical ground cover (`088CF2` + sibling, Starling city) drew as light-green squares: ETATU's 2x upscale left its `coverground01/02.dds` background at alpha 1–15 and the meshes alpha-test at threshold 0. Fixed Mesh Lighting's two meshes with threshold 128. Only visible case among 30,883 winning meshes. Sort above Fixed Mesh Lighting. Generated. No squares seen in game with it on (not A/B-checked) |
| [`PusBeetleFixes`](arch-docs/patches/PusBeetleFixes.md) → `Zenderal - Pus Beetle Fixes.esp` + generated `skeleton.nif` (not committed) | none | Pus beetle (chaurus) ranged hits register: Pus Beetle Replacer's kwama body stuck out of the chaurus hit capsules (22.6% of it > 10 units out; vanilla 3.1%), so capsules grown to fit (0.1%). Spit no longer knocks back: EGO's `XionParalyzeKnockback` dropped from `crChaurusPoisonSpit01 06F6FE` (owns it; load after EGO). Mod sorts above Pus Beetle Replacer. Generated. Unverified in game |
| [`AimFacingLock`](arch-docs/patches/AimFacingLock.md) → `ZenAimFacingLock.dll` | none | While aiming a bow/crossbow/musket in third person the body faces the camera every frame (W+A swung the weapon off the crosshair; not TDM). Logs heading drift. Unverified in game |
| [`PerkOverhaul`](arch-docs/patches/PerkOverhaul.md) → `Zenderal - Perk Overhaul.esp` + `.pex` | `0x800–0x8FF` | Class perk rework on top of EGO, one class at a time. Blade Master `069D52`: crit +25 (EGO +10), sword/dagger crits heal 10 via PE `OnCriticalHit`. 13 Trickster archery MESGs name muskets (text only; generated `tools/01`). Replica `069CD6`: +30% per bow/musket hit to drop one ammo on the target (PE `OnWeaponHit`). **Owns** each reworked PERK and its Hero Menu MESG (change both). Needs powerofthree's Papyrus Extender; load after EGO. Unverified in game |
| [`TraitsRework`](arch-docs/patches/TraitsRework.md) → `Zenderal - Traits.esp` | `0x800–0x88F` | 18 Enderal-specific traits (perk entry points + stat effects; Gunslinger: pistols +35%, melee −25%, 50% bullet drops from humanoid enemies, Arps and goblins) replace Biggie's own in the trait menu; Zen Traits' 9 stay via its FLM ini. Also ships Biggie's `Traits_Utils.pex` with the two menu natives rewritten in Papyrus (Biggie's `Traits.dll` is hidden on 1.7.104, so the menu opened empty); must outrank Biggie Traits in MO2. **Owns** `Traits_AbilityList 000002:Biggie Traits.esp`. Masters `Zenderal - Flintlock Overhaul.esp` (Gunslinger's pistol keyword/bullets) and `Zenderal - Goblins.esp` (Goblin Slayer targets its goblin races + FalmerRace Arps). HEDR **1.71** (2026-10-23), paired with Biggie's 1.71 copy ([`BiggieTraits171`](arch-docs/patches/BiggieTraits171.md)). Generated. Unverified in game |
| [`StancesNoIcon`](arch-docs/patches/StancesNoIcon.md) → `Zenderal - Stances No Icon.esp` | none | Curator's taste: no stance icon over the player's head — the 4 Stances `*_icon_mgef` (`06AD25`–`06AD27`, `07F13A`) minus `HitEffectArt`; switching, movesets and the coloured stance glow untouched. Generated. Unverified in game |
| [`ReadTheRoomEnderal`](arch-docs/patches/ReadTheRoomEnderal.md) → `Zenderal - Read the Room Enderal.esp` | none | Read the Room's safe areas are Skyrim `LocType*` keywords (only Ark has one in Enderal), so helmets never came off in town. **Owns** its `SafeKeywords 00080A`: + Enderal's town keywords `02EAA6`/`01E9FC` (59 locations). MCM Equip must be *leaving a safe area* (Enderal has no hostile keywords). Unverified in game |
| [`BloodyCritSound`](arch-docs/patches/BloodyCritSound.md) → `Zenderal - Bloody Crit Sound.esp` + 1 loose `.wav` (not committed) | none | Curator's taste: crit sound `UISneakAttack 0C06CE` repointed to its own Motion Array bloody-cut `.wav`, so Impactful Crits no longer matters. **Owns** `0C06CE` (Rumble - UI's record + new path); load after `Rumble - UI.esp`. Unverified in game |
| [`LevelUpSound`](arch-docs/patches/LevelUpSound.md) → `Zenderal - Level Up Sound.esp` + 1 loose `.wav` (not committed) | none | Curator's taste: level-up sound `UILevelUpSD 057B44` repointed to its own Motion Array holy spell cast `.wav` (Rumble - UI had already swapped Enderal's for Skyrim's). **Owns** `057B44` (Rumble - UI's record + new path); load after `Rumble - UI.esp`. Unverified in game |
| [`ZenKeyTrace`](arch-docs/patches/ZenKeyTrace.md) → `ZenKeyTrace.dll` | none | Stance hotkeys on AE: re-implements dTry's Key Utils key trace (`dtryKeyUtil/config/custom/*.ini`, add spell on press / remove on release). PaulMix's extend 3.3 (the only `DtryKeyUtil.dll` SKSE 2.3 loads) has no config reader, and dTry's AE 1.1 is refused (old Address Library). Runs alongside PaulMix's, which keeps the direction trace. Unverified in game |
| [`CreatureRagdollFix`](arch-docs/patches/CreatureRagdollFix.md) → Pandora patch `zragfix` | none | Human `0_master` only: MichelKI's Death and Ragdoll Behavior Fix `#0260` contact edit his page asks for by hand. Plus the draugr get-up pose matchers start on `GetUpBegin` (they started on `Ragdoll`, which they never receive: skeletons got up in an A-pose). The first creature version (contact event + `TurnOnMatchingRagdoll` too) was **reverted** — their `CollisionListener` only runs in the death state, so the human logic doesn't transfer, and the edits broke get-up. The mid-air freeze is fixed by [`AirborneGetUpFix`](arch-docs/patches/AirborneGetUpFix.md). **Rerun Pandora with `zragfix` ticked.** |
| [`ZenPlayer3DTrace`](arch-docs/patches/ZenPlayer3DTrace.md) → `ZenPlayer3DTrace.dll` | none | **Testing tool, not part of the list.** Logs the player's race, own/race skin, skeleton path, filled biped slots and 3D tree while the player is a given race (built for Force of Nature's Horned Lord: found the player's own `SkinNaked 000D64` winning over the race skin). Removed from the list after use (2026-10-28) |
| [`ZenExceptionTrace`](arch-docs/patches/ZenExceptionTrace.md) → `_ZenExceptionTrace.dll` | none | **Testing tool, not part of the list.** Logs first-chance exceptions with a chosen plugin on the stack (module + RVA, C++ type/what(), stack): for SKSE's silent "fatal error occurred while loading plugin". Found Shatterveil's missing-ID null read |
| [`ZenRagdollTrace`](arch-docs/patches/ZenRagdollTrace.md) → `ZenRagdollTrace.dll` | none | **Testing tool, not part of the list.** Logs graph events in/out + 4 Hz knock/ragdoll/controller state for any non-player actor that ragdolls, to find the mid-air skeleton freeze. **Disabled 2026-10-25** (DLL `.mohidden`): first suspected of the MQP03 temple freeze, then cleared (it froze without it too) |
| [`ZenWaterTrace`](arch-docs/patches/ZenWaterTrace.md) → `ZenWaterTrace.dll` | none | **Testing tool, not part of the list** (Wabbajack-ignored). Logs, read-only, every 500 ms (and in full on F11) which Unified Water LOD tiles are hidden or culled with a chunk node whose bound/multibound is out of view: Vyn's sea pops in and out with the camera although the cache is complete. Found the misaligned grid that `UnifiedWaterGridFix` fixes; **disabled 2026-10-28** |
| [`AirborneGetUpFix`](arch-docs/patches/AirborneGetUpFix.md) → `ZenAirborneGetUpFix.dll` | none | Enemies hit while flying as a ragdoll (Seismic Stomp + its SlowTime) froze mid-air: the engine sends `GetUpBegin` ~55 ms after the hit and the body turns animation-driven with no controller. Holds `GetUpBegin` until the pelvis has settled (1 s within 4 units, 8 s timeout, wall clock: `Actor::Update`'s float arg is 0). Refuses `stagger*`/`recoil*`/`bleedOutStart` while an actor (alive or dead, 1.1.1) is ragdolled or knocked down (a stagger pulls the graph out of ragdoll and pins the body). Verified in game (1.1.1, incl. dead skeletons) |
| [`DFSlowTimeGuard`](arch-docs/patches/DFSlowTimeGuard.md) → `ZenDFSlowTimeGuard.dll` | none | Dismembering Framework's slow-mo reset (`SetGlobalTimeMultiplier(1.0)`) cancelled Seismic Stomp's SlowTime; re-registers that native so DF can't change time while the player has a SlowTime effect. Unverified in game |
| [`SkeletonRagdollFix`](arch-docs/patches/SkeletonRagdollFix.md) → generated loose `skeletons.hkx` (not committed) | none | Skeletons ragdolled as a rigid A-pose: Bethesda's skeleton rig locks all 14 limb hinges at ±1° with axes along the bones. Patched IN PLACE (an hkxconv XML round trip loses physics precision): draugr hinge axes/ranges for knees/ankles/elbows/wrists, forward-swing hinges for hips/shoulders/head/jaw, draugr neck limits; frames rebuilt so bind = 0°. Built from XPMSE's winning copy; mod must beat XPMSE; rerun `tools/01` when XPMSE changes. Generated. Verified in game |
| [`TestingCheats`](arch-docs/patches/TestingCheats.md) → `Zenderal - Testing Cheats.esp` + 2 scripts | `0x800–0x804` | **Testing tool, not part of the list.** Lesser power with B612 sliders: real Enderal level-ups via `_00E_EPUpdateFunctions.receiveEP` (setting `PlayerExp` alone never levels), raw EP, Prophecy points. Requires B612. Unverified in game |
| [`LostOneArcherAmmo`](arch-docs/patches/LostOneArcherAmmo.md) → `Zenderal - Lost One Archer Ammo.esp` | none | Lost One archers fired one arrow, then backed off and stared: EGO gives their bows `NPCsUseAmmo`, and Lost Ones Revised - EGO Patch adds a lone Old Iron Arrow (`0028B0` ×1) they could equip. Its 8 records minus that entry; **owns** them, load right after Lost Ones Revised - EGO Patch; rerun `tools/01` after it updates. Also **owns** archer combat style `csDraugrMissile 038A23` (58 undead archers): `CantWait` added, `Dueling` off, no fallback/avoid-threat (`tools/02`, rerun after EGO updates). And **owns** 11 skeleton archer NPCs won by Lost Ones Revised's copy of `mihailancientskeletons.esp` (1 arrow → 15; 4 bowless ghost archers get EGO's bow + 18 arrows; `tools/03`). And **owns** melee style `csDraugrMelee 000D0D`: `Dueling` off, so Ancient Skeletons' new sword-and-shield skeletons attack instead of blocking (`tools/04`, unverified in game). Generated. Parts 1–3 verified in game |
| [`ThirdPersonSpellAim`](arch-docs/patches/ThirdPersonSpellAim.md) → third-party Hit Where You Aim + `Zenderal - Settings`' `SmoothCam.json` | none | Third-person spells missed the crosshair, most up close (Consecrate Dead's 10-unit beam passed over corpses): the engine fires from the left hand's `LMag` node parallel to the camera's forward, which starts ~130 units away (traced). SmoothCam can't fix it (its projectile fix is arrows only; its 3D magic crosshair only moves the crosshair). HWYA re-aims each projectile at the crosshair point; it needs SmoothCam's `use3DBowAimCrosshair`/`use3DMagicCrosshair` **false**, so a SmoothCam preset load must not turn them back on. Verified in game |
| [`SpellAimTrace`](arch-docs/patches/SpellAimTrace.md) → `ZenSpellAimTrace.dll` | none | **Testing tool, not part of the list.** Logs each player projectile's launch origin/direction vs camera and crosshair pick, its first updates and its impacts (collision layer). Found the parallel-to-camera launch. **Disabled 2026-10-29** (DLL `.mohidden`) |
| [`CastingBarAE`](arch-docs/patches/CastingBarAE.md) → `CastingBar.dll` | none | zax-ftw/CastingBar 3.0 (Apache-2.0) rebuilt for 1.7.104: the SKSE Menu Framework edition froze at load (its CommonLib reads Address Library formats 1–2; 1.7.104 is format 5, fatal box hidden behind the game). Re-adds the SMF page + per-widget layouts; hides with Ultimate Immersion Toggle (follows `HUD Menu` `_root._alpha`). Sort above Casting Bar (SWFs). Unverified in game |
| [`AspectLayout`](arch-docs/patches/AspectLayout.md) → `_ZenAspectLayout.dll` + ini + generated layout sets (not committed) | none | No resolution/HUD preset to pick: at SKSE load writes `SSEDisplayTweaks_custom.ini` with the primary monitor's resolution and copies Vel'dun's 16x9/21x9/32x9 HUD layout into place (only when the shape changes, so in-game HUD edits stick). Replaces the 8 `Zenderal - Resolution …` presets and the 3 Vel'dun aspect patches (keep those disabled); must outrank Zenderal - Settings, Vel'dun UI and Casting Bar. Rerun `tools/01` after a Vel'dun patch update. Verified in game (3360x1440 only). 1.1.0: never writes a file listed in `SKSE/Plugins/ZenAspectLayout_Skip.txt`, which only the curator's unshipped Zen's Ultrawide carries (MO2's VFS made it overwrite that mod) |
| [`SilvergroveStoneWalls`](arch-docs/patches/SilvergroveStoneWalls.md) → generated meshes + textures (not committed) | none | Curator's taste: desert-town stone walls (`_00E_Tropical_ClayHouseWall01–03`, only users of `silvergrove\brickwall01`) and the well's stones (`08A241`, world-axis projection; wood shape untouched) get Skyrim 202X's farmhouse cobbles, colour-matched to SureAI's palette (numpy CIELAB: Pillow's LAB a*/b* are signed bytes → magenta); per-face box projection at 160 units/repeat with vertex splits (one projection for all stretched the flanks), tangents recomputed (mapping learned from the original: stored tangent = dP/dv). **Sort ABOVE PG Patcher Output**; the 4 meshes are in PGPatcher's blocklist. Generated. Unverified in game |
| [`SPRPBRTweaks`](arch-docs/patches/SPRPBRTweaks.md) → 8 generated PGPatcher JSONs (not committed) | none | SPR PBR's Duenenhaim (desert town) PBR parallax 1 → 0.3, and **off** for `loamwall01/02`: SRP's speckled height maps at PBR displacement made fur-like streaks on the Old Ishmorlep tower `0607D1` (Markarth dwarf tower mesh, ~14% of two shapes' area UV-stretched > 3×; 0.3 still streaked). Same-path JSON overrides; sort above SPR PBR, rerun PGPatcher. Generated. Unverified in game |
| [`TerrainParallaxShadowDistance`](arch-docs/patches/TerrainParallaxShadowDistance.md) → 3 generated Bottled Shaders files (not committed) | none | Bottled Shaders cut terrain parallax self-shadows off at a hard 1024 units (`ParallaxCheapDistance`, a `static const`: a line across the ground that moves with you); v1.1 doubles all three limits (shadows 2048, depth fade 2048–4096, `doTerrainPom` cut-off 4096) in copies of its 3 files. Must outrank Bottled Shaders (below it in MO2's left pane); rerun `tools/01` after a Bottled Shaders update. Generated. Verified in game |
| [`HighPolyDefaultHeads`](arch-docs/patches/HighPolyDefaultHeads.md) → `Zenderal - High Poly Default Heads.esp` | none | The 18 vanilla humanoid head parts (`Male/FemaleHead*`) use High Poly Head's mesh + 3 .tri (Enderal's record, only the 4 paths swapped), so Enderal's presets (all vanilla heads) start high-poly and the list's HPH-fitted beards fit — the head poked through their stubble shells (chin patches). Masters only Skyrim.esm; needs HPH's files. Generated. **Retired 2026-10-25 for [`HighPolyPlayerHead`](arch-docs/patches/HighPolyPlayerHead.md): hard-froze the game; freeze gone with it off (verified in game)** (facegen NPCs keep their 898-vert baked mesh but take the HDPT's 3598-vert HPH .tri morphs; MQP03 temple corpse). Never ship vanilla HDPTs with a new topology without regenerating facegen |
| [`HighPolyPlayerHead`](arch-docs/patches/HighPolyPlayerHead.md) → `ZenHighPolyPlayerHead.dll` | none | High Poly Head as the default head **for the player only**: each frame, a vanilla face part on the player (explicit or race default) becomes its HPH `00KLH_*` twin (player's NPC record + 3D); NPCs and every record untouched. Twin texture sets set to Enderal's in memory (FemaleHeadNord). Needs HPH. Verified in game (new game, 1.0.1). **1.1.1 (2026-10-27) acts only inside the race menu**: race/sex change (or menu open on a new game) = HPH twin + all sliders 0 (picking a race applies a preset, whose sliders only suit vanilla); picking a preset reverts to vanilla; 1.0 swapped on menu close over the presets (beta reports). Unverified in game |
| [`UnskippableCinematics`](arch-docs/patches/UnskippableCinematics.md) → 7 recompiled SureAI scripts | none | Curator's taste: every `Game.PlayBink` (intro, near-death vision ×2, Black Guardian, credits ×3) non-interruptible — a key press ended them, and the intro opens with narration over black that reads as a broken screen. One argument per script; generator checks each fork = rebuilt source = shipped `.pex` strings. MCM "Skip videos" still skips. Intro verified in game |
| [`PrettyRighteousPathSMP`](arch-docs/patches/PrettyRighteousPathSMP.md) → 8 generated meshes (not committed) + `ZenRighteousPathFlaps.xml` | none | Curator's taste: Pretty Righteous Path cuirass's front/rear flaps (red set `armor\ebony\`, and the Righteous Keeper's black set `armor\ebony\alt\` from Semi-Unique's BSA) (`SkirtB`, already on XPMSE `SkirtF/BBone02/03`) simulated by FSMP, hinged at each child bone's own origin, colliding with the greaves. **Must outrank both Pretty Righteous Path and ERA Part 1** (all three ship `armor\ebony\` cuirasses; ERA's has no flaps). Generated. Unverified in game |
| [`KnightOfThePath`](arch-docs/patches/KnightOfThePath.md) → `Zenderal - Knight of the Path.esp` + 25 meshes copied from ERA (not committed) | `0x800–0x813` | Curator's taste: ERA Part 1's Righteous Path remaster (which overwrote Pretty's at `armor\ebony\` + `weapons\ebony\ebonyshield.nif`) as its own 5-piece set: Forged Righteous Path stats, crafted only at the forge with EGO's Forged recipes (same blueprints). New records only. **ERA must sort below Pretty Righteous Path** (else it takes the Righteous Path's paths again) and stay enabled (textures). Generated. Verified in game (crafting + look) |
| [`NoCombatMusic`](arch-docs/patches/NoCombatMusic.md) → `Zenderal - No Combat Music.esp` | none | Curator's taste: battles keep the area's music. 2.1 plays generic battle music via DOBJ `BTMS` = `_00E_Music_Combat_Regular 0773F1` (2.0's `_00E_CombatSoundtrackScript` is gone from 2.1's BSAs). **Owns** `0773F1`: silent track `0963BB`, priority 65 → 100 (below every exploration type), no abrupt/duck. Quest-scripted `_NoCond`/special music untouched; generic boss music goes too. Generated. Unverified in game |
| [`UnifiedWaterEnderal`](arch-docs/patches/UnifiedWaterEnderal.md) → generated `Zenderal - Vyn Full Extend.esp` (not committed) | `0x800–0x6606` | Bottled Shaders' Unified Water drops a distant chunk's whole LOD water and redraws only cells with CELL+LAND inside the WRLD bounds; 12,246 of Vyn's sea cells had neither (strips everywhere). Enderal's "Full Extend": flat LAND at Vyn's default −2048 for them (11,825 new CELLs, 421 base cells copied byte for byte) + Occlusion.esp's WRLD with `NAM0` widened to −96, −64. **Full plugin, not ESL. Load LAST, after Occlusion.esp; rerun tools 00→01 after a DynDOLOD run or any Vyn cell change.** Generated (binary). Verified in game together with `UnifiedWaterGridFix` |
| [`UnifiedWaterGridFix`](arch-docs/patches/UnifiedWaterGridFix.md) → `ZenUnifiedWaterGrid.dll` | none | Unified Water's chunk lookup assumes LOD grids start at multiples of the chunk size (Tamriel); Vyn's starts at −69, −55 (`vyn.lod`), so each chunk got another chunk's tiles: water popped with the camera and strips at LOD borders. Detours-chained after Unified Water's `BGSTerrainBlock::Attach` hook, rebuilds misaligned chunks' tiles from Unified Water's own cache on the real cells (registered like Bottled Shaders' own code). **1.4.0 builds the tiles without the Depth flag `0x4`**: with it, whole tiles read zero thickness and showed only the seabed (cause in Bottled Shaders unknown). **1.5.0 hides a coarse chunk's tiles in quarters a finer chunk covers** (Unified Water moves the water off the terrain node, so the game no longer does; they fought the real water near the player); tiles never cross a quarter; also hooks `BGSTerrainBlock::Detach`. Needs Vyn Full Extend. Verified in game |
| [`SteaminTWoEWeatherList`](arch-docs/patches/SteaminTWoEWeatherList.md) → generated `Root/enbseries/_weatherlist.ini` (not committed) | none | Steamin ENB under Bottled Shaders' **Effects 11** (reads `_weatherlist.ini` like ENB): adds the 19 in-play weathers Steamin never mapped — TWoE's FS auroras/desert/rain-fog/Thalgard…, Diverse Weathers' 5 new ones, Foggy Nights' fog. Runtime FormIDs are **load-order dependent** (FS = `07`: Skyrim.ccc's CC files load before it); `--check` verifies vs `skse64.log`. Rerun after load-order changes; sort above Steamin ENB. Unverified in game |

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
- **Since the 1.7.104 update the list's crash logs come from Crash Logger SSE**, as `crash-*.log` in
  `OneDrive\Documents\My Games\Skyrim Special Edition\SKSE\`, next to the SKSE plugin logs. The Papyrus log is in
  `…\Logs\Script\`, not the Enderal folder. .NET Script Framework's `overwrite\NetScriptFramework\Crash\` is the
  1.5.97 era. → [`workspace/testing-and-debugging.md`](arch-docs/workspace/testing-and-debugging.md)
- **CRDW is gone (disabled since the 1.7.104 update, 2026-10-21)** — no cache to rebuild after installs
  or Pandora runs. If it is ever re-enabled, a stale `data_*_.cache` makes newly installed files unloadable. → [`modlist/mod-gotchas.md`](arch-docs/modlist/mod-gotchas.md)
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
## Never search from the filesystem root
Do not run `find /` (or any recursive search starting at `/`) in Bash. On this PC it walks into
Windows' device namespace and crashes the system via a vJoy driver bug (BSOD 0x3B in vjoy.sys).
Always search a specific folder instead, e.g. `find /e/Zenderal ...` or `find /c/Users/frien ...`.