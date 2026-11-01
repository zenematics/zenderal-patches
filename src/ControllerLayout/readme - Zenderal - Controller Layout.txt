Zenderal - Controller Layout
============================

The list's whole controller layout in ONE mod. Tick it on and it wins; untick it and the list
falls back to Zenderal - Input Defaults / Complete Controller Setup exactly as before.

INSTALL: give it the HIGHEST priority of every input mod in MO2's left pane (lowest in the
list), i.e. above Zenderal - Input Defaults, Complete Controller Setup, Gamepad++ and
Zenderal - Settings. Enable "Zenderal - Controller Layout.esp" (ESL, masters only Skyrim.esm).

Works on an existing save: about 15 s after loading (out of menus) it writes the save-stored
parts. Check Papyrus.0.log for "[ZEN_ControllerLayout] layout v7 applied".


CONTROLLER
----------
  Left stick / Right stick   Move / Look
  LB / RB                    Left / Right hand attack and block
  LT                         Parry (Dual Wield Parrying)
  RT                         Power attack (ZenOCPASecondKey)
  A                          Activate
  A + LB / A + RB            Draw-sheathe weapon / Shout-power
  B                          Sprint; tap B to dodge (TK Dodge)
  X                          Wheeler
  Y                          Jump
  L3 / R3                    Sneak / Toggle view
  Start / Back               Journal / Tween menu
  B + Back                   Favourites
  B + Start                  Wait
  B + D-pad Up               Hero Menu
  B + D-pad Right/Left/Down  Inventory / Magic / Map

  D-pad    tap                 double-tap          A + tap         hold (weapon drawn)
  Up       favourite hotkey 2  Magicka potion      -               High stance
  Right    favourite hotkey 3  Stamina potion      Call horse      Mid stance
  Down     favourite hotkey 4  -                   -               Low stance
  Left     favourite hotkey 1  Health potion       Quick Light     Neutral stance

  Every D-pad press also uses that favourites slot, including the first press of a
  double-tap or hold.
  A + tap: hold A, tap the D-pad, and keep A held a moment (~0.3 s) - Gamepad++ only counts
  the combo if A is still down when it decides the tap.
  Potions are Swift Potion's hotkeys. Quick Light has no hold-Activate trigger (switched off).

  Inside Wheeler (X):
    D-pad Left / Right       previous / next item
    D-pad Up / Down          move entry back / forward
    LT / RT                  previous / next wheel
    RB / LB                  use with right / left hand
    Y / A                    add wheel / add empty slot
    L3 / R3                  move wheel back / forward
    B                        exit

  Menus:
    A / B                    accept / back
    RB / LB                  equip right / left
    L3                       drop
    R3                       inspect item; flips sort order in item lists
    LT / RT                  sort column; map zoom


KEYBOARD AND MOUSE
------------------
  W A S D                    Move
  Left / Right click         Right / Left hand attack and block
  Mouse 4                    Power attack
  Mouse 5                    Parry
  Left Alt                   Dodge (tapping Shift also dodges)
  E / R                      Activate / Draw weapon
  Left Shift / Space / LCtrl Sprint / Jump / Sneak
  Caps Lock / .              Always run / Auto-move
  Z / X                      Toggle view / Shout
  Tab / Esc                  Tween menu / Pause
  I / F / J / M              Inventory / Favourites / Journal / Map
  T                          Wait
  H                          Hero Menu
  1-8                        Favourite hotkeys (1-4 are also the D-pad taps)
  F1 / F2 / F3 / F4          High / mid / low / neutral stance
  K                          Quick Light (lantern on the hip by default; style in its MCM)
  Left / Up / Right arrow    Health / Magicka / Stamina potion (Swift Potion)
  L                          Call horse (once you own the horse flute)
  Y                          Meditate (once you have the ability)
  Q                          Wheeler
  U                          Ammo Wheel (Wheeler)
  B                          Helmet toggle
  V                          Hide the whole UI
  '                          Compass toggle (No Compass In Dialogue)
  Shift + mouse wheel        Cycle targets (Better Third Person Selection)
  F7                         SKSE Menu Framework
  F5 / Pause                 Quicksave / Quickload
  ~                          Console

  Gaps and clashes:
    - No keyboard Quick Magic key (unbound); open Magic through Tab.
    - H is also the keyboard Quick Stats key and Theo's Render Pipeline's overlay toggle
      (ToggleOverlay=0x23). In practice it opens the Hero Menu.
    - keybinds.json still lists a lantern key, but no lantern mod is installed.
    - The Ammo Wheel has no controller button (keyboard U only).


WHAT IS IN HERE
---------------
Loose files (win by MO2 priority):
  Interface\Controls\PC\controlmap.txt     CCS layout; Quick Stats + Auto-Move pad combos unbound;
                                           Back = Tween, B+Back = Favourites, B+Start = Wait
  ControlMap_Custom.txt                    keyboard binds + gamepad block (same Tween/Wait)
  MCM\Settings\OCPA.ini                    power attack = Mouse 4 (259); RT is
                                           Patch Collection's ZenOCPASecondKey (281)
  MCM\Settings\keybinds.json               helmet B, UI toggle V (its lantern entry is
                                           stale - no lantern mod is installed)
  MCM\Settings\BetterThirdPersonSelection.ini, MCM\Config\SkyUI_SE\settings.ini
  SKSE\Plugins\dtryKeyUtil\config\custom\Stances.ini   F1-F4 keyboard; pad keys [ \ ; ]
  SKSE\Plugins\wheeler\Controls.ini, AmmoWheel.ini
  SKSE\Plugins\DualWieldParryingSKSE.ini, TK Dodge RE.ini, SKSEMenuFramework.ini
  Gamepad++\Presets\gpp_default_doNotDelete.gppd       same D-pad layout, for Gamepad++'s
                                                       "Restore Default Settings"

Script (ZEN_ControllerLayout) - things other mods keep IN THE SAVE, written once per save:
  - Gamepad++ D-pad gestures and A + D-pad potion combos (the tables above)
  - Quick Light's keyboard key L -> K (L is also Enderal's horse call), hold-Activate trigger off
  - B + D-pad Up opens the Hero Menu (taps H for Enderal's native menu)

Fixed relative to the old setup:
  - Holding D-pad Right no longer toggles the compass. The mid stance used the ' key, which is
    also No Compass In Dialogue's toggle key; it now uses \.
  - Double-tap D-pad Left toggles Quick Light without also calling your horse (both were on L).
  - Double-tap D-pad Right opens the Hero Menu again (Input Defaults had changed it to K, which
    does nothing), and B now closes it.

Known, left alone:
  - Keyboard L calls your horse (Enderal's own default mount key).
  - A D-pad tap always uses that favourites slot, including the first tap of a double-tap or hold.
  - Turning this mod OFF does not undo the save-stored parts; Gamepad++ MCM -> Presets & Info ->
    Restore Default Settings goes back to whichever preset then wins.
  - Changes you make later in the Gamepad++ / Quick Light MCMs stick; the script only writes once.
