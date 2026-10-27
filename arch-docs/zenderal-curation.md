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

These are properties of Enderal itself, verified against the install (see [`enderal/install-and-engine.md`](enderal/install-and-engine.md) → "Enderal
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
| *(original Enderal bug, no third-party mod involved)* | — | Boarding the Ark Myrad dropped the player off the platform edge before the mount animation finished, then had it fly straight into the mountain wall behind Ark. Confirmed present with every other mod-conflict cause ruled out (exhaustive FormID scan of the whole modlist, checked twice). | **ArkMyradPlatformFix** → `Zenderal - Ark Myrad Platform Fix.esp` | One-record override: repositions reference `02F0B5:Enderal - Forgotten Stories.esm` (the actual takeoff marker, reached via the FS-only `_00E_FS_MyradTakeOffMarker` keyword on `Ark_MyradRef`'s FS override — **not** `Ark_MyradRef`'s own placement or the base-game `_00E_MyradStartPosition` marker, both of which are dead ends) toward the platform's east edge, giving the Myrad's westward-facing neck clearance before it runs off the platform's short axis. Master: `Skyrim.esm` + `Enderal - Forgotten Stories.esm`. See the postmortem in [`patches/ArkMyradPlatformFix.md`](patches/ArkMyradPlatformFix.md) for the full investigation — worth reading before touching any other Myrad-adjacent record, since this cost an entire session to a wrong-layer FormKey lookup. |

### Modern combat

| Mod | Version | Why | Patch | Notes |
|---|---|---|---|---|
| [Relentless Sword SE](https://www.nexusmods.com/skyrimspecialedition/mods/114022) — johnskyrim, **Patreon ZEN build** | 2024-03-15 | A craftable high-tier longsword and greatsword in Enderal's own dark-metal register, in plain/Fire/Ice plus the Patreon-only *Zen* design (black handle, gold runes) — eight blades. Small (43 records); overrides only two existing records — the Riverville Temple cell and one blueprint vendor list. | **RelentlessSwordPatreon** | **Install for meshes/textures only — its own `.esp` must be disabled.** The ZEN download is johnskyrim's whole mod rebuilt, so it *replaces* the free Nexus download rather than sitting alongside it; its installer has no NoRune branch and no damage branch, the only choices being Fire/Ice/**Zen** glow intensity, all asset-only, and 2K and 4K ship identical plugins and meshes. **The free six-blade Nexus build is no longer supported** — that release and its `src/RelentlessSword/` tree were removed on 2026-08-16. The shipped plugin cannot load or function in Enderal on four counts, all fixed in the patch — see below. |
| [Apocalypse — Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090) — EnaiSiaion | 10.3.0 + Enderal Patch v1.2.0 (2026-08-27) | 175 book-taught player spells, 35 per school, filling out Enderal's spell rosters. Installed as two mod folders: the original (assets) + "Apocalypse - Enderal Patch" (the [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) rebuild of its `.esp` at HEDR 1.70 with Enderal distribution/pricing/fever). | **MagicPatches** | The rebuild made it *load and distribute*; **`Zenderal - Magic Patches.esp` makes it *balanced*** — its magicka costs kept Skyrim's scale, 4–7× EGO's ladder (FF tier medians 393/720 vs EGO's 97/124 at expert/master). The patch overrides all 175 book-taught player spells with `ManualCostCalc` + repriced `BaseCost` onto EGO's per-tier medians. Regenerate via `src/MagicPatches/tools/`. Since v1.2.0 its vendor stock rides the `<Merchant>_CustomMerchandise` hooks, so it is out of the chest war and **KataFixes** no longer restores its tomes; the surviving KataFixes duty is keeping the hook entry alive in the three chests it still merges. Pack-2 Kata duplication resolved in **KataFixes**: its recompiled distribution script no longer injects the 29 spell lines both Kata packs ship (pack 1's EGO-rebalanced copies remain the obtainable ones; pack 2 keeps its unique spells). New games only — the injection quest is RunOnce. |
| [Triumvirate — Mage Archetypes](https://www.nexusmods.com/skyrimspecialedition/mods/39170) — EnaiSiaion | 1.8.0 + Enderal Conversion v1.0.0 (2026-08-27) | 75 spells across five mage archetypes (Druid, Shadow Mage, Warlock, Cleric, Shaman) — flavourful kits Enderal's rosters have nothing like. Installed as two mod folders: the original (two BSAs of assets) + "Triumvirate - Enderal Patch" (the [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) conversion: distribution rebuilt onto ten `_CustomMerchandise` hooks, DLC masters removed, tomes repriced, Tamriel renamed out). | **MagicPatches** | The conversion deliberately ships Enai's spell costs untouched, and they run up to **~10× EGO's ladder** (FF tier live medians 46/82/168/356/1207 vs EGO's 30/53/76/97/124). `Zenderal - Magic Patches.esp` overrides all 75 book-taught spells with `ManualCostCalc` + repriced `BaseCost` (tools `05`/`06`), and adds the Arcane Fever tax the conversion left out to its three self-heals (tool `07`): Aura of Vigor gets EGO's Boon fever block verbatim, Mass Immortality 5, Spirit of the Sun 10. **Magic Patches now masters Triumvirate, so it must load after it.** Its `dgintimidate*` brawl-stub overwrite (same Brawl Bugs Patch defect as Apocalypse's) is fixed by the conversion shipping SureAI's stubs loose — the patch mod folder must win that file conflict. **Conjure Ravagor and Call Hound of Hircine need [Bristlebacks In Enderal]**: both run the Dragonborn boar graph, whose 33 idle records (`BoarMoveStart`, `BoarTurnLeft`, …) and `Boar_Default_MT` live in the empty `Dragonborn.esm`, so without it the summon idles in place and never turns or moves. Bristlebacks injects them (`0179D6:Dragonborn.esm` and the `Boar*` IDLEs). Verified in game 2026-10-18. Keep it enabled while Triumvirate is. |

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

| [Apocalypse — Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090) — Enai Siaion | 10.3.0 (Enderal Patch v1.2.0, 2026-08-27) | 373 spells across all five schools; the standard answer to Enderal's thin mage offering. Enderal keeps all five vanilla magic ActorValues, so the spells themselves need no mechanical conversion. | **`Apocalypse - Enderal Patch`**, released from [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) | **Replaces `Apocalypse - Magic of Skyrim.esp`.** Install Enai's mod for its two BSAs, then let the conversion overwrite the plugin. Apocalypse ships at `HEDR` form version **1.71**, which Enderal's 1.5.97 engine silently refuses to load, so a patch is impossible — the plugin itself is rebuilt at 1.70. Delete any old `Zenderal - Apocalypse.esp`. Since v1.2.0 its vendor stock goes through the six `<Merchant>_CustomMerchandise` hook lists instead of overriding merchant chests, and the Apprentice tier moved from Maxus Tabbakus back to Tarhutie in Riverville. |

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
   of the 160 were still purchasable nowhere. So every tome is stocked by a **named merchant,
   deterministically**, tiered by the gold each carries — Emberlord and Fireflash (Master), Torius
   Flameling (Expert), Barnabas (Adept A/C/D), Ora Stonehand (Adept I/R), Tarhutie in Riverville
   (Apprentice), Milbert Foxhand (Novice). Every tome is buyable at exactly one shop. The 15 cut
   `WB_C*` Daedra/Dwemer summons have no vendor **by design**.

   > **How the stock is delivered changed in v1.2.0 (2026-08-27).** v1.1 wrote the tomes directly
   > into the six merchant chests, which put Apocalypse in the chest-override war — all six lost to
   > `EGO SE - Leveling Redone.esp` in the original order (verified 2026-08-11), then *won* after
   > the 2026-08-20 load-order flip, reverting LR's rebalance and re-selling deprecated base tomes.
   > `Zenderal - Kata Fixes.esp` spent two weeks as a seven-chest merge cleaning that up. v1.2.0
   > exits the war entirely: the stock now goes through **SureAI's own `<Merchant>_CustomMerchandise`
   > hook lists** — an empty extension-point LVLI Enderal ships inside every one of its 67 merchant
   > chests — so no merchant record is overridden at all. Kata Fixes shrank back to the three
   > genuinely contested chests (Kata staves / xxOpenSpells / Emberlord), and its overrides of those
   > **must keep the hook entry in the chest** or Apocalypse's stock dies at that shop (asserted in
   > the generator). `src/KataFixes/tools/00-audit-vendor-conflicts.py` reports the set clean.

   World loot stays random and keeps the leveled-list route: the tomes and all 130 scrolls are still
   injected into `_00E_SpellBooksLootA–D` and `00E_ScrollsLowChance` via the six sublists
   (`ZP_Apoc_Tomes_R000`–`R100`, `ZP_Apoc_Scrolls`), every existing entry untouched. The four
   `_00ETraderSpellBooksLevel*` overrides were **deleted** once the vendors carried the real thing.

   > **`KataPUMBSpellPack.esp` conflict — resolved by the hooks.** v1.1 had to leave Tarhutie's
   > chest unclaimed so Kata's 15 staves survived somewhere, which pushed the Apprentice tier to
   > Maxus Tabbakus in Duneville, and `Zenderal - Kata Fixes.esp` compensated by copying the novice
   > tomes to Tarhutie. All three workarounds are gone: the hooks touch no chest, the Apprentice
   > tier is back at Tarhutie (the town a level-1 player is actually in), and the Kata Fixes
   > curation stage was retired with it — upstream now sells every tome at exactly one shop.

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
   [`enderal/install-and-engine.md`](enderal/install-and-engine.md) "Masters"). The patch repoints or drops the references that mattered. All six FormIDs
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

| *(original tuning, not a conversion)* | — | Sprint speed felt sluggish for both the player and NPCs, and stamina ran out too fast to sprint anywhere useful. | **FasterSprint** → `Zenderal - Faster Sprint.esp` | Global (player + NPC) sprint speed boost (+92.03%) plus a sprint stamina drain cut (-50%), overriding EGO's current values directly. Overrides `NPC_Sprinting_MT`/`AIControlledNPC_Sprinting_MT` (`ForwardWalk`/`ForwardRun` only) and GMST `fSprintStaminaDrainMult`. **Must load after both `Enderal SE - Gameplay Overhaul.esp` AND `Dynamic Sprint.esp`** — the latter overrides the same two movement-type records, and losing that conflict silently reverts this patch's speed boost with no error (confirmed the real cause of a long "boost isn't showing up" investigation). **The sprint-speed portion also requires `Sprint Sneak Movement Speed Fix` (SKSE) with `WieldingMovementTypeFixes=true`** to reach armed/weapon-drawn sprint — without it, a vanilla behavior-graph bug reads `NPC_Default_MT` instead while a weapon is out (sheathed sprint, and the stamina-drain cut, are unaffected by this and always apply in full). See [`patches/FasterSprint.md`](patches/FasterSprint.md) for the full mechanism and how both were confirmed. |
| *(original tuning, not a conversion)* | — | Player feedback (2026-10-19): one-handed maces felt slow for their damage under the For Honor moveset. Every 1H mace in the list sits at weapon Speed 0.8 (axes 0.9, swords 1.0) and EGO lowered their damage. | **MaceSpeed** → `Zenderal - Mace Speed.esp` | EGO's 22 winning mace records verbatim with Speed 0.8 → 0.9 (player and NPCs). Generated from a live load-order scan; Pretty's unplayable Pyrean mace, Apocalypse's summon weapons and Castle Bleakstar's 0.85 unique left alone. Masters EGO. See [`patches/MaceSpeed.md`](patches/MaceSpeed.md). Unverified in game. |
| *(original tuning, not a conversion)* | — | Player feedback (2026-10-21): Blade Dancer felt weak next to two-handed. Start of a class-by-class perk rework on top of EGO. | **PerkOverhaul** → `Zenderal - Perk Overhaul.esp` + script | Blade Master (`069D52`): EGO's sword/dagger crit chance +10 → +25, and sword/dagger crits restore 10 Health (Papyrus Extender `OnCriticalHit` on a perk-granted ability). Hero Menu MESG `069E31` updated to match. Masters EGO. See [`patches/PerkOverhaul.md`](patches/PerkOverhaul.md). Unverified in game. |
| Biggie Traits - Enderal Conversion | — | Biggie's traits are Skyrim-flavoured; replaced with Enderal-specific ones that use Enderal's schools, places and economy. | **TraitsRework** → `Zenderal - Traits.esp` | 16 traits (pass 1: perk entry points and stat effects only), each with an upside and a downside, replace Biggie's in the trait menu; Zen Traits' 9 stay. See [`patches/TraitsRework.md`](patches/TraitsRework.md). Unverified in game. |
| *(original tuning, not a conversion)* | — | `Smart NPC Potions` and `NPCs Use Potions` are both in the list, but Enderal's humanoid NPCs carry almost no consumables, so neither had anything to act on. | **NpcPotions** → `Zenderal - NPC Potions_DISTR.ini` | SPID config, no plugin. See below. |
| *(supports EGO SE - Leveling Redone — **RETIRED 2026-10-14** with it; row kept as history)* | — | Leveling Redone provides the list's way to *spend* learning/crafting points, leaving the books' vanilla behaviour (spend 1 point → +1 skill) redundant. | **LearningBooks** → `Zenderal - Learning Books Grant Learning Points.esp` | Inverts all 72 book records: each Learning Book now **grants** +1 Learning Point (`Lernpunkte 031ACB`) and each Crafting Book +1 Crafting Point (`Handwerkspunkte 085A79`) when read, with a "You received…" notification. Overrides are EGO's records verbatim (prices/names kept) with only the consume effect swapped to two new grant MGEFs; regenerate with `src/LearningBooks/tools/01-generate-book-overrides.py`. **Memory books (`_00E_Erinnerungsbuch`) and the `+2` grant books untouched — Memory Points are a separate currency.** Masters EGO (8 Entropy/Psionics books carry its `LehrbuchForbidden` keyword), which also forces load-after-EGO. |
| [For Honor Reforged](https://www.nexusmods.com/skyrimspecialedition/mods/172176) 2.4 (**MCO version**) + Attack MCO-DXP 1.6.0.6 | — | On MCO, side and back power attacks played Enderal's vanilla animations, so For Honor Reforged's directional power attacks (picked by DMK's `DirecionalCycleMoveset`) never fired. Attack MCO-DXP's Nemesis patch reroutes only the standing power-attack state into `MCO_PowerAttack`, and `Attack_MCO.esp` only redirects `PowerAttackForward` (`019B25`). | **MCODirectionalPowerAttacks** → `Zenderal - MCO Directional Power Attacks.esp` | Overrides `PowerAttackLeft`/`PowerAttackBackward`/`PowerAttackRight` (`019B22`/`23`/`24`) with animation event `attackPowerStartInPlace`, the same one-field change `Attack_MCO.esp` makes to `019B25`. Every other subrecord is byte-identical to `Skyrim.esm`, and no other plugin in the list touches these idles. Also removes the vanilla Critical Charge / Great Critical Charge perk requirement (nothing in Enderal grants either perk) from the three sprint power-attack idles (`0EC3CC`/`CE`/`CF`), the only senders of `attackPowerStart_Sprint` on MCO, and from the two sprint light-attack idles (`0F0A3E`/`1038BF`, LMB while sprinting — `Attack_MCO.esp`'s own perk-free one did not fire in game), so FHR's sprint attack (`MCO_SprintPowerAttack`) plays again; on BFCO, BFCO's own idle sent that event. Directional power attacks, sprint power attacks and LMB sprint attacks all confirmed working in game. MCO setups only — do not install with BFCO. Also needs the original For Honor in Skyrim's `meshes`/`scripts` hidden (its OAR submods tie FHR's priorities). |

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
| Pretty Enderal Armory set (11 plugins: Common, Semi-Unique, Unique, Mages, Factions, Pyrean, Holy Order, Holy Order Grandmaster, Clothing, Backpacks, Armory - Fixes) + 5 asset-only parts (Aeterna, Companions, Righteous Path, Rune, Starling) | — | Modern visuals for Enderal's own armour, weapons and clothing. | **PrettyArmoryEGO** → `Zenderal - Pretty Armory EGO Patch.esp` | The 11 plugins load after EGO and were authored against vanilla Enderal, so 140 of the 144 records they share with EGO silently reverted EGO's armour ratings, weapon damage/crit/speed, prices, weights, enchantments, armour types (EGO's robes-as-Clothing came back as light armour) and keywords — and on Tealor and four MQ07a Pyrean soldiers, EGO's perks/skills/combat styles. They also reverted 12 Enderal SE - Bug Fixes values and AOS footsteps on 2 boots. The patch (141 generated overrides) keeps every Pretty mesh/armature/outfit and forwards those gameplay fields; it also replaces 3 Pretty Unique weapon descriptions that ship as mis-encoded Russian. Visual replacers Pretty already beats (Unique Amulet Replacer, Guard Armor Replacer Falconer) are deliberately left losing — the look is unchanged. The asset-only parts carry no plugin and need no patch. `Pretty Unique Sets` ships its own older `Pretty Pyrean Armory.esp`, overwritten by the `Pretty Pyrean Armory` mod folder. Verified build, not yet verified in game. |
| Guard Armor Replacer Falconer (Enderal Nexus 556) + Falconer Armor SE (62871) | 1.0.0.0 | Dresses Enderal's city guards in Falconer armor by repointing four ARMAs | `Zenderal - Guard Falconer Patch.esp` | Pretty Factions Armory reverted the cuirass addon `0EB250` and swapped the helmet in outfit `046ECE`, so guards wore Falconer boots/helmet over Enderal's haubergeon. Pretty Common Armory also reverts the gloves addon `0A6D7C`, deliberately left alone: guard outfits carry no gauntlets, and that addon is Heavy Leather Gauntlets for everyone |
| The Perpetuum Theater - Neo Enderal (Enderal Nexus 1092) + its EVGAT and ETATU patches | 1.0.0.0 | Rebuilds Ark's theater and opens its terrace and courtyard | **PerpetuumTheaterEVGATFix** → `Zenderal - Perpetuum Theater EVGAT Fix.esp` | Its EVGAT patch 1.0 misses four EVG Animated Traversal 2.3 refs: a plank and post that float over the rebuilt corner, plus two invisible collision planes. The fix disables them. The theater asks for a new game. |
| ETATU - Complex Material Addon (Enderal Nexus 811), Save compatible plugin `Enderal TAT CM Fixes.esp` | 0.92a | Complex-material textures and meshes for Enderal's architecture | **OldCemeteryCryptFix** → `Zenderal - Old Cemetery Crypt Fix.esp` | The plugin re-bases the Old Cemetery's house `016A98` onto `SStyrrsHouse ark`, a mesh it never ships. The house rendered as nothing, so the crypt door stood alone. The fix puts the original static back. Re-check on update (0.93 is out). |
| Enderal Grass Redone (Enderal Nexus 452) **EGR Default 2.0** + its requirements: Tamrielic Grass (SSE 46217, plain, ESLified, green tundra/Rift), Cathedral 3D Pine Grass (42032) + High Poly Green Grass Update, Origins of Forest (45719), Folkvangr (44899), Cathedral Landscapes (21954, **Grass Only**) | 2.0 | Grass overhaul for Enderal; replaced *Skyrim Flora Overhaul stripped for Enderal* + *SFO Complex Grass ENB* on 2026-10-20 | none | **Use the plain-texture builds, not the ENB Complex Grass ones (EGR ENB, Tamrielic for ENB Complex Grass, Rock Grass for ENB Complex Grass are installed but disabled).** ENB complex grass textures are 2:1 with the normal map packed in the bottom half, and the meshes map the full height; on Skyrim 1.7.104 no ENB build (0.504 and 0.505 tested) applies complex grass, so each tuft drew its normal-map half: grass looked raised by half its height and rock grass showed rainbow streaks. SFO looked raised for the same reason (SFO Complex Grass ENB's 2:1 textures won). Switch back only if an ENB build supports 1.7 complex grass. EGR's plugins are byte-identical between Default and ENB. Its 8-mod block sits at the old SFO slot (EGR highest); plugins in master order TamrielicGrass → 3D Pine Grass → Origins → Folkvangr → Cathedral Landscapes → Enderal Grass Redone, before Occlusion/DynDOLOD. All 452 EGR overrides resolve; all 70 vanilla-FormID LTEX/GRAS the requirements touch are re-overridden by EGR; after the swap no winning grass texture is complex-packed (12 naturally tall kelp/reed/flower textures). `Enderal Grass Redone.ini` sets iMinGrassSize 25 / fade 18000 / grass shadows. ~300 shapes still carry emissive 1.0, which Enderal 2.1.4 zeroed to stop meshes glowing in shadow. Unverified in game. |

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
| after `Perpetuum Theater - Enderal TAT CM Fixes.esp`, before `Occlusion.esp` | `Zenderal - Perpetuum Theater EVGAT Fix.esp` | both Perpetuum patches and `EVGAT_Enderal.esp` | It forwards the Nobles Quarter cell headers from them and disables four EVGAT refs. Mastering both theater patches enforces the order |

> The **ZEN** release is the *same plugin filename* carrying two extra swords, so it occupies the
> same load-order slot and inherits the same rule. It is an either/or with the row above, never an
> addition — see the ZEN row in the mod table. It needs the Patreon build of johnskyrim's mod for
> `relentless_zen.nif`; installed against the Nexus build, its two Zen blades are invisible while
> the other six work normally.

**Patches from this repo load last**, after everything they forward, or they are not forwarding
anything. See `enderal-record-patterns.md` §0.1.

### Asset (left-pane) priorities

| Mod | Must win over | Because |
|---|---|---|
| `Pretty Righteous Path Armory` (+ `Zenderal - Pretty Righteous Path SMP` above it) | `Enderal Remastered Armory Part 1 - Standard Armory` | Both replace the Righteous Path's `armor\ebony\` meshes and `weapons\ebony\ebonyshield.nif` (their only 25 overlaps). Pretty is the Righteous Path; ERA's remaster lives on as its own set through **KnightOfThePath** (`Zenderal - Knight of the Path.esp`, meshes copied to `armor\zenderal\knightofthepath\`). Set 2026-10-27. |
| `Ingredients` (Pfuscher, Nexus 40777) | `High Poly Project`, `Static Mesh Improvement Mod`, `Ruins Clutter Improved SE` | Its 13 ingredient meshes put salts/powders in pottery bowls. Sorted below them, it lost every file (3 salts to HPP, 10 meshes to SMIM, 2 textures to RCI): Fire/Frost/Void Salts showed as bare piles with no bowl (reported 2026-10-12). Moved directly above HPP in `modlist.txt` (Alpha 0.5); **verified in game 2026-10-12** on Fire Salts. Those 15 files are its only overlaps. |

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

Patches are built and released from this repo, not from the modlist. The CI build is run by hand
(`gh workflow run build.yml --ref main`) and publishes a timestamped pre-release; `/github-release`
promotes its archives into a named `vX.Y.Z` release. See README →
"CI build & release" and the `/github-release` skill.

When the list ships a new version, note **which patch release it pins** — a modlist referencing
"latest" is a modlist that breaks when this repo moves.

| List version | Patch release | Date | Notes |
|---|---|---|---|
| _(none yet)_ | | | |
