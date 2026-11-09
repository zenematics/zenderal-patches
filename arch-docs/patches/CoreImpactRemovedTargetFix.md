# CoreImpactRemovedTargetFix

- **Source:** `src/CoreImpactRemovedTargetFix/tools/01-patch-dll.py`. It is a byte patch that asserts every original
  byte. CIF is GPL-3.0 (source: `github.com/Seb263/SkyrimSE_CoreImpactFramework`), so this script is the published
  change.
- **Ships:** MO2 mod *Core Impact Framework - Removed Target Fix (Zenderal)*, which must **outrank** *Core Impact
  Framework (CIF)*: below it in MO2's left pane, above it in `modlist.txt`. It holds
  `SKSE/Plugins/CoreImpactFramework.dll`, a patched copy that is generated and not committed. It has a Wabbajack
  `Include` rule, because the patched DLL matches no download.
- **FormID block:** _(none)_

## Why (2026-11-08)

**The crash:** a player (keithsmyas) shot an undead in the Old Aisolon tar pit (`UndercityAltAisolonL1 0FF034`) with a
pistol, and the game crashed. The log showed:

- `EXCEPTION_ACCESS_VIOLATION` at `SkyrimSE.exe+06AEF73`: `Actor::IsBlocking` (ID 37952+0x13) reading
  `[this+0x38]` with `this` = null.
- CIF's frames under it (`CoreImpactFramework.dll+0029C13` and `+519A5`), all inside a projectile impact
  (IDs 44204–44206, then 38786 / 38668).
- The bullet (`MissileProjectile` "Bullet", AdventurerFlintlockPack) had hit a **Fleshless Lost One whose FormID was
  already `0x00000000`**. Its base had been changed by `mihailancientskeletons.esp`. A FormID of 0 means the game had
  already torn the actor down by the time the impact was processed.

**The cause, read from CIF's source and confirmed in the 2.0.7 binary:** `DeferredHitFunctions::SetDeferredHit
(Projectile*, Actor*, bool)` in `src/Core/DeferredHit.hpp` (binary `+299A4`) runs on every projectile hit.

```cpp
auto* victim = MiscUtils::GetValidReference<RE::Actor>(victimRef);   // null for FormID 0 / FFFFFFFF or Deleted
auto* attacker = MiscUtils::ResolveHandle<RE::Actor>(projectileRuntime.shooter);
if (!attacker) return;
...
if (victim->IsBlocking()) {                                          // no null check
```

- **The check that nulls it:** `GetValidReference` is inlined at `+299FB`–`+29A29`. It returns null when the reference
  is not a Character (form type `0x3E`), when its FormID is 0 or `FFFFFFFF`, or when it has the Deleted flag (`0x20`).
- **The missing check:** nothing tests `victim` before `IsBlocking`. The magic-only branch above it does test it
  (`else if (victim)`).
- **Still in 2.0.9:** the bug is unchanged in upstream 2.0.9 (commit `562ac4d`, 2026-10-20).
- **The only buggy caller:** CIF's other `IsBlocking` caller (`+293C8`, `MiscEffect.hpp`) checks for null first. The
  other inlined copies of the same check (`+27EC4`, `+8FE6C`) leave on a rejected target.

**Why the skeleton had FormID 0 is unknown.** Enderal's Old Aisolon boss script only enables its swarm and never
deletes it, and Lost Ones Revised ships no scripts.

- **A possible link:** undead whose limbs our Dismembering Framework patches cut off already appear in a freed-actor
  crash (`0FDDB2D`, see [`EnemyDensity.md`](EnemyDensity.md)). Nothing ties this crash to that one yet.
- **If it repeats:** ask for `DismemberingFramework.log` and `CoreImpactFramework.log`.

## The patch

The patch rewrites the 16 bytes at `+0x29A1C`–`+0x29A2B`.

| | Before | After |
|---|---|---|
| `+29A1C` | `mov ebx, r13d` | `mov rbx, rdx` |
| `+29A1F` | `cmp r8b, 0x3E` | `jmp +29A2C` (valid target: carry on as before) |
| `+29A21`–`+29A28` | `cmove rbx, rdx` / `jmp +29A2C` | `jmp +29DF9` (rejected target: leave), 3 × `int3` |
| `+29A29` | `mov rbx, r13` (victim = null) | `jmp +29A21` |
| `+29A2B` | — | `int3` |

**Why it is safe:**

- **Same value:** `mov rbx, rdx` gives the value the old `cmove` gave. That point is reached only with `rdx` non-zero,
  which happens only when the form type was `0x3E`, and nothing reads the flags those instructions set.
- **An exit the function already uses:** `+29DF9` is the function's own epilogue (cookie check, restore, `ret`). The
  function already jumps there from the same frame when it is given no target (`+299E6`) or no shooter (`+29A64`,
  `+29A83`).
- **The behaviour upstream would add:** this is `if (!victim) return;`, which is the upstream fix too.
- **The caller is fine with it:** `+519A0` ignores the return value. Next it looks the target up by FormID
  (`+2A978`), which returns early for 0.

**Checks the tool asserts:**

- the source md5 and timestamp;
- the replaced bytes, the exit's bytes, and the crash call's bytes;
- that the site, the exit and the call are in the same `.pdata` function;
- that the only branches anywhere in the DLL landing inside the rewritten bytes are the three rejecting ones
  (`+29A06`, `+29A10`, `+29A1A`), all at `+29A29`;
- that no base relocation falls in the range;
- by disassembling the result, that every jump lands where intended.

It changes 15 bytes. The PE checksum is 0 in the original, and stays 0.

## Keeping it right

- **CIF on Nexus is at 2.0.9; the list ships 2.0.7.** The tool refuses any other build (md5 check). After an update,
  check whether `DeferredHit.hpp` has the null check yet. If it has, retire this mod and its Include rule. If not, find
  the same branch in the new build.
- **Reported upstream** on 2026-11-08 as
  [Seb263/SkyrimSE_CoreImpactFramework#2](https://github.com/Seb263/SkyrimSE_CoreImpactFramework/issues/2), with the
  one-line fix `if (!victim || !attacker) return;` after `GetValidReference`. The author asks for contributions through
  the repository rather than forks. Retire this mod once a release carries the check.

**Not deployed in Ultra yet.** The folder was created while MO2 and the game were running, so MO2 has not added it to
the profile. It needs ticking once MO2 picks it up: it comes in at the highest priority, which already outranks CIF.
**Unverified in game.** The crash needs a bullet to hit an actor in the instant it is being torn down, so it is rare;
the test is no repeat.
