# FlintlockOverhaul

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FlintlockOverhaul/`
- **Ships:** `Zenderal - Flintlock Overhaul.esp` + `ZP_FlintlockAmmoPlayerScript.pex` + `Zenderal - DAR Rifles Recipes Off.esp` + `_KID.ini` + Wheeler icons
- **FormID block:** `0x800–0x81A`

## What it does

A Gentleman's Flintlock Armoury (Enderal Nexus 378) ships its 8 pistols as **staves** firing `PMPistolShot 000802` (flat 100–300, soul-gem recharged). `800` `ZP_FlintlockBullet` (Ordo's ball mesh), `801` recipe (1 iron → 5), plus an override of Ordo's `OLMRecipeMusketBalls 00CE18` (Musket Balls `002F9D`): 2 iron → 10 (the winning Muskets-of-the-Enderal recipe was 2 iron + 1 steel → 3; the Imperial Muskets one, 1 iron → 20, loses in MO2), `802` pistol FormList, `803` StartGameEnabled quest + PlayerRef alias, `804–80B` per-pistol shot enchantments, `80C` keyword `ZP_FlintlockShot`, `80D` hidden perk `ZP_FlintlockArcheryScaling`, `80E–813` `ZP_DeathItem_*` UseAll lists, `814` `ZP_LootGunAmmo` (pick-one: Musket Balls ×10/×15, Flintlock Bullets ×5/×10). **Chest loot** (`tools/07`, 2026-10-15): one `ZP_LootGunAmmo` entry is appended to each of Enderal's 14 tiered chest-loot lists, where its arrows live — `01E–04E` `BeuteGering/Klein`, `BeuteMittel`, `BeuteGross/Gro`, and `01E/02E_Kampfitems`. Each override is EGO's record verbatim (EGO wins all 14 in a live load-order scan). `02E_Kampfitems 085667` was won by Ordo's base-Enderal copy, which reverted EGO's version (ChanceNone 0.15, extra arrows, 4 items), so it is now EGO's version plus Ordo's three additions (Musket Balls ×10/×15, Old Flintlock Musket `00F5E9`). **This plugin owns these 14 lists**; rerun `tools/07` after any EGO update. **Script:** SKSE `OnActorAction` type 2 (Spell Fire fires for staves, `slot` = hand) empties the hand; 2 s later one bullet refills it; equip loads from a bullet, unequip refunds, `InventoryMenu` close strips soul-gem charge. **Writing `Left/RightItemCharge` [verified in game 2026-10-12]:** `RestoreActorValue` only returns DAMAGED charge, so a gun at a hard 0 never reloads; from 0, Right took `SetActorValue`, Left ignored it and only took `ForceActorValue` — the script tries Restore → Set → Force, re-reading each time. **Damage** (`tools/01`): magnitude = **1.2** × the pistol's Damage stat (Archery-50 value; puts each pistol just under the Ordo-Enderal musket of its tier — muskets are weapon 6–35 + ammo 6/10/8, about bow level); perk applies ×0.5·(1+Archery×0.02), Fortify Archery, Strong Bowstring I/II, Concentration, Expert Locksmith and EGO's bow bonus with EGO's conditions (bow talents are `ModAttackDamage` on `WeapTypeBow` and never touch a staff spell). **Loop pistol animations** (2026-10-17, `tools/01`): the 8 WEAPs keep EitherHand (Loop's clips serve the left hand, mirrored copies the right; LeftHand `013F43` was used briefly), and their 8 `FirstPersonModel` statics (`00080A–000811`, `000833–000837`) point at rotated copies `Zenderal\LoopPistols\...` generated into the `Zenderal - Loop Pistol Animations` MO2 mod by `src/LoopPistolAnims/tools/02`. **The static is the equipped model in third person too** (verified in game); the WEAP `Model` stays original as the world model. See [`LoopPistolAnims`](LoopPistolAnims.md). **NPCs** (`tools/00-scan-overriders.py` = reusable master-aware binary scan of the live load order → `overriders.json`; `tools/04-rebuild-npcs.py`): Ordo Legionis (Muskets of the Enderal, Nexus 525 — ships its OWN `OrdoLegionisMuskets.esp`, replacing the Skyrim one by filename; same FormIDs) overrides 95 NPCs, the flintlock pack 17, Enderal SE - Crossbows 8 of Ordo's, all as **base-Enderal copies** that reverted EGO's levels/skills/perks/AI/outfits on 82+10. 111 rebuilt = previous non-gun winner verbatim (EGO 92, FS 9, Skyrim 7, our UCR patch 2, EGO-Kata 1) + each gun mod's inventory delta vs the record it copied (Crossbows wins its 8, so Ordo's delta is skipped there); every second hostile musket NPC (Bandit/Nehrimes/Soeldner, sorted) gets a low pistol (Flintlock/Ancient ≤ level 10, else Priest's) + 5–10 bullets instead; 6 non-human carriers (Steel Watcher, Pahtira Centurion, skeleton miner, Miskahmur, Lyguria, Navigator) drop the pistol via a death list instead of wielding it; the porter's 7 deleted-pistol entries are dropped; orphan `02DE35:FS` "Gravewarden" (not a record in FS) skipped. **Sound** (`tools/02`): Ordo's own sounds; only `OLM_WPNBiggunFire 0197F7` / `OLM_WPNBlunderbussFire 00F5B8` re-pointed from the stub `01686B:Dawnguard.esm` output model to `10E425:Skyrim.esm`. **DAR Rifles** (`tools/05`): its anims require `IsEquippedRightHasKeyword("DAR Rifles.esp" | 0x800-0x802)`; the `_KID.ini` (archive root) adds `WeapTypeRifleBoltAction` to Ordo's 14 muskets; the separate ESL hides its 54 modern-gun recipes (AK-47…blasters) with `Smithing >= 1000`, no Items (originals reference Dawnguard). **First-person aim snap** (`tools/06`, MO2 mod `Zenderal - Musket Aim Fix`, clips not committed): the first-person sequence (OAR animation log 2026-10-14) is `CrossBow_IdleHeld` (hip, vanilla) → `CrossBow_Aim` (the RAISE) → `CrossBow_IdleDrawn` (the aimed HOLD, DAR) → `CrossBow_Release` (DAR). DAR's first-person `432101`/`432102` ship no `crossbow_aim`, so vanilla's plays: **0.2 s, 7 frames**, ending with the right arm ~100°, right hand ~150° and the `Weapon` bone 18 units off DAR's hold pose, which the graph closes in a quick blend just before the shot (first person only; third-person `432101` has its own aim). **v1** shipped the clips DAR parked in `432102/dlc01/New folder` — **byte-identical to vanilla**, no change. **v2** used DAR's hold clip as the raise — the gap just moved into the state blend, no change. **v3** (0.5 s synthesised raise) played slower, then still jumped: the first-person `1hm_behavior` clip generator `CrossBow Aim` (and Sneak/Dwarven) carries a **behaviour trigger `bowDrawn` at absolute 0.200 s**, and `CrossBowDrawing → CrossBow_IdleDrawn` fires on it with `fastBlendTransition` — **the raise is cut at 0.2 s whatever its length, so its 0.2 s pose must already be the hold**. A slower raise needs a behaviour patch moving that trigger (delaying fire for every first-person crossbow). **v4:** an OAR submod (keyword `0x800`, priority 432200) with a synthesised raise of exactly 0.2 s per variant: vanilla raise frame 0 (≈ the hip pose) smoothstep-eased into DAR's hold frame 0, keeping vanilla's annotations; read/written with **PyNifly's `hkx/anim_skyrim.py`, which reads and writes SE animation HKX without Blender** (round-trip exact; it decodes vanilla `sneakcrossbow_aim` track 41 `AnimObjectR` translation/scale as NaN — the tool starts that bone from the hold). v4 built 2026-10-14, not yet verified in game. **Holster: tried and reverted 2026-10-12.** Pistol meshes carry `Prn = SHIELD` (sheathed on the back); copies re-pointed at XPMSSE's `WeaponDaggerBackHip` did not give the wanted result in game, so they were removed — the curator places them with **Immersive Equipment Displays** instead (own holster nodes, apart from staves, since 2026-10-29: [`IEDPistolHolsters`](IEDPistolHolsters.md)). (PyNifly 29.1 cannot write `NiStringExtraData`, `NYI ... type 64`; the edit was a header string-table rewrite.) **Wheeler icons** (`tools/03`): `SKSE/Plugins/wheeler/resources/icons_custom/FID_<plugin>_0X<local FormID, no padding>.svg` (per-keyword variant `KWD_<EditorID>.svg`), curator's art. Masters: Skyrim, Update, FS, EGO, flintlock, Ordo, Crossbows — **load after Enderal SE - Crossbows**. Verified in game: reload/out-of-ammo/soul-gem block. Built 2026-10-12, not yet run: NPC rebuild, 1.2× damage, KID reload anims, recipe hiding, Wheeler icons. **Unverified:** whether NPCs actually fire a pistol (staff) — check a pistol bandit; still open: flintlock recipes' blueprint `GetItemCount` runs on placed ref `02A3DB:FS`, not the player.

## Silver Musket Balls (`815`, recipe `816`) — added 2026-10-16

Ghost damage in this list is EGO's, not Enderal's ([`EGO/combat-and-damage.md`](../EGO/combat-and-damage.md#silver-ghosts-and-undead)):
`XionSilverGhostDmg 001D3F` cuts weapon damage to ×0.05 against `ActorTypeGhost 0D205E`, and EGO emptied
vanilla's `SilverPerk 10D685`. Ranged silver is `XionSilverGhostArrowDmg 001D40` (×30 vs ghosts) and
`XionSilverArrowsPerk 001D05` (×2.15 +5 vs undead), both on `Player 000007`. Their only ammo test is
subject `WornHasKeyword XionSilverArrow 001D04` **and** `WornHasKeyword WeapTypeBow 01E715`. All 14 Ordo
muskets carry `WeapTypeBow` (e.g. `OL_Blunderbuss 00F5B7`), so a musket ball with keyword `001D04` gets
EGO's silver-arrow treatment and needs no new perk. **[verified from records]** Pistols are staves firing spells, so
`ModAttackDamage` never applies to them, and silver bullets for pistols would do nothing.

- `ZP_SilverMusketBall 000815`: a copy of Ordo's `OLMusket_ammo_lead 002F9D` (same projectile `002F9E`,
  damage 6, `IgnoresNormalWeaponResistance`). Keywords `XionSilverArrow 001D04` + `VendorItemArrow` +
  `WeapMaterialSilver 10AA1A`. Value 8. Pickup sounds are EGO's bolt sounds `002C63/002C64`; Ordo's point at
  the Dawnguard stub.
- `ZP_RecipeSilverMusketBall 000816`: 1 silver ingot → 10 at the forge, Smithing ≥ 40 (EGO's silver-ammo
  threshold, without its blueprint).
- Not in loot or vendor lists yet. **[verified in game 2026-10-16]** Silver balls hurt ghosts, so equipped
  AMMO does satisfy `WornHasKeyword` with a crossbow-type musket.

## `ZP_FlintlockWeapons 000802` is overridden by Reversal Shadow (2026-10-18)

[`ReversalShadow`](ReversalShadow.md) adds its pistol to this list in its own plugin. After changing the
list here, rerun `src/ReversalShadow/tools/02-build-records.py` or the override reverts the change.

## Every pistol on bullets; pistol blueprints at traders (2026-10-22)

**Report (Zenderal alpha):** players found pistols that still ran on soul gems. A whole-load-order WEAP scan
(staves whose EditorID/name/model says pistol/gun) found exactly two sources: the pack's 8 (already ours) and
**Loop's "Simple Pistol Shooting Animation"** (`Pistol animation by Loop.esp`, installed for its animations),
which ships 4 example **Hunter Pistols** (`000802`, `00080B`–`00080D`) and 4 **Hunter Crossbows** (`000C24`,
`000C2A`, `000C2B`, `000824`), all staves with Loop's own enchantments. Their 8 forge recipes need only
`DwarvenSmithing 0CB40E`, which the Player record starts with, plus a `HearthFires.esm` component that never
resolves (DLC stub) and so did not block crafting. Curator's call: pistols convert, crossbows go.

- `tools/01` also builds `ZP_FlintlockShot_HunterPistol*` `0x817`–`0x81A` (the Flintlock Pistol's enchantment
  at 10.8 / 14.4 / 18.0 / 21.6, the pack's lower tiers) and points the 4 Hunter Pistols at them; their own
  meshes and animations stay. They are in `ZP_FlintlockWeapons`, so the reload script and the Archery perk
  treat them like the pack's pistols (Reversal Shadow's `tools/02` rerun for its copy of the list).
- `tools/08` overrides Loop's 8 recipes: the DLC-stub component dropped, the 4 Hunter Crossbow recipes hidden
  with `Smithing >= 1000`. **This plugin owns them**; Unresolved References Cleanup no longer carries them.
  Hunter Crossbows a player already owns keep using soul gems.

**Blueprints.** The pack's 5 blueprints (`PMCraftingPlan*` `000800`, `000825`–`000828`) carry
`BlueprintDONOTUSE 02A3D6`, which is on Enderal's folio list `_00E_FS_BlueprintList 02A3DD`, so the folio
takes them, and the pack's recipes test `GetItemCount` on the folio's actor `02A3DB:FS` — Enderal's own
blueprint mechanism (`_00E_FS_BlueprintContainerSpellSC`), not a bug. They were only in three quest
containers. `tools/08` adds them to the trader list `_00ETraderCraftingPlans 137A06`, which ~20 merchant chests
and the 01E/02E BeuteGross/Mittel/Gering chest lists draw from. Live winner was **Enderal SE - Crossbows**: a
base-Enderal copy + its crossbow plan `000832`, which reverted EGO's version (ChanceNone 0.05, all levels 1,
5 more plans). Ours = EGO's record + Crossbows' plan + the 5 blueprints at level 1 (63 entries). **This plugin
owns `137A06`**; rerun `tools/08` after EGO or Crossbows changes it.

Built and deployed 2026-10-22 (live-order scan: all 12 records won by this plugin). **Unverified in game.**

