# FHRParryPoise

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FHRParryPoise/`
- **Ships:** `Zenderal - FHR Parry Poise.esp`
- **FormID block:** none (overrides only)

## What it does

For Honor Reforged's parry never visibly worked. Chain (traced 2026-10-05): backward light attack (DMK `DirecionalCycleMoveset == 5`) casts `$ParrySpell` (`BackLightParrySpell 80E`) ~32× across the clip = the parry window; the ATTACKER's `ReforgedParryController 876` (SPID'd to every actor by `Reforged_DISTR.ini`) casts `HitFrameTriggerSpell 803` on its target on every landed hit; on a parry the perk casts `Weapon Parry Poise Damage 892` (or `Shield… 5F7`) = `Poise Damage Parry 5F5` on `Variable01`. The visible knockdown is FHR's `Stagger/Parry Knockdown` OAR submod, which only REPLACES a stagger, and the enemy only staggers if Chocolate Poise - Reforged lets it: it counts `Variable01` magic damage as poise (`ChocolatePoise.json` → Magic Effects → Damage) but staggers only when one hit ≥ 25% of the pool (`[Impact Thresholds] Normal = 0.25`, human pool `BaseHealth = 100` + mass). FHR's 20 / 5 never cross it. Overrides both spells (copied verbatim from `For Honor Balance Patch.esp`) to **60 / 40**; nothing else overrides them. Ruled out on the way: TDM (`TDM_DirectionalMovement 807` only gates back moves in 360° mode; the list uses Vanilla Style), FHiS leftovers (meshes/scripts `.mohidden`), PIE (loads the parry payloads), the parry MGEFs (script-less markers). Masters: Skyrim + `For Honor Balance Patch.esp`. **Built and deployed 2026-10-05, not yet verified in game.**

## HEDR 1.71 fix (2026-10-21)

TexGen stopped on *"Record [AVIF:000005F7] in file Skyrim.esm is being overridden by record
[SPEL:000005F7] in file Zenderal - FHR Parry Poise.esp. … version 1.7 which does not support form IDs <
0x800."* `For Honor Balance Patch.esp` is a 1.71 light plugin, and its `Shield Parry Poise Damage 5F7` and
`Poise Damage Parry 5F5` have object IDs below `0x800`. A 1.7 plugin cannot address those: the engine and
xEdit read any ID below `0x800` in a 1.7 plugin as a Skyrim.esm form. So the shield half of this patch
overrode Skyrim.esm's AVIF `0x5F7` (a type clash, CTD-capable), and the shield parry was never actually
raised. Only weapon parry (`892`) worked. The header is now **1.71** (light-plugin flag kept), and the
records are unchanged. A load-order scan finds no other 1.7 plugin with sub-`0x800` records from a
non-Skyrim file. Redeployed into *Zenderal - Patch Collection* (old copy in
`E:/Zenderal-backups/2026-10-21-fhr-parry-poise-171`). Unverified in game.
