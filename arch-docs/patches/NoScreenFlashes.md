# NoScreenFlashes

- **Source:** `src/NoScreenFlashes/` — one hand-copied override (verbatim from `reference/base/Skyrim/`
  with one line removed)
- **Ships:** `Zenderal - No Screen Flashes.esp` (ESL, masters `Skyrim.esm` only)
- **FormID block:** none (overrides only)
- **Pillar:** modern visuals (curator's taste)
- **Built:** 2026-10-16. Builds clean and is deployed. **Not yet verified in game.**

## What it does

Removes full-screen image-space effects (radial blur plus a near-white fade) that enemy abilities
splash over the player's screen.

| Record | Fired by | Dropped image-space |
|---|---|---|
| `SprigAOEExplosion 0E41F1` | **Wood Elementals'** call-creatures spell, `SprigganCallEffect 0CB12C` (its `Explosion`) | `MAGShoutAnimalAImod 084B37`: 6 s of blur and white fade, `ISRadius` 2600 |

Wood Elementals are Enderal's spriggans. They sit on `SprigganRace 013204` (EditorIDs
`_00E_ForestElemental*`, EGO's `_07E_Waldelementar`). That race's ability `AbSpriggan 09AA38`, through
`AbFXSpriggan 09AA37` and the `SprigganCallOverride 0CB12E` package, casts
`crSprigganCallCreatures 0CB12D`, so every Wood Elemental can fire this.

`0E41F1` is used only by `0CB12C`, so the override touches nothing else. EGO overrides `0CB12C` but
not the explosion, and a live load-order scan on 2026-10-16 found no plugin overriding `0E41F1`.
Everything else on the explosion (the `0ABF05` light, the 6000 radius, the flags) is kept verbatim.

## How to find the next one

1. In game, `sisme 0` (toggles image-space modifiers). If the effect vanishes, it is an IMAD.
2. Follow the ability's chain to the record carrying `ImageSpaceModifier`: SPEL → MGEF (its own
   `ImageSpaceModifier`, its `Explosion`, its `Projectile` → `Explosion`) → explosion `PlacedObject`
   (an FX placer can destroy itself into a further explosion).
3. **A high `ISRadius` is the tell.** An ISM at `ISRadius` 1 never reaches the camera.
4. If the explosion is shared (check every reference in `reference/`), copy it under a new FormID
   instead of editing it. `FlameShot` does this for `ExplosionRuneFlame01 06051F`, which fire runes,
   gas traps and Kata's Fire Nova all use.

Flame Shot's own flash is removed inside [`FlameShot`](FlameShot.md), which owns those records.
