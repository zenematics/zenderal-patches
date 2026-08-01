# Scripting and repurposed ActorValues

**Primary source:** `reference/base/EnderalScripts/source/scripts/` — 5029 **real** `.psc` files
shipped by SureAI in `ScriptsEnderal.zip`, not decompiles. Read these; never run Champollion on an
Enderal script.

## Naming convention

Enderal's own scripts are prefixed **`_00E_`** — 1257 of them. **[verified]** Secondary prefixes seen
in the tree: `_00E_FS_` (Forgotten Stories), `_00E_A0_`–`_00E_A3_` (ability/talent tiers),
`_00E_Class_` and `_00E_Affinity_` (progression), `_00E_Game_` (core systems), `_00E_Phasmalist_` /
`_00E_Theriantrophist_` (FS classes), plus `_fs_`, `_sag_`, `_60E_`, `_40E_`.

Auto-generated Papyrus fragments keep Bethesda's conventions: `tif__########` (topic-info
fragments), `qf__*` (quest fragments), `PRKF_*` (perk fragments), `pf_*` (package fragments).

## The 55 overridden vanilla scripts

Enderal ships its own copy of 55 script names that also exist in vanilla. **All 55 differ from the
vanilla file — not one is an accidental identical duplicate.** **[verified]** by byte comparison of
`reference/base/EnderalScripts` against `reference/base/VanillaScripts`.

Two are explicit `; DUMMY, DO NOTHING` stubs — Enderal has **deleted the vanilla brawl/intimidate
system**: **[verified]**

| Script | Vanilla | Enderal |
|---|---:|---:|
| `dgintimidateplayerscript.psc` | 59 lines | **4 lines** |
| `dgintimidatealiasscript.psc` | — | stub |

The rest are real modifications: the `critter*` family, `default*` handlers, `dragonactorscript`,
`fx*` effects, and so on.

> **This is why compile import order matters.** The Papyrus compiler's `-i` path is **first-wins**
> **[verified]**, so Enderal's tree must come first. Compile against vanilla's copy and you link in
> brawl logic Enderal deliberately removed. It fails at *runtime*, not at compile time — there is no
> error to see. Full detail in CLAUDE.md → "The import path is first-wins".

## Repurposed vanilla ActorValues

**This is the highest-value section in this document.** Enderal stores several of its own stats in
vanilla ActorValues, because the engine's AV list is fixed and Papyrus can't add to it. A patch that
touches these AVs for their vanilla meaning will corrupt an Enderal system, and nothing will warn
you.

| Vanilla AV | Actually holds | Evidence |
|---|---|---|
| **`LastFlattered`** | **Arcane Fever** (stored negated) | `_00E_FS_AlchAddArcaneFever`: `akTarget.ModAV("LastFlattered", -fArcaneFeverAdd)` then displays `-1*(akTarget.GetAV("LastFlattered"))`. 28 uses across the tree. **[verified]** |
| **`DragonSouls`** | **Memory Points** (display mirror of the `TalentPoints` global) | `Game.GetPlayer().SetAV("dragonsouls", TalentPoints.GetValueInt())` in `_00e_class_perkscript.psc`, `_00e_erinnerungslehrbuch.psc`, `_00e_lehrbuch_plus1memorypointsc.psc`, `_00e_mqp03_functions.psc` and others. 8 uses. **[verified]** |

### Rules

1. **Never write `LastFlattered` or `DragonSouls`** for their vanilla purposes. You are writing
   Arcane Fever and Memory Points.
2. **Arcane Fever is negative.** `GetAV("LastFlattered")` returns the negation; display code
   multiplies by −1. Get the sign wrong and you cure the player by poisoning them.
3. **Memory Points have two sources of truth.** `TalentPoints` (GlobalVariable) is authoritative;
   the AV is a mirror for the UI. Update both or the menu desyncs.

### Finding more of them

This list is what a scan of the shipped source turned up. Re-run it after any Enderal update:

```bash
cd reference/base/EnderalScripts/source/scripts
grep -rhoiE '(Mod|Get|Set|ForceA|Damage|Restore)AV\("[A-Za-z]+"' . \
  | grep -oiE '"[A-Za-z]+"' | tr -d '"' | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn
```

Anything with a high count that isn't an obvious combat stat deserves a look. Current top hits
**[verified]**: `health` 62, **`lastflattered` 28**, `aggression` 26, `speedmult` 20, `magicka` 19,
`stamina` 11, **`dragonsouls` 8**, `carryweight` 8, `assistance` 7.

## Core controller scripts

Where the systems live. Read the script before patching anything near it.

| System | Script | Notes |
|---|---|---|
| Character menu, classes, affinities | `_00E_Game_SkillmenuSC` | ReferenceAlias, 1082 lines, registers for `"Journal Menu"` |
| Leaving the menu | `_00E_Game_SkillmenuLeaveSC` | |
| XP / levelling | `_00E_EPUpdateFunctions` | owns `PlayerExp`, `PlayerLevel`, `PlayerNeededExp`, `Lernpunkte`, `Handwerkspunkte`, `TalentPoints` |
| Talent tier lookup | `_00E_TalentLibrary` | `GetPlayerTalentLevel`, `GetTalentLevel` — global functions |
| Talent activation / cooldown | `_00E_Game_TalentControlSC`, `_00E_Game_TalentCooldownSC` | |
| Class recalculation trigger | `_00E_Game_CalculateClassSC` | ObjectReference trigger box; calls `Player.GetPlayerClass()` on `OnTriggerLeave` |
| Perk purchase | `_00E_Class_PerkScript`, `_00E_Class_OpenClassMenuScript`, `_00E_ClassMenuEScript` | |
| Player setup | `_00E_PlayerSetupScript` | |
| Shared helpers | `_00E_PlayerFunctions`, `_00E_QuestFunctions` | imported widely |
| Arcane Fever | `_00E_ArkanistenfieberEffect`, `_00E_FS_AlchAddArcaneFever`, `_00E_ArkanistenfieberTriggerbox` | German *Arkanistenfieber* |
| Phasmalism (FS) | `_FS_Phasmalist_ControlQuest`, `_00E_Phasmalist_*` (~25 scripts) | apparitions, souls, workbench |
| Theriantrophy (FS) | `_00E_Theriantrophist_*` | werewolf, chymikum alchemy |
| Player housing | `_00E_PlayerHousing*` (~12 scripts) | build mode, furniture |

## Working with Enderal scripts

- **Read, don't decompile.** Real source ships in `ScriptsEnderal.zip`. Champollion output is a
  reconstruction with auto-named variables and lost comments.
- **Don't ship a modified `_00E_` file** unless overriding it *is* the fix. A `.pex` with the same
  filename wins or loses purely on MO2 conflict order, and the loser is invisible. If you must, say
  so explicitly in the patch's notes and in `arch-docs/zenderal-curation.md`.
- **Some shipped `.psc` contain stray non-UTF-8 bytes** (German text in comments). `grep` may report
  "binary file matches" — pipe through `tr -d '\000'` or use `grep -a`. **[verified]** on
  `_00e_game_skillmenusc.psc`.
- **Enderal is pinned to SSE 1.5.97.** Any SKSE `.dll` a script depends on must be a 1.5.97 build.
- **The compiler needs all three source trees** — Enderal, SKSE, vanilla — in that order, and the
  flags file `TESV_Papyrus_Flags.flg` only exists in the vanilla tree. See the `papyrus-compile`
  skill.
