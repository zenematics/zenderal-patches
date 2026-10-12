# How Enderal works

Reference documentation for building Zenderal patches. **Read `plugin-architecture.md` first** — it
contains the one fact that invalidates most Skyrim modding intuition, and the rest of these documents
assume it.

## The documents

| Document | Covers |
|---|---|
| [`plugin-architecture.md`](plugin-architecture.md) | **Start here.** The two-ESM structure, why `Skyrim.esm` is not Skyrim, what a FormKey suffix actually means, record inventory |
| [`progression-and-classes.md`](progression-and-classes.md) | XP/levels, the three point currencies, memory trees, talents, the affinity system, the custom character menu |
| [`combat.md`](combat.md) | What a combat overhaul collides with: talents, combat styles, weapons, races, the stubbed brawl system |
| [`visuals-and-world.md`](visuals-and-world.md) | Weathers, imagespaces, lighting templates, climates, worldspaces — and why ENB presets don't transfer |
| [`crafting-alchemy-economy.md`](crafting-alchemy-economy.md) | Crafting benches, 1859 recipes, Arcane Fever, the potion economy |
| [`scripting-and-actorvalues.md`](scripting-and-actorvalues.md) | Script architecture, the `_00E_` convention, **repurposed vanilla ActorValues**, key controller quests |
| [`factions.md`](factions.md) | The 335+96 faction records, why the lore factions (Rhalâta, Holy Order) mostly don't exist as records, crime/vendor factions, the German↔English glossary |
| [`bestiary.md`](bestiary.md) | Enemy families and how to classify them, the `_NNE_` tier system, per-actor XP, the boss roster — and why nothing scales to the player |
| [`world-and-dungeons.md`](world-and-dungeons.md) | The 22 real regions, the abandoned Location/EncounterZone systems, interior-cell conventions, and the full map-marker dungeon census |

## How these were written

Everything here was derived from the **serialized plugins and SureAI's own Papyrus source** in
`reference/base/`, not from recollection or community wikis. Facts cite the record or script they
came from so you can re-check them:

- Records: `reference/base/Skyrim/` and `reference/base/EnderalFS/` (Spriggit YAML)
- Scripts: `reference/base/EnderalScripts/source/scripts/` (5029 real `.psc` from SureAI)

Regenerate the record trees with `/spriggit-decompile-reference`; see CLAUDE.md → "What's in
`reference/base/`". Counts below were taken on **2026-08-01** against **Enderal SE 2.0.12.4**.

**If you can't cite it, mark it.** These documents use the same confidence convention as CLAUDE.md:

- **[verified]** — read directly out of a record or script in `reference/base/`
- **[upstream]** — from SureAI's or Mutagen's own documentation/source
- unmarked — inference or convention; treat as a hypothesis, not a fact

When you learn something new the expensive way, add it here with its citation. This directory is
worth exactly as much as its accuracy.

## The five-minute version

If you read nothing else:

1. **`Skyrim.esm` in Enderal's Data folder is Enderal**, not Skyrim — a 191 MB replacement authored
   by `mcarofano` containing 12223 `_00E_` records and no Tamriel worldspace. **[verified]**
2. **Progression is entirely custom.** No vanilla levelling, no vanilla perk UI, three separate point
   currencies, and a character menu drawn by Papyrus. Perks added to vanilla trees are unreachable.
3. **Enderal repurposes vanilla ActorValues** for its own stats — Arcane Fever lives in
   `LastFlattered`, Memory Points mirror into `DragonSouls`. **[verified]**
4. **Enderal overrides 55 vanilla script names**, and all 55 genuinely differ. Compile order matters.
5. **Lighting is wholly replaced** — 147 weathers, 339 imagespaces, 60 lighting templates, and its
   own climates. Skyrim ENB presets are a starting point, not a drop-in.
6. **Nothing scales to the player** — zero LeveledNpc records, every NPC at a fixed level, and only
   2 encounter zones (neither carries a level). Dungeons are hand-levelled. **[verified]**
