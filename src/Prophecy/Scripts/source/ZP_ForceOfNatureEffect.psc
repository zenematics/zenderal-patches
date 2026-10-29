Scriptname ZP_ForceOfNatureEffect extends ActiveMagicEffect
{Prophecy Druid - Force of Nature (lesser power, 2026-10-27). Costs FeverCost Arcane Fever the way Legion of the Damned
takes it (through Zen Traits' ZenTraits_ArcaneFeverScript when present, so the fever traits apply; otherwise a plain
ModAV with Mental Expert's x0.67) and refuses when the cost would take the player to 100. Then it casts Triumvirate's
Force of Nature (FormSpell; its TVR_Wildshape_Script turns the player into a Horned Lord for 60 s) and, once that form
is on, the familiars (Familiars: a raven, a snow leopard and two rattlesnakes, summons of their own duration; the
Force of Nature perk raises the summon limit while FormEffect is on the player). While this effect runs it watches
the form: when it ends early (Triumvirate's dispel power), the familiars are dispelled with it.
Arcane Fever is stored negated in LastFlattered. Compiles against Zen Traits' source.
Sorcery's Mana Burn power uses it too (2026-10-27): FormSpell = the Mana Burn spell, no Familiars (then it only
casts FormSpell), Refusal its own text.
StripArmor (Force of Nature, 2026-10-28): the player turned invisible in the form. Triumvirate's script only takes
weapons and spells off, and its race has no ArmorRace, so worn armour (whose addons do not list the Horned Lord
race) draws nothing and hides the race's own body under it. Worn armour is taken off before the form and put back
when the form ends.
FormSkin (Force of Nature, 2026-10-28): the real cause of the invisible form. The player's actor base carries its own
skin, SkinNaked 000D64 (ZenPlayer3DTrace: "skin(actor base) 00000D64"), and an actor's own skin wins over the race's,
so after the race swap the player wore SkinNaked, whose addons have no Horned Lord version: no body slot was filled,
only the skeleton loaded. NPCs have no own skin, so they got the race's. While the form is on, the player's actor
base wears FormSkin (the race's skin); the saved skin goes back when the form ends. Each switch rebuilds the 3D.}

Spell Property FormSpell Auto
MagicEffect Property FormEffect Auto
Spell Property Familiars Auto
Message Property FeverMessage Auto        ; _00E_Player_sArcaneFeverIncreased
ImageSpaceModifier Property FeverImod Auto ; _00E_ArkanistenfieberIMOD
Perk Property MentalExpert Auto           ; _00E_Class_Thaumaturge_P07_MentalExpert
Float Property FeverCost = 50.0 Auto
Float Property PollSeconds = 1.0 Auto
String Property Refusal = "Your Arcane Fever is too high to call on the Force of Nature." Auto
Bool Property StripArmor = False Auto
Armor Property FormSkin Auto              ; the form race's skin, worn by the player's actor base during the form

Actor player
Bool summoned = False
Armor savedSkin
Bool skinSwapped = False
Form[] stripped
Int strippedCount = 0

Event OnEffectStart(Actor akTarget, Actor akCaster)
	player = akCaster
	If !player
		player = akTarget
	EndIf
	If !player || !FormSpell
		Return
	EndIf
	ZenTraits_ArcaneFeverScript zen = (Game.GetFormFromFile(0x802, "Zen Traits.esp") as Quest) as ZenTraits_ArcaneFeverScript
	Float cost = FeverCost
	If zen
		cost = -zen.ApplyIncreaseFeverMods(-FeverCost)
	ElseIf player.HasPerk(MentalExpert)
		cost = cost * 0.67
	EndIf
	If -player.GetActorValue("LastFlattered") + cost >= 100.0
		Debug.Notification(Refusal)
		Return
	EndIf
	If zen
		zen.ModFever(-FeverCost, True)
	Else
		player.ModActorValue("LastFlattered", -cost)
		FeverMessage.Show(cost, -player.GetActorValue("LastFlattered"))
		FeverImod.Apply()
	EndIf
	If StripArmor
		StripWornArmor()
	EndIf
	FormSpell.Cast(player, player)
	If !Familiars
		If strippedCount > 0
			RegisterForSingleUpdate(PollSeconds)
		EndIf
		Return
	EndIf
	; the familiars only once the form is on: the summon limit the perk raises depends on it
	Int wait = 0
	While wait < 30 && !player.HasMagicEffect(FormEffect)
		Utility.Wait(0.1)
		wait += 1
	EndWhile
	If FormSkin && player.HasMagicEffect(FormEffect)
		WearFormSkin()
	EndIf
	Familiars.Cast(player, player)
	summoned = True
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnUpdate()
	If (!summoned && strippedCount == 0 && !skinSwapped) || !player
		Return
	EndIf
	If !player.HasMagicEffect(FormEffect)
		If summoned
			player.DispelSpell(Familiars)
		EndIf
		summoned = False
		RestoreSkin()
		RestoreArmor()
		Return
	EndIf
	RegisterForSingleUpdate(PollSeconds)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	; the form normally ends first (60 s against this effect's 75); if it has, the armour goes back on
	If player && !player.HasMagicEffect(FormEffect)
		RestoreSkin()
		If strippedCount > 0
			RestoreArmor()
		EndIf
	EndIf
EndEvent

Function WearFormSkin()
	ActorBase base = player.GetActorBase()
	savedSkin = base.GetSkin()
	base.SetSkin(FormSkin)
	skinSwapped = True
	player.QueueNiNodeUpdate()
EndFunction

Function RestoreSkin()
	If !skinSwapped
		Return
	EndIf
	player.GetActorBase().SetSkin(savedSkin)
	skinSwapped = False
	player.QueueNiNodeUpdate()
EndFunction

Function StripWornArmor()
	stripped = new Form[32]
	strippedCount = 0
	Int slot = 0
	While slot < 32
		Form worn = player.GetWornForm(Math.LeftShift(1, slot))
		If worn && (worn as Armor) && stripped.Find(worn) < 0
			stripped[strippedCount] = worn
			strippedCount += 1
		EndIf
		slot += 1
	EndWhile
	Int i = 0
	While i < strippedCount
		player.UnequipItem(stripped[i], False, True)
		i += 1
	EndWhile
EndFunction

Function RestoreArmor()
	Int i = 0
	While i < strippedCount
		If player.GetItemCount(stripped[i]) > 0
			player.EquipItem(stripped[i], False, True)
		EndIf
		i += 1
	EndWhile
	strippedCount = 0
EndFunction
