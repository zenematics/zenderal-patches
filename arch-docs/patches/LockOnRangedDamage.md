# LockOnRangedDamage → `Zenderal - Lock-On Ranged Damage.esp`

- **Status:** built 2026-11-16, Spriggit round trip identical. **Unverified in game.**
- **Shape:** patch, ESL, HEDR 1.7. One new PERK (`0x800`) + one MGEF override (TDM's `000804`).
- **Masters:** Skyrim.esm, Update.esm, Enderal - Forgotten Stories.esm, `TrueDirectionalMovement.esp`,
  `Zenderal - Flintlock Overhaul.esp`.
- **Load after** `TrueDirectionalMovement.esp` and `Zenderal - Flintlock Overhaul.esp` (any position after both).
- **Ships in:** `Zenderal - Patch Collection` since 2.6 (2026-11-16); the standalone MO2 mod and its Include rule
  are gone (folder in `E:/Zenderal-backups/2026-11-16-compile-prep-2`). Deploy rebuilds into Patch Collection.

## The request

Curator, 2026-11-16: shooting a bow, crossbow, musket or pistol while locked on deals 60% damage. Manual aim keeps
full damage.

The list's TDM aims a locked shot for the player. `uTargetLockArrowAimType` and `uTargetLockMissileAimType` are 1
(predictive aim, TDM's default). `Zenderal - Settings`' `TrueDirectionalMovement.ini` does not change them.

## How TDM signals the lock

While a target lock is on, TDM puts its ability `TDM_TargetLockSpell 000805` on the player. The ability carries the
dummy effect `TDM_TargetLock 000804` (Script archetype, no script). TDM's page documents the effect for DAR
conditions. The DLL (2.3.1) looks the spell up by ID at load: there is a `lea` of the string
`TrueDirectionalMovement.esp`, then `mov edx, 0x805`, then the form lookup (RVA `0x428dd`). TDM also sets the
graph variable `TDM_TargetLock`, which this patch does not use.

## Mechanism

TDM's effect `000804` is copied verbatim, with `PerkToApply` set to our hidden perk `ZP_LockOnRangedDamage 0x800`.
A perk applied by an effect is added and removed with the effect, so the perk is on the player exactly while the
lock is on. There is no script and no quest. The list already uses this pattern in Zen Traits, Kata's book perks,
Reforged Directional Combat's dist effects and base Enderal's `_00E_Frozen_ME`. No plugin in the Ultra load order
masters `TrueDirectionalMovement.esp` (scanned 2026-11-16), so this is the only override of `000804`. Only the
player gets the effect, so NPCs are unaffected.

The perk has three entries, each Multiply `LOCKED_DAMAGE` (0.6):

| Entry point | Condition | Covers |
|---|---|---|
| `ModAttackDamage` | weapon (tab 1) has `WeapTypeBow 01E715` | bows, crossbows, Ordo muskets (all carry the keyword, see [`TraitsRework`](TraitsRework.md)'s Gunslinger) |
| `CalculateMyCriticalHitDamage` | same | the crit part of those hits |
| `ModSpellMagnitude` | spell (tab 1) has `ZP_FlintlockShot 00080C` | pistols: staves whose damage is the shot enchantment's magnitude, the same condition [`FlintlockOverhaul`](FlintlockOverhaul.md)'s scaling perk `00080D` uses |

The condition is read when the damage is worked out. That happens when an arrow or ball hits, and when a pistol
shot is cast. A shot fired while locked that lands after the lock is released does full damage, and the reverse also
holds.

**Also scaled:** a bash made with a bow, crossbow or musket while locked (`ModAttackDamage` does not tell a bash
from a shot). Reversal Shadow's Witch Bolt is scaled too, because its shot keeps `ZP_FlintlockShot`. The Flintlock
scaling perk already behaves the same way.

**Not scaled:** talent effects that ride on a hit (Deadeye's bleed, Arcane Arsenal's element, Ice Shot's freeze),
ammo explosions (Flame Musket Balls), and anything else outside these three entry points.

**Order (open):** the list's flat Add entries on bow hits are Enderal's Master of the Bowstring (+1) and EGO's silver
arrows (+5 against undead). Both are priority 0, like these entries. It is not established whether they are added
before or after the ×0.6. The difference is at most 2 points a hit.

## Regenerating

`python -I src/LockOnRangedDamage/tools/01-build-lock-on-ranged-damage.py` writes everything under
`LockOnRangedDamageESP/` from `reference/mods/TDM/`. The reference was re-serialized from the installed TDM 2.3.1 on
2026-11-16 and matched byte for byte. The generator asserts that exactly one line (`PerkToApply`) is added. It
refuses to run if TDM's effect already applies a perk.

**After a TDM update:** re-serialize `TrueDirectionalMovement.esp` into `reference/mods/TDM/`, rerun the generator,
and check the DLL still looks up `0x805`.

## Testing

In game, third person, a bow or musket against the same enemy: shoot without lock-on, then with it. The locked hit
should take about 60% as much Health. `player.hasperk <load-order ID>800` is 1 only while locked (the ID depends on
the ESL slot). For pistols, do the same with any flintlock pistol.
