# PusBeetleFixes

- **Source:** `src/PusBeetleFixes/` (generated: `tools/01-widen-hit-capsules.py`, `tools/02-build-spit-without-knockback.py`)
- **Ships:** `Zenderal - Pus Beetle Fixes.esp` + a generated `skeleton.nif` (not committed), MO2 mod `Zenderal - Pus Beetle Fixes`
- **FormID block:** _(none — one override)_

## What it does

Two curator requests, 2026-10-24: ranged hits on pus beetles (Enderal's chaurus) often didn't register, and their
venom spit knocked the player back.

### Ranged hitbox **[verified from the meshes 2026-10-24]**

Arrows and spells hit a creature's ragdoll capsules (`bhkCapsuleShape`s in its `skeleton.nif`), not the visible mesh. All
four beetle NPCs (`_10E_PusbugNerfed 038C65`, `_10E_PusbugTemplate 092A6D`, `_20E_Pusbug 0FEC83`, `_31E_Pusbug 1337A8`)
use `ChaurusRace 0131EB`, `ChaurusRaceLarge 006BB0` or `ChaurusRaceSmall 0133F5`, all on
`Actors\Chaurus\Character Assets\skeleton.nif`. The winning copy is **Pus Beetle Replacer**'s (Enderal SE Nexus 48),
ahead of Creature Replacer Pack and XPMSE. It swaps in 4thUnknown's kwama forager (`ChauurusSkin.nif`) but keeps the
chaurus's 26 capsules unchanged.

Measured by putting each skinned vertex in skeleton space through its dominant bone and taking its distance outside the
nearest capsule:

| Body | Vertices > 10 units outside the capsules | Worst |
|---|---|---|
| Vanilla chaurus (`Skyrim - Meshes0.bsa`) | 3.1% | 17 |
| Pus Beetle Replacer | **22.6%** | 34 |
| This fix | 0.1% | 10 |

The gaps were on the head (2,214 vertices, up to 23 units out), the end of the tail (`Tal3`, up to 34), the neck, the
forelegs and the ribcage. `tools/01` copies the replacer's skeleton and grows each capsule's radius by the 95th percentile
of how far its own vertices stick out (never shrinking, capped at +25). 20 of 26 grow, the largest by 23.9. Only the
radius floats change: 219 bytes. It asserts the result is no worse than vanilla's. The mod must have **higher MO2
priority than Pus Beetle Replacer**. Rerun `tools/01` if that mod updates.

Side effect to watch: larger capsules also make the death ragdoll bulkier.

### Venom spit knockback

EGO adds `XionParalyzeKnockback 0008C8` (Stagger archetype + `voicepusheffectscript`) as the first effect of
`crChaurusPoisonSpit01 06F6FE`. The override is EGO's record verbatim minus that effect, and the poison
(`crChaurusSpitFFAimed 06F6FD`) stays. EGO is the only other plugin that overrides the spell. The plugin masters EGO and
loads right after it. Regenerate with `python src/PusBeetleFixes/tools/02-build-spit-without-knockback.py reference/mods/EGO`
after an EGO update.

## Status

Built and installed 2026-10-24 in Ultra. Plugin round trip identical. **Unverified in game.**

**2026-10-25: the plugin had never loaded.** The MO2 mod was enabled, but `Zenderal - Pus Beetle Fixes.esp` sat
**unticked** in `plugins.txt` (MO2 lists a new mod's plugin disabled), so beetles still knocked the player down.
Ticked (line 430, after EGO at 52). Rechecked the beetles for other knockback: race `ChaurusRace 0131EB` (EGO) carries
the spit, `AbChaurusFX`, `Xion75%PoisonRes` and attack spells `crChaurusPoisonBite01`/`DiseaseRattles`, none with a
knockback; the 4 NPCs carry no spells. EGO's only other `XionParalyzeKnockback` user is `crXionParalyzeBite 001D52`,
on `_30E_DesertSpiderSmall` only. The capsule half (loose `skeleton.nif`) was always active.
