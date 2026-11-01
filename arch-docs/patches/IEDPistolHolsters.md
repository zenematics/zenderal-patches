# IEDPistolHolsters

- **Source:** `src/IEDPistolHolsters/`
- **Ships:** *(no plugin)* IED ExtraGearNodes file `SKSE/Plugins/IED/SkeletonExtensions/ExtraGearNodes/00300_ZenderalPistolHolsters.json`
  (committed), plus a generated IED export `SKSE/Plugins/IED/Exports/Zenderal - Pistol Holsters.json` (the curator's
  config + the changes below; not committed, not in the release). MO2 mod `Zenderal - IED Pistol Holsters`, directly
  above `Immersive Equipment Displays` (adds files only, no conflicts).
- **FormID block:** _(none)_

## The problem

Immersive Equipment Displays (1.7.4, AE build `Immersive Equipment Displays - 1.7.104 Update`) could only place the
flintlock pistols together with staves, so a good spot for one was a bad spot for the other.

**Why they share** (from IED's and Simple Dual Sheath's source, `SlavicPotato/ied-dev` and `SlavicPotato/SimpleDualSheath`):

- IED's display slots are fixed by weapon type (`Data.h`: `WEAPON_TYPE::kStaff` → `ObjectSlot::kStaff`). The pistols
  are staff-type WEAPs ([`FlintlockOverhaul`](FlintlockOverhaul.md), [`LoopPistolAnims`](LoopPistolAnims.md)), and
  changing the type would break their animations and reload.
- The *equipped, sheathed* pistol hangs on the gear node `WeaponStaff` (right hand) / `WeaponStaffLeft` (left): SDS's
  staff-attach hook (`GetWeaponStaffSlotNode_Hook`, `[Staff] Flags=Player|NPC|Right` in the list) picks the node by
  weapon type. The equipped model's `Prn = SHIELD` (the `LoopPistols` statics) plays no part.
- IED moves equipment by re-parenting those gear nodes (Gear nodes → Placement). The curator's export
  `Gunslinger 2.json` (2026-10-21) did exactly that for the player: `WeaponStaff` → `MOV BOLTXP32`,
  `WeaponStaffLeft` → `MOV BOLTABQ` (XPMSE's bolt-quiver nodes, with CME offsets), which put the player's staves on
  the hips too.

## The fix: IED config only

IED can already do this with its own config. No IED file is edited, and no WEAP changes.

1. **Own holster nodes.** `00300_ZenderalPistolHolsters.json` creates `CME/MOV ZenPistolRight` (parent `Bolt Quiver`,
   MOV transform read from `MOV BOLTXP32`, end node read from `WeaponStaff`) and `ZenPistolLeft` (parent
   `Aesthetic Bolt Quiver`, `MOV BOLTABQ`, `WeaponStaffLeft`). It matches only skeletons that have those nodes
   (`obj_match`; XPMSE). XPMSE's `CME BOLTXP32`/`CME BOLTABQ` are identity (read from XPMSE's `skeleton.nif` with
   PyNifly), so a node with the same parent and MOV transform, plus the same CME offset, lands on the same spot. Extra
   nodes show up in IED's gear positioning list and as placement targets (`NodeOverrideData::m_mov`).
2. **Placement override.** On `WeaponStaff`/`WeaponStaffLeft`, the first placement override is
   *Hand (right / left) has keyword `Pistol_Animation_By_Loop 0x801:Pistol animation by Loop.esp`* → `MOV ZenPistol*`
   (condition type 25 `Hand`, `kMatchLeftHand` = bit 7: it tests the process manager's equipped object in that hand,
   `match_hand_item`). The base target stays the staff spot. It goes into default_player, default_npc and every
   actor/NPC/race entry that already places these nodes, because IED takes a node's placement from the first class
   that has one (actor > NPC > race > global).
3. **Migration of the curator's workaround.** An entry whose base target was `MOV BOLTXP32`/`MOV BOLTABQ` has its
   `CME BOLT*` transform copied to `CME ZenPistol*` and its base target cleared. Pistols stay where they were and
   staves go back to the default staff node. default_player/default_npc get the same CME transform, so NPC pistols
   holster where the player's do.
4. **Displays.** The staff slots `staff`/`staff_l` get a last equipment override, *this item has the keyword* (type 2
   `Keyword`, `kMatchThisItem` = bit 10, evaluated by `get_equipment_override_fp` against the displayed form) → node
   `ZenPistolRight`/`Left`. A carried, unequipped pistol is displayed in the holster, not on the staff spot. It sits
   after the "Disable no armor / with cuffs" overrides, so those still win.

The keyword is on all 13 pistols: Loop's 4 Hunter Pistols and Reversal Shadow's own carry it, and the pack's 8 get it
through KID (`AdventurerFlintlockPack_PABL_KID.ini`, `added to 8/588`). Loop's 4 Hunter Crossbows (staves, recipes
hidden by the Flintlock Overhaul) carry it too, so they would holster as pistols.

## Applying it to a save

IED keeps its whole config in the SKSE co-save. A file only reaches a running game through File → Import.

1. MO2 and the game closed: run `python src/IEDPistolHolsters/tools/01-build-ied-pistol-holsters.py`. It reads the
   newest export in `overwrite/SKSE/Plugins/IED/Exports` (or `--source <file>`) and writes the mod. **Export your
   current config from IED first** (File → Export) if it changed after the last export, or the import rolls it back.
2. In game: IED (Backspace) → File → Import → `Zenderal - Pistol Holsters`, **without Merge**. IED's merge replaces
   whole classes (`DoImportMerge`), so it is no safer.
3. Position: Gear nodes → Positions → *Pistol holster (Zenderal)* / *left* (CME ZenPistol*); staves keep
   `WeaponStaff`'s own entry. Placement for staves: Gear nodes → Placement → WeaponStaff base target.
4. New games use `DefaultConfigUser.json` (`overwrite/SKSE/Plugins/IED`, not this mod). Once it looks right, save the
   current config as the default from IED, or new games start without the overrides. The ExtraGearNodes file alone
   only adds the nodes.

Rerun `tools/01` on a fresh export whenever the IED config is redone. It strips its own overrides (by description)
before re-adding them, so reruns don't stack.

## Status

Generated from `Gunslinger 2.json` and installed in `Ultra` on 2026-10-29 (`modlist.txt` backup in
`E:/Zenderal-backups/2026-10-29-ied-pistol-holsters`). The JSON shapes follow IED's parsers (`JSONConfigNodeOverride*`,
`JSONEquipmentOverrideConditionParser`, `JSONConfigExtraNodeEntryParser`).

Imported in game and saved as the list default the same day. IED wrote `overwrite/SKSE/Plugins/IED/DefaultConfigUser.json`
at 14:26, after the 14:15 export. It holds all 24 placement and 8 display overrides, and the curator moved the
player's `CME ZenPistolRight`/`Left` in game (right `[43.5, -9, 12]`, left `[-37.5, -5.5, 21]`, new left rotation).
That means IED created the holster nodes and offered them for positioning. **Verified in game 2026-10-29** (curator:
"all working"). **Note:** the saved default is newer than the export, so never copy
the export over `DefaultConfigUser.json`. That would undo the in-game positioning.

**Hotfix miss (2026-10-29):** the hotfix shipped the nodes and the export but **not** the default, because IED saved
`DefaultConfigUser.json` into MO2's `overwrite`, which Wabbajack never ships. Players' pistols stayed on the back. Fixed
by copying it into the mod (`SKSE/Plugins/IED/DefaultConfigUser.json`, md5 `999a4697…`). **Whenever the default is
saved again in game, copy it from `overwrite` into the mod before compiling.** It only applies to new games: an
existing save keeps the IED config in its co-save and needs File → Import → `Zenderal - Pistol Holsters`.
