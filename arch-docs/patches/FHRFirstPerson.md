# FHRFirstPerson

- **Source:** `src/FHRFirstPerson/tools/` (`01-build-fhr-first-person.py`, `hkx_annotate.py`)
- **Ships:** *(no plugin — generated OAR mod, MO2 mod `Zenderal - FHR First Person`, 1,503 clips / 35 MB, not committed)*
- **FormID block:** _(none)_

## What it does

For Honor Reforged 2.4's directional attacks and parry in **first person**, on the list's own first-person
animations (the SIGMA sets, SigmaJelly katana, JellyFish daggers). Third person is untouched: everything lives
under `_1stperson/animations/OpenAnimationReplacer/Zenderal - FHR First Person/`.

| Input in first person | Plays | FHR tags added |
|---|---|---|
| back + light attack | **a parry move**: one of Enhanced 1stperson Parry Animation's three for the weapon type, at random | `$BackLight` + `$ParrySpell` at 0.10 s: FHR's parry window (not while FHR's player cooldown `5F9` is on, as in FHR) |
| light attack while FHR's parried mark is on you (2 s after an enemy hit lands in the window) | **the riposte**: the same light attack | `$BackLight` at 0.0 s, `$ParryKnockdown` 0.133 s before contact: the hit FHR's perk turns into parry poise damage |
| left / right + light attack (not while parried) | the same light attack | `$LeftLight` / `$RightLight` at 0.10 s (dispels the Directional Combat addon's NPC buffs) |
| left / right + power attack | the submod's own left / right power attack | `$LeftHeavy` / `$RightHeavy` + `$FHFX` at 0.10 s |
| back + power attack | the submod's own back power attack | `$BackHeavy` (guard break) + `$FHFX` at 0.10 s |
| forward + power attack | the submod's own forward power attack | none (FHR's forward is its neutral attack) |

## Why: two separate gaps [verified in files 2026-10-31]

**FHR's mechanics only exist inside its third-person clips.** FHR 2.4 ships them as Payload Interpreter
annotations in its OAR clips (scan of every non-NPC FHR clip): `PIE.$ParrySpell`, `$BackLight` and
`$ParryKnockdown` in the 25 "Backward Light Attack" folders, `$BackHeavy` in back power attacks, `$LeftLight`…
`$RightHeavy` in the side folders. The macros are defined in FHR's
`SKSE/PayloadInterpreter/Config/For Honor In Skyrim.ini` (`$ParrySpell = @CAST|0X80E|For Honor Balance Patch.esp|…`).
Its submods pick direction with `CompareValues` on DMK's graph variable `DirecionalCycleMoveset` (right 3,
back 5, left 7; all 171 folders agree). FHR's own page: "the mechanics will not work with non Reforged
move-sets". The first-person graph plays SIGMA's clips, which carry none of these tags.

**Directional power attacks were collapsed in first person by our own idle patch.**
[`MCODirectionalPowerAttacks`](MCODirectionalPowerAttacks.md) (and Attack_MCO for forward) makes
`PowerAttackLeft/Right/Backward 019B22–24` send `attackPowerStartInPlace` so third person reaches MCO. The
first-person graph (Pandora output `_1stperson/behaviors/1hm_behavior.hkx`, read with hkxconv) still has the
vanilla states — `attackPowerStartLeft` → `AttackPowerLft` → `1HM_AttackPowerLeft.hkx` etc. — but routes
`attackPowerStartInPlace` only to `AttackPowerInPlace` → `1HM_AttackPower.hkx`. So every first-person power
attack played SIGMA's standing one. The idles stay as they are; the fix is on the clip side.

Nexus 172666 (*For Honor Reforged - First Person Addon*, Strife) does this for FHR **1.31 only** (its page:
"will not work with Version 2.0"); its design (Keytrace + DAC + SBF) has no first-person-only trigger, which is
why this patch annotates first-person clips instead.

## Mechanism

**Parry = parry move, then riposte (2026-10-31, v2).** v1 kept the normal swing for back + light, like the Nexus
addon; in game that gave no way to tell whether the input registered. FHR's own parry is one move whose window
opens at 0.10 s and whose hit lands at ~0.45–0.7 s; its perk (`ReforgedParryController 876`) applies `Weapon Parry
Poise Damage 892` only when the player's hit lands carrying `BackLight 88A` (lingers ~1.25 s) **and** the parried
mark `WeaponParryTrigger 82A` / `ShieldParryTrigger 811` (2 s, put on the player by the attacker's
`HitFrameTriggerSpell 803` if its hit landed inside the window `810`/`80F`, a ~0.15 s taper). No first-person
parry swing exists (list scan, Nexus search); the list does carry **Enhanced 1stperson Parry Animation** (Nexus
20374: "3 variation of parrying moves", deflect and push the attack away) as loose `1hm/2hm/2hw_blockhit[a|b].hkx`,
which SIGMA's OAR block sets outrank, so they never played. So:

- **Parry**: one submod (`Parry - Back Light`, priority 1,900,000,000, above every twin) replaces each light-attack
  file with a `_variants_` folder of the weapon type's three parry moves (random), tagged with FHR's window. Its
  clips had **no annotation tracks**; `hkx_annotate.py` adds one. The graph's `attackStop` trigger is timed from the
  clip's **end** (`relativeToEndOfClip`), so the shorter clip still ends the attack; the submod leaves OAR's default
  triggers on.
- **Riposte**: twins of every light-attack submod, conditioned on `82A` or `811`, cast `$BackLight` at the start
  and `$ParryKnockdown` (effect `835`, 0.5 s taper) 0.133 s before contact — the same order as FHR's back-light
  clip, split over two attacks. Side-light twins require *not* parried, so they never compete with it.

**v3 (2026-10-31), from the v2 test's ZenParryTrace log [verified in log]:**

- **Two PIE tags at the same time arrive as one event.** The parry clip carried `$BackLight` and `$ParrySpell`
  both at 0.10 s; the player's event sink got 36 `PIE $BackLight` and not one `$ParrySpell`, so `810` never went on
  and every goblin hit logged `ParryDamageCheck` (hit before the window) — the attacker's `803` did apply
  `82A`/`811`, whose conditions then failed. FHR's own clips stack tags at the same time too. Now every PIE tag in a
  clip is at least `TAG_GAP` = 0.1 s from any other (the generator refuses otherwise): parry `$ParrySpell` 0.10 s
  (FHR's time) + `$BackLight` 0.20 s; power `$…Heavy` 0.10 s + `$FHFX` 0.20 s; riposte `$BackLight` 0.05 s.
  **Corrected 2026-11-10: the time was not the cause.** `hkx_annotate.py` wrote the new strings back to back, and
  Havok's `hkStringPtr` uses bit 0 of the pointer as a flag, so any string at an odd offset is read from one byte
  earlier (an empty tag, no event). `$ParrySpell` came second; moving the tags apart changed which strings landed odd.
  Proven on LSdFHighStance's trace (every odd-offset tag lost, every even one fired; [`LSdFHighStance`](LSdFHighStance.md)
  postmortem). The deployed clips (Patch Collection copy, built before the fix) still lose **all 378 `$ParryKnockdown`
  and 168 of 252 `$FHFX`** tags — the likely cause of the "short parry knockdown" left open below. The tool now aligns
  every string to 16 bytes and refuses odd offsets; **rerun `tools/01` and redeploy into Patch Collection.** The 0.1 s
  gap can stay (harmless).
- **An attack after a parry replayed the parry.** The second attack (~0.2 s after the first ended) logged
  `$BackLight` 84 ms in, i.e. the parry submod matched again; the parry clips carry no root motion
  (no `hkaDefaultAnimatedReferenceFrame`), so the v2 direction test (`DMK == 5`, or `DMK == 0` and moving back)
  passed on DMK's value or on S still held — the log could not tell which. v3: direction = **Keytrace.esp's
  held-key effect** (PaulMix's dTry Key Utils extend keeps `BackwardMGEF 803` etc. on the player only while the key
  is held), pure (no perpendicular key), **or** moving that way with DMK reading that direction or 0; and the parry
  is off while parried (`82A`/`811`), so after a successful parry the next attack is the riposte even with S held.
  ZenParryTrace 1.1.0 logs every direction signal (`DIR`) to settle which one holds.

**v4 (2026-10-31), from the v3 test's ZenParryTrace 1.1.0 log [verified in log / OAR source]:**

- v3's fixes held: `$ParrySpell` fired (8), the window opened (7), one parry succeeded (`WeaponParryTrigger` on
  after a Highwayman's axe landed inside it). **DMK is not sticky** — `DirecionalCycleMoveset` reads 5 in *both*
  graphs while S is held and 0 on release — and **PaulMix's Keytrace effects never appear** (`keytrace=....`
  throughout; its `KD*` bools stay false too), so v3's Keytrace branch is dead and movement + DMK carries it.
- **The parry loop is OAR's echo.** The attack after the successful parry started with DMK 0, not moving, parried —
  and still played the parry clip. An attack started while the last one still blends out restarts ("echoes") the
  same clip generator; OAR re-picks only if the submod *playing* has `replaceOnEcho`, default false
  (`ActiveClip::OnLoopOrEcho` → `ShouldReplaceOnEcho`, `ReplacerMods.cpp` default; an original with no replacement
  playing re-picks if any candidate has it, `TestReplaceOnEcho`). v4: `replaceOnEcho` on the parry, every twin and
  vanilla twin, **and** a `user.json` in this mod for each of the 96 twinned SIGMA/JellyFish submods = their config
  verbatim + `replaceOnEcho` (OAR's user.json replaces config.json — RaySensePriority's pattern; one checked: only
  that key differs). Without the overrides a quick S + attack right after a SIGMA swing would stay SIGMA's.
- **Side attacks set FHR's markers but no strip was seen.** `$LeftLight`/`$RightLight` applied `Left Light 880` /
  `Right Light 881` (2 s) on the player each time, and the player's hits landed while they were on. The strip is
  FHR's: perk `ReforgedEnemyDirectionalDispels 82C` (player via start-game quest `818` → ability `819`) has
  `ApplyCombatHitSpell` entries `880 → 82A`, `881 → 829`, `882 → 827`, `883 → 826` at priority 0–4. The engine
  applies **one** combat hit spell per hit (see `Prophecy.md`), and FHR's own `ReforgedParryController 876` adds
  two **unconditional priority-8** entries (`605 BlackPriorTriggerSpell`, `803 HitFrameTriggerSpell`) — likely the
  winners, which would also starve the riposte's `892` (priority 4), in third person as well. 1.1.0 could not see a
  hit spell landing on an enemy (it logged only applications involving the player); 1.2.0 logs everything applied to
  an actor within 1.5 s of the player hitting it. **Trace 1.3.0 test (2026-10-31, 13 1P power attacks + a few 3P)
  settled it:**
  - **Light strips work** on a clean, unblocked light hit (`155658`: right light took the enemy's right-light arrow
    off 6 ms after landing). They fail on blocked hits by FHR's design (the block variant also needs `8BC`).
  - **The heavy marker never goes up in first person.** Zero `$LeftHeavy`/`$RightHeavy`/`$FHFX` from the player in
    1P. The player's 1P power-attack clip generators (`AttackPowerInPlace_Player` → `1HM/2HM/2HW_AttackPower_Intro`/main,
    sneak too) carry `flags 16` = `FLAG_DONT_CONVERT_ANNOTATIONS_TO_TRIGGERS` (value read from `SkyrimSE.exe`'s Havok
    enum table), so no annotation in whatever clip plays there becomes an event — our tags are inert. The player's
    1P light generators (`1HM_1stPAttackRight/Left`) have 0, which is why light tags fire. 2HM/2HW power intros also
    start at 0.333 s. Flipping the flag is not safe on its own: the power clips carry 700+ `HitFrame`/`WeaponSwing`/
    `attackStop`/`Collision_*` annotations each, which would double the graph's own triggers.
  - **Every 1P power attack starts as a light attack** (`SBF_NormalAttackStart` + the side light tag, then
    `SBF_PowerAttackStart` ~300 ms later, a hold), so the side *light* marker (`880`/`881`, ~1.4–2 s) is on at every
    side power-attack hit. That is the usable heavy signal: light marker + `IsPowerAttacking`.
  - **One combat hit spell per hit, confirmed** (the winning spell's MGEFs apply ~1 ms before `TESHitEvent`). Side
    light hits: Directional's light dispel won (2/2) over FHR's `803`. Power-attack hits on humanoids: EGO's
    `XionPowerStagger 001DBD` (priority 0, `IsPowerAttacking` + target `01E715` + weapon keywords) won 7/7, so even
    with the marker a heavy dispel (priority 0/1) would lose to it. Whether the engine orders entries by priority
    across perks or by perk order is not settled (both fit EGO → Directional → FHR).
  - 3P: FHR's own side power attacks produced `$FHFX` but no `$LeftHeavy` in this log either (not investigated).

  Proposed data-only fix (not built): override `82C` so the heavy entries accept `882`/`883` **or** side light marker
  + power attacking, every entry also needs the enemy to carry the matching arrow (so it only takes the slot when it
  strips; ordinary side lights get FHR's parry check `803` back), light entries need not power attacking (FHR's
  rule); and split EGO's `XionPowerStagger` entry into mutually exclusive conjunctive entries that fail exactly in a
  strip case (independent of the ordering question). **Side lights have no visible side** (curator, same day):
  SIGMA's 1P light set is the ordinary chain (`1hm_attackright`, `attackleft` + the two diagonals, picked by combo
  order), and the Light twins replay the same clip (`names = {f: f for f in LIGHT}`), only adding the tag chosen by
  movement — against the rule that an input needs its own visible animation. Candidate: a Left Light twin plays the
  submod's left-starting swing in every light slot, Right the right-starting one (which file starts on which side is
  unverified: decoding needs PyNifly, whose path is gone, or a look in game). The curator chose the strip fix only
  (lights keep their swing): **built 2026-10-31 as [`FHRDirectionalStripFix`](FHRDirectionalStripFix.md)**, data
  only. The earlier idea (an SKSE plugin applying FHR's player-side hit spells on `TESHitEvent`) was dropped.
- **Enemies knocked down by a parry got straight back up** (user report). FHR's `Stagger/Parry Knockdown` submod
  replaces Modern Stagger Lock's stagger with stuxjr's large staggers (2.17 s, `MSL_*StaggerTriggerOpen` at 0.2 s)
  when the staggering actor's combat target has `BackLight 88A` (or `894`), or the actor has `835`; not with
  `86F`/`8B0`. **Cause found (2026-10-31) [upstream source + session log]: Break Stagger** (Nexus 178745, 1.0.2,
  no `Viny Mods/Break Stagger/Settings.json` anywhere → defaults from `include/Settings.h`: NPC base 2000 ms,
  −350 ms per stagger from the 1st, count reset after 5000 ms, 3000 ms immunity). On every `staggerStart` /
  `SBF_StaggerStart` it counts the actor's staggers and, `2000 − 350 × (count − 1)` ms later, sends `staggerStop`
  if the actor is still staggered (`src/Events.cpp` ~430–556): 1st stagger 2.00 s, 2nd 1.65, 3rd 1.30, 4th 0.95,
  5th 0.60, 6th 0.25, 7th → 0 s + 3 s immunity. FHR's knockdown (a 2.17 s stagger replacement) is cut by the
  same timer, so mid-fight, a few staggers in, it ends in a fraction of a second. Its log for the 11:35–11:40
  session shows the 7th-stagger threshold reached three times (`0004C630`/`0004C631`). Not first-person
  specific. **Fixed (curator's choice, same day): Break Stagger off for NPCs** — `Zenderal - Settings` ships
  `Viny Mods/Break Stagger/Settings.json` with `npc.enabled = false` (see `modlist/mod-gotchas.md`). Unverified in game.

**Intro clips are not touched.** Two-handers' first-person attack starts in an intro state and switches to the main
clip on the intro's end-timed `attackRelease`, so replacing or tagging both would play the parry (or cast
everything) twice. One-handers' intros sit in `1HM_AttackRightRoot_Player_OLD`, unreachable: the branch is
picked by `startStateId` bound to `iIsPlayer`.

**Twins.** For every enabled first-person OAR submod (MO2 profile `Ultra`, VFS-resolved, `user.json` over
`config.json`, disabled ones skipped) that replaces one of the player's light-attack clips (the 11 non-locomotion,
non-intro clips of the graph's `AttackRight_State`/`AttackLeft_State`) or has a left/right/back/forward power
attack, the generator writes one twin per kind (riposte, left/right light, four power directions):

- same config fields (blend times, `triggersFromAnnotationsOnly`, …), same conditions **plus** the direction
  (or the parried mark, for the riposte), priority = original + **1,000,000,000**. Every first-person original
  sits below that (highest: SigmaJelly katana 800000004), so the twins keep the originals' order and beat all of
  them: in a given direction the twin of whichever submod would have played wins. Asserted per submod.
- power twins replace the standing file (`1hm_attackpower`, `1hm_sneakattackpower`, `2hm_attackpower`,
  `2hw_attackpower`) with that submod's directional clip; `_variants_` folders are copied whole and their
  `replacementAnimDatas` entries re-pointed.
- 7 **Vanilla** twins (riposte, two side lights, four power directions) at priority exactly 1,000,000,000 carry the load order's winning loose/BSA clip (all from
  `Skyrim - Animations.bsa` today), for when no OAR submod would have played. DAR sets (*Stances based
  animations for 1st person combat*) are not twinned; in a held direction the vanilla twin beats them. SIGMA
  covers every weapon type they do, so this should not show.

**Direction** (v3, see above) = Keytrace's held-key effect for that direction alone, **or** OAR
`IsMovementDirection` (1 forward / 2 right / 3 back / 4 left, from OAR's `Conditions.cpp`) with
`DirecionalCycleMoveset` == N (FHR's own test: right 3, back 5, left 7) or 0. v1/v2 used DMK alone or, at 0,
movement alone. BDI injects DMK's variable into every
project under `Actors\` (source: `DataHandler::get_subpaths` is a path-prefix match), first person included,
but whether DMK *writes* the first-person graph is unverified — the movement fallback covers it. Forward = DMK
1 is inferred from FHR's clockwise 3/5/7; if wrong, forward power attacks just stay standing.

**Annotations** are added by `hkx_annotate.py` straight into the binary packfile (hk_2010.2.0-r1, 64-bit): the
annotation track's array is copied to the end of `__data__` with the new entries, its pointer fixup moved, new
string fixups added, fixup tables rewritten. Nothing else changes — an hkxconv/HKX2 XML round trip would rewrite
every float as text. Check: 52 output clips (40 random, 6 parry, 6 riposte) converted with hkxconv are
identical to their source apart from the added tags (v2, 2026-10-31).

**Timings** are FHR's: in all 171 sampled FHR clips every directional tag and `$ParrySpell` sit at 0.10 s;
`$ParryKnockdown` most often 0.133 s before `HitFrame`. Here "contact" = the first `HitFrame` or
`Collision_Add*` (Precision; SIGMA has no `HitFrame`), else first `weaponSwing` + 0.1 s, else 0.3 s (48
annotation-less JellyFish/SIGMA sneak clips); never before 0.15 s. Result: 0.15–1.53 s (the late ones are
slow warhammer sneak attacks).

**Left out:** FHR's `$StaggerKnockDown` (its back-power clips carry it, but 2.4's config comments the macro
out — inert), FHR's followups (parry/guard-break followup attacks need their own clips), unarmed and
dual-wield left-hand attacks. The generator refuses to emit a tag no Payload Interpreter config defines.

## Install / regenerate

```
python src/FHRFirstPerson/tools/01-build-fhr-first-person.py [<modlist root>] [<profile>]
```

Writes `mods/Zenderal - FHR First Person` (deletes and rebuilds it). Enable it in MO2; its position does not
matter (no file is shared with another mod; OAR priorities decide). **Rerun after any first-person animation
mod, FHR or OAR config change** — twins copy the submods' conditions and clips at generation time.

## Status

**2026-10-31, first test (v1):** directional power attacks work in game. The parry did not seem to fire, and with
no animation of its own there was no way to see the input. Ruled out from files: FHR 2.4 also casts `$ParrySpell`
once at 0.10 s (all 25 back-light clips), and the player does get the parry perk `876` (quest `806`'s player-alias
ability `807`, since SPID never targets the player). **v2 (same day):** parry move + riposte (above): the move
played in game, but `$ParrySpell` never fired and attacking after a parry replayed it. **v3 (same day):** spaced
tags, Keytrace direction, riposte over parry (above): parry window verified in log, one parry succeeded, but
attacks after a parry still replayed it. **v4 (same day):** `replaceOnEcho` everywhere incl. 96 `user.json`
overrides; unverified in game. Side-attack strip and the short knockdown are open (above). [`ZenParryTrace`](ZenParryTrace.md)
1.1.0 logs each link plus the direction signals.

Test v2: S + light attack shows a parry move. Time it so the enemy's swing lands just after you start it (the
window is ~0.10–0.25 s in). If it counted, attack again without S within 2 s: that riposte should take a chunk of
poise (knockdown only if it empties).

Original test plan (built and deployed 2026-10-31): Test, sword drawn in first person:
strafe left + power attack → a sideways swing; back + power attack → the back power attack; back + light
attack into an enemy swing → FHR's parry (sound, slowdown, poise damage). OAR's in-game menu (animation log)
shows which twin played. If nothing directional happens while moving, DMK and the fallback both failed — check
the log for `Zenderal - FHR First Person` submods being evaluated.
