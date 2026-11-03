# FHRDirectionalStripFix

- **Source:** `src/FHRDirectionalStripFix/` (generated: `tools/01-build-fhr-directional-strip-fix.py`)
- **Ships:** `Zenderal - FHR Directional Strip Fix.esp` (ESL, **HEDR 1.71**: it references Reforged Directional
  Combat's sub-`0x800` IDs `497`/`498`), MO2 mod `Zenderal - FHR Directional Strip Fix`
- **Masters:** Skyrim.esm, Enderal SE - Gameplay Overhaul.esp, KataHiddenPowers.esp, For Honor Balance Patch.esp,
  Reforged Directional Combat.esp. **Load after `Reforged Directional Combat.esp` and `EGO SE - KataPUMB Hidden
  Powers.esp`** (directly after Reforged Directional Combat is fine).
- **Status:** built and deployed 2026-10-31; the truth table of every generated entry checks out offline (below).
  **Unverified in game.**

## What it fixes

For Honor Reforged's directional addon (Reforged Directional Combat) shows *empowered-attack arrows* over enemies;
the player strips one by hitting with an attack of the same side and weight (lights strip lights, heavies strip
heavies). In this list:

- **Side power attacks never stripped a heavy arrow in first person.** FHR's heavy marker (`LeftHeavy 882` /
  `RightHeavy 883` on the attacker) comes from a `PIE.$LeftHeavy`/`$RightHeavy` clip annotation. The player's 1P
  power-attack clip generators (`AttackPowerInPlace_Player` → `1HM/2HM/2HW_AttackPower_Intro` and the main
  generators, sneak too) carry `flags 16` = `FLAG_DONT_CONVERT_ANNOTATIONS_TO_TRIGGERS` (value read from
  `SkyrimSE.exe`'s Havok enum table), so no annotation in a 1P power-attack clip ever becomes an event —
  [`FHRFirstPerson`](FHRFirstPerson.md)'s tags on those clips are inert. Flipping the flag would also fire the
  clips' own `HitFrame`/`WeaponSwing`/`attackStop`/`Collision_*` annotations (700+ each across the 1P power clips) on
  top of the graph's triggers.
- **Even with the marker, EGO took the slot.** The engine applies **one** combat hit spell per hit (trace: the
  winning spell's effects apply ~1 ms before `TESHitEvent`, never two spells). EGO's `XionPowerStagger 001DBD`
  (priority 0; power attacking, humanoid target, weapon keywords) won 7/7 power-attack hits; FHR's heavy dispels
  are priorities 0/1 in their own perk.
- **Side lights used the slot when there was nothing to strip.** FHR's dispel entries only checked the attacker's
  marker, so every side light hit cast a dispel spell (beating FHR's own parry check `803`, 2/2 in the trace) even
  on an enemy with no arrow.

Evidence: `ZenParryTrace` 1.3.0 log of 2026-10-31 ([`ZenParryTrace`](ZenParryTrace.md)); record reads below.

## How

Two overrides, both regenerated from the serialized winners:

1. **`ReforgedEnemyDirectionalDispels 00082C:Reforged Directional Combat.esp`** — its four `ApplyCombatHitSpell`
   entries (priorities and spells unchanged: right heavy 0 → `826`, left heavy 1 → `827`, right light 3 → `829`,
   left light 4 → `82A`):
   - **Target tab (new):** the matching arrow (`801`/`802`/`804`/`805`) and (not blocking OR `0008BC`) — exactly
     when the dispel spell's purge (arrow + not blocking) or block-purge (arrow + `8BC` + blocking) MGEF strips.
   - **Heavy owner tab:** heavy marker OR (side *light* marker AND `IsPowerAttacking`), written as
     `(H OR L) AND (H OR PA)`. Every 1P power attack starts as a light attack (`SBF_NormalAttackStart` + the light
     tag, then `SBF_PowerAttackStart` ~300 ms later on the hold), so the light marker (`880`/`881`, ~1.4–2 s) is on at
     every side power-attack hit; NPCs and third person still use the real heavy marker.
   - **Light owner tab:** FHR's own (marker OR unarmed buff `497`/`498`) AND not power attacking (lights strip
     lights). Upstream's right-light entry ends with a stray OR, so the owner tabs are written fresh, never appended.
2. **`XionPowerStagger 001DBD:Enderal SE - Gameplay Overhaul.esp`**, from **`EGO SE - KataPUMB Hidden Powers.esp`**,
   which wins it (it adds `002E32:KataHiddenPowers.esp` absent). Its one entry becomes four copies, split by which
   side markers the attacker carries (right = `883` or `881`, left = `882` or `880`): none / right only / left only /
   both, each adding "the matching heavy arrow is not strippable" to the target tab. Exactly one copy passes
   unless a heavy dispel strips — then none does, and the dispel takes the slot. This holds however the engine orders
   entries across perks (the trace fits both "lowest priority number wins" and "perk order EGO → Directional → FHR").

No other enabled plugin overrides either perk (binary scan of the Ultra load order, 2026-10-31).

## Costs (curator accepted)

- A hit that strips a heavy arrow does not also get EGO's power-attack stagger (one hit spell per hit).
- The heavy signal in first person is the side light marker, which lasts up to ~2 s: a left light followed within
  that time by a right power attack carries both markers and may strip a left heavy arrow.
- Side light attacks in first person have no visible side (SIGMA's lights are the plain chain; see
  [`FHRFirstPerson`](FHRFirstPerson.md)); unchanged here by choice.
- A blocking enemy is only stripped with FHR's `8BC` — FHR's own rule, kept.

## Verification so far

- Spriggit round trip of the built plugin: both perks identical to the source YAML; HEDR 1.71, ESL, the five masters.
- Truth table: every generated entry evaluated with Skyrim's OR grouping over all 2048 combinations of the four side
  markers, power attacking, the four arrows, blocking and `8BC`: each dispel passes exactly when intended, EGO's four
  copies never overlap, and EGO yields exactly when a heavy dispel strips (0 mismatches).
- Not yet: in game. Test with [`ZenParryTrace`](ZenParryTrace.md) 1.3.0: a side power attack into a same-side
  yellow arrow should show `BUFF … arrows [-]` right after the `HIT`, and the APPLY lines just before the hit
  should name the heavy enemy purge, not EGO's `Stagger`.

## Regenerate

After Reforged Directional Combat or EGO SE - KataPUMB Hidden Powers updates: re-serialize them into
`reference/mods/FHRDirectional` and `reference/mods/EGOKataPUMBHiddenPowers` (Spriggit 0.40.0), run
`python src/FHRDirectionalStripFix/tools/01-build-fhr-directional-strip-fix.py` (it asserts the upstream entries'
spells, priorities and conditions and stops if they changed), deserialize, redeploy. If another plugin starts
overriding either perk, build from the new winner.
