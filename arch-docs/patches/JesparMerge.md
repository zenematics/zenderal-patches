# JesparMerge

- **Source:** `src/JesparMerge/` (generated: `tools/01-build-jespar-merge.py`)
- **Ships:** `Zenderal - Jespar Merge.esp` (ESL, HEDR 1.7), its own MO2 mod `Zenderal - Jespar Merge` (Wabbajack
  `NoMatchInclude`). Masters Skyrim, Update, FS, EGO, `Jespar Has Better Steel - Malphas' Blessing.esp` and
  `Hands of the Prophet - A Jespar and Calia NPC Replacer.esp`. **Must load after both of those.**
- **FormID block:** none (one override)
- **Owns:** Jespar's NPC record `_00E_MC_Jespar 018A9A:Skyrim.esm`
- **Status:** built and checked against both sources 2026-11-11, deployed. Unverified in game.

## Why

Curator's request (2026-11-11): install **Hands of the Prophet - A Jespar and Calia NPC Replacer** (Enderal Nexus 1175)
for Jespar only, not Calia.

The mod is installed as MO2 mod *Hands of the Prophet - Jespar Only*, by hand from the archive in `downloads/`, with
exactly the files of its FOMOD's choices **Jespar** + male body texture **Vanilla** (the list's male skin is Tempered
Skins for Males, a vanilla-body texture) + **EGO SE: Yes**. That plugin keeps the archive's filename but holds only
Jespar's records. It sorts above Jespar Has Better Steel, Malphas' Blessing and Enderal NPC Overhaul, the two of which
also ship Jespar's face meshes (`00018a9a.nif`, `0014be8f.nif` and face tints). No other file in the list is
overwritten (checked).

Four plugins already edited Jespar's main record `018A9A` before it:

| Plugin | Changes |
|---|---|
| EGO 1.93.1 | stats/level, perks (4), keywords, combat style, one Steel Dagger |
| Malphas' Blessing (+ MB - EGO) | face |
| Jespar Has Better Steel - Malphas' Blessing (loaded last, so it won) | his own `JesparDagger` x2 instead of the Iron Daggers |

Jespar Has Better Steel is built on the **non-EGO** Malphas' Blessing record, so while it won, Jespar had lost EGO's
perks, stats, keywords and combat style. Hands of the Prophet's EGO plugin is EGO 1.93.1's record (the version
installed) with its own face: keywords, perks and inventory equal EGO's once master indices are resolved. Loading it
last would bring back EGO but drop Better Steel's daggers.

## The fix

Hands of the Prophet's `018A9A` verbatim with only the inventory replaced by Jespar Has Better Steel's
(`JesparDagger` x2 + MQ09 door key `0EAA0D`). The generator asserts both inventories (Hands of the Prophet = EGO's
Iron Dagger + Steel Dagger + key) and that every FormKey the record uses comes from a declared master. In the built
plugin the record differs from Hands of the Prophet's only in `COCT`/`CNTO`, plus Mutagen's two unused padding fields
in `DNAM` (Spriggit writes them as zeros; health, magicka, stamina and skills are byte-identical).

The Purge-quest twin `_00E_MC_Jespar_Purge 14BE8F` needs no merge: only Malphas' Blessing touches it, and Hands of the
Prophet loads after it.

## Upkeep

After an update to Hands of the Prophet or Jespar Has Better Steel, re-serialize them into
`reference/mods/HandsOfTheProphet/Jespar EGO` (the archive's `02. EGO SE\Jespar` plugin) and
`reference/mods/JesparHasBetterSteel`, rerun `python -I src/JesparMerge/tools/01-build-jespar-merge.py`, rebuild and
copy the `.esp` into the MO2 mod. An EGO update needs the same check: the Hands of the Prophet plugin carries EGO
1.93.1's fields.

## To verify in game

Meet Jespar (prologue camp, or `prid 00018A9A` + `moveto player`): Hands of the Prophet's face with no dark face or neck
seam, and two Jespar Daggers (`openactorcontainer 1` on him). Calia keeps Malphas' Blessing's face.
