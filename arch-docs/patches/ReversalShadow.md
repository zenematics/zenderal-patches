# ReversalShadow

- **Source:** `src/ReversalShadow/`
- **Ships:** `Zenderal - Reversal Shadow.esp` + 2 generated meshes + 1 generated texture (not committed)
- **FormID block:** `0x800–0x807`
- **Pillar:** modern combat (curator's request, 2026-10-18)

## What it does

**Reversal Shadow** is a black-and-silver flintlock pistol whose shot also casts Triumvirate's
**Witch Bolt** on whatever it hits. It is the Priest's Dueling Pistol (`PMDuelingPistol02 000817`,
A Gentleman's Flintlock Armoury, as the Flintlock Overhaul rebuilt it) with a new enchantment and
a recoloured texture.

| FormKey | Record | From |
|---|---|---|
| `800` | WEAP `ZP_ReversalShadow` "Reversal Shadow" | `000817` verbatim; Name, Model, ObjectEffect, FirstPersonModel, Value 700 → 2400, Damage 12 → 30 / critical 12 → 20 (the top pistol, `PMFlintlockPistool04 00083A`), + Loop keyword |
| `801` | STAT `1stPersonZP_ReversalShadow` | `1stPersonPMDuelingPistol02 00080A` verbatim; Model → `ReversalShadow1st.nif` |
| `802` | ENCH `ZP_ReversalShadowShot` "Witch Bolt Shot" | `ZP_FlintlockShot_PriestsDuelingPistol 000805`, bullet magnitude 14.4 → 36.0 (1.2 × Damage, the Flintlock Overhaul's rule) + Witch Bolt's two effects |
| `803` | MGEF `ZP_ReversalShadowBullet` | `PMPistolShot 000802` verbatim; BaseCost 1.2 → 50; description "Fires a Flintlock bullet." (was "Fires a musket ball"; the full stop separates it from Witch Bolt's text on the item card) |
| `804` | COBJ `ZP_RecipeReversalShadow` | forge: Priest's Dueling Pistol + 2 Silver Ingots `05ACE3`, Smithing ≥ 50 |
| `805` | COBJ `ZP_TemperReversalShadow` | `PMTemperDueling02 000830` verbatim, new product |
| override | FLST `ZP_FlintlockWeapons 000802:Zenderal - Flintlock Overhaul.esp` | the Flintlock Overhaul's 8 pistols + `800` |
| `806` | MGEF `ZP_EldritchBlastWitchBoltBonus` "Witch Bolt Resonance" | `TVR_Warlock_Balefire_Effect_EldritchBlast 19B464` verbatim; flat (no `PowerAffectsMagnitude`, DualCastScale 1), BaseCost 0, no hit art / imagespace, no `IsBalefireSpell` keyword |
| override | SPEL `TVR_Warlock_D000_Spell_EldritchBlast 19B465:Triumvirate` | **Zenderal - Magic Patches' copy** (cost ladder) + `806` under a Witch Bolt condition |
| override | ENCH `TVR_Warlock_D000_StaffEnchantment_EldritchBlast 419B32:Triumvirate` | Triumvirate's record + `806`; `NoAutoCalc` added so the charge cost stays 32 |

**Witch Bolt** = Triumvirate's `TVR_Warlock_D050_Spell_WitchBolt 1AF89A`. Its damage effect
`TVR_Warlock_Balefire_Effect_WitchBolt 1BEBB6` (3 raw damage/s for 60 s, `NoRecast` so repeated shots
refresh rather than stack) and `TVR_Warlock_Balefire_Effect_BindSpirit_FFAimed 19B46E` (1000 / 60 s) are
copied at the values Triumvirate's own Witch Bolt staff enchantment `419B35` uses. Triumvirate is the
winner of both effects in the magic dataset; no plugin overrides them.

**Why the bullet MGEF is copied (`803`).** An enchantment's projectile, release sound and casting art
come from its **costliest** effect. Witch Bolt's effect costs 168; the stock bullet ~23
(1.2 × 14.4^1.1), so the shot would have flown as Witch Bolt's dark-fire bolt with no gunshot. The
copy raises only BaseCost (cost ≈ 940); the enchantment is `NoAutoCalc` (cost 1 per shot), so nothing
else reads it. [community rule, unverified in game here]

**Archery scaling also hits Witch Bolt.** `ZP_FlintlockArcheryScaling 00080D` conditions on
`EPMagic_SpellHasKeyword ZP_FlintlockShot 00080C`, which `803` keeps — and that condition is true for
every effect of the shot, so Witch Bolt's 3/s is scaled too (×0.5 at Archery 0, ×1.5 at Archery 100,
before talents). Accepted as a feature; drop `803`'s keyword-scaling only by moving Witch Bolt to a
separate spell.

**Reload and animations.** The Flintlock Overhaul's `ZP_FlintlockAmmoPlayerScript` only loads/refills
weapons in `ZP_FlintlockWeapons`, so this plugin overrides that list (**this plugin now owns
`000802`**: if the Flintlock Overhaul ever changes its list, rerun `tools/02`, which rebuilds the
override from it). The WEAP carries `Pistol_Animation_By_Loop 000801:Pistol animation by Loop.esp`,
which the [`LoopPistolAnims`](LoopPistolAnims.md) OAR submods also test. **In game (2026-10-18) the keyword alone did
not select Loop's animations** (OAR log clean; KID log shows the keyword live), so LoopPistolAnims' `tools/01` now
also matches `800` by form (`EXTRA_PISTOLS`), the path verified in game for the other 8. Cause of the keyword
miss not found.

**Black and silver (`tools/01`).** `FlintBlackBase_d.dds` (uncompressed 24-bit BGR, 12 mips) is
recoloured per mip level: saturated bright pixels (the copper, green and red inlays) → cool silver,
everything else → luminance × 0.35 (ebony stock, blackened steel). The `_m` environment mask already
marks the inlays reflective, so they read as polished silver. The two meshes are byte copies of
`FlintlockPistol02.nif` (world model) and Loop's rotated copy (the equipped model, see LoopPistolAnims)
with one same-length string changed, `flintblackbase_d.dds` → `flintrevshadow_d.dds`; the script
asserts one hit each. Outputs go straight into the MO2 mod `Zenderal - Reversal Shadow`.

## Placed at Old Crosswatch (2026-10-18)

Curator's request: one Reversal Shadow lies on the **lower board of the shelf at Old Crosswatch**
(`CommonShelf04 0CE786`, ref `0F916D:Skyrim.esm`, exterior cell `001F20` (Vyn −21, 3), next to the
chest). REFR `807`, base `800`, at `-84394.278, 14275.100, 5505.371`, rotation Z `3.8939877`.

- **Position from the mesh, not by eye.** The winning shelf mesh is Skyrim 3D Furniture's (above SMIM in
  `modlist.txt`); measured with PyNifly its lower board tops out at z ≈ 17.5, interior x ±68 / y ±27.
  The pistol's world model lies flat in its own XY plane (x −7…16.7, y −9.3…38.6, z −2.9…3.2), so it only
  turns about Z: barrel along the shelf, centred, 0.5 above the board for Havok to settle. `tools/02`
  asserts every corner stays inside the shelf. Bethesda Z rotation is clockwise from +Y.
- **Nothing overrides the shelf ref** (live scan of profile `Ultra`); the console's `Ref last changed by:
  Skyrim.esm` agrees.
- **Cell header = Forts of Enderal's**, the cell's winner (`Skyrim → FS → EGO → Forts of Enderal`);
  the four headers differ only in `Grid.Flags`. Masters `Forts of Enderal.esp` for that. **This plugin
  now owns `CELL 001F20`'s header.**
- **WRLD header** = Forts' copy truncated before `TopCell` (four scaffolding files, see
  [`spriggit.md`](../workspace/spriggit.md)). 75 plugins touch Vyn's header; `BristlebacksInEnderal.esp`
  (395) loads after this one (394) and still wins it. If this plugin ever becomes the last Vyn overrider,
  its header would win instead — recheck then.
- `tools/02` reads `reference/mods/FortsOfEnderal/` (spriggit-decompile-reference, made 2026-10-18).
- **In game 2026-10-18 it was there but tilted**: Havok settled it propped on the grip. The REFR now carries
  **Don't Havok Settle** (`0x20000000`) and sits 0.1 above the board, so it stays flat as placed until
  touched. A save that already loaded the cell keeps the settled pose; test on a save that has not.
  **[unverified in game]** after the change.

## Eldritch Blast bonus (2026-10-18)

Curator's request: **while Witch Bolt is on a target, Eldritch Blast does 20 more damage.** The Eldritch
Blast spell and Triumvirate's Eldritch Blast staff enchantment each get a fourth/third effect entry, `806`,
magnitude 20 over 1 s (the same shape as Eldritch Blast's own 20), conditioned on
`HasMagicEffect TVR_Warlock_Balefire_Effect_WitchBolt 1BEBB6 == 1`. On a fire-and-forget spell an effect's
condition Subject is the **target**, so the entry only applies to an actor Witch Bolt is burning, whether
from this pistol or from the Witch Bolt spell. **[unverified in game]**

- **Flat +20:** the bonus does not scale with power or dual casting; Eldritch Blast's own 20 still does.
- **Not a second balefire hit:** the copy drops `TVR_Balefire_Keyword_IsBalefireSpell 19B468`, the hit
  art and the imagespace modifier. Perks that test the *spell* for that keyword still see Eldritch
  Blast's own effect.
- **Not the costliest effect:** BaseCost 0, so Eldritch Blast's projectile, sound and casting art are unchanged.
- **Ownership:** `19B465` is now won by this plugin, built from Magic Patches' YAML (which only changed
  cost/flags). **Rerun `tools/02` after Magic Patches regenerates its Triumvirate spells**, or this
  override reverts the new cost. Masters `Zenderal - Magic Patches.esp` to force the load order.
- `tools/02` reads `reference/mods/Triumvirate/` (spriggit-decompile-reference of the installed
  `Triumvirate - Mage Archetypes.esp`, made 2026-10-18).

## Regenerate

```
python src/ReversalShadow/tools/01-build-assets.py      # meshes + texture into the MO2 mod
python src/ReversalShadow/tools/02-build-records.py     # YAML from the Flintlock Overhaul's records
```

Rerun `tools/02` after the Flintlock Overhaul's `tools/01` (damage / Loop meshes) changes the Priest's
pistol, and `tools/01` after LoopPistolAnims' `tools/02` regenerates its rotated meshes.

## Status

Built 2026-10-18 (deserializes clean, HEDR 1.7, ESL). First in-game look: Loop animations missing (fixed by form match
above, unverified); damage raised to the top tier on request. **Fix not yet run in game.** To check: craft it
(or `help "Reversal Shadow"` → `player.additem`), confirm the shot shows the musket ball and gunshot
sound, the target burns with Witch Bolt for 60 s, the pistol reloads with a Flintlock Bullet, and the
texture is black and silver in both hands. Load after `Zenderal - Flintlock Overhaul.esp`.
