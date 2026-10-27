# Prophecy

- **Source:** `src/Prophecy/` — **generated** by `tools/01-build-trees.py`; never hand-edit `ProphecyESP/` beyond `0x800–0x809`
- **Ships:** `Zenderal - Prophecy.esp` + 35 scripts + Ordinator/Subclasses meshes and textures
- **FormID block:** `0x800–0x9AF`, next free `0x9B0` (still **non-ESL**, deliberately — see below)
- **Needs:** Enderal (UIExtensions list menu ships with Enderal) and, since 2026-10-23, **Triumvirate - Mage
  Archetypes as a master** (Send a Raven's silent raven copy). Prophecy loads well after it (433 vs 291 in Ultra).
  Custom Skills Framework is NOT used

## Postmortem: points re-awarded on every opening (2026-10-24)

Report: Prophecy points kept going up each time the menu opened, without the levels for them. Papyrus log
(2026-10-23 22:45): `Cannot call GetValueInt() on a None object` / `Cannot call SetValue() on a None object` in
`ZP_ProphecyMenu.AwardPoints`. **A running quest keeps the property values it started with in a save** (the
same reason `Refresh` passes the arrays), so a save whose `ZP_ProphecyInit` started before
`ZP_ProphecyPointsEarned 0x809` existed has that property as None forever: "earned" read 0, the write failed,
and every opening re-awarded `level / 5` points. The plugin's fill was always correct.

Fix (`ZP_ProphecyMenu.psc`): `BindGlobals()` resolves `0x802`/`0x809` with `GetFormFromFile` when a property is
None, and a once-per-save `RepairLedger()` lowers the balance to `due − learned perks` (never raises it) and sets
earned to due. Side effect: points granted by Testing Cheats are clamped by that one repair. `AwardPoints`
now `Debug.Trace`s level/due/earned/points.

**Follow-up the same day: testers at level 6 had 0 points (fresh saves).** That first `RepairLedger` (V2) only ever
lowered the balance but still marked `due` as earned, so a save that first opened the menu at level 5+ never got
those points. And before it, points were only handed out when Prophecy was cast, with no sign at level-up. Now
(V3): repair sets earned = balance + learned perks (what the save was really given), capped at due, and lowers
only an inflated balance. `AwardPoints` then pays each missing point with its own prompt. `ledgerRepairedV3`
re-runs it on saves that ran V2.

**Point levels and prompts: one point every 3 levels, 30 at level 90 (curator, 2026-10-25;** before that: levels 5,
10, 15, 20, 30, then every 5, capped at 20) (`PointsDueAt`/`PointLevel`). The cap of 30 is a literal in
`PointsDueAt`: saves keep the `MaxPoints` they started with (20), so that property is now unused. Each point arrives with a `Debug.MessageBox` of flavour text
(`PointText`: five unique lines, then three in rotation) the moment it is earned. The quest script listens for
`MessageBoxMenu` closing (`RegisterForMenu`: in `OnInit` for new saves, on the first menu opening for older
ones). Enderal's `_00E_EPUpdateFunctions.levelUp` shows the level-up box and only then calls
`Game.SetPlayerLevel`, so `OnMenuClose` waits 0.5 s and re-checks.

**Existing saves:** `OnInit` of `ZP_ProphecyInit` already ran in them, so the listener would only start on the first
menu opening. Hand-written quest **`ZP_ProphecyLevelWatch 0x80E`** (StartGameEnabled, Player alias forced to
`PlayerRef`, script `ZP_ProphecyLevelWatch`) fixes that. A quest new to the plugin starts when an existing save
loads; its alias `OnInit` and every `OnPlayerLoadGame` call `ZP_ProphecyMenu.WatchLevelUps()` after a 2 s wait.
That (re)registers `MessageBoxMenu` and pays any point the save is already owed, with its prompt. `0x80E` is in
`tools/01`'s `keep` set next to `0x809`/`0x80D`; `0x804` (the prototype's old test perk) and `0x80F` stay free. `_00E_EPUpdateFunctions` itself stays
untouched ([`FeverDeathLatchFix`](FeverDeathLatchFix.md) owns it). **Rule for this quest: never rely on a property added after
release — look the form up.** `ProphecyV2`'s `ZP_ProphecySanctum` has the same award code and is not fixed
(not deployed). Unverified in game.

## Holy Templar Magic (2026-10-25)

Kittytails' *Holy Templar Magic* (`Lightpower.esl`, a Skyrim SE mod). The curator has her permission to convert the
spells, and they are to feed a reworked Faith tree. `tools/01` copies its six player spells and their 73-record
closure from `reference/mods/HolyTemplarMagic` into this plugin at `0xA1A–0xA62`, after everything else (spec:
`HOLY_*`, `write_holy`, `copy_holy_assets`). Loose meshes, the sky-bolt wav and Kittytails' four `_lip_` scripts come
from `reference/mods/_raw/HolyTemplarMagic`, a gitignored copy of the mod folder.

**Triage (skyrim-to-enderal-porter, 2026-10-25).**
- HEDR 1.7, ESL, no SKSE DLL. The scripts are vanilla Papyrus plus `Weapon.IsBow` and use no `GetFormFromFile`, so
  copying the records and remapping their properties is enough.
- Left out, because they are dead in Enderal: the 6 tomes and both injector quests (their 6 vanilla leveled lists do
  not exist), the author's test cell (a Dawnguard 001DBA override), and the NPC/SPID variants (their factions
  `0B3292:Skyrim.esm`, `014217:Dawnguard.esm` do not exist).
- **Two vanilla scripts Enderal does not ship:**
  - `magicPlaceExplosionScript` is replaced by our `ZP_HolyPlaceExplosion` (same property name). Wrath of the
    Heavens' sky-bolts depend on it.
  - `MagicPlaceHazard` is dropped from Sanctuary. Its SpawnHazard archetype already places the hazard, the same way
    Enderal's Circle of Protection works.
- The Dawnguard/Dragonborn forms are stubs in Enderal (`HOLY_SUBST`):
  - hand art → `Heal01HandEffects 01C859`;
  - inventory art → `MAGINVTurnUndead 1097CA`;
  - shaders → `TurnUnFXShader 04C6D8` (Kata's Holy Cross look);
  - impact set → `01C2AF`;
  - charge sound → `056622`;
  - far boom → `02518F`;
  - the two screen-flash ISMs and the DLC races on the shield ARMA are dropped.
- `0153D3:Skyrim.esm` (stagger push) is a vanilla form Ordinator also overrides, so the copy uses
  `remap(..., vanilla_ok=True)`.

**Balance.** The list's cost ladder (EGO medians: FF 30/53.5/76.5/97/124, Concentration 16–43/s) and Enderal's own
holy line at the same tier (Holy Ray, Holy Cross, Holy Sun Burst). The mod's "undead take double damage" is kept.

| Spell (tier) | Was | Now |
|---|---|---|
| Consecrate Dead (Novice) | 25 Magicka; restores 60 H/M/S; undead 8 | 30; restores 30; undead 15 |
| Sun Shards (Apprentice, conc.) | 41/s; 20/s | 18/s; 12/s |
| Sunlight Targe (Adept) | 180; Reflector Beam 8 | 76; beam 20 (25% magic resist, disease immunity, 120 s kept) |
| Hallowed Flare (Expert) | 275; bolt 80, 9 beams × 40 | 97; bolt 40, beams 10 |
| Sanctuary (Master) | 700; 8→24/s over 30 s | 124; 6→18/s |
| Wrath of the Heavens (Master) | 925; 120 s, bolts 80 | 160; 60 s, bolts 40 (they share Hallowed Flare's bolt spells) |

No Arcane Fever on Consecrate's heal (Faith stays fever-free, except Wrath's stated cost). The original mod can be
disabled: everything it does that works in Enderal is now in this plugin. Sun Shards, Sanctuary and the Hallowed Flare
spell itself are converted but granted by nothing.

### The Faith rework (curator's design, 2026-10-25)

The five major talents keep the old node ids, seeds and FormIDs `0x810–0x814`. The old perks are rewritten in place
(`FAITH_NEW`: the old entry points and script stripped, as for Utility Droid), so no copied closure or later ID moved,
and a save that owned an old talent owns its successor in the same position. `faith4` is the capstone now and `faith5`
the merge talent; `FAITH_CAPSTONE` tells `weave_stats`. The six stat talents stay; Serenity hangs off Templar.

| Slot | Talent | How |
|---|---|---|
| `faith1` 0x810 root | Consecrate Dead | the spell, granted by the menu (`write_menu` grants) |
| `faith2` 0x811 | Righteous Path (was Sunlight Targe) | ability `0xA63`. Script `ZP_RighteousPathEffect` sends the Reflector Beam at each attacker the player blocks (Kittytails' hit logic). 25% magic resistance, disease immunity and a `TurnUnFXShader` glow are gated on IsBlocking + left hand item type 0 or 9 (`RP_BLOCKING`), so a spell in the left hand counts (Dual Wield Parrying) and a shield or left weapon does not. Her summoned shield is NOT used: equipping it would push a spell out of the left hand |
| `faith3` 0x812 | Smite (was Hallowed Flare) | its own `ApplyCombatHitSpell` on weapons with `WeapMaterialSilver 10AA1A`, not bows (bows and muskets keep the shared gun hit spell; one combat hit spell per hit). Hit spell `0xA66`, 15% roll on its effect `0xA67`, which places Hallowed Flare's player explosion (the sky-bolt) on the target via `ZP_HolyPlaceExplosion` |
| `faith5` 0x814 merge | Templar | unchanged, fever-free |
| `faith4` 0x813 capstone | Wrath of the Lightborn (was Wrath of the Heavens) | the spell (`0xA43`), granted by the menu. No Mana (curator), 50% Arcane Fever, cloak reach 45 → 20 ft. **Fixed the same day:** the first version put `LastFlattered > -50` on every effect; the engine re-checks an active effect's conditions, so the cast's own +50% fever ended the cloak after one volley. Now `0xA43` holds only the gate effect `0xA6A` (`ZP_WrathGate`). It checks fever once at cast: at 50% or more it refuses with a message (100% kills); otherwise it casts the cloak `0xA6B` (the balanced Wrath, no conditions, full 60 s) and the fever spell `0xA6C` (`11A4B6` at 50). Code: `wrath_split` |

Rewritten records' display strings: `HOLY_RENAME`. Unverified in game.

**Righteous Path's look (2026-10-25, curator: "the shield doesn't appear while blocking").**
- **The ward shield.** `ZP_Prophecy_RighteousPath_Ward 0xA68` (ARMA `0xA69`) is Kittytails' shield copied into slot
  FX01. Her mesh's `Prn = SHIELD` puts it on the left forearm, and the left hand stays free. `ZP_RighteousPathEffect`
  wears it from `blockStart`/`blockStartOut` to `blockStop`/`blockStopOut`, re-checking every 0.25 s while it is up.
  The first version's `TurnUnFXShader` glow (`0xA65`) is off the ability.
- **Dual Wield Parrying (same day).** Its DLL forces the block by sending `blockStart`/`blockStop` *into* the graph
  and setting `IsBlocking` (its strings). That raises none of the block events above, so the ward never showed. The
  ward is now also worn by `0xA65` (`ZP_Prophecy_RighteousPath_WardEffect`, script `ZP_RighteousPathWard`, formerly
  the glow), gated on the ability with `RP_BLOCKING` like the resistances. The engine starts and ends it for any
  block, up to about a second late (the effect-condition update interval). Both paths are idempotent. A save that
  already owns the perk needs it removed and re-added for the new ability effect.
- **Instant ward (v3, same day: "appear quicker and disappear fast").** `ZenProphecyUI.dll` owns the ward when it is
  loaded. Every 33 ms it queues a game-thread check:
  - the conditions: perk `0x811`, graph `IsBlocking`, and a left hand that is empty or holds a spell or scroll;
  - on a change it equips or unequips `0xA68` with sounds off and `applyNow`, adding or removing the item.

  After a load it re-checks, which clears a ward a save may hold. Both Papyrus paths return early when
  `SKSE.GetPluginVersion("ZenProphecyUI") > 0`, so they only run under v1. See
  [`ProphecyV3.md`](ProphecyV3.md).
- **First-person ward model (same day: "a white mesh in the effect").**
  - **Cause:** `HolyShield:0` is a disc drawn with `textures\white.dds`, softened by the effect shader's view-angle
    falloff. In third person it reads as a glow; at first person's close, grazing angle it shows as a white sheet.
  - **Fix:** the ward ARMA `0xA69` has its own `FirstPersonModel`, `Lightpower\HolyShield_1st.nif`. It is the same
    mesh with that shape *detached*: its entry in the root's child list is set to -1 (four bytes, written by
    `copy_holy_assets`). The glow spot (`HolyShield:1`) and the particles stay. Third person is unchanged.
  - **The glow spot goes too (2026-10-26).** With the white disc gone, the curator saw "a smaller strip in the
    middle": the glow-spot disc `HolyShield:1`, also flat and edge-on. It is detached as well
    (`HOLY_WARD_1ST_DROP`), so first person shows only the particles; third person keeps both discs.
  - **The hidden bit did not hold.** The first version only set the shape's hidden flag; the curator still saw the
    white sheet in game the next day. The likely cause is that attaching armor 3D re-shows culled shapes; nothing
    animates that shape.
- **The beam costs 10 Mana (2026-10-26, curator).** `ZP_RighteousPathEffect.OnHit` checks Magicka ≥ 10 before
  firing and spends 10 (`DamageActorValue`). With less, the block stays an ordinary block. The ward, resistances and
  pose are unaffected. The 10 is a literal in the function, not a property: a property added later stays unset in
  saves already running the effect.
- **Why not art.** Using the mesh as hit-effect art was not pursued: no vanilla magic/effect art uses `Prn`, and the
  bone-attached body FX (`baneundeadcastbodyfx` and others) resolve their nodes some way not confirmed here.
- **The shield animations.** The graph plays shield-block clips only for a real shield in the left hand, so
  `tools/06-build-righteous-path-block.py` generates the MO2 mod **`Zenderal - Righteous Path Shield Block`** (clips
  not committed). It mirrors Dynamic Block Hit (Rebalanced)'s 15 non-javelin shield sets as OAR submods that serve
  `shd_blockidle`/`shd_blockanticipate`/`Maxsu_ShieldBlockHit` as `1hm_*`/`Maxsu_WeaponBlockHit`.
- **Conditions and priority.** Each set keeps its own conditions, except "shield in the left hand", which becomes
  `HasPerk 0x811` plus left hand of OAR type 0 or 12–17 (empty, a spell, a scroll). Priority is 2100000000 + (the
  set's own − 8970000): above everything that applies to the player.
- **First person (same day).** One more submod under `_1stperson` (priority 2100002000; the top first-person 1hm
  block set is SigmaJelly Katana's 800000003). It serves SIGMA - Shield animations - 1st person's
  `shd_blockidle/anticipate/hit/hit_vara/hit_varb` as `1hm_blockidle/anticipate/hit/hita/hitb` (vanilla's from the
  BSA if SIGMA is off), on the same conditions. Bashes and the shield equip clip are left alone. The ward needs no
  first-person model: vanilla shield ARMAs (e.g. `14587A`) have only a world model, which first person reuses.
- **Gaps.** An unarmed right hand (h2h block) and a spell in each hand are not covered. Rerun 06 after a Dynamic Block
  Hit update. Unverified in game.

## Capstones need level 30 (curator, 2026-10-25)

A capstone is the talent after its tree's W2 stat talent. All 7 need player level 30 (`CAPSTONE_LEVEL`). That is the
earliest point at which 10 points have been earned; the shortest path to a capstone costs 6. The gate lives in the
script, because `AddPerk` ignores perk conditions:
- `write_menu` writes a per-perk `LevelReq` array (30 or 0) next to the other menu arrays, on the quest and on the
  power effect.
- `ZP_ProphecyPowerEffect` passes it into `Refresh` (a new 11th argument), so existing saves get it on their next
  cast.
- `ZP_ProphecyMenu.TryLearn` refuses below the level, and the v1 cards show "- Level 30". `LevelNeeded` returns 0
  while `LevelReq` is still None.
- v3 reads `minLevel` per node from `ZenProphecyUI.json`. Below that level the DLL shows the node as locked
  ("Requires level 30").

Same day: the v1 card menu's pick buffer was `new Bool[8]` (5-talent trees) and silently dropped picks 9–11 of the
11-talent trees. It is now 16.

## Stat talents (2026-10-25)

The curator asked for six more talents per tree, with stat bonuses, after Subclasses of Skyrim 2's stat nodes. Each
tree now has 11 talents (77 in all), and points went to one every 3 levels, 30 max. Spec: `STAT_NODES` / `STAT_FX`
in `tools/01`, woven into `TREES` by `weave_stats()`:

- **W1** sits between the root and both branches (the branches now need it).
- **W2** sits between the last talent and the capstone (the capstone now needs it; it needs what the capstone needed).
- **Four side talents** each hang off one talent and unlock nothing.

Each talent is one perk with a `PerkAbilityEffect` to a constant ability (Skyrim.esm's `Ab*` effects, all checked
present in Enderal's `Skyrim.esm`). Veteran uses Fortify One-handed + Two-handed, not `AbFortifyMeleeDamage`: only an
enchantment uses `MeleeDamage`, so it is unproven. **Regen magnitudes follow SureAI's convention:** points on the
100-scale `*RateMult` read as "percent". Thaumaturge's Mental Master adds `MagickaRateMult` +10 and says "10 percent
faster", although the player sits at 10 (Mana) and 1 (Health) through `_00E_Game_AbHealRateDamageFull 01DA25` on
Player. So Mana regen talents are +10 (not the +25 first discussed: three of them would be over 8x regen), and
Health regen talents are +25 `HealRateMult`. The two regen MGEFs are copies of `AbFortifyStaminaRate 105F21`.

IDs, allocated after everything else so nothing older moved (checked: all old files byte-identical except the 21
perks whose prerequisite changed and the menu arrays): perks `0x9C4–0x9ED` in tree order, abilities `0x9EE–0xA17`,
MGEFs `0xA18` (Health) / `0xA19` (Mana). Next free: `0xA1A`. Text only: no card art (their image paths are missing
files). Existing saves: owned branches and capstones stay owned. W1/W2 can be bought later, and the extra points are
paid on load with their prompts. Unverified in game.

## What it does (2026-10-21)

The **Prophecy** power (granted once per save by `ZP_ProphecyInit`) awards Prophecy points — **one every 3 levels, max 30 (since 2026-10-25)**, counted up on every cast like Subclasses of Skyrim's `dar_sostreescript` (Enderal's leveling calls
`Game.SetPlayerLevel`, so `GetLevel()` is the Enderal level) — then sets `ZP_ProphecyShowMenu` and CSF opens one menu
with **four trees of five perks**: root → two branches → merge (needs either branch) → capstone.

| Tree | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Faith (until 2026-10-25; now the Holy Templar rework below) | Descending Light (ORD) | Respite (ORD) | Edgewalker (ORD) | Healing Presence (SoS; +1 fever/tick until 2026-10-25) | Templar (SoS; +4 fever until 2026-10-25) |

**No Arcane Fever from Faith (curator, 2026-10-25).** `add_fever` (Enderal's fever tax `11A4B6` on the two free
heals) is no longer called. With Healing Presence, fever rose every 10 s in any fight. Necromancy's fever (Legion's
cost, Corpse Fever reading it) stays: it is those talents' point.
| Sharpshooter (was Gunslinger until 2026-10-23) | Quick Reload (ORD Quick Shot) | Elemental Rounds (new) | Bleeding Shot (SoS Monk's bleed) | Run and Gun (ORD Ranger) | Deadeye (ORD Snipe) |
| Gadgets | Tripwire (ORD) | Smokescreen (ORD) | Utility Droid (was Bear Traps, ORD + Lockjaw; replaced 2026-10-23) | Clockwork Turret (ORD Dwarven Autocannon) | Overclock (ORD Firing Line + Spin Up folded) |
| Martial Arts | Iron Fist (ORD, 15% of Stamina) | Hissing Dragon (ORD) | Stunning Blows (SoS Saboteur, unarmed only) | Breaking Waves (ORD) | Flow State (new) |

**How the generator copies a perk:** the picked perk plus every record it reaches (spells, effects, activators,
explosions, sounds, art, recipes that unlock on it), renumbered into our plugin; refs to unpicked source perks →
`ZP_Prophecy_Never 0x808` (never owned, so their `HasPerk` conditions read false); Skyrim forms Enderal lacks go
through the `SUBST` table (Jorrvaskr brawl quest/location → inert dummies `0x80A/0x80B`, `DGIntimidateQuest` →
Enderal's `11A493`, Become Ethereal → dummy spell `0x80C`, the bear-trap recipe's vanilla-only item → Leather Strips);
anything else unresolved fails the run. Folded perks alias to the node's perk, so Lockjaw/Firing Line/Spin Up
conditions follow it. Ordinator's compiled scripts ship unchanged (none looks up a plugin by name); its four vanilla
script dependencies are in Enderal's `E - Misc.bsa`. Display text is de-Skyrimed (Dwarven → Clockwork etc.).

**Hand-built:** one gun hit spell `ZP_Prophecy_GunHitSpell` for both Elemental Rounds and Bleeding Shot (the engine
applies only ONE `ApplyCombatHitSpell` per hit), each effect gated on its perk via PlayerRef; perks gate on the
weapon carrying `WeapTypeBow` (muskets have it). Flow State = `ZP_FlowStateEffect` listening for TK Dodge's
`TKDR_DodgeStart` animation event, casting Ordinator's Quick Reflexes slow-time spell, 10 s cooldown.
**Shock Nova (2026-10-23, curator).** The same combat dodge also places `ZP_Prophecy_FlowStateNova 0x93D` at the player's
feet, on its own 15 s cooldown (`NovaCooldown`; the two cooldowns are independent). It is Enderal's
`ExplosionShockMass01ShockDamage 03BC85` (model `Magic\ExplosionShockMass01.nif`, its sounds, Force 128) copied without
its full-screen ISM `0D13E9`, radius 149 → 300 (~14 ft). Its enchantment `ZP_Prophecy_FlowStateNovaEnch 0x93E` copies
the shared weapon enchantment `EnchWeaponShockDamage06 045F9E` (so that one is not edited) at 40 shock damage
(`EnchShockDamageFFContact 04605C`, which EGO only tags with keyword `001F93`; resisted by Shock Resistance), conditioned
`IsHostileToActor PlayerRef` so the player and followers in the blast are spared. Values in `FLOW_NOVA` in `tools/01`.
"Perfect dodge" here is any TK Dodge RE dodge in combat: the list's TK Dodge (`tkds`, TK Dodge RE's standalone patch)
sends `TKDR_DodgeStart`; there is no separate perfect-timing check. **Existing saves:** a running Flow State effect keeps
its old property values (no `Nova`) until it restarts; `player.removeperk` / `player.addperk` on Flow State `0x823`
restarts it. Previous plugin in `E:/Zenderal-backups/2026-10-23-prophecy-pre-flow-nova/`. Unverified in game.

**Sharpshooter is muskets only (curator, 2026-10-23: "fire damage from a Sharpshooter talent on my bow").** The tree
used to key on `WeapTypeBow`, which bows and muskets share. Now every part requires a crossbow-type weapon:
`GetEquippedItemType` Right == 12 (`MUSKET_IN_HAND` / `MUSKET_TAB_COND` in `tools/01`). That is Ordo's muskets plus
the list's 4 Xion crossbows; only Enderal SE - Crossbows' keyword `00081B` tells those apart, and Prophecy does not
master that plugin.
- **Gun hit spell:** Elemental Rounds' fire, Bleeding Shot's bleed and its knife sound, Deadeye's sound and both
  Snipe markers (a bow hit no longer marks a target).
- **Quick Reload:** the `bPerkQuickdraw` flag, which also sped bow draws, is gated. Its `PerkAbQuickShot 106642`
  is shared with Enderal's Rapid Shot, so it was replaced by `ZP_Prophecy_QuickReload_Ability 0x97C`, a copy of
  Enderal SE - Crossbows' winning version keeping only its item-type-12 effect.
- **Run and Gun:** `bPerkQuickShot` gated, next to its `IsSneaking` check.
- **Deadeye:** its three crit/damage entries are gated on tab 0, and its two enchantment entries lose their
  "or a bow" (type 7) alternative.
- Unverified in game.

**Quick Reload is wired correctly for crossbows/muskets [verified from the live graph 2026-10-22].** It is
Enderal's own Rapid Shot (`_00E_Class_Trickster_P05_B_RapidShot 069CD5`) over again: the same
`PerkAbQuickShot 106642` (Enderal SE - Crossbows' winning copy: WeaponSpeedMult ×1.3 with a bow **or** crossbow)
and `SetBooleanGraphVariable bPerkQuickdraw`. A character who already has Rapid Shot gains nothing from it. In
Pandora's generated `1hm_behavior.hkx` (converted with `src/EnderalPairedAnims/tools/hkxconv`):
- `CrossBow_Reload_MSG` (and Sneak/Dwarven) bind `selectedGeneratorIndex <- bPerkQuickDraw`. Index 1 is the same
  `CrossBow_Reload.hkx` at **playbackSpeed 1.3** (`CrossBow_ReloadFast`). That covers standing, sneaking, moving
  (legs only swap) and first person. An OAR/DAR musket replacement of `CrossBow_Reload.hkx` is played 1.3× too.
- The outer `CrossBow_ReloadRootBehavior` state (`startStateId <- bPerkQuickShot`, set by Ranger / Run and Gun)
  wraps the **same** generator in both states. It only changes the AI iState tag (3 → 16): Run and Gun does
  **not** speed the reload.
- `bPerkQuickDraw` also picks the faster bow draw (`Bow_DrawNock_MSG`) and crossbow release (`CrossBow_ReleaseMSG`,
  clips bound to `weaponSpeedMult`). So the flag must stay on Quick Reload.
- Reload clip ends are safe to shorten: `reloadStop` is relative to the clip's end (−0.195 s), and `Reload` / `ReloadFast`
  fire at its start (first- and third-person graphs alike).

**Quick Reload + Rapid Shot stack (2026-10-22, `tools/04-build-quick-reload-stack.py` → MO2 mod
`Zenderal - Quick Reload Stack`, clips not committed).** One flag can't count to two, so holding both perks
reloaded no faster than holding one. The mod's OAR submods (priority 432300, plus 432301 for first-person muskets
with `DAR Rifles.esp 0x800`) require **HasPerk `0x815` AND HasPerk `069CD5`**. They swap in copies of the would-win
reload clips (loose files by MO2 order, then `Skyrim - Animations.bsa`; first-person muskets from DAR 432101),
retimed `STACK_FACTOR` 1.3 shorter. Duration, frame and block times and annotations are scaled, and poses are
unchanged (≤0.07° re-encode drift, asserted). The graph's 1.3 still applies on top, for 1.69× total:

| Reload | Neither | One perk | Both |
|---|---|---|---|
| 3rd person (Zodd's loose clip, 2.03 s) | 2.03 s | 1.56 s | 1.20 s |
| 1st person (DAR 432101 musket / vanilla) | 2.67 s | 2.05 s | 1.58 s |

Rerun the tool after any change to the crossbow animation mods. **Unverified in game.**

**Known gaps:** pistols (staves) get neither gun hit effects nor faster reload — those need `FlintlockOverhaul`'s own
shot enchantments/script to check the perks; Flow State's event registration is unverified (re-registers every 30 s);
Iron Fist's ability still grants Light Armor "experience" (inert in Enderal); EGO's `XionPowerStagger` also uses
`ApplyCombatHitSpell`, so on an unarmed power attack only one of it and Stunning Blows' stagger applies.
**Non-ESL until** CSF is proven to resolve FormIDs in a light plugin. Built 2026-10-21, round-trips (269 records,
refs/conditions/effects/entry points/properties identical); **not run in game**. Credit Enai Siaion (Ordinator) and
Darenii (Subclasses of Skyrim 2) on any upload; keep it out of Donation Points unless Enai agrees.

**The power is a Lesser Power** (`Type: LesserPower`, reusable at will — it was a once-a-day Power).

**Menu = Enderal's UIExtensions list menu (2026-10-21).** Custom Skills Framework was dropped after four in-game
tests: it draws on Skyrim's own perk screen (StatsMenu), which Enderal never uses, and under Enderal 2.1 (runtime
1.7.104, CSF 3.2.0 loaded correctly) that screen never behaved — (1) one 4-skill group on CSF's default vampire dome:
only the first tree had a constellation, entering warped and closed the menu, WASD inside crashed; (2) the vanilla
18-tree `INTPerkSkydome.nif`: constellations off-centre, entering zoomed into black; (3) four 1-skill JSON files:
tree small and off-centre, black once entered, perks cyclable; (4) legacy INI configs at Destiny's node positions:
"the whole menu swooshes away" on WASD. Ruled out: the controlmap (Stats/Menu Mode contexts identical to vanilla),
Enderal's `statsmenu.swf` (only text-fit helpers vs vanilla's NX art), Enderal scripts, `EnderalSE.dll`'s
`MenuAspectRatioFix` (off in `EnderalSE.ini`), a camera mod (curator tested). Destiny itself cannot be tried: it needs
Scrambled Bugs, which has no 1.7 build.

The power's effect calls `ZP_ProphecyMenu.RequestOpen()` on quest `ZP_ProphecyInit 0x807` (the menus run there via
`OnUpdate`, because the power's instant effect ends at once). Flow: award points → tree box `ZP_ProphecyMenu 0x80D`
→ list menu of the tree's 5 perks (learned / locked) → the perk's description box `ZP_Prophecy_Info_* 0x913–0x926`
(Learn / Back) → `AddPerk`, −1 point. Prerequisites are the quest's `ParentA`/`ParentB` int arrays (either unlocks).
All generated by `tools/01`. `0x800/0x801/0x803` globals are now unused. Not yet tested in game.

**Tripwire explosion (2026-10-21, curator's request).** When an enemy snaps the wire, a fireball goes off at their
feet: `ZP_Prophecy_TripwireBlast 0x913` = Enderal's `FireBallExp01 0439C0` + `Damage: 40`, minus its full-screen ISM
`0439C1` (the list strips screen flashes). Placed by `ZP_TripwireBlastEffect` (MGEF `0x914`), an extra effect on
Ordinator's Tripwire Snap spell (the one its untouched wire script remote-casts on whoever trips it), conditioned
`IsHostileToActor PlayerRef`; one blast per 0.5 s (`ZP_Prophecy_TripwireBlastTime 0x915`) so a snap catching several
actors explodes once. Damage is flat; Tripwire's perk text still describes only the knockdown. Unverified in game.
**Placing animation (fixed 2026-10-21).** Ordinator's kneel while the wire is laid is a quest scene,
`ORD_Tripwire_Quest_Scene_Placement 0379A9`. It runs package `0379A7` (idle `IdleSearchBody`, a kneel, on the
`HoldPosition` template) until the 5 s Tripwire Scene effect ends. The scene points at the quest, never the other
way round, so the forward-only copy dropped it and the power placed the wire with no animation. `tools/01` now
copies any scene of a copied quest, plus its closure, as `0x925–0x926`, together with its fragment script
`SF_ORD_Tripwire_Quest_Scene__010379A9`.

**Thumbnails (2026-10-21).** The curator's art (`outputs/trait-icons/ZP_Prophecy_<Perk>.png`, 1254×1254, gitignored
scratch) is converted by `tools/02-convert-thumbnails.py`: centre-cropped to 932:760, then xEdit's `Texconvx64` →
932×760 BC1/DXT1, one mip — the same format as `Zenderal - Traits`' TraitPics. Output (committed):
`assets/interface/ProphecyPics/<EditorID>.dds`, shipped by v1 only. To change a picture: replace the PNG and rerun 02.
**2026-10-25:** all 35 cards were replaced with the curator's new set (`Zenderal New Icons`). Andrasta's Owl's art file
is still named after its old perk, `ZP_Prophecy_SendaRaven` (the curator's `Owl.png`). v3 also shows these cards in its
hover tooltips.
`tools/01` clears only `assets/meshes` and `assets/textures`, so it no longer deletes these.

**Card menu amendments (2026-10-21, curator's feedback).** B612's Random button is hidden
(`_root.Traits_mc.RandomBtn_mc`, set again 0.25 s after `Show`). Card titles carry only "- Learned"; the
"Requires X" text was unreadable. Picking a locked card now shows a message box ("X: learn Y first.") and reopens
the tree. Tripwire is renamed **Explosive Tripwire** via `RENAME` in `tools/01`; `EDITORID` keeps the EditorID
`ZP_Prophecy_Tripwire`, so the art path is unchanged. The plain "Tripwire" string showed up lowercase because Papyrus
pools strings case-insensitively and vanilla has a `tripwire` script.

**Descriptions get a header; grammar pass (2026-10-24, curator).** Each card's description now starts with the
talent's name, then the text on the next line. B612's description panel is plain text: `b612_traitsmenut.swf`'s
`updateDetails` sets `ItemText_tf.text`, not `htmlText`, so bold or HTML would show literally.
- **The header is added at runtime**, in `ZP_ProphecyMenu`: `Perks[idx].GetName() + "\n" + Descriptions[idx]`. A
  Papyrus `"\n"` is a lone LF; the compiled `.pex` was checked. The first build stored `name\n\ndescription` in the
  plugin's `Descriptions` array. Mutagen writes every line break there as CRLF (even a lone `\r`, tested), and the
  field showed it as a huge gap (curator: "the space ... is massive"), consistent with Flash breaking on CR and LF
  separately. The array now holds the bare descriptions. `write_menu` still writes it as double-quoted YAML
  (`dqstrs`), and the perk records' own `Description` fields carry no header.
- **Arcane Echo's `\"`:** Ordinator's description is a double-quoted YAML scalar (`"Grants the \"Lion's Arrow\"…"`),
  and `write_menu` only unwrapped single-quoted ones, so the outer quotes and escapes reached the menu. It now
  `json.loads` double-quoted scalars.
- **All 35 texts** were reworded for grammar and consistency (`Grants the "X" power: …`, `once every N seconds`,
  `% Arcane Fever`, "Requires both hands to be empty"), with the numbers unchanged. Deadeye, Hissing Dragon and Arcane
  Echo, which kept Ordinator's text, now have explicit descriptions in `TREES`. Two texts gained facts the old
  wording left out: Utility Droid (thrown, the power recalls it, the first droid is free) and Clockwork Turret (you
  get one when you learn it).

Previous plugin in `E:/Zenderal-backups/2026-10-24-prophecy-pre-descriptions/`. Unverified in game.

**Powers are granted with `AddSpell` (2026-10-21).** Adding a perk from a script with `AddPerk` did not hand out its
`PerkAbilityEffect` when that spell is a Power or LesserPower: Explosive Tripwire was learned, but no power appeared.
`tools/01`'s `perk_powers()` finds the affected perks and writes them into the quest's `PowerPerk` and `PowerSpell`
arrays. Today these are Explosive Tripwire, Smokescreen and Clockwork Turret. The menu `AddSpell`s each power when its
perk is learned. `RepairPowers()` runs every time Prophecy opens, so perks learned before this fix get their power
back. v2's `ZP_ProphecySanctum` does the same (it repairs on Enter). Unverified in game.

**Glory tree (2026-10-21, curator's design).** A fifth tree of 5 perks: Seismic Stomp (root), then Second Wind or
Dragon Scale, then War Banner or Death or Glory (each needs either). Its records sit at `0x916–0x924`, after every other block, so adding it
renumbered nothing in existing saves. All of it is built by `write_glory` in `tools/01`.
**Order since 2026-10-24 (curator):** Seismic Stomp → Second Wind / Dragon Scale → **Surrounded** (needs either) →
**War Banner** (the capstone, needs Surrounded). Only the `TREES` order and War Banner's parent changed: the node keys
stay (`glo4` = War Banner `0x919`, `glo5` = Surrounded `0x93A`), so no FormID or card moved. A save that took War Banner
without Surrounded keeps it.
- **Seismic Stomp** (2026-10-22, replaced Gap Closer; perk `0x916` kept) is a lesser power, `0x92F–0x936`. It
  follows Enderal's own stomp beat in `_00E_MQ15_Functions.TealorBreakWall`: `PlayIdle(_00E_IdleStomp 146675)`, wait
  0.5 s, place the shockwave, `ShakeCamera(0.5)`. The idle is Enderal's FNIS basic idle `Stomp` (`stomp.hkx` in
  `FNIS_Enderal_Behavior.hkx`). Pandora's `0_Master` links that behaviour, and Enderal plays the idle on the player
  itself (the Theriantrophist transform). The shockwave `0x931` copies Apocalypse's Thrumming Stone shockwave
  `07FE7C`: its model `ApocNew\AlterationEarth_Explosion_Massive.nif` comes from Apocalypse's BSA, Force 256 and
  Radius 400. It drops Apocalypse's ISM, uses the curator's stomp sound `0x932` and Enderal's
  `FXDragonTailstompImpactSet 03F819`, and doesn't master Apocalypse. `ZP_SeismicStompEffect` then pushes every
  hostile within 400 units away from the player (`PushActorAway` 4). It casts a target-delivered copy (`0x933`/`0x934`)
  of Bleeding Shot's Monk bleed `0x829` (10/s for 5 s) on each one. The cooldown, 30 s since 2026-10-22 (was 60), uses Templar's
  pattern (`0x935`/`0x936`).
  **Launch and slow time (2026-10-22, curator's request).** Once `PushActorAway` has ragdolled the targets, a
  0.1 s wait follows, then `ApplyHavokImpulse(0, 0, 1, LiftImpulse = 200)`. That's the technique Frozen
  Electrocuted Combustion uses to float ragdolls (50–100 per nudge, scaled by mass). 200 flew higher than the
  curator wanted, so on 2026-10-22 it was lowered to 150. Height grows with the square of the impulse, so that is
  about 56%, aimed at head height. Later the same day the curator asked for another 30% off: **105** (about 49% of
  150's height, 28% of 200's). It is a script default in `ZP_SeismicStompEffect.psc`, not a record value. If any enemy is hit, the player also casts `ZP_Prophecy_SeismicStomp_SlowTime` (`0x937`/`0x938`):
  Quick Reflexes' self SlowTime effect copied at world speed 0.3 (`STOMP_SLOW`), with its dispel-after-delay script
  set to the same duration: 5 s at first, 10 s since 2026-10-22 (curator's request). Since 2026-10-22 it also drops
  Quick Reflexes' `MagicImodBasicScript`, which applied `QuickReflexesImod 10C761` (radial blur, double vision, depth
  of field) for the whole effect, so the stomp's slow time has no screen blur. Flow State's effect keeps it. Verified in game by the curator
  (knock-up, slow time, attacking afterwards, player at full speed).
  **The player keeps full speed (2026-10-22, curator: the stomp slowed them too).** Slow time slows the player as
  well, unless a perk entry `ModPlayerMagicSlowdown` overrides it. Enderal's Keeper perks Fast Reflexes `069D6C` and
  Steadfast `069D6D` set it to 0.5, and Ordinator's Quick Reflexes sets it to 1. Both gate the entry on
  `PerkQuickReflexesKeyword 046BB3`. The modification is `Set`: Spriggit omits it as the default, and it never
  appears explicitly. The Seismic Stomp perk `0x916` now has Ordinator's entry (Set 1), gated on a keyword of its own,
  `ZP_Prophecy_SeismicStompSlowKeyword 0x939`. That keyword replaces `046BB3` on the stomp's slow-time copy `0x938`,
  so Enderal's 0.5 no longer catches it and Flow State's slow time (which keeps `046BB3`) is unchanged. Untested
  claim on the CK wiki talk page: one report said the entry works, another that it did nothing. Ordinator and Enderal
  both ship it, so it is used as-is. Unverified in game.
  **Can't attack after stomping (fixed 2026-10-22).** `_00E_IdleStomp` is an FNIS idle. Once played, the player's
  graph stays in that idle state, which blocks attacks, until something sends it home. Enderal ends its own idles with
  `Debug.SendAnimationEvent(ref, "IdleForceDefaultState")` (`_00E_MQ15_Functions`, `_00E_FS_NQ01_Functions`). The
  script now does the same `RecoverDelay` (0.8 s) after the impact.
  The power's effect lasts 6 s, so it outlives the script's waits even when slow time stretches them.
  **With a weapon drawn (2026-10-22, third attempt).** Even after the reset, the curator couldn't attack with a
  weapon drawn, and walked unarmed with the sword in hand. The stomp is an *unarmed* idle that Enderal only plays
  with weapons away. Sheathe → stomp → redraw was tried and reverted the same day as not fluid enough. The current
  approach uses **Hot Key Skill** (Nexus 86352, in the list). It adds an unconditioned wildcard transition on
  `CustomStartJ` to `1hm_behavior` (`#4872`: `condition null`, `FLAG_DISABLE_CONDITION`). That transition plays
  `HKS_CustomAnimJ.hkx` and returns to the drawn weapon by itself, and Pandora's output carries it. HKS ships its
  custom clips as placeholders meant for DAR/OAR replacement, and no list mod replaces slot J.
  `tools/04-install-stomp-anim.py` writes an OAR submod (priority 2100000000, no conditions) whose
  `HKS_CustomAnimJ.hkx` is Enderal's `animations\enderal\stomp.hkx`, into both Prophecy MO2 mods. The clip is SureAI's,
  so it is not committed. The script now chooses:
  - melee weapon or fists drawn (`GetEquippedItemType(1)` 0–6): `SendAnimationEvent("CustomStartJ")`, with no reset;
  - weapons away: the Enderal idle plus `IdleForceDefaultState`, as before;
  - bow, crossbow, staff or spell drawn: no animation.
  Unverified in game.
  **Gap Closer's records are retired:** shout `0x91A`, word `0x91B`, voice spell `0x91C` and effect `0x91D` are kept
  as unused names in `GLORY_RECORDS`, so later IDs don't move. Never reuse those IDs: older saves still point at
  them. Prophecy no longer overrides Enderal's dash idle `016980`.
- **Surrounded** (2026-10-22, curator; replaces Death or Glory on the same perk `0x93A`): "While 3 or more enemies are
  close to you, your Stamina regenerates 2 points per second." The perk grants ability `ZP_Prophecy_Surrounded_Ability
  0x93B`, whose Script effect `0x93C` runs `ZP_SurroundedEffect`. Once a second, in combat only, it counts living actors
  hostile to the player within `Radius` 400 (Seismic Stomp's radius, ~19 ft), using powerofthree's
  `FindAllReferencesOfFormType` as the stomp does. It stops counting at `MinEnemies` 3, then `RestoreActorValue
  ("Stamina", 2)`. Values are in `SURROUNDED` in `tools/01`. A save that had taken Death or Glory now has Surrounded,
  since it is the same perk. The EditorID stays `ZP_Prophecy_DeathorGlory` (`EDITORID`), so its art keeps that file name: the curator's Surrounded art (warrior ringed by four enemies,
  amber) replaced `ZP_Prophecy_DeathorGlory.png`/`.dds` on 2026-10-22. Needs Second Wind or Dragon
  Scale. Generated and deployed 2026-10-22 (previous plugin in `E:/Zenderal-backups/2026-10-22-prophecy-pre-surrounded/`).
  Unverified in game.
- **Death or Glory** (2026-10-22, curator's pick, **replaced by Surrounded the same day**) was perk `0x93A`:
  Ordinator's `ORD_Two60_DeathOrGlory_Perk_60 005474`, hand-built. It started at **75%** Health instead of 50%, and
  covered **every melee power attack**, because Ordinator's two-handed keyword tab was dropped. Six mutually
  exclusive 12.5% Health bands of `ModPowerAttackDamage`: <75% ×1.17, <62.5% ×1.33, <50% ×1.5, <37.5% ×1.67,
  <25% ×1.83, <12.5% ×2. The notes below on its ID allocation still apply to `0x93A`.
  **Its ID is allocated after the last Glory block** (`GLORY_LATE_NODES`), so no existing record moved: a rerun
  changed only the new perk and the menu quest's arrays (card #25, parents Second Wind / Dragon Scale).
  **Not in v2:** rerunning `src/ProphecyV2/tools/01-build-v2.py` numbers its per-perk info messages in tree
  order, so the new message took `0xC1A` and renumbered every sanctum ref after it. That run was reverted. v2
  needs the same append-last allocation before it can take a new perk. Thumbnail art still needed
  (`ProphecyPics/ZP_Prophecy_DeathorGlory.dds`). The menu now picks up new perks on existing saves (see *Menu arrays
  refresh on every cast* below). Unverified in game.
- **Menu arrays refresh on every cast (2026-10-22).** The menu's arrays (`Perks`, `Descriptions`, `Images`,
  `ParentA`/`B`, `PowerPerk`/`Spell`, `TreeStart`, `GiftPerk`/`Item`) were properties on `ZP_ProphecyInit 0x807`
  only. A running quest keeps the property values it started with in the save, so Death or Glory never showed on a
  save from before it was added; nothing refreshed them. `write_menu` now writes the same block on the power's
  effect `0x806` too. An ActiveMagicEffect instance is built from the plugin on every cast, so
  `ZP_ProphecyPowerEffect` passes those current arrays to `ZP_ProphecyMenu.Refresh(...)` before `RequestOpen`.
  `Refresh` assigns them over the quest's saved copies, unless the menu is already open. The quest keeps its own copy
  (what a new save starts with). Both copies come from one string in the generator, so they can't drift.
  `giftDone` is still indexed by gift position, so append new gifts last. v2 (paused) hasn't been rebuilt with this.
- **Second Wind** is an ability whose `ZP_SecondWindEffect.OnHit` restores 20 Stamina when the player is at or
  below 50% Health. Hits closer than 0.25 s count once, because frameworks fire several `OnHit` events per hit.
- **Dragon Scale** is an ability with Enderal's own `AbResistFire 024314`, `AbResistFrost 024315` and
  `AbResistShock 024318` effects at 25.
- **War Banner** is a lesser power whose effect lasts 15 s. It plants `CivilWarBanner02 060165` (the standard in
  Enderal's Nehrimese camps) 120 units ahead. Each second the player heals 20 if within 400 units, and every
  unbound hostile in range gets Triumvirate's Stave of Binding proc `423DA8` (`RemoteCast`; immobilize, stamina
  drain, 25% disarm, stagger). The proc is read with `GetFormFromFile`, so Triumvirate is not a master. The
  5-minute cooldown is Templar's pattern: the script-less effect `0x924`, checked with `HasMagicEffect`.
  **2026-10-22:** `CivilWarBanner02` turned out to be a bare frame: two uprights and a crossbar at z 387-399, with no
  cloth. Enderal places it bare too. The script now hangs Enderal's `_00E_BannerNehrimesian 0EAC23` (a skinned,
  wind-animated cloth, 90 wide, about 184 long, attached at its origin) at z 390 on the frame. It turns both 90° so
  the crossbar faces the player, where before it was edge-on. Casting sounds a war horn through
  `ZP_Prophecy_WarBanner_HornSound 0x927` and marker `0x928`, which play `Sound\FX\Zenderal\ZEN_WarBannerHorn_01.wav`.
  That file is the curator's own stock SFX, so it is not committed (as with BloodyCritSound). Install it with
  `python -I src/Prophecy/tools/03-install-sounds.py "<folder with the .wav files>"`, which copies every Prophecy sound
  into both Prophecy MO2 mods (see Power sounds below).
  **2026-10-22 (later):** in game the frame went missing while its cloth floated, and no goblin was bound. Checked:
  the frame mesh (PG Patcher's copy, identical to vanilla) does have both uprights from z 0 to 420; po3's
  `FindAllReferencesOfFormType` matches the ref **or** its base (62 finds ACHRs), 3D-loaded only; the proc's
  conditions (not flying, not `ActorTypeDragon`) pass for goblins. Unproven root cause. The fix makes the two
  suspects impossible: frame and cloth are now `PlaceAtMe`d from positioned XMarkers (`Game.GetForm(0x34)`), so
  nothing is moved or rotated while disabled, and a `finished` flag cleans up anything placed after the effect has
  ended (a late-placed cloth was the only way one could outlive its frame). `Debug.Trace` lines tagged
  `[ZP WarBanner]` log the placement Z and, per update, actors found / bound. Script only (no record change).
- The menu grants Gap Closer like the powers: `PowerSpell` is now `Form[]`, and a shout gets `TeachWord`,
  `UnlockWord` and `AddShout`. Tree sizes come from the quest's `TreeStart` array. The tree message `0x80D` is now
  generated from `TREES`.
- Both scripts need powerofthree's Papyrus Extender (`FindAllReferencesOfFormType`); compile with its `Source/scripts`
  on the import path. Thumbnails for the four Glory perks still need art. Unverified in game.

**Utility Droid (2026-10-23, curator; replaced Bear Traps).** Gadgets node 3 keeps its perk `0x81C`; its EditorID
follows the new name, `ZP_Prophecy_UtilityDroid`, so the card shows the curator's droid art
(`ProphecyPics/ZP_Prophecy_UtilityDroid.dds`, 2026-10-23). Ordinator's Bear Traps + Lockjaw stay as the node's seed and folded perk so the
copy closure, and every ID after it, is unchanged (still 254 records copied). The perk is rewritten in place
(`DROID_NODE` in `tools/01`): its entry points and perk-script fragment are dropped, and it grants the lesser power
`ZP_Prophecy_UtilityDroid_Power 0x944`, which the menu hands out like the other powers. The copied Bear Traps forge recipe
`0x90E` now needs `ZP_Prophecy_Never`, so traps can no longer be crafted.
- **The droid** `ZP_Prophecy_UtilityDroid 0x93F` is Enderal's own Starling Spider, re-purposed from the friendly
  Starship-cave spider `_00E_StarshipCaveHelpfulSpiderPatrol01 130AE8` (EGO's record, `DwarvenSpiderRace`, height 0.5).
  Changes: `PlayerFaction` instead of the Starship faction, SureAI's `_DefaultFollowPlayer 04B037` (Follow template,
  target PlayerRef) instead of its patrol package, Aggressive / Brave / helps friends and allies, no death item, and its
  ability `0x940`.
- **The power** (`0x944`/`0x945`, `ZP_UtilityDroidPowerEffect`): one droid at a time, remembered in FormList `0x946`.
  If it lives, the power calls it back to the player (free). Otherwise it deploys a new one: the first is free
  (global `0x947`, once per save), each later one costs 10 Spare Parts (`_00E_CraftingPieces 0773ED`), and with too few
  it says so. On deploy: Health = 100 + 10 × player level, `SetPlayerTeammate`.
- **The ability** (`0x940`/`0x941`, `ZP_UtilityDroidEffect`, on the droid): every 4 s it restores 15 Health to the player
  when they are within 640 units and hurt; every 6 s in combat it casts `ZP_Prophecy_UtilityDroid_Stagger 0x943` on
  each living actor hostile to the player within 300 units (PO3 `FindAllReferencesOfFormType`). That spell's effect
  `0x942` copies Enderal's `StaggerAttackFFContact 07809B` as a target-actor effect at magnitude 0.5 (Stunning Blows
  uses 0.25). No damage, no screen flash.
- Values are in `DROID` in `tools/01`. **Existing saves** that owned Bear Traps own Utility Droid now; if the power is
  missing, `player.addspell` the power `0x944` (load order index + `000944`). Previous plugin in
  `E:/Zenderal-backups/2026-10-23-prophecy-pre-utility-droid/`. Unverified in game.
- **Thrown (2026-10-23, curator: "throw the utility droid when deploying").** A new droid is thrown the way Enderal's
  Starling Dummy talent (Vagrant tree, `_00E_A2_StarlingdummyDetSC`) throws its spider. It is SureAI's chain copied
  record by record, each link re-pointed, allocated after Necromancy (`DROID_THROW_RECORDS`, `0x9AA–0x9AE`):
  1. The power `Cast`s `ZP_Prophecy_UtilityDroid_ThrowSpell` (from `_00E_A2_StarlingdummyProjSP 0F64A7`: Voice,
     Aimed) and plays SureAI's swing sound `WPNSwingUnarmedM 07BB93`.
  2. Its effect (`0F64A6`) fires the lobbed projectile (`0697F1`: `StarlingDummyProjectile.nif`, gravity 0.7,
     speed 1000).
  3. The projectile bursts in the landing explosion (`069836`, without its `MAGShockExpImod` flash).
  4. The burst places the invisible activator (`06983E`, without its self-destroying destructible data) whose
     `ZP_UtilityDroidPlacerScript` (`OnInit`) does what SureAI's `_00E_A2_StarlingdummySC` does: a dust burst
     `0EEFB1`, 0.3 s, `PlaceActorAtMe`. It then sets Health (100 + 10 × level), the teammate flag and
     `DroidList`, and deletes itself.

  **No navmesh snap (fixed the same day, curator: "the placement of where he spawns vs the throw is off").** The
  first build snapped the droid with PO3's `MoveToNearestNavmeshLocation`. PO3's PDB shows it works on the navmesh's
  `BSTArray<BSNavmeshVertex>`, i.e. it moves to the nearest navmesh **vertex**, meters off on open ground. SureAI's
  placer has no snap, and neither does ours now. Legion of the Damned still snaps, but there an offset doesn't
  matter: they spawn in an arc anyway.

  Spare Parts are paid before the throw. The call-back of a living droid is still a teleport. Previous plugin in
  `E:/Zenderal-backups/2026-10-23-prophecy-pre-droid-throw/`. Thrown in game (curator); landing spot fix unverified.
- **The heal shows (2026-10-23, curator: "an effect for when the droid heals me").** The droid now casts
  `ZP_Prophecy_UtilityDroid_Heal 0x9AF` at the player (`RemoteCast`, droid as source) instead of `RestoreActorValue`.
  The spell carries Enderal's heal-other effect `RestoreHealthFFActor 01CEA7` (`HealOther 012FD2`'s) at 15: the
  healing shimmer (`HitShader 012FD9` + `HitEffectArt 03F1B4`), no Arcane Fever. A droid already out when this
  shipped has no `HealSpell` (property added to a running effect), so the script looks it up by ID `0x9AF` and falls
  back to the bare heal. Previous plugin in `E:/Zenderal-backups/2026-10-23-prophecy-pre-droid-heal/`. Unverified
  in game.

**Clockwork Turret gives one turret (2026-10-22).** Ordinator's power deploys only while a turret item
`ZP_ORD_Smh_DwarvenAutocannon_Misc 0x884` is carried. Otherwise its fail effect `0x883` says "This power requires a
Clockwork Turret in your inventory." The script takes the item when it deploys and returns it after the 30 s,
unless the turret is destroyed. The only source is a forge recipe (`0x90F`) using five rare "Ancient Nation" scraps
(`0AEBF1`, `0C8866`, `0C8868`, `0C8872`, `0DB8A2`, each placed only 7-11 times in Vyn), so in practice the power never
worked. Now both menus hand out the item once per save when the perk is owned: the `GIFTS` table in `tools/01`
feeds the quest's `GiftPerk`/`GiftItem` arrays, and the script's `GiveGifts` runs on learning and on every open,
with a `giftDone` flag kept in the save. Opening Prophecy therefore never replaces a destroyed turret; crafting does.
The same pass fixed v2: its quest never granted the Gap Closer shout, because only v1's `write_menu` added it.

**Clockwork Turret aims itself (2026-10-23, curator: "target things on their own instead of where I aim").**
Ordinator's `ORD_DwarvenAutocannon_Script` was read from its bytecode with `tools/pexdis.py` (Champollion isn't
installed). Every `ORD_UpdateRate` (0.75 s), while the player is within `ORD_RemoteControlDist` 260 (12 ft), it moved
the empty-activator aim marker `ShootAim` along the **player's** heading and pitch (`GetAngleZ`/`GetAngleX`). It then
`RemoteCast` the shell spell `0x88F` from `ShootStart` (55 up from the turret) at that marker, so shots ran parallel
to the crosshair. Both turret effects, the main one `0x89E` and Overclock's Firing Line one `0x888` (`ORD_AngleDelta`
±60), now run `ZP_ClockworkTurretEffect` instead. `tools/01` swaps the script name on the copied records and keeps
every property. It is the same deploy, teardown, Electrobolt counter and spin-up (now only on shots), with its own
aim:
- **Target:** the player's combat target if valid and within `TargetRange` 2048 of the turret, else the nearest valid
  actor (PO3 `FindAllReferencesOfFormType`). Valid = alive, loaded, hostile to the player **and already in combat**,
  so a turret never starts a fight or breaks stealth. With no target it holds fire.
- **Each shot:** the turret turns to face the target (`SetAngle` on the activator), the aim marker goes to
  `AimHeight` 0.6 of the target's height, and the shell is `RemoteCast` at it, blamed on the player as before.

**The 12-foot rule is gone (curator, same day):** the turret fires wherever the player is. Ordinator's
`ORD_RemoteControlDist` check (fire only within 260 units unless Remote Control) was removed from the script; the
property stays because the copied records still set it. Ordinator's script also deleted only `ShootStart`;
`ShootAim` is cleaned up too now.
Built and deployed 2026-10-23 (previous plugin in `E:/Zenderal-backups/2026-10-23-prophecy-pre-turret-aim/`).
Unverified in game.

**Power sounds (2026-10-22, curator's files).** Ordinator ships Explosive Tripwire and Smokescreen silent. Each now
has an extra effect on its power whose one-line script `ZP_PlaySoundEffect` plays a sound marker, so Ordinator's
own scripts stay untouched. `POWER_SOUNDS` in `tools/01` lists them; append new ones last, because the IDs follow
the table's order.
- Tripwire: a hand ratchet as the player kneels, `0x929–0x92B`, `ZEN_TripwireRatchet_01.wav` (3.6 s).
- Smokescreen: a smoke-grenade burst, `0x92C–0x92E`, `ZEN_SmokescreenBurst_01.wav` (9.6 s).
- Clockwork Turret and War Banner already had sounds; Seismic Stomp's (`ZEN_SeismicStomp_01.wav`, 2.0 s) is its
  shockwave's own sound, not a `POWER_SOUNDS` entry.

**Smokescreen blinds undead, and no longer alerts (2026-10-26, curator: "still detected immediately with maxed
stealth").** How it works:
- Ordinator's `ORD_SmokeCurtain_Script` (disassembled) places the cloud.
- Every 0.5 s it `RemoteCast`s `Smoke Curtain` (`0x8A3`) from the cloud, blamed on the player.
- The pulse was Blindness 100 for 2 s (`0x8A6`) plus `ORD_Alert_Script` (`0x8A4`, `SetAlert(True)` on every hostile
  in 35 ft).

The engine honours the Blindness AV: Enderal's Arps carry `AbBlind 052FF3` through `AbFalmer 052FF4`, and EGO has
`XionBlindness`. A blind actor detects by sound only. Two faults, fixed by `fix_smoke_blind()`:
- **Undead were never blinded.** Both effects skipped `ActorTypeUndead` and `IsUndead`, which is most of Enderal's
  enemies. Those two conditions are removed; `ActorTypeDwarven` stays.
- **The pulse kept enemies on alert.** The alert effect is removed from the pulse, since it put everyone in the cloud
  on alert twice a second.

Unverified in game.

**Chaff (2026-10-26, curator).** Gadgets' 12th talent (`gad6`, perk `0xA6D`), a side talent off Smokescreen with no
effect of its own. `fix_smoke_blind` turns the blindness's automaton condition into "not `ActorTypeDwarven` OR the
player has Chaff", so with it the cloud also blinds Enderal's automatons (`DwarvenCenturionRace`, `DwarvenSphereRace`,
`DwarvenSpiderRace`). It is allocated after the Faith records through `LATE_NODES`, which the first allocation loop
skips, so no older ID moved; `weave_stats` allows a tree its late extras. On v3's wrench it is a spur off Smokescreen.
No card art yet. Unverified in game.

**Smokescreen turns you invisible (2026-10-23, curator: "make smokescreen also turn you invisible on cast").** The
power `ZP_ORD_Sne_SmokeCurtain_Spell 0x89F` gets a third effect after the cloud and the burst sound:
`InvisibillityFFSelf 01EA6A` for 10 s (`SMOKE_INVISIBLE` / `add_smoke_invisibility` in `tools/01`). That is the engine
invisibility with no script (attacking or activating ends it), as in EGO's `NPCInvisibility`. Enderal's Spectral Veil
effect `_00E_A1_InvisibilityME 067239` was rejected: its script **sets** base Sneak and SneakMod +75 and writes the
saved values back at the end. Overlapping the player's own Spectral Veil talent, the two restores could cross and leave
Sneak permanently changed. 10 s is Spectral Veil's rank I (10/16/22 s); KataHiddenPowers' "Smoke curtain" uses
7–16 s. The perk text says so. Ordinator's cloud script is untouched. Previous plugin in
`E:/Zenderal-backups/2026-10-23-prophecy-pre-smoke-invisibility/`. Unverified in game.

**Deadeye and Bleeding Shot sounds; Deadeye joins the gun hit spell (2026-10-23).** Deadeye (Ordinator's, gun 5)
applied its own on-hit spell `ZP_ORD_Arc_ArcheryOnHit_Spell 0x8B4` through `ApplyCombatHitSpell`, the entry point
Elemental Rounds and Bleeding Shot use for `ZP_Prophecy_GunHitSpell 0x910`. The engine applies one such spell per
hit, and Deadeye requires both gun perks, so one side always lost: either the Snipe markers never landed (every
shot a triple crit) or fire and bleed never fired. Which side lost was never checked in game. Now Deadeye's entry
points at `0x910` too, which carries `0x8B4`'s Snipe Blocker (1 s) and Snipe (10 s) in Ordinator's order. `0x8B4`'s
other 11 effects are all gated on `ZP_Prophecy_Never`; the record stays, unused. `write_gunhit` in `tools/01`.
Two sounds open the spell's effect list (before Snipe/bleed land, so their conditions see the target as it was):
- Deadeye's trigger, `0x948–0x94A`, `ZEN_DeadeyeShot_01.wav` (a rocket-launcher blast, 5.1 s), played **on the
  shooter** (`ZP_PlaySoundEffect` got `PlayOnCaster`). Gate: owns Deadeye, target lacks Snipe — Ordinator's
  Blocker only lands on a target that already has Snipe, so "no Snipe" is exactly the triple-crit case.
- Bleeding Shot's proc, `0x94B–0x94D`, `ZEN_BleedingShot_01.wav` (a bloody knife, 1.4 s), on the victim. Gate:
  owns Bleeding Shot, target not dead (the bleed's own condition), no bleed running (the bleed is `NoRecast`).
Both are extra effects: the weapon's own fire sound still plays. Unverified in game.

**Arcane Archery, the sixth tree (2026-10-23, curator's design).** Arcane Arsenal → No Distractions / Ice Shot →
Andrasta's Owl (was Send a Raven) → Arcane Echo (Ordinator's Lion's Arrow). Values in `ARC` in `tools/01`; records by
`write_arcane` and `arcane_hits`.
**Bows only** (curator, the same day): crossbows and Ordo's muskets carry `WeapTypeBow` too, so the tree checks
the item type instead: `GetEquippedItemType` Right == 7 (`BOW_IN_HAND`) on the four hit-spell effects (run on
PlayerRef) and on Lion's Arrow's in-combat effect. The scripts check the same: No Distractions on draw, Ice Shot
on cast (no bow → refuses, no cooldown), and the shatter (`Weapon.GetWeaponType() == 7`). The ice musket ball was
dropped; its two IDs (`0x962`/`0x963`) stay reserved and unwritten.
**Every record of this tree is allocated after all older blocks** (perks `0x94E–0x952`, `ARC_RECORDS`
`0x953–0x968`, Lion's Arrow's copied closure `0x969–0x97B`). Its Ordinator closure is a second pass over
`ARC_SEEDS` + Lion's Arrow, run after the older trees close over exactly their old seeds, so the regenerate
changed no older record but the gun hit spell and the menu arrays (diffed 2026-10-23).
- **Arcane Arsenal** (`arc1`): lesser power → message box (Fire / Frost / Lightning / None) → global
  `ZP_Prophecy_ArcaneArsenal_Element 0x956`. The gun hit spell carries `EnchFire/Frost/ShockDamageFFContact`
  (`04605A/B/C`) at 10, each gated on the perk and its global value 1/2/3. The perk adds its own
  `ApplyCombatHitSpell` entry → `0x910` (one hit spell per hit, see Deadeye).
- **No Distractions** (`arc2`): ability + `ZP_NoDistractionsEffect`. When a bow starts drawing, the script **casts
  the list's own Spell Ward (Rank II)**, `_10E_SpellSpellWard 085654`. "Starts drawing" means the graph events
  `bowAttackStart` / `BowDraw` / `bowDrawStart`, whichever arrives first. **SKSE's actor action 5 (Bow Draw) only
  fires once the bow is fully drawn** (curator, in game 2026-10-23); it is kept as a fallback. The animation-event
  registrations are renewed on `OnPlayerLoadGame` and on every ward start. Levin's Enderal Spell
  Ward Rework (`WardsShellVariantEnderal.esp`) wins that record and makes it a fire-and-forget shell ward: sphere
  art `000815`, start/hit/break/end explosions via `ANDR_ShellDispellScript`, 58 ward + 58 armor, 11 s. It skips the
  cast if the player already has a `MagicWard` effect, and only ever dispels a ward it cast itself.
  - **Removal:** Bow Release (6) or Sheathe Begin (9) dispels it at once. In between, the script polls the behavior
    graph every 0.25 s and dispels after two polls with neither `IsAttacking` nor `bBowDrawn`. Both are graph
    variables of the human `0_master` (read from the Pandora build).
  - **History:** the first build (same day) used a constant value-modifier ward with Ordinator's Mage Ward art. The
    curator saw the wrong ward, and lowering the bow without firing sends no actor action, so it stayed up until a
    20 s safety drop. Its records (`0x959–0x95B`) stay reserved and unwritten; a save that has that ability loses it
    on load. The Mage Ward art (`0x969`) is still copied so Lion's Arrow's IDs don't move.
- **Ice Shot** (`arc3`): bows only; 3 ice arrows; **no cooldown, costs 50 Magicka**, which the script takes since a
  lesser power has no cost of its own. **The arrows never expire.** Every ice-arrow hit deals 25 frost and freezes the
  target for 8 s; the next bow hit shatters it. Since 2026-10-23 it has three parts, none of which depends on a
  long-lived effect:
  - **The power** (`ZP_IceShotEffect`, effect 1 s): checks the bow and the Magicka, and remembers the equipped ammo
    in FormList `0x98E` (via `13E955`, unless it is already ice arrows). It takes any ice arrows still held, then adds
    and equips exactly 3 and sets global `0x991` (shots left) to 3.
  - **The watcher** (`ZP_Prophecy_IceShot_Watcher 0x987`, an ability from the perk, `ZP_IceShotWatcherEffect`):
    `OnPlayerBowShot` with an ice arrow records real time in global `0x98C`, counts pending shots in `0x98D` (reset
    after a 3 s window) and counts `0x991` down. At zero (or none held) it takes any ice arrows left and re-equips the
    remembered ammo 1 s later.
    - **The first counting build ended the cast after one shot:** the watcher was already running in the save, so
      its new `Remaining` property stayed `None` (read as 0). It now falls back to
      `GetFormFromFile(0x991, "Zenderal - Prophecy.esp")` (see [papyrus.md](../workspace/papyrus.md#gotchas)).
    - **Why it counts its own shots (in game, 2026-10-23):** 15–17 ice arrows had piled up from earlier builds that
      no longer took leftovers back. During one fight the count stayed at 15 shot after shot: fired arrows were put
      back by something. So "run out" never happened and the old ammo never came back.
  - **The hit** (`ZP_Prophecy_IceShot_HitTrigger 0x989` on the gun hit spell, gated on the perk + a bow; the perk
    has its own `ApplyCombatHitSpell` → `0x910`): if a pending ice shot is within 3 s and the target is not
    frozen, it casts `ZP_Prophecy_IceShot_FreezeSpell 0x98A` on the target. That spell is target-delivered: 25 frost
    (`0x98B`, a TargetActor copy of `EnchFrostDamageFFContact 04605B`) plus `ZP_IceShotFreezeEffect` for 8 s.
  - **The burst:** the ice arrows still explode in Enderal's ice-spike burst (`MAGIceSpikeVolleyExplosion 0D6C63`,
    no image space), now visuals only.
  - **The projectile must be an exploding *Arrow*** (Flame Shot ranks 2/3's `_00E_A1_FireArrow_ProjectileL02
    0670DA` shape: `Type: Arrow`, `Explosion`, `DisableCombatAimCorrection`). The first build copied rank 1's
    `Type: Missile`, whose hits never reach `ApplyCombatHitSpell`. Once the trigger replaced the explosion's
    enchantment, nothing froze (in game, 2026-10-23).
  - The watcher and the trigger `Debug.Trace` each ice shot and each hit (`ZP_IceShot watcher:` /
    `ZP_IceShot hit on`) in `Papyrus.0.log`.
  - **The freeze is SureAI's, done directly by `ZP_IceShotFreezeEffect`:** AI off and Paralysis 1 (as
    `_00E_FrozenMEScript`), the ice-form shader `FrostIceFormFXShader02 0DC20E` (the one Enderal's
    `_00E_Frozen_ME` shows), and Arctic Wind's freeze sound `10A6A0`; it thaws at the end. `MagicNoFreeze 0EEE66`
    targets and player teammates are skipped.
  - **The shatter:** after 0.5 s, the player's next bow hit (`OnHit` on the frozen target, weapon type 7) runs
    SureAI's `ShatterEnemy` (kill, shatter explosions, ice pile), copied. Essential actors never shatter.
    - Its two explosions are copies without screen blur: `0x98F` (Forgotten Stories' `_00E_FrostShatteringExplosion
      066897`) and `0x990` (`_00E_FrostShatteringExplosion02 066895`). Both originals carry image-space modifier
      `04408A` at `ISRadius` 1024 (curator 2026-10-23: "remove the blur").
    - Enderal's own Arctic Wind shatter keeps the originals. The ice burst on impact never had a modifier.
    - **Only the frost burst `0x990` is placed** (curator, same day: "giant logs fly out"). It is a particle-only
      `ExplosionFrost01.nif` with Force 0 (was 128), so nearby clutter stays put. SureAI's other two shatter
      explosions carry physics debris: Forgotten Stories' `IceShatterExplosionTest.nif` (6 rigid-body chunks
      textured with an invisible test texture and a Dwarven arrow's maps, the likely "logs") and the NPC/draugr
      ice gore `033468` (14 meat chunks, force 240 over 512 units). The copy `0x98F` is still written, unused.
  - **History (all 2026-10-23, in game):**
    - It first followed Flame Shot (`_00E_A1_FireArrowSC`): 14 s, a 110 s cooldown, a 35% freeze roll with Arctic
      Wind's level cap, delivered by the explosion's enchantment. Nothing froze.
    - The arrows then vanished after a short time even with a day-long effect. The effect ended early for an
      unknown reason, and its cleanup took the leftovers.
    - Bears were never frozen: a 100-unit explosion misses big creatures, measured from where the game takes the
      actor's position.
    - Records `0x95E`/`0x95F` (cooldown) and `0x965` (enchantment) stay reserved and unwritten.
    - **A save that took Ice Shot before this build** may need the perk re-added to receive the new watcher ability.
- **Send a Raven** (`arc4`): a script effect on the gun hit spell (30 s, living target, not already on it) places
  Triumvirate's Call Raven creature (`TVR_Primal_Actor_CallRaven 14F4E2`, `GetFormFromFile`, no master) at the
  player. The raven joins `PlayerFaction`, becomes a teammate and `StartCombat`s the target; its own attacks
  blind. One raven at a time (FormList `0x968`). It leaves when the effect ends (target dead or 30 s).
  - **In game the first build's raven never moved and died at once.** Triumvirate - Enderal Patch already repairs
    the race, which pointed at Dawnguard's movement type `0051FC` (Enderal's Dawnguard.esm is a stub); the
    winning race uses `ChaurusDefault_MT 064113`, and the Dawnguard flyer graph ships in SSE's
    `Skyrim - Animations.bsa`. A placed raven still never moved. Why is unknown; Triumvirate's own Call Raven
    summon was not tested. So a script flies it: every 0.5 s, if the raven is farther than 180 units from the
    target, it `TranslateTo`s a point at head height in front of the target (900 u/s); otherwise it
    `StopTranslation`s and `StartCombat`s.
  - **Second build (same day): the raven vanished after ~2 s, and the curator wants it to stay until killed.**
    The cause was the spawn effect's own condition "target lacks this effect". A hit-spell effect's conditions
    are re-checked while it runs, so once the effect landed, that check turned false and ended it. Its
    `OnEffectFinish` deleted the raven. **Do not put a "not already applied" condition on a lasting effect**
    (or tie anything to its lifetime).
  - **Now:** the spawn effect (`0x967`, 1 s, no self-check) only spawns the raven or **redirects** the live one
    (`StartCombat` on the new target, fetched first if it was left behind or unloaded). The raven gets
    `ZP_Prophecy_SendRaven_RavenAbility 0x97D`, effect `0x97E` (`NoDeathDispel`), script `ZP_RavenBrainEffect`.
    That script does the flying above: it picks its own combat target, else the player's, and with no fight it
    keeps behind the player's shoulder. It moves the raven to the player when more than 3000 units away or in
    another cell while the player is indoors. On `OnDying` it empties the FormList and removes the body after 3 s.
  - **Health and lifetime:** no ghost any more. Health is 50 + 5 × player level (`SetActorValue`, from a
    5-Health base). It stays until killed.
  - **Third build (same day): the raven cawed nonstop.** The raven's only NPC sound was
    `TVR_Primal_Descriptor_Crow_Conscious 000853`, a **looping** crow call that plays for as long as it is
    conscious. An actor's own sounds can't be switched off from a script. So Send a Raven now places its own
    raven: `ZP_Prophecy_SendRaven_Raven 0x97F`, Triumvirate's record as Triumvirate - Enderal Patch wins it
    (serialized into `reference/mods/TriumvirateEnderalPatch`), with no `Sound` block. The spawn script plays
    one caw: `ZP_Prophecy_SendRaven_CawSound 0x980`, a non-looping descriptor on the same `crowvoice.wav`, via
    marker `0x981`. This made **Triumvirate a master of Prophecy**; the spawn script no longer uses
    `GetFormFromFile`.
  - **The curator still heard constant cawing**: the save still had the previous build's raven (Triumvirate's
    record). Ravens stay until killed, and a hit only redirects the live one. So the spawn script now replaces a
    live raven whose base isn't `0x97F`. That **still cawed**: a base-record check is not trustworthy for a
    level-scaled creature, and old ravens that had dropped out of the FormList kept following the player through
    their brain. See the stamp below.
- **Andrasta's Owl** (`arc4`, was Send a Raven, then Send an Owl, curator 2026-10-23; EditorID kept as `ZP_Prophecy_SendaRaven`,
  scripts keep their raven names). The curator installed **Mihail's Barn Owls** (`mihailowl.esp`, Enderal Barn Owls'
  1.71 light copy wins). That mod adds **no creature**: only an animated Activator (`mihailowl_npc 000800`) placed
  as scenery, whose `owl1.nif` flies a baked path (`NiPathInterpolator`). Its other mesh, `owl1go.nif`, carries a
  `ChaurusFlyerSpine1` bone and its own wing animation, i.e. it is made to be worn on the chaurus-flyer skeleton.
  - **The bird:** NPC `0x97F` (now `ZP_Prophecy_SendOwl_Owl`, "Barn Owl") is still Triumvirate's raven creature
    (race `00084F`, chaurus-flyer skeleton and graph, no sound types). It wears `ZP_Prophecy_SendOwl_Skin 0x982`
    / addon `0x983`, Triumvirate's crow skin with the model swapped.
  - **`owl1go.nif` as the model drew nothing (in game, same day: spawn sound, no owl).** It is skinned to the owl's
    *own* bones (`BoneMain`, `BoneL/RWing01/02` under the vanilla bird-of-prey rig), which the raven skeleton lacks.
    So **`tools/05-build-owl-mesh.py` re-rigs it**:
    - It poses each owl vertex in the owl's own displayed bind. That is the rig's 0.5 scale times the skin's 0.667
      scale and ~77° pitch: a horizontal owl facing +Y, 95 units across.
    - It scales that ×1.5 to the crow's 143-unit wingspan and puts the shoulders on the midpoint of the crow's two
      top-wing bones.
    - It re-weights `BoneMain` → `ChaurusFlyerNeck` (what the crow's body follows) and the wings →
      `ChaurusFlyerTopWingLeft/Right`, keeping each vertex's body/wing blend.
    - It binds with the crow mesh's (`basecrow.nif`) own skin-to-bone transforms and its partition, writes SE
      (`BSTriShape` + `BSDismemberSkinInstance`), and keeps the owl's shaders, textures (Mihail's, loose) and alpha.
    - Output: `meshes\Zenderal\Prophecy\BarnOwl.nif` in the Prophecy MO2 mod. It is not committed (built from two
      mods' assets); rerun after either mod updates.
    - The look in flight (size, seating on the body, wing flaps) is **unverified in game**.
  - **Renamed "Andrasta's Owl"** (curator, same day); EditorIDs and script names unchanged.
  - **Immune to all friendly fire** (curator, same day). The owl's perk `0x984` adds `ModIncomingDamage` ×0 and
    `ModIncomingSpellMagnitude` ×0 when tab 1 (attacker/caster) is the player (`GetIsID 000007`), a
    `GetPlayerTeammate` or in `PlayerFaction`. Triumvirate's `181F3A` used the same entry-point shape on this
    creature. Script effects ignore magnitude, so the Ice Shot freeze and the owl's spawn/redirect effect both
    skip `IsPlayerTeammate()` targets (no freezing or shattering the owl or a follower, no sending the owl at them).
    The Papyrus name is `IsPlayerTeammate`, but the condition function is `GetPlayerTeammate`; the wrong name gave
    Spriggit a NullReferenceException.
  - **The player's arrows pass through it** (curator, same day). The friendly-fire perk zeroed the damage, but the
    owl still stopped the arrows: it hovers in front of the target's head, in the line of fire. `ZP_RavenBrainEffect`
    `SetGhost`s it while the player has `bBowDrawn` or `IsAttacking`, and for 3 polls (1.5 s) after, enough for an
    arrow in flight. It is solid again otherwise, so enemies can still kill it. Only script variables were added,
    so a running brain in a save picks this up.
  - **+2 Magicka per second while the owl lives** (curator, same day): `ZP_RavenBrainEffect` restores
    `PlayerMagickaPerSecond` (`ARC['OwlRegen']`) × its 0.5 s poll to the player on every update. The regen is a
    script tick, not an ability, so it stops the moment the owl dies or is removed.
  - **Its strikes drain Magicka to the player:** perk `0x984` (in place of Triumvirate's
    `TVR_Primal_Perk_ExtraDamageTaken 181F3A`, which made it take extra damage) has `ApplyCombatHitSpell` → spell
    `0x985` → effect `0x986`, `ZP_OwlAbsorbEffect`. That drains up to 10 Magicka (`ARC['OwlDrain']`) and restores
    it to the player; a plain Absorb would feed the owl. The hit shows `AbsorbMagickaConstant`'s shader `057C67`.
  - **Spawn sound:** the curator's `ZEN_OwlSpawn_01.wav` (`tools/03`) through descriptor `0x980` / marker
    `0x981`, the old caw IDs. The bird has no sound types, so it is silent after that.
  - **The stamp:** the spawn script sets actor value `Variable08` = 7 on every bird it places. A bird without it
    is an older build's raven: the spawn script replaces it, and `ZP_RavenBrainEffect` deletes the bird it runs
    on, which also clears strays no longer in the FormList.
- **Arcane Echo** (`arc5`): Ordinator's Lion's Arrow (`ORD_Arc90_LionsArrow_Perk_90_OrdASISExclude 010258`) copied
  with its own description, scripts and records, **renamed Arcane Echo** (curator 2026-10-23). The rename is via
  `LORE` in `tools/01`, on every display string (perk, power, effects, description); the perk's EditorID stays
  `ZP_Prophecy_LionsArrow` (`EDITORID`, the card's file name). Its learn power needs a true dual cast, and in
  Enderal that needs a class dual-cast talent (Elementalist, Thaumaturge, Practiced Ritualist). The exclusion list
  loses four vanilla spells Enderal lacks (`SUBST`).
- Built, round-tripped through Spriggit (only defaults dropped) and deployed 2026-10-23. The previous plugin is
  in `E:/Zenderal-backups/2026-10-23-prophecy-pre-arcane-archery/`. **Card art** (the curator's
  `outputs/trait-icons/ZP_Prophecy_{ArcaneArsenal,NoDistractions,IceShot,SendaRaven,LionsArrow}.png`) was converted
  by `tools/02` and installed the same day. The SendaRaven card now shows the curator's barn owl (the raven art is
  kept as `old-ZP_Prophecy_SendaRaven-raven.png`, outside the converter's `ZP_Prophecy_*` pattern).

**Necromancy, the seventh tree (2026-10-23, curator's design; the numbers are ours).** Corpse Fever → Dark Effigy /
A Willing Sacrifice → The Dead Don't Forget (needs A Willing Sacrifice only: it only improves that power) → Legion of
the Damned. All hand-built: values in `NEC`, records by `write_necro`, allocated after everything else (perks
`0x992–0x996`, `NEC_RECORDS` `0x997–0x9A9`; next free `0x9AA`). The regenerate changed no older record, only the
three menu records (diffed). Card EditorIDs follow the curator's file names (`EDITORID`: `ZP_Prophecy_WillingSacrifice`,
`_DeadDontForget`, `_LegionDamned`).
- **Corpse Fever** (`nec1`): four `ModCommandedActorLimit` Add +1 entries (Priority 100), at `LastFlattered` ≤ −25 / −50
  / −75 / −100 (Arcane Fever is stored negated). **The engine has one summon limit for every kind of summon**, so it
  counts all summons, not only undead ones (the curator asked for undead). A per-spell tab condition on the limit
  might restrict it, but which tab that entry point's second condition tab is was not verified, so it was not built.
- **Dark Effigy** (`nec2`): a **spell**, granted by the menu's `grants` (an `AddPerk` never teaches a spell).
  Summon Ancestor's spell (EGO's `11C383`) copied and turned on the caster: 100 Magicka (manual cost, its half-cost
  perk), 1.5 s charge, either hand, Entropy (Conjuration) with Summon Ancestor's casting art and sounds.
  `ZP_DarkEffigyEffect` plants `HagravenDeadGoatPole01 0ACAFD` (×1.4) in front of the player for 60 s, with the
  sacrifice's eldritch burst. Once a second, within 512 units: every ally (the player, teammates, actors the player
  commands, Legion skeletons) gets `ZP_Prophecy_DarkEffigy_Armor` (+250 `DamageResist` for 2 s, so it lapses soon
  after leaving). The player's own undead also heal 2 Health: keyword `ActorTypeUndead`, or a raised corpse (every
  reanimate effect carries `MagicSummonUndead 02482B`). Since 2026-10-26 (curator) the player heals the same 2 per
  second within range (no fever). Recasting replaces the totem.
- **A Willing Sacrifice** (`nec3`): lesser power, 15 s cooldown (War Banner's pattern). Every actor the player commands
  (PO3 `GetCommandedActors`) and every Legion skeleton explodes, one after another (0.35 s apart). **Damage = half the
  summon's base Health** to every living actor hostile to the player within 300 units (14 ft; Enderal's Fireball is
  12 ft). That is SureAI's own Corpse Explosion rule (`_00E_FS_Entropy_CorpseExplosionSC`: half the victim's base Health,
  set with `SetNthEffectMagnitude`). The damage is the spell `ZP_Prophecy_WillingSacrifice_Blast`, set per summon and
  `RemoteCast` blamed on the player: plain Health damage, resisted by magic resistance, carrying `BlameSpellKeyword`,
  so kills pay EP (`_00E_EPOnDeath`). The look is Corpse Explosion's: FS's shader `02F280` and its sound `02F2E3`,
  both read with `GetFormFromFile` so the plugin does not master FS. The burst is a copy of
  `_00E_FS_Entropy_CorpseExplosionEXP 02F27D` without its damage enchantment, its screen effect and its push.
  It has no remains pile: an ash pile takes the disintegrated actor's inventory, which would leave summon and Legion
  gear to loot. The first build attached FS's `02F3D4`.
  Summons die by their own hand (`Kill(self)`), so a raised enemy pays no second EP.
  Rough scale: a Summon Ancestor (~150 Health) blasts for ~75, about a Fireball (Rank II) at 45 and Rank III at 63; a
  Legion skeleton at level 30 (320 Health) for 160 each.
- **The Dead Don't Forget** (`nec4`): no effects of its own. A Willing Sacrifice's script checks the perk and
  restores 50 Magicka per enemy hit, each enemy counted once per sacrifice.
- **Legion of the Damned** (`nec5`): lesser power. **Since 2026-10-24 the fever goes through Zen Traits**, as every
  fever change in this list does ([`TraitsRework.md`](TraitsRework.md)). The script reads
  `ZenTraits_ArcaneFeverScript` (`Zen Traits.esp 0x802`, the quest `ArcaneFever.ModFever` uses). It prices the cost
  with `ApplyIncreaseFeverMods(-50)` (Mental Expert ×0.67, Night Fever by day, Purified Blood, Arcane Addict) and charges
  it with `ModFever(-50, True)`, which applies the same math and shows Enderal's message, sound and screen effect. It
  compiles against Zen Traits' source in `Zenderal - Patch Collection/Source/Scripts`. Without Zen Traits it falls back
  to the first build's way, which is Enderal's own: `ModAV("LastFlattered", -cost)` with Mental Expert only, then
  `_00E_Player_sArcaneFeverIncreased` and `_00E_ArkanistenfieberIMOD`. 2.1's `_00E_ArkanistenfieberBlitzheilungSCN`
  no longer changes the value itself, so the fever effect `11A4B6` was never trusted for a cost this large. The power
  refuses if the real cost would reach 100.
  It then kills the old Legion and places six copies of base Enderal's player skeleton `11C391` (Skyrim.esm's version:
  EGO's copy adds FS/EGO forms) in an arc 160 units in front of the player, each snapped to the navmesh (PO3) and shown
  with the summon portal `DA07SummonTargetFX 107D96` (the VFX of art `SummonTargetFX 03F811`) and sound `14C018`. The
  first build pointed the `VisualEffect` property at the ARTO itself, so it never bound and the portal never played. The copies, `0x9A4`–`0x9A6`:
  - **Warrior:** its skeleton weapon list.
  - **Archer:** Oak Bow + 99 Old Rune Arrows, on `csDraugrMissile` (LostOneArcherAmmo's fixes).
  - **Mage:** the weapon list + the Lost Mage's fire bolt `048006`, on `csDraugrMagic`, with 200 Magicka.

  All are level × 1.0 of the player, in the player's faction and teammates, on `_DefaultFollowPlayer`, with no bone
  meal and no Summonable flag. Health is 80 + 8 per level. They are placed actors, so they do not use summon slots.
  Their ability `ZP_LegionSkeletonEffect` stamps a game-time expiry into `Variable07` (300 real seconds at the current
  TimeScale, so reloads don't reset it) and kills them when it passes. On death they leave the list and fade out after
  3 s; deleting the corpse takes its gear with it. A weapon an actor drops as it dies can still be picked up.
  **Crash, fixed 2026-10-23:** the ability first called `UnequipAll` and `RemoveAllItems` in `OnDying`. Sacrificing a
  Legion Archer crashed the game in `UnequipAllVisitor`, because the archer was being disintegrated (Crash Logger
  `crash-2026-10-23-21-47-34.log`, `SkyrimSE.exe+0164668`). No inventory call is made on a dying actor now.
- Built, round-tripped through Spriggit (only defaults and ordering differ) and the four scripts compiled 2026-10-23.
  The `.pex` and the curator's five cards (converted by `tools/02`) are installed. The esp was deployed after the game
  closed (a running game holds it open: `cp` fails with "Device or resource busy"). The previous plugin is in
  `E:/Zenderal-backups/2026-10-23-prophecy-pre-necromancy/`.
  The menu now has 8 tree buttons + Cancel. **In game (curator, 2026-10-23): everything worked except A Willing
  Sacrifice, which crashed (above).** The fix is built and deployed, and is not yet retested in game. Dark Effigy also
  stopped calling `UnregisterForUpdate` in `OnEffectFinish`, where it only logged an error.

All the `.wav`s, the War Banner horn included, are stock SFX the curator supplied: loose under
`Sound\FX\Zenderal\` and not committed. `tools/03-install-sounds.py <folder>` copies them into both Prophecy
MO2 mods, converting any file that isn't 16-bit / 44.1 kHz PCM with BloodyCritSound's converter. The smoke
grenade was 24-bit / 48 kHz.

**Point-gained flourish (2026-10-25, curator's request).** Each Prophecy point now arrives with a sound and a
visual before its prompt. The sound is the curator's holy spell cast (`ZP_Prophecy_PointGainedSound 0x9B0`, marker
`0x9B1`, `ZEN_ProphecyPoint_01.wav`; not committed, `tools/03`). The visual is Enderal's own
`_00E_Class_MemoryAbsorbFXS 0ACDC5`: the memory wisps `_00E_Class_PerkScript` plays when a talent is learned in the
meditation space, shown for 2.5 s. Its dragon-absorb streams (they need a source ref) and its screen flash are left
out. `AwardPoints` looks both up with `GetFormFromFile`, because a running quest keeps the property values it
started with in a save. Both play before `Debug.MessageBox`, because the box pauses the game. Unverified in game.

## History
### 2026-10-08 prototype

**PROTOTYPE — not an ESL yet, on purpose.** A separate perk tree for Ordinator-derived perks (see [`arch-docs/ordinator/`](../ordinator/)), opened by the **Prophecy** power and drawn by **Custom Skills Framework** on the engine's vanilla StatsMenu. `800` `ZP_ProphecyLevel`, `801` `ZP_ProphecyRatio`, `802` `ZP_ProphecyPoints` (the tree's own currency; CSF spends it), `803` `ZP_ProphecyShowMenu`, `804` test perk *First Omen*, `805` power `ZP_ProphecyPower`, `806` its script MGEF, `807` StartGameEnabled+RunOnce quest that `AddSpell`s the power. The power just sets `ZP_ProphecyShowMenu` to 1 — CSF polls that global every frame and opens the tree, so no CSF Papyrus native is needed and it works with either CSF build. Config is the CSF v2 / meh321 INI format (`Data/NetScriptFramework/Plugins/CustomSkill.<id>.config.txt`). **Needs a 1.5.97 CSF**: current Exit-9B CSF (3.x) is AE-only (address IDs like `410201`); the candidates are meh321's original NetScriptFramework CSF (NSF is already in the list) or CSF v2.0.2's SE build from Nexus 41780 old files. CSF v2 renders through the beast-skill (vampire) path and defaults to `DLC01/Interface/INTVampirePerkSkydome.nif`, which Enderal ships in `Skyrim - Meshes0.bsa`. Kept non-ESL until CSF is proven to resolve FormIDs in a light plugin (one variable per test). Built 2026-10-08, round-trips identically; **not run in game**.
