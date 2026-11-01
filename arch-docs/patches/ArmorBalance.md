# ArmorBalance

- **Source:** `src/ArmorBalance/`
- **Ships:** `Zenderal - Armor Balance.esp` (ESL, HEDR 1.7; masters `Skyrim.esm`, `Update.esm`, FS,
  `_Fuse00_AdventurerArmor.esp`, `Grievous Rose Multicolor.esp`, `Pretty Pyrean Armory.esp`)
- **FormID block:** none (10 overrides)
- **Status:** built 2026-10-30, Spriggit round trip identical; deployed as MO2 mod `Zenderal - Armor Balance`
  (not yet enabled in the profile at the time of writing). **Unverified in game.**

## The report

Player report, 2026-10-30: the Adventurer Armor (43 in the inventory) is "like triple the armour of a
regular leather one". Curator: look into a balance pass for the list's armor.

## What was found

`tools/00-scan-armor.py` (master-aware binary walk of every enabled plugin in the `Ultra` profile) reads
every ARMO's winning armor rating, weight, value, type, slots and keywords, and every recipe that makes one.

- **The base game's armor is consistent.** Its winning values are EGO's, and
  [`PrettyArmoryEGO`](PrettyArmoryEGO.md) already puts EGO's values back over Pretty's. **[verified]**
- **What to measure a mod armor against is EGO's crafted cuirass ladder.** Every tier needs its
  blueprint (in the player's inventory or the folio) plus a Smithing level. **[verified]** (EGO's
  winning `_0?E_RecipeArmor_*Forged` records):

  | Cuirass (forged) | Leather | Firm Leather | Fine Leather | Thief | Pyrean | Assassin | Aeterna |
  |---|---|---|---|---|---|---|---|
  | Armor | 16.4 | 19.8 | 21.6 | 21.6 | 25.9 | 28.8 | 33.3 |
  | Smithing | 0 | 20 | 25 | 28 | 38 | 45 | 60 |

  The found (loot) versions sit a little lower (Leather Cuirass `01CBFC` 15.3, Pyrean `07B1F3` 24.8).
- **Fuse00's Adventurer set** (`_Fuse00_AdventurerArmor.esp`, a Skyrim mod) is 25 / 15 / 10 / 10
  (cuirass / hood / gauntlets / boots), about Pyrean level, at leather's weight. Its 4 recipes have **no
  conditions** (any forge; 1–2 iron ingots, leather strips, a pelt). The in-game 43 is the 25 after skill
  scaling. **[verified]**
- **It was also tagged as heavy iron armor while being light armor** (`ArmorHeavy 06BBD2` +
  `ArmorMaterialIron 06BBE3` on three pieces; the hood has no type keyword). So EGO's
  `XionArmorHeavyPlayer 0008CE` raised spell costs for each piece worn (×1.035 … by `ArmorHeavy` count),
  Vagrant's light-armor-only talents (`WindWalker 069CF5`, `PerfectFit 069CF8`, … test
  `WornHasKeyword ArmorHeavy`) treated it as heavy, and `Suitable Armor 069CF2` (bonus on `ArmorLight`)
  skipped it. **[verified]** in EGO's records. No talent reads either material keyword.
- **Grievous Rose** (dress 30, between Assassin and Aeterna): every recipe needs its craft book
  `000811`. Its Enderal integration (Nexus Enderal 982) gives the book to Adila in the late main quest
  "All the Dead Souls". But the book's own recipe `000_RecipeArmor_Book 000813` has **no items and no
  conditions**, so the set could be crafted at once. The integration offers an optional ESP that removes
  that recipe; it was not installed. **[verified]**
- **Pretty Pyrean's Jakal's Soldier Cuirass** `000810` is 34.8, above every light cuirass (Aeterna 33.3).
  It is lootable from the MQ07a soldiers who wear it (`_D_JakalSoldierNonPlayable`,
  `_D_JakalArcherNonPlayable` outfits; the armor records themselves are playable). Its EditorID
  `_02E_19_` puts it at Enderal's tier 19, and its helmet/gauntlets/boots (17.4 / 12.4 / 10.2) already
  fit that tier. **[verified]**
- Checked and left alone: EAM's plate set (Starling-level numbers, each piece placed once in the
  monastery, 81 weight), Pretty Holy Order Grandmaster (exactly the Keeper set's numbers), Pretty
  Factions, [`KnightOfThePath`](KnightOfThePath.md), Castle Bleakstar's Bloodmoon Shield (a quest reward,
  46.4), Kata's mage robes (Black Mage Robes 26 at weight 1, Smithing 30; generous, not broken), the
  Duneville Supply Ship's Tricorn (clothing with 18 armor, placed once).

## What the patch does

Each override is the winning record copied verbatim from `reference/mods/<mod>/` with only these fields
changed (`tools/01-build-armor-balance.py`, which first checks against `tools/armor.json` that each source
plugin still wins its record):

| Record | Change |
|---|---|
| Adventurer Armor `00080F` / Hood `00080B` / Gauntlets `000817` / Boots `000813` | 25 / 15 / 10 / 10 → **19.8 / 12.1 / 8.6 / 7.0** (Firm Leather's forged pieces); `ArmorHeavy` dropped, `ArmorLight` added, `ArmorMaterialIron` → `ArmorMaterialLeather 06BBDB`. Weight, value, models untouched |
| Their 4 recipes `000811`, `00080C`, `000819`, `000815` | + `Smithing >= 20` (EGO's Firm Leather gate; the set has no Enderal blueprint) |
| Grievous Rose `000_RecipeArmor_Book 000813` | + `Smithing >= 1000`: hidden, so the book comes only from Adila |
| Jakal's Soldier Cuirass `000810` | 34.8 → **26.6**, a quarter of the way from Pyrean (tier 18, 25.9) to Assassin (tier 22, 28.8) |

The backpacks (0 armor) and the tempering recipes are untouched. Armor already in a save keeps the new
numbers (an ARMO's rating is read from the record); a Grievous Rose book already crafted keeps working.

**Load order:** after the three mods it masters. Nothing else overrides these 10 records (live scan
2026-10-30), so the exact position does not matter; it is safe after the two load-last cleanups too,
which carry none of them.

## Regenerating

```
python -I src/ArmorBalance/tools/00-scan-armor.py      # rescans the Ultra load order -> tools/armor.json + report
python -I src/ArmorBalance/tools/01-build-armor-balance.py
```

Re-serialize a source mod into `reference/mods/` (`Fuse00AdventurerArmor`, `GrievousRoseMulticolor`,
`PrettyPyreanArmory`) after it updates. `tools/00`'s report is also the starting point for the next armor
check: it lists every mod-added armor with its recipe gates next to the base game's range for its slot.
