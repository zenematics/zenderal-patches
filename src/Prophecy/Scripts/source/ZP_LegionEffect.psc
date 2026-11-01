Scriptname ZP_LegionEffect extends ActiveMagicEffect
{Prophecy Necromancy - Legion of the Damned (lesser power). Costs FeverCost Arcane Fever and raises six skeletons in an arc in front of the player - two
warriors, two archers, two mages - with Enderal's summon portal art. They are placed actors, not summons, so they do
not count against the summon limit: in the player's faction, teammates, following on SureAI's _DefaultFollowPlayer.
Each has BaseHealth + HealthPerLevel per player level. Their own ability (ZP_LegionSkeletonEffect) crumbles them
after their time is up or when they die. A new Legion replaces the old one. Arcane Fever is stored negated in
LastFlattered; the fever goes through Zen Traits' ZenTraits_ArcaneFeverScript (Zen Traits.esp 0x802, the same call
ArcaneFever.ModFever makes), so the fever traits change the cost; without Zen Traits it is a plain ModAV with Mental
Expert's x0.67. The power refuses when the cost would take the player to 100. Needs powerofthree's Papyrus Extender
(MoveToNearestNavmeshLocation); compiles against Zen Traits' source (Zenderal - Patch Collection/Source/Scripts).}

ActorBase Property Warrior Auto
ActorBase Property Archer Auto
ActorBase Property Mage Auto
Message Property FeverMessage Auto        ; _00E_Player_sArcaneFeverIncreased
ImageSpaceModifier Property FeverImod Auto ; _00E_ArkanistenfieberIMOD
Perk Property MentalExpert Auto           ; _00E_Class_Thaumaturge_P07_MentalExpert
FormList Property LegionList Auto
VisualEffect Property SummonArt Auto      ; DA07SummonTargetFX: the summon portal art SummonTargetFX 03F811 as a VFX
Sound Property RaiseSound Auto            ; MAGConjurePortalOpenM
Float Property FeverCost = 50.0 Auto
Float Property BaseHealth = 80.0 Auto
Float Property HealthPerLevel = 8.0 Auto
Float Property SpawnDistance = 160.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
	Actor player = akCaster
	; the fever goes through Zen Traits (curator 2026-10-24), as every fever change in this list does: its
	; ApplyIncreaseFeverMods applies Mental Expert, Night Fever, Purified Blood and Arcane Addict, and ModFever applies
	; the same math, then shows Enderal's fever message, sound and screen effect. Without Zen Traits: Mental Expert only.
	ZenTraits_ArcaneFeverScript zen = (Game.GetFormFromFile(0x802, "Zen Traits.esp") as Quest) as ZenTraits_ArcaneFeverScript
	Float cost = FeverCost
	If zen
		cost = -zen.ApplyIncreaseFeverMods(-FeverCost)
	ElseIf player.HasPerk(MentalExpert)
		cost = cost * 0.67
	EndIf
	If -player.GetActorValue("LastFlattered") + cost >= 100.0
		Debug.Notification("Your Arcane Fever is too high to raise the Legion.")
		Return
	EndIf
	If zen
		zen.ModFever(-FeverCost, True)
	Else
		player.ModActorValue("LastFlattered", -cost)
		FeverMessage.Show(cost, -player.GetActorValue("LastFlattered"))
		FeverImod.Apply()
	EndIf
	; the old Legion crumbles (its skeletons leave the list as they die)
	Int i = LegionList.GetSize()
	While i > 0
		i -= 1
		Actor old = LegionList.GetAt(i) as Actor
		If old && !old.IsDead()
			old.Kill(old)
		EndIf
	EndWhile
	LegionList.Revert()
	Float health = BaseHealth + HealthPerLevel * player.GetLevel()
	Float a = player.GetAngleZ()
	RaiseSound.Play(player)
	i = 0
	While i < 6
		ActorBase kind = Warrior
		If i == 2 || i == 3
			kind = Archer
		ElseIf i >= 4
			kind = Mage
		EndIf
		Float ang = a - 75.0 + 30.0 * i
		Actor s = player.PlaceActorAtMe(kind)
		If s
			s.MoveTo(player, SpawnDistance * Math.Sin(ang), SpawnDistance * Math.Cos(ang), 0.0, False)
			PO3_SKSEFunctions.MoveToNearestNavmeshLocation(s)
			s.SetAngle(0.0, 0.0, a)
			s.SetActorValue("Health", health)
			s.RestoreActorValue("Health", 100000.0)
			s.SetPlayerTeammate(true)
			SummonArt.Play(s, 2.0)
			LegionList.AddForm(s)
		EndIf
		i += 1
	EndWhile
EndEvent
