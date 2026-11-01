Scriptname _00E_Theriantrophist_PlayerAsWerewolf extends ReferenceAlias 
; Main script of the theriantrophist system; this alias contains the player during the transformation
; and while he is in werewolf form. 
; this script is responsible for stats calculation, controlling the player as werewolf and propagation
; events/control signals to chymikum activemagiceffect scripts etc.

_00E_Theriantrophist_TransformStorage Property EquipementStorage Auto
_00E_Theriantrophist_WolfAttributes Property WolfAttributes Auto
_FS_TheriantrophistControlQuest Property ControlQuest Auto

Spell Property _00E_Theriantrophist_WolfFormSP Auto
{the spell that visually transforms the player}
GlobalVariable Property _00E_Theriantrophist_IsTransformed Auto

Perk Property _00E_Class_Theriantrophist_P06b_BeastInstinct Auto
{the perk that gives the player life detection when in wolf form}
Spell Property _00E_Theriantrophist_DetectLifeBaseSP Auto
{the life detection spell given if the player has the beast instinct perk}
Perk Property _00E_Class_Theriantrophist_P09b_Disguise Auto
Perk Property _00E_Class_Theriantrophist_P09c_AetherBlood Auto

Perk Property _00E_Class_Theriantrophist_P06c_Nightwolf_01 Auto
Perk Property _00E_Class_Theriantrophist_P06c_Nightwolf_02 Auto
Perk Property _00E_Class_Theriantrophist_P06c_Nightwolf_03 Auto

Idle Property WerewolfSneakStart Auto
Idle Property WerewolfSneakStop Auto
Weapon Property _00E_Theriantrophist_Claws Auto

Keyword Property _00E_Theriantrophist_NoTransformLocation Auto
Keyword Property _00E_Theriantrophist_NoTransformLocationTown Auto
Message Property _00E_Theriantrophist_ForceTransformBackMessage Auto
Message Property _00E_Theriantrophist_ForceTransformBackMessageTown Auto
GlobalVariable Property _00E_FS_Theriantrophist_AllowTemporaryTransform Auto

Spell Property _00E_FS_Affinity_AbBrute Auto
Spell Property _00E_FS_Affinity_AbDrifter Auto
Spell Property _00E_FS_Affinity_AbDruid Auto
Spell Property _00E_FS_Affinity_AbNightwolf Auto
Spell Property _00E_FS_Affinity_AbRavager Auto
Spell Property _00E_FS_Affinity_AbScourge Auto
Spell Property _00E_FS_Affinity_AbSoulcaller Auto

Spell Property _00E_FS_Affinity_ScourgeOfTheWilds_TitanSP Auto

Armor Property _00E_FS_Theriantrophist_Skin_Brute Auto
Armor Property _00E_FS_Theriantrophist_Skin_Drifter Auto
Armor Property _00E_FS_Theriantrophist_Skin_Druid Auto
Armor Property _00E_FS_Theriantrophist_Skin_Nightwolf Auto
Armor Property _00E_FS_Theriantrophist_Skin_Ravager Auto
Armor Property _00E_FS_Theriantrophist_Skin_Soulcaller Auto
Armor Property _00E_FS_Theriantrophist_Skin_Scourge Auto

Shout Property _00E_A1_Theriantrophist_TransformBack Auto
WordOfPower Property _00E_FS_Theriantrophist_TransformBack_Word01 Auto

Quest Property FS_NQ11 Auto

float fPlayerScale = 1.0

; Achievement
bool bTransformAchievementUnlocked = false

; Balancing data
Float Property AlchemyPercentageDmg = 0.25 Autoreadonly Hidden
{damage is boosted by this percentage for each alchemy skill point the player has}
Float Property AlchemyPercentage = 0.03 Autoreadonly Hidden
{all werewolf attributes are boosted by this percentage for each alchemy skill point the player has}
Float Property StaminaPercentage = 0.06 Autoreadonly Hidden
{damage is boosted by this percentage for each attribute point over 90 the player has; the atrribute is stamina per default, but may be switched to mana if the player has the special perk}
Float Property BaseDamageResist = 10 Autoreadonly Hidden
{without extra perks and stuff, the werewolf has this amount of damage resist, i.e. this percentage of every damage point is prevented}
Float Property BaseDamagePerSkillLevelInEquippedSpellsSchool = 0.33 Autoreadonly Hidden
{the base claw damage of the werewolf (damage before the boost factor is applied) uses the DPS of equipped weapons, or the player skill level in the magic school of an equipped spell.
This skill level is multiplied with BaseDamagePerSkillLevelInEquippedSpellsSchool and treated as a DPS value of a weapon after that}

Float Property BalancingDamageMalusPercent = 5 Autoreadonly Hidden
{the claw damage of the wolf is decreased by this percentage for balancing purposes}
Float Property BalancingHealthMalusPercent = 85 Autoreadonly Hidden
{the health of the wolf is decreased by this percentage for balancing purposes}
Float Property BalancingStaminaMalusPercent = 75 Autoreadonly Hidden
{the stamina of the wolf is decreased by this percentage for balancing purposes}
Float Property BoostFactorInfluenceOnArmor = 11 Autoreadonly Hidden
{the boost factor multiplied with this value is the wolf armor bonus for balancing purposes}

_00E_Theriantrophist_TransformSC Property transformEffect Auto
_00E_Theriantrophist_Chymikum[] RegisteredChymikums
bool Sneaking = false

int function _GetScriptVersion() Global
    return 2
endFunction

Function Transform(_00E_Theriantrophist_TransformSC aTransformEffect = None, int duration = 0)
	
	bool bWasParalyzed
	Actor player = self.getActorReference()
	while player.GetActorValue("Paralysis") == 1
		bWasParalyzed = true
		Utility.Wait(1)
	endwhile
	
	If bWasParalyzed
		Utility.Wait(6)
	EndIf
	
	player.restoreav("stamina", 9999)
	player.restoreav("magicka", 9999)
	fPlayerScale = player.GetScale()
	
	if SKSE.GetVersion()
		EquipementStorage.saveEquippedItems()
	else
		EquipementStorage.saveEquippedItemsVanilla()
	endif
	
	float preTransformDmgResist = player.GetActorValue("damageResist")
	
	transformEffect = aTransformEffect
	
	if duration > 0
		; Wolf Blood should dispel the wolf form on finish (as of 2.1)
		; With SKSE, we equalize their duration. The 5 seconds offset serves as a failsafe in case the main effect ends without changing the race.
		_00E_Theriantrophist_WolfFormSP.setNthEffectDuration(0, duration + 5)
	endif
	
	_00E_Theriantrophist_WolfFormSP.Cast(player)
	WolfAttributes.SetInWolfForm(true)
	player.additem(_00E_Theriantrophist_Claws, abSilent = true)
	player.equipItem(_00E_Theriantrophist_Claws, abSilent = true)
	_Init(preTransformDmgResist)
	gotoState("Transfomed")
	 _TeachTransformBackTalent()
	 
	If !bTransformAchievementUnlocked
		bTransformAchievementUnlocked = true
		Steam.UnlockAchievement("END_WEREWOLF_01")
	EndIf
	 
	If FS_NQ11.GetCurrentStageID() == 15 || FS_NQ11.GetCurrentStageID() == 17
		FS_NQ11.SetObjectiveCompleted(20)
	EndIf

EndFunction

Function TransformBackByTimer()
	transformEffect = None
	TransformBack()
endfunction

Function TransformBack()
	
	If _00E_FS_Affinity_ScourgeOfTheWilds_TitanSP == None
		_00E_FS_Affinity_ScourgeOfTheWilds_TitanSP = Game.GetFormFromFile(0x0102F19E, "Enderal - Forgotten Stories.esm") as Spell
	EndIf
	
	;MagicEffect _00E_FS_Affinity_ScourgeOfTheWilds_TitanME = Game.GetFormFromFile(0x0102F19F, "Enderal - Forgotten Stories.esm") as MagicEffect
	
	Actor PlayerREF = Game.GetForm(0x14) as Actor

	If PlayerREF.dispelSpell(_00E_FS_Affinity_ScourgeOfTheWilds_TitanSP)
		while PlayerREF.getscale() > fPlayerScale
			Utility.Wait(0.05)
		endwhile
	EndIf
	PlayerREF.dispelSpell(_00E_Theriantrophist_WolfFormSP)
	
	if transformEffect
		transformEffect.GotoState("ForcedFinish")
		transformEffect.Dispel()
		transformEffect = None
	endif
	
Endfunction

Function OnWolfFormSpellEnd()
	gotoState("")
	Actor wolf = self.getActorReference()
	self.clear()
	wolf.removeSpell(_00E_Theriantrophist_DetectLifeBaseSP)
	wolf.removeItem(_00E_Theriantrophist_Claws, 100, abSilent = true)
	; Dispel chymicum effects before all other effects to properly restore values
	_DispelAllChymikums()
	WolfAttributes.SetInWolfForm(false)
	EquipementStorage.equipeItems()
EndFunction

Function TransformBackIfTransformed()
	if (IsTransformed())
		TransformBack()
	EndIf
Endfunction

Bool Function IsTransformed()
	return _00E_Theriantrophist_IsTransformed.GetValueInt() == 1
Endfunction

Function _TeachTransformBackTalent()
	if !Game.getPlayer().HasSpell(_00E_A1_Theriantrophist_TransformBack)
		Game.getPlayer().addShout(_00E_A1_Theriantrophist_TransformBack)
		Game.unlockWord(_00E_FS_Theriantrophist_TransformBack_Word01)
	Endif
Endfunction

Function _UpdateChymikumTransformed()
	Int i = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			RegisteredChymikums[i].OnWolfFormStart()
		EndIf
		i += 1
	EndWhile
Endfunction

Function _UpdateChymikumTransformedBack()
	Int i = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			RegisteredChymikums[i].OnWolfFormFinish()
		EndIf
		i += 1
	EndWhile
Endfunction

Function _DispelAllChymikums()
	Int i = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			RegisteredChymikums[i].Dispel()
		EndIf
		i += 1
	EndWhile
Endfunction

Function RegisterChymikum(_00E_Theriantrophist_Chymikum value)
	if (RegisteredChymikums.length != 5)
		RegisteredChymikums = new _00E_Theriantrophist_Chymikum[5]
	EndIf
	Int index = RegisteredChymikums.Find(None)
	RegisteredChymikums[index] = value
Endfunction

Function UnRegisterChymikum(_00E_Theriantrophist_Chymikum value)
	Int index = RegisteredChymikums.Find(value)
	if index != -1
		RegisteredChymikums[index] = None
	EndIf
Endfunction

Int Function CalcRegisteredChymikumCount()
	Int i = 0
	Int count = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			count += 1
		EndIf
		i += 1
	EndWhile
	return count
EndFunction

_00E_Theriantrophist_Chymikum Function CalcNthRegisteredChymikum(Int index)
	Int i = 0
	While i < RegisteredChymikums.length
		if RegisteredChymikums[i] != None
			if index == 0
				return RegisteredChymikums[i]
			Endif
			index = index - 1
		EndIf
		i += 1
	Endwhile
	return None
EndFunction

Function _Init(float preTransformDmgResist)
	_InitStats(preTransformDmgResist)
	Actor player = self.getActorReference()
	if (player.hasPerk(_00E_Class_Theriantrophist_P06b_BeastInstinct))
		player.addSpell(_00E_Theriantrophist_DetectLifeBaseSP, false)
	Endif
Endfunction

Function _InitStats(float preTransformDmgResist)
	Actor player = self.getActorReference()
	Float boostAttribute = player.getAV("stamina") - 115
	if player.hasPerk(_00E_Class_Theriantrophist_P09c_AetherBlood) && player.getAV("magicka") - 90 > boostAttribute
		boostAttribute = player.getAV("magicka") - 90
	EndIf
	
	; damage, health and stamina in werewolf form are boosted by this factor
	Float boostFactor = 1 + player.getAV("alchemy") * AlchemyPercentageDmg + boostAttribute * StaminaPercentage
	Float boostFactorLifeStamina = 1 + player.getAV("alchemy") * AlchemyPercentage 
	
	float fHealthMod = player.getBaseAV("health") * boostFactorLifeStamina * (1 - BalancingHealthMalusPercent / 100.0)
	float fStaminaMod = boostAttribute + 115 * boostFactorLifeStamina * (1 - BalancingStaminaMalusPercent / 100.0)
	if player.hasPerk(_00E_Class_Theriantrophist_P09c_AetherBlood) && player.getAV("magicka") - 90 > boostAttribute
		fStaminaMod = boostAttribute + 90 * boostFactorLifeStamina * (1 - BalancingStaminaMalusPercent / 100.0)
	EndIf
	
	WolfAttributes.ModWolfHealth(fHealthMod)
	WolfAttributes.ModWolfStamina(fStaminaMod)
	
	float fClawDamage = 1 + boostFactor * (1 - BalancingDamageMalusPercent / 100.0)
	float ClawDamageBonus = player.GetAV("LastBribedIntimidated")
	WolfAttributes.ForceWolfUnarmedDmg(fClawDamage)
	
	float fDamageResistBonus = BoostFactorInfluenceOnArmor * boostFactor
	float fDamageResist = fDamageResistBonus
	
	WolfAttributes.ForceWolfDamageResist(fDamageResist)
	WolfAttributes.ForceWolfSpeedMult(100)
	
EndFunction

Float Function _CalcWeaponSpellStrength(Actor player)

	Float result = EquipementStorage.getWeaponDamageSpeed()
	
	if (EquipementStorage.isEquippedItemRightSpell())
		result += _GuessPlayerSkillInSpellSchool(player, EquipementStorage.getEquippedSpellRight()) * BaseDamagePerSkillLevelInEquippedSpellsSchool
	EndIf
	
	if (EquipementStorage.isEquippedItemLeftSpell())
		result += _GuessPlayerSkillInSpellSchool(player, EquipementStorage.getEquippedSpellLeft()) * BaseDamagePerSkillLevelInEquippedSpellsSchool
	EndIf
	
	return result
	
EndFunction

Float Function _GuessPlayerSkillInSpellSchool(Actor player, Spell s)
	String guessedSchool = s.getNthEffectMagicEffect(0).getAssociatedSkill()
	return player.GetActorValue(guessedSchool)
EndFunction

Int Function _CalcNumberOfPerksPlayerHas(Perk[] perks)
	Actor player = self.getActorReference()
	Int i = perks.length
	Int perkCount = 0
	while (i > 0)
		i = i - 1
		if (player.hasPerk(perks[i]))
			perkCount += 1
		EndIf
	Endwhile
	return perkCount
Endfunction

Function UpdateChymikumsLoadGame()
	Int i = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			RegisteredChymikums[i].OnPlayerLoadGame()
		EndIf
		i += 1
	EndWhile
EndFunction

Function UpdateChymikumOnCombatHit(Actor target)
	Int i = 0
	while (i < RegisteredChymikums.length)
		if (RegisteredChymikums[i] != None)
			RegisteredChymikums[i].OnCombatHit(target)
		EndIf
		i += 1
	EndWhile
Endfunction

bool function CanBeTransformed(Location loc)
	if loc && loc.hasKeyword(_00E_Theriantrophist_NoTransformLocation) && _00E_FS_Theriantrophist_AllowTemporaryTransform.GetValueInt() != 1
		return false
	elseif loc && loc.hasKeyword(_00E_Theriantrophist_NoTransformLocationTown) && !Game.getPlayer().hasPerk(_00E_Class_Theriantrophist_P09b_Disguise) && _00E_FS_Theriantrophist_AllowTemporaryTransform.GetValueInt() != 1
		return false
	endif
	return true
Endfunction

Function _ReapplySkins()

	if ! SKSE.GetVersion()
		return
	endif
	
	Actor player = GetReference() as Actor
	
	if !player || player.IsOnMount() || player.IsSwimming()
		return
	endif
	
	ActorBase playerbase = player.GetActorBase()
		
	if player.HasSpell(_00E_FS_Affinity_AbBrute)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Brute)
	elseif player.HasSpell(_00E_FS_Affinity_AbDrifter)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Drifter)
	elseif player.HasSpell(_00E_FS_Affinity_AbDruid)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Druid)
	elseif player.HasSpell(_00E_FS_Affinity_AbNightwolf)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Nightwolf)
	elseif player.HasSpell(_00E_FS_Affinity_AbRavager)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Ravager)
	elseif player.HasSpell(_00E_FS_Affinity_AbScourge)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Scourge)
	elseif player.HasSpell(_00E_FS_Affinity_AbSoulcaller)
		playerbase.SetSkin(_00E_FS_Theriantrophist_Skin_Soulcaller)
	else
		playerbase.SetSkin(playerbase.GetRace().GetSkin())
	endif
	player.QueueNiNodeUpdate()
EndFunction

Function _FixNotTransformedPlayerSkin()
	if ! SKSE.GetVersion()
		return
	endif

	Actor player = Game.GetForm(0x14) as Actor
	
	if player && ! player.IsOnMount() && ! player.IsSwimming()
		player.getActorBase().SetSkin(player.GetRace().GetSkin())
		player.QueueNiNodeUpdate()
	endif
EndFunction

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
	if !CanBeTransformed(akNewLoc)
		if akNewLoc.hasKeyword(_00E_Theriantrophist_NoTransformLocationTown)
			_00E_Theriantrophist_ForceTransformBackMessageTown.show()
		else
			_00E_Theriantrophist_ForceTransformBackMessage.show()
		endif
		RegisterForSingleUpdate(6)
	Endif
Endevent

Event OnUpdate()
	if !CanBeTransformed(self.GetRef().GetCurrentLocation())
		TransformBackIfTransformed()
	Endif
EndEvent
	
Function OnPlayerLoadGame()
	WolfAttributes.renewNotPersistentStats()
	UpdateChymikumsLoadGame()
	_FixNotTransformedPlayerSkin()
Endfunction

State Transfomed

	Event OnBeginState()
		_UpdateChymikumTransformed()
		RegisterForControl("Sneak")
		SendModEvent("Theriantrophist_Transformed")
		Sneaking = false
		AddInventoryEventFilter(_00E_Theriantrophist_Claws)
		; Change _00E_Theriantrophist_IsTransformed after applying chymicum effects in order to properly restire values
		_00E_Theriantrophist_IsTransformed.setValue(1)
	Endevent
	
	Event OnEndState()
		if (Sneaking)
			self.getActorReference().playIdle(WerewolfSneakStop)
			WolfAttributes.SetTemporarilyWolfSpeedMultMod(0)
			Sneaking = false
			ControlQuest.GetAffinityControl().OnSneak(false)
		Endif
		_DispelAllChymikums()
		_00E_Theriantrophist_IsTransformed.setValue(0)
		SendModEvent("Theriantrophist_TransformedBack")
		UnRegisterForControl("Sneak")
	Endevent
	
	Function OnPlayerLoadGame()
		WolfAttributes.renewNotPersistentStats()
		UpdateChymikumsLoadGame()
		RegisterForControl("Sneak")
		_ReapplySkins()
	Endfunction
	
	Event OnControlDown(string control)
		If Sneaking
			self.getActorReference().playIdle(WerewolfSneakStop)
			WolfAttributes.SetTemporarilyWolfSpeedMultMod(0)
			Sneaking = false
			ControlQuest.GetAffinityControl().OnSneak(false)
		Else
			self.getActorReference().playIdle(WerewolfSneakStart)
			
			Actor akplayer = self.GetActorReference()
			
			if akplayer.HasPerk(_00E_Class_Theriantrophist_P06c_Nightwolf_01)
				WolfAttributes.SetTemporarilyWolfSpeedMultMod(-55)
			elseif akplayer.HasPerk(_00E_Class_Theriantrophist_P06c_Nightwolf_02)
				WolfAttributes.SetTemporarilyWolfSpeedMultMod(-50)
			elseif akplayer.HasPerk(_00E_Class_Theriantrophist_P06c_Nightwolf_03)
				WolfAttributes.SetTemporarilyWolfSpeedMultMod(-40)
			else
				WolfAttributes.SetTemporarilyWolfSpeedMultMod(-60)
			endif
			
			Sneaking = true
			ControlQuest.GetAffinityControl().OnSneak(true)
		EndIf
	EndEvent

	Event OnObjectEquipped(Form akBaseObject, ObjectReference akReference)
		if akBaseObject != _00E_Theriantrophist_Claws
			self.getActorReference().UnequipItem(akBaseObject)
			self.getActorReference().equipItem(_00E_Theriantrophist_Claws, abSilent = true)
		Endif
	Endevent
	
	Event OnObjectUnequipped(Form akBaseObject, ObjectReference akReference)
		if (akBaseObject == _00E_Theriantrophist_Claws)
			self.getActorReference().equipItem(_00E_Theriantrophist_Claws, abSilent = true)
		Endif
	Endevent
	
	Event OnItemRemoved(Form akBaseItem, int aiItemCount, ObjectReference akItemReference, ObjectReference akDestContainer)
		if (akBaseItem != _00E_Theriantrophist_Claws)
			return
		Endif
		If !akDestContainer
			akItemReference.delete()
			self.getActorReference().addItem(_00E_Theriantrophist_Claws, abSilent = true)
			self.getActorReference().equipItem(_00E_Theriantrophist_Claws, abSilent = true)
		Else
			akDestContainer.removeItem(_00E_Theriantrophist_Claws)
			self.getActorReference().addItem(_00E_Theriantrophist_Claws, abSilent = true)
			self.getActorReference().equipItem(_00E_Theriantrophist_Claws, abSilent = true)
		Endif
	EndEvent
EndState
