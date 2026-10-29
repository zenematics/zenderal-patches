# Prophecy v3 (Constellation)

- **Source:** `src/ProphecyV3/` (DLL in `dll/`, layout generator in `tools/`, generated data in `data/`)
- **Ships:** MO2 mod `Zenderal - Prophecy v3 (Constellation)`: v1's `Zenderal - Prophecy.esp`, scripts and assets,
  plus `SKSE/Plugins/ZenProphecyUI.dll` and `ZenProphecyUI.json`
- **FormID block:** none of its own (v1's plugin, unchanged)
- **Requires:** SKSE Menu Framework (in the list); everything v1 needs
- **Status:** built 2026-10-25; **unverified in game**

## What it is

The third A/B option for the Prophecy menu (v1: B612 cards, v2: walk-in sanctum). The Prophecy power opens an SKSE
Menu Framework window that draws each tree like the website's talent trees: one tab per tree, stars joined by lines
(solid between learned stars, dashed otherwise), root at the bottom, capstone at the top with a larger ring. Learned
stars are filled with a halo, learnable ones (unlocked, with a point to spend) get a gold ring and gold label, locked
ones are dim. Hovering shows the card art, the state ("Learned", "Click to learn", "Requires X or Y", "No Prophecy
points left") and the description; clicking a gold star asks to confirm. Escape or the window's X closes it.

## How it works

- **One script for all three versions.** `ZP_ProphecyMenu` (v1's) checks `SKSE.GetPluginVersion("ZenProphecyUI")`
  after paying points, repairing powers and handing out gifts. When the DLL is loaded it registers for the mod event
  `ZP_ProphecyLearn` and sends `ZP_ProphecyUI_Open` instead of showing the card menu. The DLL opens its window on
  that event, and a confirmed click sends `ZP_ProphecyLearn` with the node's index; `OnProphecyLearn` calls the same
  `TryLearn` the cards use, so points, powers, shouts and gifts never left Papyrus. A runtime check, not a script
  property: saves keep a property's stored value, so a v1 save would never switch.
- **Data.** `tools/01-build-layout.py` reads the menu quest `ZP_ProphecyInit 0x807` that the plugin ships (`Perks`,
  `Descriptions`, `Images`, `ParentA`/`ParentB`, `TreeStart`), so a node's index is the script's array index. Names
  come from the perk records, tree names from v1's `TREES`. Run it after `src/Prophecy/tools/01-build-trees.py`.
- **Layout (symmetrical, generated).** Tier = longest path from the root; each tier is centred, nodes 1.0 apart,
  ordered by their parents' mean position. Every current tree comes out root / two branches / merge / capstone.
- **ImGui.** SKSE Menu Framework 1.90.8's cimgui exports, bound by name. Verified from the DLL before writing code:
  functions that return an `ImVec2` write it through a first out-pointer (`igGetCursorScreenPos`, `igCalcTextSize`
  disassembled); `AddWindow(RenderFunction)` takes one argument and returns a handle whose first member is
  `std::atomic<bool> IsOpen`; `LoadTexture(const char* path, ImVec2* size)` (strlen'd path, size read only if
  non-null) returns the texture; the DLL checks the `DDS ` magic, so the existing card `.dds` files are used as is.
- **Zoom (2026-10-25, curator: "a little small").** The first build capped the tier gap at 150 px and drew the tree
  over about half the canvas. The tiers now spread over the full height (up to 260 px each), the width is 1.3x the
  tier gap, and star size, line width and label size (`ImDrawList_AddText_FontPtr` at up to 1.6x the window font)
  scale with it.
- **Side talents (2026-10-25).** Necromancy's The Dead Don't Forget needs A Willing Sacrifice only, by design, so
  Dark Effigy leads nowhere. Centring every row drew a slanted line and a branch that looked cut off. Now a dead end
  below the top tier goes out to the side, and the talents that lead up stay centred, so the spine is straight.
- **Window (2026-10-25).** It opens centred, 85% of the screen tall and 45% wide (900–1500 px), every time
  (`ImGuiCond_Appearing`). The screen size is read from `ImGuiIO.DisplaySize` at offset 8.
- **Backgrounds (2026-10-25).** One curator painting per tree. `tools/02-convert-backgrounds.py <folder>` takes
  `<Tree-Name>.png` (spaces → hyphens), centre-crops it to 16:9 and writes a 1600×900 BC1 `.dds` to
  `assets/interface/ProphecyBackgrounds/` (committed, shipped by the manifest). `01-build-layout.py` records each
  tree's `background` in the JSON. The window draws it behind the tree, cropped to the canvas's aspect, dimmed to
  about 58%, with a light overall shade and dark gradients on all four edges. Over a background, labels get a dark
  drop shadow. A tree without art keeps the plain panel.
- **Shaped trees (2026-10-25, curator's request).** `SHAPES` in `tools/01-build-layout.py` hand-places a tree's
  talents in square units (y up): Glory is a sword (pommel → crossguard ends → blade → tip), Faith a crucifix (foot
  → crossbar ends → above the crossing → top), Sharpshooter a long musket (butt → hammer / trigger guard → barrel →
  muzzle; `yscale` 1.4, Elemental Rounds' label above its star). `via` routes a prerequisite line through
  waypoints so it follows the figure; `stars`/`lines` are faint decoration completing the outline (not
  clickable). The unlock order is unchanged; the generator asserts every talent is placed. The window fits the
  whole figure into the canvas at one scale for x and y. Trees not in `SHAPES` keep the generated layout. Previewed
  with Pillow at game proportions before shipping; unverified in game.
- **All seven trees shaped, 11 talents each (2026-10-25, with v1's stat talents).** The figures:
  - Faith: a patriarchal crucifix (long bar, short bar above).
  - Glory: a Zweihänder (pommel, guard with drooping quillons, parrying hooks, blade).
  - Sharpshooter: a musket (one straight line from butt to muzzle; butt plate, hammer, trigger and ramrod as short
    strokes).
  - Gadgets: an open-end wrench holding a nut.
  - Martial Arts: a lotus.
  - Arcane Archery: a drawn bow, arrow up.
  - Necromancy: a scythe (two grips on the snath, blade curving left).

  Three rules carry them:
  - The root's side talent is the foot, pommel or butt.
  - A merge talent's two children sit level with it as a short bar.
  - The capstone's line runs on through the merge talent along the shaft (a `via` at its position).

  That one stroke reads as "after the merge talent", which is true one step removed. No decorative stars or lines.
- **2026-10-25 fixes.** (1) Clicking a lit star did nothing. The confirm popup was opened with `igOpenPopup` inside
  the tree's tab item but drawn with `igBeginPopupModal` after `igEndTabBar`. ImGui finds a popup by its name in the
  current ID stack, so the two never matched. The click now only sets `g_openConfirm`, and `ConfirmPopup` opens and
  draws the popup in the same window-level scope. (2) The curator wanted only the talents rearranged, so the shapes'
  decorative `stars`/`lines` are empty; the routed prerequisite lines stay. Both unverified in game.
- **Selection notes (2026-10-25, curator's request).** Clicking a learnable star plays the next note of the
  curator's piano melody (`Piano-003.wav`: 18 notes in C minor, about 105 s), so choosing talents plays the tune in
  order, wrapping after the 18th. `tools/03-split-piano.py <wav>` detects the onsets (energy rise 1.5x; 1.3–1.6 all
  find the same 18, while 1.8 misses the soft A♭2 at 28.4 s under a ringing B♭2). It stops unless it finds exactly 18,
  then cuts each note 20 ms before its onset to at most 3.5 s with a 0.8 s fade. FFT resampling to 16-bit/44.1 kHz
  keeps the pitches (checked: C3 130 Hz, D3 147 Hz, E♭2 77.5 Hz…). The clips go to the v3 mod's
  `Sound/FX/Zenderal/Prophecy/` and are not committed. Records: `ZP_Prophecy_SelectNote_01–18`
  (`0x9B2`–`0x9C3`, in v1's generator so the plugin stays one), using `AudioCategoryUI 064451` and `SOMUIDefault
  0B75FB` so they sound while the menu pauses the game. The JSON lists them in `selectNotes`; the DLL plays them with
  `BSAudioManager::Play(descriptor)` from a game-thread task. Verified in game by the curator (2026-10-25).
- **P key and first-point auto-open (2026-10-25, curator's request).** `ZenProphecyUI.ini [General] Hotkey`
  (DX scan code, default 25 = P, 0 = off). An input sink casts `ZP_ProphecyPower 0x805` with `CastSpellImmediate`,
  so the key does exactly what the power does. A press while the window is open closes it. Ignored while the game
  is paused and in the console, dialogue, main menu and loading screen. P was Quick Magic in both keybind layouts;
  that entry `(40, 0x19)` is now unbound `(40, 0xFF)` in `Zenderal - Input Defaults`, `Zenderal - Personal Keybinds`
  and its `Root` copy. The keyboard block keeps 27 entries, still sorted by key; originals are in
  `E:\Zenderal-backups6-10-25-quick-magic-off-P`. In v1's shared `ZP_ProphecyMenu`, paying point #1 sets
  `openAfterFirstPoint`; when a message box closes and no other is left, the script calls `RequestOpen` (cards in
  v1, the window in v3). The menu-open path clears the flag. Unverified in game.
- **Threads.** Render runs on SMF's render thread and only reads a snapshot (perks owned, points) that a game-thread
  task refreshes every 10 frames while the window is open; the learn event is sent from a game-thread task.

## The radial map (2026-10-27)

The curator wanted every tree on one Path-of-Exile-style canvas. It replaces the tabs whenever `ZenProphecyUI.json`
has a `radial` block; the old tab view stays as the fallback. Concept image: `outputs/prophecy-radial-concept.png`.

- **Layout** (`tools/01`, `place_radial`). A Prophecy start point sits at the centre. Each tree's shaped figure is
  turned so its root → capstone axis points straight out along its own spoke. The spokes run clockwise from Faith at
  the top, in TREES order, and each root sits at `RADIAL_ROOT` 5.2 units. The tool writes:
  - per node `mx`/`my` (map units, y up) and `minor` (stat talents);
  - per tree `color`, `angle`, `labelPos` (beyond its furthest talent) and `mapRoutes` (waypoints transformed);
  - top level `radial` {`extent`, `rootRadius`, `background`}.

  No cross-links: each tree is reached from the centre only. The learn rules are untouched, since the roots need no
  parent.
- **Background.** The curator's art has the seven themes in wedges in the same clockwise order. Since the same day it
  is `Radial mutes.png`, a muted version; it was `Prophecy-Radial.png`. `tools/02` (`RADIAL_PNG`) centre-crops it to
  a square and converts it to `assets/interface/ProphecyBackgrounds/Radial.dds` (2048² BC1).
  - **Size:** it covers [−e, e] with e = extent × canvas aspect × 1.45, so a wide window has no black bars even
    zoomed out and panned. A uniform scale about the centre keeps every wedge on its spoke.
  - **Tint:** light (215/210/202), because the art is already muted.
  - **Tree names** sit `RADIAL_LABEL_GAP` 1.9 units past their furthest talent; at 0.8 they covered the capstones'
    labels.
- **Spacing and labels (same day: "names are overlapping").** Tuned against a simulator of the whole-map view on the
  curator's canvas (1784×1130, real Futura metrics; scratchpad `labelsim.py`).
  - **Before:** 22 overlapping labels.
  - **Spread and root:** `RADIAL_SPREAD` 1.5 scales every figure and `RADIAL_ROOT` 5.5. Spread alone bottoms out
    near 11, because the fit shrinks it back.
  - **Label sides:** `place_labels` picks each talent label's side (below/above/right/left, `labelSide`, 0–3), the
    one that collides least with stars, tree names and earlier labels, capstones first. Widths come from a
    per-character table, since Pillow is unavailable under `-I`.
  - **Tree names** step out until they clear their own stars.
  - **Result:** 4 left, each a label grazing a small stat-talent dot.

- **Second pass (same day: "some nodes are even closer").** A shared root radius with 1.5× figures pushed the wide
  figures into their neighbours. The fixes:
  - **Per-tree start distance.** Each tree's root now sits as far out as its figure needs to stay within
    `RADIAL_FILL` 0.75 of half its 51° slice (`RADIAL_ROOT` 3.5 is only the minimum).
  - **Spread** went back to 1.2.
  - **Figures opened up:** the scythe's grips and heel, the musket's hammer, trigger and ramrod, the wrench's nut.
  - **Tried and dropped:** per-tree length normalization (`RADIAL_LENGTH`, kept at 0), because shrinking the rifle
    squeezed its barrel.
  - **Result at the whole-map view:** closest stars 34 px (were 24), across trees 65 px (were 42), 4 labels
    grazing a small dot. Preview: `outputs/prophecy-radial-preview.png` (scratchpad `mappreview.py` renders the
    JSON as DrawMap does).

- **Room between talents (same day: "too bunched up, archery almost through glory").** The DLL sizes stars and
  text from pixels per map unit (`z = sc / 45`), so the room between talents *relative to their names* depends
  only on the figures' size in map units, at every zoom. `RADIAL_SPREAD` 1.2 → **2.0** (closest pair 1.08 → 1.8
  units) and `RADIAL_FILL` 0.75 → **0.6** (closest stars of two trees 2.1 → 6.6 units; extent 18.1 → 33.5).
  The DLL's zoom factors grew by the same ×1.85 so a tree looks as large as before: tree buttons 2.4 → 4.4× fit,
  wheel max 5 → 9×, stat-talent names from 1.6 → 2.9× fit. The whole-map view gets smaller (labels are clamped at
  their minimum size there; the label simulator reports 16 crowded instead of 4). Preview renders: scratchpad
  `mappreview.py <zoom> <cx> <cy> <out>`.

  In the DLL, talent names always show and stat-talent names from 1.6× the fit zoom; it was absolute z ≥ 0.75, which
  hid every name once the map got larger. Click areas cover the star plus its label on its side.
- **DLL** (`DrawMap`). One canvas `InvisibleButton` (left and right buttons) with `SetNextItemAllowOverlap`, so the
  talent buttons drawn after it still take the hover:
  - **Pan:** drag either button (`igGetMouseDragDelta` + `igResetMouseDragDelta` while the canvas is active).
  - **Zoom:** the wheel zooms at the cursor, 0.8–5× the fit scale.
  - **The wheel itself:** it is read as ImGuiKey `MouseWheelY`'s `AnalogValue` from `igGetKeyData_Key` (+12). The
    key's number is found once by name with `igGetKeyName`, because it differs between ImGui versions; no `ImGuiIO`
    offsets are assumed.
  - **What it draws:** spokes and prerequisite lines in tree colours (solid once learned, dashed otherwise), the four
    node states as before, a capstone ring, tree names, and the start point.
  - **Labels:** a stat talent's label shows only when zoomed in.
  - **Edges:** a talent whose button would cross the canvas edge gets no button, since it would grow the content and
    add scrollbars. The window opens with `NoScrollbar | NoScrollWithMouse`, 70% of the screen wide.
  - **Jump bar:** "Whole map", plus one button per tree that centres and zooms on it.
- **Eighth tree, Shadow (2026-10-27):** a dagger, point up, through an upturned crescent moon, between Gadgets and
  Martial Arts. With eight narrower slices every root sits further out, so the whole-map view draws everything
  smaller. Its wedge is not in the background art, `Radial mutes.png`, which still has seven. A tree's name now steps
  out until it also clears the room its talents' names may take, not just their stars ("Gadgets" sat on Clockwork
  Turret's name). The map's extent grows to keep a moved name in view.
- **Eleven trees (2026-10-27): Druid, Sorcerer, Rage.** Order clockwise: Faith, Sharpshooter, Gadgets, Shadow, Martial Arts,
  Glory, Rage, Druid, Arcane Archery, Necromancy, Sorcerer. `RADIAL_WEIGHT` sizes the slices: Glory and Rage 1.35, which
  moves Druid and Arcane Archery further clockwise (curator). A tree draws its figure larger by its weight, and `RADIAL_SCALE` draws one smaller without changing its slice: Necromancy 0.65 (curator: it stuck out; its scythe blade forced its root furthest out and set the whole map's size, so shrinking it also drew every other tree larger). The whole-map
  view cannot keep every name clear at eleven trees (70 overlap); each tree reads cleanly from its jump button.
- Unverified in game.

## Building

1. `python -I src/Prophecy/tools/01-build-trees.py` (v1), then `python -I src/ProphecyV3/tools/01-build-layout.py`.
2. `src/ProphecyV3/dll/build.cmd`, copy `build/ZenProphecyUI.dll` to `compiled/` (committed: CI cannot build it).
3. `build/build.ps1`; copy `build/staging/Zenderal - Prophecy v3 (Constellation)` into the MO2 mod.
4. Loose files (not committed): `src/Prophecy/tools/03-install-sounds.py`, `04-install-stomp-anim.py` and
   `05-build-owl-mesh.py` now also write into the v3 mod when it is installed.

Only one of v1, v2, v3 may be enabled (same plugin name).

## To check in game

- the window opens from the Prophecy power (SKSE log `ZenProphecyUI.log`: "window opened", trees/perks resolved);
- the cursor and input: SMF windows take the mouse; a controller is not supported yet;
- the card art in tooltips (`texture ...: loaded` in the log);
- learning: gold star → confirm → "Learned X." and the star fills.

## PG Patcher (2026-10-25)

PG Patcher scans every loose mesh in the load order and writes patched copies into `PG Patcher Output`, which sits
near the top of the list. Its 11:04 run on 2026-10-25 had patched the 11 Ordinator meshes this mod ships under
`meshes\ordinator\` (Hissing Dragon projectiles, mage ward, Dwarven autocannon), and those copies (different bytes)
overrode the mod's own. `*\ordinator\*` is now in PGPatcher's blocklist (`Tools/PG Patcher/PGPatcher/cfg/settings.json`,
`params.processing.blocklist`; only this mod has that folder), and the 11 stale copies were moved out of the output to
`E:/Zenderal-backups/2026-10-25-pgpatcher-prophecy/` with the old settings file. Later PG Patcher runs leave them alone.
