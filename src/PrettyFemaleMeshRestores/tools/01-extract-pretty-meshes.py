"""Rebuild the `Zenderal - Pretty Female Mesh Restores` MO2 mod from the Pretty mods' own BSAs.

Why: the Pretty * Armory / Pretty Enderal Clothing mods pack their redesigned meshes in BSAs, while
CBBE ships LOOSE CBBE conversions of the vanilla meshes at the same paths. A loose file beats every BSA
regardless of MO2 priority, so female characters got CBBE's vanilla-shape mesh -- and where Pretty
also ships a loose re-authored texture (e.g. clothes/merchantclothes/torsof_d.dds), that texture is
wrapped over UVs it was never painted for. First reported on the merchant clothes ("Fine Clothes").

This mod ships Pretty's own mesh loose for every path where an enabled Pretty BSA collides with a loose
CBBE mesh, so Pretty wins again. It must sort ABOVE CBBE in MO2 (modlist.txt is highest-priority-first).
Trade-off: Pretty's meshes carry no BODYTRI, so RaceMenu body morphs do not reshape these outfits.

The collision set is DERIVED from the live profile, not hardcoded, and asserted against EXPECTED so a
Pretty or CBBE update fails loudly instead of shipping quietly. The meshes are Pretty's, so they are
extracted from the user's own install and never committed.

Usage:  python 01-extract-pretty-meshes.py [<modlist root>] [<profile>]
        (defaults E:/Zenderal, "Alpha 0.5")
"""
import os, sys, struct, hashlib, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SettingsApplier', 'tools', 'capture'))
from bsa import lz4_frame  # noqa: E402

MOD = 'Zenderal - Pretty Female Mesh Restores'
LOSER = "Caliente's Beautiful Bodies Enhancer -CBBE-"
EXPECTED = 157  # verified 2026-10-11 against Alpha 0.5; re-check the diff before raising it
BS = chr(92)


def bsa_entries(path):
    """Yield (lower-case path with '/', reader) for every file in an SE BSA (v105)."""
    with open(path, 'rb') as fh:
        d = fh.read()
    magic, ver, fro, aflags, fcount, filecount, tfnl, tfil, ff = struct.unpack_from('<4sIIIIIIII', d, 0)
    assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
    p = fro
    counts = []
    for _ in range(fcount):
        counts.append(struct.unpack_from('<QIIQ', d, p)[1]); p += 24
    recs = []
    for c in counts:
        ln = d[p]; name = d[p + 1:p + ln].rstrip(b'\0').decode('latin1'); p += 1 + ln
        for _ in range(c):
            h, size, off = struct.unpack_from('<QII', d, p); p += 16
            recs.append((name, size, off))
    names = d[p:p + tfil].split(b'\0')

    def reader(size, off, want):
        def read():
            comp = bool(aflags & 4) ^ bool(size & 0x40000000)
            sz = size & 0x3FFFFFFF
            q = off
            if aflags & 0x100:
                ln = d[q]; q += 1 + ln; sz -= 1 + ln
            blob = d[q:q + sz]
            if not comp:
                return blob
            data = lz4_frame(blob[4:])
            assert len(data) == struct.unpack_from('<I', blob, 0)[0], want
            return data
        return read

    for (dn, size, off), n in zip(recs, names):
        rel = (dn + '/' + n.decode('latin1')).replace(BS, '/').lower()
        yield rel, reader(size, off, rel)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
    profile = sys.argv[2] if len(sys.argv) > 2 else 'Alpha 0.5'
    mods_dir = os.path.join(root, 'mods')
    prof_dir = os.path.join(root, 'profiles', profile)
    with open(os.path.join(prof_dir, 'modlist.txt'), encoding='utf-8') as fh:
        enabled = [l[1:].strip() for l in fh if l.startswith('+')]
    assert LOSER in enabled, f'{LOSER} not enabled in {profile}'
    with open(os.path.join(prof_dir, 'loadorder.txt'), encoding='utf-8') as fh:
        load = [l.strip().lower() for l in fh if l.strip() and not l.startswith('#')]

    loser_dir = os.path.join(mods_dir, LOSER)
    loose = set()
    for r, _, fs in os.walk(os.path.join(loser_dir, 'meshes')):
        for f in fs:
            loose.add(os.path.relpath(os.path.join(r, f), loser_dir).replace(BS, '/').lower())

    # BSAs load with their plugin, so among Pretty BSAs the one whose plugin loads LATER wins a path.
    bsas = []
    for m in enabled:
        if not m.startswith('Pretty'):
            continue
        for f in os.listdir(os.path.join(mods_dir, m)):
            if not f.lower().endswith('.bsa'):
                continue
            # "<plugin>.bsa" or "<plugin> - Textures.bsa": the longest plugin name prefixing the stem
            stem = f[:-4].lower()
            hits = [(len(p), i) for i, p in enumerate(load) if stem == p[:-4] or stem.startswith(p[:-4] + ' - ')]
            assert hits, f'{m}/{f}: no plugin for this BSA in the load order'
            pos = max(hits)[1]
            bsas.append((pos, m, f))
    bsas.sort()

    winner = {}
    for pos, m, f in bsas:
        for rel, read in bsa_entries(os.path.join(mods_dir, m, f)):
            if rel in loose:
                winner[rel] = (m, f, read)

    if len(winner) != EXPECTED:
        raise SystemExit(f'expected {EXPECTED} colliding meshes, found {len(winner)} -- review before updating EXPECTED')

    out_root = os.path.join(mods_dir, MOD)
    if os.path.isdir(os.path.join(out_root, 'meshes')):
        shutil.rmtree(os.path.join(out_root, 'meshes'))
    for rel in sorted(winner):
        m, f, read = winner[rel]
        blob = read()
        assert blob[:20] == b'Gamebryo File Format', rel
        out = os.path.join(out_root, *rel.split('/'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as fh:
            fh.write(blob)
        print(f'{len(blob):>9}  {hashlib.sha1(blob).hexdigest()[:12]}  {rel}  <- {m}/{f}')
    print(f'{len(winner)} files -> {out_root}')


if __name__ == '__main__':
    main()
