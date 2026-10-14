# ControllerTweaks

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ControllerTweaks/`
- **Ships:** *(no plugin — three file overrides)*
- **FormID block:** _(none)_

## What it does

**The repo's first release that ships NO plugin but DOES ship a script**, and its first fork of an **Enderal** script rather than a third-party one. Adapts the Complete Controller Setup stack to Enderal, and **must sort above `Complete Controller Setup` and `Vel'dun UI Enderal Default`** to win the file conflicts. (1) `Interface\Controls\PC\controlmap.txt` — CCS 5.3.5's, `Quick Stats` gamepad combo (B+DpadUp, `0x2000+0x0001`) unbound to `0xff`; it opened Skyrim's vanilla perk starfield, a UI Enderal never uses. (2) `interface\skyui\config.txt` — forked from **Vel'dun UI Enderal Default's** copy (re-forked 2026-10-12: the earlier fork of Dear Diary Dark Mode's, no longer in the list, silently replaced Vel'dun's whole list layout and colours), `[Input]` gamepad sort bindings moved off CCS's equip/drop buttons: `prevColumn` 274→280 (LT), `nextColumn` 275→281 (RT), `sortOrder` 272→273 (R3), so RB-equip and L3-drop stop re-sorting the item list. (3) `Scripts\_00E_Game_SkillmenuSC.pex` — SureAI's script recompiled with four `; ZP` additions binding **B + D-pad-Up → open Hero Menu, B → close**; see the controller gotcha below for why the chord cannot live in Gamepad++. **Also carries Hero Menu Enhanced's data fill (2026-10-14):** HME's `EnderalHeroMenu.dll` opens the Hero Menu natively from the tween menu's "Skills" (and Quick Stats), bypassing `OpenSkillmenu()`; HME's own copy of this script fills the menu from `OnMenuOpen("00E_heromenu")`. Ours outranks HME's, so until then the tween route opened an **empty** Hero Menu (the H key worked — it fills the menu itself). Now `RegisterForMenu("00E_heromenu")` in `OnInit` + `OnPlayerLoadGame` (existing saves pick it up on load) and HME's `OnMenuOpen` handler, minus its `Debug.Notification("HeroMenuOpen!")`. Compiled against `papyrus-source/vanilla-stubs/` (no vanilla source on this machine), so the disassembly was diffed against the 13 Oct real-source build: identical apart from the new handler/registrations and int→float constant folding; the `_00E_Game_MenuIMOD` `Apply(1.0)`/`Remove()` calls match. **Must keep outranking HME** — and if HME is ever removed, the tween route stops opening the Hero Menu at all. Setup, required Nexus files and the `bGamepadEnable` INI trap are in [`arch-docs/zenderal-controller-setup.md`](../zenderal-controller-setup.md). **Credit SureAI on any mod page** — this redistributes a modified copy of their script

## `bGamepadEnable`, Gamepad++ and the Hero Menu chord

- **`bGamepadEnable` lives in `[MAIN]` of `EnderalPrefs.ini`, not `[Controls]` — and since 2026-10-13 the list ships
  it `=1` (Alpha 0.5 and 0.5.1; Auto Input Switch 1.1.2, which loads on 1.5.97, switches between mouse and pad).** **[verified in-game 2026-08-16]** The launcher-style `[Controls]` placement is ignored;
  the game-written INI puts the setting in `[MAIN]` (next to `bSaveOn*`/`bCrosshairEnabled`), and
  only a value there takes effect. Bethesda's INI reader is section-scoped, so a right-named key in
  the wrong section fails silently. Three companion facts from the same diagnosis: (1) the **live**
  INI is the MO2 profile's copy (`profiles/<profile>/EnderalPrefs.ini`, `LocalSettings=true`), and it
  wins even through PrivateProfileRedirector — proven by A/B: Documents=0 + profile=1 → pad works;
  (2) engine 1.5.97 is one-input-at-a-time (gamepad mode locks out the mouse and vice versa) — the
  *Auto Input Switch* SKSE mod is the switcher, and its current Nexus build is AE-only, rejected by
  SKSE 2.0.20 as `does not appear to be an SKSE plugin` (no `SKSEPlugin_Query` export — the quick
  binary test for any DLL); a 1.5.97 build exists in the mod's old files / the mod-166519 backport;
  (3) an XInput pad's health is testable outside the game — poll `XInputGetState` slot 0 from
  PowerShell before blaming the game. Controller stack in the list: Complete Controller Setup's
  `controlmap.txt` wins the 3-way conflict (over Gamepad++ and Modern Toggle Walk-Run Fix), and its
  eight required mods are all present. Two follow-up fixes live as in-place edits that a mod
  reinstall reverts: CCS's controlmap has `Quick Stats`' gamepad combo (B+DpadUp) unbound → `0xff`
  (it opened Skyrim's vanilla perk starfield, which Enderal never uses), and **SkyUI's gamepad sort
  bindings are NOT in any MCM — they live in `interface\skyui\config.txt`, whose winning copy is
  Dear Diary Dark Mode's**, edited to CCS's scheme (prevColumn 274→280 LT, nextColumn 275→281 RT,
  sortOrder 272→273 R3) so RB-equip and L3-drop stop re-sorting the item list. Third file in that
  mod: a recompile of **SureAI's `_00E_Game_SkillmenuSC`** binding **B + D-pad-Up → Hero Menu, B →
  close** (four `; ZP`-marked additions: `ZP_iGamepadModifier` 277/B, `ZP_iGamepadOpenKey` 266/D-pad
  Up, a held-flag, an `OnKeyUp` event, two `RegisterForKey` calls, and the chord in the existing
  `OnKeyDown`). **A GAMEPAD CHORD MUST LIVE IN A SCRIPT THAT STAYS REGISTERED — do not route one
  through Gamepad++.** **[verified in-game 2026-08-16, the expensive way]** Gamepad++ *can* emulate
  a keyboard key on a combo (`Input.HoldKey`) and it works in gameplay, but it **goes inert while
  any menu is open**, so nothing it binds can ever *close* a menu — the Hero Menu could only be
  shut with Esc. (Its `OnMenuOpen` guard `if !MenuName == "FavoritesMenu"` *looks* like a
  precedence bug that would keep it live; the observed behaviour says otherwise, so trust the
  test.) Two further reasons the script is the right home: Gamepad++ **stores its bindings IN THE
  SAVE**, reloading its `.gppd` only via MCM → Info → "Reset to Defaults" — so editing that file
  changes nothing in an existing save, and a distributed list would need every user to press it —
  and the script route needs no MCM step at all. If you ever do edit a `.gppd`, note its JSON order
  is **[single, double, triple, LONG press] per D-pad direction**, not the Papyrus array's index
  order (`i*4 + iMultiTap`) — read `gpp_mcm_combo_one.psc`'s `saveData()` first. Enderal's other
  script hotkeys (Meditate, Phasmalist teleport, Horseflute) are listed in `_00e_enderalmcm.psc`
  and can take the same treatment; **`_00E_Game_SkillmenuSC` compiles clean from SureAI's source**
  with the standard three-tree `-i` order, and `UIExtensions`/`UIListMenu` are already inside
  `reference/base/EnderalScripts`. Note there is **no free gamepad button** left in this layout to
  bind Enderal's MCM hero-menu key to instead: X is Wheeler's `toggleWheel`, LT is Dual Wield
  Parrying, and the four D-pad long-presses are Stances (`[ ] ; '` = 26/27/39/40). Also: CCS ships
  its own `gpp_keyhandler.pex`/`gpp_mcm_*.pex` that **override Gamepad++'s** — diffing the `.pex`
  string tables shows the only change is the version-nag `Debug.MessageBox` calls stripped, so
  Gamepad++'s `.psc` source is still accurate for reading. **`.pex` is BIG-ENDIAN** — a
  little-endian string-table reader fails immediately.
