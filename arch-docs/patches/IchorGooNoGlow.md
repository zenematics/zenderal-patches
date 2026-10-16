# IchorGooNoGlow

- **Source:** `src/IchorGooNoGlow/`
- **Ships:** *(no plugin — generated meshes, MO2 mod `Zenderal - Ichor Goo No Glow`)*
- **FormID block:** _(none)_

## What it does

**Curator's taste: the green Dwemer ichor puddles keep their puddle but lose the green glow** (reported
2026-10-16 at `DweIchorGoo02 088896`, ref `0A1BBD` in `SuntempleChronikum 009900`). The glow is not a
placed light: the nearest LIGH refs in the cell are warm SolitudeInn candle/window lights 270+ units
away. It comes from JS Dwemer Ichor Barrels SE's replacement `clutter\dwemer\dweichorgoo01/02.nif`, whose
root BSFadeNode has four children: the puddle shape (`ooze` / `L1_GooBase09`), an `L2_warp0N` shimmer
billboard, a `PCloud0N-Emitter` additive green particle haze, and an `ENBLight` billboard
LightMesh that ENB turns into a green point light. That light is what tints the books and bowls around it.

`src/IchorGooNoGlow/tools/01-strip-goo-glow.py` copies JS's two meshes and sets the root's child
refs to the particle emitter and the ENB light to `-1`. It asserts exactly two detached per file. The
output differs from JS's file by 8 bytes, and the orphaned blocks stay in the file unreferenced.
The meshes are not committed. The mod must have **higher MO2 priority than JS Dwemer Ichor Barrels SE**,
and CRDW must be rebuilt after generating. **Verified in game 2026-10-16** (puddle kept, no green haze or light).
