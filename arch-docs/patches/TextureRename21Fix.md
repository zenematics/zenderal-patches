# TextureRename21Fix

- **Source:** `src/TextureRename21Fix/` (generator only — run `tools/01-forward-renamed-textures.py`)
- **Ships:** *(no plugin — generated textures, MO2 mod `Zenderal - 2.1 Texture Rename Fix`, ranked above every texture mod)*
- **FormID block:** _(none)_
- **Status:** generated 2026-10-20 (2 files). Unverified in game.

## Why

Enderal 2.1 renamed four texture-set normal-map paths to the standard `_n` suffix (diff of
`reference/base` vs `reference/base-2.1.4.4` TextureSets, 2026-10-20 — the only TXST path changes):

| TXST | 2.0 | 2.1 |
|---|---|---|
| `_00E_Sand01 020F1C`, `_00E_Sand02 020F1D` | `enderal\landscape\ground_wet_sand01_n_DXT1.dds` | `enderal\landscape\ground_wet_sand01_DXT1_n.dds` |
| `_00E_MossRock 020F1A` | `enderal\rock_moss03_n_DXT1.dds` | `enderal\rock_moss03_dxt1_n.dds` |
| `_00E_CrystallPlant01 0213F0` | `enderal\flora\_00E_CrystallPlant01_g.dds` | `enderal\flora\_00E_crystallplant01_n.dds` |

Texture mods made for 2.0 ship the old names, so after 2.1 the sets reached another mod's file at the
new name: SRP Enderal - Landscapes and Trees (2K)'s sand and moss-rock colour maps were drawn with ETATU
nor landscape 4x's normals (made for Enderal's original images).

## What it does

For each rename, copies the file winning the OLD path to the NEW path when that winner (a loose mod)
outranks the NEW path's winner. 2026-10-20: sand and moss rock copied from SRP (outranking ETATU nor
landscape 4x); crystal plant kept (ETATU Plants Leaves Grass 2x ships both names). Files are SRP's,
byte-identical, generated from the user's install, never committed. Re-run after texture mods change.

## Related

- Found with the CS hard-square terrain report (2026-10-20). The squares themselves were CS Extended
  Materials **height blending** on terrain whose textures have no height maps; it is turned off by
  `Zenderal - Settings`' `SKSE/Plugins/CommunityShaders/Overrides/Zenderal_ExtendedMaterials.json`
  (`EnableHeightBlending: 0`). Verified in game: the squares are gone.
