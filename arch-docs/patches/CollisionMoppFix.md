# CollisionMoppFix

- **Source:** `src/CollisionMoppFix/` (generated: `tools/01-fix-broken-mopp.py`)
- **Ships:** *(no plugin — 18 generated meshes, MO2 mod `Zenderal - Collision MOPP Fix`)*
- **FormID block:** _(none)_

## What it does

**Stops two collision crashes, nearly all in Enderal's own meshes** (plus one Bank of Ark SE mesh and one
Bethesda ceiling). A MOPP is the byte-code tree Havok walks to find which collision triangles a query touches.

- **Broken code (2026-10-31, 7 meshes):** SkyParkour sets it off next to a handful of Enderal objects. Their MOPP
  code is cut short or jumps into the middle of an instruction. A query that walks into the broken branch makes
  the game stop with `EXCEPTION_BREAKPOINT` at `SkyrimSE.exe+0CC4904`.
- **Keys past the mesh (2026-11-09, 11 meshes):** the MOPP code is well formed, but one leaf hands out a key
  that names no triangle. A query that reaches it reads past the compressed mesh's index list and crashes with
  `EXCEPTION_ACCESS_VIOLATION` at `SkyrimSE.exe+10E675B`. See [Second fault](#second-fault-a-leaf-key-past-the-compressed-mesh-verified-2026-11-09).

The fix closes each broken branch or bad leaf by changing one byte to `00`.

| Mesh | Placed as | Fault | Byte changed | Winning copy it replaces |
|---|---|---|---|---|
| `enderal\miscellaneous\streetlamhanging01.nif` | `_00E_ArkStreetlamp02 07BBBB`, 22 refs (Ark streets, harbour, Undercity) | split `11` at 351 of 352 bytes: its 3 argument bytes lie past the end | 351 | ETATU - CM Meshes (PG Patcher Output until its 2026-11-09 run) |
| `enderal\miscellaneous\rackcommon_scrolls.nif` | scroll rack | split `11` at 1327 of 1328 | 1327 | `E - Meshes.bsa` |
| `enderal\clutter\miscellaneous\rackcommon_scrolls.nif` | same mesh, second path | same | 1327 | `E - Meshes.bsa` |
| `enderal\architecture\ancientruins\ruins_24c.nif` | ruin piece | split `15` at 927 of 928 | 927 | ETATU - CM Meshes |
| `enderal\food\breadpile02.nif` | bread pile | split `15` at 207 of 208 | 207 | ETATU - CM Meshes |
| `enderal\clutter\miscellaneous\cart.nif` | cart | final 32-bit jump `70` at 7003 lands on undefined `58` at 6161 | 7003 | `E - Meshes.bsa` |
| `enderal\architecture\ark\suntemple\beacon\leuchtfeuer_newwithsphere_fixed.nif` | Ark Sun Temple beacon | final 32-bit jump `70` at 10363 lands 3 bytes inside a leaf, on `5E` | 10363 | SRP Enderal - Architecture (2K) |

Every copy in the list carries the same MOPP bytes as Enderal's archive: ETATU, SRP and PG Patcher only change
shaders and textures. It is SureAI's data, and no third-party mesh in the list has the fault (below).

The second fault. In every case the bad leaf is the MOPP's **last instruction**, a 24-bit leaf `52` in its last
4 bytes:

| Mesh | Placed as | Bad key (chunk, index / indices) | Byte changed | Winning copy it replaces |
|---|---|---|---|---|
| `enderal\landscape\tropical\vegetation\mangrovefanpalm03.nif` | `_00E_TropicalTree_MangroveFanPalm03 088145`, 41 refs in Vyn (desert, coast) | `000400C6` (0, 198 / 24) | 124 of 128 | Enderal - Fixed Mesh Lighting |
| `enderal\landscape\tropical\vegetation\lataniapalm01.nif` | latania palm | `000400C6` (0, 198 / 24) | 108 of 112 | Enderal - Fixed Mesh Lighting |
| `enderal\landscape\tropical\vegetation\screwpalm.nif` | `_00E_TropicalTree_ScrewPalm 0880EF` | `000400C6` (0, 198 / 46) | 284 of 288 | Enderal - Fixed Mesh Lighting |
| `enderal\architecture\ark\suntemple\beacon\beaconpillarbroken01.nif`, `02`, `03` | broken Sun Temple beacon pillars | `00040011` (0, 17 / 14) | 76 of 80 | SRP Enderal - Architecture (2K) |
| `enderal\architecture\silvergrove\doorstairs.nif` | Silvergrove door stairs | `00040015` (0, 21 / 18) | 124 of 128 | PG Patcher Output |
| `enderal\esrathir\architecture\mining\esr_al_waterchannelsinglepillar.nif` | Esrathir water-channel pillar | `00040011` (0, 17 / 18) | 108 of 112 | PG Patcher Output |
| `enderal\tesa\resourcekit\clutter\fishing\fishingcreel01.nif` | fishing creel | `000A0011` (1, 17 / 18) | 524 of 528 | ETATU - CM Meshes |
| `architecture\solitude\arkbankstair01.nif` | Bank of Ark stair | `0006003D` (0, 61 / 18) | 124 of 128 | PG Patcher Output (Bank of Ark SE's mesh) |
| `creationclub\_shared\dungeons\ayleidruins\interior\arceilingwelkydgreen01.nif` | Ayleid ceiling | `00040068` (0, 104 / 36) | 220 of 224 | `Skyrim - Meshes0.bsa` |

These are the same bytes in every copy: Enderal's `E - Meshes.bsa` (Bethesda's archive for the ceiling, Bank of
Ark SE's own mesh for the stair), with ETATU, SRP, Fixed Mesh Lighting and PG Patcher passing them along.

## Second fault: a leaf key past the compressed mesh **[verified 2026-11-09]**

**The crash.** A player (LIGHT, 2026-11-09, 1.7.104, Crash Logger 1.25, 3 h 24 min in) crashed with
`EXCEPTION_ACCESS_VIOLATION` at `SkyrimSE.exe+10E675B` (ID 80713+0xBB, `movzx ecx, word ptr [rdx+rax*2]`,
RAX `0x8700`), on a Havok thread.

- **The call path:** ID 80699, then the MOPP ray query (62402 / 62400 / 60685), then `hkpSimpleWorldRayCaster`.
  It was set off by Hit Where You Aim's per-frame crosshair ray (`PlayerSetAimPitchHook` →
  `BallisticSolver::Solve`) while the player aimed.
- **On the stack:** `hkScaledMoppBvTreeShape`, `hkpCompressedMeshShapeShared`, `hkpTriangleShape`, and cell
  `001D94`.

**The engine's key decode**, read from ID 80699 (`+0x10E5950`) on the list's exe:

| Key's section (`key >> bitsPerWIndex`) | What the key names |
|---|---|
| 0 | big triangle `key & wIndexMask` |
| all ones | a convex piece (Skyrim's data has none) |
| anything else | chunk `section − 1` (or its `reference`), position `i = key & wIndexMask & indexMask` |

- **The unchecked read:** a chunk triangle reads `indices[i]`, `[i+1]` and `[i+2]`. ID 80713 multiplies each by 3
  to index the chunk's quantized vertices. Nothing checks `i` against the index count.
- **What went wrong here:** the third index came back as 11520 (RAX `0x8700` = 11520 × 3), far past the chunk's
  vertices. R14 held **198**.

**How the mesh was found:**

1. **The scan:** a scan of the collision of every winning mesh (12,191 with a compressed mesh) checked every MOPP
   leaf key against this decode. **11 meshes** each yield exactly one key with `i + 2` past their chunk's index
   list. Three are tropical palms whose bad key is `000400C6`, which is position **198**, the R14 value.
2. **The ray:** the two points on the stack, Havok (983.4, −166.3, 40.8) to (1027.3, −309.6, 33.7), × 69.99 =
   game (68830, −11642) to (71899, −21670), describe a crosshair ray about 10,500 units long.
3. **The palm:** a `MangroveFanPalm03` ref in cell `001D94` (Vyn 17, −6, the desert next to
   `_00E_DesertPulvermineLocation`) stands 14 units from that ray. That is the cell on the stack.

**No other mesh-data faults:** in every compressed mesh in the list, every chunk index names a vertex of its chunk,
and every big triangle names a big vertex. The 11 bad keys are the only fault of this kind.

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

**Bad keys (2026-11-09).** When the MOPP wraps a `bhkCompressedMeshShape`, the tool parses its
`bhkCompressedMeshShapeData`. It refuses the file if any chunk index or big triangle names a vertex that isn't
there. Then it checks every leaf key against the engine's decode.

- **The edit:** each leaf instruction that yields a key naming no triangle becomes `00`. That is one byte. A leaf
  ends its branch anyway, so `00` only drops the key.
- **When it refuses:** if the same instruction also yields a valid key on another path, or another instruction
  reads it as an argument.
- **What it asserts:** the walk afterwards is clean, and the leaf keys are the old set minus exactly the bad ones.
  Those keys never named a triangle, so no collision is lost.

Scan of the whole list on 2026-10-31 (Ultra, 860 enabled mods, 63 archives): 76,486 copies of 48,620 mesh paths,
27,199 with a MOPP (`--all-sources`). Only the 7 Enderal meshes above are broken. The non-winning copies (Enderal's
archive, ETATU) have the same faults and are not shipped.

**Deployed 2026-10-31:** MO2 mod `Zenderal - Collision MOPP Fix`, enabled in Ultra directly **above PG Patcher
Output** (`modlist.txt` line 6; previous `modlist.txt` in `E:/Zenderal-backups/2026-10-31-collision-mopp-fix/`).
Checked after deploying: each of the 7 paths is now won by this mod, walks clean and differs from the copy it
replaced by one byte. **Unverified in game.** The crash was intermittent, so "no crash" near a lamp proves
little. A crash log with the same stack after this mod is enabled would prove it wrong.

**Rerun 2026-11-09 with the bad-key check:** 45,946 mesh paths, 12,362 with a MOPP, **18 meshes written** (the
7 above plus the 11 bad-key ones). The mod was at `modlist.txt` line 11, above PG Patcher Output (13), so it
outranks every source of all 18. Previous folder in `E:/Zenderal-backups/2026-11-09-mopp-keys/`.

**Checked on the written files:**

- every MOPP walks clean, and no leaf key points past its compressed mesh;
- the 6 older paths are byte-identical to the 2026-10-31 output;
- the street lamp differs only because its winning copy is now ETATU's: PG Patcher Output no longer carries it
  after its 2026-11-09 run.

**Unverified in game.** For the palms, the test is aiming a bow, gun or spell across a fan palm in the desert
(cell 17, −6).

## Keeping it right

- **Rerun `tools/01` after PG Patcher runs, after any mesh mod is added, removed, updated or reordered, and after
  a load-order change.** The shipped copies are the winners at the time of the run: a newer PG Patcher pass on
  the lamp would be hidden behind this mod's older copy. Rerunning also catches a newly installed mesh with the
  same fault.
- The mod must outrank every source of these meshes. PG Patcher Output wins some of them (stair, door stairs,
  water-channel pillar), so this mod sits directly above it.
- The meshes are other authors' work and are generated, not committed.
- Retire a mesh from the fix if SureAI re-exports it; the script then finds nothing to fix for it.

## Not done

- **The cut branches are not rebuilt.** Their contents are lost (cut short) or unknowable (the bad jumps). They
  never produced a triangle, so the fix takes away no collision the game had. Rebuilding the trees would need
  Havok's MOPP compiler for compressed meshes; NifSkope's `NifMopp.exe` does not cover them.
- The cart's and the beacon's jumps both land exactly 3 bytes too far. Pointing them 3 bytes back would probably
  restore the intended branch, but that is a guess, so they are closed instead.
