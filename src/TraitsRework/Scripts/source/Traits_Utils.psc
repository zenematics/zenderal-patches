ScriptName Traits_Utils Hidden

; ZP: Biggie Traits' own Traits_Utils (Biggie Traits - Enderal Conversion/Source/Scripts), with the two
; functions the trait menu needs moved from Traits.dll into Papyrus. Traits.dll is an old CommonLibVR/NG
; build that can't read the 1.7.104 address library, so it is hidden and its natives are unbound. The menu
; then opens empty. Everything else stays native, exactly as upstream. No properties, so the loose-script
; swap is save-safe.

; skill books no longer teach skills
Function StripSkillTeachingFromAllBooks() Global Native

; skill books will teach skills again
Function RevertStripSkillTeaching() Global Native

; utilities for rendering B612_TraitsMenu
; ZP: was native. Fills the menu the caller already opened (b612.GetTraitsMenu() in
; Traits_QuestScript.ShowTraitsMenu) with each list entry's name and description (SPEL DESC, read through
; powerofthree's Papyrus Extender). The image path is Traits.dll's own convention, "TraitPics/<EditorID>.dds"
; under Interface/ (EditorIDs come from powerofthree's Tweaks' cache). Traits without a file show no picture.
Function PopulateTraitsList(FormList akList) Global
    b612_TraitsMenu menu = Game.GetFormFromFile(0x803, "b612.esp") as b612_TraitsMenu
    If ! menu || ! akList
        Debug.Trace("[Zenderal - Traits] PopulateTraitsList: menu or list missing")
        Return
    EndIf
    Int i = 0
    Int size = akList.GetSize()
    While i < size
        Spell trait = akList.GetAt(i) as Spell
        If trait
            String image = ""
            String editorId = PO3_SKSEFunctions.GetFormEditorID(trait)
            If editorId
                image = "TraitPics/" + editorId + ".dds"
            EndIf
            menu.AddItem(trait.GetName(), PO3_SKSEFunctions.GetDescription(trait), image)
        Else
            ; keep indexes aligned with the list for GetTraitsAtIndexes
            menu.AddItem("", "", "")
        EndIf
        i += 1
    EndWhile
EndFunction

; ZP: was native. The menu returns the picked rows as indexes into the list that PopulateTraitsList walked.
; Papyrus can't size a Spell[] at runtime, so the result comes from a literal-size ladder; Biggie's MCM caps
; picks at 5 (iMaxTraits:Main slider max).
Spell[] Function GetTraitsAtIndexes(FormList akList, String[] aiIndexes) Global
    If ! akList || ! aiIndexes
        Return NewSpellArray(0)
    EndIf
    Int count = 0
    Int i = 0
    While i < aiIndexes.Length
        If akList.GetAt(aiIndexes[i] as Int) as Spell
            count += 1
        EndIf
        i += 1
    EndWhile
    If count > 5
        Debug.Trace("[Zenderal - Traits] GetTraitsAtIndexes: " + count + " picks, keeping the first 5")
        count = 5
    EndIf
    Spell[] result = NewSpellArray(count)
    Int n = 0
    i = 0
    While i < aiIndexes.Length && n < count
        Spell trait = akList.GetAt(aiIndexes[i] as Int) as Spell
        If trait
            result[n] = trait
            n += 1
        EndIf
        i += 1
    EndWhile
    Return result
EndFunction

Spell[] Function NewSpellArray(Int aiSize) Global
    If aiSize == 1
        Return new Spell[1]
    ElseIf aiSize == 2
        Return new Spell[2]
    ElseIf aiSize == 3
        Return new Spell[3]
    ElseIf aiSize == 4
        Return new Spell[4]
    ElseIf aiSize == 5
        Return new Spell[5]
    EndIf
    Spell[] empty
    Return empty
EndFunction

Function InjectMasterofOne(Int hotkey) Global Native
Int Function GetCurrentSkillInStatsMenu() Global Native

Spell[] Function GetAllSpells(String asSkill = "", Int aiMinSkill = -1, String asCompare = "=", Int aiLimit = 0, FormList akExcludeList = None) Global Native

Book[] Function GetAllSpellBooks(String asSkill = "", Int aiMinSkill = -1, String asCompare = "=", Int aiLimit = 0, FormList akExcludeList = None) Global Native

Perk[] Function GetAllPerks(Int aiSkill) Global Native

Book[] Function GetSpellBooksWithKeyword(Keyword akKeyword, String asSkill, Int aiMinSkill, String asCompare = "=", Int aiLimit = 0) Global Native

Spell[] Function GetSpellsWithKeyword(Keyword akKeyword, String asSkill, Int aiMinSkill, String asCompare = "=", Int aiLimit = 0) Global Native
