Zenderal - Controller Tweaks
============================

Two file overrides adapting the Complete Controller Setup (CCS) stack to Enderal.
This mod must WIN file conflicts against both source mods (place it at higher
priority than Complete Controller Setup and Dear Diary Dark Mode).

1. Interface\Controls\PC\controlmap.txt
   Base: Complete Controller Setup 5.3.5 (Nexus SE 99978)
   Change: "Quick Stats" gamepad combo (B + DpadUp, 0x2000+0x0001) unbound -> 0xff.
   Why: it opened Skyrim's vanilla perk-starfield StatsMenu, which Enderal
   never uses (Enderal's character menu lives in its own journal UI).

2. interface\skyui\config.txt
   Base: Dear Diary Dark Mode (white text) - its copy wins the config.txt
   conflict over SkyUI's, so it is the one that must be forked.
   Changes ([Input] section only, everything else untouched):
     controls.gamepad.prevColumn = 274 -> 280  (LB -> LT)
     controls.gamepad.nextColumn = 275 -> 281  (RB -> RT)
     controls.gamepad.sortOrder  = 272 -> 273  (L3 -> R3)
   Why: CCS's layout puts equip on LB/RB and drop on L3; SkyUI's defaults put
   sort-column switching on LB/RB and sort-order toggle on L3, so equipping or
   dropping an item also re-sorted the item list.

3. Scripts\_00E_Game_SkillmenuSC.pex  (+ Scripts\Source\ .psc)
   Base: SureAI's own source, verbatim, from ScriptsEnderal.zip.
   Gives the B + D-pad-Up combo freed up in file 1 a job: it opens Enderal's
   Hero Menu, and B closes it again.

   Why it has to be done here and not in Gamepad++: Gamepad++ CAN emulate the
   "H" hero-menu key on a combo, but it goes inert while any menu is open, so
   nothing it binds can ever CLOSE the menu (verified in-game - only Esc
   worked). Enderal's own script is already listening for keys the whole time,
   so putting the chord there fixes open and close together, with no MCM
   configuration and nothing stored in the save.

   The four added lines, all marked "; ZP":
     - int ZP_iGamepadModifier   = 277   (SKSE gamepad keycode: B)
     - int ZP_iGamepadOpenKey    = 266   (D-pad Up)
     - bool ZP_bGamepadModifierHeld      (tracks the chord; RegisterForKey
       cannot express a two-button chord on its own)
     - Event OnKeyUp()                   (releases the modifier)
   plus two RegisterForKey calls in UpdateKeyRegistration(), and the chord
   added to the existing OnKeyDown condition. Everything else is byte-for-byte
   SureAI's.

   NO Property declaration was added, removed or renamed - verified by diffing
   the compiled .pex string tables against a build of the pristine script
   (additions: OnKeyUp, the three ZP_ names, fHoldTime, one compiler temp;
   removals: none). That matters because the host plugin stores this script's
   property VALUES in its VMAD and binds them by name.

   Loose scripts beat the copy in E - Misc.bsa, so this wins automatically.
   Deliberately NO Gamepad++ preset ships here any more: if Gamepad++ also
   emitted "H" on the same chord, it would toggle the menu shut the instant
   this script opened it.

MAINTENANCE: all three files are full-file copies with small edits. If Complete
Controller Setup or Dear Diary Dark Mode is updated, re-copy the new file and
re-apply the change described above. If ENDERAL itself is updated, re-apply the
"; ZP" edits to the new _00E_Game_SkillmenuSC.psc and recompile with Enderal's
source tree FIRST on the -i import path.

CREDIT: _00E_Game_SkillmenuSC is SureAI's script, redistributed here in
modified form solely to add gamepad support.
