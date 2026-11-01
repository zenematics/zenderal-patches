# Marksman Rename

- **Ships:** `Zenderal - Marksman Rename.esp` (ESL, HEDR 1.7), its own MO2 mod *Zenderal - Marksman Rename*
- **Source:** `src/MarksmanRename/` (generated: `tools/00-find-archery.py` → `tools/01-build-marksman-rename.py`)
- **Load:** after `EGO SE - KataPUMB New Affinities.esp`, the last plugin whose records it copies
- **Status:** built and installed 2026-10-29, unverified in game

## Why

Curator's taste (2026-10-29): "any mention of Archery as a skill across learning books, passives, talents is changed
to the wording Marksman". Enderal's own interface already calls the skill Marksman (`interface\translate_english.txt`
in `E - Misc.bsa`: `$Archery	Marksman`; the AVIF `AVMarksman 00044E` is named Marksman), but record text kept
SureAI's, EGO's and the add-ons' "Archery".

## What

33 winning records, copied from their winners with only the English display strings changed (34 strings; a
localized base record keeps every other language untouched):

| Group | Records |
|---|---|
| Learning books | the four `_00E_LehrbuchSpellMarksman25/50/75/99` effects' descriptions ("Increases Marksman for Apprentice…"); the books' own names already said Marksman |
| Level-up message | `_00E_Levelsystem_sSkillNameMarksman 036FD1` ("Increased Marksman by…") |
| Fortify effects | `AbFortifyArchery 023163`, `AbFortifyArcheryHidden 045DC8`, EGO's `EnchFortifyArcheryConstantSelf 07A0FE`, 12 `Fortify Archery` enchantments (base + EGO) |
| Potions | EGO's three `0?E_Bogentrank` ("Marksman Potion (…)") |
| Affinities | Enderal's Arcane Archer `143349` (EGO's text), KataPUMB's Acrobat, Dragon Hunter, Highlander, Wolf Hunter (EGO KataPUMB New Affinities' text) |
| Others | Amnesia Shrine's book menu button `00E221`, Loop's two pistol effect descriptions, Triumvirate's "Fortify/Drain Weapon Skills - Marksman" effects |

Left alone: the placeable "Archery Target" (`141014`, the object), Prophecy's tree "Arcane Archery", dialogue
(`DialogTopics` not scanned), actor-value keys and EditorIDs. Records **our own plugins** win are fixed in their own
generators instead (one owner per record): Flame Shot's Wayfarer affinity `14334A`, Prophecy's Marksman stat
talents and its `ZP_ORD_Arc_ArcheryOnHit_Spell` name (`marksman()` in Prophecy's `tools/01`, applied to everything it
writes).

Not in a plugin: UIExtensions' own `interface\translations\uiextensions_english.txt` still maps `$Archery` to
"Archery" (list menus); a loose copy would fix it.

## Regenerating

After any winner changes (EGO, KataPUMB, Triumvirate, Loop's pistols, Amnesia Shrine):

1. `python src/UnresolvedRefsCleanup/tools/00a-serialize-all.py <scratch>/all` (every enabled plugin, ~25 min)
2. `python src/MarksmanRename/tools/00-find-archery.py <scratch>/all <scratch>/archery.json`
3. `python src/MarksmanRename/tools/01-build-marksman-rename.py <scratch>/all <scratch>/archery.json`, then deserialize

The 2026-10-29 run: four plugins did not serialize (Ark Bridge Overhaul - EPPI Improved Locations Patch,
UndercityCutContent, TempleCutContent, UndercityHome - cells and locations, no skill text).
