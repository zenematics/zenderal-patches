# PowerAttackPitch

- **Source:** `src/PowerAttackPitch/Pandora_Engine/mod/zpapitch/` (`info.xml`, `patches/0_master.xml`, **generated**);
  `tools/01-build-patch.py` (reads Precision's installed Nemesis files, asserts the mechanism, writes the patch,
  self-checks it).
- **Ships:** *(no plugin)* Pandora-native patch `zpapitch`, MO2 mod `Zenderal - Power Attack Pitch` (manifest release
  of the same name). **Needs a Pandora run with `zpapitch` ticked.**
- **FormID block:** _(none)_

## What it does

Power attacks lean the upper body toward the target the way light attacks already do, so they reach short enemies
(goblins, Arps, wolves, skeevers, spiders) instead of swinging at standing height over them. This matters most when
locked on with TDM (curator report 2026-11-11: "lower height enemies often aren't hit by my attacks when locked on").

## How "aiming down" works in this list [read in source 2026-11-11]

Two mods, one graph variable:

1. **TDM 2.3.1 sets the player's pitch.** During target lock, `DirectionalMovementHandler::LookAtTarget` sets
   `playerCharacter->data.angle.x` to the pitch from the player's torso point to the target point (line ~2856 of
   ersh1/TrueDirectionalMovement master, pushed 2026-09-01 = the installed Nexus file). Both points are the race's
   BodyPartData **torso part's VATS target node** (`GetTorsoPos`; `GetTargetPoints` falls back to the torso part
   because `uReticleAnchor` defaults to 0 = Body and the list's MCM ini does not change it). A `.toml` in
   `SKSE/Plugins/TrueDirectionalMovement/` overrides the target bones per BodyPartData (base file: dragons, giants,
   centurions…; `TDM Target Fix - BristlebacksInEnderal`: `Boar_Chest01`).
2. **Precision 2.0.6 bends the spine by it.** Every frame `PlayerCharacter_ModifyAnimationUpdateData` writes
   `Collision_PitchMult = -deg(angle.x)` (NPCs: their torso to their combat target's torso, only while attacking;
   `Hooks.cpp` 59-103). Precision's Nemesis patch `colis` (in the list's Pandora `0_master`) twists bones 24-26 about
   the model X axis by that many degrees (`Collision_Pitch_Twist_Mod`, additive, LINEAR); in XPMSE's skeleton those
   are `NPC Spine [Spn0]`, `Spine1`, `Spine2`. The twist sits in `Weap_Readied_Lean_Blend`, weighted by
   `Collision_Weight`, which ramps in at 3/s while one of Precision's `Pitch_Adjustment_*_Start_EDM`s is active and out
   after `attackStop`. Those modifiers live in `Precision_Mods`, appended to `RootModifierList #2517` (always active).

**TDM needs no change.** The torso VATS targets of the short races are real torso bones, so the lean is already
measured chest to chest (Precision's own NPC rule):

| BodyPartData | Torso VATS target | Used by |
|---|---|---|
| `FalmerBodyPartData 05DDA2` | `NPC Spine1` | Arps, Goblins' `ZEN_GoblinRace` |
| `DogBodyPartData 04FBF5` | `Canine_Spine3` | wolves, dogs |
| `SkeeverBodyPartData 0264EF` | `SpineUpperSpine` | skeevers |
| `FrostbiteSpiderPartData 017929` | `Tail1` | spiders |
| `ChaurusBodyPartData 059060` | `Spine[Spn1]` | pus beetles |
| `DefaultBodyPartData 00001D` | `NPC Spine2 [Spn2]` | humans, the player |

## Why power attacks missed

Precision ramps the weight in only on `attackStart`, `attackStartLeftHand`, `attackStartDualWield`,
`attackStartSprint`, `attackStartSprintLeftHand`, `AttackStartH2HRight/Left`, `blockStart`, `bashStart` (and
`BeginCastLeft/Right`). None of the 23 power-attack start events is among them, so a power attack started on its own
(One Click Power Attack's key, or any power attack not preceded by a light attack still in its ramp) played with
weight 0: no lean.

## The patch

27 new objects, nothing of Precision's referenced or changed: one `hkbEventDrivenModifier` per power-attack start
event (activate = that event, deactivate = `attackStop`, as Precision's own), all running one copy of Precision's
ramp-in expression `Collision_Weight = (1 * clamp((Collision_Weight +3*TimeDelta), 0, 1))`, gathered in
`ZP_PowerPitch_Mods` and appended to `#2517/modifiers`. Precision's `Pitch_Adjustment_Stop_EDM` (activate on
`attackStop`) ramps the weight back out, exactly as after a light attack. Events are written `$eventID[name]$`.

`tools/01-build-patch.py` asserts: the vanilla power-attack events (every event name starting `attackPower`, from the
vanilla list in Precision's `#0106`) equal `POWER_EVENTS`; Precision's `Pitch_Adjustment_Melee_Start_EDM` still runs
`attackStart` → `attackStop` through one expression modifier (copied verbatim); no power-attack event already starts
Precision's ramp; `#2517` is still `RootModifierList` holding `Precision_Mods`; the output is well-formed, its
references are closed, and every new object has exactly the fields, in order, of Precision's objects of the same
class. The live Pandora `0_master` (2026-11-10 build) has exactly these 23 power-attack events; no list mod adds one.

## Known gaps / open

- **Interrupted power attacks.** A power attack cut off without `attackStop` (stagger, attack-cancel dodge) leaves its
  modifier active, so the weight stays 1 until the next `attackStop` and the weapon-readied upper body follows the
  player's pitch meanwhile. Precision's light attacks have the same exposure. If the body stays bent after a
  dodge-cancelled power attack, this is why.
- **The ramp takes 0.33 s** to full weight (Precision's rate). A power attack's hit usually lands later, but a very
  fast one may hit before the full lean.
- **NPC power attacks lean too** (toward their combat target's torso), as their light attacks already do.
- First person untouched (TDM's target lock is third person; Precision's `colis` has no first-person graph).
- How much lean is *enough* is Precision's 1:1 rule; skeevers right at the feet need ~35-40°, which they get at
  melee range (torso 105 → 20 at 120 units) but only once the ramp is full. **Not enough in practice:** a two-hander
  still missed rats and spiders (player report 2026-11-12), so weapon swings also get capsules hanging under the
  blade: [`PrecisionFork`](PrecisionFork.md) patch `0004`. The lean stays for the look and for mid-height targets.
- **Unverified in game.** Pandora not yet rerun with `zpapitch` (2026-11-11).

## Install / regenerate

Tick `Zenderal - Power Attack Pitch` in MO2 (ticked in Ultra 2026-11-11), run Pandora with *Zenderal - Power Attack
Pitch* ticked, then (as after every Pandora run) move the creature behaviors from `overwrite` into `Pandora Output -
Zenderal`. Check it built: the `0_master.hkx` in Pandora Output contains `ZP_PowerPitch_Mods`. Rerun
`python src/PowerAttackPitch/tools/01-build-patch.py` after a Precision update (it fails loudly if the mechanism
moved), redeploy, rerun Pandora.

**In-game test:** lock onto a wolf, skeever or goblin and power attack with One Click Power Attack's key (Mouse 4 /
RT): the upper body should tip toward it as it does on a light attack, and the hit should land.
