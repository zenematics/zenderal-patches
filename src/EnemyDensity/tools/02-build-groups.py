"""Turn enemy-groups.json (01-plan-groups.py) into the placed enemies of `Zenderal - Enemy Density`, and write the
plugin header. Never hand-edit EnemyDensityESP/Worldspaces or RecordData.yaml: regenerate.

Every enemy is a NEW placed NPC (FormIDs from 0x800); no existing ref is touched. Its base is either an Enderal
NPC (EditorID in the plan, resolved here and checked against its WINNING record: present, not deleted, not
Unique/Essential/Protected, and not a Mihail skeleton: neither won by mihailancientskeletons.esp nor on its race)
or one of Zenderal - Goblins' goblins ('GOB:<role>', Goblins' 03-build-packs.py BASES), which carry ZEN_GoblinRespawn (back after ZEN_GoblinRespawnDays). Enderal's own NPCs come back with the
engine's cell reset, like every other placed creature.

The WRLD and cell headers are forwarded exactly as Zenderal - Goblins does (its 03-build-packs.py helpers,
imported): from the last overrider before Zenderal - Goblins, which forwards the same ones. This plugin loads
right after `Zenderal - Goblins Dismembering.esp`; re-run 01 and 02 whenever Goblins' are re-run.

Usage:  python 02-build-groups.py <all dir>
"""
import collections
import importlib.util
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location('goblins_build', os.path.join(REPO, 'src', 'Goblins', 'tools', '03-build-packs.py'))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)                      # reads sys.argv[1] (<all dir>) like this script

ESP = os.path.join(HERE, '..', 'EnemyDensityESP')
PLAN = os.path.join(HERE, 'enemy-groups.json')
MOD_KEY = 'Zenderal - Enemy Density.esp'
GOBLINS = 'Zenderal - Goblins.esp'
FIRST_REF = 0x800
NAME = re.compile(r'^(.+) - ([0-9A-F]{6})_(.+)\.yaml$')
BAD_FLAGS = ('Unique', 'Essential', 'Protected')
MIHAIL = 'mihailancientskeletons.esp'      # its skeletons crashed twice in the hordes (EnemyDensity.md): never use them


def resolve_bases(plan, src):
    """EditorID -> FormKey from the base decompiles; then the winning record of each must be a usable enemy."""
    by_edid = {}
    for root in (os.path.join(REPO, 'reference', 'base', 'Skyrim'), os.path.join(REPO, 'reference', 'base', 'EnderalFS')):
        for f in os.listdir(os.path.join(root, 'Npcs')):
            m = NAME.match(f)
            if m:
                by_edid.setdefault(m.group(1), f'{m.group(2)}:{m.group(3)}')
    wanted = sorted({r for s in plan for r in s['roles'] if not r.startswith('GOB:')})
    missing = [e for e in wanted if e not in by_edid]
    assert not missing, f'unknown EditorIDs: {missing}'
    out = {}
    for e in wanted:
        fk = by_edid[e]
        fid, plugin = fk.split(':', 1)
        tail = f'{fid}_{plugin}.yaml'
        win = None
        for p, root in src:
            d = os.path.join(root, 'Npcs')
            if os.path.isdir(d):
                hits = [f for f in os.listdir(d) if f.endswith(' - ' + tail)]
                if hits:
                    win = (p, os.path.join(d, hits[0]))
        assert win, fk
        text = B.read(win[1])
        flags = re.search(r'^Configuration:\r\n  Flags:\r\n((?:  - .+\r\n)+)', text, re.M)
        flags = re.findall(r'- (\S+)', flags.group(1)) if flags else []
        bad = [f for f in flags if f in BAD_FLAGS]
        deleted = re.search(r'^MajorRecordFlagsRaw: (\d+)', text, re.M)
        race = re.search(r'^Race: (\S+)', text, re.M)
        assert not bad, (e, fk, bad, win[0])
        assert win[0] != MIHAIL and not (race and race.group(1).endswith(':' + MIHAIL)), (e, fk, 'Mihail skeleton', win[0])
        assert not (deleted and int(deleted.group(1)) & 0x20), (e, fk, 'deleted', win[0])
        out[e] = fk
        print(f'  {e:42} {fk:42} wins: {win[0]}')
    return out


def main():
    plan = json.load(open(PLAN, encoding='utf-8'))
    src = B.sources()                            # every source loading before Zenderal - Goblins
    bases = resolve_bases(plan, [('Skyrim.esm', os.path.join(REPO, 'reference', 'base', 'Skyrim')),
                                 ('Enderal - Forgotten Stories.esm', os.path.join(REPO, 'reference', 'base', 'EnderalFS'))]
                          + [(p, os.path.join(B.ALL, re.sub(r'[^A-Za-z0-9]', '', p)))
                             for p in [ln[1:].strip() for ln in open(B.PLUGINS, encoding='utf-8') if ln.startswith('*')]
                             if os.path.isdir(os.path.join(B.ALL, re.sub(r'[^A-Za-z0-9]', '', p)))])
    for role, hexid in B.BASES.items():
        bases['GOB:' + role] = f'{hexid}:{GOBLINS}'
    shutil.rmtree(os.path.join(ESP, 'Worldspaces'), ignore_errors=True)
    outws = os.path.join(ESP, 'Worldspaces', B.WS)

    wrld = [(p, os.path.join(r, 'Worldspaces', B.WS, 'RecordData.yaml')) for p, r in src
            if os.path.isfile(os.path.join(r, 'Worldspaces', B.WS, 'RecordData.yaml'))]
    wplugin, wpath = wrld[-1]
    B.write(os.path.join(outws, 'RecordData.yaml'), B.header(B.read(wpath)))
    print(f'WRLD Vyn header <- {wplugin}')

    by_cell = {}
    for s in sorted(plan, key=lambda s: (s['cell'][0], s['cell'][1], s['center'][0], s['center'][1])):
        by_cell.setdefault((tuple(s['cell']), s['cell_fk']), []).append(s)
    # A site keeps the ref FormIDs it already has (01 carries them over); only new sites get fresh IDs.
    kept = [r for s in plan if len(s.get('refs', [])) == len(s['members']) for r in s['refs']]
    assert len(kept) == len(set(kept)), 'duplicate ref FormIDs in plan'
    fid = max([int(r, 16) + 1 for r in kept] + [FIRST_REF])
    for s in plan:
        if len(s.get('refs', [])) != len(s['members']):
            s['refs'] = []
    winners = collections.Counter()
    for ((gx, gy), cell_fk), sites in sorted(by_cell.items()):
        found = [(p, B.cell_dir(r, gx, gy, cell_fk), r) for p, r in src]
        found = [(p, d, r) for p, d, r in found if d]
        assert found, cell_fk
        plugin, cdir, root = found[-1]
        winners[plugin] += 1
        text = B.read(os.path.join(cdir, 'RecordData.yaml'))
        assert text.startswith(f'FormKey: {cell_fk}'), cdir
        body = ['Temporary:']
        for s in sites:
            fresh = not s['refs']
            for k, ((x, y, z, rot), role) in enumerate(zip(s['members'], s['roles'])):
                if fresh:
                    s['refs'].append(f'{fid:06X}')
                    fid += 1
                body += ['- MutagenObjectType: PlacedNpc',
                         f'  FormKey: {s["refs"][k]}:{MOD_KEY}',
                         f'  Base: {bases[role]}',
                         '  Placement:',
                         f'    Position: {x}, {y}, {z + 8}',
                         f'    Rotation: 0, 0, {rot}']
        blk, sub = B.block_dirs(gx, gy)
        rel = os.path.relpath(cdir, os.path.join(root, 'Worldspaces', B.WS))
        B.write(os.path.join(outws, rel, 'RecordData.yaml'), B.header(text) + B.NL.join(body) + B.NL + B.trailer(text))
        for g in ((blk,), (blk, sub)):
            gsrc = [os.path.join(r, 'Worldspaces', B.WS, *g, 'GroupRecordData.yaml') for _, r in src]
            gsrc = [p for p in gsrc if os.path.isfile(p)]
            shutil.copyfile(gsrc[-1], os.path.join(outws, *g, 'GroupRecordData.yaml'))
    assert fid <= 0x1000, f'ESL range exhausted at {fid:X}'
    n = sum(len(s['refs']) for s in plan)
    assert n == sum(len(s['members']) for s in plan) and len({r for s in plan for r in s['refs']}) == n
    print(f'{n} enemies in {len(plan)} groups, {len(by_cell)} cells, last ref {fid - 1:X}; cell headers from: ' +
          ', '.join(f'{p} {c}' for p, c in winners.most_common()))

    used = set()
    top = os.path.join(os.path.normpath(ESP), 'RecordData.yaml')
    for dirpath, _, files in os.walk(os.path.normpath(ESP)):
        for f in files:
            path = os.path.join(dirpath, f)
            if f.endswith('.yaml') and path != top:
                used |= set(re.findall(r'[0-9A-F]{6}:([^\r\n:]+?\.(?:esm|esp|esl))', B.read(path)))
    used.discard(MOD_KEY)
    order = [ln[1:].strip() for ln in open(B.PLUGINS, encoding='utf-8') if ln.startswith('*')]
    extra = sorted(used - set(B.BASE_MASTERS), key=lambda p: order.index(p))
    masters = B.BASE_MASTERS + extra
    lines = ['SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', f'ModKey: {MOD_KEY}',
             'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
             '  Author: Zenderal',
             '  Description: More enemy groups across Vyn, built from the creatures Enderal places in each region.',
             '  MasterReferences:']
    for m in masters:
        lines += [f'  - Master: {m}', '    FileSize: 0']
    lines += ['  INTV: 1']
    B.write(top, B.NL.join(lines) + B.NL)
    B.write(os.path.join(ESP, 'spriggit-meta.json'), json.dumps(
        {'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.40.0', 'Release': 'EnderalSE', 'ModKey': MOD_KEY},
        indent=2) + '\n')
    print('masters: ' + ', '.join(masters))
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:   # plan gains each group's ref FormIDs
        json.dump(plan, fh, indent=1)
        fh.write('\n')


if __name__ == '__main__':
    main()
