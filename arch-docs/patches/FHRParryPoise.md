# FHRParryPoise

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FHRParryPoise/`
- **Ships:** `Zenderal - FHR Parry Poise.esp`
- **FormID block:** none (overrides only)

## What it does

For Honor Reforged's parry never visibly worked. Chain (traced 2026-10-05): backward light attack (DMK `DirecionalCycleMoveset == 5`) casts `$ParrySpell` (`BackLightParrySpell 80E`) ~32× across the clip = the parry window; the ATTACKER's `ReforgedParryController 876` (SPID'd to every actor by `Reforged_DISTR.ini`) casts `HitFrameTriggerSpell 803` on its target on every landed hit; on a parry the perk casts `Weapon Parry Poise Damage 892` (or `Shield… 5F7`) = `Poise Damage Parry 5F5` on `Variable01`. The visible knockdown is FHR's `Stagger/Parry Knockdown` OAR submod, which only REPLACES a stagger, and the enemy only staggers if Chocolate Poise - Reforged lets it: it counts `Variable01` magic damage as poise (`ChocolatePoise.json` → Magic Effects → Damage) but staggers only when one hit ≥ 25% of the pool (`[Impact Thresholds] Normal = 0.25`, human pool `BaseHealth = 100` + mass). FHR's 20 / 5 never cross it. Overrides both spells (copied verbatim from `For Honor Balance Patch.esp`) to **60 / 40**; nothing else overrides them. Ruled out on the way: TDM (`TDM_DirectionalMovement 807` only gates back moves in 360° mode; the list uses Vanilla Style), FHiS leftovers (meshes/scripts `.mohidden`), PIE (loads the parry payloads), the parry MGEFs (script-less markers). Masters: Skyrim + `For Honor Balance Patch.esp`. **Built and deployed 2026-10-05, not yet verified in game.**
