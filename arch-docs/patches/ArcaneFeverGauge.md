# ArcaneFeverGauge

- **Source:** `src/ArcaneFeverGauge/`:
  - `ArcaneFeverGaugeESP/`: one quest.
  - `Scripts/source/ZFG_ArcaneFeverWidget.psc`, compiled `.pex`.
  - `widget/arcanefever.as`: the widget's ActionScript, our own code.
  - `tools/01-build-widget.py`: builds the `.swf`.
  - `tools/02-preview.py`: a Ruffle preview page.
  - `data/Interface/exported/widgets/zenderal/arcanefever.swf`: built, but **committed**, because CI has no FFDec.
- **Ships:** MO2 mod `Zenderal - Arcane Fever Gauge`, made of:
  - `Zenderal - Arcane Fever Gauge.esp` (ESL, HEDR 1.7, masters Skyrim/Update/FS only);
  - `Scripts/ZFG_ArcaneFeverWidget.pex` and `ZFG_ArcaneFeverMCM.pex`, plus their source;
  - `Interface/exported/widgets/zenderal/arcanefever.swf`;
  - `MCM/Config/Zenderal - Arcane Fever Gauge/config.json` + `settings.ini` (the MCM page and its defaults).

  `Scripts/stubs/` holds MCM Helper's public API (`MCM.psc`, `MCM_ConfigBase.psc`, Exit-9B/MCM-Helper, MIT) for
  compiling only; it never ships.

  Wabbajack: `NoMatchInclude` in `Zenderal.compiler_settings` (added 2026-11-12).
- **FormID block:** `0x800–0x801`: quest `ZFG_ArcaneFeverGauge` (the gauge) and `ZFG_ArcaneFeverGaugeMCM` (its MCM page).
- **Status:**
  - Build 1 (2026-11-12): the gauge drew and filled in game (curator), but in the wrong place (see below).
  - Build 2 (same day) sits next to TrueHUD's bars: verified in game ("aligned perfectly").
  - Build 3 (same day): `GapK` 0.24 → 0.05, 2 mm closer on the curator's word.
  - Build 4 (same day): "a lot closer, but not touching". The widget now measures the visible arrow tips, and
    `GapK` is 0.15, about 0.1 × the block height of clear space. "Looks ok" (curator).
  - Build 5 (same day): MCM page (hotkey, hide, fade after N s). Fade tested in a Ruffle harness; **the MCM page and
    hotkey are unverified in game**.

## Why

Curator's request (2026-11-12): Arcane Fever as a HUD gauge in the Vel'dun style, to the right of the Health and Mana
bars. The style reference was a ChatGPT mock-up, not an existing element: a dark disc, a thin gold ring with diamond
points, a purple arc and a symbol in the middle. A search found no existing Arcane Fever widget, either in the list
or on Nexus.

## How it works

**The value.** Enderal stores the fever as the negative of actor value `LastFlattered` (0 down to −100). Every
SureAI script that shows it reads `-GetActorValue("LastFlattered")`: `_00E_ArkanistenfieberEffect`,
`_00E_HeroMenuAlias` (`SkillmenuFloats[6]`), `_00E_EPUpdateFunctions`, and the potion and Ambrosia scripts.

**No DLL.** Enderal ships SkyUI, including its widget framework: `SKI_WidgetManager`, `SKI_WidgetBase`, and
`interface/exported/skyui/widgetloader.swf` in `SkyUI_SE.bsa`. The setup is SkyUI's standard widget pattern:

- Quest `0x800` is `StartGameEnabled`.
- Its player alias (forced `000014`) runs `SKI_PlayerLoadGameAlias`, so the widget reloads on every load.
- The quest script `ZFG_ArcaneFeverWidget` extends `SKI_WidgetBase`. It returns `zenderal/arcanefever.swf`, which
  SkyUI loads from `Interface/exported/widgets/`; the loader sits under `exported/`, so its root path is `exported/`.
- Every `UpdateInterval` (0.25 s) the script reads the fever and calls `setFever` on both copies (see below), only
  when the value has changed (rounded to 0.1). The loop starts in `OnGameReload`, not in SkyUI's `OnWidgetReset`,
  because the TrueHUD copy does not need SkyUI.
- Its modes are the bars' own (`HUDMenu.SetModes`): All, StealthMode, Swimming, HorseMode, WarHorseMode.

**The visible bars are TrueHUD's, not the HUD's.** The first build followed Vel'dun's HUD bars and appeared
near the top of the screen, right of nothing (curator's screenshot, 2026-11-12). The list's `TrueHUD.ini` (from
Aspect Layout, same in all three layouts) has `bPlayerWidgetHideVanillaBars=1` and
`bPlayerWidgetForceHideVanillaBars=1`, so the bottom-left bars are TrueHUD's player widget in Vel'dun's TrueHUD skin.
The HUD's own `Health`/`Magica` clips are hidden. They still sit where `skyhud.txt` puts them (`fHealthPosY=30` plus
the HUD root at (616.65, 475.45), y ≈ 59 of 720), which is exactly where that first gauge landed. Two copies of the
movie now run:

- **The TrueHUD copy.** The script loads this one itself. Once menu `TrueHUD` is open, it calls `createEmptyMovieClip`
  (`ZFG_ArcaneFeverGauge`, depth 16000) and then `loadMovie` (`exported/widgets/zenderal/arcanefever.swf`) on
  `_root.TrueHUD.TrueHUD_MainVisibilityWidgets`, the container TrueHUD attaches `TrueHUD_PlayerWidget` to (TrueHUD.swf's
  `HUD.TrueHUD.AddPlayerWidget`). It is checked once a second and loaded again if TrueHUD rebuilds its movie, up to 5
  tries a session.
  - **Placement:** the movie sees `_root.TrueHUD` (no `_lockroot` in either TrueHUD movie). It unites the visible
    corners of `playerWidget.Health/Magicka/Stamina` and sits right of that block, vertically centred. So it follows
    any TrueHUD position, scale and bar width.
    - **The visible tip is not the frame's bounds.** Each bar's `Frame` is Vel'dun's `LargeBarFrame`
      (`TrueHUD_Assets0.swf`): a scale-9 sprite whose shape spans x −69..69 around a −50..50 centre.
      `TrueHUD_Bar` sizes it to bar + 38 (`fFrameWidthOffset` = 138 − 100), so a fixed 19-unit cap sits past each
      bar end.
    - Rendered at 4×, the shape is drawn only to ±59.5 (alpha > 8; y is full height). So the arrow tip is
      `FRAME_PAD` = 9.5 units inside the bounds. That pad is in the bar's own space whatever the width, because the
      cap is scale-9.
    - The widget takes the Frame's bounds in bar space, moves each corner in by the pad, and converts those points.
    - Build 2–3 used the raw `Frame`/`Outline` bounds. On the curator's 1440p screenshot that left a 29 px gap where
      the model predicts about 22 px; the remaining ~7 px is unexplained, and is within measuring error on a
      downscaled image. The log line gives the measured `bars right/top/bottom` to settle it.
    - Another TrueHUD skin would need its own pad; bars without a `Frame` count by their whole bounds.
  - **Visibility:** it shows and fades with the player widget (its alpha × the most visible bar's), and its container
    hides it with TrueHUD's own visibility mode. The bar modes are 4 (always on; TrueHUD fades only modes 1–3).
  - **Tested:** in Ruffle with a harness that builds TrueHUD's structure: placed right of the block, and a wide
    invisible child inside each bar is ignored.
- **The HUD copy.** SkyUI's widget, as below. The script hides it (`setSuppressed`) while the TrueHUD copy reports
  `active` (player widget found), so it only shows when TrueHUD or its player widget is off.

**The HUD copy follows Vel'dun's own bars.** Every 20 frames it finds two corners of Vel'dun's bar frame:

- **The frame:** shape 758 in Vel'dun's `hudmenu.swf`, the dark body with the arrow-tipped border.
- **Health's top-right corner** in `HUDMovieBaseInstance.Health.HealthMeter_mc`: the shape is placed at
  (−123.6, 0), scale 0.6726/0.6718, so the corner is (142.69, −37.35).
- **Mana's bottom-right corner** in `HUDMovieBaseInstance.Magica.MagickaMeter_mc`: placed at (0.4, 1.7), unscaled,
  so the corner is (396.3, −24.5).
- The shape's bounds are x −28.3..395.9, y −55.6..−26.2.

`localToGlobal` takes both corners into the widget holder's space. Let `h` be the bar block's height (Health top to
Mana bottom). Then:

- radius = `RadiusK` × `h` (default 0.64);
- left gap = `GapK` × `h`, from the bars' right end to the gauge's centre minus its radius (0.15; see "Tuning");
- centre = halfway between Health top and Mana bottom, plus `OffsetX` / `OffsetY` × `h`.

So the gauge follows any `skyhud.txt` position, bar scale and aspect layout. A plain `getBounds` would be wrong:
each meter clip also holds a 633-unit mask (shape 433, the green strip in FFDec) wider than the frame. If the bar
clips are missing (another HUD), the widget falls back to the Papyrus `X`/`Y` (1280×720 units, SkyUI's mapping) at
radius 30. Each new placement is logged to `skse64.log`:

```
Zenderal Arcane Fever Gauge: placed at x,y rR
```

**The HUD copy's visibility follows Vel'dun's bars.** It hides when `Health` and `Magica` are both hidden, when the
HUD is hidden, or when the script suppresses it. Its alpha is the HUD's alpha × the bars' alpha (clip × meter). The
list ships `uPersistentMeter=1`, so Vel'dun's bars stay at 100 whenever they are shown.

**The look.** Colours are read from Vel'dun's frame shape: fills only, frame `#7D7767`, body (29,26,23) and
(35,31,32) at 60%.

- **Ring:** an outer ring in the frame colour with four diamond points, outlined like the bar tips, and a hairline
  inner ring.
- **Arc:** a dark channel (`#241D38`, 45%) and the arc `#7A5CE0` over a soft glow, with a light leading edge
  `#C2B0FF`. It fills clockwise from the top.
- **Symbol:** a flame loop over curled arms and a tapering blade, cream `#CFC3A6`. A lavender copy over it fades in
  with the fever (55% at 100).
- **Feedback:** a rise flashes the arc (55% alpha, about 0.45 s), and from 80 fever the arc pulses. The arc eases to
  each new value.

Every shape comes from the drawing API: filled polygons, plus line strokes for the symbol. Nothing sits on the timeline.

## The build

`python -I src/ArcaneFeverGauge/tools/01-build-widget.py`:

1. Writes a one-frame SWF 8 skeleton: FileAttributes, background, an empty DoAction, ShowFrame.
2. Runs FFDec's `-importScript` with `widget/arcanefever.as` as `frame_1/DoAction.as`.
3. Decompiles the result and asserts that every function name SkyUI and the Papyrus script call is in it, and that
   it is still SWF 8 with one frame.

A failure in FFDec's output stops the build.

**Preview:** `python -I src/ArcaneFeverGauge/tools/02-preview.py <out.html> [size]` writes a page that runs the movie
in Ruffle (pinned `0.8.0-nightly.2026.10.25`, from unpkg). Without a HUD, the movie centres itself and steps the
fever 0 → 100 every 2 s. Serve the page over http (the browser pane only shows a static snapshot of a `file://` page
outside the project). Ruffle is not Scaleform: it checks the drawing, not the HUD placement or SkyUI's calls.

## Tuning

**Layout:** `RadiusK`, `GapK`, `OffsetX` and `OffsetY` are `AutoReadOnly` constants in `ZFG_ArcaneFeverWidget.psc`,
all shares of the bar block's height `h`. Change them there and recompile. They are not `Auto` properties on
purpose: a save keeps an `Auto` property's value, so a new default (or a plugin VMAD value) never reaches a game
already running the quest. The script sends them to both copies on every load.

**Gap history (curator, 2026-11-12):**
- Build 2 had `GapK` 0.24 and was "aligned perfectly", but the curator asked for 2 mm closer.
- On their 1440p screen the block was about 46 px tall, and the visible gap from the bar tips to the ring's left
  diamond was about 33 px. So TrueHUD's measured right end (`Frame`/`Outline` bounds) reaches roughly 24 px past the
  visible tips.
- 2 mm is about 8.6 px on a typical 34" ultrawide (0.19 × `h`), so build 3 set `GapK` to 0.05.
- Then "a lot closer, but not touching". Build 4 measures the visible tips, where the left diamond reaches
  0.08 × radius past the radius. The gap you see is (`GapK` − 0.051) × `h`, so `GapK` 0.15 leaves about
  0.1 × `h` (about 5 px at 1440p), unverified.

**Look:** colours and shapes live in `widget/arcanefever.as`. Edit it, rerun `tools/01`, recommit the `.swf`.

## Settings (MCM)

The curator chose an MCM page over an SKSE Menu Framework page. SMF 3.18 only takes pages from a C++ plugin; MCM
Helper (already in the list) needs no DLL.

- **The page:** `Mod Configuration → Arcane Fever Gauge`, defined in MCM Helper's `config.json` (one page). Values
  are MCM Helper mod settings; `modName` = the plugin name, so `MCM.GetModSetting*("Zenderal - Arcane Fever Gauge",
  "<name>:General")`. Defaults come from `settings.ini` next to it, and a player's changes go to
  `MCM/Settings/Zenderal - Arcane Fever Gauge.ini` (MO2's overwrite unless a mod ships one: that is where a list
  default would go, e.g. in `Zenderal - Settings`).

  | Setting | Default | Effect |
  |---|---|---|
  | `iToggleKey` (keymap) | −1, unbound | The show/hide hotkey |
  | `bHidden` (toggle) | 0 | Gauge hidden. The hotkey writes it back, so it holds across saves and the MCM shows it |
  | `bAutoFade` (toggle) | 0 | Fade out once the fever has not changed for `fFadeDelay` s |
  | `fFadeDelay` (slider 1–30) | 5 | Seconds before the fade, which takes 1 s; disabled while `bAutoFade` is off |

- **The scripts:**
  - Quest `0x801` runs `ZFG_ArcaneFeverMCM` (extends `MCM_ConfigBase`; player alias with
    `SKI_PlayerLoadGameAlias`). It only calls `Gauge.ApplySettings()` on each change (`OnSettingChange`) and on
    close.
  - `ZFG_ArcaneFeverWidget.ApplySettings` (also on every load) reads the four settings, re-registers the key
    (`RegisterForKey`) and sends `setDisplay(autoFade, delay, hidden)` to both copies.
- **The hotkey (`OnKeyDown`, ignored in menus and text input):** hidden → shown. Faded out by auto-fade → shown again
  for the delay. Shown → hidden.
- **In the movie:**
  - Every fever change of 0.05 or more, or the first value after a load, calls `peek()`. `setDisplay` also does,
    so the gauge shows for the delay after a load or a setting change.
  - `fadeA` rises to 100 in 0.2 s while `getTimer() < showUntil` (or auto-fade is off), then falls to 0 in 1 s.
  - `follow()` multiplies it into the alpha, and hides the clip at 0 or when hidden.
- **Harness (2026-11-12, 2 s delay):** shown on load; alpha 77 at 2 s (fading); gone at 4 s; back on the change at
  6 s; fading again at 8 s.

## To verify in game

1. Tick `Zenderal - Arcane Fever Gauge` in MO2 (F5 first) and enable its plugin.
2. Load a save. The gauge should appear right of the Health/Mana bars. On a save that never had the plugin, it may
   only show after one more save and reload (SkyUI's manager may already have sent its ready event).
3. Check `skse64.log` for the copies' lines. `Zenderal Arcane Fever Gauge: truehud at x,y rR (bars right …)` is the visible one;
   the HUD copy logs `hud at …` and stays hidden. `truehud, no player widget` means TrueHUD's widget is off, and the
   HUD copy shows instead.
4. `player.modav lastflattered -20` should fill a fifth of the ring with a flash.
   `player.modav lastflattered 20` empties it again.
5. Dialogue and menus should hide the gauge together with the bars.
6. Under `Mod Configuration → Arcane Fever Gauge` (SkyUI can take a few seconds to register a new page on an
   existing save):
   - bind the hotkey; it hides and shows the gauge;
   - tick *Fade out when unchanged*; the gauge fades 5 s after the last change, and the next change (or the hotkey)
     brings it back.
