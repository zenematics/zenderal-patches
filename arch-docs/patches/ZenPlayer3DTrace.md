# ZenPlayer3DTrace

- **Source:** `src/ZenPlayer3DTrace/` (CommonLibSSE-NG, AE / Address Library; `build.cmd`)
- **Ships:** nothing — **testing tool, not part of the list**
- **FormID block:** _(none)_

## What it does

Every 2 s, on the main thread, while the player is Triumvirate's Horned Lord race (`000837`, looked up at data load),
it logs twice per race change (on seeing it, and 3 s later) to `My Games/Skyrim Special Edition/SKSE/ZenPlayer3DTrace.log`:

- the race, the race's skin, the actor base's **own** skin, and the skeleton path for the player's sex;
- every biped slot holding something, first and third person: item, addon, model, and whether the part attached;
- the third- and first-person 3D trees: node type, name, `HIDDEN` (AppCulled), local scale, geometry.

It hooks nothing and changes nothing. To trace another race, change the `LookupForm` in `main.cpp`.

## Why (2026-10-28)

Force of Nature left the player with no body, and four fixes built on guesses failed (armour, skeleton, mesh format,
overlays; see [`Prophecy.md`](Prophecy.md)). The first log showed `skin(actor base) 00000D64` (`SkinNaked`), no biped
slot filled and only the skeleton in the 3D: the player's own skin wins over the race's. Fixed in
`ZP_ForceOfNatureEffect.FormSkin`, verified in game the same day.

**Lesson:** for "invisible actor" bugs, log the actor's biped slots and 3D first; one log answered what six console
tests and four builds did not.

## Deploy for a test

Copy `compiled/ZenPlayer3DTrace.dll` into any enabled mod's `SKSE/Plugins/`, launch, reproduce, read the log, then
remove it. After the 2026-10-28 run it was moved out with the retired Triumvirate SE Meshes mod
(`E:/Zenderal-backups/2026-10-28-retired-triumvirate-se-meshes/`).
