# CBBENeverNudeMorphs

- **Source:** `src/CBBENeverNudeMorphs/` (generated: `tools/01-merge-tri.py`)
- **Ships:** *(no plugin — one generated `femalebody.tri`, not committed; MO2 mod `Zenderal - CBBE NeverNude Morphs`)*
- **FormID block:** _(none)_

## What it does

**The NeverNude bra and panties follow RaceMenu's body sliders.** Player report (Nexo, Discord 2026-10-30):
undressed, the character's bra sits inside the body under the breasts.

**[verified 2026-10-30 on the Ultra profile]**

- The list's female body is CBBE 2.0.3, installed as **Slim + NeverNude + RaceMenu Morphs (BodyMorph)**
  (its FOMOD choices in `meta.ini`). Both female body textures (CBBE's and BnP's) are nude; the underwear is
  NeverNude's own mesh: `femalebody_0/1.nif` hold three shapes, `CBBE`, `Bra` and `Panty`.
- RaceMenu morphs body shapes from the `.tri` named by the nif's `BODYTRI` (`femalebody.tri`). CBBE's shipped
  file has **one shape, `CBBE`** (97 morphs): nothing for `Bra` or `Panty`. Any body slider moves the body and
  leaves the underwear where it was; raising the breasts pushes them through the bra.
- Nothing else in the list ships a body `.tri`, CBBE's installer has no option that morphs NeverNude, and a
  search found no prebuilt Nexus mod for it. BodySlide is the intended route.

## How it is built

1. BodySlide and Outfit Studio 6.0.0 (Nexus 201, MO2 mod `BodySlide and Outfit Studio`, on the compiler's
   Ignore list: a build tool, never shipped) copied to a scratch folder with CBBE's `CalienteTools/BodySlide`
   merged in, `Config.xml` `TargetGame` 4. A one-member group `ZenNeverNude` = `CBBE NeverNude`, then:
   `BodySlide.exe --groupbuild "ZenNeverNude" --targetdir <out> --preset "CBBE Slim" --trimorphs`.
2. `tools/01-merge-tri.py <CBBE's femalebody.tri> <build's femalebody.tri> <out>` writes the shipped file.

**Only the `.tri` ships; CBBE's meshes stay as installed.** Neither the `CBBE Slim` nor the zeroed build
matches CBBE's prebuilt NeverNude meshes (up to ~2 units off; the prebuilt `Bra` is median 0.75–0.94 units
from the build), so shipping a rebuilt body would change every woman's shape. The morphs fit the shipped
meshes: the triangle lists of all three shapes are identical between build and install (same vertex order),
and the build's `CBBE` morphs match the shipped ones to 0.07 units.

The build's `CBBE` morph set lacks six of the shipped ones (`BreastSideShape`, `BreastUnderDepth`,
`ButtDimples`, `ButtUnderFold`, `HipCarved`, `NippleDip`) and adds 30 (`*_v2` and others). The merge keeps all
97 shipped `CBBE` morphs byte for byte, adds the build's 30 extra, and takes the build's `Bra` (76) and
`Panty` (61): 3 shapes, 3,221,604 bytes. The trailing UV-morph section is identical in both inputs and kept.

File format (RaceMenu `PIRT`): `u16` shape count; per shape `u8`-length name, `u16` morph count; per morph
`u8`-length name, `f32` multiplier, `u16` vertex count, then per vertex `u16` index + 3 × `i16` delta
(× multiplier); then the UV-morph section.

## Install

MO2 mod `Zenderal - CBBE NeverNude Morphs` (one file,
`meshes/actors/character/character assets/femalebody.tri`), **sorted above CBBE in priority** (below it in
MO2's left pane), on the compiler's Include list.

## Rerun

After a CBBE or BodySlide update: rebuild step 1, rerun `tools/01`, recopy. `tools/01` asserts the shipped file
has only `CBBE`, the build has `CBBE`/`Bra`/`Panty` and the UV sections match. If CBBE's own morph file ever
covers `Bra`/`Panty`, retire this.

## Status

Built 2026-10-30. **Verified in game 2026-10-30**: with the mod enabled, the bra follows a raised breast slider
in RaceMenu's Body Morphs tab. (A first test without it showed the bug: the mod hadn't been enabled in MO2.)
