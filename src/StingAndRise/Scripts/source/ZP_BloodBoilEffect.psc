Scriptname ZP_BloodBoilEffect extends ActiveMagicEffect
{Sting and Rise - Blood Boil. The second effect of each dagger's enchantment starts this, and only when the struck
target already carries the OTHER dagger's damage over time (Sting's venom on a Rise hit, Rise's burn on a Sting hit)
and no Blood Boil cooldown: the enchantment's conditions check both. The target's blood bursts out of it:
BoilVisual, Forgotten Stories' gore burst with its meat taken out (blood drops and streams from chest height, blood
decals around, its own sound, no damage or push of its own), and Blast - a hostile spell blamed on the wielder, so
kills and Enderal's EP go to them as with the weapon hit - on the target and on every living actor within Radius
that is hostile to the wielder, each splattered with blood (BoilShader, Enderal's bloody shader, quick to show).
Cooldown puts a marker on the target first, so it cannot boil again until that ends. Same shape as Prophecy's
A Willing Sacrifice (ZP_WillingSacrificeEffect), which needs powerofthree's Papyrus Extender the same way.}

Spell Property Blast Auto
EffectShader Property BoilShader Auto
Explosion Property BoilVisual Auto
Spell Property Cooldown Auto
MagicEffect Property CooldownEffect Auto

Float Property Radius = 250.0 AutoReadOnly          ; 02-build-records.py BOIL_RADIUS (checked there)
Float Property ShaderSeconds = 2.0 AutoReadOnly     ; then the shader's own 2 s fade
Int Property kActorCharacter = 62 AutoReadOnly

Event OnEffectStart(Actor akTarget, Actor akCaster)
	If !akTarget || !akCaster || akTarget.HasMagicEffect(CooldownEffect)
		Return
	EndIf
	Cooldown.Cast(akCaster, akTarget)
	akTarget.PlaceAtMe(BoilVisual)
	Boil(akTarget, akCaster)
	ObjectReference[] near = PO3_SKSEFunctions.FindAllReferencesOfFormType(akTarget, kActorCharacter, Radius)
	Int i = 0
	While near && i < near.Length
		Actor a = near[i] as Actor
		If a && a != akTarget && a != akCaster && a.IsHostileToActor(akCaster)
			Boil(a, akCaster)
		EndIf
		i += 1
	EndWhile
EndEvent

Function Boil(Actor akVictim, Actor akWielder)
	If akVictim.IsDead()
		Return
	EndIf
	BoilShader.Play(akVictim, ShaderSeconds)
	Blast.RemoteCast(akWielder, akWielder, akVictim)
EndFunction
