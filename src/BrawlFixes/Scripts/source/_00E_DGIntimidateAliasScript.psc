scriptName _00E_DGIntimidateAliasScript extends ReferenceAlias

; ============================================================================
; Zenderal - Brawl Fixes
;
; SureAI's _00E_DGIntimidateAliasScript with ONE change, marked "; ZP".
; Everything else is their original from ScriptsEnderal.zip. Credit: SureAI.
;
; ---------------------------------------------------------------------------
; HOW AN ENDERAL BRAWL IS ACTUALLY WON
; ---------------------------------------------------------------------------
; Read this before touching anything here, because the win condition is NOT
; where it looks like it is. It lives in an AI package on the opponent alias,
; DGForceGreetAfterBleedoutPackage (108B54), which fires only when ALL of:
;
;     GetStageDone(DGIntimidateQuest, 20) == 0     ; forcegreet not done yet
;     IsBleedingOut                       == 0     ; opponent is back UP
;     GetStage(DGIntimidateQuest)         >= 15    ; opponent went down
;     GetStage(DGIntimidateQuest)         <  100   ; <-- THE FRAGILE ONE
;
; So the intended flow is: opponent bleeds out (stage 15) -> StopCombat ->
; the engine stands her back up AT FULL HEALTH -> the package activates, she
; walks over and force-greets the player, and THAT conversation is the win.
;
; The full-health recovery is therefore CORRECT AND REQUIRED. It is not the
; bug. The bug is when the forcegreet that should follow it never comes.
;
; ---------------------------------------------------------------------------
; THE BUG - stage 150 is a one-way door that locks the win out
; ---------------------------------------------------------------------------
; OnMagicEffectApply below treats ANY hostile magic effect landed by the player
; as "the player cast a spell instead of using fists" and sets stage 150. 150
; is >= 100, so it permanently fails the last package condition above: the
; victory forcegreet can never fire again for the rest of that brawl. Nothing
; reverses it. The player is left knocking the opponent down over and over,
; watching her stand back up at full health, with no way to finish.
;
; That was safe in 2016. It is not safe next to an animation-driven combat
; framework. For Honor Reforged's UNARMED move-set - and a brawl is unarmed by
; definition - casts LimbStrikes (0008AE) on the target through Payload
; Interpreter on knee, elbow and shoulder strikes, and that spell carries two
; effects that are BOTH flagged Hostile:
;
;     Poise Damage Non Blocking  00089F
;     Stamina Damage             00089E
;
; Its parry system does the same with Weapon Parry Poise Damage (000892 ->
; 0005F5, Hostile) through the ReforgedParryController perk, which SPID hands
; to every actor in the game at 100%. So the first landed punch of the brawl
; sets stage 150 and the brawl is already unwinnable.
;
; Third person only, because Behavior Data Injector registers For Honor's
; animation events on the shared "Actors" behaviour project - the first-person
; graph has none of them, no payload fires, no hostile effect is applied, and
; the brawl resolves normally. For Honor in Skyrim on its own is fine too: its
; unarmed hit casts SP_Impact_Fist (00082D -> 000823), which is NOT Hostile.
;
; ---------------------------------------------------------------------------
; THE BUG - OnHit's "akWeapon" is really akSOURCE, and a spell lands there too
; ---------------------------------------------------------------------------
; This is the one that actually bites, and it is worse than stage 150 because
; it runs on EVERY punch. OnHit's second parameter is the hit SOURCE - a Weapon
; for a swing, but a Spell for a magic hit. SureAI test it as
;
;     if akProjectile || (akWeapon && akWeapon != UnarmedWeapon)
;
; i.e. "the source exists and is not my fists". A Spell satisfies that. And For
; Honor Reforged casts HitFrameTriggerSpell (000803) at the target on every
; single landed hit, through ReforgedParryController's unconditional
; ApplyCombatHitSpell entry - and NONE of its four effects carries the
; NoHitEvent flag, so OnHit fires. Same for Parry Knockdown Spell (000836),
; ParryStaggerKnockdownSpell (0008B1) and SP_Stagger_Parry (00082F), which is
; why a timed block does it too - and why it happens in FIRST person, where
; blocking still works even though the movesets do not.
;
; So on every normal hit, every heavy hit and every parry, the brawl runs its
; full "you cheated" teardown: both fighters are pulled out of
; DGIntimidateFaction, StopCombat(), SendAssaultAlarm(), StartCombat(), stage
; 150. The visible tell is the opponent dropping out of combat and re-readying
; her fists, and her health snapping back to full as the combat is restarted on
; an Essential actor. Reported as "she just jumps back to 130, instantly, not
; regen, after one hit or a few".
;
; ---------------------------------------------------------------------------
; THE FIX
; ---------------------------------------------------------------------------
; 1. Only a real Weapon can convert the brawl. "akWeapon as Weapon" is None for
;    a spell, so a combat framework's marker spells stop tearing the brawl down
;    on every hit. A player who really does cast a spell at their opponent is
;    still caught, by OnMagicEffectApply below.
;
; 2. Test what Enderal actually cares about there too: did the player use real MAGIC?
; Enderal's own offensive effects all carry one of the five magic schools in
; MagicSkill; combat-framework markers carry none - verified across For Honor
; in Skyrim and For Honor Reforged, where not one magic effect has a MagicSkill,
; against 482 of base Enderal's that do. Casting a real spell at your brawl
; opponent still counts as cheating, exactly as SureAI intended.
;
; DO NOT "help" by calling SetStage(200) from OnEnterBleedout. It looks like it
; ends a stuck brawl and it does the opposite: 200 is >= 100, so it fails the
; same package condition and kills the victory forcegreet - and its fragment
; then AllowBleedoutDialogue(False)s and Stop()s the quest. That was tried here
; and it made the brawl unwinnable on its own. The 5-second OnUpdate poll below
; is SureAI's intended shutdown and it must be allowed to lose the race to the
; forcegreet.
;
; NO Property was added, removed or renamed - the host quest's VMAD binds these
; by name and would silently fail to deliver a value if either changed.
; ============================================================================

;-- Properties --------------------------------------
Weapon property UnarmedWeapon auto
Faction Property DGIntimidateFaction Auto
;-- Variables ---------------------------------------

;-- Functions ---------------------------------------

Event OnUpdate()
	actor pActor = self.GetActorRef()
	if pActor.IsInCombat() == 0  && pActor.IsBleedingOut() == 0 && GetOwningQuest().GetStage() <= 15 ;&& GetOwningQuest().GetStage() < 15
		GetOwningQuest().SetStage(200)
	endIf
EndEvent

Event OnEnterBleedout()

	GetOwningQuest().SetStage(15)
	self.GetActorReference().EvaluatePackage()
	Utility.Wait(3)
	self.GetActorReference().StopCombat()

EndEvent

Event OnMagicEffectApply(ObjectReference akCaster, MagicEffect akEffect)
	if akCaster == game.GetPlayer() && akEffect.IsEffectFlagSet(0x00000001) ; Hit by player with a hostile ME
		if ZP_IsRealMagic(akEffect) ; ZP - a combat framework's marker effect is not the player casting a spell
			GetOwningQuest().SetStage(150)
		endIf
	endIf
EndEvent

; ZP - true only for an effect belonging to one of the five magic schools, i.e.
; the player genuinely cast a spell. Combat-framework marker effects (poise
; damage, stamina damage, stagger and knockdown flags, impact FX) have no
; associated skill and return "None" here.
bool Function ZP_IsRealMagic(MagicEffect akEffect) ; ZP
	if !akEffect
		return false
	endIf
	string sSkill = akEffect.GetAssociatedSkill()
	return sSkill == "Destruction" || sSkill == "Restoration" || sSkill == "Conjuration" || sSkill == "Alteration" || sSkill == "Illusion"
EndFunction

Event OnHit(ObjectReference akAggressor, Form akWeapon, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)
	actor pActor = self.GetActorRef()
	actor pPlayer = game.GetPlayer()

	; ZP - akWeapon is misnamed: the event parameter is akSOURCE, and OnHit also
	; fires for SPELLS, in which case this is a Spell and not a Weapon at all.
	; SureAI's test below is "is the source non-None and not my fists", so ANY
	; spell landing on the brawl opponent reads as "the player swung a weapon"
	; and tears the whole brawl down. See the header for what that costs.
	Weapon pSource = akWeapon as Weapon ; ZP - None unless this really was a weapon swing

	if akAggressor == pPlayer
		if pSource && pSource != UnarmedWeapon ; ZP - was: akProjectile || (akWeapon && akWeapon != UnarmedWeapon)
			pPlayer.RemoveFromFaction(DGIntimidateFaction)
			pActor.RemoveFromFaction(DGIntimidateFaction)
			pActor.StopCombat()
			pActor.SendAssaultAlarm()
			pActor.StartCombat(pPlayer)
			GetOwningQuest().SetStage(150)
		endIf
	elseIf pSource || akProjectile ; ZP - a third party really hit her; ignore a framework's marker spell
		GetOwningQuest().SetStage(150)
	endIf
EndEvent
