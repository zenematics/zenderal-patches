# Zenderal Patches — Spriggit Workspace Guide

> **This file is the most valuable thing in the repo.** It is what a future session reads instead of
> re-deriving these conventions from scratch. When you learn something the hard way — a FormID
> allocation, a record shape that didn't work, a compile import you needed — write it here.
>
> Facts below marked **[verified]** were checked against this machine's actual Enderal install or
> toolchain on 2026-08-01. Facts marked **[upstream]** come from Mutagen/Spriggit/SureAI source or
> documentation. Anything unmarked is convention, not measurement — treat it as changeable.

## What this is

**Zenderal** is an Enderal: Forgotten Stories (Special Edition) modlist aiming at three things:
**bug fixes**, **modern combat**, and **modern visuals**. *This repo is not the modlist.* It is the
workspace where the **patch plugins Zenderal ships** are authored, built and released — the
compatibility and bugfix `.esp` files that make the list's third-party mods work together on
Enderal — plus the curation docs that record what the list does and why.

Plugins are decompiled to YAML, edited as text, and re-packed to `.esp`.
**Never hand-edit binary plugins — edit the YAML.**

- Game: **Enderal: Forgotten Stories (Special Edition)**, running on the SkyrimSE engine.
- Spriggit game release: **`EnderalSE`** — *not* `SkyrimSE`. See "Why EnderalSE" below.
- Spriggit package/source: `Spriggit.Yaml.Skyrim`
- Spriggit CLI version: **`0.40.0` — deliberately pinned, do not upgrade** (see below).
- CLI path + all tool paths: `.claude/config/tools.json` (gitignored; see Tooling config below).

### Why `EnderalSE` and not `SkyrimSE`

`GameRelease.EnderalSE` is a real Mutagen release (value `6`), and `GameCategory.cs` maps
`GameRelease.EnderalSE => GameCategory.Skyrim`, which is why the **Skyrim** serializer package
still handles it. **[upstream]** What differs is the implicit **base-master set**:

```csharp
// Mutagen.Bethesda.Core/Plugins/Implicit/Implicits.cs
EnderalSE = SkyrimSE with { BaseMasters = new ImplicitModKeyCollection(SkyrimSE.Listings.And(enderal)) };
//   where enderal = ModKey.FromFileName("Enderal - Forgotten Stories.esm")
```

So under `EnderalSE`, `Enderal - Forgotten Stories.esm` is treated as an implicit base master
alongside the five Bethesda ones. Under `SkyrimSE` it is not, and a patch that overrides Enderal
records is handled as though it depended on an ordinary third-party mod. **Keep
`.spriggit`, `spriggit-meta.json` and `tools.json`'s `spriggit.gameRelease` all reading
`EnderalSE`.**

Mutagen also resolves the load order from `%LOCALAPPDATA%\Enderal Special Edition\plugins.txt` for
this release **[upstream]**, which is the correct file on this machine **[verified]**.

> **Why Spriggit 0.40.0 is pinned.** Spriggit **0.41.0 silently corrupts leveled-list entries that
> carry COED owner ExtraData**, verified 2026-07-31 and reverted. Its deserializer throws a
> `NullReferenceException` on the 0.40 shape (`MutagenObjectType: NoOwner` + `RawOwnerData`), and its
> serializer rewrites that as `UntypedOwner` + FormKeys while **dropping the next entry's `Data:`
> block** — an entry vanishes from the built plugin with no error. There is no YAML workaround: the
> `0xFFFFFFFF` "no variable" sentinel cannot survive FormKey encoding and returns as `0x04FFFFFF`, so
> even a hand-corrected record builds a different plugin.
>
> This bites Zenderal specifically: **loot/vendor patches are exactly the leveled-list-heavy records
> that trip it.** Before ever unpinning: confirm the bug is fixed upstream, grep the tracked YAML for
> `MutagenObjectType: (No|Untyped|Typed)Owner` and `RawOwnerData`, and prove the upgrade by
> rebuilding every `.esp` and comparing SHA-256 against the previous release's. A clean build on a
> repo with no such record proves nothing. 0.41.0 also requires the **.NET 10 SDK** (its serializer
> package ships `tools/net10.0` only), failing with a `DotnetToolSettings.xml was not found` error
> that never mentions .NET.

## Enderal ground truth

Everything in this section was read off the installed game, not recalled. Re-verify with the same
commands if the install moves or updates.

**Install** — Enderal SE is a *separate Steam app* with its own copy of the engine; it is not a mod
folder inside Skyrim SE. On this machine:
`C:/Gaming/steamapps/common/Enderal Special Edition` (version **2.0.12.4**). **[verified]**

**Engine / SKSE version.** The game folder ships `skse64_1_5_97.dll` — Enderal SE is pinned to
**SSE 1.5.97**, not 1.6.x. **[verified]** Every SKSE plugin (`.dll`) in the list must be a **1.5.97
(“Special Edition”, pre-AE)** build. A 1.6.640/AE build loads nothing and usually takes SKSE down
with it. This is the single most common source of "the list doesn't launch" reports.

**Masters.** `Enderal - Forgotten Stories.esm` declares exactly **two** masters — `Skyrim.esm` and
`Update.esm`. **[verified]** (Read from the TES4 header: two `MAST` subrecords, then `ONAM`. Author
`Niseam`, HEDR version 1.7, flags `0x81` = ESM + Localized.)

> **Do not master the DLC.** `Dawnguard.esm`, `HearthFires.esm` and `Dragonborn.esm` sit in Enderal's
> `Data/` because Enderal ships a whole SSE copy, but they are **not** in `plugins.txt` and **not**
> mastered by Enderal. **[verified]** Mutagen's *implicit* base-master list for `EnderalSE` does
> include them **[upstream]**, so Spriggit will not object if you add one — the game will. A patch
> that masters a DLC in Enderal is a patch that fails to load.

**Stock load order** (`%LOCALAPPDATA%\Enderal Special Edition\plugins.txt`) **[verified]**:

```
*Enderal - Forgotten Stories.esm
*SkyUI_SE.esp
```

SkyUI is **built into Enderal**, not an add-on. Do not let the list install a second copy.

**Archives.** Enderal's own content is in `E - *.bsa`; voices in `L - Voices.bsa`; the vanilla
`Skyrim - *.bsa` are also present. **[verified]**

| Archive | Holds |
|---|---|
| `E - Meshes.bsa`, `E - Textures1.bsa`, `E - Textures2.bsa` | Enderal meshes/textures |
| `E - Misc.bsa` | interface, **scripts** and misc |
| `E - Sounds.bsa`, `L - Voices.bsa` | audio, voiced dialogue |
| `E - Update.bsa` | later-patch overrides — **loads last, so it wins** |
| `Skyrim - *.bsa` | untouched vanilla assets Enderal still uses |

**No Creation Kit and no Papyrus compiler ship with Enderal.** **[verified]** Both come from an
ordinary Skyrim SE install (`skyrimSeRoot` in `tools.json`). They are the correct tools — Enderal SE
*is* SSE — you just point them at Enderal's `Data`.

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
in xEdit (**in `-EnderalSE` mode**) to verify before shipping.

## Folder map

```
src/                       # EVERY patch lives here — one folder per patch
  <PatchName>/
    <PatchName>ESP/        # Spriggit YAML — COMMITTED, source of truth
    Scripts/source/*.psc   # Papyrus source — COMMITTED
    Scripts/compiled/*.pex # COMMITTED via a .gitignore exception (CI can't compile Papyrus)
build/                     # build.ps1 + manifest.json + committed FOMOD trees
arch-docs/                 # patch-authoring guide, curation docs, generated build report
reference/                 # gitignored — Enderal/third-party decompiles, LOOKUP ONLY
modlist/                   # gitignored — the installed Zenderal MO2 instance, hundreds of GB
papyrus-source/            # gitignored — unpacked Enderal/vanilla .psc trees
```

`src/` is the only place patch content goes, and it holds as many patches as the list needs. Each
gets its own `src/<PatchName>/` folder and its own `build/manifest.json` release entry; the
`/mod-new-plugin` skill sets both up.

**There is deliberately no starter plugin.** `build/manifest.json` ships with `"releases": []`, and
the build reports "nothing to build" and exits 0 in that state — the repo is green from the first
commit and stays green until there is a real patch to ship.

## Guardrails — how to work in this repo

These are distilled from real failures in this workspace's lineage. They cost test cycles to learn.

1. **Ground-truth before claiming.** Do not conclude a patch is or isn't needed, or that a record
   does what its name suggests, from the name alone. Read the serialized record, trace the
   FormKeys, and **show the evidence alongside the verdict**. If a mechanic depends on a third-party
   mod's compiled script, read that script's decompiled source — data-driven parts extend to your
   records, hardcoded index checks do not.
2. **Assume nothing transfers from Skyrim.** Enderal reuses the engine and almost none of the
   design. Progression, crafting, lighting, economy and the perk UI are all Enderal's own (see
   "How Enderal differs" below). A pattern that is correct for Skyrim modding is a *hypothesis* here
   until you have read Enderal's record or script.
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
   this. Rule out "never loaded" before debugging "loaded but broken".
8. **A clean build is not a working patch.** Deserialize, xEdit and the Papyrus compiler all passing
   proves it *builds*. Only launching Enderal proves it *runs*. Say which of the two you have
   actually established.
9. **Recompile and re-commit `.pex` whenever a `.psc` changes.** CI cannot run the Papyrus
   compiler. `build/build.ps1` fails on a *missing* `.pex` but cannot detect a *stale* one.
10. **PowerShell 5.1 is the target** for build scripts and skills: `Set-StrictMode` is on, there is
    no `&&`/`||`, no ternary, no null-coalescing, and no built-in YAML parser. Write `-Encoding utf8`
    explicitly when a file will be read by other tools.

## FormKey discipline

- **New** records use the patch plugin's own name as the FormKey suffix: `<hex>:<PatchName>.esp`.
- **Overrides keep the defining master's suffix** — that is how you tell at a glance which records
  you invented and which you are modifying:

  | Suffix | Means |
  |---|---|
  | `:Enderal - Forgotten Stories.esm` | overriding an Enderal record — the common case here |
  | `:Skyrim.esm` / `:Update.esm` | overriding a record Enderal left vanilla |
  | `:<SomeMod>.esp` | overriding a third-party list mod — check *its* load position |
  | `:<PatchName>.esp` | a record this patch invented |

- **Master order in `RecordData.yaml`** is load order:
  `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then any third-party plugin you
  override, in list order.
- **ESL (`Small`) plugins are constrained to FormIDs `0x800–0xFFF`.** Patches should almost always
  be ESL-flagged — a list carries a lot of them and the 254-plugin limit is real. Note that
  *overrides consume no new FormID*, so an ESL patch can override thousands of records and still
  only need a handful of the 2048 new-record slots.
- Allocate a **contiguous block per feature** for readable diffs.
- ALWAYS grep the whole workspace (your patch folders + `reference/`) for a hex FormID before
  assigning it — use the `formkey-check` skill.

## Papyrus toolchain

Scripts go through extract → decompile → edit → compile → package. Use the matching skills; the
`papyrus-script-engineer` subagent handles decompiled-source cleanup and compile-error fixing.

**Tool paths:** all resolved from `.claude/config/tools.json` — do not hardcode.

| Step | Tool | Config key |
|------|------|------------|
| Extract `.bsa` | `bsab.exe` | `$Tools.bsab` |
| Decompile `.pex`→`.psc` | `Champollion.exe` | `$Tools.champollion` |
| Compile `.psc`→`.pex` | `PapyrusCompiler.exe` (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Open Creation Kit | `CreationKit.exe` (from Skyrim SE) | `$Tools.creationKit` |

### The import path is first-wins, and Enderal must be first

There are **three** Papyrus source trees in an Enderal setup, and **55 script names exist in both
Enderal's and Skyrim's** — `critter.psc`, `dgintimidateplayerscript.psc`, `dragonactorscript.psc`,
the `default*` handlers, and so on. **[verified]** Compile against the wrong copy and you get code
built on vanilla signatures that fails at runtime, not at compile time.

**The Papyrus compiler's `-i` path is FIRST-WINS. [verified]** — tested directly on this machine's
`PapyrusCompiler.exe` by putting a deliberately broken copy of a script in the first import dir and
a good copy in the second: with `-i="broken;good"` the compile **failed** on the broken copy; with
`-i="good;broken"` it **succeeded**. So the correct order is:

```
-i="<papyrusSource.enderal>;<papyrusSource.skse>;<papyrusSource.vanilla>;<importDirs...>"
```

> SureAI's own `How to modify Enderal scripts.txt` (inside `ScriptsEnderal.zip`) states the sources
> "must be loaded in the following order: Creation Kit scripts (Scripts.zip), SKSE scripts, Enderal
> scripts (ScriptsEnderal.zip)". That is **precedence** order — last one wins — describing the CK's
> source-folder list. It is the **reverse** of the `-i` order above. Both say the same thing:
> *Enderal's copy is the one that must be used.* Don't paste that readme's order into `-i`.

**Where the three trees come from** (unpack once; `papyrus-source/` is gitignored):

| Tree | Source | `tools.json` key |
|---|---|---|
| Enderal (~5000 `.psc`) | `<gameDataDir>/ScriptsEnderal.zip` → its `source/scripts/` | `papyrusSource.enderal` |
| SKSE (74 `.psc`) | `<gameDataDir>/Source/Scripts` — already loose in an Enderal install | `papyrusSource.skse` |
| Vanilla (~14300 `.psc`) | `<skyrimSeRoot>/Data/Scripts.zip` → its `Source/Scripts/` | `papyrusSource.vanilla` |

**Flags file.** `TESV_Papyrus_Flags.flg` ships only in the **vanilla** `Scripts.zip` — neither
Enderal tree contains one. **[verified]** It resolves off the `-i` path, so having vanilla on the
path is what makes `-f=TESV_Papyrus_Flags.flg` work.

**Enderal's own scripts are prefixed `_00E_`** (1257 of them). **[verified]** A script name starting
`_00E_` is Enderal's; treat it as third-party source you read but do not edit in place — patch by
adding your own script, not by shipping a modified `_00E_` file, unless overriding it *is* the fix
and you have said so in the patch's notes.

**Per-project import dirs** — persist in `tools.json`'s `importDirs` array (the `papyrus-compile`
skill appends them to `-i` after the three trees). Record each one here as you discover it:

| API / framework | Source `.psc` dir |
|-----------------|-------------------|
| _(none yet)_ | Add SkyUI/MCM, PapyrusUtil, etc. here when a patch's script needs them. |

### Creation Kit against Enderal

The CK is only needed for asset work and for the compiler binary — **all record editing here happens
in the Spriggit YAML**, so most sessions never open it. If you do:

- Use the **Skyrim SE** CK (`$Tools.creationKit`), pointed at Enderal's `Data`.
- `bAllowMultipleMasterLoads=1` must be set in `CreationKit.ini` (already set on this machine
  **[verified]**) — without it the CK refuses to load an ESP on top of an ESM chain.
- The CK's `sResourceArchiveList` lists the *Skyrim* BSAs; it does not know about `E - *.bsa`, so
  Enderal assets will be missing in the render window unless you add them.

## Testing

MO2 instances under `$Tools.modlistsRoot`, or the Zenderal instance at `$Tools.modlistRoot`.
Use the `mod-deploy` skill rather than copying by hand.

**xEdit must run in Enderal mode:** use a copy named `EnderalSEEdit.exe` or pass **`-EnderalSE`**.
**[upstream]** Plain SSEEdit mode reads the Skyrim game folder and INI and will not see Enderal's
plugins at all. The `xedit-audit` skill passes the switch.

---

# Zenderal — the list

## The three pillars

Every patch in this repo should trace back to one of these. If it doesn't, it probably belongs in a
different repo.

| Pillar | Goal | What patches here typically do |
|---|---|---|
| **Bug fixes** | Ship Enderal as SureAI intended, minus the bugs | Fix broken records, quest blockers, bad navmesh/refs, dangling references; forward community bugfix mods onto Enderal's ESM |
| **Modern combat** | Contemporary combat feel without breaking Enderal's balance | Reconcile combat overhauls with Enderal's talent/perk system, weapon/armor keywords and combat styles |
| **Modern visuals** | Current-generation look, Enderal's art direction intact | Reconcile lighting/weather/ENB-adjacent mods with Enderal's own lighting, and mesh/texture replacers with Enderal's assets |

See `arch-docs/zenderal-curation.md` for what is actually in the list and why, and
`arch-docs/enderal-record-patterns.md` for the record shapes that build clean and do nothing.

## How Enderal differs (and what that breaks)

This is the section to read before assuming a Skyrim mod "just works". Each entry is a verified
mechanism plus the class of patch it invalidates.

**Progression is not Skyrim's.** There is no learn-by-doing and no vanilla perk tree UI. Enderal's
*talents* are three-tier **Perks** paired with **WordOfPower** unlocks, read back via
`_00E_TalentLibrary.GetPlayerTalentLevel(Perk01, Perk02, Perk03)` and
`GetTalentLevel(Word01, Word02, Word03)`. **[verified]** The character sheet is a **custom menu** —
`_00E_Game_SkillmenuSC`, a script on a ReferenceAlias that registers for `"Journal Menu"` and draws
Enderal's own UI. **[verified]**

> **Consequence.** A combat mod that adds perks to vanilla perk trees puts them somewhere the player
> can never see or buy. Combat patches must hang new behaviour off Enderal's own perks/talents, or
> off keywords and combat styles, not off the vanilla progression UI.

**Lighting is wholly replaced.** SureAI's own readme: *"since Enderal changes all light settings, no
ENB preset made for Skyrim would produce adequate lighting in Enderal. Furthermore, ENB mods may
deactivate fadeouts in cutscenes, leading to visual bugs."* **[verified — quoted from
`enderal readme.txt`]**

> **Consequence.** For the visuals pillar, a Skyrim ENB/weather/lighting mod is a starting point, not
> a drop-in. Budget for an Enderal-specific reconciliation pass, and watch cutscene fades — they are
> a known ENB casualty and they are everywhere in Enderal's story.

**Skyrim mods need conversion, by the author's own statement.** *"Enderal uses its own master file
(ESM). Mods that were developed for Skyrim must be adjusted to it before they can safely be used in
Enderal."* **[verified — `enderal readme.txt`]** In practice a Skyrim mod that only edits
`Skyrim.esm` records may load, but Enderal has usually already overridden the record you care about,
and Enderal's copy wins or loses purely on load order.

**Enderal-only systems to look for** before touching anything nearby (script names verified in
`ScriptsEnderal.zip`): Arcane Fever (`_00E_FS_AlchAddArcaneFever`), Phasmalism/Apparitions
(`_fs_phasmalist_controlquest`, `_00E_Phasmalist_*`), the affinity system inside
`_00E_Game_SkillmenuSC`, memory/learning points (`_00E_Lehrbuch_Plus1MemoryPointSC`,
`_00E_Lehrbuch_Plus2SkillPointsScript`), crafting books (`_00E_Handwerksbuch*`), and the
talent cooldown/control quests (`_00E_Game_TalentControlSC`, `_00E_Game_TalentCooldownSC`).

## Useful FormKey constants

Vanilla FormIDs Enderal inherits unchanged — safe to reference, but **confirm Enderal has not
overridden the record** before relying on its contents.

| FormKey | Meaning |
|---|---|
| `000014:Skyrim.esm` | PlayerRef |
| `000038:Skyrim.esm` | GameHour global |
| `000039:Skyrim.esm` | GameDaysPassed global |
| `000010:Skyrim.esm` | MapMarker base |
| `000034:Skyrim.esm` | XMarker base |
| `10F63C:Skyrim.esm` | MapMarkerRef LocationRefType (required for discoverability) |
| `013F42:Skyrim.esm` | `RightHand` EquipType |

> Enderal's own worldspace, keywords, crafting benches and talent perks are **not** listed here on
> purpose. Look them up in a serialized copy of `Enderal - Forgotten Stories.esm` with the
> `spriggit-decompile-reference` skill and add the ones you actually use, with the EditorID you
> found them under. A constants table copied out of Skyrim documentation is worse than no table.

## Gotchas

- **`E - Update.bsa` loads last and wins.** When a record or asset doesn't look like the one you
  found in `E - Meshes.bsa`, check `E - Update.bsa` before concluding your patch is wrong.
- **A DLC master silently breaks the plugin.** Spriggit accepts it (Mutagen's implicit base-master
  set for `EnderalSE` includes the DLC) but Enderal does not load them. See "Masters" above.
- **Compiling against vanilla signatures.** If a script compiles clean and then misbehaves on an
  Enderal type, check the `-i` order — Enderal's tree must be first. 55 names collide.
- **FOMOD images that actually render in MO2** — a config can build clean, pass
  `build.ps1 -CheckFomod`, open its wizard normally, and still show *no image at all*. Nothing
  warns you. This recipe is confirmed working in MO2; copy its shape rather than re-deriving:
  1. `path=` is relative to the **archive root**, so an image at `fomod/images/foo.jpg` is
     referenced as `path="fomod\images\foo.jpg"` — *including* the `fomod` prefix.
  2. Use **backslashes** in `path=`.
  3. Declare an `<installSteps>` block, even for a patch with no real choices (one
     `SelectExactlyOne` group holding a single `Recommended` plugin). A config with only
     `<requiredInstallFiles>` gives MO2 no wizard page to draw the banner on.
  4. Use a **baseline** JPEG or a PNG, not a progressive JPEG. Check with
     `od -A d -t x1 -v img.jpg | grep -oE 'ff c[0-9a-f]'`: `ff c0` is baseline (fine), `ff c2` is
     progressive. Re-encode progressive files via `System.Drawing` before shipping.

  These four were fixed **together** after several one-at-a-time attempts each failed, so which is
  individually decisive is unverified — treat the set as the known-good recipe, and do not drop one
  on the assumption it does not matter.

  `build/build.ps1 -CheckFomod` enforces points 1, 2 and 4: an unresolvable `path=` or a
  progressive JPEG **fails** the check (with a "did you mean `fomod\…`?" hint for the missing
  prefix), and forward slashes warn. It cannot check point 3 — whether an `<installSteps>` block
  exists at all — because a config legitimately may not want one.
- **Decompiled `.psc` is a reconstruction** (Champollion): auto-named vars, reconstructed control
  flow, lost comments/flags. Enderal ships real source for its own scripts in `ScriptsEnderal.zip` —
  **read that instead of decompiling** whenever the script is Enderal's.
- **Missing-type compile errors** → the referenced API's source isn't on the import path; add its
  `Source\Scripts` dir to `importDirs` in `tools.json` and record it in the imports table above.
- **YAML comments do not survive a re-serialize.** Spriggit rewrites the folder from the binary
  plugin, so any `#` comment you add to a record file is lost the next time anyone runs
  `/spriggit-serialize`. Put durable explanation in this file, not in the record YAML.
- Edit `.psc`/YAML, never the binary `.pex`/`.esp`. Commit source, not build artifacts.
- See `arch-docs/enderal-record-patterns.md` for the in-game failure modes that produce no build
  error — that list is the single highest-value read before authoring a new patch.
