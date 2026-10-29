# TriumvirateSEMeshes

> **Not the cause (2026-10-28).** `ZenPlayer3DTrace` showed the player wore their own `SkinNaked` instead of the
> race's skin; the fix is in Prophecy's `ZP_ForceOfNatureEffect` (`FormSkin`). This conversion was built before that
> was known and costs the body's glow; retire it once the skin fix is verified in game.

- **Source:** `src/TriumvirateSEMeshes/` (`tools/01-convert-horned-lord.py`)
- **Ships:** *(no plugin — a converted mesh, MO2 mod `Zenderal - Triumvirate SE Meshes`, generated, not committed)*
- **FormID block:** _(none)_

## What it does

Converts Triumvirate's Horned Lord body, `meshes\triumvirate\verdant_actor_forceofnature.nif`, from Skyrim LE
format (stream 83, 14 `NiTriShape`s) to SE (`BSTriShape`s) through PyNifly. Prophecy's Force of Nature
([`Prophecy.md`](Prophecy.md)) turns the player into that race (`TVR_Verdant_Race_ForceOfNature 000837`).

Carried over per shape: geometry, UVs, normals, vertex colours, skin binds, the shader block, all nine texture
slots and the alpha property. Weights are capped at 4 influences (none of the 14 shapes needed trimming). Each shape
gets one `SBP_32_BODY` partition, since the source has plain `NiSkinInstance`s. **Not carried over:** the shader
colour/float controllers (an animated glow). The tool reads every shape back and asserts it, so a Triumvirate update
fails loudly. Loose files beat Triumvirate's BSA, so the mod only needs to be enabled.

## Why (curator, 2026-10-28)

In the form the player had **no body at all** (no shadow), male or female, clothed or naked, from the power or a
plain `player.setrace`. Console tests in game:

- a female NPC `setrace`d to the race **showed** the Horned Lord;
- `player.setrace ArgonianRace` (the race's head data is Argonian; same male skeleton as the fix below) kept the
  player visible.

So the failure is specific to the player wearing this LE body. The suspect is RaceMenu's overlays, which are on and
**player only** in this list (`skee64.ini`: `bEnableOverlays=1`, `bPlayerOnly=1`). The curator chose to convert the
mesh instead of testing that further, so the cause is **not proven**.

Ruled out on the way (each cost a test): the LE format by itself (the raven familiar's LE skinned `basecrow.nif`
draws), worn armour, missing skeleton bones, the Triumvirate - Enderal Patch dropping the records, the player's sex,
and Triumvirate's LE male skeleton (Prophecy now overrides it with XPMSE's `skeletonBeast.nif`; it did not help on
its own).

Other LE skinned meshes in the same BSA (`mihailsnowleopard.nif`, `basecrow.nif`, `demon_actor_leviathan.nif`,
`destructionfire_beam_volcano.nif`) are left alone: the familiars draw fine on NPCs. Leviathan is another player
form and may need the same conversion.

## Rebuild

Rerun `tools/01` after a Triumvirate update. Needs PyNifly (`tools.json` `pynifly`, V29.1.0). Unverified in game.
