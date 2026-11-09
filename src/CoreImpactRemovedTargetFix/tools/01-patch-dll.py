"""Core Impact Framework 2.0.7 (2026-11-08): a patched copy of CoreImpactFramework.dll that skips a hit whose target
actor has already been torn down, instead of crashing. See arch-docs/patches/CoreImpactRemovedTargetFix.md.

CIF's hit handler (RVA 0x299A4; args rcx = hit data, rdx = target ref, r8b) first validates the target: it must be a
Character (form type 0x3E), its FormID must not be 0 or 0xFFFFFFFF, and it must not carry the Deleted flag (0x20).
If any check fails it sets the actor (rbx) to null at +0x29A29 - and then carries on: every path reaches
`call IsBlocking(rbx)` at +0x29C13 (CIF's wrapper 0xABA40 -> SkyrimSE ID 37952), which reads [this+0x38] and crashes.
A player's log (keithsmyas, 2026-11-08): a pistol bullet hit a Fleshless Lost One whose FormID was already 0.

The patch rewrites the 16 bytes 0x29A1C-0x29A2B:

    before                               after
    29A1C mov ebx, r13d                  29A1C mov rbx, rdx          ; same value: see below
    29A1F cmp r8b, 0x3E                  29A1F jmp 0x29A2C           ; valid target: carry on as before
    29A23 cmove rbx, rdx                 29A21 jmp 0x29DF9           ; rejected target: the function's own exit
    29A27 jmp 0x29A2C                    29A26 int3 x3
    29A29 mov rbx, r13   <- 3 branches   29A29 jmp 0x29A21           ; the 3 rejecting branches land here
                                         29A2B int3

`mov rbx, rdx` equals the old `ebx = 0; cmove rbx, rdx`: 0x29A1C is reached only with rdx != 0, and rdx is non-zero
only when r8b == 0x3E (it was set by that same compare at 0x299FB-0x299FF). Nothing reads the flags those
instructions set. 0x29DF9 is the epilogue the function already takes when it is given no target at all (0x299E6) or
when its own lookups fail (0x29A64, 0x29A83): cookie check, restore, ret, from the same frame. The caller (0x519A0)
ignores the return value and then looks the target up by FormID (0x2A978), which returns early for FormID 0.

Checked (and asserted below): the three branches into 0x29A1F-0x29A2B all target 0x29A29; nothing else jumps into the
range; no base relocation lies in it; the other CIF functions with the same validation (0x27EC4, 0x8FE6C) and the
other IsBlocking caller (0x293C8) already leave on a rejected target.

Usage: python 01-patch-dll.py [<original CoreImpactFramework.dll> [<output mod dir>]]"""
import hashlib
import os
import struct
import sys

import capstone
import pefile

SRC = 'E:/Zenderal/mods/Core Impact Framework (CIF)/SKSE/Plugins/CoreImpactFramework.dll'
OUT = 'E:/Zenderal/mods/Core Impact Framework - Removed Target Fix (Zenderal)'
MD5 = 'f8526d67dd6280d119836f27bde22143'      # Nexus 146873 2.0.7 (2026-09-06 download), TimeDateStamp 0x6A9DDF15
TIMESTAMP = 0x6A9DDF15

FUNC = 0x299A4                                # CIF's hit handler
SITE, SITE_END = 0x29A1C, 0x29A2C
SITE_OLD = bytes.fromhex('418bdd 4180f83e 480f44da eb03 498bdd')
REJECT = 0x29A29                              # mov rbx, r13: where the three rejecting branches land
CARRY_ON = 0x29A2C                            # lea rcx, [rsi+0x88]
EXIT = 0x29DF9                                # mov rcx,[rbp+0x10]; xor rcx,rsp (cookie check, epilogue)
EXIT_OLD = bytes.fromhex('488b4d10 4833cc')
ISBLOCKING_CALL = 0x29C13                     # call 0xABA40, the crash
ISBLOCKING_CALL_OLD = bytes.fromhex('e8') + struct.pack('<i', 0xABA40 - (0x29C13 + 5))
REJECT_BRANCHES = {0x29A06: 'je', 0x29A10: 'ja', 0x29A1A: 'jne'}


def rel32(frm_end, to):
    return struct.pack('<i', to - frm_end)


def build_site():
    s = bytearray()
    s += bytes.fromhex('488bda')                                         # 29A1C mov rbx, rdx
    s += b'\xeb' + struct.pack('<b', CARRY_ON - (SITE + len(s) + 2))     # 29A1F jmp 29A2C
    jmp_exit = SITE + len(s)
    s += b'\xe9' + rel32(SITE + len(s) + 5, EXIT)                        # 29A21 jmp 29DF9
    s += b'\xcc' * (REJECT - SITE - len(s))                              # 29A26 int3 (unreachable)
    s += b'\xeb' + struct.pack('<b', jmp_exit - (REJECT + 2))            # 29A29 jmp 29A21
    s += b'\xcc' * (SITE_END - SITE - len(s))                            # 29A2B int3
    assert len(s) == SITE_END - SITE, len(s)
    return bytes(s), jmp_exit


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    raw = open(src, 'rb').read()
    assert hashlib.md5(raw).hexdigest() == MD5, f'unexpected CoreImpactFramework.dll (md5 {hashlib.md5(raw).hexdigest()})'
    pe = pefile.PE(data=raw)
    assert pe.FILE_HEADER.TimeDateStamp == TIMESTAMP
    img = pe.get_memory_mapped_image()
    assert img[SITE:SITE_END] == SITE_OLD
    assert img[EXIT:EXIT + len(EXIT_OLD)] == EXIT_OLD
    assert img[ISBLOCKING_CALL:ISBLOCKING_CALL + 5] == ISBLOCKING_CALL_OLD
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

    # the site, the exit and the crash call are in the one function
    exc = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXCEPTION']]
    funcs = sorted(set(struct.unpack_from('<II', img, exc.VirtualAddress + i * 12) for i in range(exc.Size // 12)))
    owner = [f for f in funcs if f[0] <= SITE < f[1]]
    assert owner and owner[0][0] == FUNC and all(owner[0][0] <= a < owner[0][1] for a in (EXIT, ISBLOCKING_CALL))

    # every branch in the DLL that lands inside the rewritten bytes: only the three rejecting ones, all at REJECT
    found = {}
    for b, e in funcs:
        for ins in md.disasm(img[b:e], b):
            if (ins.mnemonic.startswith('j') or ins.mnemonic == 'call') and ins.op_str.startswith('0x'):
                t = int(ins.op_str, 16)
                if SITE < t < SITE_END and not SITE <= ins.address < SITE_END:
                    found[ins.address] = (ins.mnemonic, t)
    assert found == {a: (m, REJECT) for a, m in REJECT_BRANCHES.items()}, found

    # no base relocation lands in the rewritten bytes
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_BASERELOC']])
    for block in getattr(pe, 'DIRECTORY_ENTRY_BASERELOC', []):
        for e in block.entries:
            if e.type and SITE - 7 < e.rva < SITE_END:
                raise AssertionError(f'base relocation at {e.rva:X} inside the patched range')

    site_new, jmp_exit = build_site()
    data = bytearray(raw)
    off = pe.get_offset_from_rva(SITE)
    assert bytes(data[off:off + len(SITE_OLD)]) == SITE_OLD
    data[off:off + len(site_new)] = site_new
    diff = sum(a != b for a, b in zip(raw, data))
    assert len(data) == len(raw) and diff <= len(site_new), diff

    if pe.OPTIONAL_HEADER.CheckSum:            # 2.0.7 ships 0: leave it so
        pe2 = pefile.PE(data=bytes(data))
        pe2.OPTIONAL_HEADER.CheckSum = pe2.generate_checksum()
        data = bytearray(pe2.write())

    # read the result back
    img3 = pefile.PE(data=bytes(data)).get_memory_mapped_image()
    code = [i for i in md.disasm(img3[SITE:SITE_END], SITE) if i.mnemonic != 'int3']
    got = [(i.address, i.mnemonic, i.op_str) for i in code]
    want = [(SITE, 'mov', 'rbx, rdx'), (SITE + 3, 'jmp', hex(CARRY_ON)), (jmp_exit, 'jmp', hex(EXIT)),
            (REJECT, 'jmp', hex(jmp_exit))]
    assert got == want, got
    for a, m in REJECT_BRANCHES.items():
        ins = next(md.disasm(img3[a:a + 2], a))
        assert ins.mnemonic == m and int(ins.op_str, 16) == REJECT, (hex(a), ins.mnemonic, ins.op_str)
    for a, m, o in got:
        print(f'  +{a:06X}  {m:5} {o}')

    plugins = os.path.join(out, 'SKSE', 'Plugins')
    os.makedirs(plugins, exist_ok=True)
    dst = os.path.join(plugins, 'CoreImpactFramework.dll')
    open(dst, 'wb').write(data)
    print(f'wrote {dst} ({diff} bytes changed, md5 {hashlib.md5(data).hexdigest()})')


if __name__ == '__main__':
    main()
