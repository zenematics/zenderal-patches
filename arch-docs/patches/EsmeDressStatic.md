# EsmeDressStatic

- **Source:** `src/EsmeDressStatic/` (generated: `tools/01-build-esme-dress-static.py`)
- **Ships:** MO2 mod `Zenderal - Esme Dress Static`, two generated meshes, not committed (they are Pretty's and
  Fuse00's work, built from the user's own install). No plugin. Loose files beat Pretty's BSA, so its MO2 position
  doesn't matter (no other mod ships these paths loose). Wabbajack: `NoMatchInclude` in `Zenderal.compiler_settings`.
- **FormID block:** none
- **Status:** built and deployed 2026-11-09, not yet enabled in MO2 (MO2 was open). Unverified in game.

## Why

Player reports (Longinus, confirmed by GreaseLord, 2026-11-09): "Esme's Dress is giving me a seizure (Physics)", then
"now its her boobs": a long skin-coloured strip from her chest to the ground.

- Esme (`_00E_FS_NQ02_Esme 01F0D0:FS`) wears the Hunter's Armor cuirass `0BCB89` (addon `0BCB85`) in both her outfits,
  `02A46C` (travelling) and `029780` (armour), and Pretty Enderal Clothing's hood `000818` (addon `000819`). Nothing
  else in the list uses that cuirass.
- **Pretty Enderal Clothing replaces the female meshes** (`Pretty Enderal Clothing.bsa`):
  - `huntertorsof_1.nif` is Fuse00's Adventurer outfit, `Adv_Female_Body_1.nif` from *Adventurer HDT-SMP Armor*, 21
    bytes apart;
  - `hoodf_1.nif` is its hood.
  - Both carry FSMP's marker (`HDT Skinned Mesh Physics Object` → `Meshes\Fuse00\Armor\Adventurer\Adv_body.xml` /
    `Adv_hood.xml`). The XML is identical in Pretty and the Adventurer mod.
- The body XML simulates the skirt, sleeves, neck straps, bags, bottle and cup bones. When the simulation goes
  unstable they are flung: the "seizure" is the skirt and sleeves, the stretched "boob" is the chest straps.
  Esme's Malphas' Blessing body (`0mbBody_Aeterna 000832`, `MB\0bodies\F\FemaleBody_1.nif`) has no breast bones or
  physics at all.
- The trigger was not found. FSMP 4.1.1's `configs.json` is near stock (`clampRotations`, `unclampedResets` at 130°).
  Esme being moved by quest scripts is the likeliest trigger. In-game workaround: `smp reset` on her.

## The fix

Curator's choice: a static dress rather than chasing the trigger.

- The generator reads both meshes out of Pretty's BSA. It renames the marker's header string to the same-length
  `ZEN Static Dress (SMP disabled)`, so FSMP finds no physics and every offset stays put.
- The bones keep their bind pose, so Esme keeps Pretty's look and the cloth no longer moves.
- Asserted: the marker appears exactly once per mesh, and only those bytes change (24 per file).
- Pretty ships only `_1` meshes, so this does too.

## Upkeep

After a Pretty Enderal Clothing update, rerun `python src/EsmeDressStatic/tools/01-build-esme-dress-static.py`. It
needs the `lz4` package, so run it without `-I`.

## To verify in game

Find Esme (Forgotten Stories, NQ02) and follow her for a while: the dress and hood stay still. No strips on the
ground. `smp list` (FSMP console command) should not list her.
