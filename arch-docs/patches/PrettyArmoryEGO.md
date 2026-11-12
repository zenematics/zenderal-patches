# PrettyArmoryEGO

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/PrettyArmoryEGO/`
- **Ships:** `Zenderal - Pretty Armory EGO Patch.esp`
- **FormID block:** none (overrides only)

## What it does

**GENERATED — never hand-edit the record folders.** 141 overrides (ARMO/WEAP/AMMO/ARMA/PROJ/NPC_) of records the 11 Pretty * plugins revert. Each = the in-game WINNER's record (Pretty's meshes/armatures/outfits/items; for 2 Heavy Leather records the winner is `Enderal Remastered Armory - Heavy Leather.esp`) with the DONOR plugins' gameplay changes forwarded: donors = EGO, `Enderal SE - Bug Fixes.esp`, the two AOS plugins. Field policy lives in the docstring of `src/PrettyArmoryEGO/tools/02-merge-pretty-ego.py`: models/armatures/bounds/templates/outfits/items always the winner's; ARMA only takes FootstepSound + AdditionalRaces; Keywords set-merged; `BodyTemplate` merged per sub-field (FirstPersonFlags from Pretty, ArmorType from EGO); names compared on the English string (EGO and Pretty are both non-localized), where an actual Pretty rename wins. Compression flags (`IsCompressed`/`MajorRecordFlagsRaw`/`MajorFlags: 0x40000`) are ignored — EGO's NPC overrides differ from base there only by storage. Pretty Unique Armory ships 3 weapon descriptions as UTF-8 Russian decoded as cp1252 (`Ð°Ð½…`); the generator detects that and restores EGO's English. **Regenerate: `01-build-override-chains.py` (reads the live MO2 profile via `tools.json`'s `modlistRoot`), then `02-merge-pretty-ego.py`, then `03-forward-npc-faces.py`, then `04-restore-pretty-meshes.py`**, after re-serializing the Pretty plugins to `reference/mods/Pretty/` and the donors to `reference/mods/PrettyContext/`. Masters: the base three + EGO + every Pretty plugin it overrides + ERA Heavy Leather — so the engine enforces load-after

## NPC faces: `tools/03` (2026-10-28)

Reported by a beta player: Tealor's Malphas' Blessing face didn't show, and moving `Malphas' Blessing - Enderal.esp`
below this patch fixed it. Tealor `01ADF1` is one of the patch's 5 NPC records. His live chain is base → EGO →
Pretty Holy Order Grandmaster → Malphas' Blessing → MB - EGO. 02 had taken his `HeadParts` from Pretty and his
`WornArmor` from base, and this patch loads last, so it put the old head and skin back under MB's baked FaceGen
mesh. **[verified]** by field diff across all six records.

`03-forward-npc-faces.py` finds, for every NPC in the patch, the face **owner**: the last plugin in the live
chain that changed any face field (`HeadParts`, `HairColor`, `HeadTexture`, `FaceMorph`, `FaceParts`,
`TintLayers`, `TextureLighting`, `WornArmor`, `Height`, `Weight`) from base. It copies that plugin's whole face
group, so the fields always match one FaceGen mesh, and adds the plugins those fields name as masters, in live
load order. Tealor now has MB - EGO's head parts and MB's skin `000831` (plugin masters
`Malphas' Blessing - Enderal.esp`), plus Pretty's outfit and EGO's perks, skills and combat style. The four
MQ07a enemies keep base faces.

No other Zenderal plugin overrides any of MB's 50 NPCs. A full 02 rerun currently stops: the chains now name
plugins without reference trees, starting with `Zenderal - 2.1 Levelsystem Cleanup.esp`. MB and MB - EGO were
serialized to `reference/mods/PrettyContext/`. Rebuilt into Patch Collection's copy (the only one); backup in
`E:/Zenderal-backups/2026-10-28-pretty-armory-ego-pre-tealor-face/`. Unverified in game.

## Compared with PEA - EGO Patch; Unique Sets, the visual winner, tool 04 (2026-10-30)

The curator downloaded the Nexus **PEA - EGO Patch** (Enderal mod 1143, 1.0; `EGO - PEA - ALL IN ONE.esp`, 187
records, plus Moonsteel mace/warhammer meshes) to see whether it should replace this patch. Field-by-field against
the live load order (PEA serialized to `reference/mods/PEAEGO/`): 87 records identical, about 50 more differ only in
`EditorID`. **Kept ours**: PEA would have reverted Tealor's Malphas' Blessing face, ERA's Heavy Leather
gauntlets/boots, Pretty Enderal Armory - Fixes' Iron Sword of Flames, Pretty Holy Order's Isle of Kor robes,
Enderal SE - Bug Fixes' critical data on the Lishari and Skaragg staves, Unique Amulet Replacer's Meadow Spirits
amulet and Pretty's keywords on the oak bows, and it lacks Zar'Ah's armour and the MQ07a NPCs. **What PEA had that
we lacked, now folded in:**

- **Pretty Unique Sets was never in `reference/mods/Pretty/`**, so 02 never saw it, and it reverted EGO on 8 records
  (Enigmatic Nomad hood/cuirass/boots: EGO's Clothing at weight 3 came back as 15.3-armour light armour at weight 4;
  Selna's Wings, Fallen One cuirass, Mage Nemesis helmet, Inodan cape, Wanderer boots' footstep sound). Serialized
  it; 7 of the 8 now resolve to `Zenderal - 2.1 Levelsystem Cleanup.esp` (Pretty's record minus `010AA2`), so that
  plugin's live copy (Patch Collection's) is serialized to `reference/mods/PrettyContext/` and it becomes a master.
  Our versions match PEA's apart from keeping the cleanup (PEA's re-add `010AA2`).
- **02's winner is now the *visual* winner** (`visual_winner()`): the last plugin in the chain that is neither a
  donor nor a face mod (`FACE_MODS`: Malphas' Blessing + MB - EGO). Audio Overhaul now loads after the Pretty
  plugins, so `chain[-1]` gave its vanilla meshes and the generator wrote nothing: Pyrean boots and Stormcloak
  boots (in the old output) would have dropped out, and Barkeeper shoes, Redguard boots and Yarl shoes had already
  shown vanilla meshes in game. All 5 now carry Pretty's armature with AOS's footstep sound; Tealor is unchanged.
- **`OWNED_ELSEWHERE`**: the 3 Moonsteel battleaxes now belong to `Zenderal - Moonsteel Pretty Patch.esp` only
  (identical content but EditorID; this patch had been overriding them from later in the load order).
- **`04-restore-pretty-meshes.py`**: 4 records no Pretty plugin overrides, where EGO's model swap hides a Pretty
  mesh at Enderal's own path: Tharael's Bow `02C5E9:FS` (NordHeroBow), Leaf Dancer's Bow `0670F5` (sabre-cat bow),
  Steel Arrow `05BB24` + `ArrowSteelProjectile 03BE12` (the steel arrow shown is ERA Part 1's loose mesh). EGO's
  record with Model/FirstPersonModel/ObjectBounds from the base record, as the Moonsteel patch does.
- **Not taken:** PEA's 13 circlet/diadem, Rhalata novice robe and Nomad amulet hookups. They point at armatures
  (`000823–00082B:Pretty Unique Armory`, `00082E:Pretty Factions`, `000806:Pretty Unique Sets`) that the list's
  Pretty **2.0** plugins (2026-09-26) don't have: a newer Pretty release added them. Enabling PEA's plugin as-is
  would make those items invisible. Revisit after updating the Pretty packs.
- **PEA's Moonsteel mace/warhammer meshes** (`meshes/dlc02/weapons/nordic/*`, Nordwar steel textures) are used:
  only EGO's Moonsteel mace/warhammer `005E71–74` and statics `005E62/64` point there. In the MO2 mod
  `PEA - EGO Patch` the plugin and `textures/cubemaps/metalic_e.dds` are `.mohidden` (that cubemap is shared with ERA
  Part 1, Pretty Rune and four Pretty texture BSAs; PEA sits at the top of the MO2 order and would win it).

Result: 153 records (was 141). Round-trip identical. Deployed 2026-10-30 into `Zenderal - Patch Collection` (the
only copy; previous one and the Ultra `modlist.txt` in `E:/Zenderal-backups/2026-10-30-pretty-armory-ego-unique-sets/`)
and `PEA - EGO Patch` enabled in Ultra (its plugin stays hidden, so `plugins.txt` is unchanged). Unverified in game.

## Pretty 2.1 (2026-11-11)

A Nexus comment from Pretty's author: the uploaded patch mastered `Pretty Enderal Armory - Fixes.esp`, which
Pretty 2.x no longer ships, so it would not load for players on 2.x.

**What changed in the list:**
- The list moved to Pretty 2.1: the FOMOD All in One (`FOMOD All in One 1072 2.1 2026-10-24T23-02Z kRAb8iuYn.7z`),
  installed into the per-pack MO2 folders with the list's existing choices:
  - Unique Sets: Honorable Knight;
  - Pyrean and Grandmaster: the vanilla plugins.
- Gone: Fixes, Pretty Enderal Backpacks (now in Clothing) and the Clothing Hotfix.
- New: `Pretty Rune Armory.esp`. All 2.1 plugins are ESL at HEDR 1.71. No record here references a Pretty form
  below `0x800`, so the patch stays 1.7.

**2.1 is loose, 2.0 was BSAs**, so a Pretty file now beats lower-priority loose mods it used to lose to:
- 79 such files were left out of the install to keep the old winners: shared cubemaps against TB's HD /
  Seamless Cubemaps, plus single textures from SMIM, Tempered Skins, Fluffworks, SRP and others.
- Also left out: 3 Pretty-vs-Pretty files where MO2 order would pick a different copy than the FOMOD's order.
- Not left out: CBBE (about 230 female meshes) and ERA Part 1 (Righteous Path paths). Pretty was always meant to
  win those, so `Zenderal - Pretty Female Mesh Restores` is retired (unticked).
- The list of left-out files and the install script are in `E:/Zenderal-backups/2026-11-11-pretty-2.0/`, with the
  2.0 folders.

**Generator changes:**
- **01 stops at this patch's own load position.** Plugins after it win anyway, and mastering one breaks load order.
  `Zenderal - 2.1 Levelsystem Cleanup.esp` had been loading before this patch (line 415 vs 438, against its own
  "load last" rule), so this patch mastered it and 7 records came from it. It now loads just before Unresolved
  References Cleanup, in all three Ultra profiles, and its cleanup applies after this patch.
- `PG_1.esp` (PG Patcher, late) wins 2 Rhalata robes, which is why rerunning PG Patcher matters.
- **01 `--standalone` + `05-build-nexus-standalone.py`: the Nexus build is Pretty × EGO only.**
  - Its chains hold only base + EGO/donors + Pretty plugins, and it skips 03.
  - It masters no list-only mod. The list build masters Malphas' Blessing (Tealor's face, 03) and ERA Heavy
    Leather (2 winners).
  - 05 puts the list's record folders back and writes `E:/Nexus uploads/Zenderal - Pretty Armory EGO Patch.7z`.
  - Run it after every list regeneration.

**Result:** 158 records, against 153 before:
- removed: the 4 Fixes-only records (Barkeeper shoes addon, Zaraah's three playable pieces; EGO now wins them
  directly) and the Mended Sword (2.1 no longer touches it);
- added: 9 records 2.1 now covers: 5 circlets, Circlet of Shadows, the Meadow Spirits amulet, and the Rhalata
  novice robes (PEA's former "not taken" hookups).

Masters: base, EGO, the 11 Pretty plugins, Malphas' Blessing, ERA Heavy Leather. Deployed into Patch Collection.
The Nexus copy masters base + EGO + the 11 Pretty plugins. Unverified in game.

**One MO2 mod (2026-11-12).** For tidiness, 14 of the 15 per-pack folders are merged into a single
`Pretty Enderal Armory`, as the FOMOD installer would build it:
- later packs overwrite earlier ones in the FOMOD's order;
- the 79 left-out files stay out;
- it sits at Holy Order's old spot, below ERA Part 1 and Adventurer HDT-SMP, which keep winning their files.

**`Pretty Righteous Path Armory` stays its own mod above ERA.** Knight of the Path needs Pretty's Righteous Path to
beat ERA's, and ERA must beat every other pack.

Checked against the old layout: 5359 paths, and only one has a different winning file:
`textures\kreis\ksmc\elmlock\head_n.dds`. It is now Factions' copy, which is what the FOMOD order picks; Unique
Sets' copy had been winning.

The generators that read Pretty files now read the merged folder: EsmeDressStatic, DragonPriestStaffSwap,
MoonsteelPretty 02 and PrettyRighteousPathSMP. Their reruns gave byte-identical output.

Backups of the emptied per-pack folders (meta.ini only) and Ultra's previous `modlist.txt` are in
`E:/Zenderal-backups/2026-11-12-pretty-merge/`.
