# KnightOfThePath

- **Source:** `src/KnightOfThePath/` (generated: `tools/01-build-knight-of-the-path.py`)
- **Ships:** `Zenderal - Knight of the Path.esp` + 25 meshes copied from ERA (not committed), MO2 mod `Zenderal - Knight of the Path`
- **FormID block:** `0x800–0x813`
- **Masters:** Skyrim.esm, Update.esm, Enderal - Forgotten Stories.esm, Enderal SE - Gameplay Overhaul.esp

## What it does

Curator's request (2026-10-27): **keep both Righteous Path looks instead of one overwriting the other.** Pretty
Righteous Path Armory stays the Righteous Path; Enderal Remastered Armory Part 1's remaster becomes a new
five-piece set, **Knight of the Path** (helmet, cuirass, gauntlets, boots, shield).

**Why only one was ever visible [verified 2026-10-27]:** all Righteous Path armors (plain, Forged and the
Keeper's addon apart) draw `armor\ebony\{m,f}\*.nif` and `weapons\ebony\ebonyshield.nif`. ERA ships 25 files and
Pretty 24 + the shield at exactly those paths, so whichever mod won in MO2 replaced the other's whole set. Their
only overlaps are those 25 files (plus the 4 SMP cuirasses), so the left-pane order of ERA vs Pretty changes
nothing else.

| Piece | ARMA | ARMO | Forge recipe | Temper | Copied from (winning version) |
|---|---|---|---|---|---|
| Helmet | `0x800` | `0x804` | `0x808` | `0x80C` | addon `05B69A` base, armor `13C54C` base, recipe `13C54E` EGO, temper `148A48` base |
| Cuirass | `0x801` | `0x805` | `0x809` | `0x80D` | `05B69C` base, `13C54B` **EGO**, `13C54F` EGO, `148A46` base |
| Gauntlets | `0x802` | `0x806` | `0x80A` | `0x80E` | `05B69B` base, `13C54A` base, `13C550` EGO, `148A44` base |
| Boots | `0x803` | `0x807` | `0x80B` | `0x80F` | `145879` **Zenderal - EGO 2.1 Compatibility** (2.1 races), `13C552` base, `13C551` EGO, `148A4B` base |
| Shield | `0x810` | `0x811` | `0x812` | `0x813` | `0E400D` base, `13C54D` **EGO**, `13C553` EGO, `148A49` base |

Winners from a scan of every enabled plugin (EditorID search incl. compressed records): EGO, EAM (adds its own
addon copies only), Enderal SE - Bug Fixes (weapons only) and EGO 2.1 Compatibility. The shield was added second,
after the profile check showed ERA also ships `ebonyshield.nif`.

- **Stats = the Forged Righteous Path** (armor rating, weight, value, keywords incl. EGO's), curator's choice.
- **Obtained at the forge only**, curator's choice: each forge recipe is EGO's Forged recipe verbatim (the same
  per-piece blueprint — e.g. helmet `135755`, cuirass `1337D9` — owned by the player or by `02A3DB:FS`, or
  Smithing ≥ 50; same materials). No leveled list, outfit or vendor is touched, so nothing else in the list can
  conflict with it, and no existing record is overridden.
- Names: "Knight of the Path Helmet/Cuirass/Gauntlets/Boots/Shield" (plain English; base Enderal's localized
  name blocks replaced).
- Meshes: ERA's files copied verbatim to `meshes\armor\zenderal\knightofthepath\{m,f}\` (both weight halves of
  each `_1` the addons name, the ground models, and `ebonyshield.nif` at the folder root); each model's MODT
  `Data` line is dropped. They keep pointing at ERA's own textures (`textures\armor_replacer\ebony\`,
  `armor_replacer\hide\minerclothes*`, `cubemaps\ebony_armor.dds` — all shipped by ERA, by nothing else), so
  **ERA must stay enabled**.

## Load order (MO2 left pane, set 2026-10-27 in the Ultra profile)

`Zenderal - Knight of the Path` → `Zenderal - Pretty Righteous Path SMP` → `Pretty Righteous Path Armory` →
`Enderal Remastered Armory Part 1` (top to bottom = higher to lower priority in `modlist.txt`). ERA must sit
**below** Pretty, or ERA's meshes take the Righteous Path's paths again. Knight of the Path's own files are at
unique paths, so its position doesn't matter. Plugin: after EGO, before the load-last cleanup patches
(`plugins.txt` line 409).

## Status

Built (ESL, HEDR 1.7, 5 ARMA / 5 ARMO / 10 COBJ; `build.ps1 -CheckFomod` passes) and deployed. **Verified in
game 2026-10-27** by the curator: crafts at the forge and looks right. Rerun `tools/01` (then deserialize) after ERA, EGO, EGO 2.1 Compatibility or base Enderal changes any of
the source records.
