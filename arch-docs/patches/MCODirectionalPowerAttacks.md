# MCODirectionalPowerAttacks

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/MCODirectionalPowerAttacks/`
- **Ships:** `Zenderal - MCO Directional Power Attacks.esp`
- **FormID block:** none (overrides only)

## What it does

MCO/ADXP setups only. Overrides `PowerAttackLeft 019B22`, `PowerAttackBackward 019B23` and `PowerAttackRight 019B24` (all `:Skyrim.esm`), setting `AnimationEvent` to `attackPowerStartInPlace`. That is the same one-field change `Attack_MCO.esp` makes to `PowerAttackForward 019B25`; every other subrecord is byte-identical to `Skyrim.esm` (verified by subrecord diff). Why: Attack MCO-DXP's Nemesis patch reroutes only the standing power-attack state (`Weap_DefaultAttackPower_MSG`/`AttackPowerInPlace`) into `MCO_PowerAttack`, so vanilla side/back power-attack events played Enderal's own animations and never reached For Honor Reforged's DMK-gated (`DirecionalCycleMoveset` 3/7/5) OAR submods. No other plugin in the list overrides these three idles. Left-hand variants (`0E3F38`/`39`/`3A`) deliberately untouched. **Also** overrides the three sprint power-attack idles `AttackRightPowerForwardSprinting 0EC3CC`, `…2HWForwardSprinting 0EC3CE`, `…2HMForwardSprinting 0EC3CF` (copied from the winning `Update.esm` versions), and the two sprint **light**-attack idles `AttackRightForwardSprinting_1hand 0F0A3E` / `_2hand 1038BF` (first children of `NonMountedCombatRight`, ahead of `NormalAttack`), removing only their `HasPerk CriticalCharge 0CB406` / `GreatCriticalCharge 0CB407` condition. The light ones were added because `Attack_MCO.esp`'s own perk-free `Attack_Sprint 0018FC` (first child of `AttackRightRoot`) did NOT fire in game: LMB mid-sprint stopped the sprint and played `NormalAttack`. Why it is skipped is unexplained from the data (its conditions, the race ATKE `attackStartSprint` and the ADXP graph path all check out); BFCO instead re-parents `AttackRightRoot` under its own `BFCO_M1Root` with its sprint idle placed before it, plus an SKSE input handler; `IsSprinting` and the weapon-type checks stay. Why: in the merged ADXP graph, `MCO_SprintPowerAttack` (which FHR's "Sprint Attacks" submods replace) is entered **only** by `attackPowerStart_Sprint` (and the 2HM/2HW sprint events), and on MCO the only sender is these vanilla idles. Nothing in Enderal or EGO grants those perks, so FHR's sprint attack was unreachable. On BFCO it worked because BFCO's own `0_ScriptIdle_PowerattackSP` sends the event with no perk check. No other plugin overrides these idles. The perk check ran on the subject actor, so NPCs can now trigger these sprint idles too. Masters: `Skyrim.esm` + `Update.esm` (the sprint idles' parent `000991:Update.esm`).

## Unarmed sprint attacks (2026-10-22)

**Symptom:** with fists drawn, LMB/power attack while sprinting played an ordinary punch; For Honor
Reforged's unarmed sprint attack never showed.

**What FHR ships** (files, `mods/For Honor Reforged/.../OpenAnimationReplacer/`): `Brawler` is FHR's
unarmed set, and `Brawler/Sprint Attacks` (priority 8070051, `IsEquippedType 0`, right hand) replaces
both `MCO_SprintAttack.hkx` and `MCO_SprintPowerAttack.hkx`. A scan of every enabled mod's OAR folders
for those two files found nothing above it that matches fists (For Honor in Skyrim's Brawler copies sit
at 8070050/8070010; Peacekeeper etc. need a weapon). So the clips were there; nothing sent the event.

**Graph** (Pandora output `1hm_behavior.hkx`, converted with hkxconv): unarmed lives in
`1HM_Behavior` (`1HM_H2H_Readied`, `AttackRight_H2H` …; 0_master has a single `Weap_BehaviorBFR` →
`1HM_Behavior.hkx`). `1HM_Ready_State` takes `attackStartSprint` → `AttackState` nested 22
(`AttackForwardSprint` → `MCO_BRG_SprintAttack`) and `attackPowerStart_Sprint` → nested 24
(`AttackPowerForwardSprint` → `MCO_BRG_SprintPowerAttack`), both with `FLAG_DISABLE_CONDITION`. No
weapon-type gate in the graph.

**Idles — the actual cause:**

| Idle | Winner | Gate that excluded fists |
|---|---|---|
| `AttackRightForwardSprinting_1hand 0F0A3E` (first child of `NonMountedCombatRight 000990`) | this patch | `GetEquippedItemType Right >= 1` |
| `AttackRightPowerForwardSprinting 0EC3CC` (before `H2HRightHandPowerAttack 0E3F3D` under `000991`) | this patch | `GetEquippedItemType Right >= 1` |
| `AttackRightH2H 0870D6` | `Attack_MCO.esp` | none — it re-parents the idle to `AttackRightRoot 013211` (Skyrim.esm-era parent, previous sibling `100F16`, which is now a child of `000990`) and sends `attackStart` with no sprint check |

**Fix:** dropped the `>= 1` condition from `0F0A3E` and `0EC3CC` (the `<= 4` stays, so fists and the
four one-handed types), and added `0870D6` = Attack_MCO's record verbatim + `IsSprinting != 1`. The
`0870D6` change is there because the engine's order for an idle whose previous sibling is in another
parent is unknown: if `AttackRightH2H` is evaluated before `NonMountedCombatRight`, it would still
catch sprinting fists. With it skipped, whichever comes next sends `attackStartSprint` — our `0F0A3E`,
or Attack_MCO's `Attack_Sprint 0018FC` (`GetEquippedItemType < 7`, includes fists). The power path
needs nothing more: `0EC3CC` precedes Attack_MCO's `0E3F3D` in the same parent. Like the perk removal,
this applies to NPCs with fists too. Load after `Attack_MCO.esp` (not mastered; only Skyrim.esm and
Update.esm FormKeys).

**Deploy:** `Zenderal - Patch Collection` ships an older copy of this `.esp`, so the rebuilt one is
its own MO2 mod `Zenderal - MCO Directional Power Attacks`, sorted directly ABOVE (winning over)
`Zenderal - Patch Collection` — same pattern as No Screen Flashes. Drop the standalone mod once the
Patch Collection carries this build.

**Status:** verified in files (graph transitions, idle chain, OAR priorities, Spriggit round trip of the
idle records). **Not yet verified in game.** Test: fists drawn, sprint, LMB → Brawler sprint attack;
sprint + power attack → Brawler sprint power attack; standing LMB still punches normally.
