Zenderal - Controller Layout
============================

The list's whole controller layout in ONE mod. Tick it on and it wins; untick it and the list
falls back to Zenderal - Input Defaults / Complete Controller Setup exactly as before.

INSTALL: give it the HIGHEST priority of every input mod in MO2's left pane (lowest in the
list), i.e. above Zenderal - Input Defaults, Complete Controller Setup, Gamepad++ and
Zenderal - Settings. Enable "Zenderal - Controller Layout.esp" (ESL, masters only Skyrim.esm).

Works on an existing save: about 15 s after loading (out of menus) it writes the save-stored
parts. Check Papyrus.0.log for "[ZEN_ControllerLayout] layout v1 applied".


LAYOUT (gameplay)
-----------------
  Left stick / Right stick   Move / Look
  LB / RB                    Left / Right attack and block
  LT                         Parry (Dual Wield Parrying)
  RT                         Power attack (One Click Power Attack)
  A                          Activate.  Hold A (nothing targeted, 0.5 s) = Quick Light
  A + LB / A + RB            Draw-sheathe weapon / Shout-power
  B                          Sprint; tap B to dodge (TK Dodge)
  X                          Wheeler
  Y                          Jump
  L3 / R3                    Sneak / Toggle view
  Start / Back               Journal / Wait
  B + Back                   Tween menu
  B + Start                  Favourites
  B + D-pad Right/Left/Down  Inventory / Magic / Map

  D-pad        tap                   double-tap        hold
  Up           favourite hotkey 7    -                 High stance
  Right        favourite hotkey 5    Hero Menu         Mid stance
  Down         favourite hotkey 8    -                 Low stance
  Left         favourite hotkey 6    Lantern           Neutral stance

  Hero Menu: B closes it (as do Tab / Esc on the keyboard).
  Menus: LT / RT change the sort column, R3 flips the sort order.


WHAT IS IN HERE
---------------
Loose files (win by MO2 priority):
  Interface\Controls\PC\controlmap.txt     CCS layout; Quick Stats + Auto-Move pad combos unbound
  ControlMap_Custom.txt                    keyboard binds + CCS gamepad block
  MCM\Settings\OCPA.ini                    power attack = RT (281)
  MCM\Settings\keybinds.json               lantern L, helmet B, UI toggle V
  MCM\Settings\BetterThirdPersonSelection.ini, MCM\Config\SkyUI_SE\settings.ini
  SKSE\Plugins\dtryKeyUtil\config\custom\Stances.ini   F1-F4 keyboard; pad keys [ \ ; ]
  SKSE\Plugins\wheeler\Controls.ini, AmmoWheel.ini
  SKSE\Plugins\DualWieldParryingSKSE.ini, TK Dodge RE.ini, SKSEMenuFramework.ini
  Gamepad++\Presets\gpp_default_doNotDelete.gppd       same D-pad layout, for Gamepad++'s
                                                       "Restore Default Settings"

Script (ZEN_ControllerLayout) - things other mods keep IN THE SAVE, written once per save:
  - Gamepad++ D-pad gestures (the table above)
  - Quick Light's keyboard key L -> K, so L lights only the lantern
  - B closes the Hero Menu

Fixed relative to the old setup:
  - Holding D-pad Right no longer toggles the compass. The mid stance used the ' key, which is
    also No Compass In Dialogue's toggle key; it now uses \.
  - Double-tap D-pad Left no longer also fires Quick Light.
  - Double-tap D-pad Right opens the Hero Menu again (Input Defaults had changed it to K, which
    does nothing), and B now closes it.
  - RT power attacks (Input Defaults had OCPA on Mouse 4, leaving RT doing nothing).

Known, left alone:
  - Keyboard L also calls your horse (Enderal's own default mount key), so double-tap Left does
    too once you own the horse flute. Change it in Enderal's MCM if it bothers you.
  - A D-pad tap always uses that favourites slot, including the first tap of a double-tap or hold.
  - Turning this mod OFF does not undo the save-stored parts; Gamepad++ MCM -> Presets & Info ->
    Restore Default Settings goes back to whichever preset then wins.
  - Changes you make later in the Gamepad++ / Quick Light MCMs stick; the script only writes once.
