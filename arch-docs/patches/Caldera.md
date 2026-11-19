# Caldera

- **Source:** `src/Caldera/`
- **Ships:** `Zenderal - Caldera.esp` + 4 scripts + its own meshes `meshes/Zenderal/Caldera/Caldera.nif` (both views),
  `CalderaShockwave.nif` and `CalderaVent.nif` (the small volcanoes) + 3 sounds (the curator's own files, `tools/03`,
  not committed) + 11 generated textures (`textures/Zenderal/Caldera/Caldera_d`, `_n`, `_g0`..`_g4`,
  `Caldera_clean_d`, `_n`, `CalderaHandle_d`, `_m`; not committed), inside **Zenderal - Patch Collection** (as Argent Verdict). Enabled in Ultra right after Argent Verdict.
- **FormID block:** `0x800–0x81C` (`0x812`, the cracked field, retired: never reuse); `0x81D+` free (placement).
- **Needs:** Apocalypse - Magic of Skyrim (master: its volcano's controller script, meshes, sounds and lava bomb
  effects run as they are), powerofthree's Papyrus Extender (the blast's `FindAllReferencesOfFormType`,
  `IsPowerAttacking` on the swing), SKSE (`NetImmerse.SetNodeScale`, `Spell.SetNthEffectMagnitude`,
  `SKSE.GetPluginVersion`, `RegisterForActorAction`), **ZenProphecyRage.dll 1.12.0+**
  and Prophecy's `ZP_Aim` script (the ground under the enemy and under each small volcano, `ZP_Aim.GroundBelow`; both in
  Patch Collection; without them the eruption falls back to the enemy's own height). The mesh is built from Pretty Enderal Armory's, but ships as our own file.
- **Credits:** Caenraes (Noble Armory: the handle, via Pretty Enderal Armory, open with credit); Enai Siaion
  (Apocalypse's Volcano, used in place, and its fountain mesh shrunk for the small volcanoes); Craftsman Tools
  Replacer's hammer01 was only *measured* for the head's and handle's proportions (its permissions forbid reuse;
  nothing of it is copied).

## What it does

A unique one-handed mace (curator 2026-11-16: "lets make a Unique 1handed Mace, I want it to look like a Forge Hammer
with cracks in it with Molten lava in them"): a sledge-block forge hammer of dark forged iron whose head is cracked
through with molten lava. 33 damage, speed 0.9, crit 24 (EGO's Aeterna Mace 29 / 0.8, 0.9 under Mace Speed), Aeterna
material (EGO's smithing; grindstone temper with an Aeterna ingot), unique, no enchanting, not sold. Reach 1.15
(1.0 until the curator: "increase the hit range on the weapon a little too it seems a little short"; Precision's
weapon capsule follows the record's reach, and the hammer is short, 38 units).

- **Burning:** every hit sets the enemy ablaze, 5 fire damage a second for 6 seconds (Enderal's own Burning, as
  Sunrise's).
- **Charges:** every light-attack hit on an enemy adds a charge, 8 for a full one; every two charges light one more
  tier of the head's cracks (5 tiers: as found, and after an eruption, the head is whole, no crack at all; at the
  second hit the cracks appear with the first lava in them; each tier fills more of them with molten fire; a full charge is the curator's picture, 2026-11-16: "let this be the most intense the
  lava on the hammer gets and its starts with no lava on it", "and progressively gets more molten cracks on it"). The
  charge that fills it plays the curator's metal whoosh (curator: "add this sound when the hammer is charged",
  MA_Floraphonic_Swing_Whoosh_Metal_Hit_39.wav; vanilla's oil trap igniting `TRPOilIgniteHighSD` until then).
- **Eruption:** the next power attack on a full charge, **hit or miss**, for **20 Mana** (curator: "charge enough
  light attacks and a power attack can trigger a volcanic eruption (look for a spell effect or 2 to combine)"; then
  "add a mana cost to the power attack trigger and make it so you don't need to hit to trigger it"; Argent Verdict's
  Smite costs the same). It goes off as the hammer swings, under the enemy swung at (the nearest living enemy within
  260 units and 50 degrees of where the player faces), or on the ground 110 units in front of the player when there is
  none (under the player if that is a drop of more than 128). Without the Mana nothing happens and the charge stays:
  1. vanilla Fire Storm's ring of flame bursts out, scaled to 350 units, and every enemy within it takes fire
     damage and a stagger (never the player);
  2. Apocalypse's Volcano erupts there: its Pyroclasm burst, then its lava fountain rising out of the ground and
     spitting lava bombs for 6 seconds over 450 units, fire damage and a light stagger each (Apocalypse's: 10 s,
     750 units, 40 damage plus the Intense Flames fear, dropped: enemies running from a melee weapon), with the
     curator's volcano eruption as its sound ("and this one too", MA_MotionAudio_VolcanoErupting_01.wav);
  3. five smaller volcanoes break open round it, one after another over about a second and a half (curator: "remove
     the fissure effect and instead add smaller volcanos scattered around, they do very little damage mainly there
     for effect"): each 170-420 units from the volcano in its own fifth of the circle, Apocalypse's volcano at 0.4 of
     its size (cone and fountain about 165 units tall, its lava spray rising 0.4 as high), spitting a weak lava bomb
     every half second for 4 seconds, lobbed lower and landing within 160 units, 3 fire damage each (flat, no
     stagger); then each sinks away as the volcano does. A lava river bubbles at the volcano meanwhile ("add this
     sound for the lava fissures", flowing and bubbling lava river-001.wav, looping) for its 6 seconds and one more.
     Until then (the same day) a big glowing cracked field lay round the strike instead (record `812`, retired).

  All of it sits on the ground (curator: "make sure the Volcano spawns on the ground, sometimes it spawns waist
  height"), found by a ray under the enemy and under each small volcano, not the enemy's position (see How it works).
- **Damage by Elementalism** (curator: "I want the damage of the fissure / volcano to scale with elementalism", then
  "lower the damage of the fissure / volcano by 25 %"): the ring 22.5 + 0.45 per point, each lava bomb 7.5 + 0.19 per
  point (the player's Elementalism as it is then, potions and gear included, counted up to 100):

  | Elementalism | 0 | 25 | 50 | 75 | 100 |
  |---|---|---|---|---|---|
  | ring of fire | 22.5 | 33.75 | 45 | 56.25 | 67.5 |
  | each lava bomb | 7.5 | 12.25 | 17 | 21.75 | 26.5 |

  For scale: Enderal's Fireball ranks do 18 to 68. The first build did 60 and 25 at any skill. The small volcanoes'
  bombs do 3 at any skill.

Picks: head "Sledge block (C)" then "this one" on the picture of Craftsman Tools Replacer's hammer01; handle "Noble
Armory mace handle", then on the same picture "change the handle to this length and width".

## The mesh (`tools/01-build-mesh.py`)

Pretty's Aeterna Mace (`meshes/weapons/elven/elvenmace.nif`, = its first-person mesh, the same file) with:

- **the flanged head cut** (core, six flanges, top knob: 2012 triangles, 8 pieces, asserted) **and the long twisted
  shaft** (288 triangles);
- **the handle in hammer01's proportions to its head** (measured from its mesh: head 12.23 x 7.47 x 7.47, a square
  section, its underside 7.75 above the hand; haft from -15.59, 3.18 wide; haft end 1.57 above the head): the
  collar, leather grip, ring and pommel shortened x0.896 and thickened x1.268 (3.58 wide), the collar just inside
  the head's underside, the hand (the mesh origin: where a one-handed weapon is held) 8.74 below it; the grip runs
  from y -12.4 to 6.8. Normals and tangents follow the stretch. The belt loop `Scb` (round the grip below the hand)
  is widened with it (in the handle's frame: it has its own transform);
- **the pommel and the collar in the head's dark iron** (curator 2026-11-16: "change the pommel and steam connecting
  the head to the same color as the hammers head"): the handle's shape points at our copy of Noble's mace texture
  (`CalderaHandle_d` / `_m`) whose pommel and collar texels (225,393; no other kept piece shares them, asserted;
  widened 3 texels for mip edges, never into the grip's or ring's) are recoloured to `IRON`'s hue with their
  brightness scaled x0.58 so their median is the head's (0.150), engravings kept, and their environment mask 0.04
  (Noble's 0.21-0.27 shine; the head has no environment map). The leather grip and the gold ring stay Noble's;
- **a sledge head of our own**: a rounded box 13.8 (along the swing, x) x 8.4 x 8.4, edge radius 0.8, on the collar's
  axis, with the haft's end standing 1.77 out of the top (a domed cylinder, the haft's width), worn like the pommel
  (curator 2026-11-16, with pictures of both: "add the worn texturing from the pommel to the head stem"): its side is
  the iron-recoloured pommel's worn side panel (`STUB_SIDE`, 164 x 162 texels inside the pommel's own, asserted) four
  times round, its top the pommel's hexagonal end cap (`STUB_CAP`);
- **its textures painted from 3D fields** (one atlas chart per face, 64.5 texels a unit, 2048), so the cracks run on
  across every edge: forged dark iron with hammer dents and worn bright edges; fissures = a domain-warped 3D Voronoi's
  cell walls (cell 2.9) chosen by a hash of each wall's seed pair (symmetric, so both sides of a wall agree), with
  finer branches (cell 1.15) next to the lit ones; dark in the diffuse, grooved in the normal map (alpha =
  specular, none in a crack), molten in the glow map (white-yellow core, orange, deep red at the walls, a dim red
  halo; glow maps at 1024);
- **five copies of the head**, `ZP_CalderaHead0..4`, each under a node `ZP_CalderaTier0..4`: tier t lights 0, 12,
  23, 34, 45% of the primary walls (and 0, 5, 11, 16, 22% of the branches), each tier the last one's and more; only
  `Tier0` (no lava) is at scale 1 in the file. The first build ran 45 to 84%; the curator picked its 45% as the most
  the hammer gets. The dark fissures in the diffuse stay the first build's (84% of the walls) on tiers 1-4; tier 0's
  head has its own diffuse and normal map without a single fissure (`Caldera_clean_d` / `_n`; curator: "the zero hits
  can we remove all cracks and the cracks only appear after 2 hits"). Each copy has its own
  shader (never shared: Clockwork Thunder's freeze), the Noble shader turned into a glow shader: type 2, `Glow_Map`
  (SLSF2 0x40) and `Own_Emit`, no environment map, emissive white x2.2, the glow map in texture slot 2 (Forgemaster's
  lit parts set it up the same way);
- **both blood overlays** (`Edgeblood`, `Edgeblood01`, copies of the flanged head) moved onto the sledge head.

`CalderaVent.nif` (the small volcanoes): Apocalypse's volcano fountain
(`meshes/ApocNew/DestructionFire_Static_VolcanoNew_Fountain.nif`: cone rock, lava lake, outpour, fire, glow, ripples
and one lava-spray particle system; a Skyrim LE file, so it is edited block by block with Clockwork Thunder's
`nifsplice.py`) at `VENT_SCALE` 0.4. Built from **Apocalypse's own copy in its BSA**, not the winning loose one: PG
Patcher Output's copy is the same mesh with the cone's dirt-cliff texture swapped for PBR ones
(`textures\pbr\landscape\dirtcliffs\*`), which a PG Patcher rerun can move. The scale sits on a new node
`ZP_CalderaVentScale` under the root holding all of the root's children, never on the root itself (the game sets a
placed reference's root transform from the reference). The spray is a **world-space** particle system: a node's
scale moves where its particles are born (the cylinder emitter, gravity, drag and collider objects are nodes under the
scale node) but not how fast they fly or how hard they fall, so its emitter speed (420 +- 480 -> 168 +- 192) and its
planar gravity (810 -> 324) are scaled by 0.4 too, and the spray rises 0.4 as high (v squared over 2 g). The
particles' size is left alone: the particle system's own node scale (1.85 in the file) is what sizes them, and it now
sits under the scale node. That reading of the engine is unverified: if the spray looks far too small (sized twice) or
far too tall, this is where to look. The cracked field (`CalderaFissures.nif` + 3 textures, a 2D Voronoi of charred
plates with lava in every crack on Dawnguard's frozen-lake crack plane) was removed from `01` and from Patch
Collection on 2026-11-16; Caldera had never been committed, so this description is all that is left of it.

`CalderaShockwave.nif`: vanilla Fire Storm's ring (`meshes/magic/FireStormAreaEffect.nif`, the winner) with its root
scaled so its reach marker `BlastRadiusNode` (615) is the eruption script's `ShockRadius` (350), as Sunrise's nova.

The mesh path `*\zenderal\caldera\*` is in PGPatcher's blocklist (`Tools/PG Patcher/PGPatcher/cfg/settings.json`,
2026-11-16): PG Patcher Output outranks Patch Collection, and a patched copy would drop the glow shader.

## Records (`tools/02-build-records.py`)

| ID | Record | What |
|---|---|---|
| `800` | WEAP `ZP_Caldera` "Caldera" | EGO's Aeterna Mace `07C990` (the winner), stats above, keywords Aeterna material, melee, mace, `MagicDisallowEnchanting`, `WeapTypeUnique` (no `VendorItemWeapon`), model `Zenderal\Caldera\Caldera.nif`, bounds measured from it, enchantment `803` (charge 3000), script `ZP_CalderaEquipScript` |
| `801` | STAT `1stPersonZP_Caldera` | `1stPersonElvenMace 036BCF` on the same mesh |
| `802` | COBJ `ZP_TemperCaldera` | the Aeterna Mace's grindstone temper `148ABB`, new product |
| `803` | ENCH `ZP_CalderaEnchant` | on every hit: `804` always; `805` on a light attack on a hostile while `807` < 8; `806` on a power attack on a hostile while `807` >= 8 and the player has 20 Mana (the fallback: the swing comes first) |
| `804` | MGEF `ZP_CalderaBurnEffect` "Burning" | Enderal's Fire Arrow burn `067252` (Flame Shot's copy, the winner), no `NoRecast`, FireFXShader `01B212` |
| `805` | MGEF `ZP_CalderaChargeMGEF` | a charge: instant script effect `ZP_CalderaChargeScript`, hidden |
| `806` | MGEF `ZP_CalderaEruptionEffect` "Eruption" | the release on a hit: `ZP_CalderaEruptionScript`, the item card's text; the fallback for a swing the game never reported |
| `807` | GLOB `ZP_CalderaCharges` | 0..8 |
| `808`, `809` | MGEF / SPEL `ZP_CalderaTiers` | the cracks' display: constant script effect `ZP_CalderaTiersScript` (every second), the ability, added while the hammer is equipped; it also hears the hammer's swings and casts `81B` |
| `80A` | EXPL `ZP_CalderaShockwave` | Fire Storm's explosion `08196B` (Embers XD's, the winner) on `CalderaShockwave.nif`, radius 350; no force, damage or image space |
| `80B`–`80D` | SPEL `ZP_CalderaBlast` + its 2 MGEFs | fire damage, 45 in the record (the Elementalism-50 value; the eruption script sets it before each eruption) (Apocalypse's lava bomb damage `0834B5`, Unresolved References Cleanup's winning copy, Touch, no projectile or script, its never-the-player condition kept) + stagger 0.5 (`0834BA`, Touch) |
| `80E` | EXPL `ZP_CalderaVolcano` | Apocalypse's Volcano explosion `0834AE` (Pyroclasm), placing `80F`; no image space |
| `80F` | ACTI `ZP_CalderaVolcanoController` | Apocalypse's controller `0834AD` (`WB_VolcanoController2_Script`: fountain `0834B2`, light `0834B8`), 6 s, bombs within 450, firing `810` |
| `810` | SPEL `ZP_CalderaLavaBomb` | Apocalypse's lava bomb `0834B3`: damage `0834B5` 17 in the record (the Elementalism-50 value, set by the eruption script), stagger `0834BA` 0.25, no Intense Flames fear |
| `811` | SOUN `ZP_CalderaChargedSound` | the full charge: `815` (vanilla's `TRPOilIgniteHighSD 04251D` until the curator's sound) |
| `812` | retired | was ACTI `ZP_CalderaFissures`, the cracked field; never reuse |
| `813` | SNDR `ZP_CalderaLavaLoopSD` | the curator's lava river, looping, mono, heard within 1800 (`SOMMono01800_verb`); played through `81A` |
| `814` | SNDR `ZP_CalderaEruptionSD` | the curator's volcano eruption, mono, heard within 6000 (`SOMMono06000_verb`); `80E`'s sound |
| `815` | SNDR `ZP_CalderaChargedSD` | the curator's metal whoosh, mono, `SOMMono06000_verb` (Argent Verdict's charged bell's) |
| `816` | ACTI `ZP_CalderaVentController` | a small volcano: Apocalypse's controller `0834AD` again (`80F`'s record, the same `WB_VolcanoController2_Script`) with fountain `817`, light `818`, 4 s, a bomb (`819`) every 0.5 s within 160, aimed 700 up (the volcano's 2000), the fountain rising 11.2 (28 x 0.4); no looping sound |
| `817` | ACTI `ZP_CalderaVentFountain` | Apocalypse's fountain `0834B2` on `CalderaVent.nif`, bounds x0.4; no looping sound (five large-fire loops would drown the volcano's) |
| `818` | LIGH `ZP_CalderaVentLight` | Apocalypse's fountain light `0834B8`, radius 192 (384) |
| `819` | SPEL `ZP_CalderaVentBomb` | Apocalypse's lava bomb `0834B3`: damage `0834B5` 3 (flat), no stagger, no fear |
| `81A` | SOUN `ZP_CalderaLavaLoopSound` | `813`, played by the eruption script at the volcano and stopped after 7 s |
| `81B` | SPEL `ZP_CalderaEruptionSwing` "Eruption" | the eruption on the swing: a self spell (Prophecy's Orbit Ward spell `B76`'s shape) carrying `81C`, cast on the player by `ZP_CalderaTiersScript` |
| `81C` | MGEF `ZP_CalderaEruptionSwingEffect` | `ZP_CalderaEruptionScript` on the player (Self, hidden), `806`'s properties |

The generator checks every copied record's winner (Ultra load order, the fountain `0834B2` and its light `0834B8`
included), the scripts' `Hits` (8), `Tiers` (5), `ManaCost` (20), `ShockRadius` (350), `SoundLife` (7) and the damage scaling
(`BlastBase` / `BlastPerPoint` / `BombBase` / `BombPerPoint` / `SkillCap`) against its own constants, and that `01`
writes the small volcano's mesh where `817` looks. The eruption effect's properties also carry the lava bomb spell
(`810`, whose damage the script sets), the small volcano `816`, the lava river `81A` and `XMarkerHeading 000034` (the
ground marker).

## How it works

1. **Charges** (`ZP_CalderaChargeScript`, Argent Verdict's charge script on Caldera's forms): `GlobalVariable.Mod`
   (thread-safe; a hit that finds it full gives it back; a corpse gives none, a target killed by the hit within 1 s
   of its death does: `Fresh`, Argent Verdict's corpse fix of 2026-11-19), the tier ability added if missing, then
   `ZP_CalderaTiersScript.Show(player, Tier(charges))`: exactly one `ZP_CalderaTier` node at scale 1, both views.
   `Tier` = charges x 4 / 8 in whole steps, so the top tier lights only at a full charge.
2. **The display** (`ZP_CalderaTiersScript`, ability `809`): sets the tier on start and every second, because a
   weapon's 3D is rebuilt with the file's scales (Tier0) on every equip, load and race change.
   `ZP_CalderaEquipScript` adds it on equip and removes it once the hammer is out of hand.
   It also **hears the swing** (Whisper's Soul Cleave's way): SKSE's `RegisterForActorAction(0)` (weapon swing),
   registered on start and again on every poll (a set; an ability started by an older build picks it up without a
   re-equip); a swing whose source is the hammer, with `807` at 8 and PO3's `IsPowerAttacking`, casts `81B` on the
   player, hit or miss. The enchantment's `806` stays as the fallback for a swing the game never reports (it needs the
   hit, the full charge and the Mana); the swing comes first, so it normally finds the charges gone.
3. **The eruption** (`ZP_CalderaEruptionScript`, from `81C` on the player or `806` on a struck enemy): reads every
   property into locals first (an instant effect is gone long before the small volcanoes are); on the swing it picks
   the enemy swung at (`FoeInFront`: the nearest living hostile within 260 and 50 degrees of the player's heading,
   `GetHeadingAngle`); claims the charges (a second release finds none), then the Mana: below 20 it gives the charges
   back and logs it, otherwise `DamageActorValue("Magicka", 20)`; back to tier 0;
   sets `80B`'s and `810`'s fire damage (effect 0 of each) from the player's Elementalism (actor value `Destruction`,
   capped at 100) with SKSE's `Spell.SetNthEffectMagnitude` (per session, as Sunrise's nova; the records carry the
   Elementalism-50 numbers); finds the ground under the enemy (with no enemy: from 96 above the player's feet, 110
   in front of them, or under the player when that ground is more than 128 below their feet):
   **`ZP_Aim.GroundBelow`** (ZenProphecyRage.dll
   1.11.0, see [Prophecy](Prophecy.md)) casts one ray straight down from 24 above the enemy's position (64 over a dead
   or knocked-down enemy, PO3's `GetActorKnockState`) to 2048 below on the pathing-pick layer (`L_PATHINGPICK`: never
   actors, props or clutter) and returns the first terrain / static / anim static surface's height (1.12.0: it passes
   through trees, water, invisible walls, collision boxes, debris and the transparent layers; 1.11.0 stopped on them,
   and its first logged eruption on a dead goblin found "ground" 20 units above the body). The enemy's own position is its feet only while it stands: a power attack
   that kills or knocks it down leaves it ragdolled, and a ragdoll's position rides its body, which is why the volcano
   sometimes rose at waist height (curator 2026-11-16; Apocalypse's controller puts the fountain exactly where its
   explosion is, and the explosion was placed at the enemy). An `XMarkerHeading` (`000034`) goes there, and `80A` and
   `80E` are placed at it, and the lava river `81A` starts playing on it (`Sound.Play`); no hit, or no DLL (the native
   is unbound, None), falls back to the position's own height. Then it applies `80B` (blamed on the player) to every
   living enemy within 350 of that spot and logs `[ZP Caldera eruption]` (the swing or the hit, where, the height and
   the ground found, the Mana, Elementalism, both damages). Then the **small volcanoes** (`Vents` 5): from a random turn, each in its own fifth of
   the circle (+-20 degrees), 170-420 units out (`VentNear` / `VentFar`), a marker at the volcano's ground height
   there and `ZP_Aim.GroundBelow` from it, starting 48 + 0.6 x its distance above that height (a 30-degree slope
   uphill; 48 + 0.25 x indoors, where a ceiling can be close: a ray starting above a ceiling lands on it); no ground,
   or ground more than 48 + 0.6 x its distance below the volcano's (a ledge, a lower floor), gets no small volcano.
   Otherwise `816` is placed on that ground, and 0.15-0.4 s later the next. Without ZenProphecyRage.dll
   (`SKSE.GetPluginVersion`) they stand at the volcano's ground height. Each logs a line (its distance, the ground
   found, or why none). `816` runs Apocalypse's own controller script: `OnLoad` places fountain `817` and light `818`,
   raises the fountain 11.2 and `RemoteCast`s `819` every 0.5 s for 4 s, then deletes it all. 7 seconds after the
   eruption (`SoundLife` = the volcano's 6 + 1) the lava river stops (`Sound.StopInstance`) and the marker is deleted.
   (`ZP_Aim.LayOnGround`, built for the cracked field in ZenProphecyRage.dll 1.12.0, is no longer called; the native
   stays in the DLL.) `80E`'s PlacedObject is the controller: its `OnLoad` raises
   the fountain and `RemoteCast`s a lava bomb every 0.125 s from just above the ground to a random point 2000 units
   up within the radius, blamed on the player; the bombs fall back as Apocalypse's do. A `RemoteCast` blamed on the
   player is re-aimed by Hit Where You Aim unless [`RemoteCastAimFix`](RemoteCastAimFix.md) lets it be (it starts
   far from the player here).

## Regenerate

```
python src/Caldera/tools/01-build-mesh.py      # mesh, shockwave ring, small volcano, textures into Patch Collection
                                               # (--out-root <dir>: dry run)
python src/Caldera/tools/02-build-records.py   # YAML (refuses if a copied record changed hands, Pretty's mesh moved,
                                               # or tools/01's mesh is not the winner of its path)
python src/Caldera/tools/03-install-sounds.py --lava "<flowing and bubbling lava river-001.wav>" \
    --eruption <MA_MotionAudio_VolcanoErupting_01.wav> --charged <MA_Floraphonic_Swing_Whoosh_Metal_Hit_39.wav>
                                               # the curator's three sounds: 16-bit 44.1 kHz mono; the river's first
                                               # 16 s looping without a seam (Whisper's mono_loop)
```

Scripts compile to `Scripts/compiled` (committed) and ship in Patch Collection's `Scripts` (sources in
`Scripts/Source`). Rerun `01` then `02` after a Pretty Enderal Armory update (the mesh comes from its Aeterna Mace;
`01` asserts the head, shaft, collar and grip pieces) or a Fire Storm mesh change; `02` after EGO changes the Aeterna
Mace, Flame Shot its burn, or Apocalypse / the cleanup patch the volcano records. Tune the eruption in `02`'s
constants (`BLAST` / `BOMB` = base and per point of Elementalism, with the eruption script's `BlastBase` ...
`BombPerPoint`; `ERUPT`, `ERUPT_RADIUS`; the small volcanoes' `VENT_ERUPT`, `VENT_RATE`, `VENT_RADIUS`,
`VENT_HEIGHT`, `VENT_BOMB`, `VENT_LIGHT`, their count and spread in the eruption script's `Vents` ... `VentGapMax`,
their size in `01`'s `VENT_SCALE`, which `02` reads), the charge in `HITS` (and the scripts' `Hits`), the look in `01`'s
(`HEAD_SIZE`, `TIER_SHARE`, `LAVA`, `EMISSIVE`, the handle from hammer01's measurements). Rerun `01` then `02` after an
Apocalypse update (`01` asserts the fountain's one particle system, its speed and gravity). The eruption script also
compiles against Prophecy's `ZP_Aim` (add `src/Prophecy/Scripts/source` to the import path).

## Placement

**Not placed yet**: where it is found is the curator's call. Test with `help "Caldera"` → `player.additem <id> 1`.

## Status

Built 2026-11-16: the look rendered offline before deploying (every tier, the handle in hammer01's proportions;
the same day the tiers re-ramped from no lava to the curator's picked look); scripts compiled (0 errors), plugin round trip through Spriggit with no differences, all 54 FormKey
references resolve; mesh, textures, plugin and scripts deployed into Patch Collection, the plugin enabled in Ultra.
The same day: the fissures (record `812`, the curator's two sounds `813`/`814`) and Reach 1.15, round trip clean,
59 references resolve, deployed. **Unverified in game**: everything (the curator had held the hammer before the reach
change). Things to look at: the glow's strength (emissive x2.2 with Bottled Shaders'
bloom), the tiers switching as the charge builds, the thick grip against the hand's fingers (3.58 wide; hammer01's
proportion, thicker than the list's 1H maces), the hammer's short length (38 units overall; Precision's swing capsule
follows the mesh, so it reaches less than a 60-unit mace), the volcano rising at the enemy and its bombs falling round
it (not towards the crosshair), the eruption's damage.

Later the same day: the eruption's damage scales with Elementalism (75% of the first proposal, curator's call), the
fissures are one big cracked field on a 300-unit disk (rendered offline first), and the ring, volcano and fissures are
laid on the ground found by `ZP_Aim.GroundBelow` (ZenProphecyRage.dll 1.11.0, built and deployed); scripts compiled
(the eruption script's bytecode checked for the ray and both magnitude calls). **Unverified in game**: the ground ray
(the Papyrus log line shows the enemy's height and the ground it found), the scaled damage, the field's look in
game.

Tested by the curator the same evening: "make the fissures spawn on the ground sometimes they float up". The log had
two eruptions: a living enemy's ground 1.3 above its feet, a dead goblin's 20 units *above* its body (1.11.0's ray
stopped on whatever the pathing pick meets first). ZenProphecyRage.dll **1.12.0**: the ray stops only on terrain,
statics and anim statics, starts 64 above a dead or knocked-down enemy, and `ZP_Aim.LayOnGround` tilts the field to
the ground's slope. Built clean, deployed with both scripts; records unchanged. **Unverified in game.**

Later that evening, before that was tested: "remove the fissure effect and instead add smaller volcanos scattered
around, they do very little damage mainly there for effect". The cracked field (`812`, its mesh and textures) is
gone; five small volcanoes (`816`–`819`, `CalderaVent.nif`) break open round the volcano, each on its own ground ray,
and the curator's lava river plays once at the volcano (`81A`). `01` rerun: the hammer's mesh and every texture
byte-identical to before (md5), only `CalderaVent.nif` new; the fissure files deleted from Patch Collection; script
compiled (0 errors), plugin round trip clean, all 64 FormKey references resolve; plugin and script deployed. **Unverified
in game**: the small volcanoes' size and spray (see the mesh section), where they land (the Papyrus log has a line per
small volcano), their weak bombs, the lava river starting and stopping.

Later that night: "add a mana cost to the power attack trigger and make it so you don't need to hit to trigger it".
The cracks' ability (`ZP_CalderaTiersScript`) now hears the hammer's swings and casts a new self spell (`81B`/`81C`,
the same eruption script) on a full-charge power attack, hit or miss; the eruption spends 20 Mana (kept charge
without it) and goes off under the enemy swung at or in front of the player; the enchantment's hit path stays as the
fallback, now also asking for the Mana. Both scripts compiled (0 errors; the swing listener and `FoeInFront` checked in
the `.pex`), plugin round trip clean, all 66 FormKey references resolve. **Unverified in game**: the swing trigger
(the log line says "on the swing" or "on the hit"), the Mana cost, where it erupts with and without an enemy in
front.

**The first test of that build crashed at load** (2026-11-16 23:05, crash log `SkyrimSE.exe+14AA7ED`): the eruption
script's docstring had grown to 4407 bytes, over the game's script loader buffer (see
[papyrus.md](../workspace/papyrus.md)). Cut to 891 bytes, recompiled and redeployed; `02` now refuses a Caldera
script whose docstring is over 3000 characters (`check_docstrings`, tested on a 4407-character one). The rest of the
list's `.pex` strings were scanned: none over 3854.
