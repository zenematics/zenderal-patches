# RelentlessSwordPatreon

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/RelentlessSwordPatreon/`
- **Ships:** `Zenderal - Relentless Sword.esp`
- **FormID block:** `0x800–0x833`

The two-build history and the one-ModKey/two-archives shape are in [`../workspace/release-shapes.md`](../workspace/release-shapes.md#two-mutually-exclusive-upstream-builds).

## What it does

`800–806` statics (1st-person models), `809–80F` weapons, `811–81F` forge + temper recipes (johnskyrim's original offsets, preserved for traceability), `820–825` dismantle recipes (new, this repo's), `826` crafting blueprint, `827` its placed reference in Riverville Temple — those 33 records were the free six-blade Nexus release. Then `828–829` statics, `82A–82B` weapons, `82C–82D` forge recipes, `82E–82F` tempers, `830–831` dismantle recipes for johnskyrim's Patreon "Zen" blade, allocated **above** the first block so a user coming from the six-blade build keeps every FormID. **The six-blade release was removed on 2026-08-16** (`src/RelentlessSword/`, plus `build-zen-tree.ps1`, which derived this tree from it and had no input left) — this folder is now hand-edited source of truth, and its assertions (42 record files, 8 blueprint-gated recipes, no `0F46CE`/`0F46D1` Skyforge refs) went with it. The **plugin filename was deliberately NOT renamed with the release**, for the same FormID reason

## Relentless Zen: the curator's own blade (2026-10-31)

The 1H Zen blade `00082A` is made the list's strongest one-handed sword, silver, and a corpse-consecrating weapon (curator's design).
The 2H Zen `00082B` and the other six blades are unchanged.

- **Stats:** damage 23 → **45**, critical damage 6 → **34**, value 1000 → 2500. The strongest obtainable one-handed sword was
  EGO's Al-Rashim's Heritage `15037B` (41 / 31), then Thorium Sword `0240F7` (35 / 26). SureAI's `_00E_Debug_Sword` (75) is
  console-only and excluded. **Rerun `tools/00-scan-swords.py` after any weapon mod change**: it ranks every winning
  one-handed sword in the Ultra profile and exits 1 when Zen is no longer strictly the strongest in damage and in critical damage.
- **Keywords added:** `WeapMaterialSilver 10AA1A` (EGO's player perks `XionSilverUndeadDmg 001D26` ×2.15 vs undead and
  `XionSilverGhostDmg 001D3F`, and Prophecy's Smite, which keys on silver), `WeapTypeUnique 14CE9A` (only read by merchant
  hello dialogue), `MagicDisallowEnchanting 0C27BD` (can't be disenchanted to learn the effect). Ebony stays, so tempering keeps
  its perk. Enderal's own Lightbringer carries the same silver/unique/disallow set.
- **Consecrate Dead on corpse hits:** enchantment `ZEN_EnchRelentlessZen_Consecrate 000833` (NoAutoCalc, cost 0, the shape of
  vanilla's `BoundSwordEnchantment 069CE7`; the weapon's charge is 1000 so it never runs dry) carries
  `ZEN_RelentlessZen_ConsecrateMGEF 000832`, a contact copy of Prophecy's `ZP_Holy_ConsecrateMGEF 000A30` (same
  `_LIP_ConsecrateScript` + `ZP_HolyPlaceExplosion` and property values; projectile, casting art/light and cast sounds dropped,
  Touch). Conditions: `GetDead == 1`, not already under `000832` or the spell's `000A30`, no `MagicNoReanimate`. The script
  disintegrates the body into an ash pile (the ash pile keeps the loot) and casts Prophecy's 30-point heal `000A41` on the wielder.
  **Masters `Zenderal - Prophecy.esp`** for those records, and needs its two scripts (Prophecy ships them).
- **Unverified in game.** Whether the engine runs a weapon enchantment on a hit against a dead actor is not proven here; the
  evidence is Bethesda's soul-trap contact effect `EnchSoulTrapFFContact 05B452`, which carries a `GetDead == 0` guard. If the
  test fails, the next step is a read-only trace of the hit, not another guess.
