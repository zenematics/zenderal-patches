# StancesNoIcon

- **Source:** `src/StancesNoIcon/`
- **Ships:** `Zenderal - Stances No Icon.esp` (ESL, HEDR 1.7, overrides only)
- **FormID block:** none
- **Pillar:** curator's taste

## What it does

*Stances - Dynamic Weapon Movesets SE* shows the current stance as an icon floating above the player's head.
Each stance applies a magic effect whose **HitEffectArt** is an ART0 with the icon mesh **[verified from records]**:

| MGEF | ART0 | Mesh |
|---|---|---|
| `stances_high_icon_mgef 06AD25` | `stances_high_icon 06AD22` | `Stances\high_icon.nif` |
| `stances_mid_icon_mgef 06AD26` | `stances_mid_icon 06AD23` | `Stances\mid_icon.nif` |
| `stances_low_icon_mgef 06AD27` | `stances_low_icon 06AD24` | `Stances\low_icon.nif` |
| `stances_neutral_icon_mgef 07F13A` | `stances_neutral_icon 07F139` | `Stances\neutral_icon.nif` |

The overrides are those four records verbatim with the `HitEffectArt` line removed. The stance perks, the
`stances_switch_*` effects and the coloured body glow (`*_shader_mgef`, HitShader `07A035`–`07A038`) are not touched.
No other plugin in the list overrides the four records (serialized load-order scan, 2026-10-21).

## Regenerating

Serialize `Stances - Dynamic Weapon Movesets SE.esp` with Spriggit 0.40.0, then run
`python src/StancesNoIcon/tools/01-build-stances-no-icon.py <that folder>`. The script asserts each removal.

## Status

Built and deployed 2026-10-21 (MO2 mod `Zenderal - Stances No Icon`, plugin right after the Stances plugin).
Unverified in game.
