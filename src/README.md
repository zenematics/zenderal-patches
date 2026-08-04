# Patch sources

One folder per patch plugin. Create them with the `/mod-new-plugin` skill — it scaffolds the
Spriggit YAML folder, the `build/manifest.json` release entry and the `.gitignore` exception for
compiled scripts in one go. It adds a FOMOD **only** if the install has options; a single `.esp`
with nothing to choose ships as a plain archive via `"fomod": false`.

```
src/<PatchName>/
  <PatchName>ESP/          # Spriggit YAML — COMMITTED, source of truth
  Scripts/source/*.psc     # Papyrus source — COMMITTED (only if the patch ships scripts)
  Scripts/compiled/*.pex   # COMMITTED via a .gitignore exception (CI cannot compile Papyrus)
```
