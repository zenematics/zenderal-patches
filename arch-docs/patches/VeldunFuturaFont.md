# VeldunFuturaFont

- **Source:** `src/VeldunFuturaFont/tools/01-build-fontconfig.py` → `src/VeldunFuturaFont/Interface/fontconfig.txt`
- **Ships:** MO2 mod `Zenderal - Vel'dun Futura Font` (`Interface/fontconfig.txt` only); `build/manifest.json`
  release of the same name. Wabbajack `Include` rule.
- **FormID block:** none (no plugin)
- **Status:** built and enabled 2026-11-09 (Ultra, directly above `Veldun fomod files`); **unverified in game**

## What it does

Curator's taste: Vel'dun UI's menus in regular **Futura Book BT**, as they were until 2026-11-03.

- Vel'dun UI 1.7 (Nexus 1098, 2026-11-02) added the installer option *4. Oblivion Interaction Icons Patch* for
  OII 3 beta → `Patches/Vel'dun Oblivion Icons patch 3 beta/`. Its `Interface/fontconfig.txt` maps all five menu
  fonts (`$StartMenuFont`, `$DialogueFont`, `$EverywhereFont`, `$EverywhereBoldFont`, `$EverywhereMediumFont`) to
  `"lato"` from `Lato.swf`, and books (`$SkyrimBooks`) to Trattatello. **[verified]** (archive)
- Vel'dun 1.6 had no such option. Its own config (`Patches/Vel'dun UI 1.0.2/`) and its OII 1.x patch
  (`Vel'dun Oblivion Icons patch 1.1/`) map those fonts to `"Futura Book BT"` from `fonts_futura.swf`
  (the only face in that file; `Lato.swf` holds only `lato`). **[verified]** (archive, `swffont.read_fonts`)
- The curator installed OII 3 beta + that option on 2026-11-02/03, so both `Veldun fomod files` and
  `Vel'dun UI Enderal Default` ship the Lato config, and the whole UI went from Futura to Lato. Description
  Framework (added 2026-11-08) has nothing to do with it: it only hooks item cards, with `iFont = -1`.
- `tools/01` takes the winning config (the highest-priority enabled MO2 mod shipping `Interface/fontconfig.txt`,
  ours excluded), points those five maps and `$ListFont` (mapped by Vel'dun 1.0.2, dropped by the beta) at Futura
  Book BT, and asserts it: each map exactly once, `fonts_futura.swf` loaded, nothing left on `lato`. Everything else
  stays byte for byte as Vel'dun ships it (UTF-8, CRLF): OII's `Fonticon.swf` + `$Iconographia`, Trattatello for
  books, `validNameChars`.
- It also guarantees `fontlib "Interface\Mage.swf"` + `map "$Mage"`, which the beta config drops and Vel'dun's item
  card needs for talent words (see [`mod-gotchas.md`](../modlist/mod-gotchas.md), 2026-11-05). The earlier fix lives
  in `Veldun fomod files` itself and is lost on a reinstall; this mod now carries it as well.

Books stay in Vel'dun 1.7's Trattatello (the curator asked only for the UI font). To bring back the old book font,
map `$SkyrimBooks` to `SkyrimBooks_Gaelic` in the tool.

## Load order

The MO2 mod must outrank every mod that ships `Interface/fontconfig.txt`: `Veldun fomod files`,
`Vel'dun UI Enderal Default`, `Oblivion Interaction Icons`. Rerun after a Vel'dun UI or OII update:

```
python -I src/VeldunFuturaFont/tools/01-build-fontconfig.py [<MO2 instance dir>]
```

## Not this mod: the location names

The same report (2026-11-09) said location names on saves and the loading screen are no longer in English. The
saves' own headers hold the English names (`Sun Temple, Chronicum`, `Ark, Marketplace`, read from every `.ess`
since 2026-11-02), and no font, DSD config or translation file in the list renames a location. Only the save
**file names** carry the German cell EditorIDs (`SuntempleChronikum`, `CapitalCityUpperTemple`, `Akropolis`), which
is the engine's normal naming. Cause still open; needs the exact text seen in game.
