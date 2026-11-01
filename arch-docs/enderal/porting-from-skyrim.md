# Porting from Skyrim: how Enderal differs

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

## How Enderal differs (and what that breaks)

This is the section to read before assuming a Skyrim mod "just works". Each entry is a verified
mechanism plus the class of patch it invalidates.

> **Porting a Skyrim mod? Use the `skyrim-to-enderal-porter` subagent first**, before planning or
> authoring anything. It runs the kill-checks in order — form version, load-proof, SKSE build,
> masters, distribution, override collisions — and decides whether the mod is portable at all and
> whether it needs a *patch* or a *replacement plugin*. The first two checks take minutes and both
> have already cost this repo a full build-and-debug cycle when skipped.
>
> **For a spell or magic mod, follow it with `enderal-magic-porter`.** That one carries everything the
> Apocalypse port cost: the five renamed schools (Alteration is *Mentalism*, Illusion is *Psionics* —
> the intuitive pairing is wrong), rebuilding distribution when Enderal has no spell tomes at all,
> repricing onto a 20–350 range, making self-heals pay Arcane Fever, renaming the Elder Scrolls gods
> out of every string, and cutting the Daedra and Dwemer summons.

**Progression is not Skyrim's.** There is no learn-by-doing and no vanilla perk tree UI. Enderal's
*talents* are three-tier **Perks** paired with **WordOfPower** unlocks, read back via
`_00E_TalentLibrary.GetPlayerTalentLevel(Perk01, Perk02, Perk03)` and
`GetTalentLevel(Word01, Word02, Word03)`. **[verified]** The character sheet is a **custom menu** —
`_00E_Game_SkillmenuSC`, a script on a ReferenceAlias that registers for `"Journal Menu"` and draws
Enderal's own UI. **[verified]**

> **Consequence.** A combat mod that adds perks to vanilla perk trees puts them somewhere the player
> can never see or buy. Combat patches must hang new behaviour off Enderal's own perks/talents, or
> off keywords and combat styles, not off the vanilla progression UI.

**Lighting is wholly replaced.** SureAI's own readme: *"since Enderal changes all light settings, no
ENB preset made for Skyrim would produce adequate lighting in Enderal. Furthermore, ENB mods may
deactivate fadeouts in cutscenes, leading to visual bugs."* **[verified — quoted from
`enderal readme.txt`]**

> **Consequence.** For the visuals pillar, a Skyrim ENB/weather/lighting mod is a starting point, not
> a drop-in. Budget for an Enderal-specific reconciliation pass, and watch cutscene fades — they are
> a known ENB casualty and they are everywhere in Enderal's story.

**DLC creature graphs have no idle tree.** A creature starts moving, turning and attacking through
IDLE records rooted at its behavior graph (`BoarMoveStart`, `BoarTurnLeft`, …), and its default
movement type is a MOVT record. For Dawnguard/Dragonborn creatures both live in the DLC ESMs, which
are empty stubs in Enderal. The `.hkx` graph and animations still ship in `Skyrim - Animations.bsa`,
so the creature loads and plays its idle loop, but **it never turns or moves**. Setting the race's
`BaseMovementDefault*` does not help, because the actions still have no idle records. Triumvirate's
Ravagor and Hound of Hircine (boar graph) did exactly this until *Bristlebacks In Enderal* injected
the 33 `Boar*` IDLEs and `Boar_Default_MT 0179D6:Dragonborn.esm`. **[verified 2026-10-18]**

> **Consequence.** Before shipping a ported mod whose race uses an `Actors\DLC01\…` or
> `Actors\DLC02\…` graph, find a list plugin that injects that graph's IDLE tree. If none does, the
> creature is dead weight.

**Skyrim mods need conversion, by the author's own statement.** *"Enderal uses its own master file
(ESM). Mods that were developed for Skyrim must be adjusted to it before they can safely be used in
Enderal."* **[verified — `enderal readme.txt`]** In practice a Skyrim mod that only edits
`Skyrim.esm` records may load, but Enderal has usually already overridden the record you care about,
and Enderal's copy wins or loses purely on load order.

**The five magic schools are renamed, not replaced.** Enderal keeps all five vanilla magic
ActorValues and only changes what they are *called*. **[verified]** — read off the `AlchFortify*`
magic effects' display strings in `reference/base/Skyrim/MagicEffects/`, and corroborated by
`_00E_BookMagicDisciplines*` and the `_00E_MagicSchool*` load screens:

| Vanilla `MagicSkill` | Enderal discipline | Higher school |
|---|---|---|
| Destruction | **Elementalism** | (an art of its own) |
| Conjuration | **Entropy** | Sinistra |
| Restoration | **Light Magic** | Thaumaturgy |
| Alteration | **Mentalism** | Thaumaturgy |
| Illusion | **Psionics** | Sinistra |

> Note the last two: **Alteration is Mentalism and Illusion is Psionics.** The intuitive pairing
> (Illusion→Mentalism) is wrong, and getting it backwards mis-files every spell in a magic patch.

The consequence is good news for ported spell mods: a Skyrim spell's `MagicSkill`, magicka cost and
skill scaling all work unchanged in Enderal. What does *not* carry over is anything user-visible
that names a school — spell tomes, load screens, descriptions — because the player has never heard
of "the School of Conjuration". Enderal's own magic metaphysics vocabulary, for rewriting those
strings, is the **Sea of Eventualities** (mages "manifest an eventuality"), **Lost Ones** (its
undead), and the two higher schools above. All from `_00E_BookMagicDisciplines*`.

**Enderal-only systems to look for** before touching anything nearby (script names verified in
`ScriptsEnderal.zip`): Arcane Fever (`_00E_FS_AlchAddArcaneFever`), Phasmalism/Apparitions
(`_fs_phasmalist_controlquest`, `_00E_Phasmalist_*`), the affinity system inside
`_00E_Game_SkillmenuSC`, memory/learning points (`_00E_Lehrbuch_Plus1MemoryPointSC`,
`_00E_Lehrbuch_Plus2SkillPointsScript`), crafting books (`_00E_Handwerksbuch*`), and the
talent cooldown/control quests (`_00E_Game_TalentControlSC`, `_00E_Game_TalentCooldownSC`).

> **Enderal taxes healing MAGIC, not healing — so a ported healing spell is free money unless you tax
> it.** **[verified 2026-08-03]** Only 11 of base Enderal's 837 spells raise Arcane Fever and every
> one is a self-heal (the `_NNE_SpellBoon` and `_NNE_SpellFlashHeal` lines), plus FS's Mystical
> Panacea and two Boon scrolls. Nothing else in the game raises it — a master-tier damage spell costs
> zero, so a ported one costing zero is *correct*.
>
> **Enderal DOES have healing potions**, and none of them costs Fever: five tiers of
> `_NNE_Genesungstrank` (`01E` `0028C8` → `05E` `0028C9`, 36 → 160 HP over 4 s, 25 → 190 gold) plus
> `_00E_Medicine` `07071F`. **[verified]** So the design is a trade — potions are the finite,
> gold-priced heal and magic is the renewable one that costs Fever instead. This repo asserted the
> opposite ("Enderal has no healing potions") for a while, from an English-only name search;
> Enderal's EditorIDs are German and `Genesungstrank` displays as *"Health Potion (Cheap)"*. **Search
> `reference/base/Skyrim/Ingestibles/` by effect FormKey, not by English name.**
> Attach `11A4B6:Skyrim.esm` (`_00E_IncreaseArcaneFeverFFSelf`, FireAndForget/**Self**) as an extra
> effect item with `Magnitude` + `Duration: 1`; its script applies the Mental Expert reduction for
> you. Concentration casts need `106EA4` paired with FS's `02F42E` instead. Price against Enderal's
> own ceilings — **26 HP per fever point burst, 78 over-time** — and note that Enderal charges a
> *flat* cost per line, so HP-per-point improves with tier. **`11A4B6` is Self-delivery and has zero
> precedent on an Aimed spell across 370 non-Self spells**, so leech/drain heals cannot be taxed this
> way. Full mechanism and the worked example in
> [`crafting-alchemy-economy.md`](../enderal/crafting-alchemy-economy.md#arcane-fever); the
> worked example is `src/Apocalypse/tools/09-arcane-fever-heals.ps1` in the
> [`enderal-mods`](https://github.com/whisperdealer/enderal-mods) repo.

**A ported Skyrim gear mod's recipes are the part most likely to be silently inert.** Enderal keeps
the crafting *plumbing* (bench keywords are vanilla — see
[`crafting-alchemy-economy.md`](../enderal/crafting-alchemy-economy.md)) but not everything
around it. Two concrete traps, both found in Relentless Sword **[verified]**:

| Vanilla FormID | In Enderal | Consequence |
|---|---|---|
| `0F46CE` `CraftingSmithingSkyforge`, `0F46D1` (Companions global) | **Do not exist** — no record at either ID in `Skyrim.esm`, `Update.esm` or the FS ESM | A Skyforge recipe can never appear. Repoint to `CraftingSmithingForge` `088105`. |
| `05218E` — vanilla's Arcane Blacksmith | `_00E_Class_Phasmalist_P04_B_ArcaneSmith`, *"You can improve enchanted armors and weapons"* | A **false friend that happens to be correct**: the standard temper condition means in Enderal exactly what it meant in Skyrim. Leave it alone. |

Enderal's own forge recipes gate on **`GetActorValue Smithing >= N`** (`RunOnType: Reference`,
`Reference: 000014:Skyrim.esm`) plus, usually, owning a `_00E_CraftingPlan_*` blueprint — **not** on
smithing perks. The vanilla smithing perks `0CB40D–0CB414` all still exist, but Enderal's `Player`
NPC record **grants every one of them at rank 1 from the start** **[verified]**, so `HasPerk
EbonySmithing` is a condition that is always true and gates nothing. Copy **both** conditions from
`_03E_RecipeWeapon_27_SwordOfTheRighteousPathForged` (`148A89:Skyrim.esm`) instead — the AV check and
the `GetItemCount <blueprint> >= 1` that follows it. Shipping only the first is the easy mistake:
the recipe works, but the item unlocks on level alone, unlike every one of its tier peers.

**Blueprints are `MiscItem`s, not Books** **[verified]** — `_00E_CraftingPlan_*`, model
`Enderal\books\Craftingplans\Craftingplan.nif` with an `AlternateTextures` entry selecting a
per-weapon-type TextureSet (`_00E_CraftingPlan_OneHandedSword` `09D079`, `…TwoHandedSword` `09D07A`,
and 22 more). Keywords `VendorItemClutter` + `VendorItemTool` + `Blueprint` (`0493B5`), `Value: 150`,
`Weight: 0.1`. Their in-game names read **`Blueprint: <item> (Handicraft <N>)`** — note **Enderal
displays the `Smithing` AV as "Handicraft"** (`_00E_Levelsystem_sSkillNameSmithing`), so a blueprint
naming the vanilla skill will look wrong to a player. Vendors stock them through three level-tiered
leveled lists — `_00ETraderCraftingPlans` `137A06` (level 1), `…PlansB` `148ABD` (10+), `…PlansC`
`148ABE` (19–30). A Handicraft-50 blueprint belongs in **C at Level 30**, where the Righteous Path
and Aeterna plans sit.

For weapon balance, Enderal's scale runs ~1.6× Skyrim's: its shadowsteel (ebony) tier sword is
**23 damage / crit 6** and its greatsword **37 / crit 11** **[verified]**. Note also that
`05AD9D:Skyrim.esm` is **`IngotShadowsteel`** here, Enderal's rename of ebony — so an ebony-tier
Skyrim recipe's *materials* usually port across unchanged even when its gating does not.

**A ported mod's DISTRIBUTION is the most likely thing to be silently dead — check it first.**
**[verified]** on Apocalypse — Magic of Skyrim, whose entire loot/vendor system is inert in Enderal.
It runs a `StartGameEnabled` quest (`WB_PopulateLists_Quest`) that copies three FormLists into **54
vanilla Skyrim vendor and loot leveled lists** — and **not one of those 54 exists in Enderal**.
Neither do the five College-of-Winterhold ritual globals it gates on (`0FDE72`–`0FDE76`), nor the
`Tamriel` worldspace it places its containers in. The mod loads, its 373 spells are all present and
mechanically fine, and the player can never obtain a single one.

This generalises: **Enderal's `Skyrim.esm` is Enderal**, so a vanilla FormID is only present if
Enderal happened to keep it. Bethesda's leveled-list IDs largely did *not* survive. So for any mod
that distributes items, the port checklist is: resolve its leveled-list targets against
`reference/base/Skyrim/` **before** assuming anything else about it — a dead distribution makes every
other consideration moot. The same applies to `MenuDisplayObject`, `LoadingScreenNif`,
`FirstPersonModel` and script `Object` properties, all of which are commonly vanilla FormIDs that
Enderal lacks.

- **A ported Skyrim mod with ANY navmesh carries a NAVI override at `012FB4:Skyrim.esm` — and in Enderal
  that ID is a Forgotten Temple floor tile.** **[verified 2026-10-07]** Vanilla Skyrim's single
  `NavigationMeshInfoMap` is `00012FB4`; the CK writes an override of it into every plugin that adds or
  edits navmesh. Enderal's `Skyrim.esm` reuses the ID for REFR `DweRmLgMid01` in `ForgottenTemple 012C3B`
  (Enderal's own NAVI is `000802:Enderal - Forgotten Stories.esm`; base `Skyrim.esm`'s has a null FormKey).
  The NAVI wins and the floor ref silently never loads — a hole with no render and no collision, which
  looks like a broken mesh and is not: the mesh, textures and records all check out, and a mesh-replacer
  bisect changes nothing. Apocalypse shipped it (`ApocalypseNaviFix`). **Porting checklist item:** grep the
  serialized mod for `NavigationMeshInfoMaps/` and delete it. Diagnostic: when a ref is intact on disk but
  absent in game, scan every active plugin for that FormID **of any record type**, using each plugin's own
  master index — a type-agnostic, master-aware scan is what found this after three wrong theories.

> **A vanilla FormID that survived may be a completely different record — check what a ported mod
> OVERRIDES, not just what it references.** **[verified]** Apocalypse overrides exactly one Enderal
> record, and it is worldspace **`00003C`**. In Skyrim that is `Tamriel`; **in Enderal it is
> `MQP01Home`**, the prologue house. Its override stamps Tamriel's `MaxHeight` grid and map bounds
> over a `SmallWorld` interior-ish worldspace, drops `Parent: Vyn`, `Location` and the
> `SmallWorld`/`CannotFastTravel` flags, and gives the persistent cell a `Regions` list of five
> FormIDs — **four absent from Enderal, and the fifth (`041449`) is `_00E_Ark_1024WallRound01`, a
> Static.** The rebuilt `Apocalypse - Magic of Skyrim.esp` forwards Enderal's own record back (from
> **Forgotten Stories**, which also overrides it — guardrail 5).
>
> Generalise the *check*, not the fix: for any ported mod, list every record it overrides whose
> FormKey suffix is `:Skyrim.esm` / `:Update.esm` and confirm the Enderal record at that ID is the
> same record type **and the same thing**. A script that maps FormID → record group for both trees
> does this in seconds. Note this override was **not** the crash it looked like — it is a real
> defect, found while chasing an unrelated bug, and worth fixing on its own merits.

**Enderal's own distribution slots**, for re-homing a ported mod's items **[verified]**
(`reference/base/Skyrim/LeveledItems/`). Note Enderal has **no spell tomes at all** — it teaches
spells from `_01E_SpellBook*` Books:

| Purpose | Lists | Level bands |
|---|---|---|
| Spell books, vendor | `_00ETraderSpellBooksLevelA/B/C/D` = `118209` / `11820A` / `1376C8` / `14479B` | 1–12 / 1–18 / 14–40 / 30–55 |
| Spell books, loot | `_00E_SpellBooksLootA/B/C/D` = `13798C` / `13798D` / `1447A2` / `1447A3` | 1–7 / 10–18 / 18–33 / 30–55 |
| Scrolls, loot | `00E_ScrollsLowChance` = `0905A5` | 1+, `ChanceNone: 0.5` |
| Crafting blueprints, vendor | `_00ETraderCraftingPlans` / `…PlansB` / `…PlansC` = `137A06` / `148ABD` / `148ABE` | 1 / 10+ / 19–30 |

> **`(Rank N)` on an Enderal spell tome is an upgrade chain, not a power tier — do not add it to a
> ported mod's tomes.** **[verified]** Enderal ships the *same spell* at six strengths, and the record
> prefix is the **player level** each unlocks at: `_01E_SpellBookFireBolt` = *Spell Tome: Firebolt
> (Rank I)* at level 1, then `_10E_` (II), `_18E_` (III), `_28E_` (IV), `_38E_` (V), `_48E_` (VI) at
> levels 10/18/28/38/48. So "(Rank I)" promises the player a Rank II of that exact spell exists.
>
> Enderal follows its own rule: **13 of its 201 spell tomes carry no suffix** — Clairvoyance, Mark,
> Return, Telekinesis, Detect Life, Detect Dead, the three Wall spells, the ghostly summons, Death
> Storm — precisely the spells that exist at one strength only. A ported spell with a single version
> therefore belongs in that group, unsuffixed. Apocalypse's tomes ship as `Spell Tome: <name>` for
> this reason; it looks inconsistent next to Enderal's and is in fact the consistent choice.

**Inject, don't rewrite.** Add entries to the host list pointing at your own sublist, and carry
every existing entry through untouched (guardrail 5). One new LeveledItem per tier keeps the diff
readable and leaves Enderal's own list contents byte-identical.

> **But one entry is not enough — weight it, or your items are statistically invisible.**
> **[verified in-game 2026-08-02]** A host list picks **one entry per draw**, so a single injected
> entry gives your entire sublist the same odds as one of Enderal's individual books, no matter how
> many items are behind it. Apocalypse's 160 tomes sat behind one slot in `_00ETraderSpellBooksLevelA`
> (15 entries): even Tarhutie, the richest spell vendor at 8+10+10 draws, worked out to **~1 Apocalypse
> tome out of ~28 books**, and Milbert at 3+4 draws expected **0.3** — i.e. usually none. The
> distribution was correct and looked completely broken.
>
> Do the arithmetic before shipping: `draws x (your entries / entries at or below player level)`.
> Duplicating the injected entry — same `Level`, same `Reference` — is the lever, because it still
> touches none of Enderal's own entries. `enderal-mods`' `src/Apocalypse/tools/06-weight-distribution.ps1` tops each
> injection up to a target multiplicity and is idempotent.
>
> Two traps when picking that multiplicity, both found by measuring rather than reasoning:
> **`ChanceNone` does not dilute your share** — it gates whether the list yields anything at all, so
> a loot list does *not* need a higher weight to compensate. And **a list whose band takes only one
> of your sublists ends up on half the share of its neighbours**, so weight per *list*, not per
> injection: Enderal's `…LevelB` / `…LootB` bands admit one Apocalypse rank where A/C/D admit two.
>
> Two things that make this look like a bug when it is not: vendor stock is **cached in the save**
> (`iDaysToRespawnVendor: 2`, so a merchant only re-rolls every 2 in-game days), and
> `player.additem <LVLI FormID> 1` **resolves a leveled list on the spot** — that command is the way
> to prove distribution works without waiting or starting a new game.

> **Weighting has a ceiling: a leveled list makes an item AVAILABLE, never FINDABLE.** **[verified
> in-game 2026-08-02]** A list is rolled per draw, so *which* of your items a shop has is random
> every restock. With 160 tomes behind one sublist, even at a healthy 38% share of a big vendor's
> spell stock, most of the 160 were purchasable **nowhere**, and a player hunting one named spell had
> no route to it at all. Two rounds of weighting did not fix that, because it is not a weighting
> problem.
>
> **If every item must be reachable, place it directly** — write the item into a named merchant's
> `Container` record as an ordinary `Items:` entry. Deterministic, restocks forever, and a player can
> be told where to go. Enderal's spell merchants, ranked by the gold in their chest (the natural
> wealth ladder for tiering what each one sells) **[verified]**:
>
> | Chest | FormKey | Gold | Shop |
> |---|---|---|---|
> | `_00E_Merchant_CCFunkentanz` | `102AD5` | 1800 | Ark, Emberlord and Fireflash (`coc CapitalCityMagierkram`) |
> | `_00E_Merchant_STTurious` | `118050` | 1430 | Sun Temple, Torius Flameling (`coc SuntempleAlchemy`) |
> | `_00E_Merchant_UC_Barnabas` | `13824A` | 1050 | Undercity, Barnabas (`coc UndercityBarracks2Barnabas`) |
> | `_00E_Merchant_CCSteinschlag` | `0F9320` | 980 | Ark, Ora Stonehand |
> | `_00E_Merchant_MaxusTabbakus02` | `022BF2` | 620 | Duneville, Maxus Tabbakus |
> | `_00E_Merchant_CCMilbert` | `127928` | 530 | Ark, Milbert Foxhand |
>
> Richer merchants exist (`Nordwind_Traveller_01` 3700, `Rhalata_SisterEnvy` 2700, `DunenhaimKarymea`
> 2700) but draw from only 1–2 spell lists, so they read as incidental rather than as mage shops.
>
> **Reprice what you distribute — Enderal's gold scale is much flatter than Skyrim's.** **[verified]**
> Enderal's *entire* spell-tome range is **20–350**, with two outliers (Paralyze Rank II 400, the
> unique Death Storm 600); scrolls run **10–100** with two at 500. Vanilla Skyrim's tome ladder is
> ~50/175/330/700/1300, and a ported mod carries it in silently — Apocalypse's masters sat at a 1407
> median, 5.6x Enderal's dearest tome, and its X-school scrolls at 2500. For scale, Enderal's
> *unique weapons and armour* run 1100–4000, so a Skyrim-priced master tome costs about what a unique
> greataxe does. Rescale by a **per-tier ratio** rather than a flat value so the author's ordering
> inside each tier survives, and let tiers overlap at the edges — Enderal's own do.
> **Forgotten Stories overrides all of these**, so copy the FS record, not base Enderal's (guardrail 5).
>
> **Check what else overrides the chest before claiming it.** `KataPUMBSpellPack.esp` adds the same 15
> staves to `CCFunkentanz`, `STTurious` and `FlusshaimTarhutieContainer`, and those three shops are
> their only vendor. **[verified]** A plugin loading after it that overrides one of those chests
> without mastering it silently deletes them. Where a mod repeats an identical set across several
> chests, **sparing one chest preserves the whole set** — that is why `Apocalypse` leaves Tarhutie
> alone and hosts its Apprentice tier at Maxus Tabbakus (620 gold vs Tarhutie's 630) instead.
