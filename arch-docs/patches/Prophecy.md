# Prophecy

- **Source:** `src/Prophecy/` — **generated** by `tools/01-build-trees.py`; never hand-edit `ProphecyESP/` beyond `0x800–0x809`
- **Ships:** `Zenderal - Prophecy.esp` + 35 scripts + Ordinator/Subclasses meshes and textures
- **FormID block:** `0x800–0x912` (still **non-ESL**, deliberately — see below)
- **Needs:** nothing beyond Enderal (UIExtensions list menu ships with Enderal). Custom Skills Framework is NOT used

## What it does (2026-10-21)

The **Prophecy** power (granted once per save by `ZP_ProphecyInit`) awards Prophecy points — **1 per 5 player levels,
max 20**, counted up on every cast like Subclasses of Skyrim's `dar_sostreescript` (Enderal's leveling calls
`Game.SetPlayerLevel`, so `GetLevel()` is the Enderal level) — then sets `ZP_ProphecyShowMenu` and CSF opens one menu
with **four trees of five perks**: root → two branches → merge (needs either branch) → capstone.

| Tree | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Faith | Descending Light (ORD) | Respite (ORD) | Edgewalker (ORD) | Healing Presence (SoS, +1 fever/tick) | Templar (SoS, +4 fever) |
| Gunslinger | Quick Reload (ORD Quick Shot) | Elemental Rounds (new) | Bleeding Shot (SoS Monk's bleed) | Run and Gun (ORD Ranger) | Deadeye (ORD Snipe) |
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
`tools/01` clears only `assets/meshes` and `assets/textures`, so it no longer deletes these.

**Card menu amendments (2026-10-21, curator's feedback).** B612's Random button is hidden
(`_root.Traits_mc.RandomBtn_mc`, set again 0.25 s after `Show`). Card titles carry only "- Learned"; the
"Requires X" text was unreadable. Picking a locked card now shows a message box ("X: learn Y first.") and reopens
the tree. Tripwire is renamed **Explosive Tripwire** via `RENAME` in `tools/01`; `EDITORID` keeps the EditorID
`ZP_Prophecy_Tripwire`, so the art path is unchanged. The plain "Tripwire" string showed up lowercase because Papyrus
pools strings case-insensitively and vanilla has a `tripwire` script.

**Powers are granted with `AddSpell` (2026-10-21).** Adding a perk from a script with `AddPerk` did not hand out its
`PerkAbilityEffect` when that spell is a Power or LesserPower: Explosive Tripwire was learned, but no power appeared.
`tools/01`'s `perk_powers()` finds the affected perks and writes them into the quest's `PowerPerk` and `PowerSpell`
arrays. Today these are Explosive Tripwire, Smokescreen and Clockwork Turret. The menu `AddSpell`s each power when its
perk is learned. `RepairPowers()` runs every time Prophecy opens, so perks learned before this fix get their power
back. v2's `ZP_ProphecySanctum` does the same (it repairs on Enter). Unverified in game.

**Glory tree (2026-10-21, curator's design).** A fifth tree of 5 perks: Seismic Stomp (root), then Second Wind or
Dragon Scale, then War Banner or Death or Glory (each needs either). Its records sit at `0x916–0x924`, after every other block, so adding it
renumbered nothing in existing saves. All of it is built by `write_glory` in `tools/01`.
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

**Clockwork Turret gives one turret (2026-10-22).** Ordinator's power deploys only while a turret item
`ZP_ORD_Smh_DwarvenAutocannon_Misc 0x884` is carried. Otherwise its fail effect `0x883` says "This power requires a
Clockwork Turret in your inventory." The script takes the item when it deploys and returns it after the 30 s,
unless the turret is destroyed. The only source is a forge recipe (`0x90F`) using five rare "Ancient Nation" scraps
(`0AEBF1`, `0C8866`, `0C8868`, `0C8872`, `0DB8A2`, each placed only 7-11 times in Vyn), so in practice the power never
worked. Now both menus hand out the item once per save when the perk is owned: the `GIFTS` table in `tools/01`
feeds the quest's `GiftPerk`/`GiftItem` arrays, and the script's `GiveGifts` runs on learning and on every open,
with a `giftDone` flag kept in the save. Opening Prophecy therefore never replaces a destroyed turret; crafting does.
The same pass fixed v2: its quest never granted the Gap Closer shout, because only v1's `write_menu` added it.

**Power sounds (2026-10-22, curator's files).** Ordinator ships Explosive Tripwire and Smokescreen silent. Each now
has an extra effect on its power whose one-line script `ZP_PlaySoundEffect` plays a sound marker, so Ordinator's
own scripts stay untouched. `POWER_SOUNDS` in `tools/01` lists them; append new ones last, because the IDs follow
the table's order.
- Tripwire: a hand ratchet as the player kneels, `0x929–0x92B`, `ZEN_TripwireRatchet_01.wav` (3.6 s).
- Smokescreen: a smoke-grenade burst, `0x92C–0x92E`, `ZEN_SmokescreenBurst_01.wav` (9.6 s).
- Clockwork Turret and War Banner already had sounds; Seismic Stomp's (`ZEN_SeismicStomp_01.wav`, 2.0 s) is its
  shockwave's own sound, not a `POWER_SOUNDS` entry.

All three `.wav`s, the War Banner horn included, are stock SFX the curator supplied: loose under
`Sound\FX\Zenderal\` and not committed. `tools/03-install-sounds.py <folder>` copies them into both Prophecy
MO2 mods, converting any file that isn't 16-bit / 44.1 kHz PCM with BloodyCritSound's converter. The smoke
grenade was 24-bit / 48 kHz.

## History
### 2026-10-08 prototype

**PROTOTYPE — not an ESL yet, on purpose.** A separate perk tree for Ordinator-derived perks (see [`arch-docs/ordinator/`](../ordinator/)), opened by the **Prophecy** power and drawn by **Custom Skills Framework** on the engine's vanilla StatsMenu. `800` `ZP_ProphecyLevel`, `801` `ZP_ProphecyRatio`, `802` `ZP_ProphecyPoints` (the tree's own currency; CSF spends it), `803` `ZP_ProphecyShowMenu`, `804` test perk *First Omen*, `805` power `ZP_ProphecyPower`, `806` its script MGEF, `807` StartGameEnabled+RunOnce quest that `AddSpell`s the power. The power just sets `ZP_ProphecyShowMenu` to 1 — CSF polls that global every frame and opens the tree, so no CSF Papyrus native is needed and it works with either CSF build. Config is the CSF v2 / meh321 INI format (`Data/NetScriptFramework/Plugins/CustomSkill.<id>.config.txt`). **Needs a 1.5.97 CSF**: current Exit-9B CSF (3.x) is AE-only (address IDs like `410201`); the candidates are meh321's original NetScriptFramework CSF (NSF is already in the list) or CSF v2.0.2's SE build from Nexus 41780 old files. CSF v2 renders through the beast-skill (vampire) path and defaults to `DLC01/Interface/INTVampirePerkSkydome.nif`, which Enderal ships in `Skyrim - Meshes0.bsa`. Kept non-ESL until CSF is proven to resolve FormIDs in a light plugin (one variable per test). Built 2026-10-08, round-trips identically; **not run in game**.
