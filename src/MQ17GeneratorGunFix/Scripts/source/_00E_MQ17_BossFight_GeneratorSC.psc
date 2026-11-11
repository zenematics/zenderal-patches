Scriptname _00E_MQ17_BossFight_GeneratorSC extends Actor  

;=====================================================================================
;              							 EVENTS                   					 
;=====================================================================================

Event OnInit()

	Self.SetActorValue("HealRate", 0)

EndEvent

Event OnUpdate()

	bPlayerWasStupid = True

EndEvent

Event OnHit(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)

	; ZP: SureAI only counted hits on the invisible hit boxes (_00E_MQ17_GeneratorHitBoxSC). The list's musket balls
	; and pistol shots reach the generator itself instead, so its hits now count too, under the hit box's own rules
	; (player only, quest stage 75+, generator alive). CheckForDamage drops the second report of one hit.
	If akAggressor == PlayerREF && !Self.IsDead()
		Quest kMQ17 = Game.GetFormFromFile(0x07FA93, "Skyrim.esm") as Quest ; ZP: MQ17, the hit box's quest
		If kMQ17 && kMQ17.GetCurrentStageID() >= 75
			Debug.Trace("[ZP MQ17 generator] hit on the generator " + Self + " by " + akSource + ", projectile " + akProjectile)
			CheckForDamageFrom(akSource, "generator")
		EndIf
	EndIf

EndEvent

Event OnDying(Actor akKiller)

	MQ17_CombatControllerREF.CollapseGenerator(Self)
	Self.BlockActivation(True)
	Self.GetActorBase().SetName("")
	MQ17_GeneratorDisplay.Kill(PlayerREF)
	MQ17_GeneratorDisplay.Disable()

EndEvent

;=====================================================================================
;              							 FUNCTIONS                   					 
;=====================================================================================

Function CheckForDamage(Form akSource)

	CheckForDamageFrom(akSource, "hit box") ; ZP: the hit box script calls this

EndFunction

Function CheckForDamageFrom(Form akSource, string asWhere) ; ZP: SureAI's CheckForDamage, plus the duplicate guard

	; ZP: one shot can hit the hit box and the generator. The same source within 0.3 s is that same hit.
	float fNow = Utility.GetCurrentRealTime()
	If akSource == ZP_LastHitSource && (fNow - ZP_LastHitTime) < 0.3
		Debug.Trace("[ZP MQ17 generator] " + asWhere + " hit by " + akSource + " ignored: already counted")
		Return
	EndIf
	ZP_LastHitSource = akSource
	ZP_LastHitTime = fNow
	Debug.Trace("[ZP MQ17 generator] " + asWhere + " hit by " + akSource + " counted, shields down " + bShieldsDown)

	If !bShieldsDown
	
		If Utility.RandomInt(0, 100) <= 75 && bPlayerWasStupid
			MQ17_CombatControllerREF.CompanionGeneratorRemark()
		EndIf
		
		DamagePlayer(10)
		
	Else
		;MQ17_GeneratorDisplay.StartCombat(PlayerREF) ; they don't have AI
		float fDamageToDeal = GetDealtDamage(akSource)
		
		_01E_Feuerblitz.RemoteCast(Self, PlayerREF, Self)
		
		Self.DamageActorValue("Health", fDamageToDeal)
		
		float fCurentHealth = Self.GetActorValue("Health")
		float fBaseHealth = Self.GetBaseActorValue("Health")
		If fCurentHealth <= ((fBaseHealth/100)*75) && !bDone75
			_00E_MQ17_BossFight_GeneratorDamageDisplay.Show(75)
			bDone75 = true
		ElseIf fCurentHealth <= ((fBaseHealth/100)*50) && !bDone50
			_00E_MQ17_BossFight_GeneratorDamageDisplay.Show(50)
			bDone50 = true
		ElseIf fCurentHealth <= ((fBaseHealth/100)*25) && !bDone25
			_00E_MQ17_BossFight_GeneratorDamageDisplay.Show(25)
			bDone25 = true
		ElseIf fCurentHealth <= 0 && !bDone0
			_00E_MQ17_BossFight_GeneratorDamageDisplay.Show(0)
			bDone0 = true
		Endif
		
		If Utility.RandomInt(0, 100) <= 50
			MQ17_SC06_BlackGuardianHeartREF.Say(MQ17_D04_FinalFightPain)
		EndIf
	
		PlayImpactFX()
		
	EndIf

EndFunction

Function ActivateShield()
	
	bShieldsDown = False
	bPlayerWasStupid = False
	_00E_MQ13c_TurretChargeSoundM.Play(Self)
	Self.GetActorBase().SetInvulnerable()
	MS04MemoryFXShader.Play(Self)
	MQ17_GeneratorDisplay.Enable()
	RegisterForSingleUpdate(5)
	
EndFunction

Function DeactivateShield()
	
	bShieldsDown = True
	Self.GetActorBase().SetInvulnerable(False)
	MS04MemoryFXShader.Stop(Self)
	
EndFunction

Function PlayImpactFX()

	MAGShockImpact.Play(PlayerREF)
	MAGShockExpImod.Apply()
	Game.ShakeCamera(afStrength = 0.25)
	NPCDwarvenCenturionInjuredM.Play(PlayerREF)
	
	If Self.GetActorValue("Health") <= 5.0
		Self.Kill(PlayerREF)
	EndIf
	
EndFunction

Function DamagePlayer(float fDamageValue)

	Self.PlayImpactEffect(MAGShock01ImpactSet)
	Game.ShakeCamera(afStrength = 0.25)
	MAGShockExpImod.Apply()
	PlayerREF.DamageActorValue("Health", fDamageValue)
	MAGShockImpact.Play(PlayerREF)
	ShockFXShader.Play(PlayerREF)
	Utility.Wait(1)
	ShockFXShader.Stop(PlayerREF)
	
EndFunction

float Function GetDealtDamage(Form akDamageSource)

	if ! SKSE.GetVersion()
		return 55.0
	endif

	bool bIsSpell
	bool bIsArrow

	If akDamageSource.GetType() == 22
		bIsSpell = True
	ElseIf akDamageSource.GetType() == 64
		bIsArrow = True
	EndIf
	
	If bIsArrow
		
		float fBowBaseDamage = 0
		
		If PlayerREF.GetEquippedWeapon(false) != None ; check right hand
			fBowBaseDamage = PlayerREF.GetEquippedWeapon(false).GetBaseDamage()
		ElseIf PlayerREF.GetEquippedWeapon(true) != None ; check left hand
			fBowBaseDamage = PlayerREF.GetEquippedWeapon(true).GetBaseDamage()
		EndIf
		
		If fBowBaseDamage > 0
			Return fBowBaseDamage*5.0
		Else
			Return 55.0
		EndIf
		
	ElseIf bIsSpell
	
		Spell spellHitSpell = akDamageSource as Spell
		float[] fArrayTotalSpellDamage = spellHitSpell.GetEffectMagnitudes()
		float fTotalDamage
		int iArrayIndex = fArrayTotalSpellDamage.Length
	
		while iArrayIndex >= 0
			fTotalDamage += fArrayTotalSpellDamage[iArrayIndex]
			iArrayIndex -= 1
		endwhile
		
		If fTotalDamage > 0
			Return fTotalDamage
		Else
			Return 55.0
		EndIf
		
	Else 
		Weapon weapHitWeapon = akDamageSource as Weapon
		
		float fWeaponBaseDamage = weapHitWeapon.GetBaseDamage()
		
		If fWeaponBaseDamage > 0
			Return fWeaponBaseDamage*3.5
		Else
			Return 55.0
		EndIf
		
	EndIf

EndFunction

;=====================================================================================
;              							 PROPERTIES                   					 
;=====================================================================================

bool bPlayerWasStupid
bool bDone75 = false
bool bDone50 = false
bool bDone25 = false
bool bDone0 = false
Form ZP_LastHitSource ; ZP
float ZP_LastHitTime ; ZP

_00E_TestBossFightSC Property MQ17_CombatControllerREF Auto

bool bShieldsDown = True

EffectShader Property ShockFXShader Auto

Actor Property PlayerREF Auto
Actor Property MQ17_GeneratorDisplay Auto

Topic Property MQ17_D04_FinalFightPain Auto

Spell Property _01E_Feuerblitz Auto

ImpactDataSet Property MAGShock01ImpactSet Auto

ObjectReference Property MQ17_SC06_BlackGuardianHeartREF Auto

Message Property _00E_MQ17_BossFight_GeneratorDamageDisplay Auto

Sound Property NPCDwarvenCenturionInjuredM Auto
Sound Property MAGShockImpact Auto
Sound Property _00E_MQ13c_TurretChargeSoundM Auto

EffectShader Property MS04MemoryFXShader Auto
ImageSpaceModifier Property MAGShockExpImod Auto