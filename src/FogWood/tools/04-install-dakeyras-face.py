"""Dakeyras' face from a RaceMenu head export (curator, 2026-11-19: "change his appearance to my preset Zen's Joseph
Goatee").

His record (tools/02 DAKEYRAS_*) carries the preset's head parts, morphs, tint and weight, but a record alone gives a
dark, mismatched face: the engine wants pre-built facegen files, and the preset's High Poly Head parts and RaceMenu
morphs only come out right from RaceMenu itself. So: in game, with the preset loaded on the player, RaceMenu's Sculpt
tab -> Export Head -> a name; that writes
    <MO2 overwrite>\\SKSE\\Plugins\\CharGen\\Exported\\<name>.nif   (the whole head: skin, hair, brows, beard, eyes, mouth, scar)
    <MO2 overwrite>\\SKSE\\Plugins\\CharGen\\Exported\\<name>.dds   (the face tint)
and this tool copies them to where the engine looks for NPC 0x81F of Zenderal - Fog Wood.esp:
    meshes\\actors\\character\\FaceGenData\\FaceGeom\\Zenderal - Fog Wood.esp\\0000081F.nif
    textures\\actors\\character\\FaceGenData\\FaceTint\\Zenderal - Fog Wood.esp\\0000081F.dds
inside Zenderal - Patch Collection (not committed). The head parts baked into the .nif must be the record's: the tool
lists the .nif's shape names next to the record's parts so a mismatch shows before a test.

Usage:
    python src/FogWood/tools/04-install-dakeyras-face.py --list            # exports found
    python src/FogWood/tools/04-install-dakeyras-face.py --export <name>   # install that export
        [--target <MO2 mod folder>]   default <modlistRoot>/mods/Zenderal - Patch Collection
"""
import argparse
import glob
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
EXPORTED = os.path.join(TOOLS['modlistRoot'], 'overwrite', 'SKSE', 'Plugins', 'CharGen', 'Exported')
PLUGIN = 'Zenderal - Fog Wood.esp'
NPC_ID = 0x81F
RECORD = os.path.join(ROOT, 'src', 'FogWood', 'FogWoodESP', 'Npcs', 'ZFW_Rogue - %06X_%s.yaml' % (NPC_ID, PLUGIN))


def record_parts():
    t = open(RECORD, encoding='utf-8').read()
    m = re.search(r'^HeadParts:\n((?:- .*\n)+)', t, re.M)
    return [l[2:].strip() for l in m.group(1).splitlines()]


def nif_strings(path):
    d = open(path, 'rb').read()
    return sorted(set(s.decode('ascii') for s in re.findall(rb'[ -~]{6,}', d) if re.match(rb'^[A-Za-z0-9_ .:\\-]+$', s)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--export', help='the name given in RaceMenu (file name without extension)')
    ap.add_argument('--target', default=os.path.join(TOOLS['modlistRoot'], 'mods', 'Zenderal - Patch Collection'))
    args = ap.parse_args()
    if args.list or not args.export:
        print('RaceMenu exports in', EXPORTED)
        for f in sorted(glob.glob(os.path.join(EXPORTED, '*.nif'))):
            dds = f[:-4] + '.dds'
            print('  %-40s %7d bytes  tint %s' % (os.path.basename(f)[:-4], os.path.getsize(f), 'yes' if os.path.isfile(dds) else 'MISSING'))
        if not args.export:
            return
    nif = os.path.join(EXPORTED, args.export + '.nif')
    dds = os.path.join(EXPORTED, args.export + '.dds')
    assert os.path.isfile(nif), 'no export ' + nif
    assert os.path.isfile(dds), 'no tint ' + dds
    geom_dir = os.path.join(args.target, 'meshes', 'actors', 'character', 'FaceGenData', 'FaceGeom', PLUGIN)
    tint_dir = os.path.join(args.target, 'textures', 'actors', 'character', 'FaceGenData', 'FaceTint', PLUGIN)
    os.makedirs(geom_dir, exist_ok=True)
    os.makedirs(tint_dir, exist_ok=True)
    dst_nif = os.path.join(geom_dir, '%08X.nif' % NPC_ID)
    dst_dds = os.path.join(tint_dir, '%08X.dds' % NPC_ID)
    shutil.copyfile(nif, dst_nif)
    shutil.copyfile(dds, dst_dds)
    print('installed\n  %s (%d bytes)\n  %s (%d bytes)' % (dst_nif, os.path.getsize(dst_nif), dst_dds, os.path.getsize(dst_dds)))
    names = [s for s in nif_strings(nif) if not s.lower().endswith(('.dds', '.tri', '.nif')) and len(s) < 60]
    print('\nshapes/nodes in the export:', ', '.join(n for n in names if any(k in n.lower() for k in ('head', 'hair', 'brow', 'beard', 'eye', 'mouth', 'mark', 'scar', 'bop', 'hverg', 'klh', 'nord', 'redguard'))))
    print('record head parts:', ', '.join(record_parts()))
    print('check: every part above has a shape in the export, and nothing in the export is missing from the record.')


if __name__ == '__main__':
    main()
