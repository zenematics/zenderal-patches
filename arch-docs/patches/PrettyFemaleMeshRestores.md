# PrettyFemaleMeshRestores

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/PrettyFemaleMeshRestores/`
- **Ships:** *(no plugin — loose meshes, MO2 mod `Zenderal - Pretty Female Mesh Restores`)*
- **FormID block:** _(none)_

## What it does

**Female characters wore CBBE's vanilla-shape meshes under Pretty's re-authored textures.** The Pretty mods pack their redesigned meshes in BSAs; CBBE ships LOOSE CBBE conversions of vanilla meshes at the same paths, and **a loose file beats every BSA regardless of MO2 priority** — Pretty sorting above CBBE did nothing. Where Pretty also ships a loose texture (e.g. `clothes/merchantclothes/torsof_d.dds`), it was wrapped over UVs it was never painted for (reported 2026-10-11 on `ClothesMerchantClothes 04223C`, which Enderal names "Fine Clothes" — no plugin overrides that record). `src/PrettyFemaleMeshRestores/tools/01-extract-pretty-meshes.py` DERIVES the set from the live profile (every enabled Pretty BSA path ∩ CBBE's loose meshes; among Pretty BSAs the later-loading plugin's wins) and extracts Pretty's mesh loose, asserting `EXPECTED = 157` (Clothing 49, Common 28, Factions 28, Mages 22, Unique Sets 18, Pyrean 6, Unique 4, Holy Order 2). No Pretty mod ships any of those paths loose. Not committed — the meshes are Pretty's. Must sort **above CBBE**. Trade-off: Pretty's meshes carry no `BODYTRI`, so RaceMenu body morphs don't reshape these outfits. Re-run after any Pretty or CBBE update, then rebuild CRDW. Other loose mods also shadow Pretty BSAs (Enderal Remastered Armory Part 1: 23 weapons; SMIM, Tempered Skins for Males, Particle Patch: 1–2 each) — not judged, deliberately not included. Built 2026-10-11, not yet verified in game.
