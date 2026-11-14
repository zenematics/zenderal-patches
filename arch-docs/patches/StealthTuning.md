# StealthTuning

- **Source:** `src/StealthTuning/`
- **Ships:** `Zenderal - Stealth Tuning.esp` (ESL; masters `Skyrim.esm`, `Update.esm`, FS, `Enderal SE - Gameplay Overhaul.esp`)
- **FormID block:** none (7 GMST overrides)
- **Replaces:** `Enderal SE - Stealth Overhaul.esp` (Nexus Enderal SE mod 12), which must be **disabled**
- **Status:** built 2026-11-12 and copied into `Zenderal - Patch Collection` (no standalone MO2 mod). **Unverified in game.**

## The report

Player feedback, 2026-11-01: sneaking is "almost impossible" early on. The curator wants it hard but
realistic.

A tester's report (2026-11-12, before this patch): up to about level 8 every bandit or beast noticed
them up close, even with everything stacked: a Fortify Sneak ring and amulet, the Swashbuckler set,
the Nightwalker trait, Shadow of the Wind maxed, Kata's Mantra of Concealment (+10 Sneak, 300 s) and a
Prophecy +10 Sneak point. Nights were "unplayable" without EGO's Night Eye spell (`XionSpellNightEye
000875`, learnt from book `000877`, costs Mana). From level 9, Prophecy's Nightblade one-shot
everything. All of that stacking goes into the skill side of the formula: Fortify Sneak effects raise
the Sneak skill, and Nightwalker and Espionage use `ModDetectionSneakSkill`. Neither touches the light
or footstep terms, which are at full strength up close. So the report points at EGO's light and
sound weights, not at the skill gap.

## How detection works (what the settings feed)

Each NPC keeps scoring the player **[upstream: UESP Skyrim:Sneak; `SkyrimSE.exe` is DRM-packed, so not
read from the engine]**:

`fSneakBaseValue + (sound + sight + NPC alertness) × (1 − d / fSneakMaxDistance)^exponent + (NPC skill − player Sneak)`

Higher means easier to detect. The distance falloff does not reach the base value or the skill gap.

- **Sight** needs line of sight and the vision cone. It uses the engine's light level at the player
  (placed lights, sun/moon, weather; a torch counts ×1.6 at night, `fTorchLightLevelNight`; spell glow
  in the hands counts). Screen darkness from ENB or Bottled Shaders does not count. UESP does not
  document the light term; `fSneakLightMult` (standing), `fSneakLightMoveMult`, `fSneakLightRunMult`
  and `fSneakLightExteriorMult` feed it.
- **Sound**: footsteps = `fSneakEquippedWeightBase + fSneakEquippedWeightMult × armor weight`
  (weapons do not count), ×2 running (`fSneakRunningMult`; sneak-running counts as running), zero
  standing still; non-dagger attacks and spells add `fSneakActionMult × sound level`. Out of line of
  sight sound counts `fSneakSoundLosMult`.
- **Searching**: once alerted, an NPC drains the player's stealth points (`fCombatStealthPoint*`).

## What was found

Live scan of the `Ultra` profile (`tools/00-scan-stealth-gmsts.py`) **[verified]**:

| Setting | Enderal | EGO | Effect of EGO |
|---|---|---|---|
| `fSneakLightMult` / `fSneakLightExteriorMult` | 0.3 / 0.5 | 1.0 / 1.0 | light ×3.3 indoors, about ×6.7 outdoors (if the exterior multiplier stacks as named) |
| `fSneakEquippedWeightBase` / `…Mult` (new in EGO) | engine 12 / 0.5 | 5 / 1 | with `fSneakSoundsMult` 1.2: cloth half as loud, leather about equal, an iron set (39) +68% |
| `fSneakDistanceAttenuationExponent` (new in EGO) | engine 2 | 3 | range protects more (10 m: about 28% less noticeable) |
| `fSneakBaseValue` | −19 | −13 | +6 on every check |
| `fCombatStealthPointDrainMult` | 3 | 12 | a search finds the player 4× faster |
| `fCombatStealthPointRegenAttackedWaitTime` / `…DetectedEventWaitTime` | 15 / 10 s | 120 / 60 s | searches last far longer |
| Player's starting Sneak (`Player 000007`) | 15 | 5 | −10 skill gap at any distance |

- `Enderal SE - Stealth Overhaul.esp` loads after EGO and re-sets 17 of these to EGO's values. It is
  a full plugin, and it adds **new** GMSTs (`000800`–`000804`) under the same names as EGO's new ones:
  the engine finds a setting by EditorID, so that still overrides. Its only different value is
  `fSneakSleepBonus` −0.15 (EGO −0.2, Enderal SE - Bug Fixes −0.1).
- NPC perception is unchanged: EGO changes the Sneak skill of only 9 NPCs, none of them common enemies.
- A Dark Warrior's Tale's `_CDW_IncreasedDetection` (light and movement ×10) sits on one intro NPC
  only, not the player.

## What the patch does

Keeps EGO's armor-noise and distance model, keeps light the biggest factor but trims its weight, and
trims the flat penalty and the lock-on:

| Setting | Enderal | EGO | Patch |
|---|---|---|---|
| `fSneakBaseValue` | −19 | −13 | **−16** |
| `fSneakLightMult` | 0.3 | 1.0 | **0.6** (indoors 2× Enderal) |
| `fSneakLightExteriorMult` | 0.5 | 1.0 | **0.6** (outdoors 0.6 × 0.6 = 0.36, Enderal 0.15) |
| `fCombatStealthPointDrainMult` | 3 | 12 | **6** |
| `fCombatStealthPointRegenAttackedWaitTime` | 15 | 120 | **60** |
| `fCombatStealthPointRegenDetectedEventWaitTime` | 10 | 60 | **30** |
| `fSneakSleepBonus` | 0 | −0.2 | −0.2 (EGO's, forwarded) |

The two light settings were added on 2026-11-13, before the first test, after the tester's report
above: the base value alone (−3) cannot help a player whose problem is the light term up close. 0.6 is
a judgment call between Enderal and EGO, not a measurement. Footstep noise keeps EGO's values.

Each record is EGO's GMST copied from `reference/mods/EGO/GameSettings/` with only `Data` changed.
The starting Sneak skill is left alone: changing it means overriding EGO's Player record, which
carries its 42 perks. The optional `EGO SE - Higher Starting Skills.esp` (all skills 10) does that
wholesale and stays disabled.

## Install

- Ships inside `Zenderal - Patch Collection`; tick `Zenderal - Stealth Tuning.esp` in MO2's plugin
  list. Rebuilds go into that folder.
- **Untick MO2 mod `Stealth Overhaul (All Languages)`** (`Enderal SE - Stealth Overhaul.esp`): if it
  loaded later it would revert three of the five values.
- Masters EGO, so it loads after it.
- Goes out with the next Patch Collection upload.

## Regenerating

```
python -I src/StealthTuning/tools/00-scan-stealth-gmsts.py    # live load order -> tools/gmsts.json
python -I src/StealthTuning/tools/01-build-stealth-gmsts.py
```

`01` refuses to run if a setting is touched by a plugin outside its known list (Skyrim.esm, Bug Fixes,
EGO, Stealth Overhaul, this patch), if EGO's value is no longer the one the patch was tuned against,
or if a plugin loads after this patch with that setting. Rerun both after EGO updates or when a mod
that changes stealth settings is enabled.

## Open questions

- **Whether 0.6 light is right.** Test: the tester's low-level setup (and a bare Sneak-5 character in
  leather) sneak-walking up behind unalerted bandits and beasts, by day and by night, indoors and out,
  with the Detection Meter. Daylight in the open should still give the player away. If light still
  dominates or stealth becomes trivial, read `player.getlightlevel` in an Ark street at noon and
  midnight, a lit dungeon room and a dark corner, with and without Quick Light, before changing
  numbers again; a read-only detection trace is the next step after that.
- Whether CS Light's Light Placer lights (small glows on clutter, mushrooms, magic objects) raise the
  engine's light level at the player. Same light-level readings.
- Night vision for non-mages (tester's request): only EGO's Night Eye spell exists. A Night Eye power
  on the Nightwalker trait or a Prophecy Shadow talent is the curator's call; not in this patch.
