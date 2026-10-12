Zenderal - Brawl Fixes
======================

Two recompiled scripts. No plugin, no records, no ESP.

  Scripts\_00E_DGIntimidateAliasScript.pex    (+ Scripts\Source\ .psc)
  Scripts\_00E_DGIntimidatePlayerScript.pex   (+ Scripts\Source\ .psc)

  Base: SureAI's own source, verbatim, from ScriptsEnderal.zip.
  Change: one guard added to each, marked "; ZP".

Credit: SureAI, for both scripts.


HOW AN ENDERAL BRAWL IS ACTUALLY WON
------------------------------------
This is the part everyone gets wrong, including three earlier attempts at this
patch. The win condition is not in a script at all. It is an AI package on the
brawl quest's opponent alias, DGForceGreetAfterBleedoutPackage (108B54), which
runs only when ALL of these hold:

    GetStageDone(DGIntimidateQuest, 20) == 0     ; forcegreet not done yet
    IsBleedingOut                       == 0     ; opponent is back UP
    GetStage(DGIntimidateQuest)         >= 15    ; opponent went down
    GetStage(DGIntimidateQuest)         <  100   ; <-- the fragile one

So the intended flow is:

    opponent bleeds out  ->  stage 15  ->  StopCombat  ->  the engine stands
    her back up AT FULL HEALTH  ->  the package activates, she walks over and
    force-greets you  ->  that conversation is the win.

The full-health recovery is CORRECT AND REQUIRED. It is not the bug. The bug is
that the forcegreet which should follow it never arrives, so all you ever see
is the recovery, over and over.


THE BUG - part 1, and this is the one that fires on every punch
---------------------------------------------------------------
OnHit's second parameter is misnamed. It is the hit SOURCE, not a weapon: a
Weapon for a swing, but a SPELL for a magic hit. SureAI test it as

    if akProjectile || (akWeapon && akWeapon != UnarmedWeapon)

which reads "the source exists and is not my fists" - and a Spell satisfies
that. For Honor Reforged casts HitFrameTriggerSpell (000803) at the target on
EVERY landed hit, through ReforgedParryController's unconditional
ApplyCombatHitSpell entry, and none of its four effects carries the NoHitEvent
flag, so OnHit fires. Same for Parry Knockdown Spell (000836),
ParryStaggerKnockdownSpell (0008B1) and SP_Stagger_Parry (00082F) - which is
why a timed block does it too, and why it happens in FIRST person, where
blocking still works even though the movesets do not.

So every normal hit, every heavy hit and every parry runs the brawl's full
"you cheated" teardown: both fighters pulled out of DGIntimidateFaction,
StopCombat(), SendAssaultAlarm(), StartCombat(), stage 150. The visible tell is
the opponent dropping out of combat and re-readying her fists, and her health
snapping back to full as combat is restarted on an Essential actor. Reported
as: "she just jumps back to 130, instantly, not regen, after one hit or a few."

The same trap is in the player script's OnHit, where a framework's self-cast
marker spell on the player reads as "somebody else attacked me" and sets stage
200, stopping the brawl quest mid-fight.

Fix: require "akWeapon as Weapon" to be non-None. A spell is not a weapon
swing. A player who really does cast at their opponent is still caught, by
OnMagicEffectApply.


THE BUG - part 2, stage 150 locks the win out permanently
---------------------------------------------------------
Both brawl scripts treat an incoming magic effect as proof somebody cast a
spell, and answer with SetStage(150):

  _00E_DGIntimidateAliasScript.OnMagicEffectApply   ; on the OPPONENT
      any HOSTILE effect landed by the player            -> SetStage(150)

  _00E_DGIntimidatePlayerScript.OnMagicEffectApply  ; on the PLAYER
      ANY effect at all from any caster but the player   -> SetStage(150)

150 is >= 100, so it permanently fails the last package condition above. The
victory forcegreet can never fire again for the rest of that brawl, and nothing
reverses it.

That was safe in 2016. It is not safe beside an animation-driven combat
framework, which casts invisible marker effects on every landed blow through
Payload Interpreter and Dynamic Animation Casting. For Honor Reforged's UNARMED
move-set - and a brawl is unarmed by definition - fires LimbStrikes (0008AE) on
knee, elbow and shoulder strikes, and that spell carries two effects that are
both flagged Hostile:

  Poise Damage Non Blocking  00089F   Hostile, Detrimental, HideInUI, Painless
  Stamina Damage             00089E   Hostile, Detrimental, HideInUI, Painless

Its parry system does the same with Weapon Parry Poise Damage (000892 ->
0005F5, Hostile), cast through the ReforgedParryController perk that SPID hands
to every actor in the game at 100%. The opponent does it back to the player.

So the first landed punch sets stage 150 and the brawl is already unwinnable.

Why third person only: Behavior Data Injector registers For Honor's animation
events on the shared "Actors" behaviour project. The first-person graph has
none of them, so no payload fires, no marker effect lands, stage 150 is never
set, and the brawl resolves normally - exactly as reported.

Why For Honor in Skyrim on its own is fine: its unarmed hit casts
SP_Impact_Fist (00082D -> 000823), which is NOT Hostile, and Reforged's payload
config comments out every one of its Hostile MA_Stagger_* / MA_Ragdoll lines.

Not a For-Honor-only defect - any framework that fires marker effects on melee
hits does the same. For Honor Reforged 2.2 fixed its half upstream ("unarmed
should no longer break brawls"); this fixes Enderal's half, so an older build
or a different framework is covered too.


THE FIX
-------
Ask what Enderal actually cares about: was that REAL magic? Enderal's own
offensive effects all carry one of the five magic schools in MagicSkill;
combat-framework markers carry none - verified across For Honor in Skyrim and
For Honor Reforged, where not one magic effect has a MagicSkill, against 482 of
base Enderal's that do. Both OnMagicEffectApply handlers now gate on
GetAssociatedSkill() returning Destruction, Restoration, Conjuration,
Alteration or Illusion. Casting a real spell at your brawl opponent still
counts as cheating, exactly as SureAI intended.

Nothing else is changed. Neither script gained, lost or renamed a Property -
the host quest's VMAD binds UnarmedWeapon, DGIntimidateFaction, Opponent and
OpponentFriend by name and would silently deliver nothing if any changed. The
player script's curScriptVersion / LATEST_SCRIPT_VERSION migration is untouched.

WHAT NOT TO DO, because it was tried here and it is worse: do NOT call
SetStage(200) from OnEnterBleedout to "end a stuck brawl". 200 is also >= 100,
so it fails the same package condition and kills the victory forcegreet
outright - and its fragment then AllowBleedoutDialogue(False)s and Stop()s the
quest three seconds after the opponent goes down. The 5-second OnUpdate poll is
SureAI's intended shutdown and has to be allowed to lose the race to the
forcegreet.


SCOPE
-----
Every brawl in Enderal runs through these two scripts:

  NQ12  "Divide and Conquer"  - Silia Foxhand, in the Undercity
  NQ_G_04                     - Duul
  FS_NQ06                     - Darius Kupferhammer
  EnvironmentScene01          - the tavern drunk


INSTALL
-------
Ordinary mod, no options. Nothing else in the list ships either script loose
(they live only inside Enderal's E - Misc.bsa), so a loose file wins
automatically and no particular sort position is required.

The "Apocalypse - Enderal Patch", "Triumvirate - Enderal Patch" and "Enhanced
Blood Textures Enderal SE" mods do ship loose dgintimidatealiasscript.pex /
dgintimidateplayerscript.pex - those are the UNPREFIXED vanilla names, which
Enderal ships as do-nothing stubs and which its brawl quest does not use. They
do not conflict with these files.


SAVE COMPATIBILITY
------------------
Safe to add mid-playthrough; no new game needed. A .pex override takes effect
wherever the script next runs, and these events run fresh on every brawl.

A brawl you are ALREADY in has stage 150 set, and no script change un-sets it.
Reset it from the console:

    setstage 11A493 15

Then STOP ATTACKING and back off. She gets up at full health - that is the
intended behaviour - and should then walk over and start the victory
conversation.

To check the diagnosis yourself, "sqs 11A493" lists the brawl quest's completed
stages. 150 present = this bug.
