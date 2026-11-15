# ArgentVerdict

- **Source:** `src/ArgentVerdict/`
- **Final** (curator 2026-11-15: "this version we've made is THE Argent Verdict", "remove the other versions"): the
  spiked gauntlet head and the Smite, version 3. The hand head, the gauntlet's second weapon record and every older
  Smite are removed, and their backups in `E:/Zenderal-backups` deleted (git history keeps what was committed).
- **Ships:** `Zenderal - Argent Verdict.esp` + its own mesh `meshes/Zenderal/ArgentVerdict/ArgentVerdict.nif` (the
  spiked gauntlet; `ArgentVerdictGauntlet.nif` until 2026-11-15) + 7 generated textures from `tools/01` and the
  Smite's from `tools/03` (not committed), inside **Zenderal - Patch Collection** (as Sting and Rise)
- **FormID block:** `0x800–0x860` (`0x802` retired: the first build's texture swap; `0x806`–`0x807` retired: the
  gauntlet's own record and first-person static while it was compared with the hand head; `0x80C`, `0x845`–`0x847`,
  `0x84B`, `0x84F`–`0x860` the Smite (version 3), its charges and orbs (`0x85E` retired); `0x841`–`0x844`,
  `0x848`–`0x84A`, `0x84C`–`0x84E` retired (version 2); `0x808`–`0x80B` and `0x80D`–`0x840` retired (the Judgement
  Blade and the Penance fan, scrapped 2026-11-14): never reuse; `0x861+` free for the placement)
- **Needs:** Zenderal - Prophecy (master: the Smite effect's shape), powerofthree's Papyrus Extender (the chain's
  `FindAllReferencesOfFormType`); the mesh is built from Pretty Enderal Armory's, but ships as our own file, so Pretty
  is not needed at run time; Dark Hierophant Magic is **not** installed (its records and files are copied)
- **Credit:** the model is **Caenraes' Noble Armory** warhammer (Skyrim SE Nexus 124896: modification and asset use
  allowed with credit, not in paid mods), shipped in Pretty Enderal Armory (longlivethehighking). Since v2 a modified
  copy of that mesh ships with us. Credit Caenraes in Patch Collection's description. The Smite's glow, impact and
  strike sound are **Kittytail's**, from Dark Hierophant Magic (Skyrim SE Nexus 108499: asset use and modification
  open; Kittytail has also given the curator permission to patch her mods for Zenderal): credit Kittytail too. The
  church bell is the curator's licensed Motion Array sound (`MA_A2DStudios_ChurchBellsImpacts_3.wav`), not committed.
- **Pillar:** modern combat (curator's request, 2026-11-13)

## What it does

A unique silver great hammer (there was none): **Argent Verdict**, all polished silver. Its head is a **clenched
human hand gripping a stake** that carries the face and spike, **bones breaking through the back of the hand**;
its **forearm flows into the handle** under a **bracelet of thorns**, two **thorny rose vines** winding up it, and
the grip is dark navy leather. **Smite** (version 3, 2026-11-14): every two light attacks that hit an enemy light a
very small mote of runic light on one of the head's four knuckles (8 for a full charge since the balance pass of
2026-11-15; any hit, one a mote, before) (Kittytail's Absolution rune circle, about 1.5 units across, round
each gauntlet spike or on each bone knuckle); the hit that lights the fourth rings a church bell (ready). Once all
four are lit, the next power attack, for 20 Mana (none spent, charge kept, below it), **calls Kittytail's
Absolution beam down from the sky** onto up to four enemies round the player (the struck one first, then the nearest
within 800 units): her rune circle hangs in the sky over each and the beam runs straight down onto it, a church bell
rings and the motes go out; each enemy takes 80 to Health and 40 to Stamina and Magicka (40 / 20 until the first
test: "Raise the damage"), and each beam scatters four orbs out along the ground that strike the enemies in their path
for 15: Prophecy's Smite orbs (starburst flares) in Dark Hierophant's white with black wisps.
Undead take double. It is a
silver weapon (EGO's silver perks against undead and ghosts; with Prophecy's Smite talent its ordinary hits get that
talent's 15% too).

Curator's choices (2026-11-13), in order:

- v1: the base among Pretty's two-handed hammers whose original authors allow modification (the shortlist and each
  source mod's permissions are in the memory note `project_silver_greathammer`): **the Aeterna Warhammer**; name
  *Argent Verdict*; "All silver, white grip"; "Power attacks have a 25% chance to Smite".
- v2: "change the leather wrapping handle to a dark navy, enlarge the head of the hammer by 15% / change the middle
  section of the head to a clenched fist, resembling holding the hammer and spike like a stake"; on the first fist,
  "make the hand look more human like".
- v3: "reduce the size of the hand by at least 30% it looks a little too comical, can you add more complex detailing
  to the hand itself? engravings or skin texture, still metallic silver".
- v4: "make the hand a skeleton instead, remove the engravings from the hand base instead wrap metal roses around
  it" ("for the hand I mean a skeletal hand").
- v5 (2026-11-14): "can we lose the base with the roses and have the hand mold into the handle?", "and make the hand
  human again", "you can add a bracelet of thorns to help blend the wrist to handle"; then "remove the engraving from
  the back of the hand, instead have skeletal structures protruding from the hand"; then, of the bare forearm, "can
  we add some detail to this, maybe leaves and roses".
- Gauntlet variant (2026-11-14): "save what we have but make a variant that is a spiked Gauntlet instead of a hand
  with a poorly blended wrist". The hand (v5) is kept as it is (rebuilt byte for byte); the gauntlet is a second
  weapon record on its own mesh, **Argent Verdict (Gauntlet)**, so the two can be compared in game. Settled
  2026-11-15: the gauntlet is THE Argent Verdict, on `800`'s own mesh path; the hand head and `806`/`807` removed.
- Gauntlet v2 (2026-11-14, from in-game screenshots of the first build): "change the black palm to metal, is there
  a way we can make the wrist section more vertically symmetrical rather than leaning diagonally? add some metal
  Rose and thorns".
- Gauntlet v3 (2026-11-14, texture only): "overall sculpt looks good, can we just add more worn / scratched look to
  the smooth metal parts such as fingers and back of the hand", "similar to the pommels texture".
- Judgement Blade (2026-11-14): "Now to change the weapons effect, there should be a the Dark heirophant spell pack in
  my downloads can you give me some options for a Smite weapon effect?"; of five options from the pack (Judgement
  Blade, the same with Searing Light on every hit, Chains of Light, Penance Fan, Ordinance of Light) the curator
  picked **Judgement Blade**. "we have perms from Kitty to patch things for Zenderal". Then the Penance fan (light
  hits charge eight swords round the player, a power attack shoots them up and drops the Judgement Blade).
- Smite (2026-11-14), after five tests of the Judgement Blade and the fan (the last: "this isn't working", "the swords
  are massive.", "that white you are seeing is 1 sword.", "I don't understand why you don't just use the kittytail
  spell that has the swords already positioned the way i want"): "lets scrap this idea for the unique weapons effect.
  lets just do a unique smite with a Dark hierophant colored Lightning bolt than chains to enemies, let it be a 20%
  chance"; "the smite still comes from the sky vertically"; with the curator's church bell, "add this sound
  addtionally to the smite".
- Charges (2026-11-14, with a picture of Kittytail's Absolution rune circle): "lets make the chain lighting apply from
  the hammer instead of a chance lets have it build charges", "can the charges be very small motes of light that light
  up on each of the knuckles of the hammers gauntlet headpiece", "maybe this circle effect shown in the picture as the
  mote but make them very small on each knuckle of the hammers head", "after all knuckles are lit, the next power
  attack unleashes the chained lightning hit (keep the white and black color)", "so no more lightning from the sky
  just from the hammer". That is version 2 (below; removed 2026-11-15).
- Version 3 (2026-11-14, with a picture of Absolution's beam): "ok bank this and now we make a version 3 / Keep the 4
  knuckle motes / instead of the Chain lightning, smite 4 enemies in proximity to the player on charged power attack.
  the smite beams come from the sky like regular smite. but the effect is like the effect from the picture (I believe
  this is the Absolution spell in Dark hierohant)".
- Orbs (2026-11-14, "beams look great now"): "can we add the motes we use on the knuckles as orbs that fire out of
  the smite beams (just like the regular Smith from Prophecy talent but dark heirophant effect)". The first orbs (the
  motes' rune circle) were not seen: "no orbs appear"; then, with a picture of Prophecy's Smite orbs: "this is what a
  regular smites orbs look like, I want this but the Dark heirophant effects / colors".

**The gauntlet variant**: the same hammer, the same grip on the stake, but the hand is a **spiked plate gauntlet**:
plate lames down every finger and the thumb, a spike over each middle knuckle, a knuckle guard with a gadling over
each knuckle, a riveted back plate with a ridge and a centre spike, the palm and the inside of the fist **silver
scale mail**, and **telescoping wrist lames** stacked straight down the shaft under the wrist, the top one ringed
with six spikes, a collar under the last. Two **thorny rose vines**, mirror images of each other, rise from the back
of the collar, wind round either side of the lames and meet at the front under **one large rose**, a smaller rose
on each side. The lames carry the wrist into the handle, where the hand's forearm was "poorly blended".

| FormKey | Record | From |
|---|---|---|
| `800` | WEAP `ZP_ArgentVerdict` "Argent Verdict" | the spiked gauntlet head (the hand head until 2026-11-15); EGO's Aeterna Warhammer `07C993` (the winner): 46 damage (EGO 42; Qalian's Absolution 44), crit 23, speed 0.65, value 1500, weight 28; keywords Aeterna material (EGO's smithing), melee, warhammer, `MagicDisallowEnchanting`, `WeapMaterialSilver 10AA1A`, `WeapTypeUnique` (no `VendorItemWeapon`, as Qalian's Absolution); model `Zenderal\ArgentVerdict\ArgentVerdict.nif` (`tools/01`'s; textures in the mesh, no swap), bounds measured from it; enchantment `803`, charge 3000 |
| `801` | STAT `1stPersonZP_ArgentVerdict` | `1stPersonElvenWarhammer 036BD2` on the same mesh (Pretty's 1st-person mesh is the same file) |
| `802` | *retired* | v1's TXST `ZP_ArgentVerdictSilver` (the texture swap onto Pretty's mesh); never reuse |
| `803` | ENCH `ZP_ArgentVerdictSmite` | weapon enchantment (Touch), cost 1, charge 3000, on hits on a target hostile to the player (instant: tested once per hit): `851` on a light attack (player not power attacking) while `852` is below 8; `804` on a power attack while `852` is 8 and the player has at least 20 Magicka (Mana). Until 2026-11-15: `851` on any hit below 4, `804` at 4 with no Mana; until 2026-11-14: `804` on 25% of power attacks, then the Penance fan's charges, then 20% of hits |
| `804` | MGEF `ZP_ArgentVerdictSmiteEffect` "Smite" | the release: Prophecy's Smite effect `A67`'s shape (instant script effect on the struck target) running `ZP_ArgentVerdictSmiteScript` (version 3: the sky beams); not hidden, with the item card's description |
| `805` | COBJ `ZP_TemperArgentVerdict` | the Aeterna Warhammer's grindstone temper `148AB7`, new product (Aeterna ingot; enchanted, so Enderal's Arcane Blacksmith rule) |
| `806`, `807` | *retired* | WEAP "Argent Verdict (Gauntlet)" and its first-person static (2026-11-14 to 2026-11-15): the gauntlet beside the hand head while the curator compared them; the gauntlet is `800`'s own mesh now; never reuse |
| `80C` | SNDR `ZP_ArgentVerdictStrikeSD` | the strike: Kittytail's `_BL_ExpFlareSD 863` on `SmiteStrike.wav` (her FlareBig 1.3 times faster, 2.4 s); the impact's sound |
| `808`–`80B`, `80D`–`840` | *retired* | the Judgement Blade and the Penance fan (2026-11-14, scrapped the same day); never reuse |
| `841`–`844`, `848`–`84A`, `84C`–`84E` | *retired* | version 2's bolt (PROJ, light), the bolt from the hammer, the chain's jumps, Kittytail's impact set / impact, the strike's sound marker; removed 2026-11-15 with its backup; never reuse |
| `845`, `846` | MGEF a beam's damage to Health, and its twin on undead | Kittytail's Absolution effect `_BL_DischargeMGEF 801` (ResistMagic), Touch, fixed numbers, hidden, her white glow `84B`, no projectile, casting art, screen flash, impacts or sounds, hostile actors only; `846` only on `ActorTypeUndead 013796` |
| `855` | MGEF a beam's damage to Stamina and Magicka | her `_BL_DischargeStaminaMagickaMGEF 802`, trimmed the same way |
| `847` | SPEL `ZP_ArgentVerdictStrike` | 80 / 80 undead / 40 (40 / 40 / 20 until the first test), Touch: the release script's `DoCombatSpellApply` on each smitten enemy |
| `84B` | EFSH `ZP_ArgentVerdictShockGlow` | Kittytail's `_BL_EffectShaderWhiteShockGlow 848` on our white `Verdict_gradshockhitW.dds` |
| `856` | ACTI `ZP_ArgentVerdictBeamFX` | a smite beam (`VerdictSmiteBeam.nif`), nameless; FXEmptyActivator `0B79FF`'s record |
| `860` | ACTI `ZP_ArgentVerdictOrbSpawner` | the orbs' spawner, placed by `857` (its PlacedObject); FXEmptyActivator's record (its empty model), script `ZP_ArgentVerdictOrbSpawnerScript` |
| `85A` | PROJ `ZP_ArgentVerdictOrbProj` | an orb: Prophecy's Smite orb `ZP_Holy_LightshaftScatterProj A4B` (Kittytails' Holy Templar light shaft: 540 a second, range 1620) on `VerdictOrb.nif`, light `85F`; her Cone type (one build's Missile changed nothing, see the orbs' postmortem) |
| `85F` | LIGH `ZP_ArgentVerdictOrbLight` | its light `A49` in a cool white, radius 300 (Prophecy's 600: up to 16 orbs at once) |
| `85B`, `85C` | MGEF an orb's damage to Health, and its twin on undead | her Absolution effect `801` as `845`, but Aimed on `85A` |
| `85D` | SPEL `ZP_ArgentVerdictOrb` | 15 / 15 undead, Aimed: the beam script RemoteCasts it |
| `85E` | *retired* | the first orb's impact (that orb was never seen in game; Prophecy's Smite orb has none); never reuse |
| `858` | SNDR `ZP_ArgentVerdictChargedSD` | `84F`'s record on `SmiteCharged.wav`, the curator's second church bell ("add this sound once the weapon is full charged ready to release its payload") |
| `859` | SOUN `ZP_ArgentVerdictChargedSound` | plays `858`: the charge script rings it at the player when the fourth knuckle lights |
| `857` | EXPL `ZP_ArgentVerdictBeamImpact` | where a beam lands: `VerdictImpact.nif` (Kittytail's impact, white and black), sound `80C`, placed object `860` (the orbs); Enderal's Wayfarer nova `143325`'s record without its enchantment, screen effect, decals, push and damage |
| `84F` | SNDR `ZP_ArgentVerdictBellSD` | `80C`'s record on `SmiteBell.wav` (the curator's church bell), no pitch variance |
| `850` | SOUN `ZP_ArgentVerdictBellSound` | plays `84F` |
| `851` | MGEF `ZP_ArgentVerdictChargeMGEF` | a charge: `A67`'s shape running `ZP_ArgentVerdictChargeScript`, hidden |
| `852` | GLOB `ZP_ArgentVerdictCharges` | 0..8 (light-attack hits; a mote for every 2; 0..4 until 2026-11-15) |
| `853` | MGEF `ZP_ArgentVerdictMotesMGEF` | the motes' display: a constant script effect (Prophecy's `AD6`'s shape) running `ZP_ArgentVerdictMotesScript` |
| `854` | SPEL `ZP_ArgentVerdictMotes` | the ability carrying `853`, added while a hammer is equipped (the weapons' `ZP_ArgentVerdictEquipScript`) and by the first charge |

Masters: the base three + Zenderal - Prophecy (and EGO). ESL, HEDR 1.7. Load after Prophecy.

## The mesh (`tools/01` + `tools/fist.py`)

*The clenched hand below was the first head (v1 to v5); it was retired on 2026-11-15 for the spiked gauntlet (next
section). Its code stays in `tools/fist.py`, `tools/fist_tex.py` and `tools/roses.py` because the gauntlet is built on
it (the hand's pose, the stake and sockets, the painter); its own mesh, atlas (`ArgentFist_*`) and shapes are gone.*

Our own copy of Pretty's `Weapons\Elven\ElvenWarHammer.nif` (Noble Armory's), built in place by `tools/01`:

- the head's **centre block** (the head piece's triangles whose centre lies in x −4.2..4.6; the block's measured
  extent is asserted) and the **knob** on top of it (its own 384-triangle piece) are taken off;
- the face and the spike (the rest of the head piece) are **scaled 1.15** about the block's centre (0.25, 39.46,
  −0.07); the two blood-overlay copies of the head (`Edgeblood`, `Edgeblood01`) get the same cut and scale;
- the generated parts (223) are added as **two shapes on one atlas**, each with its own copy of the hammer's
  shader (never shared: Clockwork Thunder's freeze) and the same painted texture set (`ArgentFist_*`, below):
  `ZP_ArgentFist` (the hand with its forearm and protruding bones, the stake, the sockets, the thorn bracelet:
  25,978 vertices, 48,968 triangles) and `ZP_ArgentRoses` (the rose vines: 12,181 / 21,088). One BSTriShape holds at
  most 65,535 of either, and the roses would have taken one shape past it (70,056 in all); `fist_tex.split` cuts the
  assembled mesh by each part's `group`. Appended last, so shape order is unchanged;
- the face and spike stay where they were, so the **stake** the hand holds (radius 1.01, polished) runs out of both
  sides of the hand to a **socket** round each neck's cut end (superellipse collars 0.16 wider than the neck, over its
  last 0.55, closing down onto the stake);
- the shaft ran up into the block: its top rings are **pulled down and in** inside the forearm (1.0 above the arm's
  end, but no higher than the arm still holds the whole shaft, measured: the arm leans back as it rises, so higher
  up the shaft came out of its front; and drawn in to 0.97 of the shaft's radius: those rings were wider);
- the hammer shape's texture set is ours, so the records need no alternate textures.

**The hand** (`fist.py`), built from adult proportions (85 mm across the knuckles = 10.4 units, round a 1.55 stake),
in a frame with u up and w toward +Z, then scaled 0.68 about the stake (v3: "at least 30%" smaller) and cocked back 8°:

- four fingers (index on the face side), each three phalanges joint to joint (index 44/25/20 mm, middle 49/30/21,
  ring 46/28/21, little 36/21/18), each phalanx its own rounded, slightly square-sectioned volume, waisted between
  joints (the joints read as knuckles and creases), tapering to the tip; proximal phalanx over the top of the stake,
  middle down its front, distal tucked back under it into the palm; a nail on each fingertip;
- **bones break through the back of the hand** (v5, `bone_path`, `palm_back`): the four metacarpals rise out of the
  skin near the wrist (a tenth of their depth out) and run along the back of the hand, half standing out of it, to
  the knuckles, which are bone heads (the knuckle row, sloping down to the little finger); four carpals peep out at
  the back of the wrist. Each metacarpal follows the back's own surface (the palm box's superellipse solved for its
  back) at a set share of its depth out (`PROTRUDE`), its profile v4's `METACARPAL` × 1.2;
- the palm and back of the hand: one deformed superellipsoid (wide at the knuckles, narrowing to a 58 × 38 mm
  wrist), the palm pressing the stake from behind; a filler fills the curl (under the proximal phalanges, behind the
  middle ones), so the side of the fist shows no hole; a hypothenar pad on the little-finger edge;
- the thumb (metacarpal, proximal, distal) rises from a thenar mound and lies across the index and middle fingers'
  middle phalanges, its nail outward;
- **the forearm into the handle** (v5, `into_shaft`): the palm's own rings are cut 9 mm above the wrist (before its
  rounded bottom) and run on down as the forearm, one surface with the hand (v5's first build was a separate forearm,
  which left a crease at the wrist): the wrist's own section first, then it narrows, turns 25° and settles, nearly
  tangent, into a round 1.025 × the shaft's radius on the shaft's axis, 4.4 units below the wrist's centre, where it
  ends; the shaft's twisted flutes run out from under it. An exact fit to the shaft's fluted, twisting section was
  tried and dropped: the arm showed through the flutes;
- **the bracelet of thorns** (v5, `thorn_bracelet`, curator's idea): two slightly uneven thorny branches twisted round
  each other into a ring on the arm's end (strand radius 0.12, 7 twists), 26 hooked thorns pointing out, up and down;
- **the rose vines** (v5, `roses.py`): two thorny vines (stems 0.08 and 0.06) wind round each other up the forearm,
  from just above the bracelet to just below the wrist (1.15 and 0.95 turns, standing just off the arm's surface,
  found from its rings by `ring_surface`), carrying five roses (sizes 0.74 to 0.98; a tight centre and petal rings of
  3, 5, 5 and 5, each more open, the outer ones curling back), a closed bud with four sepals at each vine's top, a
  leaf pair under each rose, 13 more leaves (pointed ovals folded along the midrib) and 14 small thorns. The first
  build (one vine, three smaller roses) read as sparse.

History of the hand: draft 1 (coiled rings round a bar) and draft 2 (four uniform tubes, a pillow palm) read as a
cartoon; v2 rebuilt it with a flesh hand's anatomy; v3 scaled it 0.68 and added the stake, sockets, skin texture and
engravings, over a cuff; v4 was a skeletal hand over a rose-wreathed base (both since dropped); v5 is v3's hand again,
its forearm flowing into the handle under a bracelet of thorns, no cuff, and bones breaking through the back of
the hand where the engraved panel was, and two thorny rose vines up the forearm. A 20° tilt that put the wrist straight on the
shaft leaned the fingers forward; 8° + the forearm's own lean onto the shaft keeps the hand upright.

The **collision** (Pretty's convex hull) is unchanged: a dropped hammer's physics shape is the original head's.

## The gauntlet variant (`tools/gauntlet.py`)

`tools/01` builds the gauntlet (its `HEAD` table: mesh path, texture prefix, shape name; the hand's entry and
`--variant` removed 2026-11-15, when its output stayed byte-identical apart from version 2's bolt node); the
hammer's own cut, scale, silver set and shaft are as for the hand. The
gauntlet is one generated shape `ZP_ArgentGauntlet` (25,488 vertices, 47,328 triangles, roses included) on its own
painted set `ArgentGauntlet_d/_n/_m`.

`gauntlet.py` reuses `fist.py`'s pose (finger joints, thumb, palm box, scale 0.68) and armours it, every part a
`fist.Grid`. **The hand is turned about the stake until its wrist's centre is straight under it** (19.9°, computed
from the palm's wrist, `arctan(wrist_w / u_bot)`; the hand variant keeps 8°): with 8° the wrist sat 1 unit behind
the shaft's axis and the first build's lames walked their centres from there onto the shaft, which read as a
diagonal lean in game. Now every band is on the shaft's axis (asserted).

- **finger and thumb lames** (`lame`): three per digit, along the phalanges, 1.12 × 1.16 the finger's section,
  squarer (superellipse 3.2), each far end flared 8% into a lip over the next; a 15 mm spike over each middle knuckle
  and the thumb's joint;
- **knuckle guard** (`swept`): a bar over the four knuckles carrying a 25 mm gadling over each;
- **back plate**: a deformed box over the back of the hand (`fist.palm_back`), a ridge down its middle, a domed
  rivet near each corner and a 22 mm centre spike;
- **under the plates**: palm, curl and thumb pad in scale mail (kind `mail`; the first build's navy leather read as a
  black palm in game);
- **wrist lames** (`wrist_lames`): four bands with rolled lower rims, from 1.12 × the wrist down to 1.18 × the shaft
  radius, all on the shaft's axis; six spikes round the top band at 0°, 60° … 300° (`LAMES['phase']`: none at the
  front, where the rose is, or the back, where the vines start); a collar on the shaft under the last. The shaft runs
  up inside them as high as every ring still holds its whole section (`held`, the hand variant's rule);
- **roses and thorns** (`roses.column_roses`, `COLUMN`): two vines (stem 0.1), mirror images across the plane through
  the shaft square to the head, rise from the back of the collar (`G_VINE`), each winding half a turn round its side of the lames, standing
  off their outer surface (`column_surface`: at each height the outermost band, held over each band's lower rim and
  softened, so a vine crosses the steps instead of dropping into them), with 4 leaves, 7 thorns and a rose of 0.74
  each; they meet at the front of the second band under a rose of 1.3 with a leaf pair. The first try (stem 0.07, one
  rose of 0.86) was lost under the fist in the preview;
- the stake and its two sockets as the hand variant.

Its texture (`fist_tex.paint`, the kinds `plate`, `lame`, `spike`, `mail`, plus the hand's `thorn`, `petal`,
`leaf`): plate polished and a shade darker at each edge, two raised rivets near the start of each finger lame; spikes
brighter toward the point; **mail** = staggered rows of round scales (`MAIL`: row pitch 0.17 units, columns a whole
number round each part), each row lying over the one below with its free edge toward the part's start, each scale
rising to that edge and dipping all round its rim (without the rim dip the preview read as rows of bricks).

**Wear (v3, `fist_tex.WEAR`, `wear`)**: v2's plates read as clean chrome in game beside the hammer's own grimy
silver. The hammer's wear lives in its diffuse (its normal map is nearly flat: xy spread 0.02-0.03), so it was
measured there, as positions on the silver ramp: the pommel's barrel mean 0.5, spread 0.07 / 0.15 / 0.17 at large /
middle / fine scale (bright rubbed speckle); the plain silver round it mean 0.16, 0.08 / 0.11 / 0.08 (tarnish,
grime, brushing). The gauntlet's plates, lames, spikes, stake and sockets (the last two flagged `meta['worn']` in
`gauntlet.py`, so the hand variant's stay as they were) get the same, all seeded per chart (a build is repeatable):
the base 0.13 darker; tarnish clouds (solid noise on the mesh position, so they cross seams and parts); brushed
streaks along each part (fast across, slow along; wrapping round the ring); dark grime spots, speckled inside; bright
rubbed speckle in a band at each end of a part (its lips and rims) and in patches, soft 1-2 texel dots; faint
hairline arcs. Relief stays tiny, as on the hammer. Grime and dark tarnish cut the gloss a little (CM green −0.22,
red −0.08, highlight −0.15). The mail gets the tarnish and grime only, at 0.6.

## The fist's texture (`tools/fist_tex.py`)

Each part is a stack of rings (`fist.Grid`), so it unwraps as a rectangle: columns round its rings (plus a seam
column), rows along it by surface length. All 223 rectangles are shelf-packed into one 2048² atlas at one density
(about 55 texels per unit; the mostly hidden curl filler and the plain stake at lower density). Every texel is traced
back to its point on the part, in millimetres of the full-size hand, and gets a height:

- **skin** (fingers, thumb, palm, knuckles, thenar, hypothenar, the curl): solid 3D noise, so the relief runs across
  every seam: soft undulation (0.07 mm), fine grain, pores (0.025 mm deep);
- **the forearm**: the same skin at the wrist, fading to plain polished silver 14 to 42 mm below it, as it becomes
  the shaft;
- **knuckle wrinkles**: five wavy creases across the back of each middle and end joint and the thumb's joint,
  fading round the sides and away from the joint (none over the knuckles themselves, which a fist stretches);
- **nails**: polished, fine lengthwise ridges, no pores;
- **the bones** through the back of the hand: a fine, slightly uneven grain with sparse small pits, a touch brighter
  than the skin;
- **the thorn bracelet and the rose vines' stems and thorns**: polished, a shade darker, faint lengthwise lines;
- **rose petals**: smooth and polished, shaded darker toward the heart of each rose; **leaves**: a midrib and paired
  side veins, pressed in;
- **engravings**, cut 0.12 mm and filled dark like niello: two lines and a bead row round each socket. The stake is
  polished. (v3's engraved panel on the back of the hand, a sun over scrolls, gave way to the bones.)

From the heights: the normal map (tangent space, **DirectX: green = +v**; measured, see below; alpha = highlight
mask 0.80 on skin, 0.86 on metal, low in the cut lines), the diffuse on the hammer's silver ramp (skin mottled by its
relief, darker in pores and wrinkles, near black in the cut lines) and the Complex Material mask (the hammer's
reflective, glossy silver; the cut lines matte). Tangents are stored in the hammer shape's own convention (stored
tangent = dP/dv, stored bitangent = dP/du, measured by median).

**Normal map green channel:** for a height-derived map, dR/dv = dG/du when G encodes +v. Across Bethesda's own maps
(`dirt01_n`, `snow01_n`, `silversword_n`, Enderal's `mountainslab01_n`) the correlation is +0.2 to +0.5, so the game's
maps are green = +v (DirectX). Noble Armory's baked map is near 0 (its bake's geometry dominates).

A relief preview (the diffuse lit through the normal map under a fixed light, `fist_tex.paint(..., preview=True)`)
checks the directions: cut lines read as recessed, pores and wrinkles as dips.

## Smite (`tools/02`, `tools/03`, `ZP_ArgentVerdictSmiteScript`)

Kittytail's **Dark Hierophant Magic** (`Ghostlight.esl`, 20 holy-light spells) is not installed: it would bring a
Dawnguard cell (`DLC1FalmerTemple01`, an empty stub in Enderal), spell tomes and a SPID file aimed at Skyrim's
Dawnguard factions. Its archive's contents sit in `reference/mods/_raw/DarkHierophantMagic`, its plugin serialized
in `reference/mods/DarkHierophantMagic` (both gitignored); the download is
`E:/Zenderal/downloads/Dark Hierophant Magic-108499-1-43-*.zip`. It has no lightning bolt (its beam, Absolution's
`LightDischargeLaser.nif`, is a laser), so the bolt is Bethesda's in Kittytail's colours.

**How it works** (version 3, 2026-11-14):
1. **Charges.** Every light-attack hit on an actor hostile to the player (the player not power attacking) runs
   `851` (`ZP_ArgentVerdictChargeScript`) while `ZP_ArgentVerdictCharges` (`852`) is below 8 (`HITS`): one more
   charge (`GlobalVariable.Mod`, thread-safe; a hit that finds it full gives it back), and a mote lit for every 2
   (`ZP_ArgentVerdictMotesScript.Lit`: whole steps, so the fourth lights only at a full charge). The hit that fills it
   rings the curator's second church bell at the player (`859` → `858`, `SmiteCharged.wav`): ready. Until the
   balance pass (2026-11-15: "make the charge up be 8 light attacks not 4") any hit, light or power, lit one mote,
   4 in all; power attacks before a full charge now add nothing.
2. **The motes** are nodes in both hammer meshes (`tools/motes.py`, called by `tools/01`): over each knuckle a node
   `ZP_ArgentMote1`..`4` at scale 0 holds a very small copy of Kittytail's Absolution rune circle (her camera-facing
   node `FlareFX` from `light/LightDischargeLaser.nif`, with her rune rings `RunesA` / `RunesB` / `RunesC`, the cross
   circle `RuneCore` and the white flare `FlareA` at twice her size as the glow), 0.75 units to its outer ring, 0.25
   off the surface: on the gauntlet's knuckle guard round each gadling, on the hand's bone knuckle heads (the knuckles
   are about 1.9 units apart; `tools/01` asserts the motes do not overlap). Each shape is a byte copy with its own
   shader and alpha property (never shared: Clockwork Thunder's equip freeze), its shader controllers dropped (a
   weapon runs none: the circle stands still), its emissive multiples set (`MULT`), Kittytail's textures as our
   downsized copies (`tools/03`: `VerdictMoteCircle.dds` 256, `VerdictMoteRunes.dds` 512 x 256) and her vanilla
   palette our white one. A mote is lit by SKSE's `NetImmerse.SetNodeScale` (1 = lit, 0 = out) in the third- and
   first-person 3D. A weapon's 3D is rebuilt at scale 0 on every equip, load and race change, so an ability (`854` /
   `853`, `ZP_ArgentVerdictMotesScript`) sets them again every second while the hammer is equipped (the weapon's
   `ZP_ArgentVerdictEquipScript` adds and removes it; the first charge adds it too, for a hammer already in hand). The
   charges stay when the hammer is put away. (Version 2's node `ZP_ArgentBoltNode`, where its bolt left the hammer,
   was dropped from the mesh on 2026-11-15.)
3. **The release.** A power attack hit while the charges are full (8) and the player has 20 Mana runs `804`
   (`ZP_ArgentVerdictSmiteScript`): the charges are claimed (a second release finds none), the 20 Mana spent (the
   charges handed back if the Mana went in between) and the motes go out. Up to 4 enemies (`Targets`): the struck
   one, then the nearest others within 800 units of the player (`Radius`; powerofthree's
   `FindAllReferencesOfFormType`, living, hostile, not teammates). The curator's church bell (`850` → `84F`) rings once.
   The struck enemy's beam goes down first, before anything else runs (even on a corpse), and strikes 0.1 s later;
   then the search (one pass) and the others: over each, 0.1 s apart, a smite beam (ACTI `856`) is placed 1024 units
   (`BeamLength`) above the enemy's feet, so its strips run down onto it; 0.1 s after each appears (`LandDelay`): the impact (EXPL `857`, the
   strike's sound) at the enemy's feet and the damage `847` through `DoCombatSpellApply`, blamed on the player. Each
   beam vanishes 0.6 s after its own strike (`Linger`; `Disable` without fade, then `Delete`), all on one clock. The
   first test (2026-11-14): "the beams last for too long they should strike and then disappear" (they stood 1.2 s and
   faded 1 s more), so 0.2 s; then "the beams could stay a little longer", so 0.6 s.
4. **The beam** (`VerdictSmiteBeam.nif`, `tools/03` `sky_beam`): Kittytail's Absolution beam (the curator's picture):
   particle strips (`BSStripParticleSystem` pStripsA/B, pStripsOrb, flares and orbs) emitted from a ring past her
   rune circle (`FlareFX`) and pulled to a gravity point 1024 units along the mesh (`EndGravityNode`). Stood on end: a
   new node `ZP_SkyDown` under the root turns +Y to -Z (a placed reference's transform replaces the root's), so the
   circle hangs in the sky and the strips run down 1024 units (`tools/03` asserts the end point and that the script's
   `BeamLength` matches; its BSXFlags already mark it Animated, so its particles run on a placed object). Every
   palette our white one (`Verdict_<palette>W.dds` from Bethesda's), every emissive and particle colour grey. Half
   Kittytail's width (`BEAM_WIDTH` 0.5; curator: "can we make them thinner?"): every emitter's particle radius (the
   strips' width: 48 +- 12, grown up to 2.4 times over a strip's life) and the emitter rings `EmitRing` / `EmitterADD`;
   speeds and gravity untouched, so the length and timing stay hers. Her five
   textures under `textures/Light` ship at the pack's paths (`flare`, `fxlightningbolt01`, `lenshexshape01_d`,
   `matlas`, `mcircle2`); the rest are the game's own (checked to resolve).
5. **The orbs**, Prophecy's Smite chain: Smite's explosion `A54` places activator `A46`, whose script
   (`_LIP_LightshaftSkyboltActivatorScript`) fires the light shafts from `OnInit` (read from its string table:
   `OnInit`, `PlaceAtMe`, `SetPosition`, `RandomFloat`, `RemoteCast`; its bytecode, disassembled since: a marker
   80 up (`SpawnHeight`), each shaft RemoteCast from it at a point +-512 out and 50 below to 80 above it). Here the beam's impact (EXPL `857`, placed at
   each enemy's feet as its beam strikes) places the orb spawner (ACTI `860`, its PlacedObject), whose script
   (`ZP_ArgentVerdictOrbSpawnerScript`, `OnInit`, its own thread) fires 4 orbs (`Orbs`): each RemoteCast, blamed on the
   player, from an empty activator 90 units out (`StartOut`, clear of the enemy there) at 80 up (`OrbHeight`,
   Prophecy's), at one 700 further out the same way, spread evenly round the circle from a random start (+- 20
   degrees), between 50 below and 80 above the launch height (`AimLow` / `AimHigh`, Prophecy's); then
   it deletes its markers and itself. Each burst writes `[ZP Argent orbs]` to the Papyrus log, and the release writes
   `[ZP Argent release]` lines (charges claimed, enemies, each strike). The orb is Prophecy's Smite orb in Dark
   Hierophant's colours (`VerdictOrb.nif`, `tools/03` `orb`): Kittytails' `Lightpower\HolyBoltProj.nif` (Bethesda's
   Dawnguard sunlight projectile, the copy Prophecy ships) with its starburst rays, flash and sparkles on white palettes
   and grey colours and its soft wisps and halo black on normal blending; its projectile is Prophecy's (Cone, 540 a
   second, range 1620: the orbs drift out as Smite's do). Each orb hits the first thing in its path: enemies take 15
   (undead 30), anyone else nothing (the effects' hostility condition).
   - **First build** (the same day): the knuckle motes' rune circle on Kittytail's Penance blade projectile, fired at
     the beam's foot (inside the enemy there) when the beam's 3D loaded plus 0.3 s. In game: "no orbs appear". A
     projectile that starts inside an actor most likely hits it at once; the curator then asked for Smite's orbs.
   - **Second build**: Smite's orbs, from 90 units out, fired by the beam's own script when the release activated
     the beam (`Activate` / `OnActivate`). In game: "it doesn't seem the orbs appear at all"; the Papyrus log of
     that session (on the new build) has no line from the beam script at all, so `OnActivate` never ran there. The
     scripts of both builds were banked until 2026-11-15, then deleted with the other versions.
   - **Spawner builds 1-3: the orbs flew along the floor** ("almost under the floor" at 70 up, "still on the floor"
     at 150, "still seems to fire the orbs low" as a Missile). Every `[ZP Argent orbs]` line of those three sessions
     (249 bursts in the Fog Wood) put the launch within 10 units of the Fog Wood's ground (its height formula in
     `src/FogWood/tools/01`), whatever `OrbHeight` said. Cause: the spawner script's position locals were named `x`,
     `y` and `z`, and in the loop the compiler read those names as the reference's own `X`/`Y`/`Z` properties
     (`ObjectReference.psc`), not the locals: the bytecode has `propget z, self` where the markers are set, so both
     markers sat at the spawner's own height, the enemy's feet, and the log line printed that too. The locals are
     `baseX`/`baseY`/`baseZ`/`launchZ` now (bytecode checked; no other compiled script in the repo reads X/Y/Z of
     itself). The Cone-to-Missile switch of the third build rested on the wrong cause and was undone; the 150 height
     too (Prophecy's 80 instead, read from its bytecode).

Version 2 (the same day; banked with its sources, plugin, scripts and assets until 2026-11-15, then deleted with
the other versions): the same charges, then a bolt of white and black lightning (Bethesda's Chain Lightning
bolt, one strand black) from the mesh's `ZP_ArgentBoltNode` into the struck enemy (40 shock) and up to 4 jumps of 20,
Clockwork Thunder's chain. Version 1: 20% of hits, the same bolt straight down from the sky, then the chain.

**Damage:** hostile actors only (`IsHostileToActor` the player: no followers, never the player); each effect has a
twin on `ActorTypeUndead` for double damage; vanilla shock's shape (Health, half as much Magicka, `ResistShock`);
fixed numbers (no PowerAffectsMagnitude). The numbers are `KNUCKLES`, `STRIKE`, `TARGETS` in `tools/02` (the item
card's text is built from them; `TARGETS` must equal the release script's `Targets` and `KNUCKLES` all three
scripts' `Knuckles`, which `tools/02` checks);
heights, range and delays are the script's `AutoReadOnly` properties.

**The look** (`tools/03`, into Patch Collection, all generated):
- the bolt (`VerdictBolt.nif`): Bethesda's Chain Lightning bolt `magic/lightningbolt02.nif`, read from
  `Skyrim - Meshes1.bsa` (the list's winning copy is Lightning VFX Edit's, not ours to ship modified): three
  procedural lightning strands. The two outer ones (`object0`, `object4`) on a white palette from Bethesda's
  `GradShockExplosion` (its brightness on a cool white) with grey emissive colours; the violet middle one (`object2`,
  `GradVioBright`) black: normal blending instead of additive (black cannot show additively) and a black emissive
  colour. Dark Hierophant's white light with black;
- the impact (`VerdictImpact.nif`): Kittytail's `BlacklightImpact` (`light/LightImpact.nif`), its flash and ring
  white, its mist black, every colour key grey;
- the glow on the struck: Kittytail's white shock glow (`84B`) on our white `GradShockHit`;
- the palettes (`Verdict_<palette>W/K.dds`) are our own, from Bethesda's: the list's Glorious Gradients recolours the
  vanilla gradients, Kittytail's included;
- the sounds: `SmiteStrike.wav`, Kittytail's `FlareBig.wav` (a 4.1 s flare at 48 kHz) 1.3 times faster, 44.1 kHz, cut
  to 2.4 s with a 0.4 s fade (the Judgement Blade's strike sound, which the curator kept); `SmiteBell.wav`, the
  curator's church bell (Motion Array, licensed: `tools/03 --bell <file>` converts its 24-bit / 48 kHz to 16-bit /
  44.1 kHz, windowed-sinc resample, TPDF dither, peak -2 dBFS; neither file is committed); `SmiteCharged.wav`, the
  curator's second bell (`MA_A2DStudios_ChurchBellsImpacts_0.wav`, `tools/03 --charged <file>`, the same way), when
  the hammer is fully charged.

### Scrapped the same day: the Judgement Blade and the Penance fan

Built and tested in game five times on 2026-11-14 (records `808`–`840`, now retired; the scripts, `tools/03` and
every asset were banked until 2026-11-15, then deleted with the other versions). What they taught:
- **Kittytail's Grand Cross at melee range whites out the screen**: its cross faces the camera through a billboard
  with four sheets 940–2000 units across under a dynamic light of fade 4, radius 1024 (the screen 93% near-white for
  ~2 s, measured on the recording); and its sword, from 650 units up at 4200 a second, was never seen.
- **Her sword's blade is a flat card** (35 × 88 × 2 units): falling straight down it is seen edge-on from behind the
  player. A copy of the card turned 90° about the blade, appended to the same shape, fixed it.
- **A spell projectile vanishes the moment it strikes** (only arrows stick): a blade that stays must be a placed
  reference moved by `TranslateTo`.
- **Her Penance Aura - Fanning art** lays its eight swords flat along the spokes of a ring, on a billboard node that
  turns the ring to the camera, and spins the ring. Moving the ring off the billboard needs the billboard's transform
  folded in (moved alone it stood on edge); each blade as its own art object is its own animation instance, so a
  spinning ring bunches blades started by different hits.
- **Each fan sword's soft glow** (`pGlow`, radius 90 × the sword's scale, 115 units at × 1.28) filled a third-person
  view, and a full ring puts a sword between the camera and the player: "that white you are seeing is 1 sword".
- The curator's question at the end: "why you don't just use the kittytail spell that has the swords already
  positioned the way i want". The fan was built on the Fanning *Out* art and re-posed after three guesses; which of her
  spells the curator meant was never asked. With a reference picture: name the source spell with the curator first,
  then render it (memory `feedback_render_reference_first`).

## The hammer's textures (`tools/01`)

`tools/01` imports Sting and Rise's texture pipeline (`src/StingAndRise/tools/01-build-assets.py`) and runs its
`gold_set` with a silver recipe:

- every metal texel (Noble Armory's own env mask, 68% of the texture) onto a cool, near-neutral silver ramp by its
  brightness (`SILVER_RAMP`; the first ramp, 0.56 at the low end, read near white all over, so the low end is 0.42:
  the head's engraved borders and floral panels stay readable);
- a Complex Material mask (reflect 0.94 / gloss 0.93 / metal 1, alpha 0; written with `-sepalpha` and its 1×1 mip
  checked against Bottled Shaders' own test) and the normal map's highlight mask on the metal raised 0.17 → 0.83;
- the grip's leather UV islands (the four wrap strips and two small caps: 6 islands, each ≥ 80% leather; the 8
  metal islands dropped) recoloured **dark navy** (0.06, 0.09, 0.22 at the leather's 75th-percentile brightness,
  full contrast; v1 was white);
- a silver cubemap graded from Bethesda's `chrome_e.dds` for where Complex Material is off (the fist's shader uses
  it too).

The hammer's stored tangents disagree on its mirrored UV islands (mean agreement 0.84), so `tools/01` reads the
tangent convention by the median vertex before adding the fist (Sting and Rise's check uses the mean).

## Regenerate

```
python src/ArgentVerdict/tools/01-build-assets.py    # meshes (with the knuckle motes, motes.py) + textures into
                                                     # Patch Collection (--out-root <dir>: dry run)
python src/ArgentVerdict/tools/02-build-records.py   # YAML (refuses if a copied record changed hands, Pretty's mesh
                                                     # moved, or tools/01's mesh is not the winner of its path)
python src/ArgentVerdict/tools/03-smite-assets.py --bell <MA_A2DStudios_ChurchBellsImpacts_3.wav> \
    --charged <MA_A2DStudios_ChurchBellsImpacts_0.wav>
                                                     # the Smite's bolt, impact, palettes and sounds (without
                                                     # --bell the installed bell is kept)
```

The script compiles to `Scripts/compiled` (committed; `.gitignore` exception) and ships in Patch Collection's
`Scripts` (its source in `Scripts/Source`). After a Dark Hierophant Magic update: unpack the archive into
`reference/mods/_raw/DarkHierophantMagic`, serialize `Ghostlight.esl` into `reference/mods/DarkHierophantMagic`
(Spriggit, EnderalSE), rerun `02` and `03`.

Rerun both after a Pretty Enderal Armory update (mesh and textures come from Pretty's copy of Noble Armory's;
`tools/01` asserts the block, knob and blood overlays); rerun `02` after EGO changes the Aeterna Warhammer or
Prophecy changes its Smite effect. Change the gauntlet in `tools/gauntlet.py` (its pose, stake and sockets come
from `tools/fist.py`, its vines from `tools/roses.py`) or the texture in `tools/fist_tex.py`, then rerun `01` (and
`02`: the bounds).

## Placement

**Not placed yet**: where it is found is the curator's call. Test with `help "Argent Verdict"` →
`player.additem <id> 1` (`…800`; a save that held the compared gauntlet `…806` loses it: add `…800`).

## Status

v1 to v4 built 2026-11-13, v5 (human hand, forearm into the handle, thorn bracelet) 2026-11-14: deserializes clean,
round trip through Spriggit with no differences (FormKey references checked on v2; since then only the bounds and
the plugin description changed), the mesh re-reads byte for byte through our NIF writer and opens in PyNifly (5
shapes); mesh, textures and plugin deployed into Patch Collection. **Unverified in game**: the hand, forearm, bracelet and
rose vines, their relief and engravings (the normal map's green convention is measured, not seen), the silver (both
views), the navy grip, the item card's text. Not ticked in MO2
yet.

Gauntlet variant built 2026-11-14 (records `806`/`807`): round trip clean, all 25 FormKey references resolve, the
hand mesh rebuilt byte for byte (same md5) beside it; both meshes, both painted sets and the plugin deployed into
Patch Collection. Seen in game by the curator the same day (screenshots: the black palm, the leaning wrist); v2
(metal mail palm, upright wrist, roses and thorns) built and deployed the same day, the hand mesh again unchanged
(md5), the plugin round trip clean (only `806`'s bounds changed). v3 (wear) the same day, texture only: the
gauntlet mesh and records unchanged, the hand's mesh and texture unchanged. **v2 and v3 unverified in game.**

Judgement Blade and Penance fan: built and tested in game five times on 2026-11-14, then scrapped (above).

Smite built 2026-11-14: version 1 (from the sky, 20% of hits), version 2 (the charges and the knuckle motes, the
bolt from the hammer and its chain), version 3 the same day (the charges kept, Absolution beams from the sky
on up to 4 enemies): scripts compiled (0 errors), plugin round trip through Spriggit with no differences, all 42
FormKey references resolve, the meshes (with the motes, rendered from the knuckle side: one circle per knuckle), the
beam, its textures, the plugin and scripts deployed into Patch Collection (the plugin is ticked in Ultra, after
Prophecy); version 2's bolt mesh and its two palettes removed from Patch Collection.
**Unverified in game**: the motes lighting one a hit and showing at all (`SetNodeScale` on an equipped weapon's
nodes, both views), their size and brightness; the release only on a full power attack; the beams' height and the
circle in the sky. First test the same day: the beams came down but stood too long, so they vanished 0.2 s after
striking; second round: 0.6 s, half as wide, damage doubled to 80 / 40, a bell at full charge; third: "beams look
great now", and the orbs added; sixth: orbs seen, "almost under the floor" (then 150 up), and "the Smite itself is
triggered a bit late": the log showed the search for the other enemies taking 1-2 s before any beam, so the struck
enemy's beam now goes down and strikes first (0.1 s, `LandDelay` was 0.3), even on a corpse the blow killed (two
releases in that log found 0 enemies for that reason), the search is one pass, the others follow; fourth: "no orbs appear", so they started outside the enemy, fired on
the beam's activation and looked like Prophecy's Smite orbs in white and black; fifth: "it doesn't seem the orbs
appear at all" (no log line), so they now come from Smite's own chain, an explosion-placed spawner's OnInit, with
log lines; sixth to eighth: seen, but flying along the floor at every height (the spawner's `x`/`y`/`z` locals,
see the orbs' postmortem), so they now leave 80 up as Prophecy's do. **Verified in game 2026-11-15**: "everything
is perfect" (the motes, the beams, the orbs, the bell, the damage).

Final (2026-11-15): the balance pass (8 light-attack hits a full charge, two a mote; 20 Mana a release), then "this
version we've made is THE Argent Verdict" and "remove the other versions": the hand head, records `806`/`807`, the
`--variant` option and version 2's bolt node removed (the rebuilt mesh is the compared gauntlet's, byte for byte, minus
that empty node; every texture identical), the three backup banks deleted. Plugin round trip clean, scripts and
plugin deployed into Patch Collection. **The balance pass is unverified in game.**
