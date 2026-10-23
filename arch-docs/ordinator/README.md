# Ordinator — Perks of Skyrim: what it is, and what Zenderal could take from it

Research notes for a possible **Zenderal perk overhaul** that cherry-picks Ordinator mechanics.
Nothing here is built. Everything marked **[verified 2026-10-08]** was read off the archive the user
supplied (`E:\Mod Frankenstien\Ordinator 9.35.0-….zip`), serialized with Spriggit 0.40.0 into the
gitignored `reference/mods/Ordinator/`.

## Regenerate the lookup material

```bash
# 1. serialize (lookup only — SkyrimSE release, it is a Skyrim mod)
"<spriggitCli>" serialize --InputPath "<Ordinator - Perks of Skyrim.esp>" --OutputPath reference/mods/Ordinator --GameRelease SkyrimSE --PackageName Spriggit.Yaml.Skyrim --PackageVersion 0.40.0
# 2. human-readable catalog: every tree perk, every rank, skill requirement, description, entry points
python -I arch-docs/ordinator/tools/01-build-catalog.py reference/mods/Ordinator reference/mods/Ordinator-catalog.md
# 3. implementation class per perk + which vanilla perk IDs it overrides and what they are in Enderal
python -I arch-docs/ordinator/tools/02-classify-perks.py reference/mods/Ordinator reference/base/Skyrim <out.json>
```

`reference/mods/Ordinator-catalog.md` is the thing to read when choosing perks.

## The archive **[verified 2026-10-08]**

| | |
|---|---|
| Version | 9.35.0, by Enai Siaion |
| Plugin | `Ordinator - Perks of Skyrim.esp`, 1.8 MB, **HEDR 1.71**, not ESL |
| Masters | `Skyrim.esm`, `Update.esm`, **`Dragonborn.esm`** (an empty stub in Enderal) |
| BSAs | main + textures. **465 compiled `.pex`, zero `.psc`** — no source shipped |
| Records | 828 Perks, 1324 MGEFs, 951 Spells, 360 Messages, 221 Keywords, 137 Globals, 41 Quests … |
| Player-facing perks | **469 tree nodes** across the **18 vanilla skill trees** (rank chains via `NextPerk`) |

Script dependencies: SKSE only. No PapyrusUtil, JContainers or po3 calls; one MCM script
(`ord_skse_script`). 88 scripts use `RegisterForSingleUpdate`, **36 use `OnHit`**, 17 use animation
events.

## Why it cannot simply be installed

1. **Its perks live in the vanilla `ActorValueInformation` perk trees, which Enderal never draws.**
   Every one of the 469 nodes would be unreachable (see
   [`progression-and-classes.md`](../enderal/progression-and-classes.md) — perks must be in a
   `*Perks` FormList, or granted some other way).
2. **103 of its tree perks are overrides of vanilla perk FormIDs.** 89 of those IDs do not exist in
   Enderal's `Skyrim.esm` (they would be injected as orphan records), and **14 land on real Enderal
   records** that Ordinator would overwrite, including:

   | FormID | In Enderal | Ordinator puts there |
   |---|---|---|
   | `05218E` | `_00E_Class_Phasmalist_P04_B_ArcaneSmith` (an FS talent) | Arcane Blacksmith |
   | `058F67` | `_00E_PowerBashPerk` | Power Bash |
   | `0581F9`, `105F23`, `05820C`, `058213`, `0581FD` | Respite, SilentRoll, LightFoot, MuffledMovement, QuietCasting | rewritten versions |
   | `03AF81`, `052D52`, `0CB406`, `0CB407`, `0D799C`, `0D799E` | SavageStrike, DevastatingBlow, (Great)CriticalCharge, Oblivion/SoulStealer | rewritten versions |

   Also `058F68` (DeflectArrows) is one of **EGO's 61 injected records**. So a whole-plugin install
   would silently rewrite Enderal/EGO perks the player may already own.
3. **Lore.** Divines, shrines, Daedra, Coldharbour, Dragonborn blood, Dwemer autocannons, Thu'um,
   "major cities of Skyrim", the Dragons of Fate. Whole sub-systems (Bone Altars, Spirit Tutors,
   Robber's Eye, Thief's Eye) place things in Skyrim's world or quests.
4. **EGO is already the balance layer.** It puts 42 perks on `Player 000007` and rebalances the
   memory trees; Ordinator's "+25/50% damage" masteries would stack on top of it.

## What *does* carry over

**The combat vocabulary resolves in Enderal.** All weapon-type keywords (`WeapTypeSword 01E711` …
`WeapTypeBattleaxe 06D932`), `ArmorLight/Heavy/Clothing`, and the attack-type keywords Ordinator's
directional perks test with `IsAttackType` (e.g. `PowerAttackTypeForward 0914E6`) all exist at the
same FormIDs in Enderal's `Skyrim.esm`. **[verified]** So a perk built purely from entry points
usually ports by copying the record and repointing its own internal references.

Implementation class of the 469 nodes **[verified]** (per record — a perk that only modifies another
perk inherits that perk's class, e.g. Judgment needs Clash of Champions):

| Class | Count | Port cost |
|---|---:|---|
| **E** — entry points only | 248 | Copy + renumber. Cheapest. |
| **A** — ability spell, no script | 40 | Copy the SPEL + MGEFs too. Cheap. |
| **S** — a script on the perk, spell or effect | 181 | Needs the `.pex` decompiled (Champollion is **not installed**), read, Enderal-checked, and recompiled. Each is real work. |

Per tree, with class, is in the catalog; the combat trees in short:

- **One-Handed** — E: Cross Cut, Mangle, Apex Predator, Skull Crack, Savage, Death Adder, Rogue's
  Parry, Aftershock, Judgment. S: Clash of Champions, Bleed Like a Lamb, Denting Blows, Smite, all
  the directional power-attack perks (Falling Sword, Windswept, Shieldbiter, Twin Fang, …).
- **Two-Handed** — E: Death or Glory, Rive, Execute, Batter, Grand Slam, Bear Hide. A: Crushing
  Blows, Clash of Heroes, Decimate. S: Bleed Like a Dog, Maul, Avalanche, Pendulum, Subjugate, …
- **Block** — E: Dominion, Dragon Scales, Poke the Dragon, Apocalypse Proof (all hang off **Timed
  Block, which is S**).
- **Heavy / Light Armor** — mostly E: Never Kneel, Battle Weary, Out of the Inferno, Immortal,
  Sovereign, Annoying Mosquitoes, Into the Maelstrom, Wardancer, As a Leaf, Wild and Free.
- **Archery** — E: Long Shot, Thread the Needle, Clean Kill. Most of the rest is S.
- **Destruction** — strikingly portable: 29 of 37 are E (Combustion / Merciless Cold / Ionized Path
  missing-resource scaling, Frostfall, Crystalize, Scarring Burns, Conflagration, Hypothermia,
  Electroconvulsions, Glacial Prison, Cataclysm …).

## Overlap with what the list already runs — check before picking

- **Directional power attacks.** For Honor Reforged repurposes the **backward** attack as its parry,
  and BFCO/MCO replace the attack system. Ordinator's "forwards/sideways/standing power attack"
  perks rely on vanilla attack-type keywords firing on the race's attack data — **must be tested in
  game** with this list's combat stack before relying on any of them.
- **`OnHit` scripts.** 36 Ordinator scripts use `OnHit`, where the "weapon" parameter is the hit
  *source* and FHR makes it a Spell on every blow (see the `OnHit` gotcha in `CLAUDE.md`).
- **Timed block / stagger / poise.** The list already has a timed-block mechanic and Chocolate Poise;
  Ordinator's Block tree and its stagger/knockdown perks would double up.
- **Shouts.** Enderal delivers *talents* through the shout machinery, so Ordinator's "when you
  shout…" perks (World Serpent, Windborne, Force Redoubled, Thu'um of War) would fire on Enderal
  talents — possibly interesting, certainly untested.
- **Enderal's own trees** (Bastion, Bladedancer, Vandal, Vagrant, …) are mostly flat-percentage
  perks; several duplicate Ordinator ideas already (Enderal has axe bleed, mace armor-ignore,
  sweeping sideways two-handed attacks, sprint power attacks).

## Decided 2026-10-08: a separate "Prophecy" tree

The picked perks get their **own perk tree**, opened by a **Prophecy** power and drawn by Custom
Skills Framework, paid for with a separate **Prophecy points** currency. Prototype: `src/Prophecy/`
(see its row in `CLAUDE.md`). The three options below were the alternatives considered.

## Alternatives considered: where would cherry-picked perks live?

Ordinator is organised **per skill** with skill-level gates. Enderal's skills have **no perks of
their own**; its perks are bought with Memory Points in 11 class trees. Three shapes, none decided:

1. **Into Enderal's memory trees** — add to a `*Perks` FormList. Unknown yet whether the Hero Menu's
   SWF can draw extra nodes or only fixed slots per tree; read `_00E_Game_SkillmenuSC` and the SWF
   before choosing this.
2. **Replace weak Enderal perks in place** — override an existing tree perk's effects with an
   Ordinator mechanic. Keeps the UI slot, but is guardrail 5's risk squared (EGO overrides these).
3. **Skill milestones, granted automatically** — an always-on ability on the player whose MGEFs are
   conditioned on `GetBaseActorValue <Skill> >= N` and carry `PerkToApply`. The perk turns on as the
   player spends Learning Points on that skill. No script, no menu work, and it gives Enderal's
   skills the per-skill identity Ordinator is built around. **Archetype not yet proven in Enderal.**

Whatever is chosen: new records at our own FormIDs (never Ordinator's vanilla-ID overrides),
`HEDR 1.70`, no `Dragonborn.esm` master, lore-renamed text, and credit Enai Siaion — check
Ordinator's permissions before shipping any of its records or scripts.

## Permissions **[verified 2026-10-21, Nexus SSE 1137 "Permissions and credits"]**

Enai Siaion's open permissions, as listed on the mod page:

- **Modification:** allowed "so long as you credit me as the original creator".
- **Conversion:** allowed to other games with credit (Enderal is the same engine, so this is a port at most).
- **Asset use:** allowed "without permission as long as you credit me".
- **Upload:** allowed with credit.
- **Not allowed:** use in anything **sold** (paid mods, Creations).
- **Ask first:** if the uploaded file is opted into Nexus **Donation Points**, get his permission.
- All assets are his own or free-to-use resources.

So Prophecy may copy Ordinator records, scripts and meshes (e.g. Smokescreen's smoke `.nif`). Obligations: credit
Enai Siaion in the plugin header and on the mod page, and keep Prophecy's Nexus upload **out of Donation Points**
unless he agrees.

### Subclasses of Skyrim 2 (Nexus SSE 98784, "Destiny" tree) — permissions **[verified 2026-10-21]**

Same open set as Ordinator — modify, convert, use assets, upload, all **with credit**; no paid use — except that
**Donation Points are allowed** without asking. It ships its Papyrus **source** (`scripts/source/dar_*.psc`), so its
scripted perks need no decompiler. Serialized at `reference/mods/SubclassesOfSkyrim/` + `-catalog.md` (52-node tree).
