# EnderalTextureRestores

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/EnderalTextureRestores/`
- **Ships:** *(no plugin — loose textures, MO2 mod `Zenderal - Enderal Texture Restores`)*
- **FormID block:** _(none)_

## What it does

Puts back textures Enderal **re-authored at a vanilla path** that a Skyrim texture mod overrides on a mesh Enderal still uses unmodified. The `.dds` are SureAI's/Bethesda's, so they are **never committed** — `src/EnderalTextureRestores/tools/01-extract-enderal-textures.py` extracts them from the game BSAs into the MO2 mod (Wabbajack sources them from game files). Must sort **above** every texture mod it beats. Currently: `dungeons\dwemerruins\DweStoneRubble01.dds` (Enderal's, `E - Textures1.bsa`) + its `_n` (vanilla, `Skyrim - Textures4.bsa`, which is what unmodded Enderal pairs it with) — `DweFloorRubbleFlat01 0B28B4` is an alpha-tested decal, and Stony AF Markarth and Dwemer Ruins 2K's Markarth-shard texture (72% cut out vs Enderal's 27%) rendered as bright chips across the Sun Coast temple ruins (`SonnenkuesteTempelschlucht 015D52`). **How it was found (2026-10-07), reusable:** of 713 textures Enderal ships at vanilla paths, 711 differ from vanilla; diff each live winner against Enderal's original and keep only those where the cut-out changed (alpha-mask IoU) on an alpha-tested mesh **the texture mod does not itself ship** — a mod that ships its own meshes (SRP Enderal, ~6000 nifs) is a matched set. Open candidates, unverified in game: Skyrim 202X's `windhelm\ivy.dds` (Enderal's copy is fully transparent — likely deliberately blanked), `whgrayqmessystone.dds` (Enderal plaster → 202X stone wall), `whivy.dds`. Built 2026-10-07, not yet verified in game.
