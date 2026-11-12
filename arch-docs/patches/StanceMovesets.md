# StanceMovesets

- **Source:** `src/StanceMovesets/tools/` — `stance_sources.py` (the source and layer tables), `00-install-sources.py`,
  `01-build-stance-overlays.py`, `02-verify.py` (all three stances). Reuses `src/LSdFHighStance/tools/01-build-lsdf-high-stance.py`
  for the DAR parser, OAR condition builders and the For Honor Reforged exceptions.
- **Ships:** *(no plugin)* MO2 mod `Zenderal - Stance Overlays`: **267 OAR `user.json` files and nothing else** (68 over
  eleven third-party stance sources installed **untouched** from Nexus downloads, 95 lifting the list's sprint submods,
  104 switching Smooth Moveset's idle chain off where a stance owns the idle).
  Must win MO2 over any other mod shipping a `user.json` at those paths (02 checks there is none).
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
| idle, turns, walks, runs, equip (and whatever else the source keeps in those folders: Muay Thai's block idle) | the stance's guard |
| sprint (weapon drawn or sheathed) | the list's sprint mods, as in F4 (Dynamic Sprint, JellyFish one handed Sprint, Smooth Moveset, CATA) |
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
   - **Weapon drawn:** a folder whose author requires `IsWeaponDrawn`, or holding a clip the sheathed state plays
     (`mt_sprintforward`), also gets `IsWeaponDrawn` (see the 2026-11-12 postmortem).
   - **Sprint = F4's:** a stance folder holding any `*sprint*` clip gets `NOT IsSprinting` (01 refuses an attack folder
     with sprint clips), and every enabled third-person OAR submod outside the stances that is sprint-only (all clips
     sprint locomotion, never sprint attacks, or its own conditions require `IsSprinting`, or `ALSO_LIFT`) gets a
     user.json = its winning settings with the priority rank-mapped to 1,600,000,000+ (own order and ties kept): 95
     submods of Dynamic Sprint, JellyFish one handed Sprint, Smooth Moveset, Goetia staves and Patch Collection's
     Crossbow Sprint Swap. 02 checks every one is lifted, unchanged otherwise, in order, and lists any non-lifted
     submod that outranked a lifted one in F4 with overlapping conditions (hands/drawn/sprint/combat evaluated,
     keywords unknown).
   - Priorities: High 1,500,030,000, Mid 1,500,010,000, Low 1,500,020,000, each + 10 × layer: above every FHR /
     Smooth Moveset / Patch Collection moveset submod, below Beam Walking Assist, UNDERDOG's states and RaySense;
     the stances are mutually exclusive by perk. Nordic's out-of-combat folder `31002` is disabled like Desert's
     `32003`.
3. Lost against the copy build: no `$FHFX` heavy tell on these sets, no slot padding (after an FHR directional clip
   hands over a slot past a set's count, that one attack is FHR's neutral clip), and each source's whole folder
   comes along (Muay Thai/Kick Boxing block idles; the packs' sprints are switched off while sprinting, 2026-11-12).

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

## Postmortem: sheathed sprint with a crooked right hand in High / Mid (2026-11-12)

**Symptom (player report, GreaseLord):** in High or Mid, running (sprinting) with the weapon sheathed held the right
hand out at an angle.

**Cause [verified offline]:** the race packs' locomotion folders (Nordic `31001`/`31002`, Desert `32001`/`32003`,
Imperium `33001`/`33002`) ship `male/` and `female/mt_sprintforward.hkx` next to their drawn sprints
(`mt_sprintforwardsword`, `2hm_`/`2hw_`/`dw_sprintforwardsword`). `mt_sprintforward` is the clip the **sheathed**
sprint plays, and OAR's `IsEquippedType` is true for a sheathed weapon, so a gate of perk + player + weapon pair played
the pack's armed sprint pose with no weapon in hand. Nordic's and Desert's authors require `IsWeaponDrawn()` in their
own `_conditions.txt`; 01 evaluated it as true for liveness but never wrote it into the overlay. Imperium's author has
no such test (Low showed the same clip, less visibly).

**Fix:** 01's `needs_drawn`: an enabled folder whose author requires the weapon drawn, or which holds any `mt_` clip
but `mt_sprintforwardsword`, gets `IsWeaponDrawn` after its weapon/combat gate (the six folders above; none holds an
equip clip, so drawing is unaffected). With the weapon sheathed the list's normal sprint (CATA) plays again in every
stance. 02 fails on such a folder without `IsWeaponDrawn` (mutation test: removing it from `31001` → 1 problem).

**Follow-up the same day (curator):** "the sprinting for F1 F2 and F3 is not correct, it's the wrong sprint
animations", with the weapon drawn too. Those same six guard folders carry the packs' NPC drawn sprints
(`mt_`/`1hm_`/`2hm_`/`2hw_`/`dw_sprintforwardsword`) under the clip names the list's sprint mods replace (Dynamic
Sprint 93.9M, JellyFish one handed Sprint 901M, Smooth Moveset, CATA), and the stance band 1.5e9 outranked all of
them. OAR conditions are per folder, so those folders now also carry `NOT IsSprinting`: the stances keep their guard,
walks and runs, and sprint like F4.

**Second follow-up (curator: "the sprint should be the same as F4 ... it's not"):** `NOT IsSprinting` cannot win a
sprint's first frame: the engine sets the sprint flag only after the sprint clip has started. Dynamic Sprint relies on
exactly that (its *Per-Sprint* folders, the sprint start, are gated on `NOT IsSprinting` and interruptible), so the
stances still opened every sprint with the pack's clip instead of Dynamic Sprint's start. Fix: the list's sprint-only
submods are lifted above the stance bands (Mechanism 2), so whatever F4 plays for a sprint wins in every stance; the
`NOT IsSprinting` gate stays for the pairs no sprint mod covers. F4's own winners are unchanged except where a mixed
FHR folder outranked a lifted one: **Gladiator - No Shield Idles** (`weaptypespear`) and **Lancer - Movement and
Idles** (`weaptypeheavylance`): keyword-gated spear/lance weapons, believed absent from the list (not checked: the
plugin scan was stopped). CATA's armor-based sheathed movement is untouched (the stance folders now need the weapon
drawn; Dynamic Sprint already outranked CATA). Unverified in game.

## Postmortem: Smooth Moveset's idles loop in the stances (2026-11-12)

**Symptom (curator's video, OAR log):** after a sprint, standing in F1 with a sword and a lantern, the lantern arm
snapped every ~1.7 s ("we've had a ton of loop animation issues with Smooth Moveset").

**Cause [verified offline]:** Smooth Moveset's idle chain is a state machine. Dynamic Animation Casting casts its
state spells (`mag_start on` 801, `loop on` 802, `move on` 803, `combat on` 804 …) on events that sit in Smooth's
own `1hm_idle` / `2hm_idle` / `dw1hm1hmidle` … clips (`Smooth_loop`, `Smooth_Stop`, `Smooth_Combat`;
`SKSE/Plugins/_DynamicAnimationCasting/SmoothMoveset.toml`). A stance's guard outranks those clips, so the events
never fire, and the clips of the same submod the stance does not replace keep looping the state they were left in:
here the Move Stop option's `1hm move/MLh_Idle` (1.667 s), whose `1hm_idle` sends the `Smooth_Stop` that ends it.
Lifting Smooth's move-stop submods over the stances instead was tried and backed out: it reorders Smooth's own
start/loop chain in F4 (79 overlaps in 02).

**Fix:** 01's `smooth_chain_blocks`: every enabled submod that tests a `Smooth Moveset.esp` effect and shares a
non-sprint clip with an enabled stance folder gets a user.json = its winning settings (Patch Collection's copy where
it wins) + `NOT(stance perk AND the weapon pairs that stance's folders serve)`, one block per stance: 104 submods.
In a stance at those pairs Smooth's chain is off entirely (the left arm falls to the next provider); F4 and pairs no
stance covers keep Smooth. 02 checks every such user.json (mutation test: deleting `1hm move`'s → 1 problem).
Unverified in game. **Rerun 01 + 02 after a Patch Collection rebuild of the Smooth configs** (the user.json carries
their conditions).

**Curator's taste, same day:** Smooth's `1hm / 1hm Non-Combat idle Loop2` (random variant of the relaxed one-handed
idle; ~8-10 s in it lifts the blade over the right shoulder) is `"disabled": true` in Patch Collection's config.json.
01 skips disabled submods, so it writes no user.json there. With a spell in the left hand the shoulder rest came from
the older DAR pack *Smooth Combat non Combat Animation*'s `701332` (male) / `702332` (female) (out of combat,
sword/axe/mace + spell; blade back over the shoulder the whole clip; found in OAR's log): both disabled by OAR
`user.json` in Patch Collection's `DynamicAnimationReplacer/_CustomConditions/70x332/`. The pack's `601332` (crouched
raised guard, any right type 0-4) then took over out of combat, which the curator did not want either: its Patch
Collection `user.json` keeps its weapon conditions and adds `IsInCombat`.

**Install check, same day (Nexus pages read):** FHR 2.4 requires For Honor in Skyrim (meshes + scripts hidden, as its
page says: done), DMK, SCAR 2.01, Maxsu Block Overhaul, Chocolate Poise (Blessed); FHiS requires Smooth Moveset - OAR
and wants FHiS over Smooth; MO2 has FHR > FHiS > Smooth. Smooth's requirements (OAR 3.2.1, OAR IED Conditions, IED
1.7.4, Simple Dual Sheath, Disable Turn Animation, Draw Fix, BDI + Universal Support, DAC NG Plus 3.2.5, no old DAC)
are all installed and OAR's log has no invalid conditions. Missing only the recommended *War Hammer and Battle Axe
Movement Fix*. Smooth's FOMOD options installed: Jormungandr, Warden, Move Stop, Dynamic Sprint. Three main-file
submods are absent from the installed mod since 2026-08-12 (`1hm` / `2hm` / Warden `2hm Heavy Armor` `Non-Combat
idle Start`). Curator (2026-11-12): most likely removed on purpose to stop idles getting stuck in a loop, but an
incorrect install is not ruled out; no record of the removal was found. If they are ever restored (reinstall Smooth's
main file with the same FOMOD options), rerun 01 + 02: the Smooth chain blocks cover whatever submods are installed.

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

Rerun 01 + 02 after a **For Honor Reforged** change, an OAR `user.json` on an FHR submod, a source update, or any
change to a sprint mod (Dynamic Sprint, JellyFish one handed Sprint, Smooth Moveset, Goetia, CATA) or the enabled
mods holding sprint clips.

## Not done / open

- **Unverified in game.**
- Leviathan II Greatsword Low Stance: the list has the loose v1.0 (cannot be gated). Its v1.1 (Nexus file 798373,
  2026-08-31) is OAR: download it and add a `('levi', 'oar', None, {5})` layer to Low to get the HEMA greatsword guard.
- Wabbajack: the eleven sources are plain Nexus downloads with `.meta` (no Include rule needed); only the overlay mod
  is ours. Settle Elder Creed – Blade with Kars before compiling.
- First person untouched; NPCs never get it (perks are the player's).
- Optional upgrades from the 2026-11-10 shortlist, not downloaded: Valhalla Greatsword, Leviathan II Greatsword MCO
  Moveset, SkyMA 2H Battleaxe & Warhammer, Realistic Halberd Poleaxe — each one more layer in `stance_sources.py`.
