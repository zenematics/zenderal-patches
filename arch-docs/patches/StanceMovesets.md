# StanceMovesets

- **Source:** `src/StanceMovesets/tools/` — `stance_sources.py` (the source and layer tables), `00-install-sources.py`,
  `01-build-stance-overlays.py`, `02-verify.py` (all three stances). Reuses `src/LSdFHighStance/tools/01-build-lsdf-high-stance.py`
  for the DAR parser, OAR condition builders and the For Honor Reforged exceptions.
- **Ships:** *(no plugin)* MO2 mod `Zenderal - Stance Overlays`: **68 OAR `user.json` files and nothing else**, over eleven
  third-party mods installed **untouched** from Nexus downloads.
- **FormID block:** _(none)_

## What it does

The Stances mod's High (F1, `stances_highstance_perk 042518`, `stances_switchspell_H 093543`), Mid (F2,
`stances_midstance_perk 042519`, `stances_switchspell_M 093544`) and Low (F3, `stances_lowstance_perk 04251A`,
`stances_switchspell_L 093547`) stances get their own movesets; Neutral (F4) is For Honor Reforged unchanged.
High was [`LSdFHighStance`](LSdFHighStance.md) (a generated conversion) until the curator shelved it on 2026-11-10
for cheming1228's Nordic pack, which completes the set: Nordic / Desert / Imperium = High / Mid / Low, as in
DoinkBoink's Stances pack 134152.

| Stance | Source (Nexus, installed as its own MO2 mod) | Used for |
|---|---|---|
| High | cheming1228, *Nordic Combat Animations for Nord and Orc* 1.3 (72966, file 378682) | base: every weapon's attacks and guard (AC Valhalla style), mixed duals included; no fists |
| High | MoFu, Black, Old Fire, Mathieu, *Elden Sword Definitive (MCO - SCAR)* 1.1 (136573, file 573596), `Moveset` + `Extra Power Attack` | sword with the off-hand free (or staff, spell, scroll, torch); forward + power attack = its extra power attack |
| High | MoFu, Black, Mathieu, *Lothric Fighter - MCO* 1.0 (136588, file 573437), `Moveset` + `Shield Bash` | sword + shield; forward + power attack = its shield bash (its back power attack is off: FHR owns back attacks) |
| Mid | cheming1228, *DesertRace Combat Animations for Redguard and Khajiit* 1.1 (77474, file 378693) | base: every weapon's attacks and guard (AC Origins style) |
| Mid | Austio, *Elder Creed - Axe Moveset AIO* (71937) | war axe alone, with shield, dual |
| Mid | Kars, *Elder Creed - Blade* 1.2, `ADXP-MCO` option (75533) | sword (free hand / shield) |
| Mid | cheming1228, *Skyrim Martial Arts - Muay thai* (77297) | fists |
| Low | cheming1228, *Imperium Combat Animations for Breton and Imperial Races* 1.1 (88752, file 378700) | base: every weapon's attacks and guard (footman style) |
| Low | Vector1886, *Realistic Mercenary 1H Sword Animation* (75920), folder `20003` | sword attacks |
| Low | Verolevi, *Vanargand Animations II - Sword Low Stance* 1.1b (187094), `Main` + `Hip Equip` | sword guard |
| Low | cheming1228, *Skyrim Martial Arts - Kick Boxing* (69201) | fists |

| In High / Mid / Low | Plays |
|---|---|
| light / power attack chains, forward/standing power attack | the stance's set for the weapon pair |
| idle, turns, walks, runs, equip (and whatever else the source keeps in those folders: its sprints, Muay Thai's block idle) | the stance's guard |
| left/right/back light and power attacks, back-light **parry**, parry / block-slide / **knockdown** follow-ups, shield parry, FHR combo layers | **For Honor Reforged's own clips, with their mechanics** |
| mixed dual wield (e.g. sword + dagger) | High: Nordic's mixed-dual set (`31090`); Mid / Low: For Honor Reforged (no source has one) |
| fists in High | For Honor Reforged (Nordic has no unarmed set) |

Downloaded but unused: Vanargand II Unarmed MCO + Pugilism Stance (110676, 109684; curator's choice, 2026-11-10);
*Nordic Locomotions for Player* (72966, file 378683): the player build of the pack's own `31001`/`31002` locomotion
folders (`40001`/`40002`, same conditions with `IsActorBase(player)`), which the overlay already gives the player.

## Why overlays (2026-11-10)

The first build copied the sources' clips into two generated mods (padded slots, `$FHFX` added). Their Nexus
permissions (read the same day) mostly say *ask before modifying or using assets*; Elder Creed – Blade forbids asset
use outright and even condition-fix reuploads without permission; only Realistic Mercenary allows modification with
credit. The overlay shape redistributes no animation: Wabbajack installs each source from Nexus as-is, and the list
ships only our `user.json` files (DoinkBoink's Stances pack 134152 does the same over cheming's packs).

| Source | Modification | Asset use | Upload | Author's note |
|---|---|---|---|---|
| Nordic, Desert, Imperium, Muay Thai (cheming1228) | ask | ask | no | — (Nordic read 2026-11-10) |
| Kick Boxing (cheming1228) | ask | ask | yes, with credit | — |
| Elder Creed – Blade (Kars) | ask | **no** | no | "You may not reupload … DAR conditions fixes without my permission" |
| Elder Creed – Axe (Austio) | ask | ask | no | "Please do not re distribute these animations without my permission" |
| Realistic Mercenary (Vector1886) | yes, with credit | ask | no | — |
| Elden Sword Definitive, Lothric Fighter (MoFu et al.) | **no**, "including creating bug fixes … under any circumstances" | **no** | no | some assets from other authors (read 2026-11-10) |
| Vanargand II Sword Low Stance (Verolevi) | ask | ask | no | — |

**Still to settle before shipping:** Kars's note covers condition fixes, so Elder Creed – Blade's two user.json files
need his OK (or Mid's sword falls back to the Desert pack by dropping that layer in `stance_sources.py`). The same
goes for Elden Sword Definitive and Lothric Fighter (High's sword and sword + shield fall back to Nordic without
them): their pages forbid modification "including creating bug fixes", and a user.json rewrites their conditions.

## Evidence

- **All sources are SSE packfiles and already MCO** (`MCO_WinOpen`/`Close`, `MCO_Recovery`,
  `PIE.@SGVI|MCO_nextattack|N`; 663 clips, every header `8, 1, 0, 1`).
- **None can be installed with its own conditions.** cheming's race packs are NPC builds (`NOT IsActorBase(player)
  AND IsRace(...)`), the rest ungated: installed as-is they would replace FHR in every stance and on NPCs.
- **OAR `user.json` replaces a submod's settings**, in OAR folders (beside `config.json`) and in legacy DAR folders
  (DoinkBoink's pack does the latter). An OAR folder's user.json here is its `config.json` with priority, conditions
  and `disabled` changed; a DAR folder's is `{priority, disabled, conditions}`.
- **Muay Thai and Kick Boxing both ship DAR folder `40050`** (and `40051–40054`); MO2 would merge them file by file.
  Kick Boxing's author: "If you using number 40050 already, change the numbers" — 00 installs it at `40060–40064`.
- **MCO's attack graph** (`Attack MCO-DXP/meshes/actors/character/behaviors/MCO_Attack.hkx`, decoded 2026-11-10): all
  20 `MCO_ClipGenerator_MCO_attackN` share one `hkbClipTriggerArray` (reached through global fixups):
  `MCO_InputBuffer` 0.2 s after start and `attackStop` 0.1 s before the end, for every clip. The 1hm graph patch
  takes the next attack on `attackStart` between `MCO_InputBuffer` and `MCO_WinClose`, starting it at `MCO_WinOpen`.
  So a clip only needs `MCO_WinOpen`/`MCO_WinClose` (+ the PIE next slots); no source uses `MCO_InputBuffer`.
- **Realistic Mercenary ships `SKSE/PayloadInterpreter/Config/Blades.ini`** (`$enableIframe`/`$disableIframe` =
  `@SETGHOST`): installed untouched, its attacks have the author's short invulnerability frames. Its `$ES_*` macros are
  defined by no enabled mod and stay inert.
- **FHR's guard clips carry no FHR mechanics** (334 player clips: only Smooth Moveset's `$Smooth_C` and pistol tags).

## Mechanism

1. **00** extracts each download's data folder into `mods/<source>` byte for byte (+ MO2 `meta.ini`; Kick Boxing
   renumbered as above), writes a `.meta` for a download that lacks one (the race packs were downloaded outside
   MO2; Nexus file ids 378693 / 378700 / 378682 match their names on Nexus).
2. **01** lists every submod folder of every source. Per stance, layers low → high (`stance_sources.STANCES`); for
   every weapon pair each layer's own conditions are evaluated for the player in combat with the weapon drawn (race
   and actor-base tests dropped, `IsSneaking`/Keytrace `HasMagicEffect` false: FHR owns direction inputs).
   - An **attack-bearing folder** is enabled only for the pairs where it is the highest live layer with attack
     clips, so a pair's attack set is always one source's whole set (Elder Creed's 5-attack sword never picks up the
     Desert pack's attack 6). It also gets one negated block per FHR special submod that shares a clip
     (`fhr_negations`).
   - A **guard-only folder** is enabled wherever it is live; OAR's per-clip priority (layer order) picks each clip.
     Liveness is evaluated in and out of combat: the race packs' relaxed weapon-drawn locomotion (Nordic `31002`,
     Desert `32003`, Imperium `33002`, author conditions `NOT IsInCombat() AND IsWeaponDrawn()`) is enabled with
     `NOT IsInCombat`, one priority step above the pack's combat guard set, as its folder number places it in DAR.
   - A **directional addon** (layer tuple's 5th item: Elden Sword's `Extra Power Attack`, Lothric's `Shield Bash`)
     is a source's own forward + power attack, which its authors gate on dTry Key Utils' Keytrace effect `801`.
     Keytrace's effects never appear in this list (traced for [`FHRFirstPerson`](FHRFirstPerson.md)), so as shipped
     they are dead; 01 regates them on OAR `IsMovementDirection` 1 (forward) with DMK's `DirecionalCycleMoveset` 1
     or 0 (FHRFirstPerson's direction test; forward = 1 is inferred from FHR's clockwise 3/5/7), only at the pairs
     where their own source's set is the attack set, 5 priority above it, with their own FHR exceptions. FHR's
     directional submods need DMK 3/5/7, so the gate never meets them.
   - **Every other folder** (NPC folders 2500002/3, Keytrace direction folders 4005x/4006x, Imperium's `33003`
     (its one clip, `dw1hm1hmidle d.hkx`, is named for no state), Vanargand's `Sprint`, sets a higher layer replaces
     everywhere) gets `disabled: true` plus
     conditions that can never be true (player AND NOT player).
   - Priorities: High 1,500,030,000, Mid 1,500,010,000, Low 1,500,020,000, each + 10 × layer: above every FHR /
     Smooth Moveset / Patch Collection moveset submod, below Beam Walking Assist, UNDERDOG's states and RaySense;
     the stances are mutually exclusive by perk. Nordic's out-of-combat folder `31002` is disabled like Desert's
     `32003`.
3. Lost against the copy build: no `$FHFX` heavy tell on these sets, no slot padding (after an FHR directional clip
   hands over a slot past a set's count, that one attack is FHR's neutral clip), and each source's whole folder
   comes along (Desert/Imperium sprints, Muay Thai/Kick Boxing block idles).

## Postmortem: F1's run "doesn't look like a run" (2026-11-10)

**Symptom (curator):** in F1 with a sword or sword + shield, the run (not the sprint) looked odd.

**Cause [verified offline]:** the first overlay build evaluated every source for the player *in combat* only, so the
packs' out-of-combat folders were disabled and running with a weapon drawn played the combat guard set everywhere.
Nordic's combat run is a guard jog. Gait read from the clips (PyNifly `anim_skyrim` on XPMSE's skeleton, forward
run, 0.70 s cycle):

| Run clip | hand swing | foot lift | pelvis bob |
|---|---|---|---|
| Nordic `31001` (combat) | 11.8 | 21.2 | 3.1 |
| Nordic `31002` (out of combat) | 30.8 | 35.5 | 6.2 |
| Desert `32001` / `32003` | 11.9 / 39.6 | 30.1 / 31.8 | 7.3 / 5.2 |
| Imperium `33001` / `33002` | 24.6 / 37.0 | 25.3 / 31.6 | 6.7 / 3.9 |
| Smooth Moveset 1hm (F4) | 41.0 | 31.4 | 3.6 |

All 54 clips of `31001` and `31002` differ; the pack's *Nordic Locomotions for Player* file (72966, 378683) is
byte-identical to `31001`/`31002` (56 of 56 clips), so it adds nothing. Elden Sword and Lothric ship only an idle;
the run was always Nordic's. Nothing else outranks the overlay's priority for `1hm_run*` except Beam Walking Assist's
fence folders.

**Fix:** liveness in and out of combat (Mechanism 2); the three relaxed folders are on out of combat. In combat the
packs' guard jog stays, as their authors made it. **Verified in game 2026-11-10** (curator, F1 sword run: "looks to
be fixed now").

## Verification (2026-11-10, offline)

`02-verify.py`, FHR re-read from the live profile (364 special submods): every source folder has an overlay
(0 ungated), enabled ones gated on their stance perk + player, unused ones locked; at most one attack set per
weapon pair; every attack-bearing submod × weapon pair × FHR special submod sharing a clip has a covering exception:
**High 7,695 (Nordic + Elden Sword + Lothric), Mid 7,815, Low 7,444 cases, 0 uncovered** (High was LSdF's 34,216 until 2026-11-10: it is
checked per skill band too). The check catches a removed exception (mutation test on the copy build: dropping one
set's 36 DMK exceptions left 75 FHR submods uncovered). It also fails while the shelved LSdF mod is ticked, since both
gate on the High perk, and checks that each addon sits above its own source's set at every pair it serves.

## Install / rerun

1. The eleven downloads in MO2's `downloads/` (names in `stance_sources.SOURCES`). MO2 closed.
2. `python src/StanceMovesets/tools/00-install-sources.py` (skips installed mods; `--force` reinstalls).
3. `python src/StanceMovesets/tools/01-build-stance-overlays.py` — rewrites `mods/Zenderal - Stance Overlays`.
4. `python src/StanceMovesets/tools/02-verify.py` — exits 1 on any problem.
5. Ultra profile (2026-11-10): the overlay mod and the eleven sources ticked next to *Stances - Dynamic Animation
   Sets*, *Zenderal - Le Sentiment du Fer High Stance* unticked (shelved); MO2 order does not matter (no source ships a user.json; 01 refuses if one does). Backups of the earlier
   `modlist.txt` in `E:/Zenderal-backups/2026-11-10-stances/`.

Rerun 01 + 02 after a **For Honor Reforged** change, an OAR `user.json` on an FHR submod, or a source update.

## Not done / open

- **Unverified in game.**
- Leviathan II Greatsword Low Stance: the list has the loose v1.0 (cannot be gated). Its v1.1 (Nexus file 798373,
  2026-08-31) is OAR: download it and add a `('levi', 'oar', None, {5})` layer to Low to get the HEMA greatsword guard.
- Wabbajack: the eleven sources are plain Nexus downloads with `.meta` (no Include rule needed); only the overlay mod
  is ours. Settle Elder Creed – Blade with Kars before compiling.
- First person untouched; NPCs never get it (perks are the player's).
- Optional upgrades from the 2026-11-10 shortlist, not downloaded: Valhalla Greatsword, Leviathan II Greatsword MCO
  Moveset, SkyMA 2H Battleaxe & Warhammer, Realistic Halberd Poleaxe — each one more layer in `stance_sources.py`.
