# EnderalPairedAnims

- **Source:** `src/EnderalPairedAnims/`
- **Ships:** *(no plugin — a Pandora-native behaviour patch, `Pandora_Engine/mod/zpaired/`, MO2 mod `Zenderal - Enderal Paired Animations`; tick **Zenderal - Enderal Paired Animations** in Pandora)*
- **FormID block:** _(none)_

## What it does

Puts Enderal's six FNIS paired/killmove scenes back into the third-person `0_master` graph that
Pandora builds. Without it they never play: MQ07b's Calia-vs-bandits scene and the hugs and kisses
stand still.

| FNIS line (`fnis_enderal_list.txt`) | Clip | Player / NPC event | IDLE |
|---|---|---|---|
| `km CaliaMassacre` | `enderal\paired_calia_massacre.hkx` | `pa_CaliaMassacre` / `CaliaMassacre` | `pa_MQ07b_CaliaMassacre 13FAA3:Skyrim.esm` |
| `pa HugB` | `enderal\paired_hugb.hkx` | `pa_HugB` / `HugB` | `0F4699` |
| `pa Kiss2Female` | `enderal\paired_kiss_2female.hkx` | `pa_Kiss2Female` / `Kiss2Female` | `13FA9D` |
| `pa Kiss2Male` | `enderal\paired_kiss_2male.hkx` | `pa_Kiss2Male` / `Kiss2Male` | `13FA92` |
| `pa KissMaleFemale` | | `pa_KissMaleFemale` / `KissMaleFemale` | `13FA9C` |
| `pa KissFemaleMale` | | `pa_KissFemaleMale` / `KissFemaleMale` | `141596` |

## Why it is needed

Pandora 5.0.0-beta's FNIS support only registers each listed clip in `defaultmale.hkx` /
`defaultfemale.hkx` and splices the mod's shipped `FNIS_<mod>_Behavior.hkx` into `0_master`; the
`Paired` case in `FNISAnimationFactory.Create` is commented out and `BasicAnimation.BuildBehavior`
is a stub. FNIS writes `pa`/`km` states into `0_master.hkx` itself, and Pandora's `0_Master.hkx`
(rebuilt from its vanilla template) overrides Enderal's FNIS-built one, so the states are gone.
Full diagnosis in [`modlist/mod-gotchas.md`](../modlist/mod-gotchas.md). The clips themselves are
still registered — `paired_calia_massacre.hkx` was already in Pandora's `defaultmale.hkx` and
`defaultfemale.hkx` before this patch — so only `0_master` needs the patch. Enderal's FNIS build
adds no `animationdatasinglefile` entries for these clips, so the patch adds none either.

## How it was built **[verified from the files 2026-10-16]**

The source of truth is Enderal's FNIS-built
`Stock Game/Data/meshes/actors/character/behaviors/0_master.hkx`. Both it and Pandora's template
(`Pandora_Engine/Skyrim/Template/actors/character/behaviors/0_master.hkx`) were converted to XML
with `tools/hkxconv` (Pandora's own HKX2 library; the template is a *meta* packfile that keeps the
Nemesis node names `#0106`…, so it needs `--meta`). The two trees were aligned from the root:

- Enderal's file = the template + 136 FNIS nodes. 6 of them are the three `FNIS_State*` behaviour
  references on `RootBehaviorGraph`, which Pandora already splices from the shipped
  `FNIS_*_Behavior.hkx`. The other **130** hang off 12 new states: `Player_/NPC_FNISkm1` on
  `KillMove_Behavior` (`#0788`) and `Player_/NPC_FNISpa1..5` on `MT_PairedAnimationsBehavior`
  (`#0724`).
- Changed template nodes: those two state machines' `states`, their wildcard-transition arrays
  (`#0789` +2, `#0725` +10 — appended, the vanilla transitions are byte-identical), and
  `eventNames`/`eventInfos` (+12 events `HugB`, `pa_HugB`, … `CaliaMassacre`, `pa_CaliaMassacre`,
  flags 0). The first 1217 events and 230 variables are identical in both files, and the new nodes
  use only vanilla variables (`bIsSynced` 51, `DisablePitch` 58, `Is3rdPKillOnly` 213).
- Not carried: FNIS also added `NPCKillMoveStart/End` and `2_KillMoveStart/End` clip triggers to
  vanilla `HugA`'s clips and an enter-event to `NPC_HugA`. Vanilla HugA is not one of the six scenes
  and Pandora's template does not have those edits; left alone.

`tools/01-build-paired-patch.py` does this alignment and writes
`data/Pandora_Engine/mod/zpaired/patches/0_master.xml` in Pandora's native format: one
`<Append path="">` holding the 130 nodes renamed `#zpaired$N`, `<Append path="#0788/states">` /
`#0724/states` (text), `<Append path="#0789/transitions">` / `#0725/transitions` (elements), and the
event appends. Every reference to an FNIS event is written `$eventID[name]$`: Pandora's
`PackFileValidator` resolves those in new nodes and in changed nodes after all mods' events are
added, so the indices stay right whatever other mods add. The script asserts the event set, that
the vanilla transitions match, and that each appended transition targets a new state.

Regenerate (only if Enderal's `0_master.hkx` or Pandora's template changes):

```
dotnet build -c Release -p:Hkx2Dir=<HKX2-Enhanced-Library checkout>/HKX2 src/EnderalPairedAnims/tools/hkxconv
hkxconv "<Stock Game>/Data/meshes/actors/character/behaviors/0_master.hkx" enderal.xml
hkxconv --meta "<Pandora>/Pandora_Engine/Skyrim/Template/actors/character/behaviors/0_master.hkx" pandora.xml
python src/EnderalPairedAnims/tools/01-build-paired-patch.py enderal.xml pandora.xml src/EnderalPairedAnims/data/Pandora_Engine/mod/zpaired/patches/0_master.xml
```

`HKX2-Enhanced-Library` is the submodule of Monitor221hz/Pandora-Behaviour-Engine-Plus at tag
`v5.0.0-beta` (commit `de77588`); it targets net10.0 — on a net9-only SDK, change `HKX2E.csproj`'s
`TargetFramework` to `net9.0` (builds clean).

## Part 2 — the animation sets (`zpairset`) **[verified from the files 2026-10-16]**

`zpaired` alone was not enough: in game Calia and Karek stood still, and A-Pose Fix logged a load
error on `paired_calia_massacre.hkx` (it "converted" the clip into a byte-identical loose copy in
`overwrite`). The graph was proven identical to Enderal's (the 750-line canonical dump of the four
paired states, events and variables resolved by name, diffs to zero), so the gap is elsewhere:
**SSE only loads a clip listed in the actor's active animation set** in
`animationsetdatasinglefile.txt`. Enderal's FNIS build lists the clips under the
`animations\enderal` folder hash (`679778984`, Bethesda CRC32 = reflected 0x04C11DB7, init 0, no
xorout) in dedicated trigger sets `PlayerFNIS1..6Start` / `NPCFNIS1..6Start` (Calia also in
`H2HDual`/`H2HSolo`) — Calia 8 times, each hug/kiss 4 times. Pandora's output has 0. Nemesis's `km`
template writes these sets too; Pandora's FNIS support does not.

Pandora cannot create new sets and Pandora-native mods have no animset hook (`PandoraAssembler.AssemblePatch`
only reads `patches/*.xml` and `native/`), so `Nemesis_Engine/mod/zpairset/` — a Nemesis-format
mod — adds the six clips to **all 374 sets** of DefaultMale and DefaultFemale, the way Pandora's own
bundled killmove pack `snusnu` does. It uses `animationsetdatasinglefile/<project>/<set>.txt`, not
the root `<project>.txt` form, because `AssembleAnimSetDataPatch` `break`s after the first root
file (only one project would be patched). Generated by `tools/02-build-animset-patch.py` from
Pandora's template set list:

```
python src/EnderalPairedAnims/tools/02-build-animset-patch.py "<Pandora>/Pandora_Engine/Skyrim/Template/animationsetdatasinglefile.txt" src/EnderalPairedAnims/data/Nemesis_Engine/mod/zpairset
```

Tick **both** entries in Pandora: *Zenderal - Enderal Paired Animations* and *… (anim sets)*.
Check a run with: Pandora output's `animationsetdatasinglefile.txt` must contain `679778984`.

## Status

- 2026-10-16: patch generated and deployed (MO2 mod enabled in profile Ultra, `zpaired` added to
  Pandora's `ActiveMods.json`). **A list Pandora run with it has NOT been verified yet**, and it has
  **not been tested in game**.
- 2026-10-16 (later): `zpaired` verified in a list Pandora run (output `0_Master.hkx` carries the
  states) but scenes still froze in game — missing animation-set entries (Part 2). `zpairset`
  generated and deployed.
- **2026-10-16: verified in game** — with both entries ticked, the 18:51 Pandora output lists the
  `animations\enderal` hash 4488 times (748 sets × 6 clips) and the MQ07b Calia massacre plays.
  Hugs/kisses share the same mechanism but were not separately watched.
- **Trap — never run Pandora outside MO2 from a copy of its folder.** Pandora 5.0.0-beta ignored
  `-o:"…"` and wrote to the `outputPath` in its own `Settings.json`, which in this list's copy is
  `Stock game\Data`: an isolated test run overwrote Stock Game's `0_master.hkx`,
  `defaultmale/defaultfemale.hkx` and both `animation*singlefile.txt`. The originals are in the
  Steam Enderal SE install (`E:/Steam/steamapps/common/Enderal Special Edition/Data`, verified
  identical). Run Pandora only from MO2. Launching it through MO2's CLI from a Claude session fails
  anyway (usvfs launch: `ERROR_ACCESS_DENIED`).
