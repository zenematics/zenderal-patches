Scriptname Kata_Enderal_SpellPackageAddToLLists extends Quest

; ---------------------------------------------------------------------------
; ZENDERAL PATCH - "Zenderal - Kata Fixes"
; (formerly shipped alone as "Zenderal - No Kata Debug Prompt")
;
; Original script by KataPUMB, shipped with "KataPUMB Spell Package"
; (Nexus / Enderal SE mod 47, KataPUMB_SpellPackage.esp). Redistributed here
; MODIFIED, as a loose Scripts/ override of the author's own loose .pex.
;
; TWO changes from the author's source:
;
; 1) DEDUPE - 58 AddForm lines below are commented out with ";ZP-DEDUPE".
;    They injected the 29 spell lines this pack shares with KataPUMBSpellPack
;    (Death Beam, Death Mantle, Fire/Frost/Shock Nova, Holy Cross, Holy Ray,
;    Lightborn Recital) into the vendor/loot lists - giving the player two
;    same-named copies of each spell, and bypassing the EGO rebalance that
;    only covers pack 1's copies. The books, spells and this pack's UNIQUE
;    lines are untouched; only the duplicates' distribution is suppressed.
;    The injection is Books.GetAt(<index>) with hardcoded indices, so this
;    script is the ONLY place it can be fixed - editing the FormList would
;    shift every index and scramble the rest of the distribution.
;    NOTE: the quest is StartGameEnabled + RunOnce - saves where it already
;    ran keep their injected duplicates; this bites on new games.
;
; 2) In the original, OnInit() opens a message box on every new game:
;
;     Int msg = DoYouWannaCheat.Show()
;     "Do you want to activate debug mode? (this means everything this mod
;      adds will be added to your inventory in addition to the leveled lists)"
;
; Show() blocks the new-game sequence on a modal prompt that is a debugging
; aid, not a player-facing option. This copy hardcodes the "No" answer:
;
;     Int msg = 1
;
; Everything else - the property list, the non-duplicate injections below -
; is byte-for-byte the author's. The DoYouWannaCheat property is deliberately
; left DECLARED even though it is now unused: the quest record's VMAD still
; stores a value for it (007182:KataPUMB_SpellPackage.esp), and removing the
; declaration would make Papyrus log an unresolved-property warning on load.
;
; The debug branch is left in place rather than deleted so this file still
; diffs cleanly against the author's source. It is simply never taken.
;
; Load AFTER "KataPUMB Magic Package" in MO2's mod order, or the author's .pex
; wins the file conflict and the prompt comes back.
; ---------------------------------------------------------------------------

FormList Property Armors Auto
FormList Property Books Auto
FormList Property CraftingPlanes Auto
LeveledItem[] Property SpellTomesLI  Auto  
LeveledItem[] Property ArmorLI  Auto  
LeveledItem[] Property CraftingPlanesLI Auto

Message Property DoYouWannaCheat Auto

Actor Player

;CraftingPlans
;0 A
;1 B
;2 C

;SpellTomes
;0 Loot A
;1 Trader A
;2 Loot B
;3 Trader B
;4 Loot C
;5 Trader C
;6 Loot D
;7 Trader D

Event OnInit()
	; ZENDERAL: was `Int msg = DoYouWannaCheat.Show()`. 1 = the "No" button, so
	; the debug-inventory branch below is skipped and no prompt is ever shown.
	Int msg = 1
	Player = Game.GetPlayer()
	Int i = 0

	If msg == 0
		While i<Armors.GetSize()
			Player.AddItem(Armors.GetAt(i) as Armor)
			i+=1
		EndWhile
		i=0
		While i<Books.GetSize()
			Player.Additem(Books.GetAt(i) as Book)
			i+=1
		EndWhile
		i=0
		While i<CraftingPlanes.GetSize()
			Player.Additem(CraftingPlanes.GetAt(i) as MiscObject)
			i+=1
		EndWhile
	EndIf


;AmorLI
;0 TraderA
;1 TraderADuplc
;2 DraugrShield50
;3 ShieldLight
;4 Lightall
;5 BootsLight
;6 CuirasLight
;7 GauntletsLight
;8 HelmetLight

	;Boots
	ArmorLI[5].AddForm(Armors.GetAt(3), 15, 1)
	ArmorLI[5].AddForm(Armors.GetAt(10), 3, 1)

	;Hood
	ArmorLI[8].AddForm(Armors.GetAt(1), 15, 1)
	ArmorLI[8].AddForm(Armors.GetAt(12), 3, 1)

	;Cuirass
	ArmorLI[6].AddForm(Armors.GetAt(2), 15, 1)
	ArmorLI[6].AddForm(Armors.GetAt(13), 3, 1)

	;Gauntlets
	ArmorLI[7].AddForm(Armors.GetAt(0), 15, 1)
	ArmorLI[7].AddForm(Armors.GetAt(11), 3, 1)
	
	;AllLight
	ArmorLI[4].AddForm(Armors.GetAt(0), 15, 1)
	ArmorLI[4].AddForm(Armors.GetAt(1), 15, 1)
	ArmorLI[4].AddForm(Armors.GetAt(2), 15, 1)
	ArmorLI[4].AddForm(Armors.GetAt(3), 15, 1)
	ArmorLI[4].AddForm(Armors.GetAt(4), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(5), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(6), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(7), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(8), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(9), 20, 1)
	ArmorLI[4].AddForm(Armors.GetAt(10), 3, 1)
	ArmorLI[4].AddForm(Armors.GetAt(11), 3, 1)
	ArmorLI[4].AddForm(Armors.GetAt(12), 3, 1)
	ArmorLI[4].AddForm(Armors.GetAt(13), 3, 1)
	ArmorLI[4].AddForm(Armors.GetAt(14), 6, 1)
	ArmorLI[4].AddForm(Armors.GetAt(15), 6, 1)
	ArmorLI[4].AddForm(Armors.GetAt(16), 6, 1)
	ArmorLI[4].AddForm(Armors.GetAt(17), 6, 1)
	;ArmorLI[4].AddForm(Armors.GetAt(18), 6, 1) MadDestruction
	ArmorLI[4].AddForm(Armors.GetAt(19), 6, 1)
	ArmorLI[4].AddForm(Armors.GetAt(20), 6, 1)

	;TraderA & Duplicate
	i = 0
	int repeat = 0
	int lvl = 1
	While repeat <2
		if i<4
			lvl = 15
		elseIf i>3&&i<10
			lvl=20
		elseIf i>9&&i<14
			lvl=3
		else
			lvl=6
		EndIf
		If i!=18
			ArmorLI[repeat].AddForm(Armors.Getat(i), lvl, 1)
		EndIf
		if i>=20
			i=0;
			repeat+=1;
		else
			i+=1
		EndIf
	EndWhile

	;ShieldLight
	ArmorLI[3].AddForm(Armors.GetAt(4), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(5), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(6), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(7), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(8), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(9), 20, 1)
	ArmorLI[3].AddForm(Armors.GetAt(14), 6, 1)
	ArmorLI[3].AddForm(Armors.GetAt(15), 6, 1)
	ArmorLI[3].AddForm(Armors.GetAt(16), 6, 1)
	ArmorLI[3].AddForm(Armors.GetAt(17), 6, 1)
	ArmorLI[3].AddForm(Armors.GetAt(19), 6, 1)
	ArmorLI[3].AddForm(Armors.GetAt(20), 6, 1)

;CraftingPlans
;0 A
;1 B
;2 C

	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(0), 3, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(1), 3, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(2), 3, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(3), 3, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(4), 6, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(5), 6, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(6), 6, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(7), 6, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(8), 6, 1)
	CraftingPlanesLI[0].AddForm(CraftingPlanes.GetAt(9), 6, 1)

;SpellTomes
;0 Loot A
;1 Trader A
;2 Loot B
;3 Trader B
;4 Loot C
;5 Trader C
;6 Loot D
;7 Trader D

	;DeathBeam
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(0), 1, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(0), 1, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(1), 8, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(1), 8, 1)
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(2), 11, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(2), 11, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(3), 22, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(3), 22, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(4), 33, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(4), 33, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(5), 44, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(5), 44, 1)


	;FireShield Frost Shield & Shockshield
	SpellTomesLI[0].AddForm(Books.GetAt(6), 2, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(11), 3, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(16), 4, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(6), 2, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(11), 3, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(16), 4, 1)

	SpellTomesLI[2].AddForm(Books.GetAt(7), 11, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(12), 11, 1)
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(17), 11, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(7), 11, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(12), 11, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(17), 11, 1)

	SpellTomesLI[4].AddForm(Books.GetAt(8), 24, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(13), 24, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(18), 24, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(8), 24, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(13), 24, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(18), 24, 1)

	SpellTomesLI[6].AddForm(Books.GetAt(9), 33, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(14), 33, 1)
	;ZP-DEDUPE SpellTomesLI[6].AddForm(Books.GetAt(19), 33, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(9), 33, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(14), 33, 1)
	;ZP-DEDUPE SpellTomesLI[7].AddForm(Books.GetAt(19), 33, 1)

	SpellTomesLI[0].AddForm(Books.GetAt(10), 45, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(15), 45, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(20), 45, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(10), 45, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(15), 45, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(20), 45, 1)


	;Holy Cross
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(21), 15, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(21), 15, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(22), 28, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(22), 28, 1)
	;ZP-DEDUPE SpellTomesLI[6].AddForm(Books.GetAt(23), 40, 1)
	;ZP-DEDUPE SpellTomesLI[7].AddForm(Books.GetAt(23), 40, 1)
	
	
	;HolyRay
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(24), 2, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(24), 2, 1)
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(25), 5, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(25), 5, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(26), 11, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(26), 11, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(27), 22, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(27), 22, 1)
	SpellTomesLI[8].AddForm(Books.GetAt(28), 35, 1)
	SpellTomesLI[9].AddForm(Books.GetAt(28), 35, 1)


	;LightBornRecital
	SpellTomesLI[2].AddForm(Books.GetAt(29), 15, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(29), 15, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(30), 28, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(30), 28, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(31), 38, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(31), 38, 1)

	;rechargeStaff
	SpellTomesLI[2].AddForm(Books.GetAt(32), 16, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(32), 16, 1)

	;WhiteMage
	SpellTomesLI[4].AddForm(Books.GetAt(33), 26, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(33), 26, 1)

	;BlackMage
	SpellTomesLI[4].AddForm(Books.GetAt(34), 26, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(34), 26, 1)

	;Teleport
	SpellTomesLI[2].AddForm(Books.GetAt(35), 15, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(35), 15, 1)

	;DeathMantle
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(36), 13, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(36), 13, 1)
	;ZP-DEDUPE SpellTomesLI[6].AddForm(Books.GetAt(37), 44, 1)
	;ZP-DEDUPE SpellTomesLI[7].AddForm(Books.GetAt(37), 44, 1)

	;Mantras
	SpellTomesLI[0].AddForm(Books.GetAt(38), 1, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(38), 1, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(39), 6, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(39), 6, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(40), 12, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(40), 12, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(41), 12, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(41), 12, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(42), 26, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(42), 26, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(43), 26, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(43), 26, 1)

	;MasterTelekinesis
	SpellTomesLI[4].AddForm(Books.GetAt(44), 36, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(44), 36, 1)

	;MindWrack
	SpellTomesLI[0].AddForm(Books.GetAt(45), 1, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(45), 1, 1)
	SpellTomesLI[0].AddForm(Books.GetAt(46), 6, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(46), 6, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(47), 12, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(47), 12, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(48), 18, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(48), 18, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(49), 23, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(49), 23, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(50), 28, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(50), 28, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(51), 36, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(51), 36, 1)

	;Novas
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(52), 2, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(52), 2, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(56), 3, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(56), 3, 1)
	;ZP-DEDUPE SpellTomesLI[0].AddForm(Books.GetAt(60), 5, 1)
	;ZP-DEDUPE SpellTomesLI[1].AddForm(Books.GetAt(60), 5, 1)

	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(53), 9, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(53), 9, 1)
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(57), 10, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(57), 10, 1)
	;ZP-DEDUPE SpellTomesLI[2].AddForm(Books.GetAt(61), 12, 1)
	;ZP-DEDUPE SpellTomesLI[3].AddForm(Books.GetAt(61), 12, 1)

	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(54), 22, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(54), 22, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(58), 24, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(58), 24, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(62), 26, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(62), 26, 1)

	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(55), 32, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(55), 32, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(59), 34, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(59), 34, 1)
	;ZP-DEDUPE SpellTomesLI[4].AddForm(Books.GetAt(63), 36, 1)
	;ZP-DEDUPE SpellTomesLI[5].AddForm(Books.GetAt(63), 36, 1)

	;Entropy Curse
	SpellTomesLI[2].AddForm(Books.GetAt(64), 22, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(64), 22, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(65), 32, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(65), 32, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(66), 42, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(66), 42, 1)

	;Summons
	;Wood Elemental
	SpellTomesLI[2].AddForm(Books.GetAt(67), 20, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(67), 20, 1)

	;Lost Ones
	SpellTomesLI[2].AddForm(Books.GetAt(68), 20, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(68), 20, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(69), 25, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(69), 25, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(70), 30, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(70), 30, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(71), 35, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(71), 35, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(72), 40, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(72), 40, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(73), 50, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(73), 50, 1)

	;Spirits
	SpellTomesLI[0].AddForm(Books.GetAt(73), 10, 1)
	SpellTomesLI[1].AddForm(Books.GetAt(73), 10, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(74), 15, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(74), 15, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(75), 20, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(75), 20, 1)
	SpellTomesLI[2].AddForm(Books.GetAt(76), 25, 1)
	SpellTomesLI[3].AddForm(Books.GetAt(76), 25, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(77), 30, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(77), 30, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(78), 35, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(78), 35, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(79), 40, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(79), 40, 1)
	SpellTomesLI[4].AddForm(Books.GetAt(80), 45, 1)
	SpellTomesLI[5].AddForm(Books.GetAt(80), 45, 1)
	SpellTomesLI[6].AddForm(Books.GetAt(81), 50, 1)
	SpellTomesLI[7].AddForm(Books.GetAt(81), 50, 1)
EndEvent

