# GrassLightingFix

- **Source:** `src/GrassLightingFix/` (generator only — run `tools/01-zero-grass-emissive.py`)
- **Ships:** *(no plugin — generated meshes, MO2 mod `Zenderal - Grass Lighting Fix`, ranked directly above
  `Enderal Grass Redone (EGR Default)`)*
- **FormID block:** _(none)_
- **Status:** generated 2026-10-20 (297 meshes, 300 shapes). Unverified in game.

## Why

Enderal 2.1.4 changelog: *"Fixed meshes appearing too bright under shadows during daytime."* That is
enderalse commit `23eb96a9f8` (2025-08-02, "Hortophyll: fixed mesh lighting following Catnyss'
instructions") — *Enderal - Fixed Mesh Lighting* (Nexus 826) merged into the base game, 596 grass,
flora and tree meshes. The whole change per shape is one float: the `BSLightingShaderProperty` Emissive
Multiple goes 1.0 → 0.0 on shapes whose emissive colour is black. **[verified]** applying that edit to
Enderal 2.0's `nicoforestgrass01`, `fieldgrass01`, `nicowildgrass02`, `nicomalphasflowers03` and
`vurt_tundraredflora` gives files byte-identical to Enderal 2.1's.

Grass written for Skyrim never got the fix, so the list's grass overhaul (Enderal Grass Redone + its
requirements) brought the shadow glow back — reported 2026-10-20 as "the grass is really bright".

## What it does

The generator copies every **winning loose** mesh in scope and applies that same edit; coloured
emissive (a real glow) is left alone, and nothing else in the file changes (asserted per file). Scope:
the model of every winning GRAS record that a loose mod wins, plus every winning mesh of the grass mods
in `GRASS_MODS`. Meshes Enderal's own archives win are already fixed. It reads SE (BS 100) and LE
(BS 83) NIFs — Tamrielic Grass and Folkvangr ship some LE meshes; the property layout is the same up to
the multiplier.

2026-10-20 run: Tamrielic Grass 133, Folkvangr 108, Cathedral Landscapes 39, EGR Default 10, Origins of
Forest 2, Remove Small Rocks 2, ETATU CM Meshes 1, Cathedral 3D Pine Grass 1 + 1.

The meshes are other authors' work: generated from the user's install, never committed. **Re-run after
any grass mod is added, removed, reordered or updated** — the output is a snapshot of today's winners.

## Related

- The grass overhaul and why it uses the plain (non-ENB) builds: `arch-docs/zenderal-curation.md`
  (Enderal Grass Redone row). ENB complex grass does not apply on Skyrim 1.7.104 with ENB 0.504/0.505.
- *Enderal - Fixed Mesh Lighting* is now redundant (its copies equal 2.1's) but harmless.
