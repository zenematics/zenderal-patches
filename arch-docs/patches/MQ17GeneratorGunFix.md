# MQ17GeneratorGunFix

- **Source:** `src/MQ17GeneratorGunFix/Scripts/source/_00E_MQ17_BossFight_GeneratorSC.psc` (SureAI's 2.1.4.4 source,
  added lines marked `; ZP`)
- **Ships:** recompiled `_00E_MQ17_BossFight_GeneratorSC.pex`, script only. The live copy is in
  `Zenderal - Patch Collection` (`Scripts/` + `Scripts/Source/`). No other mod in the list ships this script, loose or in a BSA
  (checked 2026-11-11).
- **FormID block:** none
- **Status:** built and deployed 2026-11-11. Unverified in game.

## Why

Player report (keithsmyas, 2026-11-11): in the final boss fight, the generators took no damage from guns; bashing
worked.

How SureAI built it (MQ17, cell `MQ17BlackGuardian 143B30`):

- Each generator actor (`14BD09`, `14BD0A`, base `_00E_MQ17_Generator_02 14BCF9`, ~1550 Health) sits inside an invisible
  collision box, `MQ17_Generator_Left_Hitbox 03C5E4` / `MQ17_Generator_Right_Hitbox 03C5E3`. The boxes are
  `CollisionMarker 000021` primitives on collision layer 1.
- Only the box's `OnHit` counts (`_00E_MQ17_GeneratorHitBoxSC`). It calls the generator's `CheckForDamage(akSource)`
  when the player hits, MQ17 is at stage 75+ and the generator is alive. The generator actor's own `OnHit` is empty.
- `GetDealtDamage` covers every source the list's guns produce:
  - a weapon deals base damage × 3.5, or 55 if the base damage is 0 (muskets, and bashes);
  - a spell deals its magnitudes;
  - anything else falls to 55 (a pistol's staff enchantment, whose `as Weapon` cast is None).

  So the formula was not the problem.

The guns differ from what the fight was built for:

- Ordo's `OLM_proj_ball 002F9E` flies at 60000 with an `Explosion` on impact. A vanilla arrow flies at 3600 with no
  explosion.
- The flintlock pack's `PMPistolProjectile00` is a missile with `PassThroughSmallTransparent`.

The working theory is that their hits miss the box and land on the generator, where they were dropped. This is not
traced; the fix logs which path each hit takes.

## The fix

- The generator's `OnHit` passes the player's hits to `CheckForDamage`, under the hit box's own rules. MQ17 is read
  with `GetFormFromFile(0x07FA93, "Skyrim.esm")`, because the script has no MQ17 property and a script-only fork must
  not add one.
- `CheckForDamage` (the hit box's entry point) now calls `CheckForDamageFrom(akSource, asWhere)`, which is SureAI's body
  plus a guard: the same source within 0.3 s real time counts once, since one shot may hit both box and generator.
- Both paths `Debug.Trace` a `[ZP MQ17 generator]` line saying which one counted the hit, or that it was ignored as
  a duplicate.
- Properties are unchanged (two script variables added).

## To verify in game

In the final fight, once the generators' shields are down, shoot one with a musket and with a pistol. Its health
messages (75/50/25%) should appear. The Papyrus log (`My Games\Skyrim Special Edition\Logs\Script\Papyrus.0.log`) shows
`[ZP MQ17 generator] generator hit by ...` or `hit box hit by ...`:

- If neither line appears for a gun shot, the shots reach neither the box nor the generator, and this fix can't help.
- If both appear for one shot, the guard should have logged the second one as ignored.
