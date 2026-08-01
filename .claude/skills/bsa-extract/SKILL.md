---
name: bsa-extract
description: Extract or list files (especially scripts and assets) from an Enderal or Skyrim .bsa archive using the BSA Browser CLI (bsab.exe). Use when the user wants to pull .pex scripts or assets out of a .bsa, or inspect what an archive contains.
---

# Extract from a .bsa / .ba2 archive (bsab.exe)

Pull files out of a Bethesda archive — most often the compiled `scripts/*.pex` so they can be
decompiled and edited.

## Tool (from config)

- `$Tools.bsab` — from `.claude/config/tools.json` (loaded via `.claude/config/tools.ps1`); the
  BSA Browser CLI (`bsab.exe`). Run the **modlist-install** skill to point it at a modlist's copy,
  or edit `tools.json`.
- Usage: `bsab [OPTIONS] FILE [FILE...] [DESTINATION]`
  - `-l:[AFNSX]` list, `-e:[N]` extract (`N` = flatten, no subfolders)
  - `-f FILTER` simple wildcard filter (case-insensitive, repeatable), `--exclude FILTER`
  - `--regex REGEX`, `-o` overwrite, `-i` ignore errors

## Steps

1. **List first** to see what's inside and confirm the path layout (scripts usually live under
   `Scripts\*.pex`):

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.bsab 'bsab') -l -f "*.pex" "<Archive.bsa>"
```

2. **Extract** the scripts to a destination folder, preserving the internal directory structure:

```powershell
. ".claude/config/tools.ps1"
& (Assert-Tool $Tools.bsab 'bsab') -e -o `
  -f "*.pex" "<Archive.bsa>" "<destination>"
```

## Enderal's archives

Enderal's own content is in `E - *.bsa` (plus `L - Voices.bsa`); the vanilla `Skyrim - *.bsa` are
also present in its Data folder.

| Archive | Holds |
|---|---|
| `E - Meshes.bsa`, `E - Textures1.bsa`, `E - Textures2.bsa` | Enderal meshes/textures |
| `E - Misc.bsa` | interface, **scripts**, misc |
| `E - Sounds.bsa`, `L - Voices.bsa` | audio, voiced dialogue |
| `E - Update.bsa` | later-patch overrides — **loads last, so it wins** |

> **Check `E - Update.bsa` first.** It overrides the earlier archives, so a file pulled from
> `E - Meshes.bsa` may not be the one the game actually uses. When a file appears in both, the
> `E - Update.bsa` copy is the live one.

> **For Enderal's Papyrus scripts, don't extract and decompile at all** — real source ships in
> `<gameDataDir>/ScriptsEnderal.zip`. Only extract `.pex` when no source exists (a third-party mod).

## Where to extract

- Scripts from a mod you intend to patch → a working folder, then decompile into
  `src/<PatchName>/Scripts/source/` (see the `pex-decompile` skill).
- Anything from **someone else's** mod or from Enderal, for reference/lookup only →
  `reference/<name>/` (gitignored). Never commit third-party assets.

## Notes

- `.bsa` archives are gitignored — never commit them; they're large and belong to SureAI/Bethesda.
- Drop the `-f` filter to extract everything; add more `-f`/`--exclude` filters to narrow.
- Use `-e:N` if you want files dumped flat without their subfolders.
