# NoScreenFlashes

- **Source:** `src/NoScreenFlashes/`: one hand-copied explosion override (verbatim from
  `reference/base/Skyrim/` with one line removed), plus the generated `MagicEffects/`
  (`tools/01-build-poison-blur.py`; never hand-edit them)
- **Ships:** `Zenderal - No Screen Flashes.esp` (ESL; masters Skyrim, Update, FS, EGO, Triumvirate and
  Apocalypse since 2026-10-22). **The `Zenderal - Patch Collection` mod also ships this filename, an
  older copy.** The standalone MO2 mod must be enabled and sort ABOVE the Patch Collection, or the old
  copy wins; it was disabled until 2026-10-22.
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

## Poison blur (added 2026-10-22, curator: "remove visual blur from poisons in general")

Every poison blur in the list works the same way. A magic effect runs `MagicImodOnPlayerHitScript`
(Enderal's own source: when the target is the player, apply `OnStartImodFX`, wait 5 s, and apply
`OnFinishImodFX` when the effect ends; it does nothing else) with `PoisonHitImod 10E3D2` /
`PoisonEndImod 10E3D3`.

`tools/01-build-poison-blur.py` reads the winning version of every magic effect in the Ultra load order
(base, FS and the `src/UnresolvedRefsCleanup/tools/00a` serialization). It overrides each one whose copy
of that script points at either modifier, verbatim **minus that one script entry**. Effects that run other
scripts keep them: Triumvirate's `magicsoundplayintrooutro`, Apocalypse's `WB_Disease_Script`. It asserts:
- nothing loading after this plugin overrides a picked effect;
- the 1.71 light-plugin rule (no sub-`0x800` forms of a non-base plugin).

27 effects (2026-10-22), listed in `tools/poison-blur.json`:
- **Alchemy poisons:** Damage Health, Magicka and Stamina, and their Duration, Ravage and Rate variants (EGO's winners).
- **Weapon poisons:** EGO's `EnchPoison` / `EnchPoisonNoShader`, FS's Ralys Ryx unique.
- **Creature venoms:** `crArpPoison`, `crGrabwchterPoison`, chaurus and spider spit, frostbite venom, `DA13AfflictedSpray`.
- **Traps:** the poison trap.
- **Magic-mod poisons:** Triumvirate's druid toxic bleeds, Apocalypse's Necroplague (+AoE).
- **Crit enchantments:** Enderal's `_00E_EnchFortifyCritChance` and `_00E_EnchWeaponCritDummy`, which
  reuse the poison blur.

Not touched: Apocalypse's illusion spells (same script, Empathy/Nightmare modifiers, not poisons) and the
~400 effects whose image-space modifier is a caster-side casting flash. `Zenderal - Goblins` has its own
blur-free copy of the Arp poison. Rerun the tool whenever a mod that adds or overrides a poison effect
changes. Built 2026-10-22. Spriggit round trip equivalent: only translation tables collapse to English,
as for any non-localized override of a base record. All 91 FormKeys resolve. **Unverified in game.**

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
