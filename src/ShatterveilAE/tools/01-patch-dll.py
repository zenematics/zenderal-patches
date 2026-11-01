"""Shatterveil 1.3.1 on Skyrim 1.7.104 (2026-10-28): a patched copy of Shatterveil.dll plus the address library in the
format its CommonLibSSE-NG reads. See arch-docs/patches/ShatterveilAE.md.

Shatterveil's NG (closed source, Nexus 193420) decides the runtime from the game version's minor number - 4 VR, 6 AE,
anything else SE - so on 1.7.104 it thought it was SE and opened version-1-7-104-0.bin (missing: "failed to open
address library file"). Even as AE it reads only address library formats 1/2, and 1.7.104's versionlib is format 5.

  1. `cmp ax, 6` -> `cmp ax, 7` in Module's runtime switch: 1.7 is AE (this copy no longer runs on 1.6).
  2. "versionlib-{}.bin" -> "versionsvl-{}.bin" (same length): it loads only the converted file below, never the real
     format-5 one other plugins need.
  3. versionsvl-1-7-104-0.bin: the format-5 library re-encoded as format 2 (every entry type 0x77: u32 id, u32 offset),
     checked by decoding it back with the NG decoder's rules.

Usage: python 01-patch-dll.py <original Shatterveil.dll> <address library dir> <output mod dir>"""
import hashlib, os, struct, sys
import pefile

CMP_VA = 0x180030911                       # 66 83 F8 06  cmp ax, 6
OLD_CMP, NEW_CMP = bytes.fromhex('6683f806'), bytes.fromhex('6683f807')
OLD_STR, NEW_STR = b'Data/SKSE/Plugins/versionlib-{}.bin', b'Data/SKSE/Plugins/versionsvl-{}.bin'
# 4. The NG logger's log_directory() reads the game's "My Games" folder name through RELOCATION_ID(508778, 380738);
#    1.7.104 has no AE ID 380738, so the lookup returned 0 and the plugin read through a null pointer inside
#    SKSEPlugin_Load (SKSE: "fatal error occurred while loading plugin"; found with src/ZenExceptionTrace). The 42
#    bytes from the lookup to the dereference become: lea rax, [rip+2]; jmp to the strlen loop; the string itself -
#    as newer NG does, "Skyrim Special Edition". No jump from outside lands inside the range (checked).
LOG_VA, LOG_END = 0x180117916, 0x180117940
LOG_OLD = bytes.fromhex('e8d595f1ff4885c0741ae89b5cf1ff488b9810010000488d4db7e8bb95f1ff4803c3eb03498bc7488b00')
LOG_STR = b'Skyrim Special Edition\x00'
# 5. Decoys (effigies, Veilblades) wait to be "fully dressed" before showing - every worn armour piece counted through
#    the inventory - and otherwise show after 3 s. On 1.7.104 the count never matches (every log line: "revealed after
#    ~3050 ms (not fully dressed in time - shown anyway)"; cause not found - the ExtraDataList layout and kWorn types
#    check out), so every effigy appeared 3 s late. The 3 s (`mov esi, 0xB2D05E00`, ns, at both loads) becomes 0.4 s.
REVEAL_VAS = (0x180045279, 0x18004591B)
REVEAL_OLD, REVEAL_NEW = bytes.fromhex('be005ed0b2'), b'\xbe' + (400_000_000).to_bytes(4, 'little')
GAME = (1, 7, 104, 0)


def patch_dll(src, dst):
    data = bytearray(open(src, 'rb').read())
    pe = pefile.PE(data=bytes(data))
    off = pe.get_offset_from_rva(CMP_VA - pe.OPTIONAL_HEADER.ImageBase)
    assert data[off:off + 4] == OLD_CMP, f'runtime switch not at 0x{CMP_VA:X}: {data[off:off + 4].hex()} (new Shatterveil build?)'
    data[off:off + 4] = NEW_CMP
    assert data.count(OLD_STR) == 1, f'{data.count(OLD_STR)} copies of the versionlib path'
    i = data.index(OLD_STR); data[i:i + len(OLD_STR)] = NEW_STR
    lo = pe.get_offset_from_rva(LOG_VA - pe.OPTIONAL_HEADER.ImageBase); n = LOG_END - LOG_VA
    assert bytes(data[lo:lo + n]) == LOG_OLD, f'log_directory lookup not at 0x{LOG_VA:X}'
    body = bytes.fromhex('488d0502000000')          # lea rax, [rip+2] -> the string after the jmp
    body += bytes([0xEB, n - len(body) - 2])         # jmp short LOG_END
    body += LOG_STR
    assert len(body) <= n
    data[lo:lo + n] = body + b'\x90' * (n - len(body))
    for va in REVEAL_VAS:
        o = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
        assert bytes(data[o:o + 5]) == REVEAL_OLD, f'reveal timeout not at 0x{va:X}'
        data[o:o + 5] = REVEAL_NEW
    # PE checksum is not checked for DLLs loaded by LoadLibrary; recompute anyway for tidiness
    pe2 = pefile.PE(data=bytes(data)); pe2.OPTIONAL_HEADER.CheckSum = pe2.generate_checksum()
    open(dst, 'wb').write(pe2.write())
    print(f'patched {dst}: runtime switch at file 0x{off:X}, path at 0x{i:X}')


def convert(src, dst):
    b = open(src, 'rb').read()
    fmt, *ver = struct.unpack_from('<i4I', b, 0)
    assert fmt == 5 and tuple(ver) == GAME, (fmt, ver)
    name = b[20:84].split(b'\0')[0]
    psize, dfmt, count = struct.unpack_from('<iii', b, 84)
    offs = struct.unpack_from(f'<{count}I', b, 96)
    entries = [(i, o) for i, o in enumerate(offs) if o]
    out = bytearray(struct.pack('<i4ii', 2, *GAME, len(name)) + name + struct.pack('<ii', psize, len(entries)))
    for i, o in entries:
        out += b'\x77' + struct.pack('<II', i, o)
    open(dst, 'wb').write(out)
    # decode it back as unpack_file does (lo 7 = u32 id, hi 7 = u32 offset, hi bit 8 clear)
    p = 4 + 16 + 4 + len(name) + 8
    for i, o in entries:
        assert out[p] == 0x77 and struct.unpack_from('<II', out, p + 1) == (i, o)
        p += 9
    assert p == len(out)
    print(f'converted {len(entries)} of {count} ids (pointer size {psize}, data format {dfmt}) -> {dst}')


if __name__ == '__main__':
    dll, libdir, outdir = sys.argv[1:4]
    plug = os.path.join(outdir, 'SKSE', 'Plugins'); os.makedirs(plug, exist_ok=True)
    print('source sha256', hashlib.sha256(open(dll, 'rb').read()).hexdigest())
    patch_dll(dll, os.path.join(plug, 'Shatterveil.dll'))
    convert(os.path.join(libdir, 'versionlib-1-7-104-0.bin'), os.path.join(plug, 'versionsvl-1-7-104-0.bin'))
