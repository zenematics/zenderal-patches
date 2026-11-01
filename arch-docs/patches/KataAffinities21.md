# KataAffinities21

- **Source:** `src/KataAffinities21/` (generated: `tools/01-port-affinitycontrol.py`,
  `tools/02-build-cleaned-kata.py`, `tools/03-build-quest-override.py`)
- **Ships:** `Zenderal - KataPUMB Affinities 2.1.esp` (ESL, HEDR 1.7) + `Scripts/_00E_AffinityControl.pex` (+ source)
- **Needs on the user's machine:** the cleaned Kata copy that `tools/02` generates. It is never shipped.
- **FormID block:** none (one override)
- **Status:** built and compiled, round-trip clean; deployed to `Ultra` 2026-10-21. Plugins 236
  (`KataPUMBAffinities.esp`, from the cleaned copy), 240 (EGO patch) and 241 (this). `tools/04`: no
  trigger. **Unverified in game**

## Why it exists

KataPUMB New Affinities (Enderal Nexus 190, 2.1.0) adds 24 affinities: Acrobat, Berserker, Dragon
Hunter, Duelist, Knight, Rift Mage, Slayer, Spell Sword, Thief, Wanderer, White Mage, Bard, Enchanter,
Shadow Caster, Custodio, Highlander, Lunatic, Mercenary, Monk, Pack Leader, Poisoner, Soul Reaper,
Witcher and Wolf Hunter. It was built on Enderal 2.0's level system:

- a modified **`_00E_Game_SkillmenuSC`**, shipped in `KataPUMBAffinities.bsa` with its `.psc`;
- an override of **quest `Levelsystem 010AA2:Skyrim.esm`**, the 2.0 level-system quest whose VMAD fills
  that script's new properties.

**Enderal SE 2.1 removed both.** The level system moved into `EnderalSE.dll`. Its
`CheckIncompatibleMods()` (`fs_src.zip`, `Util.h`) runs once at data load. It pops *"OUTDATED MOD: One of
your mods modifies the Levelsystem quest or its scripts"* if any of these is true:

- `scripts/_00e_questfunctions.pex` exists;
- `scripts/_00e_game_skillmenusc.pex` exists;
- `LookupForm<TESQuest>(0x10AA2, "Skyrim.esm")` finds a quest.

`010AA2` does not exist in 2.1's masters, so Kata's plugin *re-creates* the whole 2.0 quest: a startup
stage, player aliases, and the `_00E_ConfigMenu`/`_00E_QuestFunctions`/skill-menu scripts. That would
run the old level system beside the DLL's. So the mod was disabled during the 2.1 migration, together
with its EGO patch and the Amnesia KataPUMB add-on.

2.1 keeps affinities in **`_00E_AffinityControl`**, the alias script on FS quest
**`AffinityControl 01597B`**. `EnderalFunctions.GetPlayerClassNameGlobal()` reads it for the Hero Menu.
It kept 2.0's helpers under the same names and signatures: `RegisterAffinity`, `TryUnlockAffinity`,
the `PerkTree_*Index` variables and the 21-slot arrays. That makes Kata's edit portable.

## The fix

1. **`tools/01`** ports Kata's three marked blocks verbatim onto 2.1's source
   (`papyrus-source/enderal-2.1.4.4`):
   - the 24 `RegisterAffinity(21..44, …)` calls;
   - the 24 `;KATAPUMB EDITS` unlock rules in `UpdateUnlockedAffinities()`;
   - the 72 property declarations (24 `Spell`, 48 male/female `Message`).

   Every affinity array grows from 21 to 45, including the two non-SKSE fallbacks.
   `_GetScriptVersion()` stays `1`: `_00E_AffinityControl` is on the DLL's script-version list
   (`Util.h`, `scripts["_00E_AffinityControl"] = 1`), and changing it would bring back the
   *"Script … is overwritten"* popup. Kata's other 2.0 hunks were deliberately not taken. They are
   skill-menu-only: `GetMaximumValue` modifiers, `bReadyToOpen` and `Game.UnlockAchievement`, and the
   DLL fills the Hero Menu now. Compiled from the compiler's own folder with only our source and 2.1's
   tree as imports: 0 errors, 0 warnings.
2. **`tools/03`** overrides `01597B` with FS's record verbatim. It appends the 72 properties to alias 0's
   `_00E_AffinityControl`, each filled with the `KataPUMBAffinities.esp` record whose EditorID equals
   the property name; all 72 must resolve. Properties are written case-insensitively sorted, the order
   Spriggit uses. No list plugin overrides `01597B` (binary scan of `Ultra`, 2026-10-20). The only
   round-trip difference is FS's localized objective text (`<Alias=AliasName>` in 11 languages, all
   identical), which this unlocalized plugin stores once.
3. **`tools/02`** writes **`KataPUMB New Affinities - Enderal 2.1 (Zenderal cleaned)`** from the user's
   install. The original mod is left untouched and disabled; the curator approved a cleaned copy on
   2026-10-20. The copy contains:
   - `KataPUMBAffinities.esp` under the same filename (the EGO patch masters it), with `QUST 010AA2`
     removed and nothing else changed. The script asserts that no other record references it;
   - Kata's 9 `kata_*.pex` as loose files, minus `_00e_game_skillmenusc.{pex,psc}`. The copy has no BSA.

   Amnesia Shrine 4.00 needs nothing: none of its scripts reference affinities. The old *AmnesiaShrine
   KataPUMBA Affinities BSA loader* was just a merged 2.0 skill-menu script and stays retired.

**Load order:** `KataPUMBAffinities.esp` → `EGO SE - KataPUMB New Affinities.esp` (it also masters EGO)
→ `Zenderal - KataPUMB Affinities 2.1.esp`. **`tools/04-check-levelsystem-triggers.py`** confirms that no
enabled mod ships `_00e_game_skillmenusc.pex` or `_00e_questfunctions.pex`, loose or in a BSA, and that
no plugin defines `010AA2`. Run on 2026-10-20 with this setup, it found none. The positive control (the
original Kata mod passed as enabled) reports both its BSA script and its quest.

**Existing saves:** 2.1's `OnPlayerLoadGame()` re-runs `InitAffinitySystem()`, which rebuilds the
arrays at 45 slots and resizes `affinitiesUnlocked` (2.1 code). The new properties are not in the save,
so they come from the plugin.

## Test in game

- No *Levelsystem* popup at the main menu.
- The Hero Menu still shows a class name.
- With 10 points each in Trickery and Bladedance (Derwish), choosing an affinity offers **Acrobat**.

## Regenerating

After a Kata, EGO-patch or Enderal update:

1. Re-extract `KataPUMBAffinities.bsa` into `src/KataAffinities21/build/kata` (gitignored).
2. Run `tools/01`, then recompile.
3. Re-serialize the esp into `reference/mods/KataPUMBAffinities`, then run `tools/03`.
4. Run `tools/02` with MO2 closed.

If 2.1's `_00E_AffinityControl` changes, `tools/01` re-ports onto it and asserts every anchor.
