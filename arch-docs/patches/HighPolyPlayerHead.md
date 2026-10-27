# HighPolyPlayerHead

- **Source:** `src/HighPolyPlayerHead/` (CommonLibSSE-NG SKSE plugin; `build.cmd`)
- **Ships:** `SKSE/Plugins/ZenHighPolyPlayerHead.dll` + `ZenHighPolyPlayerHead.ini`, MO2 mod
  `Zenderal - High Poly Player Head`
- **FormID block:** none (no plugin)
- **Requires:** `High Poly Head.esm` and its files (HPH SE)

## Why

Replaces [`HighPolyDefaultHeads`](HighPolyDefaultHeads.md), which fixed the same problem and froze the game.

Enderal's chargen presets and playable races use the vanilla face parts (`MaleHeadNord`, …). The list's beards
are fitted to High Poly Head, so on a new character the head poked through their stubble shells. The curator
wants High Poly Head as the default head.

HighPolyDefaultHeads repointed the 18 shared vanilla head part records at HPH's mesh and .tri files. NPCs with
baked facegen keep their 898-vertex face mesh but take the record's 3598-vertex .tri morphs, and the MQP03
temple scene hard-froze (postmortem in that doc). So the change must never reach NPCs.

## What it does

- At `kDataLoaded` it pairs every face head part `00KLH_<name>` from High Poly Head.esm with the vanilla
  `<name>`. That gives 43 pairs, including vampire variants Enderal doesn't use.
- Where the twin's texture set differs from Enderal's, it is set to Enderal's, in memory only. This affects
  `FemaleHeadNord`, which has no texture set where HPH names `SkinHeadFemaleNord 03B522`. The old patch made
  the same choice.
- From `PlayerCharacter::Update` (vfunc `0xAD`, the hook ZenCCCStandDown uses), once per frame it reads the
  player's face part: the explicit one on the NPC record, else the race's default `HEAD` entry.
- If that part has a twin that is valid for the player's race, it calls `TESNPC::ChangeHeadPart(twin)` on the
  player's base record and `Actor::ChangeHeadPart(old, twin)` on the 3D. This covers new games, existing saves,
  race and preset changes in chargen, and scripted race swaps (MQP01's child race and back).
- There is a 1 s cooldown after each swap, so a menu that keeps re-applying the vanilla head can't make it
  rebuild the face every frame.
- No record or third-party file is edited. The player's face sliders carry over, because HPH's chargen .tri
  uses the same morph names.

The log is `ZenHighPolyPlayerHead.log` (every swap, plus texture-set fixes). `Enabled=0` in the ini turns it off.

## Status

Built and deployed 2026-10-25. **1.0.1 (2026-10-26)** logs the player's face part whenever it changes: its
EditorID, whether it is on the NPC record or the race default, and whether it has a twin.

**Verified in game on a new game (2026-10-26):** `MaleHeadBreton 051633` → `00KLH_MaleHeadBreton` 50 ms after
the first frame, and 43 twins were found. A save whose character already wore `00KLH_MaleHeadNord` on its own
record needed no swap and logged none, which is expected. Beard fit on the swapped head hasn't been checked
separately.

## Shipped off (2026-10-27)

At beta launch three players (Frosty, Rathma920, wotan774) reported the same thing: chargen looks
right, then the moment the RaceSex menu closes the head turns into HPH's and most presets (female and male) look
wrong — cheekbones and eyelids. Enderal's presets are morph values tuned on the vanilla head; the twin applies the
same values to a different mesh. `Enabled=0` in all three copies (Patch Collection, which loads; the disabled
standalone mod; `data/` here): the DLL then returns at load without registering anything. Players who want HPH
pick an `00KLH_*` head in RaceMenu themselves. Saves already swapped keep the HPH head (it is on the player's
NPC record in the save); `showracemenu` and re-pick the vanilla head to undo it. Backup:
`E:/Zenderal-backups/2026-10-27-hph-player-head-off/`.

## 1.1.0: only inside the race menu (2026-10-27)

The curator wants HPH as the race menu's default, with presets left as SureAI made them and nothing forced
afterwards. 1.0 hooked `PlayerCharacter::Update`, which does not tick while the RaceSex menu pauses the game, so
its swap always landed on menu close, over whatever the player had picked. 1.1 drops that hook and hooks
`RaceSexMenu::AdvanceMovie` (IMenu vfunc `0x05`, every frame while the menu is open) instead:

- **Menu opened, or race/sex changed**, with a vanilla face and all 19 sliders at 0 → the HPH twin. A face with no
  slider values looks right on HPH; one with values (an existing character in `showracemenu`) is left alone.
- **Preset picked**: the player's sliders + nose/eyes/mouth picks now equal one of the race's `presetNPCs` (RPRM/RPRF)
  while wearing the twin this DLL put on → back to the vanilla face. Presets with no slider values are skipped
  (they look the same on either head).
- **Anything else**: a head picked by hand, moved sliders, closing the menu, NPCs, every record: untouched.

The texture-set fix on the twins (`00KLH_FemaleHeadNord`) stays. `Enabled=1` again in all three copies.
**Unverified in game.** The log (`Race menu: face …, sliders …` and `Player head A -> B: reason`) shows whether the
engine applies a preset on race change (then the default stays vanilla) and whether the menu preview redraws after
`ChangeHeadPart`. A short-lived preset patch (`Zenderal - High Poly Presets.esp`, HPH twins added to the 32
`_00E_CharacterTemplate_*` records) was built and removed the same day: it forced HPH onto the presets.

## 1.1.1: HPH neutral face as the default (2026-10-27)

1.1.0 never swapped. Its log showed that picking a race makes the engine apply one of the race's presets: the
vanilla face goes **onto the player's NPC record** and the sliders take the preset's values (`sliders set` at every
race change; the player record itself has no face data in base, FS or EGO). So the race menu's default face *is* a
preset, and "sliders at default" never held. Curator's choice (option 1 of 3): the default becomes **HPH with all 19
sliders at 0**. On a race/sex change, or the menu opening on a new game (not after a save load: `showracemenu` must
not wipe a sculpted face), the face part becomes the twin, the morphs are zeroed (nose/eyes/mouth picks kept) and
`DoReset3D(false)` rebuilds the head. Picking a preset still reverts to the vanilla face. The log now names the
preset the engine applied (`= preset _00E_CharacterTemplate_…`). If option 1 doesn't look good, option 3 is the
fallback: refit each preset's sliders for the HPH mesh from the vanilla and HPH chargen `.tri` morphs.
**Unverified in game.** Watch for: the face redrawing after the reset, and the menu's slider bars showing the old
values until touched.
