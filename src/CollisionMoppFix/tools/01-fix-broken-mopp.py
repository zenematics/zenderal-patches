r"""Build `Zenderal - Collision MOPP Fix` from the installed list -- never hand-edit its meshes.

Why: a MOPP is the byte-code tree Havok walks to find which collision triangles a query touches.
SkyrimSE.exe 1.7.104's MOPP virtual machine (Address Library ID 67551, image +0xCC3BF0) reads one
opcode byte at a time and sends every opcode it does not know to an int3 (+0xCC4904). A few of
Enderal's own meshes ship MOPP code that is cut short or holds an opcode that does not exist, so a
query that walks into that branch reads past the code into whatever memory follows, or straight
into the bad opcode, and the game stops with EXCEPTION_BREAKPOINT at SkyrimSE.exe+0CC4904.
SkyParkour's ledge checks (capsule casts, every frame) find those branches; normal play rarely does.

The fix closes each broken branch with 00, the VM's "return from this branch", written over one
byte: the plain jump that leads into the bad spot when there is one (the cart's and the beacon's
last instruction is a 32-bit jump that lands 3 bytes inside an instruction; 8821 other such jumps in
Enderal's and Skyrim's archives land on an opcode), else the bad opcode itself (an opcode whose
arguments run past the end of the code). Nothing else in the file changes. The broken branch never
produced a triangle, so the set of leaves the tree reaches is the same before and after (asserted).

The opcode table is read from the VM itself (dispatch tables at +0xCC4BCC / +0xCC4B40), not from
documentation. Each entry: length in bytes, and where the walk continues ("next" = after the opcode):
  00            return from this branch
  01-04         rescale the query, 4
  05 / 06 / 07  jump next + 8 / 16 / 24-bit offset; 2 / 3 / 4
  09 / 0A / 0B  add 8 / 16 / 32-bit to the leaf-key offset; 2 / 3 / 5
  0C            jump to code + (16-bit << 9); 3
  0D            skip; 5
  10-1C         split: next and next + b3; 4
  20-22         split: next and next + b2; 3
  23-25         split: next + (b3 b4) and next + (b5 b6); 7
  26-28 / 29-2B bounds check (may return); 3 / 7
  30-4F         leaf: offset + (op - 30); 1
  50-53         leaf: offset + 8 / 16 / 24 / 32-bit; 2-5
  60-63 / 64-67 / 68-6B   property 8 / 16 / 32-bit; 2 / 3 / 5
  70            jump to code + 32-bit; 5
  anything else the int3.
Checked on all 2398 MOPPs in Enderal's E - Meshes/E - Update archives: opcodes and arguments never
overlap, and only the 6 meshes this script exists for go wrong.

Second fault (2026-11-09): a well-formed MOPP whose leaf hands out a key no triangle has. A MOPP over a
bhkCompressedMeshShape yields shape keys, which the engine decodes like this (ID 80699, +0x10E5950):
  section = key >> bitsPerWIndex; i = key & wIndexMask
  section 0 -> big triangle i; section all ones -> convex piece i (Skyrim's data has none);
  else chunk section - 1 (or that chunk's `reference` when it is not 0xFFFF), whose triangle reads
  indices[i & indexMask], [+1], [+2], each times 3 into the chunk's quantized vertices (ID 80713).
Nothing checks i against the chunk's index count, so a key past the end reads whatever follows the index
array as a vertex number and runs off the vertex array: EXCEPTION_ACCESS_VIOLATION at SkyrimSE.exe+10E675B.
A player's log (2026-11-09) had Hit Where You Aim's crosshair ray in a Mangrove Fan Palm whose MOPP
gives key 000400C6 (index 198) for a chunk of 24 indices; R14 held the 198. Every such leaf is closed
with 00 as well (one byte; refused if the same instruction also yields a valid key on another path), and
the leaf set afterwards must be the old one minus exactly the bad keys (asserted). 11 meshes in the list
(2026-11-09), all SureAI's or Bethesda's own data, one bad key each.

Scope: the WINNING copy of every mesh in the list (loose file by MO2 priority, overwrite first;
else the last archive in load order that has it). The meshes are other authors' work (SureAI's,
and whatever mod's copy wins), so they are generated from the install, never committed. Re-run
after PG Patcher, a mesh mod change or a load-order change. The mod must outrank every source of
the meshes it ships (it sits directly above PG Patcher Output).

Usage (repo root):  python src/CollisionMoppFix/tools/01-fix-broken-mopp.py
                        [--modlist E:/Zenderal] [--profile Ultra] [--dry-run] [--all-sources]
  --all-sources  also report broken MOPPs in copies that do not win (nothing is written for them)
"""
import argparse
import os
import re
import shutil
import struct

import lz4.frame

MOD = 'Zenderal - Collision MOPP Fix'
BS = '\\'

# --- MOPP ---------------------------------------------------------------------------------------------
UNDEFINED = {0x08, 0x0E, 0x0F, 0x1D, 0x1E, 0x1F, 0x2C, 0x2D, 0x2E, 0x2F,
             *range(0x54, 0x60), *range(0x6C, 0x70), *range(0x71, 0x100)}


def oplen(op):
    if op == 0x00 or 0x30 <= op <= 0x4F:
        return 1
    if op in (0x05, 0x09, 0x50) or 0x60 <= op <= 0x63:
        return 2
    if op in (0x06, 0x0A, 0x0C, 0x51) or 0x20 <= op <= 0x22 or 0x26 <= op <= 0x28 or 0x64 <= op <= 0x67:
        return 3
    if op in (0x07, 0x52) or 0x01 <= op <= 0x04 or 0x10 <= op <= 0x1C:
        return 4
    if op in (0x0B, 0x0D, 0x53, 0x70) or 0x68 <= op <= 0x6B:
        return 5
    return 7                                        # 23-25, 29-2B


JUMPS = {0x05, 0x06, 0x07, 0x0C, 0x70}            # one successor, no test


def walk(code, leaves=None):
    """Every path from the root, with the leaf-key offset carried per path.
    -> (opcode positions, argument positions, leaf keys, problems [(kind, position, parent position)])
    leaves: a dict to fill with {leaf instruction position: set of keys it yields}"""
    starts, args, keys, problems = set(), set(), set(), []
    if leaves is None:
        leaves = {}
    todo, seen = [(0, 0, None)], set()
    while todo:
        i, off, parent = todo.pop()
        if (i, off) in seen:
            continue
        seen.add((i, off))
        if not 0 <= i < len(code):
            problems.append(('jump out of the code', i, parent))
            continue
        op = code[i]
        if op in UNDEFINED:
            problems.append(('undefined', i, parent))
            continue
        n = oplen(op)
        if i + n > len(code):
            problems.append(('truncated', i, parent))
            continue
        starts.add(i)
        args.update(range(i + 1, i + n))
        b = code[i + 1:i + n]
        val = int.from_bytes(b, 'big')
        nxt = i + n
        if op == 0x00:
            continue
        if 0x30 <= op <= 0x4F:
            keys.add(off + op - 0x30)
            leaves.setdefault(i, set()).add(off + op - 0x30)
        elif 0x50 <= op <= 0x53:
            keys.add(off + val)
            leaves.setdefault(i, set()).add(off + val)
        elif op in (0x09, 0x0A, 0x0B):
            todo.append((nxt, off + val, i))
        elif op in (0x05, 0x06, 0x07):
            todo.append((nxt + val, off, i))
        elif op == 0x0C:
            todo.append((val << 9, off, i))
        elif op == 0x70:
            todo.append((val, off, i))
        elif 0x10 <= op <= 0x1C:
            todo += [(nxt, off, i), (nxt + b[2], off, i)]
        elif 0x20 <= op <= 0x22:
            todo += [(nxt, off, i), (nxt + b[1], off, i)]
        elif 0x23 <= op <= 0x25:
            todo += [(nxt + (b[2] << 8 | b[3]), off, i), (nxt + (b[4] << 8 | b[5]), off, i)]
        else:
            todo.append((nxt, off, i))
    return starts, args, keys, problems


# --- NIF: block table only; a bhkMoppBvTreeShape's code starts 41 bytes in (shape ref, 12 unused,
# shape scale, code size, origin, scale, build type) for both SE (BS 100) and LE (BS 83) files -------
def nif_blocks(data):
    """-> [(block type, absolute offset, size)] of every block"""
    d = data
    p = d.index(b'\n') + 1
    ver, = struct.unpack_from('<I', d, p); p += 5
    assert ver == 0x14020007, hex(ver)
    user, nblocks, bsver = struct.unpack_from('<III', d, p); p += 12
    assert user == 12 and bsver in (83, 100), (user, bsver)
    for _ in range(3):
        p += 1 + d[p]
    ntypes, = struct.unpack_from('<H', d, p); p += 2
    types = []
    for _ in range(ntypes):
        n, = struct.unpack_from('<I', d, p); types.append(d[p + 4:p + 4 + n].decode('latin1')); p += 4 + n
    tidx = struct.unpack_from('<%dH' % nblocks, d, p); p += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, d, p); p += 4 * nblocks
    nstr, = struct.unpack_from('<I', d, p); p += 8
    for _ in range(nstr):
        n, = struct.unpack_from('<I', d, p); p += 4 + n
    ngroups, = struct.unpack_from('<I', d, p); p += 4 + 4 * ngroups
    out = []
    for i in range(nblocks):
        out.append((types[tidx[i] & 0x7FFF], p, sizes[i]))
        p += sizes[i]
    assert p + 4 <= len(d), 'block table runs past the end of the file'
    return out


def mopp_blocks(data, blocks=None):
    """-> [(absolute offset of the MOPP code, code size, block index of the shape it wraps)]"""
    out = []
    for t, p, s in blocks if blocks is not None else nif_blocks(data):
        if t == 'bhkMoppBvTreeShape':
            size, = struct.unpack_from('<I', data, p + 20)
            head = s - size                         # 41 with the build-type byte, 40 without
            assert head in (40, 41), ('MOPP block size', size, s)
            shape, = struct.unpack_from('<i', data, p)
            out.append((p + head, size, shape))
    return out


# --- compressed mesh: which keys name a triangle (layout: nif.xml bhkCompressedMeshShapeData) ----------
def compressed_mesh(data, blocks, shape):
    """The bhkCompressedMeshShapeData behind block `shape`, or None if it is not a compressed mesh."""
    if not 0 <= shape < len(blocks) or blocks[shape][0] != 'bhkCompressedMeshShape':
        return None
    _, sp, ss = blocks[shape]
    ref, = struct.unpack_from('<i', data, sp + ss - 4)      # Data, the shape's last field
    assert 0 <= ref < len(blocks) and blocks[ref][0] == 'bhkCompressedMeshShapeData', ('CMS data ref', ref)
    _, p, size = blocks[ref]
    end = p + size
    bpi, bpw, maskw, maski = struct.unpack_from('<4I', data, p)
    p += 16 + 4 + 32 + 2                                    # error, bounds min/max, welding + material type
    for _ in range(3):                                      # materials 32 / 16 / 8
        n, = struct.unpack_from('<I', data, p); p += 4 + 4 * n
    n, = struct.unpack_from('<I', data, p); p += 4 + 8 * n  # chunk materials
    n, = struct.unpack_from('<I', data, p); p += 4          # named materials
    assert n == 0, 'named materials'
    n, = struct.unpack_from('<I', data, p); p += 4 + 32 * n  # chunk transforms
    nbv, = struct.unpack_from('<I', data, p); p += 4 + 16 * nbv
    nbt, = struct.unpack_from('<I', data, p); p += 4
    for t in range(nbt):
        tri = struct.unpack_from('<3H', data, p + 12 * t)
        if max(tri) >= nbv:
            raise ValueError('big triangle %d names vertex %d of %d' % (t, max(tri), nbv))
    p += 12 * nbt
    nch, = struct.unpack_from('<I', data, p); p += 4
    chunks = []
    for c in range(nch):
        p += 16 + 4                                         # translation, material index
        reference, = struct.unpack_from('<H', data, p); p += 4  # + transform index
        nv, = struct.unpack_from('<I', data, p); p += 4 + 2 * nv
        ni, = struct.unpack_from('<I', data, p); p += 4
        idx = struct.unpack_from('<%dH' % ni, data, p); p += 2 * ni
        if idx and max(idx) >= nv // 3:
            raise ValueError('chunk %d index names vertex %d of %d' % (c, max(idx), nv // 3))
        n, = struct.unpack_from('<I', data, p); p += 4 + 2 * n  # strips
        n, = struct.unpack_from('<I', data, p); p += 4 + 2 * n  # welding
        chunks.append((reference, ni))
    n, = struct.unpack_from('<I', data, p); p += 4          # convex pieces
    assert n == 0 and p == end, ('CMS data layout', n, p - end)
    return dict(bpw=bpw, maskw=maskw, maski=maski, nbt=nbt, chunks=chunks)


def key_names_triangle(cms, key):
    section, i = key >> cms['bpw'], key & cms['maskw']
    if section == 0:
        return i < cms['nbt']
    if section == (1 << (32 - cms['bpw'])) - 1:             # convex piece: there are none
        return False
    if section - 1 >= len(cms['chunks']):
        return False
    reference, ni = cms['chunks'][section - 1]
    if reference != 0xFFFF:
        if reference >= len(cms['chunks']):
            return False
        reference, ni = cms['chunks'][reference]
    return (i & cms['maski']) + 2 < ni


def fix(data):
    """-> (fixed bytes or None, report lines). Raises on anything the one-byte fix can't handle."""
    out, report = bytearray(data), []
    blocks = nif_blocks(data)
    for start, size, shape in mopp_blocks(data, blocks):
        code = bytes(data[start:start + size])
        new = bytearray(code)
        cms = compressed_mesh(data, blocks, shape)
        starts, args, keys, problems = walk(code)
        if not problems and not (cms and any(not key_names_triangle(cms, k) for k in keys)):
            continue
        for kind, i, parent in sorted(set(problems), key=lambda x: x[1]):
            if parent is not None and code[parent] in JUMPS and parent not in args:
                # reached through a plain jump (one successor, no test): close the branch at the jump,
                # so the bad target byte -- which may belong to another instruction -- stays untouched
                what = ('%s %02X' % (kind, code[i])) if 0 <= i < len(code) else kind
                report.append('MOPP %d bytes: jump %02X at %d lands at %d (%s) -> 00'
                              % (size, code[parent], parent, i, what))
                new[parent] = 0x00
            elif kind != 'jump out of the code' and i not in args:
                report.append('MOPP %d bytes: %s opcode %02X at %d -> 00' % (size, kind, code[i], i))
                new[i] = 0x00
            else:
                raise ValueError('%s at %d, reached from %s: not handled' % (kind, i, parent))
        s2, a2, k2, p2 = walk(bytes(new))
        assert not p2, ('still broken', p2)
        assert k2 == keys, ('leaf keys changed', len(keys), len(k2))
        if cms:                                     # leaves whose key names no triangle
            leaves = {}
            s2, a2, k2, p2 = walk(bytes(new), leaves)
            bad = {k for k in k2 if not key_names_triangle(cms, k)}
            for i in sorted(p for p, ks in leaves.items() if ks & bad):
                if not leaves[i] <= bad or i in a2:
                    raise ValueError('leaf at %d also yields a valid key, or is an argument: not handled' % i)
                report.append('MOPP %d bytes: leaf %02X at %d gives key %s, past its compressed mesh -> 00'
                              % (size, new[i], i, ' '.join('%08X' % k for k in sorted(leaves[i]))))
                new[i] = 0x00
            if bad:
                s3, a3, k3, p3 = walk(bytes(new))
                assert not p3, ('broken after closing bad leaves', p3)
                assert k3 == k2 - bad, ('leaf keys after closing bad leaves', len(k2), len(bad), len(k3))
        out[start:start + size] = new
    if not report:
        return None, []
    return bytes(out), report


# --- the installed list (as GrassBounds resolves it) ---------------------------------------------------
class BsaIndex:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            head = f.read(36)
            magic, ver, off, flags, nfold, nfile, lfold, lfile, _ = struct.unpack_from('<4sIIIIIIIH', head)
            assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
            f.seek(0)
            d = f.read(off + 24 * nfold + lfold + nfold + 16 * nfile + lfile + 16)
        self.flags = flags
        counts, p = [], off
        for _ in range(nfold):
            counts.append(struct.unpack_from('<QIIQ', d, p)[1]); p += 24
        entries = []
        for count in counts:
            n = d[p]
            folder = d[p + 1:p + n].decode('latin1').rstrip('\0'); p += 1 + n
            for _ in range(count):
                _, size, foff = struct.unpack_from('<QII', d, p); p += 16
                entries.append([folder, None, size, foff])
        for e in entries:
            end = d.index(b'\0', p); e[1] = d[p:end].decode('latin1'); p = end + 1
        self.files = {(fo + BS + na).lower(): (sz, of) for fo, na, sz, of in entries}

    def read(self, name):
        size, off = self.files[name]
        compressed = bool(self.flags & 0x4) != bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        with open(self.path, 'rb') as f:
            f.seek(off); d = f.read(size)
        p = 0
        if self.flags & 0x100:                      # embedded file name
            p = 1 + d[0]
        if compressed:
            raw = struct.unpack_from('<I', d, p)[0]
            out = lz4.frame.decompress(d[p + 4:])
            assert len(out) == raw, (name, len(out), raw)
            return out
        return d[p:]


def enabled_mods(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8') as f:
        return [l[1:].rstrip('\r\n') for l in f if l.startswith('+')]


def load_order(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'loadorder.txt'), encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]


def loose_dirs(root, mods):
    """Loose-file sources, highest priority first: overwrite, enabled mods, Stock Game/Data."""
    out = [('overwrite', os.path.join(root, 'overwrite'))]
    out += [(m, os.path.join(root, 'mods', m)) for m in mods if m != MOD]
    out.append(('Stock Game', os.path.join(root, 'Stock Game', 'Data')))
    return out


def data_file(root, mods, rel):
    for src, d in loose_dirs(root, mods):
        f = os.path.join(d, *rel.split(BS))
        if os.path.isfile(f):
            return src, f
    return None, None


def archives(root, mods, profile, plugins):
    ini = open(os.path.join(root, 'profiles', profile, 'Enderal.ini'), encoding='utf-8', errors='replace').read()
    names = []
    for key in ('sResourceArchiveList', 'sResourceArchiveList2'):
        m = re.search(r'(?im)^%s=(.*)$' % key, ini)
        names += [n.strip() for n in m.group(1).split(',') if n.strip()]
    for plug in plugins:
        names.append(os.path.splitext(plug)[0] + '.bsa')
    out = []
    for n in names:
        src, path = data_file(root, mods, n)
        if path:
            out.append((src, path))
    return out                                      # load order: later wins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--all-sources', action='store_true')
    a = ap.parse_args()
    mods = enabled_mods(a.modlist, a.profile)
    plugins = load_order(a.modlist, a.profile)

    # every copy of every mesh: loose (highest priority first), then archives (last loaded first)
    copies = {}                                     # rel -> [(source, reader)] winner first
    for src, d in loose_dirs(a.modlist, mods):
        md = os.path.join(d, 'meshes')
        for r, _, fs in os.walk(md):
            for fn in fs:
                if fn.lower().endswith('.nif'):
                    f = os.path.join(r, fn)
                    rel = os.path.relpath(f, d).replace('/', BS)
                    copies.setdefault(rel.lower(), []).append((src, rel, lambda f=f: open(f, 'rb').read()))
    bsas = archives(a.modlist, mods, a.profile, plugins)
    for src, path in reversed(bsas):
        b = BsaIndex(path)
        for key in b.files:
            if key.endswith('.nif'):
                copies.setdefault(key, []).append(('%s (%s)' % (os.path.basename(path), src), key,
                                                   lambda b=b, key=key: b.read(key)))

    out = os.path.join(a.modlist, 'mods', MOD)
    if not a.dry_run and os.path.isdir(os.path.join(out, 'meshes')):
        shutil.rmtree(os.path.join(out, 'meshes'))
    scanned = with_mopp = 0
    written, refused, losing = [], [], []
    for key, srcs in sorted(copies.items()):
        for n, (src, rel, read) in enumerate(srcs if a.all_sources else srcs[:1]):
            data = read()
            scanned += 1
            if b'bhkMoppBvTreeShape' not in data:
                continue
            with_mopp += 1
            try:
                fixed, report = fix(data)
            except (AssertionError, ValueError, struct.error) as e:
                refused.append((rel, src, str(e)))
                continue
            if not fixed:
                continue
            if n:                                   # a copy that does not win: report only
                losing.append((rel, src, report))
                continue
            diff = sum(1 for x, y in zip(data, fixed) if x != y)
            assert len(fixed) == len(data) and diff == len(report), (rel, diff, len(report))
            written.append((rel, src, report))
            if not a.dry_run:
                dst = os.path.join(out, *rel.split(BS))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(fixed)
    if not a.dry_run:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'meta.ini'), 'w', encoding='utf-8') as f:
            f.write('[General]\ngameName=EnderalSE\nmodid=0\nversion=1.0.0\ninstallationFile=\nrepository=\n'
                    'notes=Generated by zenderal-patches src/CollisionMoppFix/tools/01-fix-broken-mopp.py\n')

    for rel, src, report in written:
        print('fixed   %s  [from %s]' % (rel, src))
        for line in report:
            print('          ' + line)
    for rel, src, report in losing:
        print('broken (does not win, not shipped)  %s  [%s]: %s' % (rel, src, '; '.join(report)))
    for rel, src, why in refused:
        print('REFUSED %s  [%s]: %s' % (rel, src, why))
    print('%s %d meshes; scanned %d copies (%d with MOPP) of %d mesh paths, %d archives'
          % ('would write' if a.dry_run else 'wrote', len(written), scanned, with_mopp, len(copies), len(bsas)))
    if refused:
        raise SystemExit('%d meshes could not be checked or fixed (above)' % len(refused))


if __name__ == '__main__':
    main()
