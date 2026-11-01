# KittytailsPacksClean: Kittytails' spell packs, made safe for Enderal

**Ships:** generated same-name copies of three plugins, each in its own MO2 mod *<pack> - Enderal cleaned plugin
(Zenderal)*. Not committed; built from the user's install by
`src/KittytailsPacksClean/tools/01-build-cleaned-packs.py`.

**Why it exists.** Prophecy masters four of Kittytails' packs. The curator chose to install them rather than copy
them, so nothing of hers is redistributed (2026-10-27):

| Pack | Plugin | Used by |
|---|---|---|
| Abyssal Wind Magic | `Aero.esl` | Druid's Twister |
| Obscure Magic | `KittySpellPack01.esl` | Sorcerer |
| Elemental Mastery Magic | `KittySpellPack02.esl` | Sorcerer |
| Constellation Magic | `Supernova.esl` | Sorcerer |

They are Skyrim mods, and three carry content that is wrong in Enderal. Each gets a copy that drops whole top-level
groups, or single records, at the binary level, and lowers the HEDR record count to match. Spriggit is not used for
this: `Aero.esl`'s test cell holds a placed hazard (`000884`) that stops Mutagen ("XRGD: Unexpected subrecord"), so
the plugin cannot be round-tripped. Every copy serializes cleanly afterwards; that is the check.

| Plugin | Dropped | Why |
|---|---|---|
| `Aero.esl` | CELL (2 cells) | Its override of Skyrim cell `MarkarthUnderStoneKeep 016DF2` is a **placed reference** in Enderal (PilzwaldNord `001F15`): a record-type collision, as in [`IronGolemClean`](IronGolemClean.md). Plus the author's test cell. |
| `KittySpellPack01.esl` | CELL + WRLD, and NPC `09D257` | Tomes placed in 14 Skyrim/Dawnguard cells and Tamriel `00003C`, which in Enderal is the prologue worldspace MQP01Home. Seven of the cell IDs are placed references in Enderal: `01523F` in Riverville's honey press, `03FC8F`, `0C7348` in MQ08's temple, `0CAB92`, `094BAB`, `016A04` at Ark's south watchtower, and `016786`. Its NPC override `dunHagsEndHagraven 09D257` is a placed reference in `MQ11bCaveEntrance 001D8C`. |
| `Supernova.esl` | GMST | `fWeatherTransAccel` 4 → 16, which made every weather change in the list four times faster. Supernova's sky effect wants it; Prophecy does not use that spell. |
| `KittySpellPack02.esl` | nothing | |
| `KittyClass_DarkWarrior.esp` (A Dark Warrior's Tale, Rage) | NAVI, CELL, WRLD, LCTN, QUST, DIAL, DLBR, DLVW, SCEN (3078 records) | A whole Skyrim class questline: its navmesh info map `012FB4` is a floor tile in Enderal (see [`ApocalypseNaviFix`](ApocalypseNaviFix.md)); 22 exterior cells in Tamriel `00003C` (= MQP01Home), its own worldspace and interiors, a `FortSungardLocation 019185` override; the story's quests, dialogue and scenes use Skyrim/Dawnguard forms. Kept: the combat kit Prophecy's Rage casts. A full plugin slot (its IDs pass 0xFFF, so no ESL). Its forge recipes are gated on its story and never show. |

**The installs leave out three things:**

- **Every `*_DISTR.ini` (SPID).** `Aero.esl`'s class filters (`CombatMageNecro 0C969F`, `CombatWitchblade 013178`,
  `CombatNightblade 01317C`, `EncClassDragonPriest 01CE1C`) exist in Enderal, so it would hand its Skyrim-priced
  spells and a shout to Enderal NPCs. The others' filters name Skyrim forms.
- **Obscure's and Constellation's plugin `.ini`.** It sets `iMaxDesired=9750`. Plugin inis load after the profile's,
  so it would lower the list's particle limit from 22000.
- **Nothing for the tome injectors:** they target vanilla leveled lists Enderal does not have, so they are no-ops.
  The spells are reached through Prophecy.

**In MO2,** each cleaned mod must sit **above** its original, which stays enabled for its BSAs. Load all four
plugins before `Zenderal - Prophecy.esp`.

**Left as they are:**

- **Orphan overrides of records Enderal does not have:** Skyrim leveled lists `03AD91`, `10BFF1` and `04C165`, and
  Dawnguard container `00F82B`.
- **Cosmetic Dawnguard/Dragonborn references,** for [`UnresolvedRefsCleanup`](UnresolvedRefsCleanup.md) to pick up
  when it is next regenerated. Prophecy's own overrides drop theirs.

Rerun the tool after any of these packs updates. It refuses when the dropped groups or records no longer match.
Prophecy's generator reads the cleaned plugins' YAML from `reference/mods/{AbyssalWindMagic, ObscureMagic,
ElementalMasteryMagic, ConstellationMagic}` (gitignored), so re-serialize them there too. Unverified in game.
