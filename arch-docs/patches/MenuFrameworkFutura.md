# MenuFrameworkFutura

- **Source:** `src/MenuFrameworkFutura/tools/` (`swffont.py` reads SWF fonts, `01-build-font.py` writes the TTF)
- **Ships:** MO2 mod `Zenderal - Menu Framework Futura`: `SKSE/Plugins/Fonts/MainFont.ttf`, generated, **not committed**
- **FormID block:** none (no plugin)
- **Status:** built 2026-10-25; the font renders correctly in FreeType (Pillow); **unverified in game**

## What it does

Curator's taste: SKSE Menu Framework's windows (its control panel, Local Map Upgrade, Prophecy v3) use regular
Futura, as the game's own menus do, instead of Futura Condensed.

- SMF draws every window in `[Fonts] PrimaryFont`. The winning `SKSEMenuFramework.ini` (Zenderal - Input Defaults /
  Zenderal - Personal Keybinds) already says `PrimaryFont = MainFont.ttf`, which SMF loads from
  `Data/SKSE/Plugins/Fonts/`. No mod provided that file, so SMF logged "Primary font 'MainFont.ttf' failed to load.
  Falling back to 'Futura Condensed (EN)' from Interface\fonts_en.swf". **[verified]** (SMF 3.14 log, DLL strings)
- Vel'dun UI (Enderal Default) maps the game's menu fonts to regular **Futura Book BT** from its
  `Interface/fonts_futura.swf`, but SMF's SWF font reader loads 0 faces from that file. **[verified]**
- `01-build-font.py` reads that DefineFont3 tag (267 glyphs, full ASCII + 169 more; quadratic outlines on a 1024 em
  at 20x, the same curve type TrueType uses, so the conversion is exact) and writes a TrueType file by hand: head,
  hhea, maxp, OS/2 v4, hmtx, cmap format 4, loca, glyf, name, post. SWF y runs down (flipped); its contour directions
  already match TrueType's (outer clockwise, holes counter-clockwise); the closing point that repeats a contour's start
  is dropped. No kerning is carried over.
- Font-wide: it changes every SMF window, not only Prophecy's.

## Licensing

Futura Book BT is a commercial Bitstream font that Vel'dun UI already distributes. The TTF is a re-wrapping of that
file for the same list, so it is not committed; regenerate it on each machine:

```
python -I src/MenuFrameworkFutura/tools/01-build-font.py [<MO2 mods dir>]
```

Enable the MO2 mod `Zenderal - Menu Framework Futura`. Rerun after a Vel'dun UI update.
