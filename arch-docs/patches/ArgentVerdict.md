# ArgentVerdict

- **Source:** `src/ArgentVerdict/`
- **Ships:** `Zenderal - Argent Verdict.esp` + its own mesh `meshes/Zenderal/ArgentVerdict/ArgentVerdict.nif` + 7
  generated textures (not committed), inside **Zenderal - Patch Collection** (as Sting and Rise)
- **FormID block:** `0x800–0x805` (`0x802` retired: the first build's texture swap; `0x806+` free for the placement)
- **Needs:** Zenderal - Prophecy (master: the Smite explosion and its script); the mesh is built from Pretty Enderal
  Armory's, but ships as our own file, so Pretty is not needed at run time
- **Credit:** the model is **Caenraes' Noble Armory** warhammer (Skyrim SE Nexus 124896: modification and asset use
  allowed with credit, not in paid mods), shipped in Pretty Enderal Armory (longlivethehighking). Since v2 a modified
  copy of that mesh ships with us. Credit Caenraes in Patch Collection's description.
- **Pillar:** modern combat (curator's request, 2026-11-13)

## What it does

A unique silver great hammer (there was none): **Argent Verdict**, all polished silver. Its head is a **clenched
human hand gripping a stake** that carries the face and spike, **bones breaking through the back of the hand**;
its **forearm flows into the handle** under a **bracelet of thorns**, two **thorny rose vines** winding up it, and
the grip is dark navy leather. Its **power attacks have a 25% chance to Smite**: a pillar of holy light on the target,
40 damage, beams of 10 on the enemies around it, double against undead (Prophecy's Hallowed Flare sky-bolt, the same
proc as Prophecy's Smite talent). It is a silver weapon (EGO's silver perks against undead and ghosts; with
Prophecy's Smite talent its ordinary hits get that talent's 15% too).

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

| FormKey | Record | From |
|---|---|---|
| `800` | WEAP `ZP_ArgentVerdict` "Argent Verdict" | EGO's Aeterna Warhammer `07C993` (the winner): 46 damage (EGO 42; Qalian's Absolution 44), crit 23, speed 0.65, value 1500, weight 28; keywords Aeterna material (EGO's smithing), melee, warhammer, `MagicDisallowEnchanting`, `WeapMaterialSilver 10AA1A`, `WeapTypeUnique` (no `VendorItemWeapon`, as Qalian's Absolution); model `Zenderal\ArgentVerdict\ArgentVerdict.nif` (`tools/01`'s; textures in the mesh, no swap), bounds measured from it; enchantment `803`, charge 3000 |
| `801` | STAT `1stPersonZP_ArgentVerdict` | `1stPersonElvenWarhammer 036BD2` on the same mesh (Pretty's 1st-person mesh is the same file) |
| `802` | *retired* | v1's TXST `ZP_ArgentVerdictSilver` (the texture swap onto Pretty's mesh); never reuse |
| `803` | ENCH `ZP_ArgentVerdictSmite` | weapon enchantment (Touch), cost 1, charge 3000: `804` with conditions *the player `IsPowerAttacking`* and *`GetRandomPercent` < 25* (an instant effect: tested once per hit) |
| `804` | MGEF `ZP_ArgentVerdictSmiteEffect` "Smite" | Prophecy's Smite effect `A67` (script `ZP_HolyPlaceExplosion` placing the sky-bolt explosion `A54`, whose activator `A46` casts as the player: kill credit); not hidden, with the item card's description |
| `805` | COBJ `ZP_TemperArgentVerdict` | the Aeterna Warhammer's grindstone temper `148AB7`, new product (Aeterna ingot; enchanted, so Enderal's Arcane Blacksmith rule) |

Masters: the base three + Zenderal - Prophecy. ESL, HEDR 1.7. Load after Prophecy.

## The mesh (`tools/01` + `tools/fist.py`)

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
python src/ArgentVerdict/tools/01-build-assets.py    # mesh + textures into Patch Collection (--out-root <dir>: dry run)
python src/ArgentVerdict/tools/02-build-records.py   # YAML (refuses if a copied record changed hands, Pretty's mesh
                                                     # moved, or tools/01's mesh is not the winner of its path)
```

Rerun both after a Pretty Enderal Armory update (mesh and textures come from Pretty's copy of Noble Armory's;
`tools/01` asserts the block, knob and blood overlays); rerun `02` after EGO changes the Aeterna Warhammer or
Prophecy changes its Smite effect. Change the hand, forearm or bracelet in `tools/fist.py`, the rose vines in
`tools/roses.py` or the texture in `tools/fist_tex.py`, then rerun `01` (and `02`: the bounds).

## Placement

**Not placed yet**: where it is found is the curator's call. Test with `help "Argent Verdict"` →
`player.additem <id> 1`.

## Status

v1 to v4 built 2026-11-13, v5 (human hand, forearm into the handle, thorn bracelet) 2026-11-14: deserializes clean,
round trip through Spriggit with no differences (FormKey references checked on v2; since then only the bounds and
the plugin description changed), the mesh re-reads byte for byte through our NIF writer and opens in PyNifly (5
shapes); mesh, textures and plugin deployed into Patch Collection. **Unverified in game**: the hand, forearm, bracelet and
rose vines, their relief and engravings (the normal map's green convention is measured, not seen), the silver (both
views), the navy grip, Smite on power attacks only and at about one in four, the item card's text. Not ticked in MO2
yet.
