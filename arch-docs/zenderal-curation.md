# Zenderal — curation

What is in the list, why it is in the list, and what it cost. This is the human-facing companion to
`enderal-record-patterns.md`: that file is about *how* to write a patch, this one is about *why a
patch exists at all*.

> **Status: skeleton.** The structure, constraints and decision rules below are settled and verified.
> The **roster tables are empty on purpose** — fill them in as mods are actually chosen. An invented
> roster would be worse than none, because the first person to read it would trust it.

## The list in one paragraph

Zenderal is an Enderal: Forgotten Stories (Special Edition) modlist with three goals — **bug fixes**,
**modern combat**, and **modern visuals** — and one non-goal: it is not a total overhaul. Enderal is
a finished, authored game with its own balance, art direction and progression. Zenderal's job is to
remove the things that get in the way of playing it in 2026, not to turn it into a different game.
Every entry below has to answer *"which pillar, and what did it break?"*

## Hard constraints

These are properties of Enderal itself, verified against the install (see CLAUDE.md → "Enderal
ground truth"). They rule mods out before taste does.

| Constraint | Consequence for mod selection |
|---|---|
| Enderal SE is pinned to **SSE 1.5.97** (ships `skse64_1_5_97.dll`) | Every SKSE `.dll` plugin must be a **1.5.97 / pre-AE** build. AE (1.6.x) builds do not load. This eliminates a large share of modern Skyrim combat and UI mods outright, or restricts them to their legacy versions. **Check this first — it is the cheapest possible rejection.** |
| Enderal masters **only** `Skyrim.esm` + `Update.esm`, but ships DLC stubs the engine force-loads | A mod mastering `Dawnguard.esm`/`HearthFires.esm`/`Dragonborn.esm` **still loads** — the stubs are always active, no profile change needed. What it does not get is content: every FormID into a stub resolves to nothing, so audit what the mod actually referenced there. |
| The engine **will not load** a plugin at `HEDR` form version **1.71** | Silently — no warning, no log line, the plugin is just absent. 1.70 is the ceiling; 1.71 comes from the AE-era CK and newer tools. **Check this second, right after the SKSE version.** A 1.71 mod cannot be patched, only rebuilt at 1.70, which needs the author's permission. Five plugins currently in The Path are 1.71 and therefore inert: CS Light, DynDOLOD, Enderal Weather - HDR, standard_lighting_templates, TerrainHelper. |
| **SkyUI is built into Enderal** | Never install SkyUI separately. UI mods that assume a stock SkyUI install need checking against Enderal's copy. |
| Enderal replaces **all light settings** (SureAI's own readme) | Skyrim ENB/weather presets are starting points, not drop-ins. Cutscene fades are the canonical regression. |
| Progression is **talents (3-tier perks + WordOfPower)** in a custom menu | Mods that add to vanilla perk trees are invisible to the player. See `enderal-record-patterns.md` §0.2. |
| Enderal overrides **55 vanilla script names** | Any mod shipping a `.pex` with one of those names will clobber Enderal's version. Check the filename against Enderal's script list before installing, not after. |

## Decision rules

1. **Pillar or out.** If a mod doesn't serve bug fixes, combat, or visuals, it doesn't go in — however
   good it is.
2. **Prefer the smallest mod that does the job.** A list's patch burden scales with how much each mod
   touches. A weapon-timing tweak that edits ten records is worth more than an overhaul that edits
   ten thousand and needs a patch against everything.
3. **Prefer mods already converted for Enderal.** An existing Enderal port has already paid the
   master/keyword/script-collision tax. Search Enderal's Nexus category before Skyrim's.
4. **Record the conversion cost.** If a mod needed a patch in this repo, its roster row must name the
   patch. A mod with an unexplained patch is a mod nobody can safely remove later.
5. **Balance is Enderal's, not yours.** Combat mods get tuned toward Enderal's numbers, not the other
   way round. Enderal's difficulty curve is authored around its talent system and its economy.

## Roster

One row per mod. `Patch` names the `src/<PatchName>/` folder in this repo that makes it work, or `—`
if it needed none.

### Bug fixes

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| _(none recorded yet)_ | | | | |

### Modern combat

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| [Relentless Sword SE](https://www.nexusmods.com/skyrimspecialedition/mods/114022) — johnskyrim, **Patreon ZEN build** | 2024-03-15 | A craftable high-tier longsword and greatsword in Enderal's own dark-metal register, in plain/Fire/Ice plus the Patreon-only *Zen* design (black handle, gold runes) — eight blades. Small (43 records); overrides only two existing records — the Riverville Temple cell and one blueprint vendor list. | **RelentlessSwordPatreon** | **Install for meshes/textures only — its own `.esp` must be disabled.** The ZEN download is johnskyrim's whole mod rebuilt, so it *replaces* the free Nexus download rather than sitting alongside it; its installer has no NoRune branch and no damage branch, the only choices being Fire/Ice/**Zen** glow intensity, all asset-only, and 2K and 4K ship identical plugins and meshes. **The free six-blade Nexus build is no longer supported** — that release and its `src/RelentlessSword/` tree were removed on 2026-08-16. The shipped plugin cannot load or function in Enderal on four counts, all fixed in the patch — see below. |
| [Apocalypse — Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090) — EnaiSiaion | 9.45 (Enderal rebuild) | 175 book-taught player spells, 35 per school, filling out Enderal's spell rosters. Installed as two mod folders: the original (assets) + "Apocalypse - Enderal Patch" (the [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) rebuild of its `.esp` at HEDR 1.70 with Enderal distribution/pricing/fever). | **MagicPatches** | The rebuild made it *load and distribute*; **`Zenderal - Magic Patches.esp` makes it *balanced*** — its magicka costs kept Skyrim's scale, 4–7× EGO's ladder (FF tier medians 393/720 vs EGO's 97/124 at expert/master). The patch overrides all 175 book-taught player spells with `ManualCostCalc` + repriced `BaseCost` onto EGO's per-tier medians. Regenerate via `src/MagicPatches/tools/`. Its vendor-chest stock is restored by **KataFixes** (`Zenderal - Kata Fixes.esp`) — the real winner of those chests turned out to be `EGO SE - Leveling Redone.esp`, which was silently wiping Apocalypse's tomes, Kata's staves and xxOpenSpells' books from Funkentanz/Torius/Tarhutie. Pack-2 Kata duplication resolved in **KataFixes**: its recompiled distribution script no longer injects the 29 spell lines both Kata packs ship (pack 1's EGO-rebalanced copies remain the obtainable ones; pack 2 keeps its unique spells). New games only — the injection quest is RunOnce. |

**The ZEN build is a superset of the Nexus one, and its six shared blades are unchanged where it
matters** (verified 2026-08-06): same FormIDs, same model paths, same stats. It differs only in
display names (`Relentless Ice` → `Relentless - Ice`) and a couple of animation flags — neither of
which reaches the game, because our patch supplies those six records and johnskyrim's plugin is
disabled. Its CORE meshes are re-exports (~390 KB vs ~750 KB) but sit at the same paths and reference the same
textures, so `Zenderal - Relentless Sword.esp` works against it unchanged. Its Zen recipes gate on
the Skyforge (`0F46CE`) and the Companions global (`0F46D1`), neither of which exists in Enderal —
the same defect as the base mod, fixed the same way. Its one extra ingredient, `063B47`, **does**
exist in Enderal as `GemDiamond` ("Diamond", 280 gold, used by two of Enderal's own recipes), so it
was kept.

**Why Relentless Sword needed a conversion rather than a patch** (all verified against
`reference/base/`, 2026-08-01):

1. Its `.esp` masters `Dawnguard.esm`, `HearthFires.esm` and `Dragonborn.esm` — no record actually
   references them, but Enderal does not load them. A patch cannot rewrite another plugin's master
   list, so the records had to be re-homed.
2. Every forge recipe used `WorkbenchKeyword: 0F46CE` (Skyforge) and `GetGlobalValue 0F46D1`
   (Companions questline). **Neither FormID exists in Enderal's `Skyrim.esm`** — the recipes could
   never have appeared. Now `CraftingSmithingForge` (`088105`) gated the way Enderal gates its own
   shadowsteel tier, copying **both** conditions off
   `_03E_RecipeWeapon_27_SwordOfTheRighteousPathForged`: `GetActorValue Smithing >= 50` **and**
   possession of a blueprint. The blueprint —
   `JS_CraftingPlan_RelentlessSword`, *"Blueprint: Relentless Sword (Handicraft 50)"* — is a
   `MiscItem` built from Enderal's `_00E_CraftingPlan_04E_SwordOfTheRighteousPathForged`, and one
   copy unlocks all eight swords. It has two sources:
   - hand-placed on the noble shelf (`13476D`) in **Riverville Temple** (`FlusshaimTemple`), which
     is the only cell this patch overrides;
   - added at Level 30 to **`_00ETraderCraftingPlansC`** (`148ABE`), the vendor tier its Handicraft-50
     peers already sit in, so it is not lose-forever missable.
3. Damage was on Skyrim's scale (11 / 20), which lands near steel tier here. Retuned to parity with
   Enderal's shadowsteel tier — **23 dmg / crit 6** (1H) and **37 / crit 11** (2H), matching
   `_03E_27_SwordOfTheRighteousPathForged` and its greatsword. Weight, speed, reach, stagger and the
   1000 value are johnskyrim's, untouched.
4. Added six dismantle recipes (`InvisibleDismantling`, → shadowsteel) so the swords are not the
   only weapons in the game that cannot be broken down, plus the `WeapTypeMelee` keyword every
   Enderal weapon carries.

Everything else in the mod already resolved correctly in Enderal and was deliberately left alone —
including the **temper** recipes, whose `HasPerk 05218E` condition resolves here to Enderal's own
`_00E_Class_Phasmalist_P04_B_ArcaneSmith` ("You can improve enchanted armors and weapons"), which
means exactly what johnskyrim intended it to mean.

| [Apocalypse — Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090) — Enai Siaion | 10.2.3 | 373 spells across all five schools; the standard answer to Enderal's thin mage offering. Enderal keeps all five vanilla magic ActorValues, so the spells themselves need no mechanical conversion. | **`Apocalypse - Enderal Patch`**, released from [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) | **Replaces `Apocalypse - Magic of Skyrim.esp`.** Install Enai's mod for its two BSAs, then let the conversion overwrite the plugin. Apocalypse ships at `HEDR` form version **1.71**, which Enderal's 1.5.97 engine silently refuses to load, so a patch is impossible — the plugin itself is rebuilt at 1.70. Delete any old `Zenderal - Apocalypse.esp`. |

> **This conversion is not built in this repo.** Being a replacement plugin rather than a patch, it
> lives in [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) and is useful to any
> Enderal player, not only this list. The analysis below is kept here because it is *why the list
> installs it* — the curation rationale — and because points 1, 5 and 7 generalise to every ported
> Skyrim mod.

**Why Apocalypse needed a conversion, and what it does** (all verified against `reference/`,
2026-08-02). Unusually, the mod is not merely unbalanced in Enderal — **out of the box it delivers
literally nothing**:

1. **Its entire distribution system is dead.** `WB_PopulateLists_Quest` copies three FormLists into
   **54 vanilla vendor and loot leveled lists, none of which exist in Enderal**; the five College of
   Winterhold ritual globals it gates on are absent too, as is the `Tamriel` worldspace it places its
   utility containers in. 373 spells, zero obtainable.

   Re-homing them into Enderal's leveled lists was tried first and **is not enough**: a list is
   rolled per draw, so which tomes a shop had stayed random, and after two rounds of weighting most
   of the 160 were still purchasable nowhere. So the 160 tomes are now written **directly into six
   named merchant chests**, tiered by the gold each carries — Emberlord and Fireflash `102AD5` (1800,
   Master), Torius Flameling `118050` (1430, Expert), Barnabas `13824A` (1050, Adept A/C/D), Ora
   Stonehand `0F9320` (980, Adept I/R), Maxus Tabbakus `022BF2` (620, Apprentice), Milbert Foxhand
   `127928` (530, Novice). Every tome is buyable at exactly one shop — except the 15 novice ones,
   which `Zenderal - Kata Fixes.esp` also sells at **Tarhutie in Riverville**, since Milbert is in
   Ark and Riverville is the town a level-1 player is actually standing in.

   > **All six of those chests lose to `EGO SE - Leveling Redone.esp`** (load order 166 vs
   > Apocalypse's 125), which carries none of Apocalypse's stock — so out of the box **all 160
   > vendor tomes are unobtainable**, verified 2026-08-11 against the serialized trees.
   > `Zenderal - Kata Fixes.esp` repairs all six plus Tarhutie: 214 entries restored across seven
   > chests, and `src/KataFixes/tools/00-audit-vendor-conflicts.py` reports the set clean. The
   > remaining 15 Apocalypse tomes (`WB_C*` Daedra and Dwemer summons) have no vendor **by design** —
   > the Enderal port cut those spells.

   World loot stays random and keeps the leveled-list route: the tomes and all 130 scrolls are still
   injected into `_00E_SpellBooksLootA–D` and `00E_ScrollsLowChance` via the six sublists
   (`ZP_Apoc_Tomes_R000`–`R100`, `ZP_Apoc_Scrolls`), every existing entry untouched. The four
   `_00ETraderSpellBooksLevel*` overrides were **deleted** once the vendors carried the real thing.

   > **`KataPUMBSpellPack.esp` conflict.** It adds the same 15 staves to three of Enderal's spell
   > merchants — Funkentanz, Turious and Tarhutie — and those are their only vendor. Apocalypse loads
   > after it and does not master it, so a claimed chest drops them. Because the set is identical at
   > all three, **Tarhutie is left unclaimed** and all 15 stay buyable there; that is why the
   > Apprentice tier sits with Maxus Tabbakus (620 gold) rather than Tarhutie (630).
   >
   > That reasoning is Apocalypse's, and it no longer binds us: `Zenderal - Kata Fixes.esp` masters
   > `KataPUMBSpellPack.esp` and re-appends the 15 staves explicitly, so Tarhutie can now carry
   > Apocalypse stock without costing anything. Its novice tomes were added there for that reason.

   **Prices were Skyrim's too.** Apocalypse costs its tomes on vanilla's ladder (~50/175/330/700/1300
   novice→master), and **Enderal's entire spell-tome range is 20–350** — two exceptions in the whole
   game, Paralyze Rank II at 400 and the unique Death Storm at 600; scrolls run 10–100 with two at
   500. An untouched master tome would have listed at 1,407 gold, about the price of a unique
   greataxe (Enderal's uniques run 1100–4000). All 175 tomes and 144 scrolls are rescaled by a
   per-tier ratio — medians now 45/95/180/280/395 and scrolls 15/30/60/125/250 — which preserves
   Enai's ordering inside each tier. Magicka costs are left alone: those are his balance, not
   inherited pricing.
2. **It masters `Dragonborn.esm`.** 138 references across 70 records, resolving to six DLC FormIDs.
   A patch cannot remove another plugin's master — and does not need to: **the engine force-loads all
   three DLC stubs regardless of `plugins.txt`**, so Apocalypse loads with no user action (see
   CLAUDE.md "Masters"). The patch repoints or drops the references that mattered. All six FormIDs
   were one of two things: the **Staff Enchanter crafting system** (`DLC2StaffEnchanter` +
   `DLC2HeartStone`, 134 of the 138 refs) and three cosmetic one-offs. `DLC2MiraakRace` is the one
   record Enderal's stub actually contains, so it resolves.
3. **Staff crafting is left alone, because it is already dead.** All 67 recipes build Apocalypse's
   staves at the Dragonborn staff enchanter out of heart stones. Both the bench keyword and the
   component are Dragonborn FormIDs that resolve to nothing in Enderal, so every recipe belongs to no
   crafting menu and can never be listed — no patching required. The staves get no distribution
   either.
   > An earlier build overrode all 67 with a null `WorkbenchKeyword`, on the reasoning that a null is
   > "a real engine sentinel" and better than a dangling FormID. That was untested, and **no recipe
   > in Enderal has a null bench keyword — all 1,859 carry a real one**. The overrides were dropped:
   > they changed nothing observable and invented a record shape the game never uses. Apocalypse
   > loading cleanly on its own is the proof that the dangling reference is harmless.
   Also note `WorkbenchKeyword: Null` is *not* implicated in the load crash that dominated this
   patch's testing — see finding 7.
4. **Fabricate Object loses its Staff Enchanter option.** The spell's `WB_MinorCreation_Script` does
   `PlaceAtMe(WB_Furniture[j])` where `j` is the button index from message `08FDEA` — array and
   message are index-coupled 1:1. Staff Enchanter is **last in both**, so dropping the tail of each
   keeps every other station valid. The other eight all exist in Enderal unchanged.
5. **15 summons cut as un-Enderal** — six Dremora, both Xivilai, Weeping Daedra, Lord of Bindings,
   Six Demon Bag, Herne, Kyrkrim, Atronach Mark and the Dwemer Craftlord. Enderal has no Daedra and
   no Dwemer. They are simply never added to distribution, so no disabling machinery is needed; the
   records lie dormant. *Daedric Crescent survives* — it binds a weapon, not a creature — but is
   renamed.
6. **Tamriel names removed.** 17 spells named for Elder Scrolls gods and mages were renamed from
   Enderal's own vocabulary, chased through every user-visible string (tome, spell, magic effect,
   scroll, enchantment, book text): e.g. *Lamb of Mara → Lamb of Irlanda*, *Meridia's Wrath →
   Malphas' Wrath*, *Breath of Arkay → Breath of Tyr*, *Medora's Memory → Esara's Memory*, *Talons
   of Nirn → Talons of Vyn*, *Oblivion Unbound → Sinistra Unbound*. Only the two figures Enderal
   actually establishes as arcanists keep possessives — *Ocato's Recital → Baledor's Recital* and
   *Tharn's Prison → Girathû's Prison*; the rest became descriptive rather than attributing spells
   to figures who were never mages. Also fixed: all five **load screens** named the vanilla schools
   ("The School of Conjuration" → "The discipline of Entropy"), and the ten **Conjure Battlemage**
   summons were named by Tamriel race (Nord, Khajiit, Altmer…) → Endralean / Nehrimese / Qyranian /
   Kiléan.

7. **Apocalypse never loaded in Enderal at all, and that is why this is a replacement.**
   Enderal's 1.5.97 engine **silently refuses any plugin at `HEDR` form version 1.71** — no warning,
   no log line, the plugin is simply absent. Apocalypse is 1.71. Proven by changing four bytes in a
   copy (1.71 → 1.70) and watching `help wither 4` go from finding nothing to finding the spell.
   A patch cannot fix this from outside: it must master Apocalypse, and binding to a master the
   engine skipped is a null-pointer CTD during data load (`mov rdx, [rax+0x158]`, `rax=0`,
   `PLUGINS: Total: 0`). So the plugin itself is rebuilt at 1.70 and shipped under Enai's filename,
   which also keeps his BSAs loading. Permissions allow modification and re-upload with credit.
   > **Owning the plugin made three earlier compromises unnecessary.** The `Dragonborn.esm` master is
   > now *removed* rather than worked around; the 67 staff recipes are *deleted* rather than
   > neutralised; and the `Tamriel` worldspace override of `00003C` — which is Enderal's prologue
   > house `MQP01Home`, not Tamriel — is replaced with Enderal's own record (from Forgotten Stories,
   > which also overrides it), keeping Apocalypse's three persistent refs because a quest and a
   > faction still point at them.
   >
   > **Cost of getting there:** eleven game launches and six falsified record-level hypotheses
   > before an empty-plugin control located the fault in the 24-byte header. An interim "fix" that
   > set our patch to 1.71 was shipped and was wrong — it stopped the crash only by making our
   > plugin invisible too. CLAUDE.md now carries both the rule and the bisection order that finds it
   > in three launches instead of eleven.
8. **Two unintended field drops, corrected.** The rename passes had silently removed
   `MenuDisplayObject` from 10 scrolls and `FirstPersonModel` from one summoned weapon — both vanilla
   FormIDs Enderal lacks. Restored: Apocalypse's other 134 scrolls carry the same dangling reference,
   so forwarding it keeps all 144 consistent instead of making ten quietly different. Likewise the
   eight spell-book leveled lists were regenerated from **Forgotten Stories'** versions after being
   built from base Enderal's, which had been reverting FS's own edits to every vendor and loot tier.

**Known residue.** Fifteen references in surviving records still point at vanilla Skyrim records
Enderal lacks, all cosmetic and all inherited verbatim from Apocalypse: `MenuDisplayObject` on 10
scrolls (`076E8F`), `FirstPersonModel` on the Battlemage sword (`03FA6A`), a `TopicToSay` dialogue
topic on Breath of Tyr (×2) and Banish Living (×1) so those `Say()` calls do nothing, and Banish
Living's `BanishTargetFXActivator` so the banish has no visual effect. The patch introduces no
dangling reference of its own. Guessing replacements would be inventing mechanisms, so they are left
and recorded here instead.

| *(original tuning, not a conversion)* | — | Sprint speed felt sluggish for both the player and NPCs. | **FasterSprint** → `Zenderal - Faster Sprint.esp` | Global (player + NPC) sprint speed boost, overriding EGO's sprint values directly. Overrides `NPC_Sprinting_MT`/`AIControlledNPC_Sprinting_MT` (`ForwardWalk`/`ForwardRun` only). **Must load after `Enderal SE - Gameplay Overhaul.esp`.** |
| *(original tuning, not a conversion)* | — | `Smart NPC Potions` and `NPCs Use Potions` are both in the list, but Enderal's humanoid NPCs carry almost no consumables, so neither had anything to act on. | **NpcPotions** → `Zenderal - NPC Potions_DISTR.ini` | SPID config, no plugin. See below. |

#### NPC Potions

A **SPID config-only release** — no plugin, no script, one `_DISTR.ini` at the archive root. 15
`Item =` lines hand Enderal's three restore-consumable lines to every `ActorTypeNPC` humanoid,
level-banded onto Enderal's own `1 / 10 / 18 / 28 / 38` ladder (the bands
`_00ETraderPotion10/20/30` and the `_01E_`…`_48E_` prefixes already use), and one `DeathItem =`
line drops Ambrosia as loot.

> **This release does not work out of the box.** It requires one setting changed in *NPCs Use
> Potions* — see [Required third-party settings](#required-third-party-settings). Without it the
> Ambrosia line silently does nothing.

| Line | FormIDs (`:Skyrim.esm`, tier order) | Chance | Count |
|---|---|---|---|
| Health `_NNE_Genesungstrank` | `0028C8` `0028C5` `0028C6` `0028C7` `0028C9` | 55 | 1 |
| Mana `_NNE_Manatrank` | `0028DB` `019E3B` `090892` `09B6CB` `1037F7` | 45 | 1 |
| Stamina `_NNE_Morgenlufttrank` | `0028DE` `085668` `09B6CA` `1037F5` `1037F6` | 45 | 1 |
| Ambrosia `_00E_Ambrosia` (**`DeathItem =`**) | `0FEC69` (no level band) | 10 | 1 |

Traits `-S/-C/-D` exclude summons, children and StartsDead props.

Counts are `1` rather than `1-2` because disabling NUP's corpse-culling (below) also removed the
thing that was trimming potion piles; three potions per NPC is the compensation for that.

Four things worth not rediscovering:

- **The restore-stamina line is `Morgenlufttrank` ("Morning Air Potion"), not `Ausdauertrank`.**
  `_NNE_Ausdauertrank` is *fortify* stamina, and base Enderal ships only two tiers of it (`019E43`,
  `11A52F`); the third, `03E_Ausdauertrank 0008C0`, is a record EGO adds. Health tier FormIDs are
  also **non-monotonic** — `0028C8` is tier 1 and `0028C5` is tier 2. Both are easy to get wrong from
  the German EditorIDs alone and neither fails loudly.
- **This supersedes `Zenderal - Enemy Potions.esp`**, an untracked mod sitting at MO2 priority 24
  with no source in this repo, which banded the same three potion lines into the `_00E_MOB_Bandit`,
  `DeathItemDraugr` and `_00E_FS_DeathItem_Human` death-item leveled lists (via `ZEN_LItemPotion*`
  sublists). **Disable it** — otherwise bandits, the Lost Ones and FS humans draw from both sources.
- **Enemies will drink these, and that is the point.** SPID's `Item` adds to the base NPC's *live*
  container, not to a death item, so the two potion-AI mods finally have stock to use. Expect a real
  difficulty increase. It also means each base NPC is stamped `SPID_Processed` once per session, so
  the level band is evaluated against whichever actor of that base loads first — exact for Enderal's
  fixed-level NPCs, player-tracking for PC-level-mult ones, which is why the bands are wide.
- **Budget `Chance` per BASE NPC RECORD, not per corpse — and expect it all-or-nothing.**
  **[verified in-game 2026-08-13]** SPID rolls once per base and adds to that base's container, so a
  base that wins gives the item to *every* instance of itself and one that loses never gives it at
  all. Ambrosia shipped at 12 and read as "never drops" over ~50 kills. The log showed it working
  exactly as configured — 22 of 182 bases, 12.1% — but ~16 of those 22 were townsfolk (Ulla
  Featherdance, Marius Vonderfull, farmers, four City Guard bases), because `ActorTypeNPC` is mostly
  civilians. A fight is only 5–10 distinct enemy bases, so `0.88^8 ≈ 36%` of encounters yield none.
  The three potion lines never showed this because five tiers at 45–55 mean almost every base wins
  something. **The diagnosis is `grep -a "Registered .*/" po3_SpellPerkItemDistributor.log` plus a
  count of the `[📦]` lines — not another play session.**

  Ambrosia was raised 12 → 30 on this reasoning, and **that was treating the wrong variable** — it
  changed nothing, because the item was being *removed after distribution* (see the NUP setting
  below), not failing to be distributed. Ruling out NPCs drinking it was correct as far as it went
  (effect `1037EC` is a `Script` archetype with no restore-actor-value, so neither the vanilla AI nor
  NUP's effect-based classifier will make an NPC consume it) but ruling out one consumer is not the
  same as finding the remover. The lesson that generalises: **when a distribution looks broken, prove
  delivery and survival separately** — a clean SPID log establishes only the first. Ambrosia is now a
  `DeathItem =` at chance 10, which also rolls per corpse and sidesteps the per-base problem entirely.

### Modern visuals

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| _(none recorded yet)_ | | | | |

### Rejected

Worth keeping — it stops the same mod being re-evaluated every few months.

| Mod | Pillar | Why not |
|---|---|---|
| _(none recorded yet)_ | | |

## Load order

Enderal's stock order is two lines:

```
*Enderal - Forgotten Stories.esm
*SkyUI_SE.esp
```

Everything else is Zenderal. Record the intended ordering **and its reasons** here as it settles —
"why does this sit below that" is the part that is expensive to re-derive, and the part LOOT cannot
tell you.

| Position | Plugin | Must load after | Because |
|---|---|---|---|
| last | `Zenderal - Relentless Sword.esp` | anything editing `FlusshaimTemple` (`015282`) or `_00ETraderCraftingPlansC` (`148ABE`) | It overrides both to place and stock the crafting blueprint. A mod that edits the Riverville Temple cell and loads after it will drop the blueprint from the shelf — the vendor entry is the fallback, but the hand-placed copy is the intended find. |

> The **ZEN** release is the *same plugin filename* carrying two extra swords, so it occupies the
> same load-order slot and inherits the same rule. It is an either/or with the row above, never an
> addition — see the ZEN row in the mod table. It needs the Patreon build of johnskyrim's mod for
> `relentless_zen.nif`; installed against the Nexus build, its two Zen blades are invisible while
> the other six work normally.

**Patches from this repo load last**, after everything they forward, or they are not forwarding
anything. See `enderal-record-patterns.md` §0.1.

## Required third-party settings

Settings **inside other mods** that a Zenderal patch depends on. These are not in this repo and not
in any archive it builds — they live in a third-party mod's own config, so a fresh install of the
list will have the vendor default unless the list's build sets it. **Every row here is a silent
failure if missed**: the patch installs, its plugin or config registers cleanly, and the feature
simply does not happen.

| Mod | File | Setting | Must be | Default | Needed by |
|---|---|---|---|---|---|
| NPCs Use Potions | `SKSE\Plugins\NPCsUsePotions.ini` → `[Removal]` | `RemoveItemsOnDeath` | **`false`** | `true` | **NpcPotions** — the Ambrosia `DeathItem` |

### NPCs Use Potions — `RemoveItemsOnDeath`

**[verified in-game 2026-08-14]** NUP ships:

```ini
[Removal]
RemoveItemsOnDeath = true
ChanceToRemoveItem = 90
MaxItemsLeftAfterRemoval = 2
```

Every dying NPC has its alchemy items culled — each faces a **90% removal roll** and at most **two
survive** — and NUP does this on a worker thread (`Started RemoveItemsHandler`,
`[TESDeathEvent] Removed item {}`), so it runs *after* anything else hooked to `TESDeathEvent`.

A single-count item cannot win that against the potions distributed alongside it. Delivered at
chance **100** to **every humanoid base in the game**, Ambrosia reached **zero** corpses. Switching
from `Item =` to `DeathItem =` did not rescue it either — the SPID log showed `[💀][📦]` delivering
to all four test corpses and the loot was still empty. Only `RemoveItemsOnDeath = false` made it
appear, on every corpse, immediately.

**Two ways to set it**, both writing the same file:

1. **In-game MCM** — NPCs Use Potions → Removal → uncheck *"Remove items from NPCs after they died"*.
   Authoritative, and survives NUP rewriting the ini.
2. **Edit the ini with the game closed.** NUP reads it at load.

**Side effect, and it is not small.** Turning this off stops NUP trimming *everything*, not just
Ambrosia — corpses now keep every potion they were given rather than at most two. `NpcPotions`
compensates by distributing count `1` per line instead of `1-2` (three potions per NPC, not six). If
you would rather keep the trimming, the alternative is `RemoveItemsOnDeath = true` with
`ChanceToRemoveItem` near `50` and `MaxItemsLeftAfterRemoval` near `4`, and the Ambrosia chance
raised from 10 to roughly 20 — **an untested suggestion, not a measured one.**

> **Open packaging question.** This setting has no home in the repo: `NPCsUsePotions.ini` is
> third-party runtime config living under the gitignored `/zenderal/` tree. Before the list ships to
> anyone else it needs to be either baked into whichever mod folder supplies NUP's config in the
> Wabbajack build, or called out as a post-install step in the list's own documentation. Until then,
> the Ambrosia line works on this machine and nowhere else.

## Known conversion hazards

Running list of things that have bitten a Skyrim→Enderal conversion. Add to it as they come up; each
entry saves someone a test cycle.

| Hazard | Symptom | Check |
|---|---|---|
| AE-only SKSE plugin | SKSE fails to load, or the game closes at the splash | Mod's file page lists a 1.5.97/SE build |
| Mod masters a DLC | Plugin doesn't load; changes simply absent | `MasterReferences` in xEdit (`-EnderalSE`) |
| Ships a `.pex` colliding with one of Enderal's 55 overridden vanilla scripts | Enderal behaviour subtly regresses elsewhere | Compare the mod's `Scripts/*.pex` names against Enderal's |
| Second copy of SkyUI | UI breakage, MCM oddities | Enderal already ships `SkyUI_SE.esp` |
| Skyrim ENB/weather preset | Washed-out lighting; **broken cutscene fades** | Run one story cutscene before signing off |
| Perks added to vanilla trees | Mod appears to do nothing | Enderal draws its own talent menu |
| A mod that strips or replaces NPC inventories | Your distributed item never reaches the player, while the distributor's own log says it worked | Prove **delivery** and **survival** separately. See [Required third-party settings](#required-third-party-settings) |

## Release process

Patches are built and released from this repo, not from the modlist. `main` produces rolling
pre-release archives on every push; a `vX.Y.Z` tag cuts a named release. See README →
"CI build & release" and the `/github-release` skill.

When the list ships a new version, note **which patch release it pins** — a modlist referencing
"latest" is a modlist that breaks when this repo moves.

| List version | Patch release | Date | Notes |
|---|---|---|---|
| _(none yet)_ | | | |
