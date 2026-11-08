"""Oxygen Meter 2 on Skyrim 1.7.104 (2026-11-07): a patched copy of oxygenMeter2.dll that no longer crashes on loading
screens. See arch-docs/patches/OxygenMeterLoadFix.md.

The winning copy is Nexus 195918's 1.7.104 rebuild (GPL-3.0, "Oxygen Meter 2 SKSE 1.7.104.0"). Its oxygen-value
function (RVA 0x16E90; it returns an optional<double>, written through RCX) reads the PlayerCharacter singleton
(Address Library ID 403521) and dereferences it with no null check. During some loading screens the singleton is null:
`mov r8, [rsi+0x60]` with RSI 0 at +0x16FC3, five crashes on the curator's PC (2026-10-28 to 11-07). That function is
the DLL's only read of the player.

The patch, one check:
  1. +0x16FC0 `mov rsi,[rax]; mov r8,[rsi+0x60]` (7 bytes) -> `jmp stub; nop; nop`.
  2. stub in the 21 int3 padding bytes at +0x955DB (no function's unwind range covers them):
         mov rsi,[rax]; test rsi,rsi; jz +0x1717E; mov r8,[rsi+0x60]; jmp +0x16FC7
     +0x1717E is the function's own "no value" exit (`mov byte [rdi+8], 0`, then the normal epilogue), reached by
     its `jb` at +0x16FDB from the same stack depth, so a null player shows no meter instead of crashing.
Only rel32 jumps are added (no relocations needed); none of the patched bytes carries a base relocation (checked).

Usage: python 01-patch-dll.py [<original oxygenMeter2.dll> [<output mod dir>]]"""
import hashlib
import os
import shutil
import struct
import sys

import capstone
import pefile

SRC = 'E:/Zenderal/mods/Oxygen Meter 2 SKSE 1.7.104.0/SKSE/Plugins/oxygenMeter2.dll'
OUT = 'E:/Zenderal/mods/Oxygen Meter 2 - Load Screen Fix (Zenderal)'
MD5 = 'ca833b413a391b8a93e30e0a3f35a179'      # Nexus 195918 build, TimeDateStamp 0x6AD52242
TIMESTAMP = 0x6AD52242

SITE, SITE_END = 0x16FC0, 0x16FC7             # mov rsi,[rax] / mov r8,[rsi+0x60]
SITE_OLD = bytes.fromhex('488b30 4c8b4660')
LOAD_SLOT = 0x16FB9                           # mov rax,[rip+0xdb4b8]: the REL::Relocation holding &singleton
LOAD_SLOT_OLD = bytes.fromhex('488b05b8b40d00')
NO_VALUE = 0x1717E                            # mov byte [rdi+8],0 (optional disengaged)
NO_VALUE_OLD = bytes.fromhex('c6470800')
CAVE, CAVE_LEN = 0x955DB, 21


def rel32(frm_end, to):
    return struct.pack('<i', to - frm_end)


def build_stub():
    s = bytearray()
    s += bytes.fromhex('488b30')                                   # mov rsi,[rax]
    s += bytes.fromhex('4885f6')                                   # test rsi,rsi
    s += b'\x0f\x84' + rel32(CAVE + len(s) + 6, NO_VALUE)          # jz no-value exit
    s += bytes.fromhex('4c8b4660')                                 # mov r8,[rsi+0x60]
    s += b'\xe9' + rel32(CAVE + len(s) + 5, SITE_END)              # jmp back
    assert len(s) == CAVE_LEN, len(s)
    return bytes(s)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    raw = open(src, 'rb').read()
    assert hashlib.md5(raw).hexdigest() == MD5, f'unexpected oxygenMeter2.dll (md5 {hashlib.md5(raw).hexdigest()})'
    pe = pefile.PE(data=raw)
    assert pe.FILE_HEADER.TimeDateStamp == TIMESTAMP
    img = pe.get_memory_mapped_image()
    assert img[LOAD_SLOT:LOAD_SLOT + 7] == LOAD_SLOT_OLD
    assert img[SITE:SITE_END] == SITE_OLD
    assert img[NO_VALUE:NO_VALUE + 4] == NO_VALUE_OLD
    assert img[CAVE:CAVE + CAVE_LEN] == b'\xcc' * CAVE_LEN
    assert img[CAVE - 1] == 0xC3 and img[CAVE + CAVE_LEN] != 0xCC, 'cave is not exactly the padding run'

    # no unwind range covers the cave; the site and exit are in the same function
    exc = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']]
    funcs = [struct.unpack_from('<II', img, exc.VirtualAddress + i * 12) for i in range(exc.Size // 12)]
    assert not any(b < CAVE + CAVE_LEN and CAVE < e for b, e in funcs), 'cave overlaps a function'
    owner = [f for f in funcs if f[0] <= SITE < f[1]]
    assert owner and owner[0][0] <= NO_VALUE < owner[0][1], 'exit is not in the patched function'

    # no base relocation lands in a patched range
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_BASERELOC']])
    patched = [(SITE, SITE_END), (CAVE, CAVE + CAVE_LEN)]
    for block in getattr(pe, 'DIRECTORY_ENTRY_BASERELOC', []):
        for e in block.entries:
            if e.type and any(lo - 7 < e.rva < hi for lo, hi in patched):
                raise AssertionError(f'base relocation at {e.rva:X} inside a patched range')

    data = bytearray(raw)
    stub = build_stub()
    site_new = b'\xe9' + rel32(SITE + 5, CAVE) + b'\x90\x90'
    for rva, old, new in ((SITE, SITE_OLD, site_new), (CAVE, b'\xcc' * CAVE_LEN, stub)):
        off = pe.get_offset_from_rva(rva)
        assert bytes(data[off:off + len(old)]) == old
        data[off:off + len(new)] = new
    diff = sum(a != b for a, b in zip(raw, data))
    assert len(data) == len(raw) and diff <= len(site_new) + len(stub), diff

    pe2 = pefile.PE(data=bytes(data))
    pe2.OPTIONAL_HEADER.CheckSum = pe2.generate_checksum()
    data = bytearray(pe2.write())

    # read the result back: the two jumps land where they should
    pe3 = pefile.PE(data=bytes(data))
    img3 = pe3.get_memory_mapped_image()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    site_ins = list(md.disasm(img3[SITE:SITE_END], SITE))
    assert [i.mnemonic for i in site_ins] == ['jmp', 'nop', 'nop'] and int(site_ins[0].op_str, 16) == CAVE
    cave_ins = list(md.disasm(img3[CAVE:CAVE + CAVE_LEN], CAVE))
    assert [i.mnemonic for i in cave_ins] == ['mov', 'test', 'je', 'mov', 'jmp'], [i.mnemonic for i in cave_ins]
    assert int(cave_ins[2].op_str, 16) == NO_VALUE and int(cave_ins[4].op_str, 16) == SITE_END
    for i in site_ins + cave_ins:
        print(f'  +{i.address:06X}  {i.mnemonic:5} {i.op_str}')

    plugins = os.path.join(out, 'SKSE', 'Plugins')
    os.makedirs(plugins, exist_ok=True)
    dst = os.path.join(plugins, 'oxygenMeter2.dll')
    open(dst, 'wb').write(data)
    lic = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(src))), 'LICENSE.txt')
    if os.path.exists(lic):
        shutil.copyfile(lic, os.path.join(out, 'LICENSE.txt'))
    print(f'wrote {dst} ({diff} bytes changed, md5 {hashlib.md5(data).hexdigest()})')


if __name__ == '__main__':
    main()
