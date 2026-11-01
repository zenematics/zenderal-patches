r"""Build `Zenderal - Grass Lighting Fix` from the installed list -- never hand-edit its meshes.

Why: Enderal 2.1.4 fixed "meshes appearing too bright under shadows during daytime"
(enderalse commit 23eb96a9f8, 2025-08-02, "Hortophyll: fixed mesh lighting following Catnyss'
instructions" = Enderal - Fixed Mesh Lighting, Nexus 826, merged into the base game). On 596 grass,
flora and tree meshes the BSLightingShaderProperty's Emissive Multiple went 1.0 -> 0.0. The emissive
colour on those shapes is black, so the multiplier looks inert, but SureAI's own fix was exactly that
one float, and with it gone the grass stops glowing in shadow.

Third-party grass written for Skyrim never got the fix, so every grass mesh it ships brings the glow
back. This script copies each WINNING loose grass/flora mesh in scope and applies the same edit:
for every BSLightingShaderProperty whose emissive colour is (0,0,0) and whose multiple is > 0, set
the multiple to 0.0. Coloured emissive (a real glow) is left alone. One float per shape changes; the
file keeps its length and every other byte. Meshes Enderal's own archives win are already fixed.

Scope:
  * the model of every winning GRAS record, when a loose mod file wins it;
  * every winning loose mesh of the grass mods in GRASS_MODS (their plant/flora meshes too).

The meshes are other authors' work, so they are generated from the user's install, never committed.
Re-run after any grass mod is added, removed, reordered or updated.

Usage:  python 01-zero-grass-emissive.py [--modlist <MO2 root>] [--profile Ultra] [--dry-run]
"""
import argparse
import os
import shutil
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'HorseCloakFluffFix', 'tools'))
from nif import Reader  # noqa: E402


class Nif:
    """Header-only NIF reader: block types and offsets. Accepts SE (BS 100) and LE (BS 83) files --
    some grass mods ship LE meshes, and BSLightingShaderProperty is laid out the same in both up to
    Emissive Multiple, which is all this script touches."""

    def __init__(self, path):
        self.data = bytearray(open(path, 'rb').read())
        r = Reader(self.data, self.data.index(b'\n') + 1)
        ver = r.take('I')
        assert ver == 0x14020007, hex(ver)
        r.skip(1)                                   # endian
        assert r.take('I') == 12                    # user version
        nblocks = r.take('I')
        bsver = r.take('I')
        assert bsver in (83, 100), bsver
        for _ in range(3):                          # author / process / export short strings
            r.skip(r.take('B'))
        types = []
        for _ in range(r.take('H')):
            n = r.take('I'); types.append(bytes(self.data[r.p:r.p + n]).decode('latin1')); r.skip(n)
        tidx = [r.take('H') for _ in range(nblocks)]
        sizes = [r.take('I') for _ in range(nblocks)]
        nstr = r.take('I'); r.skip(4)
        for _ in range(nstr):
            r.skip(r.take('I'))
        r.skip(4 * r.take('I'))                     # groups
        self.blocks, p = [], r.p
        for i in range(nblocks):
            self.blocks.append((types[tidx[i] & 0x7FFF], p, sizes[i])); p += sizes[i]

    def save(self, path):
        open(path, 'wb').write(self.data)

MOD = 'Zenderal - Grass Lighting Fix'
GRASS_MODS = [  # the enabled ones are used; each EGR/Tamrielic pair is plain vs ENB-complex-grass build
    'Enderal Grass Redone (EGR Default)',
    'Enderal Grass Redone (EGR ENB)',
    'Rock Grass for ENB Complex Grass SE',
    'Landscapes - Cathedral Concept (Grass Only)',
    'Folkvangr - Grass and Landscape Overhaul',
    'Origins Of Forest - 3D Forest Grass',
    'Cathedral - 3D Pine Grass - High Poly Green Grass Update',
    'Cathedral - 3D Pine Grass',
    'Tamrielic Grass',
    'Tamrielic Grass for ENB Complex Grass',
]
BS = '\\'


def enabled_mods(root, profile):
    """Enabled mods, highest priority first (modlist.txt is top = wins)."""
    with open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8') as f:
        return [l[1:].rstrip('\r\n') for l in f if l.startswith('+')]


def active_plugins(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'plugins.txt'), encoding='utf-8', errors='replace') as f:
        return [l.strip()[1:] for l in f if l.strip().startswith('*')]


def plugin_paths(root, mods):
    where = {}
    for m in reversed(mods):                     # lowest priority first, higher overwrite
        d = os.path.join(root, 'mods', m)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(('.esp', '.esm', '.esl')):
                    where[f.lower()] = os.path.join(d, f)
    data = os.path.join(root, 'Stock game', 'Data')
    for f in os.listdir(data):
        if f.lower().endswith(('.esp', '.esm', '.esl')) and f.lower() not in where:
            where[f.lower()] = os.path.join(data, f)
    return where


def gras_models(root, mods, profile):
    """(master, objectid) -> model path of the winning GRAS record."""
    where = plugin_paths(root, mods)
    order = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'] + [
        p for p in active_plugins(root, profile) if p.lower() not in ('skyrim.esm', 'update.esm', 'enderal - forgotten stories.esm')]
    win = {}
    for plug in order:
        path = where.get(plug.lower())
        if not path:
            continue
        d = open(path, 'rb').read()
        hsz = struct.unpack_from('<I', d, 4)[0]
        masters, q = [], 24
        while q < 24 + hsz:
            t = d[q:q + 4]; sz = struct.unpack_from('<H', d, q + 4)[0]
            if t == b'MAST':
                masters.append(d[q + 6:q + 6 + sz - 1].decode('cp1252'))
            q += 6 + sz

        def walk(p, stop):
            while p < stop:
                t = d[p:p + 4]
                if t == b'GRUP':
                    gsz, lab, gt = struct.unpack_from('<I4sI', d, p + 4)
                    if gt == 0 and lab != b'GRAS':
                        p += gsz; continue
                    walk(p + 24, p + gsz); p += gsz; continue
                sz, fl, fid = struct.unpack_from('<III', d, p + 4)
                if t == b'GRAS':
                    body = d[p + 24:p + 24 + sz]
                    if fl & 0x40000:
                        body = zlib.decompress(body[4:])
                    k, model = 0, None
                    while k + 6 <= len(body):
                        st = body[k:k + 4]; ssz = struct.unpack_from('<H', body, k + 4)[0]
                        if st == b'MODL':
                            model = body[k + 6:k + 6 + ssz].split(b'\0')[0].decode('cp1252')
                        k += 6 + ssz
                    mi = fid >> 24
                    win[((masters[mi] if mi < len(masters) else plug).lower(), fid & 0xFFFFFF)] = model
                p += 24 + sz
        walk(24 + hsz, len(d))
    return [m for m in win.values() if m]


def winning_loose(root, mods, rel):
    rel = rel.replace('/', BS).lower()
    for m in mods:
        if m == MOD:
            continue
        f = os.path.join(root, 'mods', m, *rel.split(BS))
        if os.path.exists(f):
            return m, f
    return None, None


def zero_emissive(nif):
    """Set Emissive Multiple to 0 on black-emissive BSLightingShaderProperty blocks. Returns count changed."""
    n = 0
    for typ, p, size in nif.blocks:
        if typ != 'BSLightingShaderProperty':
            continue
        r = Reader(nif.data, p)
        r.skip(4)                                   # shader type
        r.skip(4)                                   # name
        r.skip(4 * r.take('I'))                     # extra data refs
        r.skip(4)                                   # controller
        r.skip(8)                                   # shader flags 1 + 2
        r.skip(16)                                  # uv offset + scale
        r.skip(4)                                   # texture set
        col = r.take('3f')
        mult_at = r.p
        mult = r.take('f')
        if mult > 0 and max(col) == 0.0:
            struct.pack_into('<f', nif.data, mult_at, 0.0)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default=r'E:\Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    mods = enabled_mods(a.modlist, a.profile)
    grass_mods = [m for m in GRASS_MODS if m in mods]
    if not any(m.startswith('Enderal Grass Redone') for m in grass_mods):
        raise SystemExit('no Enderal Grass Redone build is enabled (update GRASS_MODS?)')
    print('grass mods in scope:', grass_mods)

    candidates = {}
    for model in gras_models(a.modlist, mods, a.profile):
        rel = model if model.lower().startswith('meshes' + BS) else 'meshes' + BS + model
        m, f = winning_loose(a.modlist, mods, rel)
        if f:
            candidates[rel.lower()] = (m, f)
    for gm in grass_mods:
        base = os.path.join(a.modlist, 'mods', gm)
        for r, _, fs in os.walk(os.path.join(base, 'meshes')):
            for fn in fs:
                if fn.lower().endswith('.nif'):
                    rel = os.path.relpath(os.path.join(r, fn), base).lower()
                    m, f = winning_loose(a.modlist, mods, rel)
                    if m == gm:
                        candidates.setdefault(rel, (m, f))

    out = os.path.join(a.modlist, 'mods', MOD)
    if not a.dry_run and os.path.isdir(os.path.join(out, 'meshes')):
        shutil.rmtree(os.path.join(out, 'meshes'))
    written = shapes = 0
    per_mod = {}
    for rel, (m, f) in sorted(candidates.items()):
        try:
            nif = Nif(f)
        except (AssertionError, ValueError, struct.error) as e:
            print(f'skip (unreadable) {rel}: {e}')
            continue
        n = zero_emissive(nif)
        if not n:
            continue
        # re-read to prove the edit landed and nothing else moved
        check = bytearray(open(f, 'rb').read())
        diff = sum(1 for x, y in zip(check, nif.data) if x != y)
        if len(check) != len(nif.data) or diff > 4 * n:
            raise SystemExit(f'{rel}: unexpected change ({diff} bytes for {n} shapes)')
        written += 1; shapes += n; per_mod[m] = per_mod.get(m, 0) + 1
        if not a.dry_run:
            dst = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            nif.save(dst)
    for m, c in sorted(per_mod.items(), key=lambda x: -x[1]):
        print(f'  {c:4} meshes from {m}')
    print(f'{"would write" if a.dry_run else "wrote"} {written} meshes ({shapes} shapes zeroed) to {out}'
          f' from {len(candidates)} candidates')


if __name__ == '__main__':
    main()
