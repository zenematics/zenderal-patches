# SPID — Spell Perk Item Distributor: reference

> **Scope.** How SPID 7.3.x actually behaves, rebuilt from the upstream source rather than
> paraphrased from the Nexus article. For what changes about SPID **inside Enderal**, read
> [`spid-in-enderal.md`](spid-in-enderal.md) — that is where the Zenderal-specific traps live.
>
> The article is powerof3's
> [*SPID: The Complete Reference*](https://www.nexusmods.com/skyrimspecialedition/articles/6617)
> (current as of SPID 7.3.0). It is the best introduction to the syntax and you should read it.
> **Where this file and that one disagree, this one wins** — every disagreement is flagged inline
> with *"the article says …"* and cites the source file that settles it.
>
> Facts marked **[verified]** were read off this machine on 2026-08-13: the installed 7.3.2 DLL, the
> upstream source at `github.com/powerof3/Spell-Perk-Item-Distributor` (`SPID/src/`), CLIBUtil
> (`github.com/powerof3/CLIBUtil`, `include/CLIBUtil/`), or the SPID log from a live Enderal run on
> 2026-08-09. Unmarked statements are summary.

## What SPID is

An SKSE plugin that adds **spells, perks, items, shouts, packages, outfits, keywords, factions and
skins to NPCs at runtime**, driven by plain `.ini` text files. No plugin, no ESP, no record edits.

Because it works on the loaded data in memory, a SPID config behaves like a virtual plugin that
applies last in the load order, and installing or removing one is generally save-safe. **The one
exception is Outfits** — see [Outfits are persisted](#outfits-are-the-exception-to-leaves-no-trace).

### Which build, and does it run here

| | |
|---|---|
| Installed in this list | `zenderal/mods/Spell Perk Item Distributor/SKSE/Plugins/po3_SpellPerkItemDistributor.dll` |
| FileVersion | **`7.3.2.1597.0`** — the trailing `1597` marks the **1.5.97 (SE, pre-AE)** build **[verified]** |
| Minimum runtime | `SKSE::RUNTIME_SSE_1_5_39` (`SPID/src/main.cpp`, `SKSEPlugin_Query`) |
| Enderal's runtime | 1.5.97 — the live log opens with `Game version : 1-5-97-0` **[verified]** |
| Hard requirement | Address Library for SKSE Plugins |
| Soft requirement | **powerofthree's Tweaks** — see [EditorIDs need po3_Tweaks](#editorids-need-po3_tweaks) |

Enderal SE is SSE 1.5.97, so the ordinary **SE** download is the correct one. An AE build loads
nothing (CLAUDE.md, "Engine / SKSE version").

### Its own settings file

`Data\SKSE\Plugins\po3_SpellPerkItemDistributor.ini` **[verified]** — `SPID/src/main.cpp`,
`InitializeLog`:

```ini
[Log]
;  Log level for SPID. Valid values: trace, debug, info, warn, error, critical.
;  Use 'debug' to enable verbose per-NPC/outfit distribution logging.
LogLevel = info
```

SPID **creates this file if absent and re-saves it on every launch**. `debug` is what turns on the
per-actor outfit chatter; `info` already logs the per-NPC `[📦] Distribution for …` blocks.

---

## How configs are found

SPID calls `clib_util::distribution::get_configs("Data\\", "_DISTR")`
(`SPID/src/LookupConfigs.cpp` → CLIBUtil `include/CLIBUtil/distribution.hpp`). That function is
twelve lines long and every one of them matters: **[verified]**

```cpp
for (const auto iterator = std::filesystem::directory_iterator(a_folder); const auto& entry : iterator) {
    if (const auto& path = entry.path(); !path.empty() && path.extension() == a_extension) {
        if (const auto& fileName = entry.path().string(); a_suffix.empty() || fileName.rfind(a_suffix) != std::string::npos) {
            configs.push_back(fileName);
        }
    }
}
std::ranges::sort(configs);
```

1. **`directory_iterator` is not recursive.** The `.ini` must sit **directly in `Data\`**. A
   `_DISTR.ini` in `Data\SKSE\Plugins\` or any other subfolder is never seen, and nothing warns you.
   In MO2 terms: at the **root of the mod folder**, next to where an `.esp` would go.
2. **The extension must be exactly `.ini`.** `.ini.txt`, `.INI` on a case-sensitive share, or a file
   MO2 has hidden as `.ini.mohidden` are all invisible.
3. **`_DISTR` is matched as a substring of the whole path, not as a suffix.** Anything ending `.ini`
   with `_DISTR` anywhere in its name loads — `MyMod_DISTR_backup.ini` and `MyMod_DISTR_OLD.ini`
   both do. To disable a config, change the **extension** (`…_DISTR.ini.disabled`); renaming around
   the `_DISTR` does nothing.
4. **Ordering is `std::ranges::sort` over the raw path strings — ASCII, case-sensitive.** Uppercase
   sorts before lowercase, so `NPCs Take Cover__DISTR.ini` loads *before* `kco_stw_DISTR.ini`.
   *The article says "orders them alphabetically from A to Z"*, which reads as case-insensitive.
   The live log's order confirms the ASCII behaviour. **[verified]**

Load order matters because entries of each type are distributed in the order they were read — file
order first, then line order within a file.

### Two mods shipping the same filename silently collide

`_DISTR.ini` files are ordinary loose files, so **two mods that ship the same filename are a normal
MO2 file conflict and only the winner is deployed.** SPID never sees the loser and never mentions
it.

This is live in the Zenderal list right now: **[verified]**

```
$ find mods -iname "*_DISTR*.ini" | wc -l
10
```
```
[23:51:20:428] 9 matching inis found
```

Both *Stewards of Skyrim - New Clothing for Stewards* and *Stewards of Skyrim Enderal Integration
SPID* ship a file called `kco_stw_DISTR.ini`. Only one is deployed. That is arguably intentional
here — the Enderal integration is meant to replace the Skyrim one — but the mechanism is invisible
and it is exactly how a config disappears by accident.

**Rule for anything this repo ships: prefix the filename so it cannot collide** — `Zenderal - <Name>_DISTR.ini`.

### SPID rewrites your ini file

`Distribution::INI::GetConfigs` sanitises every value before parsing, and if any entry changed it
writes the file back with `ini.SaveFile(path)`. **[verified]** The transformations
(`INI::detail::sanitize`):

| Input | Becomes | Note |
|---|---|---|
| `0x12345 - MyMod.esp` | `0x12345~MyMod.esp` | only when the value has no `~` already |
| `Form = X  \|  A , B` | `Form = X\|A,B` | spaces stripped around `\|` and `,` |
| `00012345` | `0x12345` | bare 8-digit form |
| `0x0012345` | `0x12345` | leading zeros |

Consequences worth knowing: your committed file and the deployed file can diverge after one launch;
under MO2 the write lands **inside the winning mod's folder**, not in the game's real Data; and if
the file is read-only or the folder is not writable the save silently fails (SPID casts the result
to `void`). Write configs in the already-sanitised form and the rewrite never fires.

---

## Entry grammar

Every line is `Key = Value`. There are **four** key shapes, tried in this order
(`LookupConfigs.cpp`, `GetConfigs`): `ExclusiveGroups::INI::TryParse` →
`LinkedDistribution::INI::TryParse` → `DeathDistribution::INI::TryParse` →
`Distribution::INI::TryParse`.

| Shape | Key | Value fields |
|---|---|---|
| **Regular** | `[Final]<Type>` | `Form\|Strings\|Forms\|Levels\|Traits\|CountOrIndex\|Chance` |
| **On death** | `[Final]Death<Type>` | same seven |
| **Linked** | `[Global]Linked[Final][Death]<Type>` | `Form\|ParentForms\|CountOrIndex\|Chance` — **four** |
| **Exclusive group** | `ExclusiveGroup` | `Name\|Forms…` |

Optional fields may be left empty or written `NONE` (`clib_util::distribution::is_valid_entry`
treats an empty string and a case-insensitive `NONE` identically).

### Form types

`RECORD::detail::names` in `SPID/src/LookupConfigs.h` — the complete list: **[verified]**

```
Form   Spell   Perk   Item   Shout   LevSpell   Package   Outfit   Keyword   Faction   SleepOutfit   Skin
```

*The article's table omits `LevSpell`.* It is a real key and it takes an `LVSP` record.

| Type | Record signatures | Notes |
|---|---|---|
| `Spell` | `SPEL`, `LVSP` | a `Spell =` entry holding an `LVSP` is auto-routed to the LevSpell list at lookup (`LookupForms.cpp`) |
| `LevSpell` | `LVSP` | the explicit key |
| `Perk` | `PERK` | added at rank 1 |
| `Item` | `ALCH AMMO ARMO BOOK INGR KEYM LVLI MISC SCRL SLGM WEAP` | anything deriving from `TESBoundObject` |
| `Shout` | `SHOU` | |
| `Package` | `PACK`, `FLST` | a `FLST` must contain **only** packages or the game will likely crash |
| `Keyword` | `KYWD` | **SPID creates the keyword if it does not exist** (`LookupOptions::kCreateIfMissing`) |
| `Faction` | `FACT` | added at rank 1 |
| `Outfit` | `OTFT` | goes through the Outfit Manager, see below |
| `SleepOutfit` | `OTFT` | written straight to `npc->sleepOutfit` |
| `Skin` | `ARMO` | written straight to `npc->skin` |
| `Form` | any of the above | type is inferred — see next |

**Type inference (`Form =`)** resolves in this fixed order (`LookupForms.cpp`,
`LookupDistributables`): Keyword → Spell → LevSpell → Perk → Shout → Item → Outfit → Faction →
Package/FormList. **`SleepOutfit` and `Skin` can never be inferred**, because `Outfit` and `Item`
match those records first. Use the explicit keys for those two.

### The `Final` modifier

`Final` may be prefixed to any key, but it is **only legal on `Outfit`**. On anything else the
parser strips it and logs:

```
Final modifier can only be applied to Outfits.
```

A `FinalOutfit` cannot be replaced by any later outfit distribution. Real example already in the
list — *Stewards of Skyrim*'s `kco_stw_DISTR.ini`:

```ini
FinalOutfit = 0xDC6~kco_stw.esp|Jorleif|NONE|NONE|NONE|NONE|NONE
```

### Linked distribution

`Linked<Type>` distributes a form **to NPCs that already received some other form during this same
distribution pass**. Its value has a different shape from a regular entry
(`LinkedDistribution.cpp`, `INI::TryParse`): **[verified]**

```
Linked<Type> = Form|ParentForms|CountOrIndex|Chance
```

- Four fields, not seven. There are **no string, level or trait filters** — the parent form *is* the
  filter.
- The `ParentForms` section is **required** (`FormFiltersComponentParser<kRequired>`); an entry
  without one is skipped with
  `SKIPPED: Linked Form must have a form and at least one Parent Form`.
- Only the plain `MATCH` bucket is honoured there. `+` and `-` are parsed and then **ignored**
  (`RawLinkedForm`: *"Raw filters in RawLinkedForm only use MATCH"*).
- **Linking is one level deep.** A form handed out by a linked entry never triggers further linked
  entries (`Distribute.cpp`: *"This only does one-level linking"*).

Key prefixes combine, and the parser expects them in this order (`LinkedKeyComponentParser`):

```
[Global] Linked [Final] [Death] <Type>
        e.g.  LinkedFinalOutfit        GlobalLinkedFinalDeathOutfit
```

- **no prefix (local scope)** — only triggers off distributions made by entries in **the same
  `.ini` file**.
- **`Global`** — triggers off any distribution from any config file.

### Death distribution

`Death<Type>` uses the full seven-field regular grammar but only runs when the NPC dies
(`DeathDistribution.cpp`). Death outfits outrank everything, including `FinalOutfit`.

Note the separate, simpler tool for the same job on the *living*: the `D` trait filter. A regular
entry with `|D` targets NPCs that are already dead or flagged `StartsDead`; a `Death…` entry fires
at the moment of death.

### Exclusive groups

```ini
ExclusiveGroup = <name>|<form>,<form>,…,-<form>
```

Declares a set of forms that are mutually exclusive: once an NPC has one member, no other member can
be distributed to it (`ExclusiveGroups.cpp`, `MutuallyExclusiveFormsForForm`). Both the name and at
least one form are required. `-` removes a form from the group, which is how a patch narrows someone
else's group. Groups with the same name from different files merge.

Object Categorization Framework uses this heavily and its groups show up in the Zenderal log —
`OCF_ExclusiveGroup_Race0` … `Race4`, `OCF_ExclusiveGroup_Heat1`.

---

## Identifying a form

`clib_util::distribution::get_record_type` decides what a string means, in this order:
**[verified]**

| Test | Type | Example |
|---|---|---|
| contains `~` | FormID + plugin | `0x12345~MyMod.esp` |
| contains `.es` | plugin name only | `MyMod.esp` (form filters only) |
| `is_only_hex` — starts `0x`/`0X`, rest hex digits | bare FormID | `0x12345` |
| otherwise | EditorID | `IronSword` |

Notes that matter in practice:

- **`0x…~Plugin.esp` is the only form of FormID reference that survives a load-order change.** A
  bare `0x…` is a full runtime FormID including the load-order byte, so it moves the moment anything
  above it is enabled or disabled. Never ship one.
- The hex test **requires the `0x` prefix**, so an EditorID like `Face` or `ABBA` is not
  misinterpreted. An EditorID may not begin `0x`, obviously.
- **EditorID is the more stable identifier** — it survives merging, ESL-flagging and compaction. It
  is also the identifier that needs po3_Tweaks for most record types; see below.
- The plugin-name test is `contains(".es")`, so it matches `.esp`, `.esm` and `.esl` — and would
  also match a mod whose name happens to contain `.es`.

### EditorIDs need po3_Tweaks

`clib_util::editorID::get_editorID` (CLIBUtil `include/CLIBUtil/editorID.hpp`) returns the engine's
own stored EditorID only for these form types: **[verified]**

> Keyword, LocationRefType, Action, MenuIcon, Global, HeadPart, **Race**, Sound, Script, Navigation,
> Cell, WorldSpace, Land, NavMesh, Dialogue, Quest, Idle, AnimatedObject, ImageAdapter, **VoiceType**,
> Ragdoll, DefaultObject, MusicType, and the three StoryManager node types.

For **everything else** — `NPC_`, `FACT`, `CLAS`, `CSTY`, `OTFT`, `SPEL`, `PERK`, `ARMO`, `LCTN`,
`WEAP`, `ARMO`… — it calls `po3_Tweaks.dll!GetFormEditorID` and **returns an empty string if that
DLL is not loaded**. SSE simply does not keep those EditorIDs in memory.

So without powerofthree's Tweaks:

- filtering by **race keyword or race EditorID** still works;
- filtering by **NPC EditorID, faction, class, combat style, location or outfit EditorID** matches
  nothing, silently;
- referencing a **distributable** by EditorID fails the same way, logged as
  `SKIP - editorID doesn't exist`.

SPID reports what it found at the top of its log:

```
### DEPENDENCIES #################################
powerofthree's Tweaks (po3_tweaks) detected : true
```

Zenderal ships it and the log confirms it. **[verified]** Treat it as load-bearing.

---

## Filters

Five filter sections, all optional: strings, forms, levels, traits, and (separately) chance.
Different sections are combined with **AND**. Within a section the rule is more subtle than the
article suggests.

### The four-bucket rule — a correction

`StringFiltersComponentParser` sorts each comma-separated term into one of four buckets by its
modifier, and `Filter::Data::passed_string_filters` then tests **all four buckets and fails on any
one of them**: **[verified]** (`LookupConfigs.h`, `LookupFilters.cpp`)

| Modifier | Bucket | Within the bucket |
|---|---|---|
| *(none)* | `MATCH` — exact | **OR** (`any_of`) |
| `*term` | `ANY` — substring | **OR** (`any_of`) |
| `a+b+c` | `ALL` | **AND** (`all_of`) |
| `-term` | `NOT` | **AND** — must fail every one |

```cpp
if (!strings.ALL.empty()   && !HasStringFilter(strings.ALL, true)) return kFail;
if (!strings.NOT.empty()   &&  HasStringFilter(strings.NOT))       return kFail;
if (!strings.MATCH.empty() && !HasStringFilter(strings.MATCH))     return kFail;
if (!strings.ANY.empty()   && !ContainsStringFilter(strings.ANY))  return kFail;
```

> *The article says* "expressions within the same section are additive (combined using logical OR)".
> That is true **only inside one bucket**. Mixed modifiers are AND-ed across buckets:
>
> | Written | Actually means |
> |---|---|
> | `A,B` | `A` OR `B` |
> | `*A,*B` | contains `A` OR contains `B` |
> | `A,*B` | **exactly `A`** AND **contains `B`** |
> | `A,B,-X` | (`A` OR `B`) AND NOT `X` |
> | `A+B,C` | (`A` AND `B`) AND (`C`) |
>
> The `A,*B` row is the one that surprises people. Form filters behave identically
> (`passed_form_filters`), except that form filters have no partial-match bucket.

Only one modifier per term (`-*Guard` is not valid). Traits are the exception — they mix freely.

### String filters

What a string is compared against (`LookupNPC.cpp`, `NPC::Data`): **[verified]**

- the actor's **display Name** (`actor->GetName()`);
- the **EditorID** of the NPC base **and of every reachable template** in its chain;
- the **keyword EditorIDs of the NPC**, including keywords SPID itself distributed earlier in the
  pass;
- the **keyword EditorIDs of the NPC's Race**.

Matching is case-insensitive throughout (`string::iequals` / `string::icontains`).

The template chain SPID can reach is limited. For a non-leveled NPC it is the final NPC and its
immediate base template. For a leveled one it is the original NPC, the closest leveled NPC, and the
picked base template — the dynamic `FF……` actor and any deeper nesting are unreachable. The article's
diagrams of this are correct; keep them.

### Form filters

Accepted record types and what each tests (`NPC::Data::has_form`): **[verified]**

| Signature | Tested against |
|---|---|
| `CSTY` | `npc->GetCombatStyle()` |
| `CLAS` | `npc->npcClass` |
| `FACT` | `npc->IsInFaction()` |
| `RACE` | the actor's race |
| `OTFT` | the NPC's **initial** default outfit (`Outfits::Manager::HasDefaultOutfit`) — not an outfit SPID gave it |
| `NPC_` | the NPC itself or any reachable template |
| `ACHR` | the specific placed actor reference |
| `VTYP` | `npc->voiceType` |
| `SPEL` | the NPC's **base spell list** — spells on the record, not runtime-added ones |
| `ARMO` | `npc->skin` |
| `LCTN` | `actor->GetEditorLocation()` — where the NPC was **placed in the editor**, not where it is now |
| `PERK` | `actor->HasPerk()` |
| `FLST` | recursive: any form in the list, including nested lists |
| *plugin name* | the NPC (or a template) is defined in that plugin |

### Level filters

```
Form = X|||<levelExpr>,<skillExpr>,<skillExpr>…
```

- **Actor level** — `min/max`, or a bare `min` for min-to-infinity, or `n/n` for exact.
- **Skill level** — `<index>(min/max)`.
- **Skill weight** — the same prefixed with `w`, e.g. `w1(2/3)`. This reads the weight off the NPC's
  **Class** record (`npcClass->data.skillWeights`), not the NPC — it describes what the class levels
  up, not what it currently has.

Skill indices are **0–17** (`LookupConfigs.h` guards with `type < 18`, `LookupFilters.cpp` maps them
onto `RE::TESNPC::Skills`):

```
 0 One-Handed    3 Block        6 Light Armor   9 Sneak      12 Alteration   15 Illusion
 1 Two-Handed    4 Smithing     7 Pickpocket   10 Alchemy    13 Conjuration  16 Restoration
 2 Archery       5 Heavy Armor  8 Lockpicking  11 Speech     14 Destruction  17 Enchanting
```

> *The article says "one of the 17 skills" and then lists 18 (0–17).* The list is right; the count
> is a typo. Enchanting is index **17** and it works.

**Only one actor-level expression survives.** `5/10,7/12` keeps `7/12` and discards `5/10` — the
parser overwrites `actorLevel` each time it sees a non-skill term. Skill expressions accumulate
normally.

Any entry carrying a level filter joins **leveled distribution**, which re-evaluates PC-level-mult
NPCs as they level (`DistributePCLevelMult.cpp`).

### Trait filters

A single `/`-separated expression. `-` inverts; unlike the other sections, modifiers mix freely.

| Trait | Means (`LookupConfigs.h`, `LookupNPC.cpp`) |
|---|---|
| `M` / `F` | sex. **`-F` is identical to `M`** and `-M` to `F` — the same switch case |
| `U` | `npc->IsUnique()` |
| `S` | `npc->IsSummonable()` |
| `C` | `actor->IsChild()` **or** the race's EditorID contains `RaceChild` |
| `L` | `actor->IsLeveled()` — PC level mult |
| `T` | `actor->IsPlayerTeammate()` **or** membership of faction `0005C84D` (PotentialFollowerFaction). That FormID is hardcoded, and in Enderal it is not a faction — see [`spid-in-enderal.md`](spid-in-enderal.md#t-teammate-is-half-dead-in-enderal) |
| `D` | currently dead **or** the record's `StartsDead` flag |

`F/-U/L/-S` is a valid expression: female, not unique, leveled, not summonable.

### Chance

A decimal percentage, default 100. Appending `!` makes the roll **deterministic**.

Two facts the article does not state: **[verified]** (`Filter::Data::PassedFilters`)

1. **The chance is rolled before any filter runs**, as an early-out.
2. The deterministic seed is `std::hash(<the entire value string of the line>)` combined with the
   current player ID and the actor's FormID. So **any edit to the right-hand side of the `=`** —
   adding a `NONE`, changing a filter, changing whitespace SPID then sanitises — reshuffles every
   roll for every NPC. The article says this; the mechanism is why.

With `LogLevel = debug` the rolls are printed:

```
Seed for Actor 00044FF5, Player 922463733, base 10841186582105476777 = 6969106352358470666. Chance: 0.645
```

---

## Count, index and package-list type

The sixth field is read against the entry's type (`IndexOrCountComponentParser`):

| Type | Field means | Default |
|---|---|---|
| `Item` | how many to add. `10-20` is a **random count** in that range | 1 |
| `Package` (a `PACK`) | the **index** to insert the package at, zero-based | 0 |
| `Package` (a `FLST`) | which package list to overwrite | 0 |
| everything else | ignored | |

Package-list slots:

| # | Slot | NPC record field |
|---|---|---|
| 0 | Default Package List | `DPLT` |
| 1 | Spectator Override | `SPOR` |
| 2 | Observe Corpse Override | `OCOR` |
| 3 | Guard Warn Override | `GWOR` |
| 4 | Enter Combat Override | `ECOR` |

One inference wrinkle: a `Form =` entry that turns out to be a package defaults to a *count*, not an
index, so a range like `2-5` is meaningless there. SPID uses the range's minimum and warns
(`LookupForms.cpp`). Use the explicit `Package =` key.

---

## When distribution happens, and in what order

### Timing

SPID hooks `RE::Character::ShouldBackgroundClone` and `InitLoadGame`
(`DistributeManager.cpp`) — distribution runs **as an actor's 3D loads**, typically on cell load.
There is no startup pass over every NPC in the game.

**Each base NPC is processed once per session.** SPID creates a runtime keyword `SPID_Processed` at
startup and stamps it on the `TESNPC` **base** after distributing:

```cpp
if (!npc->HasKeyword(processed)) {
    Distribute(npcData, false);
    npc->AddKeyword(processed);
}
```

Two consequences:

- **Everything is distributed to the base, so every actor sharing that base shares the result.**
  Distribute a ghost ability to one bandit and every actor of that bandit base is a ghost. The
  source acknowledges this as a known limitation.
- Re-rolling a chance requires restarting the game, not reloading a save.

The **player is never targeted** (`should_process_NPC`), nor are deleted NPCs.

### Order

Type order is fixed (`Distribute::Distribute`): **[verified]**

```
Keywords → Factions → Perks → Spells → LevSpells → Shouts → Packages → Items → Skins → SleepOutfits → Outfits
```

> *The article's list omits `LevSpell` and `SleepOutfit`* and places Skins before Outfits without
> mentioning SleepOutfits between them. The sequence above is the code.

Within a type, entries run in load order: config file order (§ *How configs are found*), then line
order within each file. **Keywords are the exception** — they are topologically sorted first
(`KeywordDependencies.cpp`) so a keyword may be used as a filter for another keyword without you
having to order them by hand.

### How each type is applied

| Type | Applied as |
|---|---|
| Keyword | `npc->AddKeywords()` |
| Faction | appended at **rank 1** |
| Perk | `npc->AddPerks(…, 1)` |
| Spell | added to the base spell list, then `actor->CastPermanentMagic()` so abilities take effect — including on dead actors |
| Package | inserted into `npc->aiPackages` at the given index, skipped if already present |
| Item | **`npc->AddObjectsToContainer(…, npc)`** — added to the **base NPC's container** |
| Skin / SleepOutfit | assigned directly to `npc->skin` / `npc->sleepOutfit` |
| Outfit | handed to the Outfit Manager, resolved and equipped when the actor loads |

**Items go to the base, not the actor.** The source comments on this explicitly: per-actor item
distribution is not implemented because adding to an actor writes into inventory changes, which bake
into the save. So an `Item =` entry gives the item to every instance of that base NPC, and instances
spawned later carry it too.

### Outfits are the exception to "leaves no trace"

The Outfit Manager (`SPID/src/Outfits/`) tracks a per-actor `OutfitReplacement` and **serialises it
into SPID's SKSE co-save** (`OutfitsManager+SaveLoad.cpp`). It needs to: it has to know the original
outfit to revert to, and it has to survive a `ResetInventory`. It installs eleven hooks for this,
all listed at the top of the log.

Practical effect: removing a SPID outfit config is not a no-op. SPID detects a replacement whose
distributed outfit no longer exists (`IsCorrupted()`) and reverts the actor to its original outfit,
but that reversion happens in-game, on load, not by simply deleting the file.

---

## Reading the log

`Documents\My Games\Skyrim Special Edition\SKSE\po3_SpellPerkItemDistributor.log` — the **Skyrim
SE** folder, even for Enderal, the same as every other SKSE log (CLAUDE.md, "Crash logs are written
to the SKYRIM SE folder").

Sections, in order:

| Header | Contains |
|---|---|
| *(preamble)* | version, log level, `Game version`, the Outfit Manager's hooks |
| `DEPENDENCIES` | whether po3_Tweaks was found |
| `INI` | how many configs matched and their paths — **check the count against what's on disk** |
| `HOOKS` | the actor hooks |
| `MERGES` | MergeMapper, only relevant to zmerge users |
| `LOOKUP` | **per-entry resolution failures**, grouped by type |
| `PROCESSING` | the `Registered X/Y` summary |
| `EXCLUSIVE GROUPS` | resolved groups and their members |
| `HOOKS` / `EVENTS` | leveled-distribution hooks and event sinks |
| *(runtime)* | `[📦] Distribution for [ACHR:…]` per actor, `[🧥]` outfit chatter |

### The line that matters

```
Registered 198/318 Keywords
Registered 11/14 Perks
```

`X` valid entries out of `Y` total entries of that type across all configs
(`LookupForms.cpp`, `LogDistributablesLookup`). **`X < Y` means lines were dropped and the mod is
partly not working.** This is the single cheapest check that a config is doing what it claims.

Only types actually present in some config are listed, so a missing row means "no entries of that
type", not "zero registered".

### Per-entry failure messages

Each appears once per unresolvable form or filter, prefixed with the config it came from:

| Message | Cause |
|---|---|
| `SKIP - editorID doesn't exist` | no record with that EditorID — or po3_Tweaks is missing for that record type |
| `SKIP - formID doesn't exist` | the plugin loaded but has no record at that FormID |
| `SKIP - mod cannot be found` | the named plugin is not in the load order |
| `SKIP - mismatching form type (expected: …, actual: …)` | right record, wrong type for that key |
| `SKIP - unsupported form type` | the record type cannot be distributed |
| `FAIL - couldn't create keyword` | keyword creation failed — near-fatal, not a config error |

A failed entry is skipped; the rest of the file still loads. That is why a broken config produces a
working game and no visible symptom.

### Per-actor distribution

At `info` level and above SPID prints what each actor actually received:

```
[📦] Distribution for [ACHR:00044FF5] (Base: _00E_SkelettDeadNoEquip "Skeleton" [NPC_:0002A1F1])
[📦] 	PERK
[📦] 		_SD_SDPerk "Directional Stagger Perk" [PERK:FE04F810] @ DynamicBlockHit_DISTR.ini
[📦] 	SPEL
[📦] 		summonTeammateSpell "summonTeammateSpell" [SPEL:FE0A5805] @ talkToSummons_DISTR.ini
```

The `@ <file>` suffix names the config responsible — this is the fastest way to attribute an
unexpected effect to a mod.

---

## Common mistakes, ranked by how often they bite

1. **The ini is not directly in `Data\`.** Non-recursive scan; nothing is logged. Check the `INI`
   section lists your file.
2. **Filters reference records the game does not have.** Silent, per-entry. Check `Registered X/Y`.
3. **No filters at all.** A bare `Spell = 0x…~Mod.esp` hits **every NPC in the game**, including
   critters and corpses. Two configs in this list do exactly that, and the log shows the result:
   `_SD_SDPerk` and four spells handed to a River Crab and a Pidgeon. **[verified]** Sometimes that
   is the intent; make sure it is.
4. **Mixed string modifiers read as AND.** `A,*B` is not `A OR *B`. See the four-bucket rule.
5. **Filename collision with another mod.** Only one deploys; nothing warns.
6. **Bare `0x…` FormIDs without `~Plugin.esp`.** They encode load order and break on any change.
7. **Expecting a new roll on save reload.** Distribution is per-session and stamped on the base
   with `SPID_Processed`.
8. **Expecting an `Item =` entry to give one actor a unique item.** It goes to the base; every
   instance gets it.
9. **`Final` on a non-Outfit key.** Stripped with a warning.
10. **Editing a deterministic-chance line "harmlessly".** Any change to the value reshuffles every
    roll.

## Source map

For anything not covered here, these are the files to read
(`github.com/powerof3/Spell-Perk-Item-Distributor`, `SPID/src/`):

| File | Answers |
|---|---|
| `LookupConfigs.h` / `.cpp` | the grammar — every parser, every modifier, the sanitiser, the form-type list |
| `LinkedDistribution.cpp` | linked-entry grammar, scope, one-level rule |
| `DeathDistribution.cpp` | `Death…` keys |
| `ExclusiveGroups.cpp` | `ExclusiveGroup` |
| `LookupFilters.cpp` | how filters combine, chance ordering |
| `LookupNPC.cpp` | what strings and forms are actually compared against |
| `LookupForms.cpp` | type inference order, `Registered X/Y` |
| `Distribute.cpp` / `DistributeManager.cpp` | timing, hooks, application order, `SPID_Processed` |
| `Outfits/` | outfit resolution, hooks, co-save persistence |
| `main.cpp` | runtime requirements, the settings ini |

CLIBUtil (`github.com/powerof3/CLIBUtil`, `include/CLIBUtil/`): `distribution.hpp` for config
discovery and record parsing, `editorID.hpp` for the po3_Tweaks dependency.
