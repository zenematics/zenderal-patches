# ZenTextureTrace → `ZenTextureTrace.dll`

**Testing tool, not part of the list.** MO2 mod `Zenderal - Texture Trace (testing)`, on the compiler's Ignore list.
Source `src/ZenTextureTrace/`, built with its `build.cmd` (shares the CommonLibSSE-NG clone in `lib/`).

## Why (2026-10-30)

Objects started rendering untextured on 2026-10-30: a white Frost Mirriam, a flat blue leek, a grey sack in Ark's
market. The same object was textured after a reload. Ruled out first, with evidence:

- **Missing or broken files:** the textures exist (loose or in a BSA) and are valid DDS. (The leek was a separate case:
  Skyrim's own 2011 texture, replaced since by the crop mods.)
- **VRAM:** Theo's Render Pipeline logs ~11 of 33 GB used, no budget warnings.
- **File handles:** Engine Fixes sets max stdio 8192 at launch.
- **Shader/texture errors:** none in `BottledShaders.log` or `TheosRenderPipeline.log`.
- **Generators running during play:** the curator never ran one with the game open.

The one change that lines up in time is Theo's Render Pipeline 0.5.4 → 0.5.6 (2026-10-29 16:42; it still reports
itself as 0.5.4). Its notes add a DLSS/NR/frame-generation history reset after loads, and say Neural Rendering
defaults off, while `Zenderal - Settings` turns it on. Unproven.

## What it logs

Once a second, on the main thread (an SKSE task), every placed reference within 6000 units of the player: for each
`BSLightingShaderProperty` shape, the material's diffuse and normal `NiSourceTexture` must exist, have a renderer
texture and a shader resource view.

- **STUCK:** a slot bad for 3 s or more, once per shape: the reason, ref, base form + plugin + type, model, shape, slot,
  the texture set's path, the `NiSourceTexture`'s own name and pointers, distance.
- **RECOVERED:** a STUCK slot that loads, with how long it took.
- **summary** every 30 s: cell, refs and shapes in range, slots bad now, STUCK so far.

Log: `My Games/Skyrim Special Edition/SKSE/ZenTextureTrace.log`. Reads only, never writes.

## Reading the result

- **An untextured object with a STUCK line:** its texture never loaded. Look at the path, the plugin and when it
  happens (cell load, fast travel).
- **An untextured object with no line while it is grey on screen:** the texture is loaded on the GPU, so it is being
  drawn wrong. That points at the renderer (Theo's Render Pipeline / its Neural Rendering) or a shader, not at files.

## 1.1.0: placeholder check

1.0.0 found nothing in two sessions while objects were white on screen: a placed sack and grass-mod plants
(grass is not a reference, so it is outside this trace). It only checked that a texture was *bound*. While a
texture streams in, the engine binds a shared stand-in, which passes that check and draws flat white/grey with
normal lighting. 1.1.0 also flags a diffuse whose GPU texture is 8x8 or smaller ("tiny GPU texture"), logs each
STUCK texture's GPU size, mips and view, and lists in the summary every GPU view that several differently-named
textures share.

## Status

Built and deployed 2026-10-30, enabled in Ultra. **Disable after use** (MO2 must be closed to change the profile).
