# MalphasFixesMerge

- **Source:** `src/MalphasFixesMerge/` (generated: `tools/01-build-malphas-fixes-merge.py`; never hand-edit `Npcs/`)
- **Ships:** `Zenderal - Malphas Fixes Merge.esp` (ESL, HEDR 1.7) in its own MO2 mod, `Zenderal - Malphas Fixes Merge`
  (Wabbajack `NoMatchInclude`). It goes with the third-party **Malphas' Blessing - Fixes** 1.5 (NAUT1CAY, Enderal
  Nexus 822, the plain-plugin version, not SkyPatched), which was installed the same day as MO2 mod
  `Malphas' Blessing - Fixes`.
- **Load order:** MO2: the Fixes mod and this one directly above `Malphas' Blessing`, so the Fixes mod's 18 face files
  win; only lower mods (Malphas' Blessing, Enderal NPC Overhaul) ship the same paths. Plugins:
  `Malphas' Blessing - Fixes.esp`, then this plugin, right after `MB - Unique Aeterna.esp`.
- **FormID block:** none (overrides only)
- **Status:** built and enabled in the three Ultra profiles 2026-11-12. Unverified in game.

## Why

Player report (2026-11-12): Calia in the Purge (`_00E_MC_Calia_Purge 14BE90`) had a black face. The Face
Discoloration Fix only hid it.

- Malphas' Blessing ships her a face file but keeps Enderal's Purge head parts on her record.
- The Fixes plugin replaces only her `HeadParts` with Malphas' own (`00083D`/`000850`), matching that face file.
- Hands of the Prophet, the Jespar replacer installed the day before, was not the cause. Its plugin holds only Jespar's
  two records (`018A9A`, `14BE8F`), and its face files are only those two.

The Fixes plugin overrides 17 NPCs and masters only Malphas' Blessing, so its records are Malphas' or base-game
records plus the fixes. On 7 of them another plugin edits the NPC after Malphas:

| NPC | Winner without the Fixes plugin | Fields taken from the Fixes plugin |
|---|---|---|
| Daddy `024C1E:FS` | EGO | VMAD, Name, HeadParts |
| Phasmalist warrior `025312:FS` | MB - EGO | HeadParts |
| Yuslan `02AE01:FS` | EGO | WornArmor, Name, HeadParts, TextureLighting, TintLayers |
| Tharaêl after Rhalâta `02E8E8:FS` | EGO | WornArmor, Name, HeadParts, TextureLighting |
| Eshra `04CB85` | MB - Unique Aeterna | Name |
| Lex `097C1A` | MB - EGO | Name |
| Tharaêl `13A1CA` | MB - EGO | Name |

On those 7, the Fixes plugin alone would have undone EGO's or Malphas' EGO patches' gameplay changes. This plugin
writes the current winner's record with only the top-level fields the Fixes plugin changes from its own base:
Malphas' record where Malphas has one, otherwise FS's.

- Daddy's VMAD change drops `_00E_CombatSoundtrackScript`, a 2.0 script that 2.1 no longer ships. It is harmless.
- `WornArmor` is Malphas' matching body skin.
- `Version2` and `FormVersion` are ignored as bookkeeping.

The other 10 NPCs, the Purge Calia among them, have nothing after Malphas, so the Fixes plugin wins them as it is.

## Upkeep

Rerun `tools/01` after Malphas' Blessing, its EGO or Unique Aeterna patch, the Fixes mod or EGO changes. Before
rerunning, re-serialize these into `reference/mods/`: `MBFixes`, `MalphasBlessing`, `MBEGO`, `MBUniqueAeterna` and
EGO. Then deserialize into the MO2 mod. The generator re-scans the live Ultra load order. A new plugin that edits one
of the 17 NPCs and loads before the Fixes plugin becomes the base it merges onto, provided it has a reference tree;
otherwise the generator stops.

## To verify in game

- In the Purge, Calia has Malphas' face, not a black one; `tfc` and a close look help.
- Lex, Yuslan and Tharaêl show accented names and Malphas' faces.
- `help Yuslan` shows EGO's stats unchanged.
