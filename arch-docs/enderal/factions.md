# Factions

Reference for what Enderal's FACT records actually are — and, more importantly, what they are not.
The headline: **the factions the player knows from the story mostly do not exist as records.** A
patch (or SPID config) that goes looking for "the Rhalâta faction" or "the Holy Order faction" will
find nothing to hook. This document maps the lore onto the records that really carry it.

Counts taken **2026-08-13** against the serialized trees in `reference/base/` (Enderal SE 2.0.12.4).
Extraction resolved NPC template chains and read only `Language: English` strings — see
"Localization" below for why both matter.

## The record landscape

**335 factions in base Enderal, 96 in Forgotten Stories (82 new + 14 overrides).** **[verified]**

There are essentially **no vanilla Skyrim faction stubs**. Enderal reuses low vanilla FormIDs but
repurposes the records — `CreatureFaction 000013`, `PlayerFaction 000DB1`, `UndeadFaction 005104`,
`BanditFaction 014C6F`, `SpiderFaction 018724` are all Enderal's own content on Bethesda's IDs.
**[verified]** (This is the plugin-architecture rule again: `Skyrim.esm` *is* Enderal.)

What the 335 base records actually break down into **[verified]**:

| Category | Base count | What it is |
|---|---:|---|
| Dialogue routing (`IsVoiceActor*`) | 97 | Pure voice-type plumbing, all `HiddenFromPC`. FS adds another 60 — the single largest faction group in the game is not a faction at all |
| Uncategorized one-offs | 108 | Per-house ownership factions (`FL_AlfridHouseFA`), sandboxing permissions, AI switches (`WispBusyFaction`), engine internals |
| Vendor factions | 60 | One per merchant; 69 across both trees carry the `Vendor` flag. See below |
| Creature taxonomy (`Creature_*Faction`) | 47 | The enemy-family system — the most useful faction set in the game. Covered in [`bestiary.md`](bestiary.md) |
| Quest-scoped (`MQ*`, `NQ*`, `UC0–3_*`) | 20 | Temporary combat/ally groupings for one quest |
| Crime (`TrackCrime` flag) | 3 (+1 FS) | The real law system — see below |

Engine-internal factions worth knowing by name: `BossesFaction 03C755` (boss-music trigger set),
`EPFaction 039DCE` (XP system), `ImportantNPCs 03C6BF`, `PlayerAlliesFaction 039BD7`,
`IgnoreInCombatFaction`, `CanSayFaction`/`GreetingFaction` (dialogue gates). **[verified]**

## Lore factions vs record factions

This mapping is **editorial** — the right-hand column is verified, the left-hand pairing is
interpretation:

| Lore faction | What actually exists in the records |
|---|---|
| **Golden Sickle** (Ark's merchant guild) | `ArkHaendlergilde 0A8D25:Skyrim.esm` — display name "Golden Sickle", and the *only* lore faction with a real rank ladder: Aspirant (0) → Protector (1) → Guild Master (2) **[verified]** |
| **The Holy Order** | **No dedicated faction.** Order NPCs sit in `SuntempleFaction 0F76BD` and `SuntempleGuardFaction 0F76C0`; `OrdealFaction 039907` is a generic AI faction despite the name **[verified]** |
| **The Rhalâta** | **No faction record at all.** The whole Undercity runs on `UC_MasterFaction 103476` + `UCCrimeFaction 137A04`; the only records with "Rhalata" in the EditorID are 11 FS voice-routing factions and `FS_Merchant_Rhalata_SisterEnvy 01E894` **[verified]**. FS's Rhalâim cultist *NPCs* exist (~25 records) — as NPCs, not as a faction |
| **The High Ones** | Only `Creature_HighOneFaction 046E9B`, an AI faction for their beast avatars **[verified]** |
| **Nehrim / the Nehrimese army** | `NehrimFaction 0773CD` (name "Nehrim") + `NehrimArmyFaction` — one of the few lore factions that is also a real combat faction (53 member NPCs) **[verified]** |

**Consequence:** organizing anything — a patch, a SPID distribution, a compatibility analysis —
around lore faction names fails. Organize around *places* (city factions, crime factions) and
*roles* (vendor, guard, creature family) instead; that is how SureAI built it.

## Crime factions — the actual law system

Only **four** factions in the whole game carry `TrackCrime` **[verified]**, one per legal
territory. Everything else that looks crime-related (`Arrest: True / AttackOnSight: True` on
ordinary factions) is vestigial default data — 335 of 335 base factions emit a `CrimeValues:`
block, so its mere presence means nothing.

| Faction | FormKey | Territory | Murder | Assault | Trespass | Pickpocket | StealMult | Jail infrastructure |
|---|---|---|---:|---:|---:|---:|---:|---|
| `A_CrimeFaction` | `08D90C:Skyrim.esm` | Ark | 1000 | 40 | 5 | 25 | 0.5 | `1126B0` marker, `112DA2` stolen goods |
| `FL_CrimeFaction` | `07286C:Skyrim.esm` | Sun Coast / Riverville | 1000 | 40 | 5 | 25 | **2.0** | `0729A2`, `072B51` |
| `UCCrimeFaction` | `137A04:Skyrim.esm` | Undercity | 1000 | 40 | 5 | 25 | 0.5 | **FS override supplies it**: `02EFC0`/`02EFC3:Enderal - Forgotten Stories.esm` |
| `D_CrimeFaction` | `02E9AD:Enderal - Forgotten Stories.esm` | Duneville (FS-new) | 1000 | 40 | 5 | 25 | 0.5 | `02E9AE`, `02E9B0` |

Two things to note: the Sun Coast fines stolen goods at **4× everyone else's rate** (StealMult 2.0
vs 0.5), and the Undercity's jail plumbing exists only in FS's override of the base record —
another reason never to copy the base version of a record FS also touches (guardrail 5).
**[verified]**

Guard factions are separate from crime factions: `ArkGuardFaction 09B715` carries its own combat
crime numbers (Murder 1000, Assault 100, Trespass 50) *without* `TrackCrime`. **[verified]**

`CrimeFaction` on an NPC is a **top-level scalar** (`CrimeFaction: 08D90C:Skyrim.esm`), not an
entry in its `Factions:` list — 605 base NPCs carry one. **[verified]**

## Vendor factions

**69 factions carry the `Vendor` flag** across both trees. **[verified]** Vendor plumbing is four
sibling top-level keys on the faction — not a nested block:

```yaml
Flags:
- Vendor
VendorBuySellList: 048440:Skyrim.esm     # FormList of item keywords traded
MerchantContainer: 0729D6:Skyrim.esm     # the chest that IS the shop's stock
VendorValues:
  EndHour: 24
  Radius: 1024
VendorLocation:
  Target:
    MutagenObjectType: LocationTarget    # a discriminated union — also LocationCell etc.
    Link: 07008A:Skyrim.esm
```

The `MerchantContainer` link is the one that matters for loot/stock patches — it points at the
merchant chest records documented in CLAUDE.md's vendor-chest section (the `Zenderal - Kata Fixes`
merge). The faction is how you get from "a merchant" to "their chest" programmatically.

## Names and localization

Faction display names are nearly absent and half-broken **[verified]**:

- Only **41 of 431** merged factions carry a `Name` at all. A "faction directory" built on display
  names covers under 10% of records.
- Several Names are **developer comments**, not names: `IsGuardFaction` → "All Guards in here!",
  `WispBusyFaction` → "For wisp combat fix", `BardAudienceStateFaction` → "Rank 0 - applaud; Ranks
  1-100 - listen", `GuardDialogueFaction` → "Responsible for giving the guards entry to the
  dialogue".
- Shipped copy-paste errors exist: `FL_MayorHouseFA`, `FL_PlentysonHouseFA` and `FL_TavernFA` all
  display as "Liliath's house"; `Merchant_SH_Robak` displays as "Oliel"; `Merchant_Flusshaim_Vexin`
  as "Adreyo". Display names are not authoritative identity.
- **Only the `Language: English` entry of a localized string is trustworthy.** The non-English
  entries are frequently misaligned garbage — `BossesFaction`'s German "name" is "Frostwand", a
  wall; `_45E_UniDerArchivator`'s German name is a Skyrim debug string. Any extraction must
  hard-select English.

### German ↔ English glossary

EditorIDs are German; display strings are English. Searching records by the English name a player
would use returns nothing — translate first. The recurring stems (all **[verified]** against cell,
faction and NPC EditorIDs; see [`bestiary.md`](bestiary.md) for the creature-name stems):

| EditorID stem | Means | | EditorID stem | Means |
|---|---|---|---|---|
| `Flusshaim` | Riverville | | `Haendlergilde` | merchant guild (→ Golden Sickle) |
| `CapitalCity` / `Ark` | Ark | | `Schneefels` | Frostcliff |
| `Duenenhaim` / `Dunenhaim` | Duneville | | `Bauernkueste` | Farmers Coast |
| `Sonnenkueste` | Sun Coast | | `Nordwind` | Northwind |
| `Suntemple` | Sun Temple | | `Nebelhaim` | Fogville |
| `Sternenstadt` | Star City | | `Wueste` | (Powder) Desert |

## Membership, and why naive greps are wrong

Faction membership is the top-level `Factions:` list (`Rank` present on only a handful of NPC
entries game-wide):

```yaml
Factions:
- Faction: 014C6F:Skyrim.esm      # BanditFaction
  Fluff: 0x000000
CrimeFaction: 08D90C:Skyrim.esm   # separate scalar, see above
```

But **566 of the 2,251 merged NPCs inherit data through a `Template:` chain**, and **441 of them
inherit `Factions` specifically** (`Configuration.TemplateFlags` contains `Factions`, so the NPC's
own `Factions:` list — usually absent — is ignored at runtime and the template's applies,
recursively). **[verified]** A grep that answers "who is in faction X" from the `Factions:` blocks
alone is wrong for about a fifth of all NPCs. Resolve the chain: follow `Template:` while the
relevant `TemplateFlags` bit is set.

Most-populated combat factions after resolution **[verified]**: `BanditFaction 014C6F` (318),
`UndeadFaction 005104` (289), `AnimalFaction 046E73`, `NehrimArmyFaction` (53),
`BossesFaction 03C755` (49).

## What this means for patching

1. **SPID and distribution configs must target record factions, not lore concepts.** There is no
   Rhalâta or Order faction to filter on — use `UC_MasterFaction`, `SuntempleFaction`, the crime
   factions, or the `Creature_*` families. (And read
   [`../tools/spid-in-enderal.md`](../tools/spid-in-enderal.md) first — most ported filters die.)
2. **FS faction overrides are full record copies, not deltas** — 14 of them, including the crime
   system's Undercity jail. Build any faction override from FS's version where one exists
   (guardrail 5), and diff to find what FS actually changed.
3. **A faction query pipeline needs the template resolver.** ~20% of membership is inherited; the
   worked example is the extraction script noted at the top of this file.
4. **Vendor factions are the index into merchant chests.** Before touching a merchant's stock,
   walk faction → `MerchantContainer` → check the chest against the contested-record list in
   CLAUDE.md (the seven Kata Fixes chests are owned).

## Checklist for a faction-touching patch

- [ ] Did you look up the *record* faction, or assume a lore faction exists?
- [ ] If the base record has an FS override, did you copy FS's version?
- [ ] If you queried membership, did you resolve `Template:` chains?
- [ ] If you read a display name, was it from the `Language: English` entry — and did you treat it
      as a label, not an identity (Liliath's house ×4)?
