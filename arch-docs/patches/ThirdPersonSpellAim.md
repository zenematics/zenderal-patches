# ThirdPersonSpellAim → Hit Where You Aim + SmoothCam settings

**Ships:** nothing of ours. The fix is the third-party mod
[Hit Where You Aim](https://www.nexusmods.com/skyrimspecialedition/mods/193960) (Tossapon, 1.1.2,
GPL-3, [source](https://github.com/tossaponk/HitWhereYouAim)), MO2 mod
`Hit Where You Aim - Crosshair Accuracy Fix for Arrows and Spells`, plus two keys in
`Zenderal - Settings/SKSE/Plugins/SmoothCam.json`: `use3DBowAimCrosshair` and `use3DMagicCrosshair`
both `false`. Found with the testing tool [`SpellAimTrace`](SpellAimTrace.md).

## Problem (2026-10-29)

Spells aimed in third person did not land where the crosshair was. It was worst up close and fine in
first person. Prophecy's Consecrate Dead (`ZP_Holy_ConsecrateDead 000A40`) hit the ground just past
the corpse it was aimed at, almost every time.

## Cause: measured with `ZenSpellAimTrace.dll`

In all 10 traced casts in third person (6 Consecrate Dead, 4 Firebolt), `Projectile::Launch` got:

- **origin = the left hand's `NPC L MagicNode [LMag]`** (0.0 units off), and
- **direction = the camera's forward, exactly** (0.00–0.69° off), not the direction toward the
  point under the crosshair.

The camera root sat about 130 units behind and beside the hand, so the shot runs alongside the
camera's line and never meets it. Corpse range is where this hurts most. The engine's crosshair pick
point was 96–135 units from the hand, and the launch direction was 22–34° off it. The beam always
flew flatter than needed (e.g. 24.8° pitch where the corpse needed 28.9°), passed over the body and
hit ground (layer 17) 146–359 units out. It hit a corpse (layer 32) only once, by grazing it.

Consecrate Dead is the worst case because its projectile `ZP_Holy_ConsecrateProj 000A4E` is an
invisible `Beam` with `CollisionRadius` 10: no margin. Firebolt has the same angular error but is
bigger, and was aimed at a whole crab. In first person the hand is next to the camera, so both lines
nearly coincide.

**Not SmoothCam.** In SmoothCam 1.8.1's source, `useProjectileFixes` is for arrows only (it skips a
projectile without weapon and ammo source) and only re-applies the camera's angles. The 3D magic
crosshair (`crosshair.cpp`, `IsMagicDrawn` branch) only *moves the crosshair* to where the hand's
parallel line would hit. Turning it on (tried first, same day) did not fix Consecrate Dead.

## Fix

Hit Where You Aim hooks the player's projectile launch-angle calculation and the concentration-spell
angle setters. For each projectile it casts the crosshair ray on the projectile's own collision layer
(`kSpell` for spells, which hits corpses: the beam's impacts were on layer 32) and aims from the
fire origin to that point. Beams are included: only its arrow-trail debug display skips them. It is
tested on 1.7.104 according to its file page.

Its compatibility notes ask for both SmoothCam 3D crosshairs off, which is now set; the screen-centre
crosshair is where shots go. They also ask for TDM target lock off during ranged attacks. The list's TDM has
no such setting, so don't target-lock while shooting. Installed with the **Easy** preset (pitch
correction + target leading on, `MCM/Config/HitWhereYouAim/settings.ini`).

Backups: `E:\Zenderal-backups\SmoothCamMagicCrosshair\` (the original `SmoothCam.json`, and the
one with the magic crosshair on).

## Status

Installed 2026-10-29. Tagged "AI Assisted" and 10 days old on install. **Verified in game 2026-10-29** (Consecrate Dead hits the corpse under the crosshair in third person).

Side effect, fixed by [`HWYAMusketFix`](HWYAMusketFix.md): with the Easy preset HWYA's aim-pose solver
pointed muskets straight up (fast near-zero-gravity balls lose its flat root, 2026-10-29).
