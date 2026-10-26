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
