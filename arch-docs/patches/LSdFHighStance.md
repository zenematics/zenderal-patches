# LSdFHighStance

> **Shelved 2026-11-10.** The curator put cheming1228's Nordic pack on F1 instead
> ([`StanceMovesets`](StanceMovesets.md)). The MO2 mod is unticked in Ultra (folder kept), the tools and this doc stay
> for a later return; `tools/01`'s DAR parser and `fhr_negations` are still imported by StanceMovesets. Last state:
> pace 0.96/0.88 and AMR forward steps, built but never tested in game.

- **Source:** `src/LSdFHighStance/tools/01-build-lsdf-high-stance.py` (imports `src/FHRFirstPerson/tools/hkx_annotate.py`)
- **Ships:** *(no plugin — generated OAR mod, MO2 mod `Zenderal - Le Sentiment du Fer High Stance`, 50 submods,
  960 clips, 21 MB, not committed)*
- **FormID block:** _(none)_
- **Input:** Khonraad's *Le Sentiment du Fer - HEMA Combat Overhaul* **SSE** 1.01
  (`Le Sentiment du Fer - HEMA Combat Overhaul-50798-1-01-1624751200.zip`, Nexus 50798, md5
  `1c087bdd5c72f7a5fdf28a371aa4fdc7`) read straight from MO2's `downloads/`. Not installed as a mod itself.

## What it does

Curator's request (2026-11-10): Le Sentiment du Fer (LSdF), a grounded HEMA moveset built on SkySA, as the **High
stance** of *Stances - Dynamic Animation Sets* (F1), on the list's ADXP|MCO, without breaking For Honor Reforged.
Third person only.

| In High stance (F1) | Plays |
|---|---|
| light / power attacks, any melee weapon or fists, alone, dual-wielded or with a shield/torch | LSdF's combo for the weapon and the player's skill tier |
| idle, turns, walks, runs, equip (from One-/Two-Handed 25) | LSdF's guard |
| left / right / back attacks, the back-light parry, parry, block-slide and knockdown follow-ups, FHR's combo layers | **For Honor Reforged's own clips**, with their mechanics |
| sprint attacks, blocks, bashes, recoils, staggers | unchanged (FHR, Dynamic Block Hit, the stagger mods) |
| any other stance | unchanged |

LSdF's progression is kept and lines up with Enderal's skill tiers: below 25 in both One- and Two-Handed the
"untrained" two-hit combo, 25+ (either skill) the trained guard and two hits, 50+ four attacks and power attacks, 75+
the fifth attack and the master power attack (two hits). Unlike LSdF, each tier's combo loops instead of ending, and
the next attack starts right after the hit (pace, see Mechanism). Dual wield, daggers, fists and shield combos use One-Handed;
greatswords, battleaxes and warhammers Two-Handed, exactly as LSdF's DAR folders do.

## Evidence

**F1 is High stance [verified in files].** The winning `dtryKeyUtil/config/custom/Stances.ini` (Zenderal - Input
Defaults, beats Complete Controller Setup) binds scan code 59 to `0x93543` = `stances_switchspell_H`; the High
stance perk is `stances_highstance_perk` `042518:Stances - Dynamic Weapon Movesets SE.esp` ("High Stance").
ZenKeyTrace runs those key traces on 1.7.104.

**The download the curator grabbed first was the LE build** (Nexus `skyrim` 107910): every clip is a 32-bit packfile
(`4, 1, 0, 1` header), unreadable on SSE. The same author's SSE upload (50798, same 1.01 content) is 64-bit.

**LSdF is SkySA.** DAR folders hold `skysa_<weapon>N` / `skysa_power<weapon>N` (weapon = sword, axe, mace, dagger,
h2h, dw, 2hm, 2hw), N = combo position 1–5, each attack able to turn into power attack N+1. Combo windows are clip
annotations `SkySA_AttackWinstart` / `SkySA_AttackWinEnd`; the last attack of a tier has no window. Tiers are folders
gated by `IsActorValueLessThan(6|7, 25|50|75)`; loose root `skysa_*` files are the untrained tier. Its own SkySA
behavior patch (`Nemesis_Engine/mod/skysa`) and `(SdF) HEMA Combat Overhaul.esp` / Stagger on hit are not used.

**MCO's format [verified in files].** ADXP|MCO plays `mco_attack0..10` / `mco_powerattack0..10` (Attack MCO-DXP's
`amco` Nemesis patch) and reads `MCO_WinOpen`/`MCO_WinClose`, `MCO_PowerWinOpen`/`MCO_PowerWinClose`,
`MCO_Recovery` and `PIE.@SGVI|MCO_nextattack|N` / `MCO_nextpowerattack|N`. Attack MCO-DXP's own default folders are
SkySA conversions and show the mapping (their power attacks still carry a leftover `SkySA_AttackWinEnd`): window
start → both WinOpens, window end → both WinCloses + Recovery, next slots set at 0.06 s. The amco graph has no
SkySA events, so LSdF's clips do nothing under MCO until converted.

**Dual-wield left-hand hits lived in LSdF's graph patch, not in its clips.** Its `#skysa$…` clip generators for
`skysa_dw2..5` / `skysa_powerdw1..5` carry `hkbClipTrigger`s with event id 36 (`HitFrame` in 1hm_behavior's event
list, also index 36 in Attack MCO-DXP's `#0085`) at 0.26–1.08 s (the "Lefthand Hitframe Memo" in the archive lists
them). Each clip's `weaponLeftSwing` comes before it, so the trigger is the left hand's hit. MCO does not run that
patch, so the generator writes a `HitFrame` annotation at each trigger time (not if one is within 0.03 s already). FHR's own dual-wield
clips use the same `WeaponLeftSwing` → `HitFrame` pattern.

**For Honor Reforged owns the same slots [verified in files].** Only FHR provides `mco_attack*` clips in the list
(540 enabled submods, priorities up to 80,860,070). Each class has a plain "Normal Attack(s)" submod plus special
ones told apart by **conditions**: directional (`DirecionalCycleMoveset` right 3 / back 5 / left 7, with TDM's
not-locked-on test `807`/`804`, sometimes Stamina ≥ 20), back-light parry (also not during `PlayerBackLightCooldown
5F9`), parry follow-up (target has `ParryKnockdownFollowupSelfTrigger 86E`, not `ParryFollowupCooldown 872`),
block-slide (`878`), knockdown (`828`), shield parry (`811`), combo layers (FHiS `MA_Combo_Layer_2 80E`). Their
priorities sit 1–5 above the class's normal one, so no priority slots in between (the 2026-08 stance-gate lesson).
The mechanics (`$LeftLight`, `$ParrySpell`, `$BackHeavy`, …) are PIE annotations inside those clips.

## Mechanism

1. **Exact DAR evaluation.** For every right-hand type (fists, sword, dagger, war axe, mace, greatsword, battleaxe,
   warhammer), every left-hand type (empty, the four one-handers, staff, shield, the five spell schools, scroll,
   torch; none for two-handers) and every One-/Two-Handed band pair (`<25`, `25–49`, `50–74`, `75+`, sampled at
   10/30/60/80), the generator evaluates LSdF's `_conditions.txt` (DAR rules: `OR` lines group, groups `AND`;
   higher folder number wins per file; root files lowest; player, not sneaking, NPC folders false). Results with the
   same clip bytes share one submod (LSdF's axe and mace clips are byte-identical). `tools/02-verify.py` evaluates
   the written conditions over all 1,168 cases (73 weapon pairs × 16 band pairs): every case gets exactly one attack
   submod and at most one guard submod (0 problems, 2026-11-10).
2. **Conditions per submod**: `HasPerk 042518` (High Stance), `IsActorBase` player, the weapon pairs and skill
   bands that produce it (factored into rectangles), then for attacks one negated block per FHR special submod
   that shares a slot: its whole condition list, partially evaluated for the submod's weapon pairs (an
   `IsEquippedType` that is the same at every pair becomes a constant; keyword tests stay), canonicalised and
   deduplicated, dropping any block a smaller one implies. 49–127 blocks per attack submod.
3. **Clips**: attack slots 1–10 and power slots 1–10, slots past LSdF's count repeating its sequence (an FHR
   directional clip can hand over slot 6+; it lands on LSdF, not on FHR's neutral clip). Annotations added in the
   binary (`hkx_annotate.py`, the same tool as FHR First Person; it re-reads every write):
   - **pace (2026-11-10, curator: "fast and fluid")**: LSdF's own windows open 0.34–0.54 s after the hit (median
     0.54; FHR's ~0.17), and its tiers' last attacks had none, so the combo felt slow and stopped. Now every attack
     opens `MCO_WinOpen`/`MCO_PowerWinOpen` `WIN_AFTER_HIT` = 0.15 s after its last hit (LSdF's own start if that is
     earlier), keeps it open `MIN_WINDOW` = 0.35 s or to LSdF's own end, `MCO_Recovery` 0.1 s after opening;
     `MCO_nextattack` N+1 (the last attack loops to 1), `MCO_nextpowerattack` N+1 (or 1);
     `PIE.@SGVF|MCO_AttackSpeed|0.96` at 0.0 s (MCO's own playback variable; FHR uses 0.85–1.1). The first fast
     build ran 1.2 / 1.1; the curator found it "maybe 20% too fast", so 0.96 / 0.88 (×0.8).
   - power attacks: `PIE.$FHFX` at 0.0 s (FHR's heavy-attack tell; 185 of FHR's 299 neutral power attacks have it,
     88 at 0.0), `MCO_AttackSpeed` 0.88, a window back into the combo `POWER_WIN_AFTER_HIT` = 0.25 s after the last
     hit, next slots 1.
   - All pace numbers are constants at the top of `tools/01`. Sword attack 1: next attack from 0.80 s → 0.41 s clip
     time (0.43 s real at 0.96×).
   - **forward steps (2026-11-10, curator: "no forward momentum or forward power attack")**: a Skyrim clip's root
     motion is not in the `.hkx` but in the behavior project's animation data per clip generator. LSdF's lives in
     SkySA's Nemesis patch (`nemesis_engine/mod/skysa/animationdatasinglefile/defaultmale~1/`: `skysa$N` entries,
     mapped to clips through the `SkySA_clipgenerator_*` names in its `1hm_behavior` patch). Renamed to
     `mco_attackN` the clips play on MCO's generators, so they stood still. `skysa_motion()` reads all 160 clips'
     data and writes it as Animation Motion Revolution keys (`animmotion x y z` every 1/30 s, plus `animrotation`
     where the clip turns; FHR's clips use the same keys). Light attacks share one ramp, 62.5 units forward; power
     attacks 73–146 (sword power 1: 131.7). LSdF parses by line shape: its own `skysa$11` declares 4 translation
     keys and lists 3.
   - LSdF steps **after** the hit (light: 0.26 → 0.66 s), which suited its slow windows. With the window at ~0.41 s
     a chained attack kept 35% of the step. `STEP_DONE_BY_WINDOW` plays each curve early, by (its end − window
     open), never past the moment it starts moving or turning, so both still read 0 at 0 s: light attacks are now
     56% moved at their first hit and 98% at the window (median), power attacks 66% / ≥93% (FHR's attacks are ~50%
     moved at their hit). Sword attack 1: 62.5 units between 0.0 and 0.41 s.
   - **Forward power attack:** there is no separate one to keep. `Attack_MCO.esp` sends `PowerAttackForward 019B25`
     as `attackPowerStartInPlace`, so forward + power plays the standing power attack (slot 1) in every stance; FHR's
     only forward-gated submods (`DirecionalCycleMoveset` 1) are two `Unused` combo-layer folders. With the motion
     back, F1's power attack 1 lunges (sword 131.7 units, FHR's power attack 1 moves 74–136).
   - Same-time PIE tags are fine (FHR fires three at 0.0 s; `PIE_GAP` = 0): the old 0.1 s rule was the odd-offset
     string bug in the postmortem below.
4. **Guard submods**: LSdF's idle/turn/walk/run/equip clips copied unchanged; block, bash, recoil, sneak-attack and
   `bow_`/`tor_` clips are left out (FHR, Dynamic Block Hit and the stagger mods own them).
5. **Priorities**: attacks 1,500,000,100+, guards 1,500,000,000+: above every FHR, Smooth Moveset and Patch Collection
   moveset submod; below Beam Walking Assist (2.11e9), UNDERDOG's states (2.0e9) and RaySense (2.13e9+), which stay
   on top. Our submods are mutually exclusive, so their order does not matter. MO2 position does not matter (no file
   shared with another mod).

## Postmortem: one swing and stop (2026-11-10)

**Symptom (curator, first test):** in F1 with a sword, one swing and the combo stopped.

**Trace (ZenParryTrace 1.3.0, 3P graph events):** every LSdF attack sent `PIE @SGVI|MCO_nextattack|2` at +51 ms,
`preHitFrame` +84, `HitFrame` +252 (attack 1's own timings), then at 0.8 s **only `MCO_PowerWinOpen`**: no
`MCO_WinOpen`, no `nextpowerattack`, no `MCO_WinClose`/`MCO_Recovery`. The next click inside the window therefore
became a power attack (`SBF_PowerAttackStart`, LSdF's `$FHFX`) and the combo ended. FHR's clips in the same session
fired `MCO_WinOpen` and `MCO_PowerWinOpen` together.

**Cause [verified: offsets vs trace, every case]:** `hkx_annotate.py` appended the new annotation strings back to
back. Havok's `hkStringPtr` keeps an "owned" flag in **bit 0 of the pointer**, so a string at an odd offset is read
from one byte earlier (the previous string's NUL): an empty annotation, no event. Every appended tag at an odd offset
failed in game, every one at an even offset fired (attack 1: `nextattack` even ✓, `nextpowerattack`/`WinOpen`/
`WinClose` odd ✗, `PowerWinOpen` even ✓; power attack: `$FHFX`, `nextattack` even ✓, `nextpowerattack`,
`MCO_Recovery` odd ✗). Havok's own files put every string on a 16-byte boundary (FHR's clips: all offsets ≡ 0 mod 16).

**Fix:** `hkx_annotate.Packfile.add` aligns each new string to 16 bytes, and `check_string_alignment` refuses an odd
text offset (called by `annotate()` and by this generator's `convert`). Rebuilt: 740 attack clips, 0 odd offsets.
MCO's own graph gives every attack clip `MCO_InputBuffer` at 0.2 s and `attackStop` 0.1 s before the end (a shared
trigger array in `MCO_Attack.hkx`), so the clips need nothing beyond the window and next-slot tags.

**Same defect elsewhere:** FHR First Person's 1st-person clips (built with the same tool; live copy in Patch
Collection) lose all 378 `$ParryKnockdown` and 168 of 252 `$FHFX` tags — see [`FHRFirstPerson`](FHRFirstPerson.md).

## Install / rerun

1. Have the SSE 1.01 zip in MO2's `downloads/`.
2. `python src/LSdFHighStance/tools/01-build-lsdf-high-stance.py` (default: tools.json `modlistRoot`, profile Ultra).
   It deletes and rewrites `mods/Zenderal - Le Sentiment du Fer High Stance`.
3. `python src/LSdFHighStance/tools/02-verify.py` (exits 1 on any coverage problem), and
   `python src/StanceMovesets/tools/02-verify.py`, which checks all three stances against FHR per weapon pair
   (2026-11-10: 34,216 High cases, 0 uncovered).
4. Ticked in the Ultra profile since 2026-11-10, next to Mid/Low ([`StanceMovesets`](StanceMovesets.md)).

Rerun after **For Honor Reforged** changes (its special submods are read at build time), after an OAR `user.json`
override of an FHR submod's conditions, or after an LSdF update.

## Not done / open

- **Unverified in game.** Built and checked offline only (condition coverage, annotation dump). The one-swing fix
  played in game (curator, 2026-11-10: "the animations now play"); the pace and the forward steps are untested. The
  early step is not matched to the clips' footwork (LSdF's own ramp was not either: one linear ramp for every light
  attack): watch for feet sliding in the windup, and set `STEP_DONE_BY_WINDOW = False` for LSdF's original timing.
- First person is untouched (the list's 1P stance sets and FHR First Person stay).
- NPCs never get it (the stance perk is the player's).
- In High stance, FHR's directional, parry and follow-up attacks play FHR's class clips (needed for their mechanics),
  so the look mixes LSdF neutral combos with FHR directional moves. LSdF has no directional clips; a variant that
  puts FHR's tags on LSdF clips (like FHR First Person) would need parry clips LSdF does not have.
- LSdF's special SkySA states (`SdF_H2H_pwrattack_Left/Right`, `SdF_SpecialAttackPower`: its own dual-wield/fist
  parry moves) are not ported; FHR's parry covers that input.
- Wabbajack: not set up. The mod is LSdF's clips renamed and annotated. **Permissions allow it** (Nexus 50798,
  read 2026-11-10): modification "allowed … so long as you credit me", asset use allowed with credit, conversion
  allowed; uploading the original elsewhere is not. So it can ship (Wabbajack rebuilds it from the SSE download as a
  patch) with Khonraad credited — the config's `author` field and the list's credits. Needs an Include rule.
