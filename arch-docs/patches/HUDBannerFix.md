# HUDBannerFix

- **Source:** `src/HUDBannerFix/tools/01-build-hud-banner-fix.py` (generator; nothing else committed)
- **Ships:** MO2 mod `Zenderal - HUD Banner Fix`: `Interface/hudmenu.swf`, Vel'dun UI's HUD with one class patched.
  Generated from the user's own install, not committed (Vel'dun's work). **Must outrank `Zenderal - Aspect Layout`**
  (the winning `hudmenu.swf` today; MO2: above it in the left pane's priority, i.e. lower in the list). Wabbajack:
  `NoMatchInclude` in `Zenderal.compiler_settings` (added 2026-11-11).
- **FormID block:** none
- **Status:** built 2026-11-11, **not yet enabled** (MO2 was open). Unverified in game.

## Why

Player report (iDeeSign, 2026-11-11): a small dark sliver stayed on screen, right of centre, after a shout-type talent
was learned. The curator's diagnosis: it happens when a menu is opened right after the banner. Loading a save did not
clear it; relaunching did. Prophecy grants 7 shout talents since 2026-11-05, so the banner now plays far more often
(`ZP_ProphecyMenu.Give`: `Game.TeachWord` + `Game.UnlockWord`, as Enderal's own talents do).

The winning `hudmenu.swf` is Aspect Layout's static copy of the Vel'dun Zenderal patches' HUD (md5
`222ae750…`, identical in all three layouts). Read with FFDec 26.4.0 (`tools.json` `ffdec`):

- Vel'dun rewrote `QuestNotification`: SkyUI/vanilla animate the banner as per-letter clips (`AnimatedLetter`,
  restarted after menus by `RestartAnimations`). Vel'dun empties `RestartAnimations` and draws the banner as two
  tweened pieces instead:
  - **the strip** (`AnimStrip`, a 9-slice dark bar with `Background` + `Mask`): `ShowQuestText` tweens both widths
    0 → W over 0.5 s; 3 s later `HideQuestText` tweens them back to 0; 0.5 s later `KillQuestText` sets
    `_visible = false`;
  - **the shout text** (`ShoutTextInstance.ShoutText`: `textField`, `textFieldGlow`, `Mask`): `ShowShoutText` slides
    the mask's `_x` from −W to 0 over 1 s; 2 s later `HideShoutText` slides it 0 → W over 0.5 s.
- Nothing checks the end state. A hide that stops short leaves part of the banner visible. For the shout text that is
  the right end of the last letter, right of centre, as in the screenshots. The HUD movie lives until the game exits.
- **Which timer a menu breaks was not traced.** The fix does not depend on it.

## The fix

A watchdog inside `QuestNotification`, nothing else:

- Each show records a deadline:
  - the strip: show + 0.5 + 3 + 0.5 s, plus 2 s;
  - the shout text: show + 1 + 2 + 0.5 s, plus 2 s.
- A 0.5 s interval, started in the constructor, checks the deadlines. Once one has passed:
  - for the shout text, both texts are emptied and the mask moved off;
  - for the strip, `AnimStrip._visible = false`.
- A banner that hides normally is already hidden by then, so nothing changes for it. The next show resets everything
  as before (`ResetShoutTextMask`, `SetText`, `_visible = true`).
- `AnimationCount`, sounds, objectives and the level meter are not touched.

The generator:

1. asserts the source md5;
2. decompiles the class, applies 5 text edits, each asserted to match once;
3. recompiles it with FFDec's AS2 compiler (`-replace`, class path `\__Packages\QuestNotification`);
4. re-exports both SWFs and asserts that the other 108 scripts are byte-identical in P-code and that the class has
   the watchdog.

The decompiled diff of the class (checked 2026-11-11) shows only the additions.

## Upkeep

Rerun `python -I src/HUDBannerFix/tools/01-build-hud-banner-fix.py` after a Vel'dun UI or Vel'dun patch update. If the
md5 check fails, re-read `QuestNotification` and update `SRC_MD5` and the edits. If Aspect Layout ever stops shipping
`hudmenu.swf`, point `SRC` at the new winner.

## To verify in game

Learn a shout talent in the Prophecy menu (or `player.teachword` + `unlockword`), then open the inventory or map
straight away, and close it: within a few seconds no sliver remains. A normal banner (quest update, level up) shows
and hides as before.
