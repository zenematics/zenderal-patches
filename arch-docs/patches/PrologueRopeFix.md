# PrologueRopeFix

**Ships:** recompiled `Scripts/_00E_MQP02_RopeSC.pex` (+ source), script-only. The live copy is in
`Zenderal - Patch Collection`. **Status:** built and deployed 2026-11-13; compiles clean, same 2
properties as base Enderal's script (`MQP02`, `MQP02_SC4_VeiledWomanAppears`). **Unverified in game.
The cause of the freeze is not known yet** — this is a watchdog plus a trace, like
[`BlackLightWakeUpFix`](BlackLightWakeUpFix.md).

## The report

Realite33 (Discord, 2026-11-13): *"I have a bug for 'find a rope' quest in the beginning. In
interaction with rope my character freezing."*

## How the rope works (base Enderal 2.1.4.4)

- Quest `MQP02 003158` (*A New Life*, the prologue on the ship, before character creation),
  objective 10 *"Find a rope"*. Alias 20 `Rope` = ref `12E0AE` in cell `MQP02StartShip 046ECC`,
  base activator `_00E_MQP02_Ropes 12E0AD`: an invisible `Enderal\Marker\SphericalCollision.nif`
  named "Rope", script `_00E_MQP02_RopeSC`.
- `OnActivate`: only if scene `MQP02_SC4_VeiledWomanAppears 07BBCF` action 33 (Sirius's forcegreet
  `0B6E32`, phase 1) is complete, `MQP02.SetActivationRopeBool()` sets `bRopeActivated`. Before
  that, activating the rope does nothing (no freeze).
- Scene phases (completion conditions):

  | Phase | Completes when | What happens |
  |---|---|---|
  | 0 | timer 1.5 s | |
  | 1 | stage 65 | Sirius forcegreets (action 33) |
  | 2 | `bRopeActivated` **and** Sirius < 250 from `07FAAF` | on start: objective 10 shown; **on completion: `PlayerAIWalk(False)`** (player AI-driven, movement/fight/activate off, look on) |
  | 3 | (Sirius sitting **or** player package `MQP02_SC4_PlayerAIWalkToCrate 07B8F6` done) **and** 7 s timer | player walks to `MQP02_SC4_PlayerWalkToMarker 07BB5A`, radius 8; Veiled Woman enabled |
  | 4 | 1 s timer + Sirius's topic `07B833` | |
  | 5 | stage 72 (`TIF__0007B86C`) | `OpenDoorAndStartMusic()`: `PlayerAIWalk(True)` (look off too) |
  | 6–8 | topic action 18 | Veiled Woman / Sirius lines |
  | 9 | stage 75 (`TIF__0007B85D`) | stage 75 fragment = `LevitateAndCrashPlayer()`: `SplineTranslateTo` the player up to Z 90 at 9 units/s, then `bIsLevitating` |
  | 10 | `bIsLevitating` | |
  | 11 | `bTimeToScream` | the player alias's `_00E_MQP02_PlayerKnockOutScript.OnTranslationAlmostComplete` → `DashPlayerTowardsWall()` (another `SplineTranslateTo`, sets `bTimeToScream`) → on its near-completion `KnockOutPlayer()` → stage 80 |
  | 12 | stage 80 | char-gen follows |

So from the moment the rope is accepted the player has no control until the knockout. Two steps
can wait forever: the AI travel to a radius-8 marker, and the levitation chain, which advances
**only** on `OnTranslationAlmostComplete` — a translation that is blocked never sends it.

## What the list does to it

Nothing in the data. Binary scan of all 478 plugins in Ultra (2026-11-13): the ship cell and every
ref in it, the rope ref/activator, `MQP02`, the scene, the 7 packages it runs, its 8 topics and the
two stage-setting infos are defined only by `Skyrim.esm` (FS overrides one unrelated info `07B875`;
Malphas' Blessing overrides Sirius's NPC `077407`: face, worn armor, head parts only). Nothing
lists `12E0AD`/`12E0AE` (Immersive Interactions' perk picks activators by FormList; the rope is in
none). No mod ships `_00E_MQP02_*.pex` loose. SkyParkour's key is preset 0 (jump), not activate.
Skip The Prologue is not enabled in Ultra (and skips MQP02 entirely when it is).

**Runtime suspects, not proven:** Improved Camera 2.0's BodyBumper stretches the player's
controller hull 45 units forward at every height ([`ImprovedCameraSheatheFix`](ImprovedCameraSheatheFix.md),
the stairs report of the same day; set to 0 in `Zen.json` on 2026-11-13, not shipped yet), which can
block both an AI walk in the cramped hold and a `SplineTranslateTo`; True Directional Movement's
handling of an AI-driven player. Note the pattern: [`BlackLightWakeUpFix`](BlackLightWakeUpFix.md)
is also an AI-driven player package that never arrived.

## The fix

SureAI's `OnActivate` unchanged; when the rope is accepted it starts a 1 s watchdog on the rope ref
(non-property variables only):

- logs the state on every stage change and every 5 s: stage, scene playing, objective 10, scene
  actions 2/4/18/42, `bIsLevitating`/`bTimeToScream`, player position and distance to the crate
  marker, Sirius's sit state; a `STALL` line after 60 s on one stage; an activation before action 33
  is logged too;
- **walk:** objective 10 completed, stage < 72, player > 32 units from `07BB5A` for 20 s →
  `MoveTo` the marker (the walk's own destination);
- **levitation:** stage 75, `bIsLevitating` and no dash after 25 s (the rise takes ~9 s) →
  `StopTranslation()` + SureAI's `DashPlayerTowardsWall()`; the alias's own handler then carries on
  (its state is still 0, so it dashes once more and knocks out — harmless);
- **knockout:** stage 75 and `bTimeToScream` with no stage 80 after 10 s → `StopTranslation()` +
  SureAI's `KnockOutPlayer()`;
- stops at stage 80.

Stalls before stage 75 other than the walk are logged, not forced: setting stages 72/75 by hand
would skip the scene's dialogue phases, and the log will say which one hangs.

## Testing / next step

Log lines start with `[ZP MQP02 rope]` in `My Games\Skyrim Special Edition\Logs\Script\Papyrus.0.log`
(OneDrive variant possible; Papyrus logging is on in the shipped `Enderal.ini`). A new game up to
the rope covers it. The reporter's own Papyrus log (and a crash log, if "freezing" meant the game
hung) would tell the stalled phase without a rerun.

Console escape for a stuck player today (before this fix): `setstage MQP02 80`. Stage 80's fragment
is `StartSC05()` (moves the player to the execution scene, unmutes the ambience it would have muted);
it skips only the knockout's sounds/fade and `PrecacheCharGenClear()`. Then `SetPlayerAIDriven 0` /
`EnablePlayerControls` if the player is still held after char-gen.
