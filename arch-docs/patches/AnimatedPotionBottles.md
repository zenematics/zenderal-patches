# AnimatedPotionBottles

- **Source:** `src/AnimatedPotionBottles/` (generated: `tools/01-build-potion-props.py`)
- **Ships:** MO2 mod `Zenderal - Animated Potion Bottles`, 115 generated `meshes/Animobjects/*.nif`, not committed
  (they are the Less silly authors' meshes, rebuilt from the user's own install). No plugin. **Must outrank Ultimate
  Animated Potions NG and `Less Silly Potions for Zxlice's ultimate potion animation`** (both ship
  `meshes/Animobjects/Potion*.nif`). In the Ultra profile it sits directly above the latter. Wabbajack:
  `NoMatchInclude` in `Zenderal.compiler_settings`.
- **FormID block:** none
- **Status:** built and enabled 2026-11-12. Build 1 tested in game the same day: right bottles, sitting too low in
  the hand. Build 2 lifts them into JellyFish's fist; build 3 drops the cork. **Build 3 verified in game
  2026-11-12** (curator: "it works!"). The third-person walk/run gap below is not checked.

## Why

Curator's report (2026-11-12): the bottles drunk through Swift Potion and the animated potions didn't match
*Less silly potions Enderal SE* (Enderal Nexus 85).

Swift Potion Reborn only equips the potion. The drinking animation and the bottle in the hand both come from
**Ultimate Animated Potions NG** (UAPNG 2.9.1), which hooks the equip. Both hotkey and menu drinking go through that
hook, so both showed the same wrong bottle.

How UAPNG picks the prop. This was read from `UAPNG.dll` (strings + disassembly around `AnimObjects\` /
`Updated AnimObject model path does not exist`), not from its docs:

1. It takes the file name of the potion's own model, everything after the last slash. For example,
   `Clutter\Potions\PotionHealthLesser.nif` → `PotionHealthLesser.nif`.
2. It checks that `Data\meshes\AnimObjects\<file name>` exists (`std::filesystem`, so it sees loose files only).
3. If the file exists, UAPNG uses it as the model of its drinking anim object.
4. If it does not, UAPNG uses `Animobjects\AnimObjectDrinkPotion.nif`, the generic bottle in the BSA.

UAPNG ships these per-model props as copies of the **vanilla** potion meshes. Less silly potions (85) and its
companion *Visual consistency for Less silly potions* (Enderal Nexus 144, which wins every `Potion*` mesh in the Ultra
profile) replace only `meshes/clutter/potions/*`, plus `clutter/quest/ms12whitephialrepaired.nif` and
`clutter/ingredients/frostbitevenom01.nif`. So the world and inventory showed the Less silly bottle, and the hand showed
UAPNG's vanilla one. In the Ultra profile that hit all 25 standard drinkable potion meshes (Health/Mana/Stamina tiers,
Fortify, Resist, Invisibility, `PotionFortifySkill01`, 34 items). (Build 1 also claimed 10 drinkable EGO items used
the poison vial `PoisonDamageHealth01`. Wrong: that scan's flag filter missed unindented YAML lists. All 10 are
`Poison`-flagged *Gifttrank* / *Managift*, which are applied to a weapon and never drunk.)

JellyFish Ultimate Animated Potions NG only replaces UAPNG's clips through OAR; it has no say in the prop.

## The fix

An anim object is the world mesh plus two changes:

- an `NiStringExtraData` "Prn" = `AnimObjectR` on its root (the right-hand prop bone UAPNG's props hang on);
- no collision.

Everything else stays in the world mesh's frame. UAPNG's own props and the old ZUPA Less silly patch both use identity
transforms with the bottle base at z = 0, so no reposition is needed.

What the generator does:

1. For every `.nif` the two Less silly mods ship, it takes the **winning** loose copy among the profile's enabled
   mods, so a later override of a world bottle is matched too.
2. It copies that copy's BSTriShapes (verts, tris, UVs, normals, vertex colours, shader properties and name, 9
   texture slots, alpha property) under a fresh `BSFadeNode` and adds the Prn.
3. It drops collision, `BSX` and `BSInvMarker`.
4. It reads every output back and stops on any difference from the source (Prn, shape names, vertex/triangle counts,
   vertex positions, shader type/flags/glossiness/alpha, textures, alpha flags and threshold, colour count). The
   shape blocks come out the same size as the source's.
5. It refuses two different meshes with the same file name, because UAPNG keys props by file name only.

The output is 115 props:

| Group | Count | Was |
|---|---|---|
| Replace UAPNG's vanilla copies (and the old ZUPA patch's `PotionResistFrost50.nif`) | 54 | vanilla bottle |
| Less silly poison meshes (harmless extras: poisons are never drunk) | 61 | generic bottle |

## The lift (build 2, 2026-11-12)

Curator's recording of build 1 (first person): "the potions sit too low in the hand". The fist closed on the cork,
and the whole glass body hung below it.

Measured with `tools/00-measure-grip.py`:

- **Which clips play.** JellyFish Ultimate Animated Potions NG's (OAR priority 1, no conditions). They replace UAPNG's
  standing and sneak clips in both views.
- **Where they grip.** All four close the right hand at the same place in the prop frame: fingers 7.5–13.1 up the
  prop's Z (median 10.2–10.8), thumb 12.1–12.3, finger joints 3.5–3.9 from the axis.
  - JellyFish's third-person clips carry 156 tracks. Their first 99 follow the vanilla skeleton (bind offsets match
    within 0.03), so they are measured on it.
- **Why only the cork reached the fist.** The Less silly bottles are 8.3–14.6 units tall; vanilla's are 14.5–30. The
  hand pose was made for a vanilla-sized bottle.

`tools/01` now raises each bottle along its own axis so that the top of its body sits at the thumb (`GRIP_TOP` 12.2).
The fist then wraps the upper glass body, and the band and cork stand above it.

- **Body top** = the top of the `Liquid` shape (the liquid fills the body).
- The poison vial has no `Liquid` shape; it uses 0.6 of its height (`BODY_FALLBACK`).
- The lift is each shape's translation, so the vertices are untouched. The read-back check also confirms the lift.

Lifts by bottle:

| Bottle | Lift |
|---|---|
| Resist Shock | +1.0 |
| White Phial | +2.1 |
| Fortify Skill | +4.3 |
| poison vial | +4.5 |
| Resist Fire | +4.7 |
| Stamina / Fortify Stamina | +4.8 |
| Health / Fortify Health / Invisibility | +6.0 |
| Magicka / Fortify Magicka | +6.5 |
| Resist Frost / Resist Magicka | +7.5 |

**Known gap:** UAPNG's own third-person *walk/run* drinking clips hold the prop at its base (fingers at −0.9), and
JellyFish ships no walk/run clip. A bottle drunk while moving in third person therefore sits above the hand. UAPNG's
own clips never agreed with each other: its first-person clip grips at 4.3.

## No cork (build 3, 2026-11-12)

Curator: "it makes no sense to drink with the cork on." The prop exists only while drinking: JellyFish's clips load it
with `AnimObjDraw.AnimobjectDrinkPotion` at 0.2 s and drop it with `AnimObjectUnequip` at 1.57 s. So `tools/01` builds
it uncorked (`DROP_SHAPES`). The bottle comes up already open; the world and inventory bottles keep their corks.

- **Every Less silly bottle** (59 props) has its cork as its own `Cork` shape. Its glass neck is an open tube: no
  glass vertex lies within 0.3 of the axis near the top (top ring radius 1.3–2.2).
- **The poison vial** has its stopper baked into its single bottle shape, so it keeps it. It is never drunk.
- **Not tried: a cork that pops off mid-animation.** That would need a visibility or alpha controller on the `Cork`
  shape running on an anim object. That path is unproven in this engine, and it is one-handed drinking anyway.

## Not covered

- Forgotten Stories' Chymikum flasks, Dark Blood, the Dreamflower potion, mead and Firebrand wine have no UAPNG prop
  at all, so they show the generic bottle. Their world meshes are PG Patcher Output's. Covering them is a
  `SOURCE_MODS` / folder change in the generator, but the props would then follow every PG Patcher rerun.
- Food: UAPNG doesn't animate it, and the Enderal crafting books are `FoodItem` ALCH too.

## Upkeep

Rerun `python src/AnimatedPotionBottles/tools/01-build-potion-props.py` (`--check` first shows the plan and each
bottle's lift) after either Less silly mod, any potion mesh mod or UAPNG changes. `--profile` picks the MO2 profile
(default Ultra). It rebuilds the mod's `meshes` folder from scratch.

After a JellyFish or UAPNG animation update (or a new drinking-animation mod), run `tools/00-measure-grip.py` first.
Set `GRIP_TOP` in `tools/01` to the playing clips' thumb height, then rebuild.

## To verify in game

1. Drink a Lesser Health potion (`player.additem 0028C8 5`, `01E_Genesungstrank`) from the menu, then with a Swift
   Potion hotkey, in both views. The bottle in the hand is the Less silly bottle (band, cork, red liquid), not the
   tall vanilla one.
2. Try a Mana and a Fortify potion too. The fist should wrap the upper glass body, with the band and cork above the
   thumb, and the cork should reach the mouth. Also check sneaking and third person standing.
