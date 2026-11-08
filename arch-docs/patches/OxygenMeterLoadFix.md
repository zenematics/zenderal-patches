# OxygenMeterLoadFix

- **Source:** `src/OxygenMeterLoadFix/tools/01-patch-dll.py`. It is a byte patch with every original byte asserted.
  The DLL is GPL-3.0, so this script is the published change.
- **Ships:** MO2 mod *Oxygen Meter 2 - Load Screen Fix (Zenderal)*, directly **above** *Oxygen Meter 2 SKSE
  1.7.104.0* in the left pane. It holds `SKSE/Plugins/oxygenMeter2.dll` (a patched copy, generated, not committed) and
  the rebuild's `LICENSE.txt`. It has a Wabbajack `Include` rule, because the patched DLL matches no download.
- **FormID block:** _(none)_

## Why (2026-11-07)

**The crash:** the game crashed at loading screens with `EXCEPTION_ACCESS_VIOLATION` at `oxygenMeter2.dll+0016FC3`
(`mov r8, [rsi+0x60]`, RSI 0). The stack held `oxygenMenu*`, and the job threads were in `kLoadScreen`.

- **How often:** five times on the curator's PC, on 2026-10-28 (twice), 10-31 and 11-07 (twice). The uptimes were
  38–43 s three times, then 74 s and 6 min 22 s.
- **The copy that loads:** Nexus 195918's 1.7.104 rebuild (*Oxygen Meter 2 SKSE 1.7.104.0*, md5 `ca833b41…`,
  TimeDateStamp `0x6AD52242`). The two older copies in the list (Nexus 64532 and *Fixes and Additions*, 171916) sort
  below it and never load.

**The cause, found by disassembling the winning DLL:**

- **The function:** `+16E90` is the breath meter's value function. It returns an `optional<double>` through the
  RCX return slot, which it keeps in RDI.
- **The unchecked read:** it relocates Address Library ID **403521**, CommonLib's `PlayerCharacter` singleton
  (`RELOCATION_ID(517014, 403521)`). Then it loads the player and reads `+0x5C`/`+0x60` without a null check.
- **When it fails:** during some loading screens the singleton is null. The crash log's RAX is the singleton's
  address, `SkyrimSE.exe+3230778`, and the pointer it holds is 0.
- **Only one read:** this is the only function in the DLL that reads that singleton. A scan of every function by
  `.pdata` range found the relocation and its slot used only there.

## The patch

1. At `+0x16FC0`, `mov rsi,[rax]; mov r8,[rsi+0x60]` (7 bytes) becomes `jmp stub; nop; nop`.
2. The stub goes in the 21 `int3` padding bytes at `+0x955DB`:
   `mov rsi,[rax]; test rsi,rsi; jz +0x1717E; mov r8,[rsi+0x60]; jmp +0x16FC7`.

`+0x1717E` is the function's own "no value" exit: `mov byte [rdi+8], 0`, then the normal epilogue. The function's
`jb` at `+0x16FDB` already reaches it from the same stack depth, and RDI still holds the return slot. So with no
player, the meter gets "no value" and shows nothing instead of crashing.

**Checks the tool asserts:**

- the source md5 and timestamp;
- every replaced byte and the exit's bytes;
- that the cave is exactly the padding run, and that no `.pdata` range covers it;
- that the site and the exit are in the same function;
- that no base relocation falls in a patched range (only rel32 jumps are added);
- by disassembling the result, that both jumps land where intended.

It changes 28 bytes, plus the PE checksum.

## Keeping it right

- **Rerun `tools/01` after an Oxygen Meter update.** It refuses any other build (md5 check); find the same read in
  the new build first.
- If the rebuild's author adds a null check upstream, retire this mod and its Include rule.
- **Prophecy depends on Oxygen Meter.** Its Rage meter uses the mod's `interface/oxygenMeter2.swf` in a menu of its
  own, so Oxygen Meter stays in the list.

**Unverified in game.** The crash came on roughly one load in a few, so no crash over a few dozen loads is the test.
