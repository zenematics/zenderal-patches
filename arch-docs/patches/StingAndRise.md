# StingAndRise

- **Source:** `src/StingAndRise/`
- **Ships:** `Zenderal - Sting and Rise.esp` + 5 scripts (`ZP_RiseArmorPierceScript`, `ZP_BloodBoilEffect`,
  `ZP_StingBroodMarkEffect`, `ZP_StingSpiderlingEffect`, `ZP_RiseMoteEffect`; `.pex` + source) + Sting's own mesh
  (Pretty's + a spider) + Rise's own mesh (Pretty's without its pommel knob + a gold sun pommel + gold wings over the
  guard) + 2 generated enchant-art meshes + Blood Boil's burst mesh + the spiderling's venom burst + Rise's sun mote
  and fire nova + Sting's green-gripped diffuse + 7 gold textures (Rise's grip ivory) + 3 ornament textures + 3
  recoloured palettes (not committed), all inside **Zenderal - Patch Collection** (as Clockwork Thunder)
- **FormID block:** `0x800–0x832` (`0x831`-`0x832` the placed daggers)
- **Needs:** powerofthree's Papyrus Extender (every area search: Blood Boil, the venom burst and fire nova, the
  spiderling's first target; as Prophecy's A Willing Sacrifice); an exclusion in Glow Be Gone's toml (`tools/03`,
  below)
- **Pillar:** modern combat (curator's request, 2026-11-13)

## What it does

Two unique daggers meant to be used together:

- **Midnight Sting** (renamed from "Sting", curator 2026-11-14): the point of its blade is coated in the green Dwemer ichor (the green puddle the curator saw in game):
  the tip and another 15% of the blade. Each hit poisons for **6 seconds**, 5 poison damage a second, and slows
  the enemy by **10%** for as long (curator, 2026-11-13). A blackened-steel **spider** clutches its ring pommel
  and its leather grip is **very dark green** (below). **An enemy that dies poisoned bursts into a Venom
  Spiderling** that hunts the nearest enemy at double speed and fights for the player for 30 seconds, and bursts in venom when it dies; an enemy that venom kills
  bursts into another (curator, 2026-11-13; below).
- **Sunrise** (renamed from "Rise", curator 2026-11-15; EditorIDs, files and the plugin keep "Rise"): polished, reflective gold metal, its scabbard's metal fittings too, with small flames flickering along
  its blade; a **silver** weapon; an **ivory white leather** grip; a **gold sun in place of
  its pommel** and **gold wings spread sideways over its cross guard** (curator, 2026-11-13; below). Each hit burns
  for **6 seconds**, 5 fire damage a second (Enderal's own *Burning*, the Fire Arrow talent's damage over time).
  **Undead it strikes carry a mote of sunlight** over them; a successful **Turn Undead** on a marked undead
  bursts it in a **fire nova** that burns it and the enemies around it, and the nova marks the undead it hits
  (curator, 2026-11-13; below). Since 2026-11-15 a marked undead's death sets off nothing (curator: "remove the on
  kill Fire Nova, keep the Turn undead fire nova").
- **The pair, hidden** (curator, 2026-11-13: "keep it as a hidden effect"; no item text names either): while Sting's
  venom is on an enemy, **Rise's hits ignore its armor**. And either dagger striking an enemy that carries the
  other's damage over time **boils its blood**: a blood burst, 40 damage to it and every enemy within 250 units,
  once every 6 seconds per enemy (below).

Curator's choices: no vanilla models, Pretty Armory ones. **Sting = Pretty Enderal Armory's assassin blade**
(Blood Needle's model, `Enderal\weapons\Iron\irondagger2.nif`), **Rise = Pretty's Aeterna dagger**
(`Weapons\Elven\1stPersonElvenDagger.nif`), in gold (curator, 2026-11-13). Sting shares the look of Blood
Needle; the coat sets it apart. Pretty's meshes were first only referenced by path; the curator's later requests
(Sting's spider, Rise's sun pommel and wings) need a copy of each, so `Sting.nif` and `Rise.nif` ship (curator's
decision): Pretty's shapes untouched except Rise's knob triangles, our shapes added. Rise's gold is still a
texture-set swap on Pretty's shapes (below).

| FormKey | Record | From |
|---|---|---|
| `800` | WEAP `ZP_Sting` "Midnight Sting" ("Sting" until 2026-11-14) | Yero's Last Words `13C2AF` (EGO's record: Enderal's unique dagger, 20 damage, crit 15, Speed 1.3, `WeapTypeUnique`) verbatim; Name, Model = Pretty's assassin blade, bounds measured from it, FirstPersonModel = Blood Needle's `14483F` (same nif), ObjectEffect `801` + charge 3000, Value 500 → 1000 |
| `801` | ENCH `ZP_StingVenom` "Sting Venom" | weapon enchantment (Touch), `802` at 5 for 6 s, the slow `817` at 10 for 6 s, the brood mark `819` for 6 s, then Blood Boil's `80E`; `NoAutoCalc`, cost 1, charge 3000 |
| `802` | MGEF `ZP_StingVenomEffect` "Sting Venom" | EGO's weapon poison `EnchPoisonNoShader 001F73` (No Screen Flashes' copy, the winner: no poison blur) verbatim: poison resistance, EGO's poison and weapon-enchant keywords, the green chaurus-poison hit shader on the target. **Removed:** `PowerAffectsDuration` (always 6 s), its "target does not have it yet" condition (a new hit refreshes the 6 s), `DispelWithKeywords` (see below). **Added:** EnchantArt `803` |
| `803` | ARTO `ZP_StingVenomCoatFX` | `ChillrendEnchFX 10A045` (type and shape), model `Zenderal\StingAndRise\StingEnchFX.nif` |
| `804` | WEAP `ZP_Rise` "Sunrise" (was "Rise" until 2026-11-15) | Yero's Last Words like Sting; Model = `Zenderal\StingAndRise\Rise.nif` (Pretty's Aeterna dagger without its knob, + the sun pommel and wings; below) with its blade shape's texture set swapped for `80C` and its scabbard's (`scb`, index 1) for `816` (alternate textures), bounds from the mesh, FirstPersonModel `80D`, ObjectEffect `805`, + keywords `808` and `WeapMaterialSilver 10AA1A` (curator: silver; EGO's silver perks ×2.15 vs undead and full damage to ghosts, Prophecy's Smite, as the Relentless Sword), script `ZP_RiseArmorPierceScript` |
| `805` | ENCH `ZP_RiseFlame` "Burning" | weapon enchantment (Touch), `806` at 5 for 6 s, the mote `823` for 30 s on `ActorTypeUndead 013796` only, then Blood Boil's `80E`; `NoAutoCalc`, cost 1, charge 3000 |
| `806` | MGEF `ZP_RiseBurnEffect` "Burning" | Enderal's `_00E_A1_FireArrowEnchME 067252` (Flame Shot's copy, the winner) verbatim: fire resistance, `PowerAffectsMagnitude` (fire perks raise it), the fire impact. **Removed:** `NoRecast` (a new hit refreshes the burn). **Added:** `FireFXShader 01B212` as hit shader (the target is seen burning; every fire damage effect, EGO's weapon fire included, uses it), EGO's `XionWeaponEnch 001F93` (like Sting's: EGO's spell-damage perk skips weapon enchantments), EnchantArt `807`. The item card's text names the burn and the mote (the armor bonus and Blood Boil are hidden) |
| `807` | ARTO `ZP_RiseFlameFX` | `ChillrendEnchFX 10A045`, model `Zenderal\StingAndRise\RiseEnchFX.nif` |
| `808` | KYWD `ZP_RiseKeyword` | on Rise only |
| `809` | PERK `ZP_RiseArmorPierce` | entry point **Mod Target Damage Resistance × 0**: weapon tab `HasKeyword 808`, target tab `HasMagicEffect 802`. `Hidden`, no description (not listed with the player's perks) |
| `80A`, `80B` | COBJ `ZP_TemperSting`, `ZP_TemperRise` | Yero's Last Words' grindstone temper `02A26E` verbatim, new products |
| `80C` | TXST `ZP_RiseGold` | Nettlebane's `0777C3` verbatim; diffuse / env mask / environment = `tools/01`'s `RiseGold_d` / `_m` / `_e`, normal = Pretty's own `shortsword_n.dds` |
| `80D` | STAT `1stPersonZP_Rise` | `1stPersonElvenDagger 036BD0` on `Rise.nif` + the same two swaps (`tools/02` asserts the swapped shapes keep Pretty's names and indices) |
| `80E` | MGEF `ZP_BloodBoilTrigger` | Prophecy's relay `ZP_Prophecy_BleedingShot_Relay B4A` (script, Touch, hidden, painless); script `ZP_BloodBoilEffect`. The **second effect of both enchantments** (1 s), with conditions on the struck target: Sting's `801` needs Rise's burn `806`, Rise's `805` needs Sting's venom `802`, both need no `812` |
| `80F` | SPEL `ZP_BloodBoilBlast` | Prophecy's A Willing Sacrifice blast `99D` (hostile, TargetActor); `810` at 40 |
| `810` | MGEF `ZP_BloodBoilBlastEffect` | Willing Sacrifice's `99E` (damage Health, BlameSpellKeyword); Conjuration keyword → EGO's `XionWeaponEnch` (as the daggers' own effects), no hit shader (the script plays Apocalypse's) |
| `811` | SPEL `ZP_BloodBoilCooldown` | Willing Sacrifice's cooldown `9A0`, TargetActor: `812` for 6 s |
| `812` | MGEF `ZP_BloodBoilCooldownEffect` | Willing Sacrifice's `9A1`: a marker (script archetype, no script), hidden |
| `813` | EFSH `ZP_EnchantArtCarrierFXS` | Chillrend's `FrostChillrendFXShader 10A043` with every colour black, every alpha ratio 0, no particles, no sound: draws nothing. EnchantShader of `802` and `806` (below) |
| `814` | EXPL `ZP_BloodBoilBurst` | FS's gore burst `_00E_FS_MAGGoreExplosion 06A18E`; model `Zenderal\StingAndRise\BloodBoilBurst.nif` (no meat), no Force, Radius 128, impact set `BloodSprayImpactSetRed 01F82A` (decals) |
| `815` | EFSH `ZP_BloodBoilSplatterFXS` | Enderal's `_00E_BloodyFXShader 144758`, fade-in 1 → 0.1 s |
| `816` | TXST `ZP_RiseScabbardGold` | as `80C`, for the scabbard: `RiseScabbardGold_d` / `_m`, the gold cubemap, Pretty's `sheath_n.dds` |
| `818` | STAT `1stPersonZP_Sting` | Blood Needle's first-person static `14483F` on Sting's own mesh `Zenderal\StingAndRise\Sting.nif`; Sting's WEAP `800` uses the same mesh (bounds measured from it) |
| `817` | MGEF `ZP_StingSlowEffect` | Enderal's Shadowtongue Oil slow `_00E_A1_ShadowtongueoilSlowME 0F8641` (a weapon oil's: Peak Value Modifier on `SpeedMult`, `Recover`, `MagicSlow`) without its script (it only resets the oil's global), hit shader, `FXPersist` and `PowerAffectsMagnitude`; hidden, the venom's text names it |
| `819` | MGEF `ZP_StingBroodMark` | Prophecy's relay `B4A` (script, Touch, hidden, painless); script `ZP_StingBroodMarkEffect`. Dispelled when its bearer dies: the spawn |
| `81A` | MGEF `ZP_StingBroodMarkBurst` | `819` + `NoDeathDispel`: the venom burst's mark (1 s), so a kill by the burst itself still spawns |
| `81B` | FACT `ZP_StingBroodSpawned` | hidden; a corpse that has spawned its spiderling joins it (one per corpse) |
| `81C` | NPC_ `ZP_StingSpiderling` "Venom Spiderling" | EGO's Young Moss Crawler `_03E_JungerMooskrabbler 01CB69` (the winner) minus its `_00E_EPOnDeath` script (no EP for its kills; it pays a killer of None) and `Respawn`; level = the player's (PcLevelMult 1, 1–100); `PlayerFaction 000DB1` for its faction; ability `81D`; Aggressive, Foolhardy, helps allies; `_DefaultFollowPlayer 04B037`; keyword `_00E_SummonedCreature 044FEA`; Height 0.49 → 0.30 → **0.5** (2026-11-14: at 0.30 its bite reach, the race's unarmed reach 96 × its scale, was ~22 units and it barely bit) |
| `81D` | SPEL `ZP_StingSpiderlingAbility` | Prophecy's Legion skeleton ability `9A7` → `81E` |
| `81E` | MGEF `ZP_StingSpiderlingEffect` | Legion's skeleton effect `9A8` (hidden, constant); script `ZP_StingSpiderlingEffect` (30 s lifetime, double speed (`SpeedMult` 200 + a carry-weight nudge), hunting the nearest enemy every 0.5 s, the bite assist (`82F`), venom burst, and the webs: PO3 `OnWeaponHit` / `OnMagicHit` → `82A`) |
| `81F` | FLST `ZP_StingSpiderlings` | the living spiderlings (filled and pruned by the scripts) |
| `820` | SPEL `ZP_StingSpiderBurst` "Venom Burst" | Willing Sacrifice's blast `99D`: `81A` for 1 s, then `821` at 25 |
| `821` | MGEF `ZP_StingSpiderBurstDamage` | Willing Sacrifice's `99E` (damage Health), resisted by poison resistance |
| `822` | EXPL `ZP_StingSpiderBurstFX` | FS's gore burst `06A18E` (as `814`) on `StingSpiderBurst.nif`, impact set `MAGSpiderSpitImpactSet 046008` (venom splats), Radius 64, no Force |
| `823` | MGEF `ZP_RiseMote` "Mote of Sunlight" | EGO's Mage Light `LightFFAimed 01EA6D` (the winner; Light archetype: a light on its target + the orb art above it): light `824`, art `825`, Touch, `FXPersist` + `Painless` (no `NoDeathDispel`: the death is the trigger), no keywords, sounds, skill or cost (never the enchant-art effect); script `ZP_RiseMoteEffect` |
| `824` | LIGH `ZP_RiseMoteLight` | Mage Light's `MagicLightLightSpell01 03FA58`, colour pale blue → sun gold `#FFC060`, radius 320 |
| `825` | ARTO `ZP_RiseMoteFX` | `LightSpellActorFX 041F06` on `RiseMote.nif` |
| `826` | SPEL `ZP_RiseFireNova` "Fire Nova" | `99D` like `820`: the mote `823` (undead only) for 30 s, then `827` at 25 in the record; `ZP_RiseMoteEffect` sets it to 25 + 2.5 × player level before each nova (SKSE `SetNthEffectMagnitude`) |
| `827` | MGEF `ZP_RiseFireNovaDamage` | `99E` (damage Health), resisted by fire resistance (`ResistFire`) |
| `829` | *(retired, never reuse)* | the first build's perk on the spiderling (ApplyCombatHitSpell → `82A`): never went off in game |
| `82A` | SPEL `ZP_StingWebSpell` "Spider Web" | Prophecy's gun hit spell `910` shape (Touch): `82B` at 100 for 6 s (3 until 2026-11-15) + the cooldown `82E` for 9 s |
| `82B` | MGEF `ZP_StingWebbedEffect` "Webbed" | Sting's slow `817` (Peak Value Modifier on `SpeedMult`, `Recover`): at 100 the enemy cannot move (it still turns and swings); + `FXPersist`, hit shader `82C`, hit art `82D`. In Glow Be Gone's exclusion (`tools/03`) |
| `82C` | EFSH `ZP_StingWebbedFXS` | vanilla `WebbedFXS 02E1CD` (unused in Enderal: `FXSpiderwebs01.dds` over the body, `GradCobWeb` palette) with quick fades (in 0.2, out 0.6; vanilla's fades out over 100 s), opaque (1 / 1) and white `#F4F4F0` (vanilla's pale teal at 0.35 barely showed) |
| `82D` | ARTO `ZP_StingWebbedFX` | hit art on `StingWebStrands.nif` (`tools/01`): vanilla's web strip `fxspiderwebhitstrip01.nif` (the game's copy) without collision, havok flags or blast node, × 0.4: web sheets from the ground to about the chest (0.3 was easy to miss) |
| `82E` | MGEF `ZP_StingWebCooldown` | Willing Sacrifice's marker `9A1` (as Blood Boil's `812`): 9 s = 6 webbed + 3 free |
| `82F` | SPEL `ZP_StingSpiderBite` "Venom Bite" | `99D` like `820`: `830` at 15. The spiderling's assisted bite: cast by its script on a hit frame the game's own check missed, target within 110 and 70° of its facing |
| `830` | MGEF `ZP_StingSpiderBiteDamage` | `99E` (damage Health), resisted by poison resistance |
| `828` | EXPL `ZP_RiseFireNovaFX` | Enderal's Wayfarer fire nova `_00E_A1_FireArrowWayfarerExp 143325` (Flame Shot's copy, the winner) on `RiseNova.nif`, Radius 300; no enchantment, damage, push or screen effect of its own |

Masters: the base three + EGO (its keywords). ESL, HEDR 1.7.

### Blood Boil

Curator (2026-11-13): "the daggers apply their DoT and when struck by the other dagger does a 'blood boil'
explosion". Blood effects in the list, looked at for it: Enderal's own blood splash
(`AbnormalityBloodExplosion.nif`: FS's unused `_00E_FS_Entropy_CorpseExplosionBlood 02F27F` and the NQR05 blood
geysers), Enderal's gore burst (`swordbloodexplosion.nif`, Father's Legacy: meat chunks, for a body that
explodes), Apocalypse's blood school (its explosion, the Sacrosanct shockwave, and its **Blood Boil** spell, whose
`WB_RestorationBlood_FXS_BloodBoil_Enemies 0BFAC0` shader makes an enemy's body seethe red), Triumvirate's
Bloodlust (not red: a light-beam palette). First build: Enderal's splash at the target's feet + Apocalypse's Blood
Boil shader on everyone it hurt + Corpse Explosion's sound. **The curator saw it (2026-11-13): "just red flames"**
(Apocalypse's shader is `FXFireAtlas02` particles through a blood palette; the ground splash was easy to miss) and
asked for "more of a blood splatter effect that pops". Since the on-hit rework it is a **hidden** effect (curator:
"keep it as a hidden effect"): neither dagger's text names it. Now, all Enderal's own:

- **The pop** = explosion `814`, FS's gore burst record `_00E_FS_MAGGoreExplosion 06A18E` (Father's Legacy's
  exploding enemies) on `BloodBoilBurst.nif` (`tools/01`): the winning `swordbloodexplosion.nif` (PG Patcher
  Output's copy) with its 14 meat-chunk nodes (Havok debris on man's-skin and horse-meat textures) and its meat-chunk
  emitter taken off the root; its blood drops `pBloodDrops10` and blood streams `pBloodLines04` burst from chest
  height (z 63–77, as Enderal built it), so placed at the target's feet it sprays from the body. No Force (FS's 240
  threw loose items about), Radius 128 with the blood-spray impact set `01F82A` (blood decals round the target, as
  vanilla `BloodDecalPlaceExplosion 0F3A8C` does), FS's own burst sound `02E28E`.
- **The splatter** = shader `815`, Enderal's `_00E_BloodyFXShader 144758` (the blood-splatter decal texture over the
  body, a darkening blend) with its fade-in cut from 1 s to 0.1 s, on everyone the boil hurts for 2 s (+ its 2 s fade).
- Apocalypse is no longer needed.

How it runs, Prophecy's A Willing Sacrifice's shape (`ZP_WillingSacrificeEffect`):

- Each enchantment's second effect `80E` passes its conditions only on a target that carries the **other** dagger's
  damage over time and no cooldown. A relay (1 s): the engine re-checks an active effect's conditions while it runs.
- `ZP_BloodBoilEffect` casts the cooldown `811` on the target first (6 s, and the script checks it again: two hits
  in one frame), places the burst `814` at the target (no damage, push or screen effect of its own), then
  remote-casts `80F` **blamed on the wielder** (kill credit, Enderal's EP) on the target and on every living actor
  within 250 units (`FindAllReferencesOfFormType`) hostile to the wielder, playing the splatter `815` on each.
- Glow Be Gone does not touch any of it: the burst is an explosion, the splatter a script-played shader.
- Nothing is consumed: both damage-over-time effects keep running, so Rise's armor bonus still holds for the rest of
  the venom. The cooldown is what stops a dual-wielder from boiling every other hit.
- 40 damage is a spell's (armor does not reduce it; no resistance), keyword `XionWeaponEnch` so EGO's spell-damage
  perks skip it like the daggers' own effects. Tunables: `BOIL_DAMAGE`, `BOIL_COOLDOWN`, `BOIL_RADIUS` in `tools/02`
  (the radius also in the script as `AutoReadOnly`; `tools/02` stops if they differ).
- A killing blow probably does not boil: the other damage over time is dispelled when the enemy dies.

The first build went off in game (the curator saw its shader). **[unverified in game]**: the new burst and splatter,
the decals, both directions, the damage reaching nearby enemies only, and the cooldown.

### Spiderlings and motes of sunlight (the on-hit rework)

Curator (2026-11-13): Sting "when an enemy is killed a small spider spawns from the body, the spider lasts for 15
seconds attacking any enemies nearby and on death explodes for more poison damage. If that explosion kills an
enemy, it also spawns another spider". Rise "when hitting Undead, it marks enemies with a Mote of sunlight about
the head (similar to mage light but a sun spell effect); if an enemy with a mote is killed it explodes (use the
Dawnbreaker sword's effect); explosions can proc more motes on undead". Blood Boil and the armor bonus stay, hidden.
Defaults chosen where the curator did not answer: Rise keeps its burn (the mote is added); a spiderling comes from
any enemy that dies **while Sting's venom is on it** (not only Sting's killing blow); the spider is a shrunken Young
Moss Crawler (Enderal's own spider, not a Skyrim frostbite spider).

**The death trigger** is vanilla's soul trap test: an effect without `NoDeathDispel` is dispelled when its bearer
dies, and its script's `OnEffectFinish` then sees `IsDead()` true; on a living bearer the effect just runs out. Two
hidden script effects ride on the hits for it (Sting's brood mark `819`, 6 s like the venom; Rise's mote `823`,
30 s). A kill by a burst's own damage would come too late for a mark the same spell puts on: so the venom burst's
mark `81A` carries `NoDeathDispel` and lasts 1 s, and it fires when it runs out on the corpse.

**Sting's brood** (`ZP_StingBroodMarkEffect`): only for the player's own marks (a follower with Sting spawns none).
The corpse joins `81B` (one spiderling per corpse, both marks), and if fewer than **5** spiderlings live
(`81F`, dead entries pruned) the corpse bursts (`822`) and a Venom Spiderling is placed on it with
`PlaceActorAtMe`: health 20 + 2 per player level, a player teammate, sent at the nearest living enemy of the player
within 1500 (else it follows the player, `_DefaultFollowPlayer`, until a fight starts). Prophecy's Legion of the
Damned skeletons are the archetype throughout.

**The spiderling** (`ZP_StingSpiderlingEffect`, on its own ability): Legion's lifetime stamp (game time of death in
`Variable07`, so a load does not restart it; polled every second) kills it after **15 s**. When it dies, killed or
out of time: `822` at its body (Blood Boil's burst on venom-green palettes `GradVenom`/`GradVenom02`, 40% size, with
the spider spit's splats) and `820` **remote-cast from the player** (kill credit, Enderal's EP, as A Willing
Sacrifice) on every living actor within **200** hostile to the player: the 1 s mark `81A` + **25** poison damage
(poison resistance). Then it leaves `81F` and is disabled and deleted 3 s later. No inventory call on the dying
actor (Legion's crash).

**Rise's mote** (`ZP_RiseMoteEffect`): vanilla Mage Light's own Light archetype on a Touch effect hangs the light on
the struck actor and plays its hit art there: `RiseMote.nif` = `lightspellactorfx.nif` (the orb above the head)
with its palette layer moved to a sun-gold ramp (`GradSunMote.dds`, recoloured from `gradlightspell.dds`) and its
four glow/glare layers tinted (1.0, 0.80, 0.42), plus a warm gold light of radius 320. Only on
`ActorTypeUndead 013796` (the enchantment entry's condition). When a marked enemy dies, its corpse bursts in a
**weak fire nova** (curator, same evening: "instead of the dawnbreaker effect can we make it a weak fire nova"; the
first build used Dawnbreaker's `ExplosionTurnUndeadMass01 08C1AC`): explosion `828`, Enderal's own fire nova (the
Fire Arrow talent's Wayfarer burst `143325`, Flame Shot's copy) on `RiseNova.nif` = vanilla Fire Storm's ring of
flame `FireStormAreaEffect.nif` scaled so the mesh's own reach marker `BlastRadiusNode` (615) lands on the damage
radius (× 0.488; the ring's movers carry no keyed path, so the marker is the measure: check the size in game),
with no damage, push, enchantment or screen effect of its own; and `826` is remote-cast from the player on every
living actor within **300** hostile to the player: a new mote on the undead among them first, then **25 + 2.5 × the player's level** fire
damage (fire resistance). So a nova that kills a marked undead set off the next one.

**The on-death nova is gone (2026-11-15)**, curator: "remove the on kill Fire Nova, keep the Turn undead fire
nova". `ZP_RiseMoteEffect` lost its `OnEffectFinish` + `IsDead` burst; everything below (the Turn Undead nova,
its damage, the marks it leaves) is unchanged, so the nova's marks now only matter to the next Turn Undead.

**A successful Turn Undead sets it off** (the only trigger since 2026-11-15) (curator, same evening: "successful Turn undead spells trigger Fire
Nova from any undead marked with a Mote"). The mote's script hears every effect applied to its bearer
(`OnMagicEffectApply`); one of the engine's TurnUndead archetype (`PO3_SKSEFunctions.GetEffectArchetypeAsInt` = 24:
neither the base game nor SKSE has an archetype getter here) that is still active 0.25 s later (PO3
`HasActiveMagicEffect`; a turn that fails its level check does not stay) bursts the nova from that undead, at most
once every 2 s per undead (a concentration turn re-applies; two turn effects in one cast fire once). The turned
undead is burnt by its own nova too (curator: it "doesn't actually damage the undead it comes from"): its mote is
dispelled first and the nova's own mote replaces it, refreshed rather than doubled. That covers all 17
TurnUndead effects in the list (Enderal/EGO's Turn Undead line, Kata's concentration turns, Circle of Protection's
hazards, the mass turn), whoever casts them; the nova is still blamed on the player. Rise's text names it.
**[unverified in game]**; the open question is whether a turn that fails the level check really never shows as
active for 0.25 s.

**Damage, second pass** (curator: the nova "doesn't seem to do much if any damage"): the record was fine (20 fire,
cast as the player); EGO sets every `fDiffMultHPByPC*` difficulty multiplier to 1, so 20 landed in full minus fire
resistance, nothing next to Enderal's health pools. Now 25 + 2.5 per player level (50 at 10, 100 at 30, 150 at 50),
set on `826`'s damage effect (index 1; 0 is the mote) by the script before each nova; the burst runs in a global
function so the turned case can dispel its own effect first. `tools/02` checks the script's `DamageBase` /
`DamagePerLevel` against `NOVA_DAMAGE` / `NOVA_PER_LEVEL`. **[unverified in game]**

Glow Be Gone leaves all of it alone: it nulls only an effect's enchant shader and looping (hit) shader (its source,
read for `813`), and the mote uses neither; the bursts are explosions.

Tunables: `SPIDER_LIFE`, `SPIDER_HEIGHT`, `SPIDER_BURST_DAMAGE`/`_RADIUS`, `MOTE_SECONDS`, `NOVA_DAMAGE`/`_PER_LEVEL`/`_RADIUS`,
`MOTE_LIGHT_*` in `tools/02` (the lifetime and both radii also in the scripts as `AutoReadOnly`; `tools/02` stops
if they differ; `tools/01` sizes the nova's ring from the script's radius); `MaxSpiderlings`, health and seek radius
in `ZP_StingBroodMarkEffect`; `MOTE_TINT`, `SPIDER_BURST_SCALE`, `VENOM_RAMP`, `SUN_RAMP` in `tools/01`.

**[unverified in game]**: all of it. Worth watching: the spiderling's size and that it attacks (not only follows),
the spawn on kills by other weapons while poisoned, the chain of venom kills, the 5-spider cap, the orb's height
over large undead, the nova ring's size against its 300 radius, and the chain of novas.

### The spiderlings' webs

Curator (2026-11-13): "make it so Stings spider attacks stop enemies in place with web attached", "maybe not just
feet but webs attached to them", "takes them 3 seconds to break free"; 2026-11-15: "extend ... web stop to 6 seconds". Every hit a spiderling lands
webs the enemy for **6 s**: movement speed −100 (rooted; it can still turn and attack), a white web shader over its body and vanilla
web sheets from the ground up to its chest. Then it is free for **3 s** before it can be webbed again (cooldown
`82E`, checked by the script before it casts).

**First build: the webs never fired** (curator: "Webs never triggered or appeared noticeably"). It used a perk on the
spiderling (`829`, ApplyCombatHitSpell). The moss crawler's bites (`FrostbiteSpiderRaceHoher 0EAA8E`: Bite1,
Bite2, the lunge bite) carry the race's own attack spell `0638B2`, and the perk's hit spell never went off on them.
Now the spiderling's own ability script hears its hits through PO3 (`RegisterForWeaponHit` /
`RegisterForMagicHit`: bites and anything it spits or casts, its own web and venom burst excluded) and remote-casts
`82A` from the spiderling, blamed on the player; each web is traced to the Papyrus log as `[ZP Sting] spiderling …
webbed …`. The look was also too faint: the body shader is now opaque white and the sheets × 0.4.

Tunables: `WEB_SECONDS`, `WEB_FREE_SECONDS`, `WEB_SHADER` in `tools/02`, `WEB_SCALE` in `tools/01`. **[unverified in
game]**: the webs firing (look for the trace), the root holding (SpeedMult at 0), the look on big creatures.

**Faster, hunting, landing (2026-11-14).** Curator: "last for 30 seconds and make them twice as fast ... very quickly
seek and attack targets", then "I don't think the Spiderlings ... are hitting very easily, maybe precision issue?".
Not Precision: its source (`PrecisionHandler::ActorHasAttackCollision`, `AttackHooks::Func1/Func2`) only takes a
creature's hits over when it has made attack capsules, and no Precision config in the list defines the spiders'
body-part data (`017929`), so their bites use the game's own melee check: race unarmed reach (96) × the actor's
scale. At height 0.30 × the race's 0.75 that was ~22 units, less than a human's body radius, so the AI rarely got
close enough to start a bite. Now: height **0.5** (a young moss crawler's own, reach ~36), lifetime **30 s**,
`SpeedMult` **200**, and every 0.5 s a spiderling with no live hostile target is sent at the nearest enemy within
2500. The **bite assist**: on its own `HitFrame` / `weaponSwing`, if no real hit followed within 0.15 s and its
combat target is within 110 and 70° of its facing, `82F` (15 poison) + the web land anyway (traced: `[ZP Sting]
spiderling … bite landed … (assist)`). **[unverified in game]**

### Rise's sun pommel and wings; the grips

Curator (2026-11-13): "an Angel on the pommel to Rise and wings on the cross guard" (chosen: holding a sun
overhead, wings spread out sideways, polished gold), and "Stings leather handle very dark green", "Rise handle to
ivory white leather". Then, after seeing the angel: **"change the angel for just a Sun"**, so the pommel is now a
sun (below); the angel's generator `angel()` stays in `tools/angel.py` for reference, unused.

**The first build was wrong** (never shipped in a plugin): the wings stuck on the guard arms' ends and the angel
stood under Pretty's knob. Curator: "I wanted them overlaying the existing crossguard, not stuck on the end and the
pommel should be replaced with the angel". Now (`tools/01`'s `build_rise_mesh`, geometry in `tools/angel.py`):

- **The knob is removed**: Pretty's Aeterna dagger is one shape whose pieces (triangles joined through shared
  positions) are the blade, guard, grip wrap, a ring band (bottom y −6.13) and the faceted knob (280 triangles,
  y −8.71 … −5.54; both asserted). The knob's triangles are dropped from the shape in place (`nifse.set_triangles`:
  every other field kept; its vertices stay, unused).
- **A sun** takes its place (`sun_pommel`): an oval socket capping the ring band (its rim 10% wider than the band's,
  so the surfaces do not flicker), a short neck, and a domed disc of radius 1.35 in the blade's plane (both faces
  toward ±Z, half thickness 0.42 at the centre / 0.24 at the rim) with a raised ring on each face and pointed rays
  every 22.5° from straight out along the axis, alternating 1.05 / 0.62 long, none within 35° of the neck: 13,
  mirrored across the axis (asserted; the first build stepped `360 // 16` = 22° and came out lopsided, curator). Down to y −10.6 (the knob ended at −8.71), 4.5 wide.
  About 8 200 triangles. (The angel it replaced: the same socket and a robed figure at 1.3× holding a rayed sun
  overhead, ~15 200 triangles.)
- **Each wing sheathes a guard arm**: the leading edge is a closed tube with a superellipse section (p = 4) sized,
  every 0.25 units from |x| 2.1 (where the arm leaves the centre block) to the arm's end, from the arm's actual
  section (the triangles sliced at that x: its long faces have too few vertices to sample) + 0.14 / 0.12 margin,
  then tapering smoothly 1.9 units past the end (2.5 until the curator's "a little smaller in length"). `tools/01` asserts every guard-arm vertex is inside it (546 of
  546). Over it: a row of short overlapping scale-coverts along the leading edge and a row of longer coverts on
  each face, secondaries hanging toward the grip, six primaries fanning past the end (2.4 → 1.9 long). Out to |x| ≈ 10.4 (was 11.7). About
  16 600 triangles for both. The guard's centre block stays visible between them.
- Both are their own shapes (`ZP_RiseSun`, `ZP_RiseWings`) appended to the root with Pretty's transform
  (0, −0.6, 0, scale 0.95), each on its own copy of the blade's shader (never one shared shader: Clockwork Thunder's
  freeze), textured with a plain polished-gold set on the blade gold's recipe (`RiseOrnament_d/_n/_m`: diffuse
  0.92/0.80/0.55, highlight 0.85, Complex Material mask 0.94/0.93/1/0, 1×1 mip checked) + the gold cubemap.
  Appending keeps the blade and scabbard at alternate-texture indices 0 and 1 (`tools/02` asserts).
- ~25 000 extra triangles on a dagger (sun 8 200, wings 16 600) is a lot; cut `rings_n`/`m` in `angel.py` if it
  costs frames.

**The grips** (`grip_mask`/`recolor_leather` in `tools/01`): the grip's UV islands (vertices joined where their
UVs meet) holding a triangle wholly between pommel and guard are kept when 60% of their texels are leather (warm,
not metal); every leather texel in them is moved to the new colour, its brightness relative to the leather's own
75th percentile kept. Sting: both wrap strips → very dark green (0.03, 0.10, 0.05), full contrast, written as
`StingBlade_d.dds` (Sting.nif's blade texture set points at it; the spider's copy inherits it, its patch is metal).
Rise: the two wrap strips and two lacing strips → ivory (0.92, 0.88, 0.78), the wrap's dark bands at 60% depth,
inside the gold diffuse `RiseGold_d` (the rings, end cap and guard are metal or dropped islands: untouched).

**[unverified in game]**: the sun and wings in both views and sheathed (the wings may clip the hip), the grips'
colours under the list's lighting.

### Sting's spider

Curator (2026-11-13): "add a metal spider to the hilt of Sting"; chosen: **on the pommel, blackened steel, always
visible**. Always visible means Sting needs its own mesh, so **this is the one place a Pretty mesh is copied** (the
curator's decision; Pretty's permissions are the curator's call): `tools/01`'s `build_sting_mesh` writes
`meshes\Zenderal\StingAndRise\Sting.nif` = the winning `irondagger2.nif` with every one of its 28 blocks byte-identical
except the scene root's child list, plus three new blocks: the spider's `BSTriShape` `ZP_StingSpider`, and its own copy of
the blade's `BSLightingShaderProperty` + texture set (never one shader for two shapes: that froze the game on Clockwork
Thunder). The weapon (`800`) and its first-person static (`818`, new) point at it; Blood Needle keeps Pretty's.

- **The pommel is a flat ring** (not a plate): y −12 .. −9.5, about 3.8 × 0.77, open in the middle, then a thicker
  collar. Measured from the mesh (`face` = half thickness 0.385, `rim(y)` = half width per height), not hard-coded.
- **The spider** (`tools/spider.py`, our own geometry, 3,276 vertices): cephalothorax towards the grip, abdomen
  towards the butt, straddling the ring's opening on its +Z face; two fangs, four eyes; eight legs (Catmull-Rom
  tubes, radius 0.095 → 0.04, thicker at two joints) that arch to knees 0.62 above the face, come down onto the
  ring's outer rim and curl round it to grip the back face. `clearance` asserts each leg's centre line stays ≥ 1.15 of
  its radius from the pommel's surface (sampled from its triangles): 1.35.
- **Blackened steel**: the copied shader is the blade's (env-mapped, Pretty's `billyro\assassin\blade` set, gloss
  80), and the spider's UVs sit in the middle of the blade's largest UV triangle with a spread of 0.003 per unit (well
  inside its 0.026 in-radius, asserted), so the spider has the blade's colour, env mask and sheen without its detail.
  Tangents follow the mesh's own convention (`tangent_convention`).
- The poison coat (`803`) is fitted to the same blade, so it still fits.

**[unverified in game]**: the spider's look, sheathed (the pommel sticks out of the scabbard) and drawn, both views.

### Rise in gold

Curator (2026-11-13): "make the Rise dagger shiny gold". **Bethesda's own pattern**: vanilla Nettlebane is the ebony
dagger's mesh with its blade shape's texture set swapped for a TXST through the model's alternate textures (on its
first-person STAT `0777C4`, index 3). Rise does the same on Pretty's mesh, so the mesh stays Pretty's: the swap
targets shape `Noble_Shortsword_MP` (blade, guard, grip and pommel in one shape, one texture) at index 0, its place
in the mesh's depth-first geometry order (`tools/02` reads both from the winning mesh; Nettlebane's index 3 is the
same count). The WEAP's first-person model is a STAT, so Rise gets its own (`80D`, 036BD0 + the swaps); the Aeterna
dagger and its static stay silver. **The scabbard matches** (curator, same day): shape `scb` (index 1, Pretty's own
`sheath.dds` set) is swapped for `816` the same way.

**Shiny, polished gold: three builds the same day** (curator: "shiny / reflective metallic gold", then "it's
matte").

1. A bronze-to-gold diffuse, a grey env mask (0.35 + 1.5 × Pretty's) and Pretty's own `rainbow.dds` cubemap tinted
   gold: gold-coloured, not shiny.
2. **Complex Material** (Bottled Shaders reads an env mask that carries alpha as R reflection / G gloss / B metalness /
   A parallax; `Shaders/Lighting.hlsl`, `EMAT_ENVMAP`, on by default): metal with its diffuse blacked out, reflecting
   **Dynamic Cubemaps**' live surroundings tinted by the base colour. **Read as matte in game**: that reflection is
   only as bright and as patterned as the scene round the blade (Lighting.hlsl adds it as indirect specular ×
   `GetDynamicCubemapSpecularIrradiance`), and Pretty's highlight mask stayed dull.
3. **Now: the vanilla way, which shines everywhere.** A plain env mask (BC1, no alpha, so Complex Material stays off
   and the texture set's cubemap is reflected: Lighting.hlsl's `!dynamicCubemap` path, `envColor = cubemap × mask`,
   added to the lit colour, no Fresnel cut) at **1.0 on the metal**; a gold cubemap made from **Bethesda's chrome
   studio cubemap** `cubemaps\chrome_e.dds` (read from `Skyrim - Textures3.bsa`, never a loose replacer: TB's HD
   Cubemaps wins the path), resampled 32 → 256 per face, contrast raised (luminance^1.3 × 1.5) and graded dark gold →
   gold → pale gold: bright gold light bands over deep gold, what reads as polish; and **our own normal maps**,
   Pretty's with the metal's highlight mask (the alpha) raised from **0.18 to 0.69** (0.6 + 2 × (alpha − 0.13)):
   Pretty's dull-steel highlights were the main reason the gold read matte. Diffuse: a mid gold ramp
   (0.34/0.21/0.06 in the engraving → 0.97/0.86/0.55), leather unchanged.

The scabbard gets the same diffuse and normal treatment, but **it cannot reflect**: Pretty's `scb` shader
(`BSLightingShaderProperty` 17) is type 1 without the `Environment_Mapping` flag (the blade's, 14, has it; env scale
1.0, gloss 60, specular 1.4 on both), and changing that means editing Pretty's mesh. Its fittings shine through the
raised highlights only. Mesh facts read by a script from the winning `1stPersonElvenDagger.nif`.

Not usable: Community Shaders' **True PBR**. A PBR texture set (`PBRTextureSets/<TXST EditorID>.json`) only feeds a
shape that is already PBR; the shape-level switch is a flag in the NIF (CS `TruePBR.cpp`,
`BSLightingShaderProperty_LoadBinary`, read 2026-11-13), so model alternate textures cannot turn Pretty's mesh PBR.

4. **Now (build 4): Precious Objects' gold recipe.** The curator installed *Precious Objects Complex Material and
   Dynamic Cubemap* (Nexus 114727). Its gold, read from its files: Complex Material mask R 0.94 / G 0.93 / B 1.0 /
   A 0, pale bright gold diffuse (mean 0.95/0.83/0.58), normal-map highlight mask 0.63–0.88, env scale 5 in its meshes
   (Vanilla Fresnel saturates the mask, so ours at 1 matches). Rise now has the same: mask R 0.94 / G 0.93 (− 0.04
   where Pretty's mask is dull) / B 1.0 / A 0 on the metal, highlights 0.85, diffuse mean 0.90/0.79/0.55 on the metal;
   build 3's gold chrome cubemap stays as the shine where Complex Material is off.

**Why build 2 really read matte: its mask's mips were black.** texconv builds mips weighting colour by alpha, and a
Complex Material mask's alpha is 0, so every mip below the top came out (0, 0, 0, 0). Bottled Shaders tests the
**1×1 mip** (`SampleLevel(…, 15)`): black is "grey", so the mask was refused as complex, and every distance past mip
0 also had no reflection mask at all. `tools/01` now writes RGBA textures with **`-sepalpha`** and asserts on the
decoded 1×1 mip (`smallest_mip`): alpha below 1 − 4/255, channels not all within 4/255 (with 2× margin); it also
caught R = 1.0 making that mip grey by coincidence (0.72/0.73/0.72), hence Precious's 0.94.

**[unverified in game]**: build 4's look, drawn, sheathed, dropped and in first person.

### The armor bonus

"Ignore armor" is the engine's own: **Mod Target Damage Resistance** multiplies the target's armor rating for
one attack. Enderal's Bone Breaker (`069D53`) and Blade Breaker affinity (`14333A`) and EGO's mace bonus
(`XionWeaponBonusMace 001CEE`, × 0.65 with a weapon-tab `HasKeyword`) all use it; this perk is EGO's shape at
× 0. It affects the weapon's physical damage, which is what armor reduces; the burn is fire damage (fire
resistance) and is not changed. Perks stack by multiplication, so × 0 wins over any other.

The perk belongs to the **attacker**, so the player must have it. SPID never distributes to the player
([`spid.md`](../tools/spid.md)) and a weapon enchantment only reaches the struck enemy, so Rise carries
`ZP_RiseArmorPierceScript`: on `OnEquipped` by the player, `AddPerk` once. The perk is never removed: its two
conditions already limit it to Rise's own hits (weapon tab, so a Sting hit while dual-wielding does not count) on
an enemy with Sting's venom active (the 6 s window; each Sting hit restarts it). A follower wielding Rise does not
get it. Hidden since the rework (perk flag `Hidden`, no description; Rise's text no longer names it).
**[unverified in game]**

### Why the poison lost `DispelWithKeywords`

EGO's poison dispels every effect on the target that shares a keyword with it (so poisons replace each other).
Its keywords include `XionWeaponEnch`, which Rise's burn carries too: a Sting hit would have put Rise's fire out,
and wiped any poison the player had applied.

## The effects are enchant art (`tools/01`)

An MGEF's **EnchantArt** is an art object the engine hangs on the weapon's root while an enchanted weapon is
drawn; Chillrend's frost (`ChillrendEnchFX`) and the bound weapons' effects are made this way (Enderal's own
bound dagger: `bounddaggerencheffects.nif`). Both daggers use the same nif in first and third person, so one art
mesh fits both views. It shows only while the dagger is drawn, like every enchanted weapon's glow; sheathed, on the
ground and in the inventory the daggers look like Pretty's plain models. Both effects ride on the damage effect
itself.

**The art needs an EnchantShader (2026-11-13).** The first build gave `802`/`806` an EnchantArt and no
EnchantShader (to keep a glow off the hilt), and the curator saw **neither the coat nor the flames** in game:
plugin ticked, meshes deployed, so not a load problem. Every MGEF in the list whose enchant art shows pairs it
with an EnchantShader: Enderal's Druid affinity `02F1A1` (Chillrend's art `10A045` + Chillrend's shader
`10A043`), Enderal's bound dagger `02F453`, the vanilla bound sword/battleaxe/bow, Elemental Fury, Kittytails'
Aero poison. The only one without is Mihail's ancient skeletons' NPC contact effect, which no one has seen. So both
now carry `813`, Chillrend's shader with nothing left to draw: the art still makes the whole look. The engine rule
is inferred from the records, not read from the exe.

**…and Glow Be Gone removed it again.** The second look (with `813`) showed nothing either. The list runs
**Glow Be Gone Redone - NG** (Nexus 171248, SKSE) with `RemoveWeaponFX = true`: at kDataLoaded it sets
`data.enchantShader = nullptr` on **every** magic effect that is neither protected (Conjuration school; bound
weapon, summon, reanimate, invisibility, detect life… archetypes: why the bound dagger keeps its art) nor excluded
in its toml (its source, `src/plugin.cpp`, `PatchEffectSetting`/`ShouldRemoveFX`, read 2026-11-13; it never
touches enchant art or EFSH records). So both builds ran with no enchant shader at all. Its `RemoveActorFX` also
nulls `data.effectShader`, which is the CK's **Hit Shader** (CommonLib `EffectSetting` +0x30), so the green
poison shimmer `10CC64` and the burning look `01B212` on a struck enemy were stripped too; the exclusion brings
both back (the rest of the list's effects keep showing no hit glow).
`tools/03-glow-be-gone-exclusion.py` writes Glow Be Gone's own toml with `802` and `806` added to
`MagicEffectExclusionList` (`"Zenderal - Sting and Rise.esp:00000802"`; it keeps the low 12 bits for a light
plugin) into **Zenderal - Settings** (outranks Glow Be Gone; generated from a third-party file, not committed;
rerun after a Glow Be Gone update; a new file, so refresh MO2 before launching). **[verified in game]
2026-11-13**: with the exclusion in place the coat and the flames show (curator's third look). The art nifs were
never the problem: the same meshes stayed invisible in both builds that had no live enchant shader.

`tools/nifse.py` is the SE sibling of Clockwork Thunder's LE-only `nifsplice.py`: block-level read/write
(`Nif(raw).tobytes() == raw` asserted on every input), a BSTriShape codec for unskinned shapes, a lighting-shader
copier (shader + texture set + controller chain, refs remapped) and the particle block layouts used here.

**The blade** of each dagger is found, not hard-coded: in the lit shape that reaches highest (not `Scb`, not the
blood edges), the welded mesh island holding the tip (assassin blade 75 triangles, Y 4.36–42.86; Aeterna 1040,
Y 6.9–40.5). The winding is checked against the mesh's stored normals.

**Sting's coat** (`StingEnchFX.nif`, 1930 triangles): BSFadeNode + Chillrend's BSXFlags + one BSTriShape.

- The assassin blade is 75 long slivers, so it is refined until no edge is over 0.4 units (a split edge's
  midpoint is shared, so the shell stays closed), then pushed out along the averaged normal by 0.05 + up to 0.12
  units of 3D noise: lumpy goo on a 0.38-thick blade.
- **Coverage (curator 2026-11-13: "just have the tip and another 15% of the blade")**: the tip = the point, from
  where the blade stays under half its full width (`TIP_WIDTH`; Y 38.4 on the 4.4–42.9 blade; the clipped back
  edge starts narrowing at ~27, which would have made "the tip" 41% of the blade). The coat line sits 15% of the
  blade's length below that (`COVER_BELOW_TIP`): Y 32.6 ± 0.6 of noise (each face its own), about 27% of the
  blade from the point, with three runs reaching down to Y 30.7, rounded at the end; it thins to 0.015 over its
  last 1.2 units so it meets the steel. The first build coated all but the 3 units above the guard.
- Pretty's assassin blade is a blackened blade (its diffuse averages 12/255; its env map makes it read as dark
  steel in game), so the green point stands out against it.
- **Material = the puddle's, block for block**: `L1_GooBase09` of the winning `dweichorgoo01.nif` (JS Dwemer Ichor
  Barrels through PG Patcher; same as vanilla's but without shadows): glow shader, green own-emit (0, 1, 0.71),
  green specular, `FX_IchorBarrel.dds` + `water_v2_n.dds`, and its two UV-offset controllers (the slow flow).
  UVs are planar along the blade at the puddle's own density (33.5 units per UV), tangents in the puddle's
  convention (stored tangent = dP/dv, bitangent = dP/du, measured from it), vertex colours in the puddle's range
  (its 25th–90th percentile grey: the puddle's diffuse is mostly dark; the glow and specular carry the look).
- Read back with PyNifly as an independent check.

**Rise's flames** (`RiseEnchFX.nif`): `ChillrendEnchFX.nif` with 13 of 26 blocks changed (the others asserted
byte-identical):

- the held torch's flame `pFireballCore04` (winning `torch.nif`; Particle Patch only reorders its blocks): its
  BSEffectShaderProperty (`FXFireAtlas04.dds` with the `GradFireExplosion` palette), NiAlphaProperty, particle data
  (the 8-frame atlas; cap 7 → 32), colour and size curves;
- emitter box fitted to the Aeterna blade: 1.5 above its base to 1 short of the tip, 70% of its width
  (3.07 × 31.07 × 1.21, centre 0.11, 23.97, 0.02); the emitter node and the particle system sit on its centre;
- small, short flames: radius 2.2 ± 0.4 (the torch's 13), life 0.35 ± 0.08 s, speed 3 ± 2 in any direction,
  36 a second (~12 alive), no spin; gravity 90 upward **in world space** (the torch's 405 throws its flame ~20
  units up; this licks ~5), so they rise whichever way the blade points. Chillrend's lag bone and LOD kept.

`--preview <png>` draws both blades with the coat and the flame box; `--out-root` writes elsewhere (dry run).

## Asset permissions (checked 2026-11-13, Nexus pages read in the browser)

Pretty Enderal Armory (Enderal SE 1072, longlivethehighking) is a collection; its author's instructions: anyone
adding its models or textures to a project should contact the original authors; only the author's own work
(mostly recolours and fixes) is fully open. The two models we ship modified copies of:

| Ours | Original | Its permissions |
|---|---|---|
| `Sting.nif`, `StingBlade_d.dds` (+ Sting's texture paths) | billyro's **Assassin's Dagger**, from *A Second Month of Internet Deprivation Weapon Pack* (Skyrim LE 77112; Pretty's `textures\billyro\assassin\`, credited under Uniques) | Description: "Please don't redistribute this mod. If you wish to use these weapons in a custom mod, please let me know beforehand." **Ask billyro before shipping.** (billyro's newer SE packs, Lazy Weapon Pack 1–3, allow asset use with credit: a fallback model source) |
| `Rise.nif`, `RiseGold_*`, `RiseScabbardGold_*` | Caenraes' **Noble Armory** short sword (Skyrim SE 124896; Pretty's `weapons\noble armory\short sword\`, credited under Aeterna) | Open with credit: modification and asset use allowed without asking if Caenraes is credited; not in paid mods. **Credit Caenraes.** |

Everything else shipped here is generated geometry (coat, flames, spider, sun pommel, wings) or built from Bethesda's and
SureAI's own game files.

## Placement

**Placed 2026-11-15** (curator, each from a shortlist of three), by `tools/02`'s `place_records` with this folder's
`tools/surface.py` (below):
- **Midnight Sting**, REFR `831`: "Undercity Old Vault", Forgotten Stories' vault in Ark's underworld overrun by tunnel
  spiders (level 25; cell `FSNQ03Hideout 02A9C6:FS`, FS's header verbatim, the only plugin with it): **inside the open
  coffin** that lies on a table in its coffin room (CommonCoffinOpen01 ref `02AF7A`; the coffin stacked under it,
  `02AF7B`, ends at z 1475.2, under this one's floor), along its length, centred: position (-687.09, 4807.61,
  1480.64), heading pi/2, 0.1 over the floor (mesh z 3.79, z 1479.0). The two cluttered low tables were passed over.
- **Sunrise**, REFR `832`: "Old Soltyris, The Void", the end of the Sun Path desert ruin (cell
  `DesertAltSoltyrisL2KeyLvl2 06E4F3`, Skyrim.esm's header): **on the Dwemer pedestal** (`06EEB4`) where the dungeon
  leaves its reward (the Wall of Frost tome, two potions, a soul gem, a helmet), in the free strip beside them, each
  item's mesh 2 units clear (the tome as a 26 x 20 box: its mesh has no shape the reader understands): position
  (471.75, -2373.38, 1054.88), heading 1.963, 0.1 over the top (mesh z 87.42, z 1053.54).

Both lie with **Don't Havok Settle** (still until touched, so they never shove the pedestal's loot). Unverified in game.

`tools/surface.py` (shared: Whisper's and Argent Verdict's placements import it too): reads a cell's refs from the
reference serializations (Skyrim.esm, FS, EGO merged), samples the winning furniture mesh (node transforms composed,
hidden and skinned shapes skipped), finds its flat levels (`levels`: shelf boards, a table top, a coffin floor) and
asserts the one a placement names is there, rasters the surface's top and everything rising over it (its own walls and
rails, the items already on it) on a grid, and searches the nearest spot where the item's own footprint (from its
installed mesh) lies wholly on the top, clear of all of it (`find_spot`). It checks each ref it reads is still won by
one of those serializations (`check_winners`, this folder's overrider scan), and writes the cell override: the
winning header verbatim (name English only, its navmeshes and refs out, any field after them kept), our ref, and the
block / sub-block group files, round-tripping through Spriggit unchanged. Bethesda Z rotation: the compass sense
(angle 90 faces +X). Test before an in-game look with `help "Sting"` / `help "Rise"` → `player.additem <id> 1`.

## Regenerate

```
python src/StingAndRise/tools/00-scan-overriders.py   # live winners of every copied/referenced record
python src/StingAndRise/tools/01-build-assets.py      # Sting's and Rise's own meshes, enchant-art meshes, Blood Boil's and the spiderling's bursts, Rise's mote and fire nova, the grips, Rise's gold and ornament textures, the 3 palettes into Patch Collection (--out-root <dir> for a dry run)
python src/StingAndRise/tools/02-build-records.py     # YAML (refuses if a copied record changed hands)
python src/StingAndRise/tools/03-glow-be-gone-exclusion.py   # Glow Be Gone's toml + 802/806 into Zenderal - Settings
```

Rerun `01` after a change to FS's gore burst mesh (or PG Patcher's copy of it), the Mage Light orb
`lightspellactorfx.nif`, the Fire Storm ring `FireStormAreaEffect.nif` or the game's blood/light palettes. `01`
then `02` in that order: `02` reads Rise's bounds and swap targets from the deployed `Rise.nif`.
Rerun `01` and `02` after a Pretty Enderal Armory update: the art is fitted to Pretty's blades, the gold is built from
Pretty's textures, and `02` measures the bounds and reads the swap's shape name, index and normal map from Pretty's
mesh; both stop if a dagger mesh or texture no longer comes from Pretty. Rerun `00` → `02` after EGO, No Screen
Flashes or Flame Shot changes the copied records, and after a change to EGO's Young Moss Crawler or Mage Light, or to
Prophecy's Legion/Willing Sacrifice records (`02` copies them). The scripts: `src/StingAndRise/Scripts/source`, compiled `.pex`
committed (copy both into Patch Collection's `Scripts/` after a recompile).

## Status

Built 2026-11-13: deserializes clean, HEDR 1.7, ESL, round-trips through Spriggit with no differences; script
compiles (0 errors). Deployed into Patch Collection (plugin, script + source, both meshes, gold textures) while the
game was running; ticked in Ultra by the curator after EGO. Same day: Sting's coat cut to the tip + 15%, Rise made
gold, Blood Boil added (curator); rebuilt, round trip clean, all 50 FormKey references resolve, both scripts
compile. First in-game look (curator, same day): no coat, no flames; carrier shader `813` added (above), rebuilt,
round trip clean, 51 references resolve, deployed. Second look: still nothing; Glow Be Gone found nulling the
shader, exclusion written into Zenderal - Settings. Third look: **the coat and the flames show** (verified in game).
**Unverified in game**: the gold in both views, the hit shaders on struck enemies (back with the exclusion), the
6-second poison and burn (and that a new hit refreshes them), Rise ignoring armor on a Sting-poisoned target
(compare a hit on an armored enemy with and without Sting's venom), and Blood Boil (above).

On-hit rework, same evening (curator): records `819`–`827` + 3 scripts generated; round trip clean, all 83 FormKey
references resolve, the 5 scripts compile (0 errors), the bursts, mote and palettes built and deployed with the plugin
into Patch Collection (plugin already ticked in Ultra after EGO). Descriptions rewritten; Blood Boil and the armor
bonus hidden. **Unverified in game** (above).

Later the same evening (curator): the mote's burst became a weak fire nova (`828`), Sting's grip dark green, Rise's
grip ivory, Rise's angel (then, on the curator's word, a sun) and wings. The curator looked at Rise before any of it had shipped (a first build had
stopped on two bugs: my reference check could not read the Fire Storm mesh's shapes, and the resist value is
`ResistFire`, not `FireResist`) and then rejected the first ornament layout (above). Final build: round trip clean,
85 FormKey references resolve, 5 scripts compile, every guard-arm vertex inside the wing sheaths, assets + plugin +
scripts deployed into Patch Collection. **Unverified in game.**
