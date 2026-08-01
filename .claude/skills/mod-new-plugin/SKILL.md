---
name: mod-new-plugin
description: Scaffold a brand-new Enderal SE patch plugin in this workspace — a Spriggit YAML folder with a correct EnderalSE header, a build/manifest.json entry, and a FOMOD stub — so it is buildable and CI-packaged from the first commit. Use when the user wants to start a new patch, add a second plugin, or add a compatibility patch for the Zenderal list.
---

# Scaffold a new patch plugin

Create everything a new plugin needs to be built by `build/build.ps1` and packaged by CI, **without
serializing an existing `.esp`**. Use this when authoring a patch from scratch; use
**spriggit-serialize** instead when importing one that already exists as a binary.

`src/` and `build/manifest.json` ship **empty** in this repo, so the first run of this skill is also
what makes CI start producing archives.

## Inputs to collect

Ask for anything not supplied. Do **not** guess these — a wrong `ModKey` or master list means the
plugin builds and then misbehaves in-game, which is expensive to discover.

1. **Plugin filename** — e.g. `ZenderalBugfixes.esp`. This becomes the `ModKey` and must match
   exactly, including case and extension, everywhere it appears.
2. **Folder name** — conventionally `src/<PatchName>/<PatchName>ESP/`. Patch content **always** goes
   under `src/`; never scaffold at the repo root. See the layout below.
3. **Which pillar?** Bug fixes, modern combat, or modern visuals. A patch that serves none of the
   three probably belongs somewhere else — say so rather than scaffolding it. Record the answer in
   `arch-docs/zenderal-curation.md`.
4. **ESL-flagged?** Default **yes** for a patch (`Flags: [Small]`), which restricts *new* FormIDs to
   `0x800–0xFFF`. Overrides cost nothing from that budget, so this is rarely a real constraint for a
   forwarding patch. Say so explicitly when confirming.
5. **Masters**, in load order: `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm`, then
   every list mod whose records the patch overrides, in load order.
   **Never `Dawnguard.esm` / `HearthFires.esm` / `Dragonborn.esm`** — they sit in Enderal's Data
   folder but Enderal does not load them, and a plugin that masters one fails to load in-game with no
   build-time warning. If the user asks for a DLC master, stop and explain.
6. **Does it ship Papyrus scripts?** If yes, scaffold `Scripts/source/` and `Scripts/compiled/` and
   add the `.gitignore` exception (see step 4).
7. **Its own release archive, or a plugin inside an existing one?** A small compatibility patch
   usually belongs in an existing release; a distinct pillar gets its own.

## Layout to create

```
src/<PatchName>/
  <PatchName>ESP/
    RecordData.yaml        # the plugin header
    spriggit-meta.json     # { PackageName, Version, Release, ModKey }
  Scripts/source/          # .psc — committed        (only if it ships scripts)
  Scripts/compiled/        # .pex — committed        (only if it ships scripts)
```

Record folders (`Weapons/`, `Quests/`, `MagicEffects/`, …) are **not** pre-created — Spriggit adds
them as records appear. Do not scaffold empty ones.

## Steps

1. **Write `src/<PatchName>/<PatchName>ESP/RecordData.yaml`.** Fill `ModKey`, the ESL flag, and the
   masters from the answers above. `GameRelease` is **`EnderalSE`**. Set a real `Stats.Version` —
   SSE Wrye Bash rejects `0.85`-style versions, so use `1.0` or similar:

   ```yaml
   SpriggitSource:
     PackageName: Spriggit.Yaml.Skyrim
     Version: 0.40
   ModKey: <MyPatch.esp>
   GameRelease: EnderalSE
   ModHeader:
     Flags:
     - Small                      # omit this list entirely if not ESL-flagged
     Author: <author>
     Stats:
       Version: 1.0
     MasterReferences:
     - Master: Skyrim.esm
       FileSize: 0
     - Master: Update.esm
       FileSize: 0
     - Master: Enderal - Forgotten Stories.esm
       FileSize: 0
     INTV: 1
   ```

2. **Write `src/<PatchName>/<PatchName>ESP/spriggit-meta.json`** — values must match `.spriggit` in
   the repo root and the `ModKey` above. `build/build.ps1` refuses to build a folder without this
   file:

   ```json
   {
     "PackageName": "Spriggit.Yaml.Skyrim",
     "Version": "0.40.0",
     "Release": "EnderalSE",
     "ModKey": "<MyPatch.esp>"
   }
   ```

3. **Add it to `build/manifest.json`** — the single source of truth for what CI builds. Either a new
   release object, or a new entry in an existing release's `plugins` array:

   ```jsonc
   {
     "name":        "<Release Name>",          // must match build/staging/<name>/ exactly
     "archiveName": "<Release Name>",          // -> build/dist/<archiveName>.7z
     "scripts":     { "from": "src/<PatchName>/Scripts/compiled", "to": "Scripts" },  // omit if no scripts
     "plugins": [
       { "yamlSource": "src/<PatchName>/<PatchName>ESP", "dest": "<MyPatch.esp>" }
     ]
   }
   ```

   `dest` is the path **inside the release tree**, and it must match the `source=` attribute in that
   release's `fomod/ModuleConfig.xml` — `build/build.ps1 -CheckFomod` fails the build otherwise.

4. **If it ships scripts, add the `.gitignore` exception.** `.pex` are ignored by default; a plugin
   that ships scripts must opt its compiled folder back in, because CI cannot run the Papyrus
   compiler and packages the committed `.pex` as-is:

   ```gitignore
   !src/<PatchName>/Scripts/compiled/
   !src/<PatchName>/Scripts/compiled/*.pex
   ```

5. **Create the FOMOD stub** at `build/staging/<Release Name>/fomod/` — `info.xml` and
   `ModuleConfig.xml`. This is the one part of `build/staging/` that is committed source (everything
   else there is derived and regenerated by `build.ps1`, and stays gitignored via the blanket
   `*.esp`/`*.pex` rules). Copy the shape from an existing release and keep it minimal; `fomod/` must
   sit at the **archive root**, which `build.ps1` handles. A single-plugin release needs only:

   ```xml
   <requiredInstallFiles>
       <file source="<MyPatch.esp>" destination="<MyPatch.esp>"/>
       <folder source="Scripts" destination="Scripts"/>
   </requiredInstallFiles>
   ```

   **If the release ships an installer image**, follow the confirmed-working recipe in CLAUDE.md's
   "FOMOD images that actually render in MO2" gotcha — archive-root-relative `path=` *including*
   the `fomod` prefix, backslashes, an `<installSteps>` block even with no real choices, and a
   baseline (not progressive) JPEG. If another release already has a working config, copy it
   verbatim and edit the deltas. A wrong image setup still builds and still passes `-CheckFomod`;
   it just silently renders nothing, so it costs a full install cycle to spot.

6. **Verify before reporting success.** Both must pass:

   ```powershell
   pwsh build/build.ps1 -CheckFomod     # manifest <-> ModuleConfig.xml parity
   pwsh build/build.ps1                 # full build -> build/dist/<archiveName>.7z
   ```

   A plugin with no records yet still deserializes to a valid empty `.esp`, so this is a real check
   that the scaffold is wired up — run it now rather than discovering a typo three records later.

7. **Report** the created files, the FormID range available (`0x800–0xFFF` if ESL, for *new* records
   only), and the next step: add records with the **spriggit-record-editor** subagent, then audit
   with **formkey-check** / the **spriggit-formkey-auditor** subagent.

## Notes

- Record `<PatchName>` and its FormKey allocations in `CLAUDE.md` as you go, and add the patch to
  `arch-docs/zenderal-curation.md` — those files are what future sessions read to avoid reassigning
  a FormID and to know why the patch exists.
- Read `arch-docs/enderal-record-patterns.md` before authoring the first record; it documents the
  record shapes that work in-game and the ones that silently don't, starting with the
  patch-specific traps in §0.
- Override records keep the **defining master's** FormKey suffix (usually
  `:Enderal - Forgotten Stories.esm`). Only genuinely new records use `<hex>:<MyPatch.esp>`.
