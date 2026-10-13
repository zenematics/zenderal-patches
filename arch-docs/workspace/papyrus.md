# Papyrus toolchain

Extract → decompile → edit → compile → package. Use the matching skills; the `papyrus-script-engineer` subagent handles decompiled-source cleanup and compile-error fixing.

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

**Tool paths:** all resolved from `.claude/config/tools.json` — do not hardcode.

| Step | Tool | Config key |
|------|------|------------|
| Extract `.bsa` | `bsab.exe`, or `BSArch64.exe` (see below) | `$Tools.bsab` / `$Tools.bsarch` |
| Decompile `.pex`→`.psc` | `Champollion.exe` | `$Tools.champollion` |
| Compile `.psc`→`.pex` | `PapyrusCompiler.exe` (from Skyrim SE) | `$Tools.papyrusCompiler` |
| Open Creation Kit | `CreationKit.exe` (from Skyrim SE) | `$Tools.creationKit` |

> **`bae.exe` has no usable CLI — do not reach for it.** **[verified]** It rejects `-e`,
> `--extract` and even `--help` ("Unknown option"); the `extract` string in the binary is a Qt slot
> name, not a command-line option. It is GUI/drag-and-drop only. When `bsab` is not installed, use
> **`BSArch64.exe unpack "<archive.bsa>" "<outdir>" -mt`** (bundled in xEdit's folder,
> `$Tools.bsarch`) — it is the reliable headless extractor here. Note it **requires the output
> directory to already exist** and fails with "Folder does not exist" otherwise.

## The import path is first-wins, and Enderal must be first

There are **three** Papyrus source trees in an Enderal setup, and **55 script names exist in both
Enderal's and Skyrim's** — `critter.psc`, `dgintimidateplayerscript.psc`, `dragonactorscript.psc`,
the `default*` handlers, and so on. Compile against the wrong copy and you get code built on vanilla
signatures that fails at runtime, not at compile time.

**All 55 differ from vanilla — not one is an accidental identical duplicate.** **[verified]** by
byte-comparing `reference/base/EnderalScripts` against `reference/base/VanillaScripts`. Two of them
are explicit `; DUMMY, DO NOTHING` stubs: `dgintimidateplayerscript.psc` and
`dgintimidatealiasscript.psc`, where Enderal has gutted the vanilla brawl/intimidate system down to
4 lines from 59. **[verified]** That is the concrete cost of getting the order wrong: compile
against vanilla's copy and you link in brawl logic Enderal deliberately deleted.

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
| powerofthree's Papyrus Extender (`PO3_SKSEFunctions`, used by `ZEN_SettingsApplier`) | `<modlistRoot>/mods/powerofthree's Papyrus Extender/Source/scripts` |
| JContainers (`JValue`, `JMap`, `JContainers`, used by `ZEN_SettingsApplier`) | `<modlistRoot>/mods/JContainers SE/scripts/source` |
| _(more)_ | Add SkyUI/MCM, PapyrusUtil, etc. here when a patch's script needs them. |

## Creation Kit against Enderal

The CK is only needed for asset work and for the compiler binary — **all record editing here happens
in the Spriggit YAML**, so most sessions never open it. If you do:

- Use the **Skyrim SE** CK (`$Tools.creationKit`), pointed at Enderal's `Data`.
- `bAllowMultipleMasterLoads=1` must be set in `CreationKit.ini` (already set on this machine
  **[verified]**) — without it the CK refuses to load an ESP on top of an ESM chain.
- The CK's `sResourceArchiveList` lists the *Skyrim* BSAs; it does not know about `E - *.bsa`, so
  Enderal assets will be missing in the render window unless you add them.

## Gotchas

- **Compiling against vanilla signatures.** If a script compiles clean and then misbehaves on an
  Enderal type, check the `-i` order — Enderal's tree must be first. 55 names collide.

- **Decompiled `.psc` is a reconstruction** (Champollion): auto-named vars, reconstructed control
  flow, lost comments/flags. Enderal ships real source for its own scripts in `ScriptsEnderal.zip` —
  **read that instead of decompiling** whenever the script is Enderal's.
- **Missing-type compile errors** → the referenced API's source isn't on the import path; add its
  `Source\Scripts` dir to `importDirs` in `tools.json` and record it in the imports table above.
