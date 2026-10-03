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
| [Relentless Sword SE](https://www.nexusmods.com/skyrimspecialedition/mods/114022) — johnskyrim | 1.0 | A craftable high-tier longsword in 1H and 2H, in Enderal's own dark-metal register. Small (34 records); overrides only two existing records — the Riverville Temple cell and one blueprint vendor list. | **RelentlessSword** | **Install for meshes/textures only — its own `.esp` must be disabled.** Install the **CORE** (runed) branch; the fire/ice glow intensity stays johnskyrim's FOMOD choice and is asset-only. The shipped plugin cannot load or function in Enderal on four counts, all fixed in the patch — see below. |

| [Apocalypse — Magic of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1090) — EnaiSiaion | 9.45 (Enderal rebuild) | 175 book-taught player spells, 35 per school, filling out Enderal's spell rosters. Installed as two mod folders: the original (assets) + "Apocalypse - Enderal Patch" (the [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) rebuild of its `.esp` at HEDR 1.70 with Enderal distribution/pricing/fever). | **MagicPatches** | The rebuild made it *load and distribute*; **`Zenderal - Magic Patches.esp` makes it *balanced*** — its magicka costs kept Skyrim's scale, 4–7× EGO's ladder (FF tier medians 393/720 vs EGO's 97/124 at expert/master). The patch overrides all 175 book-taught player spells with `ManualCostCalc` + repriced `BaseCost` onto EGO's per-tier medians. Regenerate via `src/MagicPatches/tools/`. Its vendor-chest stock is restored by **KataFixes** (`Zenderal - Kata Fixes.esp`) — the real winner of those chests turned out to be `EGO SE - Leveling Redone.esp`, which was silently wiping Apocalypse's tomes, Kata's staves and xxOpenSpells' books from Funkentanz/Torius/Tarhutie. Pack-2 Kata duplication resolved in **KataFixes**: its recompiled distribution script no longer injects the 29 spell lines both Kata packs ship (pack 1's EGO-rebalanced copies remain the obtainable ones; pack 2 keeps its unique spells). New games only — the injection quest is RunOnce. |
| Relentless Sword SE — **ZEN build** (johnskyrim, Patreon) | 2024-03-15 | The same sword with a black handle and gold runes, as a seventh design. Ships johnskyrim's whole mod rebuilt, so it *replaces* the Nexus download rather than sitting alongside it. | **RelentlessSwordZen** | **Install in place of the Nexus build**, for meshes/textures only — its own `.esp` must be disabled. Then install the **`Zenderal - Relentless Sword Zen`** archive *instead of* the plain one: both ship a plugin called `Zenderal - Relentless Sword.esp`, and the ZEN archive's copy carries all eight blades. **Never install both.** Its installer has no NoRune branch and no damage branch; the only choices are Fire/Ice/**Zen** glow intensity, all asset-only. 2K and 4K downloads ship identical plugins and meshes. |

**The ZEN build is a superset, and its six shared blades are unchanged where it matters**
(verified 2026-08-06): same FormIDs, same model paths, same stats. It differs only in display names
(`Relentless Ice` → `Relentless - Ice`) and a couple of animation flags — neither of which reaches
the game, because our patch supplies those six records and johnskyrim's plugin is disabled. Its
CORE meshes are re-exports (~390 KB vs ~750 KB) but sit at the same paths and reference the same
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
   copy unlocks all six swords. It has two sources:
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
   `127928` (530, Novice). Every tome is buyable at exactly one shop.

   World loot stays random and keeps the leveled-list route: the tomes and all 130 scrolls are still
   injected into `_00E_SpellBooksLootA–D` and `00E_ScrollsLowChance` via the six sublists
   (`ZP_Apoc_Tomes_R000`–`R100`, `ZP_Apoc_Scrolls`), every existing entry untouched. The four
   `_00ETraderSpellBooksLevel*` overrides were **deleted** once the vendors carried the real thing.

   > **`KataPUMBSpellPack.esp` conflict.** It adds the same 15 staves to three of Enderal's spell
   > merchants — Funkentanz, Turious and Tarhutie — and those are their only vendor. Apocalypse loads
   > after it and does not master it, so a claimed chest drops them. Because the set is identical at
   > all three, **Tarhutie is left unclaimed** and all 15 stay buyable there; that is why the
   > Apprentice tier sits with Maxus Tabbakus (620 gold) rather than Tarhutie (630).

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

| *(original tuning, not a conversion)* | — | Sprint speed felt sluggish for both the player and NPCs, and stamina ran out too fast to sprint anywhere useful. | **FasterSprint** → `Zenderal - Faster Sprint.esp` | Global (player + NPC) sprint speed boost (+92.03%) plus a sprint stamina drain cut (-50%), overriding EGO's current values directly. Overrides `NPC_Sprinting_MT`/`AIControlledNPC_Sprinting_MT` (`ForwardWalk`/`ForwardRun` only) and GMST `fSprintStaminaDrainMult`. **Must load after both `Enderal SE - Gameplay Overhaul.esp` AND `Dynamic Sprint.esp`** — the latter overrides the same two movement-type records, and losing that conflict silently reverts this patch's speed boost with no error (confirmed the real cause of a long "boost isn't showing up" investigation). **The sprint-speed portion also requires `Sprint Sneak Movement Speed Fix` (SKSE) with `WieldingMovementTypeFixes=true`** to reach armed/weapon-drawn sprint — without it, a vanilla behavior-graph bug reads `NPC_Default_MT` instead while a weapon is out (sheathed sprint, and the stamina-drain cut, are unaffected by this and always apply in full). See the `FasterSprint` notes in `CLAUDE.md` for the full mechanism and how both were confirmed. |
| [For Honor Reforged](https://www.nexusmods.com/skyrimspecialedition/mods/172176) 2.4 (**MCO version**) + Attack MCO-DXP 1.6.0.6 | — | On MCO, side and back power attacks played Enderal's vanilla animations, so For Honor Reforged's directional power attacks (picked by DMK's `DirecionalCycleMoveset`) never fired. Attack MCO-DXP's Nemesis patch reroutes only the standing power-attack state into `MCO_PowerAttack`, and `Attack_MCO.esp` only redirects `PowerAttackForward` (`019B25`). | **MCODirectionalPowerAttacks** → `Zenderal - MCO Directional Power Attacks.esp` | Overrides `PowerAttackLeft`/`PowerAttackBackward`/`PowerAttackRight` (`019B22`/`23`/`24`) with animation event `attackPowerStartInPlace`, the same one-field change `Attack_MCO.esp` makes to `019B25`. Every other subrecord is byte-identical to `Skyrim.esm`, and no other plugin in the list touches these idles. Also removes the vanilla Critical Charge / Great Critical Charge perk requirement (nothing in Enderal grants either perk) from the three sprint power-attack idles (`0EC3CC`/`CE`/`CF`), the only senders of `attackPowerStart_Sprint` on MCO, so FHR's sprint attack (`MCO_SprintPowerAttack`) plays again; on BFCO, BFCO's own idle sent that event. Directional power attacks confirmed working in game; sprint change built and verified, **not yet tested in game**. MCO setups only — do not install with BFCO. Also needs the original For Honor in Skyrim's `meshes`/`scripts` hidden (its OAR submods tie FHR's priorities). |

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

## Release process

Patches are built and released from this repo, not from the modlist. `main` produces rolling
pre-release archives on every push; a `vX.Y.Z` tag cuts a named release. See README →
"CI build & release" and the `/github-release` skill.

When the list ships a new version, note **which patch release it pins** — a modlist referencing
"latest" is a modlist that breaks when this repo moves.

| List version | Patch release | Date | Notes |
|---|---|---|---|
| _(none yet)_ | | | |
