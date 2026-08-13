# SPID in Enderal

> **Read [`spid.md`](spid.md) first** for the syntax and behaviour. This file covers only what
> changes when SPID runs on **Enderal: Forgotten Stories SE**, and what that means for the Zenderal
> list.
>
> Facts marked **[verified]** were read on 2026-08-13 off the installed modlist, the serialized
> masters in `reference/base/`, or the SPID log from a live Enderal run on 2026-08-09.

## The short version

SPID works in Enderal — the DLL loads, the hooks install, distribution runs. What does **not**
work is a `_DISTR.ini` written for Skyrim, because **Enderal's `Skyrim.esm` is Enderal** (CLAUDE.md,
"Masters"). Every EditorID and FormID in a Skyrim config resolves against a game whose content is
almost entirely different, and SPID handles that by **skipping the entry and continuing**.

Here is the current state of this list, straight out of the log: **[verified]**

```
[23:51:19:895] po3_SpellPerkItemDistributor v7.3.2.1597
[23:51:19:895] Game version : 1-5-97-0
[23:51:20:408] powerofthree's Tweaks (po3_tweaks) detected : true
[23:51:20:428] 9 matching inis found
...
[23:51:43:636] Registered 198/318 Keywords
[23:51:43:636] Registered  17/17  Spells
[23:51:43:636] Registered  11/14  Perks
[23:51:43:636] Registered   7/7   Outfits
[23:51:43:636] Registered   1/1   Items
```

**120 keyword entries and 3 perk entries never loaded**, and ten `_DISTR.ini` on disk became nine.
Nothing in the game says so. The traced causes:

| Loss | Cause |
|---|---|
| the bulk of the 120 keyword lines | OCF's Creation Club / DLC race EditorIDs (`ccBGSSSE036_BoneWolfCompanionRace`, `ccVSVSSE003_LichRace`, …) that Enderal has never had |
| 1 more keyword line | `Deflection_DISTR.ini` filters on `ccbgssse003-zombies.esl` → `SKIP - mod cannot be found` |
| 2 of the 3 perk lines | `ForHonorBFCO_DISTR.ini` filters on `BladesFaction` and `ThalmorFaction` — **neither exists in Enderal** |
| the 3rd perk line | `ForHonorBFCO_DISTR.ini` references `DWKaPoTunRace.esp` — an optional plugin the list does not install |
| 1 whole config file | `kco_stw_DISTR.ini` is shipped by two mods; MO2 deploys one |

None of those is a defect in SPID. They are the normal outcome of pointing Skyrim configs at Enderal.

---

## Does SPID run here at all — yes

| Check | Result |
|---|---|
| Enderal runtime | 1.5.97; SPID's SE build requires `>= 1.5.39` **[verified]** |
| Installed build | `po3_SpellPerkItemDistributor.dll` FileVersion `7.3.2.1597.0` — the `1597` marks the **SE (1.5.97)** build, the correct one **[verified]** |
| Address Library | in the list (`mods/Address Library for SKSE Plugins`) |
| powerofthree's Tweaks | in the list, and SPID reports `detected : true` **[verified]** |
| Config location | `Data\` = the MO2 virtual Data, i.e. the **root of a mod folder** |
| Form-version ceiling | **irrelevant to SPID** — SPID is an SKSE DLL, not a plugin. The HEDR 1.71 ceiling and BEES apply to the `.esp` a config *references*, not to the config |

There is nothing Enderal-specific to configure. Drop a correct `_DISTR.ini` into a mod folder's root
and it loads.

---

## What ports from Skyrim and what does not

This is the whole problem, so be precise about it. Checked against `reference/base/Skyrim/` —
regenerate that tree with the `spriggit-decompile-reference` skill if it is missing. **[verified]**

| Filter target | Ports? | Detail |
|---|---|---|
| `ActorType*` **keywords** | **Yes** | All 16 present: `ActorTypeNPC 013794`, `ActorTypeUndead`, `ActorTypeCreature`, `ActorTypeAnimal`, `ActorTypeDaedra`, `ActorTypeDragon`, `ActorTypeGhost`, `ActorTypeGiant`, `ActorTypeTroll`, `ActorTypeDwarven`, `ActorTypeHorse`, `ActorTypeCow`, `ActorTypeBoss`, `ActorTypeFamiliar`, `ActorTypePrisoner`, `ActorTypeUndeadHumanoid` |
| **Race** EditorIDs | **Yes — but see the trap below** | 117 races, vanilla names largely intact: `BretonRace`, `DarkElfRace`, `WolfRace`, `BearBlackRace`, `DraugrRace`, `SkeeverRace`, `NordRaceChild`, … |
| **Class** EditorIDs | **Mostly** | only 3 of Enderal's 141 classes are `_00E_`-prefixed; the familiar ones are there — `Bard`, `Beggar`, `Citizen`, `Child`, `CombatAssassin`, `CombatMageDestruction`, `CombatBarbarian` |
| **Combat style** EditorIDs | **Mostly** | 121 styles, largely `cs*`-named as in Skyrim |
| **Faction** EditorIDs | **Some** | `BanditFaction 014C6F`, `PlayerFaction`, `PlayerEnemyFaction`, `AnimalFaction`, `CreatureFaction 000013`, `GuardDialogueFaction` survive. **Skyrim-specific ones do not**: no `BladesFaction`, `ThalmorFaction`, `CrimeFaction*`, no Hold factions. Enderal's own 335 are its own — `ArkGuardFaction`, `ArkMerchantMilbert`, `SuntempleGuardFaction`, `IsGuardFaction`, the `Creature_*Faction` set |
| **Location** EditorIDs | **No** | 90 locations, all Enderal's — `CapitalCityBibliothekLocation`, `_00E_SuncoastLocation`, `_00E_FlusshaimTaverneLocation` |
| **NPC** EditorIDs / names | **No** | Enderal's cast. And note EditorIDs are German — see below |
| **Outfit / spell / perk** EditorIDs | **No** | Enderal's own |
| **Creation Club / DLC** anything | **No** | the DLC ESMs in Enderal are empty stubs (CLAUDE.md, "Masters"); `cc*` plugins are absent entirely |

**The working rule:** keyword and race filters usually port. Everything else must be checked
individually, and Skyrim-flavoured names (Hold, faction, city, questline) almost never survive.

### The trap: a vanilla EditorID may name a completely different people

Enderal keeps the *names* of the playable races and reuses them for its own. **[verified]** —
`reference/base/Skyrim/Races/`:

| EditorID | FormID | What it actually is in Enderal |
|---|---|---|
| `NordRace` | **`033899`** | **Half Arazealean** |
| `NordRaceSkyrim` | `013746` | Arazealean — *this* is the vanilla `NordRace` FormID |
| `RedguardRace` | **`033898`** | Half Qyranian |
| `RedguardRaceSkyrim` | `013748` | Qyranian |
| `BretonRace` | `013741` | Half Kiléan |
| `ImperialRace` | `013744` | Endralean |
| `DarkElfRace` | `013742` | Aeterna |
| `HighElfRace` | `013743` | Half Aeterna |
| `WoodElfRace` | `013749` | Starling |
| `OrcRace` | `013747` | Orc |
| `ArgonianRace` / `KhajiitRace` | `013740` / `013745` | kept under their vanilla names |

So a ported line reading `Form = 0x12345||NordRace` **resolves cleanly and targets the wrong
population**, with no log entry. And `0x13746~Skyrim.esm`, the vanilla `NordRace` FormID, resolves
to `NordRaceSkyrim` — a different record from the one the same config's EditorID would find.

This is the SPID instance of the CLAUDE.md rule that *"a vanilla FormID that survived may be a
completely different record"*. It is worse for SPID than for a plugin patch, because there is no
xEdit conflict view to show you.

### FormIDs are worse than EditorIDs here

`0x…~Skyrim.esm` in an Enderal config means "whatever Enderal put at that ID", which is usually
Enderal content, occasionally an unrelated record, and only rarely the vanilla one. Prefer
EditorIDs, and resolve them against `reference/base/` before shipping.

The engine-hardcoded IDs are still safe (CLAUDE.md, "Useful FormKey constants") — but SPID's only
use for one is the internal `0005C84D`, and that one is broken:

### `T` (teammate) is half-dead in Enderal

`NPC::Data` computes the teammate trait as
`actor->IsPlayerTeammate() || npc->IsInFaction(0x0005C84D)` — `PotentialFollowerFaction` in Skyrim.
**In Enderal `0005C84D` is not a faction at all.** There is no faction record at that ID in
`Skyrim.esm`, `Update.esm` or `Enderal - Forgotten Stories.esm`; the ID is occupied by an unrelated
**PlacedObject** — a scaled static in the Vyn worldspace, cell `001EF9`, base `0377D8`.
**[verified]**

`LookupByID<RE::TESFaction>` therefore returns null, and the second half of the test is permanently
false. In Enderal the `T` trait reduces to plain `IsPlayerTeammate()` — actual current followers
only, never "could be a follower" — and `-T` is correspondingly broader than it is in Skyrim.
Nothing errors and nothing is logged.

This is a textbook instance of the CLAUDE.md rule about vanilla FormIDs: the ID survived, the record
behind it is something else entirely.

### po3_Tweaks is load-bearing

Covered in [`spid.md`](spid.md#editorids-need-po3_tweaks): on SSE the engine only keeps EditorIDs in
memory for a fixed set of record types, and **`NPC_`, `FACT`, `CLAS`, `CSTY`, `OTFT`, `SPEL`,
`PERK`, `ARMO` and `LCTN` are not among them** — those go through `po3_Tweaks.dll!GetFormEditorID`
and return empty if it is absent.

Zenderal ships *powerofthree's Tweaks* and the log confirms SPID sees it. But the two Enderal
integration configs in this list are built entirely on NPC EditorIDs:

```ini
Outfit = 0xDC4~kco_stw.esp|_00E_CapitalCityBibliothekarMarius|NONE|NONE|NONE|NONE|100
Item   = 0x811~Grievous Rose Multicolor.esp|_00E_MC_Adila|NONE|NONE|NONE|1|100
```

Remove po3_Tweaks and every one of those lines matches nothing, with no error anywhere. Race and
keyword filters would keep working, which makes the failure look selective rather than
environmental.

### Enderal EditorIDs are German

The same trap CLAUDE.md documents for cells applies to every string filter. Ark is
`_00E_CapitalCity*` / `CapitalCity*`, Riverville is `Flusshaim*`, the Sun Temple is `Suntemple*`.
Searching for an English town or NPC name in `reference/base/` returns nothing.

Worked examples already deployed in this list:

| Config line targets | Displayed in game as |
|---|---|
| `_00E_CapitalCityBibliothekarMarius` | Librarian Marius, Ark library |
| `_00E_CapitalCity_MerrolBuchfiltzer` | Merrol Booksnooper, Ark museum |
| `_00E_CapitalCityBankierSamaelSilren` | Banker Samael Silren, Ark bank |
| `_00E_MQ07a_TheAgedMan` | the Aged Man's manor servant |
| `_00E_NQ17Rys` | Rys, Old Watermill, Dark Valley |

The recipe from CLAUDE.md holds: grep the localized `String:` values in `reference/base/*/…` for the
English name, then read the EditorID off the match.

---

## Anchors that do work

A starting set for authoring an Enderal config, all confirmed present in
`reference/base/Skyrim/`: **[verified]**

**Broad targeting**

| Filter | Hits |
|---|---|
| `ActorTypeNPC` | people |
| `ActorTypeCreature`, `ActorTypeAnimal` | wildlife |
| `ActorTypeUndead`, `ActorTypeUndeadHumanoid`, `ActorTypeGhost` | Enderal's Lost Ones and specters |
| `ActorTypeBoss` | bosses |
| `-C` (trait) | excludes children; also matches `*RaceChild` by EditorID |

**Factions worth knowing** — `IsGuardFaction 07286D`, `GuardDialogueFaction 07286E`,
`ArkGuardFaction 09B715`, `SuntempleGuardFaction 0F76C0`, `UCGuardFaction 137A16`,
`BanditFaction 014C6F`, `AnimalFaction 046E73`, `CreatureFaction 000013`, and the ~50-strong
`Creature_*Faction` set (`Creature_WolfFaction`, `Creature_BearFaction`, `Creature_MyradWildFaction`,
`Creature_DragonFaction`, …) which is the cleanest way to target one Enderal species.

**Races** — the vanilla creature names are intact and mean what they say:
`WolfRace`, `BearBlackRace` / `BearBrownRace` / `BearSnowRace`, `SabreCatRace`, `TrollRace`,
`DraugrRace` / `DraugrMagicRace`, `SkeletonRace`, `SkeeverRace`, `DeerRace` / `ElkRace`,
`GiantRace`, `FalmerRace`, `FrostbiteSpiderRace`, `AtronachFlameRace` / `Frost` / `Storm`.
Enderal's own additions are `_00E_*`-prefixed (`_00E_StoneGolemRace`, `_00E_SwampRace`,
`_00E_KristallwesenRace`, `_00E_OorbayaRace`) plus a handful of renamed variants
(`BearBrownRaceHoher`, `WolfHoheRace`, `SabreCatHoheRace`, `ChaurusRaceLarge`).

**Do not use the playable-race EditorIDs for flavour** without reading the trap above.

---

## Worked example: `ForHonorBFCO_DISTR.ini`

Already deployed in this list, and the best demonstration of the good and the bad. Its job is to
mark elite NPCs with a perk that OAR then reads to pick For Honor movesets. Excerpted — the file has
13 entries, and with `DynamicBlockHit_DISTR.ini`'s one they are the `14` in `Registered 11/14 Perks`:

```ini
; Bosses, captains, champions — title-bearing elites
Perk = 0xD7B~ForHonorBFCO.esp|*Boss,*Chief,*Champion,*Warlord,*Commander,*General,*Jarl,*Captain,*Master,*Veteran,*Thane,*Lord,*King,*Queen||15/255|-C/-D||80!

; Weapon masters — high combat skill (0 = One-Handed, 1 = Two-Handed, 3 = Block)
Perk = 0xD7B~ForHonorBFCO.esp|ActorTypeNPC||35/255,0(90/255)|-C/-D||10!

; Tiny elite factions
Perk = 0xD7B~ForHonorBFCO.esp|ActorTypeNPC|BladesFaction|25/255|-C/-D||55!
Perk = 0xD7B~ForHonorBFCO.esp|ActorTypeNPC|ThalmorFaction|45/255|-C/-D||12!
```

**What is right about it, and portable:**

- `ActorTypeNPC` is a keyword — it survives, and it correctly excludes wildlife.
- Level and skill ranges (`35/255`, `0(90/255)`) are engine-level data, so they work anywhere.
- `-C/-D` uses the trait combining modifier to exclude children and corpses.
- Deterministic chance `80!` keeps a given NPC's result stable across sessions for one save.
- Overlapping lines are deliberately treated as independent opportunities, not additive
  percentages — which is the correct reading of how SPID rolls each entry separately.

**What Enderal rejects, and why the file still "works":** its last three entries — the two faction
lines above and one gating on `DWKaPoTunRace.esp` — are dropped —

```
[ForHonorBFCO_DISTR.ini] Filter (BladesFaction) SKIP - editorID doesn't exist
[ForHonorBFCO_DISTR.ini] Filter (ThalmorFaction) SKIP - editorID doesn't exist
[ForHonorBFCO_DISTR.ini] Filter [0x801] (DWKaPoTunRace.esp) SKIP - formID doesn't exist
```

`Registered 11/14 Perks` — 14 perk entries in the list, 13 of them this file's, 3 rejected. The mod
appears to work, because the surviving ten lines still hand the perk to most elites, while a
designed-in behaviour (elite factions always getting it) is simply gone.

**The Enderal fix** would be to replace those with real factions:
`IsGuardFaction` for city guards, `SuntempleGuardFaction` for the Order's soldiers, or one of the
`_00E_*` faction records, chosen from `reference/base/Skyrim/Factions/`.

### The other trap this list demonstrates: no filter means everyone

```ini
Spell = 0x805~talkToSummons.esp
Spell = 0x901~DynamicBlockHit.esp
Perk  = 0x810~DynamicBlockHit.esp
```

Three of the nine configs in this list ship entries with **no filters at all**. The log shows the
result:

```
[📦] Distribution for [ACHR:00032199] (Base: _03E_Crab "River Crab" [NPC_:000164C4])
[📦] 	PERK
[📦] 		_SD_SDPerk "Directional Stagger Perk" [PERK:FE04F810] @ DynamicBlockHit_DISTR.ini
[📦] 	SPEL
[📦] 		summonTeammateSpell "summonTeammateSpell" [SPEL:FE0A5805] @ talkToSummons_DISTR.ini
```

River crabs, pigeons and corpses all receive them. **[verified]** For a stagger controller that is
probably intended; for anything with a cost it is not. Add at least `ActorTypeNPC` unless you
genuinely mean every actor in Vyn.

---

## Porting checklist

Cheapest checks first, in the spirit of the `skyrim-to-enderal-porter` subagent.

1. **Resolve every identifier before installing anything.** For each EditorID in the config, look for
   a matching file in `reference/base/Skyrim/<Group>/`; for each `0x…~Plugin.esp`, confirm the plugin
   is in the list. This is minutes of `ls | grep` and it decides whether the port is viable at all.
2. **Re-read the ones that resolve.** A hit is not a pass — `NordRace` resolves and means Half
   Arazealean. Open the record and check what it is.
3. **Rewrite or drop the Skyrim-specific filters.** Factions, locations, NPCs and quest content are
   the usual casualties. Dropping a line is a legitimate outcome; leaving a dead one is not, because
   it hides in the `Registered X/Y` count.
4. **Rename the file** so it cannot collide with another mod's: `Zenderal - <Name>_DISTR.ini`.
5. **Check the arithmetic on chance and overlap** the way `ForHonorBFCO_DISTR.ini`'s header comment
   does — separate entries are separate rolls, not additive percentages.
6. **Launch once and read the log.** `Registered X/Y` must be `X == Y`. Then grep the per-actor
   `[📦]` blocks for your config's filename to confirm it reached the NPCs you meant.

Per CLAUDE.md guardrail 8: a config that loads with `X == Y` is a **verified load**, not a verified
effect. Only seeing the behaviour in game proves the rest.

---

## Verifying a config against the reference trees

`reference/` is gitignored and rebuilt locally; use the `spriggit-decompile-reference` skill if it
is not there. Record folder names are `<EditorID> - <FormID>_<Master>.yaml`, so an EditorID check is
a filename check:

```bash
cd reference/base/Skyrim

ls Keywords  | grep -i "^ActorTypeNPC - "        # keyword exists?
ls Races     | grep -i "^NordRace - "            # ...and what FormID does Enderal give it?
ls Factions  | grep -iE "^(Blades|Thalmor)"      # empty = absent
ls Locations | grep -i "capitalcity"             # Enderal's own naming
```

To go the other way — English display name to EditorID — grep the localized strings, as CLAUDE.md
describes for cells:

```bash
grep -rl "String: Librarian Marius" reference/base/*/Npcs/
```

For anything a third-party plugin defines, serialize that plugin into `reference/mods/` first; SPID
resolving `0x…~SomeMod.esp` depends on the mod being installed, not on the reference tree, but the
reference tree is how you confirm the FormID is the record you think it is.

---

## Shipping a `_DISTR.ini` from this repo

A SPID config is a **fourth release shape** alongside the patch, replacement and script-only shapes
CLAUDE.md documents — a release with no plugin and no script, just one `.ini` at the archive root.

- Source lives at `src/<PatchName>/spid/Zenderal - <Name>_DISTR.ini`, committed. `.ini` is not
  gitignored.
- `build/manifest.json` carries it with a `files` block and `"plugins": []`, `"fomod": false`:

  ```json
  {
    "name": "Zenderal - <Name>",
    "archiveName": "Zenderal - <Name>",
    "fomod": false,
    "plugins": [],
    "files": [ { "from": "src/<PatchName>/spid/Zenderal - <Name>_DISTR.ini", "to": "" } ]
  }
  ```

  `"to": ""` means the archive root, which is where SPID's non-recursive `Data\` scan requires it.
- **Prefix the shipped filename `Zenderal - `.** Filename collisions are silent (this list already
  has one), and a Zenderal patch losing to a third-party mod's identically-named config would be
  invisible.

Because SPID edits configs in place when it sanitises them (see [`spid.md`](spid.md#spid-rewrites-your-ini-file)),
write the file already sanitised — `~` not ` - `, no spaces around `|` or `,`, `0x` FormIDs without
leading zeros — so the deployed copy never diverges from the committed one.
