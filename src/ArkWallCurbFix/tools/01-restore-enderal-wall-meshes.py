"""Rebuild the `Zenderal - Ark Wall Curb Fix` MO2 mod: Enderal's ORIGINAL (non-parallax) Ark wall meshes.

Enderal's own Ark wall meshes use no parallax. SRP Enderal - Architecture switched every shape to parallax
(BSLightingShaderProperty shader type 0 -> 3, shader flags 1 bit 11) with geometry, UVs and diffuse/normal paths
byte-identical. On the curb along the wall base that parallax smears the stone into streaks that slide with the
camera, ENB on or off (reported 2026-10-11 at `_00E_Ark_1024WallGate02 041448`, Myrad Tower, Ark's Western Wall).

VERIFIED in game 2026-10-11: Enderal's original `1024wallgate02.nif` fixed the curb. Two narrower attempts did NOT:
reverting only the `brick02` shape, and reverting only the `border02` trim shape (that one looked fixed once, but the
screenshot came from a session started BEFORE the file was swapped - it was still showing the original mesh).
So this ships Enderal's original mesh, extracted from the game BSAs, for every SRP mesh that has a parallax
`border02` (the Ark curb/trim) shape - SRP's textures still apply, only SRP's parallax on these walls is gone.

Not committed (SureAI's meshes, from the user's own install). Must sort ABOVE SRP Enderal - Architecture.
Re-run after any SRP update, then rebuild CRDW.

Usage:  python 01-restore-enderal-wall-meshes.py [--dry-run]
"""
import os, re, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'HorseCloakFluffFix', 'tools'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SettingsApplier', 'tools', 'capture'))
from nif import Nif, Reader  # noqa: E402
import bsa  # noqa: E402

Z = 'E:/Zenderal'
PROFILE = 'Alpha 0.5'
MOD = 'Zenderal - Ark Wall Curb Fix'
SRC = 'SRP Enderal - Architecture (2K)'
DIFFUSE = 'textures\\enderal\\architecture\\ark\\border02.dds'
ARCHIVES = ['E - Meshes.bsa', 'E - Update.bsa']  # E - Update loads last and wins
EXPECTED_MESHES = 36  # Alpha 0.5, 2026-10-11


def has_parallax_border02(path):
    n = Nif(path)
    for sh in n.shapes():
        typ, p, _ = n.blocks[sh['shader']]
        if typ != 'BSLightingShaderProperty':
            continue
        r = Reader(n.data, p)
        stype = r.take('I')
        r.take('i')
        r.skip(4 * r.take('I'))
        r.take('i')
        r.skip(8 + 16)
        ts = r.take('i')
        if stype != 3 or ts < 0:
            continue
        tr = Reader(n.data, n.blocks[ts][1])
        tr.take('I')
        ln = tr.take('I')
        if bytes(n.data[tr.p:tr.p + ln]).decode('latin1').lower() == DIFFUSE:
            return True
    return False


def main():
    dry = '--dry-run' in sys.argv
    mods = [l[1:].strip() for l in open(f'{Z}/profiles/{PROFILE}/modlist.txt', encoding='utf-8')
            if l.startswith('+') and l[1:].strip() != MOD]
    base = f'{Z}/mods/{SRC}'
    todo = []
    for dp, _, fns in os.walk(os.path.join(base, 'meshes')):
        for f in fns:
            if not f.lower().endswith('.nif'):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, base)
            if next(m for m in mods if os.path.isfile(os.path.join(Z, 'mods', m, rel))) != SRC:
                continue  # another mod's mesh wins; not ours to replace
            try:
                if has_parallax_border02(path):
                    todo.append(rel.lower())
            except Exception:
                continue
    for rel in todo:
        print(rel)
    print(f'{len(todo)} meshes')
    if len(todo) != EXPECTED_MESHES:
        sys.exit(f'expected {EXPECTED_MESHES} meshes; review the list above, then update EXPECTED_MESHES')
    if dry:
        return
    found = {}
    with tempfile.TemporaryDirectory() as tmp:
        for b in ARCHIVES:
            for i, rel in enumerate(todo):
                sub = os.path.join(tmp, b, str(i))
                os.makedirs(sub, exist_ok=True)
                if bsa.extract(f'{Z}/Stock Game/Data/{b}', '^' + re.escape(rel) + '$', sub):
                    found[rel] = open(os.path.join(sub, os.path.basename(rel)), 'rb').read()
    missing = [r for r in todo if r not in found]
    if missing:
        sys.exit(f'no Enderal original for: {missing}')
    for rel, data in found.items():
        dst = os.path.join(Z, 'mods', MOD, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as fh:
            fh.write(data)
    print(f'done: {len(found)} original Enderal meshes in mods/{MOD}')


if __name__ == '__main__':
    main()
