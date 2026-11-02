# CollisionMoppFix

- **Source:** `src/CollisionMoppFix/` (generated: `tools/01-fix-broken-mopp.py`)
- **Ships:** *(no plugin — 7 generated meshes, MO2 mod `Zenderal - Collision MOPP Fix`)*
- **FormID block:** _(none)_

## What it does

**Stops a crash that SkyParkour sets off next to a handful of Enderal objects.** Seven of Enderal's own meshes
ship a broken MOPP (the byte-code tree Havok walks to find which collision triangles a query touches).
A query that walks into the broken branch makes the game stop with `EXCEPTION_BREAKPOINT` at
`SkyrimSE.exe+0CC4904`. The fix closes each broken branch by changing one byte to `00`.

| Mesh | Placed as | Fault | Byte changed | Winning copy it replaces |
|---|---|---|---|---|
| `enderal\miscellaneous\streetlamhanging01.nif` | `_00E_ArkStreetlamp02 07BBBB`, 22 refs (Ark streets, harbour, Undercity) | split `11` at 351 of 352 bytes: its 3 argument bytes lie past the end | 351 | PG Patcher Output |
| `enderal\miscellaneous\rackcommon_scrolls.nif` | scroll rack | split `11` at 1327 of 1328 | 1327 | `E - Meshes.bsa` |
| `enderal\clutter\miscellaneous\rackcommon_scrolls.nif` | same mesh, second path | same | 1327 | `E - Meshes.bsa` |
| `enderal\architecture\ancientruins\ruins_24c.nif` | ruin piece | split `15` at 927 of 928 | 927 | ETATU - CM Meshes |
| `enderal\food\breadpile02.nif` | bread pile | split `15` at 207 of 208 | 207 | ETATU - CM Meshes |
| `enderal\clutter\miscellaneous\cart.nif` | cart | final 32-bit jump `70` at 7003 lands on undefined `58` at 6161 | 7003 | `E - Meshes.bsa` |
| `enderal\architecture\ark\suntemple\beacon\leuchtfeuer_newwithsphere_fixed.nif` | Ark Sun Temple beacon | final 32-bit jump `70` at 10363 lands 3 bytes inside a leaf, on `5E` | 10363 | SRP Enderal - Architecture (2K) |

Every copy in the list carries the same MOPP bytes as Enderal's archive: ETATU, SRP and PG Patcher only change
shaders and textures. It is SureAI's data, and no third-party mesh in the list has the fault (below).

## How it was found **[verified 2026-10-31]**

A player sent two crash logs from the same session, 3 hours apart (2026-10-30, 1.7.104, Crash Logger 1.25).
Both have the same stack:

- `EXCEPTION_BREAKPOINT` at `SkyrimSE.exe+0CC4904` (ID 67551+0xD14), a Havok/physics thread
- called from SkyParkourNG 3.6.5: `HavokUtil::SkyParkourHavokUpdate::PollChannelUpdateImpl` →
  `Parkouring::UpdateParkourPoint` → `GetLedgePoint` → `ClimbCheck` → `HavokUtil::ShapeCast`, a capsule
  linear cast (`hkpWorldLinearCaster`, `bhkCapsuleShape`, `hkScaledMoppBvTreeShape`,
  `hkpCompressedMeshShapeShared` and, in the second log, `hkpTriangleShape` on the stack). Both logs show the
  same cast parameters at `RSP+640..658` (10.0, FLT_MAX, 1.0).
- in ShapeCast's own stack frame (`RSP+D40`, both logs), the root node `Dummy05` of
  `Enderal\Miscellaneous\streetlamhanging01.nif`.

**The `int3` is the MOPP VM's trap for an opcode that doesn't exist.** The list's `SkyrimSE.exe` has the same MD5
as the player's (`113faeb71fd8f62b26d0c8627299ab40`) and its code is readable on disk. Function 67551 (image
`+0xCC3BF0`) reads `[rdi]`, `[rdi+1..3]` up front, rejects opcodes above `0x70`, and dispatches through a byte
table at `+0xCC4BCC` into a jump table at `+0xCC4B40`. The table sends 26 opcode values to `+0xCC4904`: `int3`
then `jmp` back to the loop. Those are `08 0E 0F 1D–1F 2C–2F 54–5F 6C–6F`, and everything above `70` goes there too. Opcode `00`'s handler
(`+0xCC4ADC`) restores registers and returns: the VM is recursive, so `00` ends the current branch.

The full opcode table, read handler by handler from the VM, is in the docstring of `tools/01`. Two points that
are easy to get wrong:

- `20–22` is a **split** (3 bytes, branches to *next* and *next + b2*). All split opcodes share a tail at
  `+0xCC4161` that takes `rdi + ecx` and `rdi + r8`. Modelling `20–22` as a single path left about 400 extra
  MOPPs with unreached bytes.
- `0C` jumps to code + (16-bit << 9) and `70` jumps to code + 32-bit. Both are absolute, from `[[vm+0x18]+0x20]`,
  the `hkpMoppCode`'s data pointer.

**Validated against every MOPP the list has:** the decoder never reads a byte as both an opcode and an argument,
in any of the 2,398 MOPPs in Enderal's `E - Meshes.bsa`/`E - Update.bsa`. And 8,821 `0x70` jumps in Enderal's and
Skyrim's mesh archives land on an opcode, 7 of them from the last instruction of their code, the same place as
the cart's and the beacon's bad ones. (Many MOPPs still have bytes no path reaches, which is not an error.)

**Why only SkyParkour finds it.** The broken branches cover a corner of a small object: the top of a lantern hanging
on a wall, one end of a cart. Walking, projectiles and the camera rarely send a query there; SkyParkour's ledge
checks sweep a capsule up walls in front of the player every frame. Even then the crash needs the bytes after the
code, or behind the bad jump, to decode to a bad opcode. That is why it was 2 crashes in ~1.5 h of play, not one
per lamp. The lamp's collision itself is clean: 44 triangles, none degenerate, a static layer-1 body, and all 22
placements at scale 1 (one at 0.94).

## The fix and its checks

`tools/01` resolves the **winning** copy of every mesh in the list: loose files by MO2 priority (overwrite first,
then `modlist.txt` order, then `Stock Game/Data`), else the last archive in load order that has it
(`Enderal.ini`'s `sResourceArchiveList`/`2`, then each plugin's `.bsa` in `loadorder.txt`, as GrassBounds does).
For each copy with a MOPP, it walks every path, carrying the leaf-key offset per path. Where a path goes wrong it
writes `00` over one byte:

- if the bad spot is reached through a plain jump (`05 06 07 0C 70`: one successor, no test), it patches the
  jump, so a byte that may belong to another instruction is never touched (the cart and the beacon);
- otherwise it patches the bad opcode itself, provided no other path reads that byte as an argument (the five
  truncated ones).

It asserts: the fixed code walks clean; the set of leaf keys is unchanged (the broken branch never produced a
triangle, so nothing loses collision); the file keeps its length; and exactly one byte differs per fix.
It refuses anything else (a jump out of the code from a split, a bad byte that is also an argument).

Scan of the whole list on 2026-10-31 (Ultra, 860 enabled mods, 63 archives): 76,486 copies of 48,620 mesh paths,
27,199 with a MOPP (`--all-sources`). Only the 7 Enderal meshes above are broken. The non-winning copies (Enderal's
archive, ETATU) have the same faults and are not shipped.

**Deployed 2026-10-31:** MO2 mod `Zenderal - Collision MOPP Fix`, enabled in Ultra directly **above PG Patcher
Output** (`modlist.txt` line 6; previous `modlist.txt` in `E:/Zenderal-backups/2026-10-31-collision-mopp-fix/`).
Checked after deploying: each of the 7 paths is now won by this mod, walks clean and differs from the copy it
replaced by one byte. **Unverified in game.** The crash was intermittent, so "no crash" near a lamp proves
little. A crash log with the same stack after this mod is enabled would prove it wrong.

## Keeping it right

- **Rerun `tools/01` after PG Patcher runs, after any mesh mod is added, removed, updated or reordered, and after
  a load-order change.** The shipped copies are the winners at the time of the run: a newer PG Patcher pass on
  the lamp would be hidden behind this mod's older copy. Rerunning also catches a newly installed mesh with the
  same fault.
- The mod must outrank every source of these meshes. PG Patcher Output wins the lamp, so this mod sits directly
  above it.
- The meshes are other authors' work and are generated, not committed.
- Retire a mesh from the fix if SureAI re-exports it; the script then finds nothing to fix for it.

## Not done

- **The cut branches are not rebuilt.** Their contents are lost (cut short) or unknowable (the bad jumps). They
  never produced a triangle, so the fix takes away no collision the game had. Rebuilding the trees would need
  Havok's MOPP compiler for compressed meshes; NifSkope's `NifMopp.exe` does not cover them.
- The cart's and the beacon's jumps both land exactly 3 bytes too far. Pointing them 3 bytes back would probably
  restore the intended branch, but that is a guess, so they are closed instead.
