# FlintlockOverhaul

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FlintlockOverhaul/`
- **Ships:** `Zenderal - Flintlock Overhaul.esp` + `ZP_FlintlockAmmoPlayerScript.pex` + `Zenderal - DAR Rifles Recipes Off.esp` + `_KID.ini` + Wheeler icons
- **FormID block:** `0x800–0x81A`

## What it does

A Gentleman's Flintlock Armoury (Enderal Nexus 378) ships its 8 pistols as **staves** firing `PMPistolShot 000802` (flat 100–300, soul-gem recharged). `800` `ZP_FlintlockBullet` (Ordo's ball mesh), `801` recipe (1 iron → 5), plus an override of Ordo's `OLMRecipeMusketBalls 00CE18` (Musket Balls `002F9D`): 2 iron → 10 (the winning Muskets-of-the-Enderal recipe was 2 iron + 1 steel → 3; the Imperial Muskets one, 1 iron → 20, loses in MO2), `802` pistol FormList, `803` StartGameEnabled quest + PlayerRef alias, `804–80B` per-pistol shot enchantments, `80C` keyword `ZP_FlintlockShot`, `80D` hidden perk `ZP_FlintlockArcheryScaling`, `80E–813` `ZP_DeathItem_*` UseAll lists, `814` `ZP_LootGunAmmo` (pick-one: Musket Balls ×10/×15, Flintlock Bullets ×5/×10). **Chest loot** (`tools/07`, 2026-10-15): one `ZP_LootGunAmmo` entry is appended to each of Enderal's 14 tiered chest-loot lists, where its arrows live — `01E–04E` `BeuteGering/Klein`, `BeuteMittel`, `BeuteGross/Gro`, and `01E/02E_Kampfitems`. Each override is EGO's record verbatim (EGO wins all 14 in a live load-order scan). `02E_Kampfitems 085667` was won by Ordo's base-Enderal copy, which reverted EGO's version (ChanceNone 0.15, extra arrows, 4 items), so it is now EGO's version plus Ordo's three additions (Musket Balls ×10/×15, Old Flintlock Musket `00F5E9`). **This plugin owns these 14 lists**; rerun `tools/07` after any EGO update. **Script:** SKSE `OnActorAction` type 2 (Spell Fire fires for staves, `slot` = hand) empties the hand; 2 s later one bullet refills it; equip loads from a bullet, unequip refunds, `InventoryMenu` close strips soul-gem charge. **Writing `Left/RightItemCharge` [verified in game 2026-10-12]:** `RestoreActorValue` only returns DAMAGED charge, so a gun at a hard 0 never reloads; from 0, Right took `SetActorValue`, Left ignored it and only took `ForceActorValue` — the script tries Restore → Set → Force, re-reading each time. **Damage** (`tools/01`): magnitude = **1.2** × the pistol's Damage stat (Archery-50 value; puts each pistol just under the Ordo-Enderal musket of its tier — muskets are weapon 6–35 + ammo 6/10/8, about bow level); perk applies ×0.5·(1+Archery×0.02), Fortify Archery, Strong Bowstring I/II, Concentration, Expert Locksmith and EGO's bow bonus with EGO's conditions (bow talents are `ModAttackDamage` on `WeapTypeBow` and never touch a staff spell). **Loop pistol animations** (2026-10-17, `tools/01`): the 8 WEAPs keep EitherHand (Loop's clips serve the left hand, mirrored copies the right; LeftHand `013F43` was used briefly), and their 8 `FirstPersonModel` statics (`00080A–000811`, `000833–000837`) point at rotated copies `Zenderal\LoopPistols\...` generated into the `Zenderal - Loop Pistol Animations` MO2 mod by `src/LoopPistolAnims/tools/02`. **The static is the equipped model in third person too** (verified in game); the WEAP `Model` stays original as the world model. See [`LoopPistolAnims`](LoopPistolAnims.md). **NPCs** (`tools/00-scan-overriders.py` = reusable master-aware binary scan of the live load order → `overriders.json`; `tools/04-rebuild-npcs.py`): Ordo Legionis (Muskets of the Enderal, Nexus 525 — ships its OWN `OrdoLegionisMuskets.esp`, replacing the Skyrim one by filename; same FormIDs) overrides 95 NPCs, the flintlock pack 17, Enderal SE - Crossbows 8 of Ordo's, all as **base-Enderal copies** that reverted EGO's levels/skills/perks/AI/outfits on 82+10. 111 rebuilt = previous non-gun winner verbatim (EGO 92, FS 9, Skyrim 7, our UCR patch 2, EGO-Kata 1) + each gun mod's inventory delta vs the record it copied (Crossbows wins its 8, so Ordo's delta is skipped there); every second hostile musket NPC (Bandit/Nehrimes/Soeldner, sorted) gets a low pistol (Flintlock/Ancient ≤ level 10, else Priest's) + 5–10 bullets instead; 6 non-human carriers (Steel Watcher, Pahtira Centurion, skeleton miner, Miskahmur, Lyguria, Navigator) drop the pistol via a death list instead of wielding it; the porter's 7 deleted-pistol entries are dropped; orphan `02DE35:FS` "Gravewarden" (not a record in FS) skipped. **Sound** (`tools/02`): Ordo's own sounds; only `OLM_WPNBiggunFire 0197F7` / `OLM_WPNBlunderbussFire 00F5B8` re-pointed from the stub `01686B:Dawnguard.esm` output model to `10E425:Skyrim.esm`. **DAR Rifles** (`tools/05`): its anims require `IsEquippedRightHasKeyword("DAR Rifles.esp" | 0x800-0x802)`; the `_KID.ini` (archive root) adds `WeapTypeRifleBoltAction` to Ordo's 14 muskets; the separate ESL hides its 54 modern-gun recipes (AK-47…blasters) with `Smithing >= 1000`, no Items (originals reference Dawnguard). **First-person aim snap** (`tools/06`, MO2 mod `Zenderal - Musket Aim Fix`, clips not committed): the first-person sequence (OAR animation log 2026-10-14) is `CrossBow_IdleHeld` (hip, vanilla) → `CrossBow_Aim` (the RAISE) → `CrossBow_IdleDrawn` (the aimed HOLD, DAR) → `CrossBow_Release` (DAR). DAR's first-person `432101`/`432102` ship no `crossbow_aim`, so vanilla's plays: **0.2 s, 7 frames**, ending with the right arm ~100°, right hand ~150° and the `Weapon` bone 18 units off DAR's hold pose, which the graph closes in a quick blend just before the shot (first person only; third-person `432101` has its own aim). **v1** shipped the clips DAR parked in `432102/dlc01/New folder` — **byte-identical to vanilla**, no change. **v2** used DAR's hold clip as the raise — the gap just moved into the state blend, no change. **v3** (0.5 s synthesised raise) played slower, then still jumped: the first-person `1hm_behavior` clip generator `CrossBow Aim` (and Sneak/Dwarven) carries a **behaviour trigger `bowDrawn` at absolute 0.200 s**, and `CrossBowDrawing → CrossBow_IdleDrawn` fires on it with `fastBlendTransition` — **the raise is cut at 0.2 s whatever its length, so its 0.2 s pose must already be the hold**. A slower raise needs a behaviour patch moving that trigger (delaying fire for every first-person crossbow). **v4:** an OAR submod (keyword `0x800`, priority 432200) with a synthesised raise of exactly 0.2 s per variant: vanilla raise frame 0 (≈ the hip pose) smoothstep-eased into DAR's hold frame 0, keeping vanilla's annotations; read/written with **PyNifly's `hkx/anim_skyrim.py`, which reads and writes SE animation HKX without Blender** (round-trip exact; it decodes vanilla `sneakcrossbow_aim` track 41 `AnimObjectR` translation/scale as NaN — the tool starts that bone from the hold). v4 built 2026-10-14, not yet verified in game. **Replaced by v5, aim down sights (2026-11-01): see the section at the end.** **Holster: tried and reverted 2026-10-12.** Pistol meshes carry `Prn = SHIELD` (sheathed on the back); copies re-pointed at XPMSSE's `WeaponDaggerBackHip` did not give the wanted result in game, so they were removed — the curator places them with **Immersive Equipment Displays** instead (own holster nodes, apart from staves, since 2026-10-29: [`IEDPistolHolsters`](IEDPistolHolsters.md)). (PyNifly 29.1 cannot write `NiStringExtraData`, `NYI ... type 64`; the edit was a header string-table rewrite.) **Wheeler icons** (`tools/03`): `SKSE/Plugins/wheeler/resources/icons_custom/FID_<plugin>_0X<local FormID, no padding>.svg` (per-keyword variant `KWD_<EditorID>.svg`), curator's art. Masters: Skyrim, Update, FS, EGO, flintlock, Ordo, Crossbows — **load after Enderal SE - Crossbows**. Verified in game: reload/out-of-ammo/soul-gem block. Built 2026-10-12, not yet run: NPC rebuild, 1.2× damage, KID reload anims, recipe hiding, Wheeler icons. **NPC pistols (traced 2026-11-11):** they fire, but an NPC's staff spends charge (2 → 1, cost 1) and at 1 the AI puts the pistol away and never fires it again: one shot per enemy. [`PistolRamrodReload`](PistolRamrodReload.md)'s enemy ability now reloads it the player's way after every shot (*Enemies reload too*). (The flintlock recipes' folio-only blueprint check was fixed 2026-10-30, see the end of this doc.)

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
- **2026-10-30: the Hunter Pistols go too** (curator, after a player report: the Hunter Pistol showed
  Damage 1, the Ancient Dueling Pistol 6). Their 4 recipes get the same `Smithing >= 1000` hide; the 4 forge
  recipes were the only way to get one (no list, container, outfit or placed ref uses them, live-order scan).
  The `tools/01` conversion stays, so one a player already crafted still fires Flintlock Bullets. Deployed over
  `Zenderal - Patch Collection`'s copy (the only live one; the old copy is in `E:/Zenderal-backups`). The new
  build differs from that copy only in these 4 recipes (YAML diff of the serialized live plugin).
  **Unverified in game.**
- A pistol's inventory **Damage** comes from the WEAP's own Damage stat, not the shot: the shot is the
  enchantment's magnitude. Loop's pistols have no Damage stat (menu: 1); the Ancient Dueling Pistol has 9 (menu:
  6, so the menu scales it, probably by the WEAP's Skill, Destruction; not checked). Both fire the same 10.8 at
  Archery 50. Every pistol's menu number is cosmetic.

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


## Pistol blueprints work from the inventory (2026-10-30)

**Report (Discord):** a player owned a pistol blueprint and saw no pistol recipe at the forge.

The pack's 5 working recipes (`PMRecipeFlintlock01 00081A`, `PMRecipeDuelingPistol01–04 000821–000824`)
need Smithing ("Handicraft", printed in each blueprint's name: 20 / 23 / 28 / 33 / 40) **and**
`GetItemCount(blueprint) >= 1` run on the folio's actor `02A3DB:FS`, nothing else. That actor only holds what
the player hands it: reading Enderal's blueprint folio book casts `_00E_FS_BlueprintContainerSpellSC`, which
opens a `ShowGiftMenu` on it; nothing moves a blueprint there by itself. Enderal's own recipes (EGO's winning
`_03E_RecipeArmor_22_AssassinCuirassForged 13CAE1`, …) check Smithing, then `GetItemCount(blueprint)` on the
subject with **OR**, then the folio, so a blueprint in the inventory or in the folio both work.
**[verified]** in the records and Enderal's script source.

`tools/08` part 3: each of the 5 recipes = the pack's record verbatim with that OR'd subject check inserted
before its folio check (Smithing AND (inventory OR folio)). **This plugin owns them.** The pack's other 4
recipes (`PMRecipeFlintlock02–05`) create `000812–000815` with blueprints `00081E–000820`, and none of those
records exist in the pack: dead recipes, left alone. So the Starling Flintlock, Guardian Flintlock and
Guardian's Blunderbuss pistols have no recipe at all (found only).

Built 2026-10-30, Spriggit round trip identical; deployed over Patch Collection's copy. Players get it with the
next Patch Collection release. **Unverified in game.**

## First-person aim down sights (v5, 2026-11-01)

**Report:** in first person the muskets were not upright and not lined up with the crosshair. No Nexus mod fixes
this (searched SE, LE and Enderal SE through the Nexus API): Crosshair-aligned Crossbow (42267, installed) and
JellyFishFP CROSSBOW (158826) fit the vanilla crossbow mesh; OrdoLegionisMusketsDAR Reupload (112086) ships
first-person clips with the same sizes as DAR Rifles' 432101 set we already run.

**Measured** with forward kinematics on the vanilla `skeletonfirst.hkx` (`Camera1st [Cam1]` is the view, +Y
forward, +Z up; weapon meshes are upside down: up is mesh -Z). Calibration: the vanilla crossbow under
Crosshair-aligned Crossbow's hold puts its bolt tip 0.1 deg / -1.8 deg off the crosshair. Under DAR's bolt-action
hold every musket is **rolled ~15.5 deg**, its front sight 2-6 deg below and up to 2 deg beside the crosshair. And
Ordo's meshes are not straight: each barrel sits -4.7..+0.4 deg (yaw) and 0..5 deg (tilt) off its mesh's own axis,
differently per mesh, so no single clip lines them all up. Improved Camera uses the first-person arms for crossbow
aim (`bEnableThirdPersonCrossbowAim=0`) and hands FOV = world FOV = 94, so these angles are what is on screen.

**Fix** (`tools/06`, rewritten; MO2 mod `Zenderal - Musket Aim Fix`, clips not committed). Per musket mesh:

1. The sight line is read from the winning mesh (unskinned shapes; points sampled over the triangles, since long
   barrel triangles have vertices only at their ends): barrel top fitted slab by slab, front = the front-sight
   tip, rear = barrel top at the breech, raised until nothing over the barrel between the eye and the front sight
   rises above it (the matchlock's and classic's rear sight blocks, breech tangs).
2. One rigid correction, solved on DAR's hold: front-sight tip **`SIGHT_DROP_DEG` = 1 deg** under the crosshair,
   rear sight **`EYE_HEIGHT` = 3 units** below the eye (you look down the barrel), upright, the breech's distance
   from the eye kept (20-35 units). Eye height rendered before choosing: 0 (eye on the line) lets the breech hide
   the barrel, 1.5 still crowded, 4.5 looks over the gun. The drop came from the first in-game test (first build
   had the tip on the crosshair): the crosshair dot sat on the muzzle; the curator wants it in clear air where the
   ball goes. That screenshot (long musket or double-barrel) put the dot's radius at ~0.2 deg and the muzzle top
   ~0.4 deg above the dot's centre, an in-game offset this model doesn't capture (Improved Camera's camera vs the
   1st-person `Camera1st` node is the suspect); 1 deg keeps the dot clear with margin on every musket.
3. It is written into the `NPC Spine2 [Spn2]` track only, in the camera's frame, on every frame of the hold, shot
   and reload (dwarven and sneak variants too). Both arms and the gun move together (grip unchanged); the camera
   is a child of the root and stays. DAR's reload starts and ends at its hold, so every hand-off stays seamless.
4. The 0.2 s raise is rebuilt into the corrected hold (v4's synthesis; `bowDrawn` still cuts it at 0.2 s).
5. Two OAR submods per mesh, keyed on its WEAPs (`IsEquipped`, right hand): `ADS <mesh>` (432400+i) and
   `ADS <mesh>, both reload perks` (432450+i): the corrected reload retimed with Quick Reload Stack's own code
   (`src/Prophecy/tools/04`, imported), so both perks still stack. QRS's keyword musket submod (432301) is
   shadowed for these 14 muskets. DAR has no first-person sneak reload: vanilla's still plays there.

**Shots landed above the dot (2026-11-01, second in-game test).** Traced with [`SpellAimTrace`](SpellAimTrace.md)
1.1.0/1.2.0 and the curator's 120 fps recording. The HUD dot is exactly at screen centre, and the first-person rig's
`Camera1st` sits exactly at the render camera, so neither the dot nor the pose was at fault. The game spawns the ball
at the first-person `NPC R MagicNode [RMag]`: DAR's clips park it ~88 units out (local 9.6, -15.1, 89.7 from the
hand), 2 right / 1-2 up of the crosshair ray. Hit Where You Aim aims from that exact point (its `origin` argument)
at the crosshair ray, but it does so in the launch-angle call one game frame (16 ms) **after** the launch. DAR's
shot clip turns `Camera1st` and `NPC LookNode [Look]` (the arms' parent, pivoting at the camera) 2.89 deg up at
frame 4 (0.135 s), the frame of `arrowRelease` (0.133 s). The camera follows: up ~2 deg within 33 ms in the
recording, already 0.40 deg in HWYA's frame. So HWYA aimed along the kicked camera: the ball flew 0.25-0.32 deg
above the view it was fired from, landing +12 to +17 units high at 2200-2700 units. Third-person shots (no kick)
were within 0.05 deg. The sneak shot clip turns the LookNode from 0.067 s, before the shot.

Fix: `delay_recoil` shifts every track of the four shot clips later by whole frames, so the camera node and the
LookNode stay at their pre-shot pose until `arrowRelease` + `REST_AFTER_SHOT` (0.067 s, two game frames at 30 fps).
Standing: held 3 frames, kick at 0.236 s instead of 0.135 s. Sneak: held 5 frames. The recoil itself is unchanged.
Reload clips also carry an `arrowRelease` annotation and are left alone.

The build re-decodes every clip and fails unless the front sight is within 0.3 deg of its target, the roll under
0.3 deg and no point of the gun in the line of sight; result: within 0.03 deg / 0.02 deg / none, on all 14.
Clips keep Havok's block header (`blockDuration` = (maxFramesPerBlock - 1) x frameDuration): v4 zeroed it, the
latent issue [`LoopPistolAnims`](LoopPistolAnims.md) v12 found. Quick Reload Stack's `retime()` writes the same
header since 2026-11-01, so the `havok_blocks()` call after it is now a no-op kept for safety.

**Rerun** after DAR Rifles, Ordo Legionis, PG Patcher Output or Quick Reload Stack changes (needs numpy).
Backup of v4: `E:/Zenderal-backups/2026-11-01-musket-aim-fix-v4/`. **In game (2026-11-01, first build):** upright
and lined up, "almost perfect", but the dot covered the muzzle. Second test: the drop works (muzzle just under
the dot in the recording) but shots landed above the dot. **Third test, with the recoil hold: verified in game**
("everything looks good"); traced over 75 first-person shots: the camera no longer moves between the launch and
HWYA's aim (±0.03 deg on ~65 of them; the rest were shots fired while turning, or led moving targets), and impacts
land 0.03-0.06 deg under the crosshair ray (e.g. -2.2 units at 2600, -0.8 at 1000), the same as third person. Still to
check: a few muskets, the raise, a shot, a reload (with and without both reload perks) and sneak aim.
Not done (curator's call): a zoom while aimed, hiding the crosshair while aimed.

## Ramrod reload, third person (`tools/09`, 2026-11-01) — NOT SHIPPED until Zodd agrees

**Curator's request:** the ramrod reload from *Zodd's 4 ramrod-loaded muskets animated* (Nexus 191481, Zodd) on all
14 Ordo muskets. The mod is five third-person DAR clips (raise, aimed hold, hip hold, shot, reload) for four
GLEN-MORIL muskets (`IsEquippedRight("Glenmoril.esm" | 0x2C9019)` in `90070009` "ramrod",
`0x2E5FC3/4/5` in `90070010` "ramrod fat"; GLEN-MORIL is not in the list). No first-person clips, no anim object (the
ramrod work is all in the hands). The shot fires at 0.2 s and **the shot clip is the reload**: 5.1 s carrying the
whole ramrod work (`arrowAttach` at 1.567 s), 3.9 s at the graph's 1.3 Quick Reload/Rapid Shot speed. Traced
(SpellAimTrace 1.3.0): after a shot the game never sends `reloadStart`, the 1hm graph stays in its attack state, plays
the shot clip to its end and leaves on the clip's own `attackStop`. Zodd's separate reload clip (4.43 s) plays only
when the game sends `reloadStart` (e.g. drawing an unloaded musket). Vanilla is built the same way (its 2.83 s
release holds the reload).

**Fit (measured, 3P skeleton from `Skyrim - Animations.bsa`):** the clips are made for a gun whose muzzle is ~55 units
from its grip origin; the left hand pours at ~51, lifts the rod to 68-72 and rams. Ordo's muzzles: 33 (musketoons),
37 (blunderbuss), 50 (double-barrels), 59-60 (Old Flintlocks), 74 (rifle), 78-89 (wheellocks, classic, long,
matchlock). As-is only the Old Flintlocks and double-barrels fit; the long guns rammed mid-barrel, the short ones air.

**Fix, per mesh** (MO2 mod `Zenderal - Musket Ramrod Reload`, clips not committed, read straight from the downloaded
archive): in the shot and reload clips the gun slides along its own barrel through the right hand by
`-w * (muzzle - 55)`, `w` = 0 while Zodd's right hand holds the stock wrist and 1 while it holds the barrel (it
regrips during the reload; smoothstep from its position along the gun). The muzzle then sits where the left hand
works; the right hand ends further up or down the barrel. Only the `Weapon` track changes. Zodd also swings the gun
muzzle-down (47 deg) before the ram (reload 0.54-0.67 s): his gun clears the ground, the long Ordo guns dug in up to
13 units, so the slide is bounded every frame to keep the gun's lowest point 1 unit above the actor's root (both
directions: muzzle up limits the slide, muzzle down forces a brief slide back; 2-6 frames on the long guns). Hands:
"ramrod fat" for muzzle radius >= 2.0 (blunderbuss, musketoons, double-barrels, Old Flintlocks), "ramrod" else. OAR
submods keyed on each mesh's WEAPs: `Ramrod <mesh>` (432500+i) and `Ramrod <mesh>, both reload perks` (432550+i, the
reload retimed with Quick Reload Stack's code). Sneak: see *Sneak* below; first person keeps the aim-down-sights set.

**Permission.** Zodd's page asks for permission before modifying the files or using the assets; this mod holds
modified copies. It is in `Zenderal.compiler_settings`' Ignore list (backup of the settings before:
`E:/Zenderal-backups/2026-11-01-compiler-settings-pre-ramrod-ignore/`), so Wabbajack never compiles it in. Remove
that entry only once Zodd has agreed, and credit Zodd.

**Side effects:** third person gets Zodd's holds and raise too (made for GLEN-MORIL meshes); reload length differs by
view until `tools/10` (below); `ZenMusketHandling`'s dodge lock caps at `MaxLockMs` 5000 (it is unticked in Ultra
anyway). The `both reload perks` submods (here, the aim-down-sights set's and Quick Reload Stack's own) retime only the
separate reload clip, which a shot never plays, so after a shot both perks reload no faster than one. **Verified in game
2026-11-01**, standing and crouched, both views. Rerun `tools/09` after Ordo, PG Patcher Output or Quick
Reload Stack changes, then `tools/10` and `tools/11` (09 rebuilds the mod folder).

### First person (`tools/10`, same MO2 mod, same permission note)

Zodd has no first-person clips, and Improved Camera can't show the third-person body for the reload alone: its
`IsAiming` counts every crossbow attack state from the draw through `kBowAttached` (the reload) as aiming, and the one
exception needs *Archery Gameplay Overhaul* (IC-NG source; the installed IC 2.0 build lacks even that). Copied
as-is, the reload happens below a level first-person view (rendered: only the muzzle tip). In Zodd's video the camera
follows the head, which looks down 10-20 deg and turns +-15-20 deg through the reload (measured on his clips).

`tools/10` retargets each musket's fitted third-person shot and reload onto the first-person arms. The camera is the
third-person `NPCEyeBone` facing the actor's forward. Everything under `NPC Spine2` is mapped into the first-person
rig, keeping third-person local rotations, first-person bone lengths (the upper arm is 20.26 there vs 22.83; finger
bases) and the slid gun. The arms are turned opposite the head's pitch and yaw relative to the clip's first frame,
so the hands appear as with a head-following camera while the world stays level (`LIFT_EXTRA_DEG` adds more). Each arm
is solved shoulder-elbow-hand onto its mapped third-person hand (exact on every frame, none out of reach),
elbows toward the mapped elbows. The pauldron attach points have different parents in the two rigs and are placed at
their mapped world. Bones above Spine2 and `Camera1st` stay at the aim-down-sights hold, so there's no camera kick. The
shot clip holds aim-down-sights until 0.3 s (shot at 0.2) and blends into the ramrod motion by 0.8 s; the separate
reload clip blends in from the idle hold over 0.3 s. Both blend into the first-person **idle hold**
(`crossbow_idleheld.hkx`, vanilla's: DAR Rifles' 432101 set has none) over their last 1.0 s and end exactly on it
(asserted): after either clip the 1hm graph is back in `1HM_Ready_State` (`attackStop` and `reloadStop` both lead
there), which plays that hold. 1.1 ended on the aim-down-sights hold, so the gun snapped from the sights down to the
hip in under 0.1 s as the clip ended (curator's recording 2026-11-01: "near the end the gun repositions"). 1.0 froze
the shot clip on the reload clip's first pose after `arrowAttach`, assuming a hand-over that never happens ("starts
but stops and just holds the gun"). The arms follow Zodd's head turn unsmoothed on purpose: his head tracks the gun
through the fast muzzle-down swing, so following it steadies the gun on screen (smoothed over 0.15 s, the gun's peak
on-screen speed rose from 35.8 to 39.4 units a frame). The swing itself (shot 1.07-1.25 s, the gun briefly leaves
the view) is Zodd's motion. Timing and annotations are Zodd's, so first and third person reload alike (5.1 s, 3.9 s
with Quick Reload or Rapid Shot). OAR, first
person: `Ramrod 1P <mesh>` 432600+i (shot + reload) and `..., both reload perks` 432650+i, above the
aim-down-sights set. Sneak: see *Sneak* below.

Rendered from the first-person camera (FOV 100, the active IC profile's): the pour, rod and ram show in the upper
left to centre of the screen. During Zodd's muzzle-down swing (shot 0.5-1.0 s, reload 0.4-0.9 s) the stock passes
6-8 units from the camera (may clip at the near plane), and the gun dips below the view for ~0.3 s before rising into
the sights at the end. **Verified in game 2026-11-01** ("the animation itself looks clean"). Keep IC's *Third Person
Crossbow* off.

### Ball and ramrod props (`tools/09` + `tools/11`, same MO2 mod, same permission note)

Curator's request (2026-11-01): "a pellet and stick loading with the left hand". Zodd's clips mime both.

**Mechanism, the list's own:** Eating Animations and Sounds (`TaberuAnimation.esp`) and JellyFish Animated Potions put
props in hands with clip annotations `AnimObjLoad.<EditorID>` (EAS: 0.2 s before) `AnimObjDraw.<EditorID>`, unloaded
by the ANIO's unload event (all 66 vanilla ANIO use `AnimObjectUnequip`). The annotation only fires if the graph lists
the event: both 1hm behaviors (1P and 3P, Pandora output) list `AnimObjLoad`, `AnimObjDraw` and `AnimObjectUnequip`,
and no transition listens to them. The prop mesh names its attach bone in an `NiStringExtraData` "Prn" on its
`BSFadeNode` root (EAS: `prn` = a finger bone). Ours hang on `AnimObjectL` (child of the left hand), whose track the
clips animate, so one bone carries the ball and then the rod wherever they need to be.

**Beats** (found per mesh from the left middle finger against the bore, `phases()`; shot clip, all 14 alike within a
frame; the reload clip is the same from 0.67 s on): hand at the hip pouch (lowest point, 1.51 s) → ball drawn; at the
muzzle (closest, 2.31-2.38) → ball unloaded, after sliding from the thumb/index pinch into the muzzle over 0.15 s;
hand under the barrel (2.79-2.89) → rod drawn in its stowed place (`ROD_GAP` below the barrel, top end 1 unit behind
the muzzle); up past the muzzle (2.95) the rod moves into the bore line and rides the fist (3 units of rod above
it), two strokes (peaks 3.05/3.42), back under the barrel (3.49-3.52) where it stops in its stowed place while the hand
slides on, unloaded as the hand leaves for the stock (3.62). Every switch between the two lines takes at least 0.1 s.

**Left hand:** Zodd's ramming hand works 8-16 units off Ordo's bores (his GLEN-MORIL muskets differ), so a rod in his
fist would hang beside the barrel. From 0.15 s before the grab to 0.15 s after the stow the left hand is eased onto
the rod line by shoulder-elbow-hand IK (its world rotation kept, elbow in its own plane), the fist held 2.5 units
above the muzzle face while ramming (Zodd's went 7 below it, into the barrel). At the stroke tops his arm is already
straight: the fist slides down the rod line to the nearest point in reach (the blunderbuss missed by up to 3.25
units otherwise), so those strokes are a little shorter. First person inherits all of it from the 3P clips
(annotations copied, `AnimObjectL` kept relative to the exactly-placed hand); the first-person arm is shorter, so where
the stretched hand is out of its reach (15 frames on some guns) the hand slides along the rod's own axis, the rod with
it (still in the bore).

**Back to the stock (`carry()` in tools/09, 2026-11-01):** curator: "near the end of the animation after firing the
rifle dips / clips below the left hand". Measured: from the stow Zodd's own hand (our clip matched his within 0.2
units from 3.69 s) lets go under the barrel and passes back over the top of the gun, 8-17 units above it, while the gun
swings from muzzle-up (+37 deg) to level under it, and takes the stock again only at 4.36 s, in both views. Now its
pose relative to the gun eases (smoothstep, lerp/slerp) from where it let go (rod_off) to the first frame it stays
within `REGRIP_DIST` 6 units of its last pose (3.66-4.40 s on most guns, to 4.73 s on the long ones), the arm solved
onto it; where the forestock is out of reach it slides along the gun toward the stock (up to 17 units, long guns). The
gun's quick muzzle-up settle right after (4.36-4.53 s, about 25 deg) is Zodd's own and stays. **First person** had a
second drift: the last second's bone-by-bone blend into the idle hold swung the left hand up to 12-14 units beside the
gun (4.4-4.6 s). tools/10's `left_on_gun()` re-solves the arm during that blend onto a grip blended from the motion's
to the idle hold's (sliding along the gun where the shorter 1P arm can't reach). After both: 1P hand within 3.2-4.4
units under and 2.4-3.2 beside the gun, never above it, contact depth no deeper than the idle hold's own (palm 1.6).
Seen in game 2026-11-01 together with the post-shot fix ("looks great").

**First person, right after the shot** (curator 2026-11-01: "the musket clips through the left hand"): the shot clip's
blend out of the aim-down-sights hold (0.3-0.8 s) went bone by bone too. The left hand travels from the hold's
forestock grip (13 units up the gun) to Zodd's at the stock wrist (1-3 units up, on the other side), and the per-bone
slerp took it within 1.4-3.3 units of the gun's centre line, through the stock: finger joints inside the gun at 0.40,
0.54 and 0.74 s (`ol_doublebarrelrifle03`, measured against the mesh surface). The same `left_on_gun()` now runs over
that blend, from the hold's grip to the motion's: the hand stays 5.3-8 units out to the side of the gun, sliding back
along the stock, fingers on its surface. Left as Zodd's: one frame at 1.07 s where his hand lifts off the stock for the
pouch and two fingers graze it (third person too). Verified in game 2026-11-01 ("looks great").

**Safety:** every clip in the submods starts with `AnimObjectUnequip`: 3P raise, holds, shot, reload; 1P shot and
reload, plus copies of the 1P idle hold (vanilla's) and the aim-down-sights set's raise and aimed hold (with Dwarven
names) in each `Ramrod 1P <mesh>` submod. A reload cut short (dodge, stagger) unloads its prop as soon as the gun
returns to a hold.

**Records and meshes (`tools/11`):** plugin `Zenderal - Musket Ramrod Reload.esp` (ESL, HEDR 1.7; YAML generated into
`src/FlintlockOverhaul/RamrodReloadESP`, built with the pinned Spriggit CLI into the MO2 mod; **not in
`build/manifest.json`**, it ships with the rest only after Zodd agrees): ANIO `ZEN_RamrodBall` 0x800 and
`ZEN_Ramrod_<mesh>` 0x801-0x80E, unload event `AnimObjectUnequip`; the loading sounds' SNDR `ZEN_MusketLoad7` 0x80F
and `ZEN_MusketLoad1` 0x810 (below). Meshes under `meshes/Zenderal/MusketRamrod/`
(generated, not committed): a 1.3-unit sphere (0.85 could barely be seen in the hand, 2026-11-01) of dark steel
(curator's choice), shaded like the vanilla steel
dagger's blade (`SteelDagger:0` from `Skyrim - Meshes1.bsa`: environment-map shader, `SteelDagger.dds`/`_n`/`_m`) with
the blade's own `ShinyDull_e.dds` cubemap and every UV on the blade's flat (0.6084, 0.8955: diffuse 63 grey,
reflection mask 105/255). The first build used the polished edge (diffuse 231, mask 206) under `ShinyBright_e.dds`
and read white in first person (2026-11-01). Per musket, a rod of length muzzle - 12 (21-78 units)
with a wider ramming head, shaded like that musket's barrel (the unskinned shape reaching furthest forward, one texel
near its muzzle; skinned, model-space-normal and vertex-colour flags cleared). Textures are referenced, not copied.

Rendered in both views (side view in 3P, the 1P camera): ball at the pouch, beside the hand and at the muzzle; rod
along the barrel at the grab, out of the muzzle under the fist at both strokes, home under the barrel at the stow.
**Tick `Zenderal - Musket Ramrod Reload.esp` in MO2's plugin list** (the mod alone is not enough). Run order:
`tools/06` → `09` → `10` → `11` → `12` (09 rebuilds the mod folder; 12 needs the two .wavs, see below).

**In game, 2026-11-01** (traced, `SpellAimTrace` 1.4.x): with the plugin unticked, every `AnimObjLoad` named a
missing record and nothing attached. Ticked: both props **load and attach in first and third person** (the game
hangs them on the active view's `AnimObjectL`, hidden until `AnimObjDraw`); the rod showed, the first ball did not.
That ball was a 0.7-unit sphere with Ordo's flying-ball shader (environment map, no cubemap or mask in the mesh) at
the thumb/index **last joints**, i.e. inside the gloved fingertips. Now: the steel shader above, and centred between
the tips (each `FINGER_TIP` 0.7 of its middle segment past the last joint) one radius out from the palm: 2.1-2.8
units from the last joints. Verified in game 2026-11-01 ("Bullet looks good"; by then radius 1.3).

### Loading sounds (`tools/09` + `tools/11` + `tools/12`, 2026-11-02, same MO2 mod, same permission note)

Curator: "add load 7 then load 1 sound effect here when the reload animation puts the ball in the barrel on
Muskets": Motion Array's BBRealSound *Weapon Gun Reload And Load 7* and *... 1* (24-bit / 48 kHz stereo, the
curator's licence; neither the files nor the converted copies are committed). The pistol's pattern
([`PistolRamrodReload`](PistolRamrodReload.md), its tools/06):

- **Events:** `SoundPlay.ZEN_MusketLoad7` as the ball reaches the muzzle (`ball_off`, the frame it is unloaded:
  2.38 s in the shot clip, 1.71 s in the reload clip) and `SoundPlay.ZEN_MusketLoad1` 1.2 s later, once Load 7 has died
  away (it stays within 30 dB of its loudest 50 ms for 1.20 s, as tools/12 measures it). In every shot and reload
  clip, standing and sneak; tools/10 copies them into first person. Both 1hm graphs (1P and 3P) list a bare
  `SoundPlay`, so `SoundPlay.<SNDR>` fires with no behavior patch (the pistol's magic graph lists none, hence its
  Pandora events). The *both reload perks* copies are 1.3x shorter but keep Load 1 1.2 s after Load 7
  (`quick_clip()`): a sound is no shorter when the clip is.
- **Records (tools/11):** SNDR 0x80F/0x810 in `Zenderal - Musket Ramrod Reload.esp`, vanilla's bow nock
  (`WPNBowNockSD`: weapon category, positional output model) verbatim with one file each,
  `Data\Sound\FX\Zenderal\MusketReload\<EditorID>.wav`.
- **Files (tools/12):** 16-bit / 44.1 kHz mono PCM (BloodyCritSound's resampler, channels averaged), with the digital
  silence each file opens and closes on cut to 2 ms (Load 7 starts 0.62 s in, Load 1 0.33 s in), so each sound starts
  on its event. It checks each sound has died away before the next one's event.
- Zodd's own `SoundPlay.WPNCrossbowReload` events (0.97, 1.33 and 2.80 s in the shot clip) are left as they were.

Run `tools/12 <..._Load_7.wav> <..._Load_1.wav>` after every tools/09 run (09 deletes the mod folder, sounds with it).
Built and checked offline 2026-11-02: all 336 shot and reload clips (both views, standing and sneak, the faster copies)
carry both events 1.2 s apart with Load 7 on the ball's unload frame, and every pose is identical to the build before
(backup `E:/Zenderal-backups/2026-11-02-musket-ramrod-pre-sounds/`). **Unverified in game.**

### Reload on demand (`tools/09` `SHOT_ONLY` + `tools/10` + [`MusketHandling`](MusketHandling.md) 1.2.0, 2026-11-03)

Curator: "can we add the reload mechanic we did for pistols, where they don't immediately reload until you press the
fire button again". The pistols' way ([`PistolRamrodReload`](PistolRamrodReload.md), *Reload on demand*) is a staff
cast with no shot; a musket is a crossbow, whose loading the engine itself tracks: the shot clip's `arrowAttach`
(1.567 s in Zodd's) is the beat that loads it (attack state 12 → 9 `kBowAttached`, SpellAimTrace 1.3.0), and
`CrossBow_AttackState` (139) leaves on `attackStop` or on a `reloadStart` the engine sends by code, into
`CrossBow_ReloadState` (140), which plays Zodd's separate reload clip (ball, rod and sounds already fitted). What the
engine does with a musket whose shot did **not** reload it is not known: send `reloadStart` at once (no on-demand
without holding it back), on the next press (on-demand for free), or fire it again unloaded. Holding back or
redirecting would need native code; `ZenMusketHandling.dll` (shipped inside Patch Collection) already hooks the
player's `NotifyAnimationGraph`.

**Shot clips:** the shot clip (both views, standing and crouched, all 14 muskets) is the shot alone (`shorten()`):
Zodd's frames to `SHOT_CUT` 0.74 s (the recoil, 0.27-0.6 s, has settled; from 0.8 s he tips the gun up for the
reload, both hand variants), then that pose eased into the whole clip's last pose (the hip hold the graph plays next)
over `SHOT_BLEND` 0.5 s, the left hand's grip blended and the arm solved onto it (within 0.5 units). No
`arrowAttach`, no props, no reload sounds; 1.24 s in all. First person retargets it as before and blends into the
idle hold over the same 0.5 s. Crouched, both views blend into `sneakmtidle` over those 0.5 s (`settle()`'s
blend-out, otherwise 1 s: with 1 s the first-person crouched shot's hands missed their targets by up to 12.6 units).
`tools/09` takes Zodd's archive as an optional second argument
(the copy in `downloads` was gone on 2026-11-03), and `tools/10` reads the aim-down-sights set from the highest
enabled mod that has it: the standalone `Zenderal - Musket Aim Fix` is gone from the list, and its clips now ship
inside `Zenderal - Patch Collection`. Backup of the build before:
`E:/Zenderal-backups/2026-11-03-musket-ramrod-pre-shot-only/`.

**Result (traced 2026-11-03 16:42, SpellAimTrace 1.4.1, first person): the engine fires an unloaded musket.** Five
shots in 6.8 s (55.30, 57.09, 58.57, 00.37, 02.12), each a full `crossbowAttackStart` → `attackRelease` →
`arrowRelease` → launch, attack state 8 → 10 → 11 → 12 → (13) → 0, with no `reloadStart` and no `arrowAttach`
anywhere: nothing in the engine remembers that the shot did not reload. A press 0.3 s into the short shot clip
(state 12) was taken too. So on-demand needs the press itself redirected: while the musket is empty, drop the
engine's `crossbowAttackStart` and send `reloadStart`, which both 1hm graphs (1P and 3P) accept from
`1HM_Ready_State` (and from `CrossBow_AttackState`) into `CrossBow_ReloadState`; load the gun on that clip's
`reloadStop` (a reload cut short stays empty, as the pistols). Only native code can drop the event (Papyrus can't);
the alternative, unequipping the ammo while empty, juggles the player's ammo.

**Built (2026-11-03): [`MusketHandling`](MusketHandling.md) 1.2.0 does exactly that** (its section 3), in Patch
Collection's copy of the DLL. The short shot clips stay: `SHOT_ONLY` and `[Reload] OnDemand` go together (either one
alone either reloads twice or fires unloaded).

**NPCs keep the whole shot (2026-11-05).** Player report relayed by the curator: "enemy's with muskets still have the
old musket reload speeds. And animation" (curator: "enemies need the same reloads or it is unbalanced"). The ramrod
submods match any actor holding one of the 14 Ordo muskets, and the Flintlock NPC rebuild arms enemies with exactly
those, so from 2026-11-03 musket enemies played the short shot too, and nothing reloads an NPC on demand (Musket
Handling only hooks the player): the engine fired them again every ~1.5 s with no reload. Now `Ramrod <mesh>`
(432500+i, every actor) carries the whole shot again, Zodd's 5.1 s with the ball, ramrod and loading sounds in it, as
before 2026-11-03, and the short shot moved to `Ramrod <mesh>, player` (432530+i, `IsActorBase` `Skyrim.esm` `7` =
the player, Smooth Moveset's own player test) for standing and crouched shots. First person is the player's only and
builds from the player submod. So an NPC needs ~5.1 s a shot, the player 1.24 s shot + 4.43 s reload (3.4 s with
Quick Reload or Rapid Shot, 2.6 s with both: NPCs have neither perk). **Verified in game 2026-11-05** (curator: "it
works").

**Verified in game 2026-11-03** (curator: "Musket reload works
great"; ZenMusketHandling.log: 6 shots and 5 presses after them, each press turned into one reload and loaded on
`reloadStop` 2.46 s later, the both-perks reload by its length; no shot fired empty).

### Sneak (`tools/09` + `tools/10`, same MO2 mod, same permission note)

Curator, 2026-11-01: "can we apply these animations to the stealth / crouch too?" Zodd ships no sneak clips. While
crouched the 1hm graph plays `sneakcrossbow_release` (the shot, which again carries the whole reload) and
`sneakcrossbow_reload`, both from DAR Rifles' sneak hold (`432101`'s `sneakcrossbow_idledrawn`), and after them
`SneakCrossBowLoweredState` -> **`sneakmtidle.hkx`** in both views (the bow's crouched idle too; vanilla wins for the
muskets: Dynamic Bow Animation's sneak idles are `IsEquippedType` 7 = bow only, RaySense Cover is off, Beam Walking
and Goetia's sneak magic don't apply). In that idle the hands hang apart (left hand ~58-68 units from the gun) and the
musket hangs pointing back along the leg; the first-person camera node sits at 86.4 instead of 120.5.

**Third person (`crouch()`, `settle()`):** Zodd's standing shot/reload with every bone outside `NPC Spine2`'s subtree
(root, pelvis, legs, lower spine) from `sneakmtidle` (looped) and Spine2 turned so the chest keeps Zodd's orientation:
arms, gun and props move as standing, just lower (eye ~112 -> ~93). Then the usual slide (its ground clamp now keeps
the crouched gun's lowest point 1 unit up through the muzzle-down swing, up to 18 frames on the long guns), props and
`carry()`. A gun whose butt would reach the ground before its muzzle meets the ramming hand crouches less (10% steps
until the fit holds: `ol_musket_classic` 80%, `ol_musket_long` 90%, the rest 100%). `settle()` holds DAR's sneak
hold until 0.3 s (the shot fires from it), blends into the motion by 0.8 s, and into `sneakmtidle` over the last
second, bone by bone, with the left hand's grip blended relative to the gun only where the far pose holds the gun
(`ON_GUN` 20 units): through the blend-in yes, into the crouched idle no (it lets go, moving steadily away from the
gun). The sneak reload starts and ends on `sneakmtidle`. The sneak raise and hold stay DAR Rifles'.

**First person:** the same motion retargeted from the standing third-person clips (arms relative to the eye are the
same crouched; the standing slide needs no crouched ground clamp), starting on the aim-down-sights set's sneak hold
and ending exactly on the first-person `sneakmtidle`; `left_on_gun()` only through blends whose far pose holds the gun.
The aim-down-sights sneak raise/hold get the `AnimObjectUnequip` safety copies too.

Built and checked offline (2026-11-01): 238 third-person and 294 first-person clips, hands on target in every frame,
both views' left hand sliding along the stock's side through the blend-in (5-8 units out) and away from the gun into
the idle; side-view render of the crouch (kneeling-style, upright chest; the classic's butt just clears the floor).
The last half second turns the gun from Zodd's forward hold to `sneakmtidle`'s backward hang. **Verified in game
2026-11-01** ("confirmed reload works in stealth now").

## Prophecy's pistol talents in the reload script (2026-11-01)

`ZP_FlintlockAmmoPlayerScript` now serves Prophecy's pistol branch ([`Prophecy`](Prophecy.md#firearms-the-pistol-branch-curator-2026-11-01))
without mastering it. `Setup()` (every load) looks up one Prophecy form with `GetFormFromFile`: Fan the Hammer's
marker effect `0xB21`. (Hair Trigger's perk `0xB12` was looked up too until 2026-11-02, for a 1.2 s `HairTriggerDelay`;
the curator took the faster reload out of the talent, which now raises the ricochet chance instead.)

The reload delay is then:
- `FanDelay` 0.1 s while Fan's effect is on;
- otherwise `ReloadDelay` 2 s.

Mod event `ZP_FlintlockReload`, sent by `ZenProphecyRage.dll` on Blade and Barrel's melee hits, loads every pending
hand at once, at most once every `BladeReloadCooldown` 15 s (real time, counted from a reload it actually made,
reset on load; curator 2026-11-01). Prophecy's `PISTOL['BladeReloadCooldown']` only feeds the talent text: change both. Without Prophecy the lookups are None and nothing changes.

No property was added: the new values are `AutoReadOnly`. The loaded copy is Patch Collection's `Scripts/` (the old
one is backed up in `E:/Zenderal-backups/pistol-talents-2026-11-01`). Compiled; unverified in game.

**Holster (2026-11-02, for [`PistolRamrodReload`](PistolRamrodReload.md)'s two-pistol reload):** mod event
`ZP_FlintlockHolster` (strArg the hand, "0" left / "1" right; numArg seconds) holds that hand's charge at 0 while the
other gun's reload has it tucked in the belt, so it cannot fire, and fills it again afterwards if the same gun is still
in that hand and loaded (per-hand tokens: a newer holster owns the release). `Setup` (every load) fills any loaded gun
it finds at 0, so a save made mid-reload cannot leave a loaded gun dead. Only this script writes charge.

**Overlapping holsters and loading by animation (2026-11-02):**
- **Holsters:** each records its end time (`holsterUntilL/R`, real time), and only the one that ends last gives the
  charge back. A gun loaded while holstered (`TryLoad`) is marked loaded with its charge left at 0 until then. Before
  this, the timer refilled a tucked gun mid-reload. The end times are reset on every load, since real time restarts
  with the game.
- **Loading by animation** (curator: a dagger attack cut the reload short and the timer loaded the gun anyway):
  `AnimatedReload` decides, per shot, whether Pistol Ramrod Reload plays a reload for it. That needs all of:
  - the pistol carries Loop's keyword, with both Loop's plugin and the reload's present;
  - the player isn't mounted, and Fan the Hammer's effect is off (Hair Trigger was excluded too for a while on
    2026-11-02, then given faster twins, then its faster reload was dropped from the talent altogether:
    [`PistolRamrodReload`](PistolRamrodReload.md#hair-trigger-2026-11-02));
  - the other hand is empty, holds a one-handed melee weapon, or holds a Loop pistol, or (a right-hand gun, since
    2026-11-03) a shield (`TYPE_SHIELD` 10; Pistol Ramrod Reload slings it on the back), or (since 2026-11-05) a
    torch (`TYPE_TORCH` 11; Pistol Ramrod Reload lowers it into a loop on the belt, still lit, and takes it back,
    [`PistolRamrodReload`](PistolRamrodReload.md#a-torch-in-the-other-hand-2026-11-05)), or (since 2026-11-07, either
    hand) a spell (`TYPE_SPELL` 9; the spell hand loads and rams,
    [`PistolRamrodReload`](PistolRamrodReload.md#a-spell-in-the-other-hand-2026-11-07));
  - the player's graph has the `ZenPistolLoadedL` / `ZenPistolLoadedR` events (registered at each shot).

  When it does, the gun loads on that event, sent where the clip rams the ball home. A reload cut short leaves the gun
  empty, with no timer. Each hand has its own deadline (`loadAtL/R`, 0 = none, `ScheduleLoad`); the old single
  `RegisterForSingleUpdate` let one hand's timer load the other.
- **No reload by itself (2026-11-03,** curator: "Shields + pistol are allowing players to infinitely shoot with no
  reload"**):** every other shot kept the 2 s timer from the shot, so with a shield (or a spell or torch) in the other
  hand the gun loaded itself while Loop's shot played and fired every ~2 s. Now only Fan the Hammer starts a timer at
  the shot (`FanDelay`, the power's text). Elsewhere, with no reload clip, the attack button on the empty gun clicks
  and starts `ReloadDelay`'s timer (`OnControlDown`; a second press while it runs does nothing), and a save keeps no
  timer (`Setup`: every pending gun waits for the press). Shields themselves now get a clip (above). Whether the
  reload plays a clip or runs the timer is decided at the press (`OnControlDown`), from what the other hand holds then.
- **Put away empty (2026-11-03,** curator: "users are also exploiting unequipping muskets and pistols to avoid the
  reload"**):** `Sync` loaded every pistol it saw equipped from a bullet, so unequipping a fired pistol and equipping
  it again reloaded it at once. Now a fired, unloaded pistol leaving a hand is kept in `stowedGuns` / `stowedCounts`
  (64 kinds; by base form, with a count, since two of the same pistol are told apart only by number). Taken up again
  it is empty (charge 0, pending, no bullet taken) if every one of its form out of both hands is; the engine doesn't
  say which of several alike it equipped, so a loaded one is assumed while the player has any, and counts are capped
  by what the player still has (one sold or dropped counts as a loaded one gone). It then reloads on the attack
  button like after a shot. Both hands' outgoing pistols are put away before either incoming one is looked at, so an
  empty gun moved to the other hand stays empty. A loaded pistol still gives its bullet back when unequipped and takes
  one when equipped. **First test (curator, same day): after a musket swap the right pistol of a pair came back
  loaded every time** (Papyrus log: `RightItemCharge 0 -> 2` right after each musket put-away, the left reloaded by
  its clip). With the same pistol in both hands coming in together, the left was looked at first and counted the
  right's copy as already in hand, so it capped the two empty ones to one and took it, and the right found none.
  Fixed: each incoming pistol's pool leaves out the other hand's copy only if that one was in hand already or came in
  just before it. `put away empty` / `taken up` lines now go to the Papyrus log (`[ZP Flintlock]`) whatever
  `DebugMode` says. Muskets: the same in [`MusketHandling`](MusketHandling.md) 1.3.0. **Verified in game 2026-11-03**
  (curator, musket ↔ two pistols swaps after firing all three: "works").
- **Reload on fire** (curator: something to prompt the shot denial and the reload start): `OnControlDown` on that
  hand's attack (`Left/Right Attack/Block`), with the gun empty and reloading by animation, plays a click
  (`UILockpickingCylinderStop 0C1912`) and sends `ZP_PistolDryReload`. Pistol Ramrod Reload then plays the reload.
  It doesn't fire:
  - while that hand's reload still plays (`IsCastingLeft`/`Right`: 1 through a full reload, 0 once an attack cuts it,
    traced);
  - within `DRY_LOCK` (0.5 s) of the last request (one request per press; the cast is on ~0.1 s after it);
  - while the gun is holstered;
  - while the other pistol casts (fires or reloads): one reload at a time.

  Since 2026-11-02 this is the only way a reload starts: a shot plays Loop's shot alone, leaving the other hand free.
  The request is gated in Pistol Ramrod Reload, with OAR on `fZenPistolReloadL/R`.

  The requested reload is a cast with no shot. Its spell-fire action reaches `OnActorAction` like a shot, and the code
  logs it as `reload started (asked for, no shot)` because the gun is already pending. No projectile launches, because
  the gun has no charge. The clip's loaded event then loads the gun.

  **No timer behind it.** The first build loaded the gun anyway if the reload wasn't seen starting within 1.6 s
  (`DRY_CHECK`). In game, pressing fire and then attacking at once cut the requested reload before its fire point, and
  that timer loaded the gun 1.6 s later: the exploit this was built against. A request the graph refuses (mid-attack)
  now leaves the gun empty for the next press. `OnAnimationEvent` takes only the two loaded events by name. The first
  build's `AnimObjLoad` registration lives on in saves, and is dropped in `Setup`.

The loaded copy is Patch Collection's; the previous copy is in `E:/Zenderal-backups/2026-11-02-flintlock-load-on-anim`.
Compiled; unverified in game.

## No cast time: hold to aim, release to fire (2026-11-02)

Curator: "remove the casting time to fire from pistols", "hold left click = aim, release left click fires". Every
pistol's staff enchantment had the pack's `ChargeTime` 0.7. Traced, a real shot went: cast start, precharge (the gun
raised, `MLh_PreChargeOut` 0.5 s), the engine's `MLh_SpellReady_event` at 0.7 s, then the release on the button's
release, with the bullet 0.334 s into the release clip (`MLh_SpellFire_Event`, the staff release state's own trigger).
`tools/01` `CHARGE_TIME` now writes 0.0 into all 12 enchantments (Reversal Shadow's copy follows through its
`tools/02`). The cast is ready as it starts, so a held button aims and its release fires, with no minimum hold. NPCs
use the same enchantments.

Still there: the 0.334 s from release to bullet. That trigger lives in the shared staff release clip generator, and
Loop's shot clip times its recoil to it, so moving it would change every staff and need trimmed shot clips.

Built and byte-compared with the deployed copy: only the 12 `ChargeTime` floats differ (0.7 → 0.0). Deployed to Patch
Collection (previous copy in `E:/Zenderal-backups/2026-11-02-pistol-charge-time`). Not opened in xEdit; unverified in
game.

`DebugMode` is False again since 2026-11-02 (the `[Flintlock]` notifications were for the reload tests). Deployed to
Patch Collection.
