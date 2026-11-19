# Undercity Water Fix

**Ships:** `Zenderal - Undercity Water Fix.esp` (ESL, HEDR 1.7, masters only Skyrim.esm / Update.esm / FS), MO2 mod
`Zenderal - Undercity Water Fix`. **Status: verified in game 2026-11-15** (curator: the water at `coc UndercityBarracks3MeddoksFishery` is fixed).

## Report

Players' video (2026-11-15): flat grey sheets in the Ark Undercity pits outside Meddok's Fishery, during
"Divide and Conquer". They mirror the fishing net hanging above them, so they are a water surface, not missing
geometry.

## What the water is

- Placed activator `Water1024Murky 062A60:Skyrim.esm`, `WaterType: MurkyWater 062A72:Skyrim.esm`.
- `MurkyWater` has near-black colours (shallow `#1A1313`, deep `#090906`, reflection `#20231B`), Opacity 100,
  **WaterReflectivity 0.55**, Fresnel 0.25 and fog-above amount 0.75 (far plane 60).
- No plugin in the list overrides either record. Water for Enderal CS's WATR list skips 062A72, and its only
  activator is `Water1024 03AC83`. The Undercity cells' other editors (EGO, Kata, RAO, Ravens) don't touch the water refs.
- The same type is used in about 20 interiors: ArkTomb, the Undercity barracks/mines/pits, Alt Askamahn, Soltyris,
  Duenenhaim, the Forgotten Mine, Deep Diggers' Hollow and others.

## The guess

Bottled Shaders (the list's Community Shaders fork) shades vanilla interior water, and its reflection turns
reflectivity 0.55 into a light, mirror-like sheet in a dark cave. Its straight edges show where the plane cuts
through the floor. This is the same look as the Ancient Ruins pond ([`AncientRuinsWaterFix`](AncientRuinsWaterFix.md)).

## The fix

`MurkyWater 062A72` is copied verbatim from base Enderal 2.1, with **WaterReflectivity 0.55 → 0.1**. Nothing else
changes, and the generator asserts exactly one changed line: `tools/01-build-undercity-water-fix.py`.

All of the ~20 interiors above get the same, duller water.

## If it doesn't help

In game at the spot:

1. Run `tws` in the console. If the sheets vanish, it is the water.
2. If they do, the next knobs are DepthReflections 0.2, the fog-above amount and distance, or Bottled Shaders'
   water features, toggled in its menu.

Retire this plugin if the sheets turn out not to be the reflection.

## Verified

2026-11-15, curator: the water at `coc UndercityBarracks3MeddoksFishery` is fixed with the plugin on. Oddity, not
resolved: neither the fishery cell nor `UndercityBarracks3` outside it places `Water1024Murky` in base Enderal, FS or
any serialized list mod. The water the curator saw must come from a neighbouring cell or a ref this scan missed.
Also note Bottled Shaders' `Water.hlsl`: with Dynamic Cubemaps on, interior water reflects the dynamic cubemap
(`DynamicCubemaps::EnvTexture`), so bright lights near the camera can still whiten other interior water (a vat seen
2026-11-15, unidentified).
