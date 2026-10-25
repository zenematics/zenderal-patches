# LostOneArcherAmmo

- **Source:** `src/LostOneArcherAmmo/`
- **Ships:** `Zenderal - Lost One Archer Ammo.esp` (ESL, HEDR 1.7, overrides only)
- **FormID block:** none
- **Pillar:** bug fix

## Symptom

Lost One (and skeleton) archers fired one arrow, then backed off and stared at the player, at any range (reported 2026-10-22).

## Cause **[verified from records 2026-10-22]**

- EGO adds the `NPCsUseAmmo` flag to the archers' bows, `_02E_16Runenbogen 07C983` and `_02E_19_SilverSteelBow 07C99D`
  (base Enderal has neither), so these NPCs spend the arrow stack they have equipped.
- `Lost Ones Revised - EGO Patch.esp`, which wins these NPCs, adds **one Old Iron Arrow `0028B0` ×1** next to the real
  stack (30 Old Rune Arrows `08659D`, or 20–35 Rune Arrows `08659E`). An archer that equips the lone arrow fires once and
  runs dry; NPCs do not re-pick ammo mid-combat, so it stays hostile with nothing to shoot.

Ruled out on the way: the arrow records (our Pretty Armory EGO patch's `08659D` is a clean merge), NPCs Take Cover
(SPID `ActorTypeNPC` only; Lost Ones are `DraugrRace`), CPR AE (returns vanilla values when its graph variables are
missing — see `CombatPathingRevolution/src/Fallback_Hook.cpp`), Confidence (all Lost Ones/skeletons Foolhardy), and
Pandora's `DraugrBehavior.hkx` (only adds four stagger states over vanilla).

## The patch

The 8 records of `Lost Ones Revised - EGO Patch.esp` that carry `0028B0` ×1 beside another stack, copied verbatim minus
that one inventory entry (3 YAML lines each; round-trip identical):

`_20E_LostOne01Bow 0C6760`, `_20E_LostOne01Bow_Aggressive 02F52F`, `_25E_LostOne01Bow 1105CC`, `_28E_LostOne01Bow 1337CD`,
`_28E_LostOne01Bow_Aggressive 02F51B`, `_28E_LostOne01Bow_Respawn_Range1500 04807F`, `_00E_MQ16_LostOne02 14893B`,
`25E_DalGalarDeadServant15 0EA86C`. Variants templated on the three base archers inherit the fix.

**Owns** these 8 NPCs. Load right after `Lost Ones Revised - EGO Patch.esp` (it is a master). Regenerate after that
plugin updates: serialize it to `reference/mods/LostOnesRevisedEGOPatch`, then run
`python src/LostOneArcherAmmo/tools/01-build-lost-one-archer-ammo.py reference/mods/LostOnesRevisedEGOPatch`
(asserts exactly 8 records).

## Part 2 — the archer combat style (`tools/02`, 2026-10-22)

The ammo fix alone did not stop it: an Ancient Lost One archer (`_30E_LostOneDesert02Bow 04BB66`, no stray arrow,
Foolhardy) still fired and ran off. **58 winning undead archers use `csDraugrMissile 038A23`** (EGO wins it; a few use
the melee draugr styles `000D0D`/`072DF6`/`072DF7`, left alone because every melee draugr shares them). Every draugr
melee style carries the **`CantWait`** record flag; the missile style does not, so the combat AI may drop into "wait"
(hold a spot and watch). With `Dueling` on and EGO's fallback raised 0.2 → 0.35, that is fire, back off, stare.

Override = EGO's record with: `CantWait` added (record-header bit `0x80000`, `MajorRecordFlagsRaw: 524288` — Spriggit's
canonical form also echoes it as `SkyrimMajorRecordFlags`/`MajorFlags`, exactly like EGO's melee draugr styles),
`Dueling` removed, `FallbackMult` 0.35 → 0, `CircleMult` 0.3 → 0.05, `AvoidThreatChance` 0.2 → 0, `OffensiveMult`
0.8 → 1, `LongRangeStrafeMult` 0.25 → 0.1. Zero fields are omitted in the YAML. **Owns** `038A23`. Regenerate with
`python src/LostOneArcherAmmo/tools/02-build-archer-combat-style.py reference/mods/EGO` after an EGO update.

Also ruled out: the arrow projectiles (EGO only raises speed 3600 → 4300).

## Part 3 — skeleton archers, "Awoken Lost One" (`tools/03`, 2026-10-22)

An Awoken Lost One archer was found **with no arrows** and ran off. The winning `mihailancientskeletons.esp` is
**Lost Ones Revised's copy** (`mods/Lost Ones Revised/`, outranks the Ancient Skeletons mod's own 6-NPC copy), and it
replaces the inventory of 11 skeleton archer records:
- 7 (`_05E_SkelettBogenAmbush`, `_10E_SkelettBogen_Aggressive`/`_Range1200`, `_20E_SkelettBogen_Range1200`/`_Range3000`,
  `_25E_SkelettBogen_Range1200`, `_25E_SkelettBogenGhost_Range1200`) carry Mihail's `EAWO_LostOneBow 00463A` (no
  `NPCsUseAmmo`) and **one** Old Iron Arrow `0028B0` — EGO had 17–20 arrows there;
- 4 ghost archers (`_20E_SkelettBogenGhost_Range1200/1500/1800/Trigger`) carry a sword + shield skin
  (`000810`/`000814`) and **no bow or arrows**.

Override = Mihail's record verbatim with the lone arrow raised to 15 (his own count on his other archers) and, on the
4 ghosts, EGO's bow kit appended (Rune Bow `07C983` + 18 Old Rune Arrows `08659D`). Masters `mihailancientskeletons.esp`.
A load-order audit of every undead archer (bow + arrow count, templates and leveled lists resolved) now finds 0 records
without a bow or with fewer than 3 arrows (was 11). Regenerate after Lost Ones Revised updates: serialize
`mods/Lost Ones Revised/mihailancientskeletons.esp` to `reference/mods/mihailancientskeletons`, then run
`python src/LostOneArcherAmmo/tools/03-build-skeleton-archers.py reference/mods/mihailancientskeletons` (asserts 7 + 4).

## Part 4 — shielded skeletons that only block (`tools/04`, 2026-10-24)

Reported with a video: a sword-and-shield "Ancient Skeleton" in the Abandoned Cabin ruins stood in the bushes at 2 m with
its shield up for 18 s and never swung. In open ground it attacked, but rarely. ZenRagdollTrace caught it at death: ref
`000E1248`, base `_10E_Skelett_Range1200 046EF1`, Enderal's own placement, not Enemy Density's.

- Ancient Skeletons is **new in the 2.1 list**. Its plugin, loading after EGO, rebuilds Enderal's sword skeletons with
  Mihail's race, `mihailskeletonsword 000810` and **`mihailskeletonshieldskin 000814`, an iron shield**. EGO's version had
  only a weapon list. It also drops EGO's level 10, `HealthOffset 115`, perk `001E9B`, class and keywords: no EGO patch
  covers these records (not fixed here).
- Their combat style is `csDraugrMelee 000D0D` (EGO wins it), with **`Dueling`**, also in Enderal's own record. A dueling
  NPC with a shield blocks and waits for an opening, and in a tight space it never gets one.
- Ruled out: Combat Pathing Revolution AE (proper 1.7.104 build; its game settings match the old release's, and nothing
  sets its per-actor graph variables, so its advance and circling features are off), combat GMSTs (reach, block, stamina,
  and shield bashes off via Disable NPC Bash), Precision's AI reach hook (humans only), Airborne Get-Up Fix (logged nothing).
- The race has a full attack set (`attackStart`, power attacks, bashes) on `DraugrSkeletonProject.hkx`.

Override = EGO's record verbatim minus `Dueling` (it already has `CantWait`). **Owns** `000D0D`. Every melee undead using
it now presses the attack. Regenerate with `python src/LostOneArcherAmmo/tools/04-build-melee-combat-style.py reference/mods/EGO`
after an EGO update. Round trip identical apart from the description's line folding.

## Status

Built and installed 2026-10-22 as MO2 mod `Zenderal - Lost One Archer Ammo` (ammo fix, then rebuilt with the combat
style, then with the skeleton archers). Ammo-only and combat-style builds tested in game: archers still fled (the
skeleton archers had no arrows). **Build with parts 1–3 verified in game 2026-10-22: Lost One and skeleton archers keep shooting.**
Part 4 built 2026-10-24. **Unverified in game.**
