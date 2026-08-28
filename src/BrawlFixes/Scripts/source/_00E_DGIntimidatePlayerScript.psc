Scriptname _00E_DGIntimidatePlayerScript extends ReferenceAlias

; ============================================================================
; Zenderal - Brawl Fixes
;
; SureAI's _00E_DGIntimidatePlayerScript with ONE change, marked "; ZP".
; Everything else is their original from ScriptsEnderal.zip. Credit: SureAI.
;
; THE BUG. OnMagicEffectApply below fires stage 150 - "the player cheated,
; do not shut the brawl down cleanly" - for ANY magic effect the player
; receives from any caster other than themselves. It does not even check that
; the effect is hostile.
;
; Next to an animation-driven combat framework that is a hair trigger. For
; Honor in Skyrim and For Honor Reforged cast impact, stagger, poise and
; stamina marker effects on whoever is hit, through Payload Interpreter and
; Dynamic Animation Casting, on every landed blow - so the brawl opponent's
; first punch lands a magic effect on the player and the brawl is flagged as
; cheated before it has begun.
;
; Stage 150 is not recoverable: DGIntimidateQuest's shutdown stage 250 chooses
; its fragment on GetStageDone(150), and only the "player did not cheat" branch
; calls StopCombatAlarm() on both fighters. Combat therefore never ends, and
; because brawl opponents are Essential they cannot die - they drop to bleedout
; and the engine stands them back up at full health, forever. See the companion
; _00E_DGIntimidateAliasScript for the same failure reached from the other side.
;
; THE FIX. Test what Enderal actually cares about: did the player get hit by
; real MAGIC? Enderal's own offensive effects all carry one of the five magic
; schools in MagicSkill; combat-framework marker effects carry none.
;
; NO Property was added, removed or renamed - the host quest's VMAD binds
; Opponent and OpponentFriend by name and would silently fail to deliver a
; value if either changed. curScriptVersion / LATEST_SCRIPT_VERSION are left
; exactly as SureAI had them so their OnPlayerLoadGame migration still works.
; ============================================================================

import game

Event OnHit(ObjectReference akAggressor, Form akWeapon, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)
	; ZP - akWeapon is really akSOURCE and is a Spell for a magic hit, so require a
	; real weapon or projectile. Without this, a combat framework's self-cast marker
	; spell on the player (aggressor = the player, who is neither brawler) reads as
	; "somebody else attacked me" and stops the brawl quest outright, mid-fight.
	Weapon pSource = akWeapon as Weapon ; ZP
	if !pSource && !akProjectile ; ZP
		return ; ZP - not a weapon swing or a shot; nothing to judge
	endIf ; ZP

	; if the player is hit with any weapon other than hands, or by anyone but the brawlers
	if akAggressor != Opponent.GetRef() && akAggressor != OpponentFriend.GetRef()
		GetOwningQuest().SetStage(200)
	endif
endEvent

Event OnMagicEffectApply(ObjectReference akCaster, MagicEffect akEffect)
	; if player is hit with any magic effect (not by himself)
	if akCaster != GetPlayer()
		if ZP_IsRealMagic(akEffect) ; ZP - a combat framework's marker effect is not somebody casting a spell
			GetOwningQuest().SetStage(150)
		endif
	endif
endEvent

; ZP - true only for an effect belonging to one of the five magic schools, i.e.
; somebody genuinely cast a spell. Combat-framework marker effects (impact FX,
; stagger and knockdown flags, poise and stamina damage) have no associated
; skill and return "None" here.
bool Function ZP_IsRealMagic(MagicEffect akEffect) ; ZP
	if !akEffect
		return false
	endIf
	string sSkill = akEffect.GetAssociatedSkill()
	return sSkill == "Destruction" || sSkill == "Restoration" || sSkill == "Conjuration" || sSkill == "Alteration" || sSkill == "Illusion"
EndFunction

Event OnEnterBleedout()
; 	Debug.Trace("player enters bleedout")
	GetPlayer().SetNoBleedoutRecovery(false)
	GetOwningQuest().SetStage(180)
	Utility.Wait(7)
	GetOwningQuest().SetStage(200)
EndEvent

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
	if GetPlayer().IsInLocation(Opponent.GetActorRef().GetCurrentLocation()) == False
		; Debug.Trace(self + "Player has left opponent's location, shutting down")
    	GetOwningQuest().SetStage(200)
 	endIf
endEvent


; Version update
Int curScriptVersion = 0
Int Property LATEST_SCRIPT_VERSION = 1 AutoReadOnly

Function Setup()
	curScriptVersion = LATEST_SCRIPT_VERSION
EndFunction

Event OnPlayerLoadGame()
	If curScriptVersion < LATEST_SCRIPT_VERSION
		curScriptVersion = LATEST_SCRIPT_VERSION

		Int curStage = GetOwningQuest().GetStage()
		If curStage >= 150 && curStage < 200 ; Terminate the quest if it's stuck
			GetOwningQuest().SetStage(200)
		EndIf
	EndIf
EndEvent


ReferenceAlias Property Opponent Auto
ReferenceAlias Property OpponentFriend Auto
