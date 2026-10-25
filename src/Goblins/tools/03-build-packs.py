"""Turn goblin-packs.json (02-plan-packs.py) into the placed goblins of `Zenderal - Goblins`, and write the
plugin header. Never hand-edit GoblinsESP/Worldspaces or RecordData.yaml: regenerate.

Every goblin is a NEW placed NPC (FormIDs from 0x900); no existing ref is touched. Spriggit needs the
worldspace and every touched cell as overrides around the refs (arch-docs/workspace/spriggit.md: four
scaffolding files per exterior cell), so this forwards, per guardrail 5:
  * the Vyn WRLD header (truncated before TopCell) from its LAST overrider in the Ultra load order;
  * each touched cell's header (everything before Landscape/NavigationMeshes/refs, plus its trailing
    MajorFlags) from that cell's LAST overrider, and its block/sub-block group files.
Sources, in load order: reference/base/Skyrim, reference/base/EnderalFS, then <all>/<plugin> for every
enabled Ultra plugin before this one (src/UnresolvedRefsCleanup/tools/00a-serialize-all.py output).
The plugin must load right after the last of them (Golden Mare Mill SE.esp, 2026-10-21); re-run 02 and
03 after any Vyn cell editor changes. Masters are computed from the FormKeys this writes.

Usage:  python 03-build-packs.py <all dir>
"""
import json
import math
import os
import re
import shutil
import sys

ALL = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ESP = os.path.join(HERE, '..', 'GoblinsESP')
PLAN = os.path.join(HERE, 'goblin-packs.json')
WS = 'Vyn - 001D3C_Skyrim.esm'
MOD_KEY = 'Zenderal - Goblins.esp'
PLUGINS = os.path.join('E:/Zenderal', 'profiles', 'Ultra', 'plugins.txt')
NL = '\r\n'
FIRST_REF = 0x900
BASES = {'Goblin': '000810', 'Scout': '000811', 'Archer': '000812', 'Shaman': '000813', 'Chief': '000814'}
BASES.update(json.load(open(os.path.join(HERE, 'mihail-npcs.json'), encoding='utf-8')))   # 01b's Mihail roles
RESPAWN_GLOBAL = ('000820', 'ZEN_GoblinRespawnDays', 3)
BASE_MASTERS = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm']
REF_SECTIONS = re.compile(r'^(Temporary|Persistent|NavigationMeshes|Landscape|SubCells|TopCell|MajorFlags):')


def sources():
    plugins = [ln[1:].strip() for ln in open(PLUGINS, encoding='utf-8') if ln.startswith('*')]
    out = [('Skyrim.esm', os.path.join(REPO, 'reference', 'base', 'Skyrim')),
           ('Enderal - Forgotten Stories.esm', os.path.join(REPO, 'reference', 'base', 'EnderalFS'))]
    for p in plugins:
        if p == MOD_KEY:
            break                                   # only what loads before us can win a header we forward
        d = os.path.join(ALL, re.sub(r'[^A-Za-z0-9]', '', p))
        if os.path.isdir(os.path.join(d, 'Worldspaces', WS)):
            out.append((p, d))
    return out


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\n', NL)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def header(text):
    out = []
    for line in text.split(NL):
        if REF_SECTIONS.match(line):
            break
        out.append(line)
    return NL.join(out).rstrip(NL) + NL


def trailer(text):
    i = text.find(NL + 'MajorFlags:' + NL)
    return text[i + len(NL):] if i >= 0 else ''


def block_dirs(gx, gy):
    return f'{math.floor(gx / 32)}, {math.floor(gy / 32)}', f'{math.floor(gx / 8)}, {math.floor(gy / 8)}'


def cell_dir(root, gx, gy, cell_fk):
    """The cell's folder in a source tree, or None. Folder = '<EditorID> - <hex>_<plugin>' or '<hex>_<plugin>'."""
    blk, sub = block_dirs(gx, gy)
    d = os.path.join(root, 'Worldspaces', WS, blk, sub)
    if not os.path.isdir(d):
        return None
    fid, plugin = cell_fk.split(':', 1)
    tail = f'{fid}_{plugin}'
    hits = [f for f in os.listdir(d) if f == tail or f.endswith(' - ' + tail)]
    assert len(hits) <= 1, (d, hits)
    return os.path.join(d, hits[0]) if hits else None


def main():
    plan = json.load(open(PLAN, encoding='utf-8'))
    src = sources()
    shutil.rmtree(os.path.join(ESP, 'Worldspaces'), ignore_errors=True)
    shutil.rmtree(os.path.join(ESP, 'Globals'), ignore_errors=True)
    outws = os.path.join(ESP, 'Worldspaces', WS)

    # --- WRLD header from its last overrider -----------------------------------------------------
    wrld = [(p, os.path.join(r, 'Worldspaces', WS, 'RecordData.yaml')) for p, r in src
            if os.path.isfile(os.path.join(r, 'Worldspaces', WS, 'RecordData.yaml'))]
    wplugin, wpath = wrld[-1]
    write(os.path.join(outws, 'RecordData.yaml'), header(read(wpath)))
    print(f'WRLD Vyn header <- {wplugin}')

    # --- refs per cell ----------------------------------------------------------------------------
    by_cell = {}
    for s in sorted(plan, key=lambda s: (s['cell'][0], s['cell'][1], s['center'][0], s['center'][1])):
        by_cell.setdefault((tuple(s['cell']), s['cell_fk']), []).append(s)
    # A site keeps the ref FormIDs it already has (02 carries them over), so goblins in existing saves stay
    # the same refs when other packs are added or removed; only new sites get fresh IDs.
    kept = [r for s in plan if len(s.get('refs', [])) == len(s['members']) for r in s['refs']]
    assert len(kept) == len(set(kept)), 'duplicate ref FormIDs in plan'
    fid = max([int(r, 16) + 1 for r in kept] + [FIRST_REF])
    for s in plan:
        if len(s.get('refs', [])) != len(s['members']):
            s['refs'] = []
    winners = {}
    for ((gx, gy), cell_fk), sites in sorted(by_cell.items()):
        found = [(p, cell_dir(r, gx, gy, cell_fk), r) for p, r in src]
        found = [(p, d, r) for p, d, r in found if d]
        assert found, cell_fk
        plugin, cdir, root = found[-1]
        winners[plugin] = winners.get(plugin, 0) + 1
        text = read(os.path.join(cdir, 'RecordData.yaml'))
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
                         f'  Base: {BASES[role]}:{MOD_KEY}',
                         '  Placement:',
                         f'    Position: {x}, {y}, {z + 8}',
                         f'    Rotation: 0, 0, {rot}']
        blk, sub = block_dirs(gx, gy)
        rel = os.path.relpath(cdir, os.path.join(root, 'Worldspaces', WS))
        write(os.path.join(outws, rel, 'RecordData.yaml'), header(text) + NL.join(body) + NL + trailer(text))
        for g in ((blk,), (blk, sub)):
            gsrc = [os.path.join(r, 'Worldspaces', WS, *g, 'GroupRecordData.yaml') for _, r in src]
            gsrc = [p for p in gsrc if os.path.isfile(p)]
            shutil.copyfile(gsrc[-1], os.path.join(outws, *g, 'GroupRecordData.yaml'))
    assert fid <= 0x1000, f'ESL range exhausted at {fid:X}'
    n = sum(len(s['refs']) for s in plan)
    assert len({r for s in plan for r in s['refs']}) == n, 'duplicate ref FormIDs'
    print(f'{n} goblins in {len(plan)} packs, {len(by_cell)} cells; cell headers from: ' +
          ', '.join(f'{p} {c}' for p, c in sorted(winners.items(), key=lambda kv: -kv[1])))

    # --- respawn global -----------------------------------------------------------------------------
    g_fid, g_edid, g_val = RESPAWN_GLOBAL
    write(os.path.join(ESP, 'Globals', f'{g_edid} - {g_fid}_{MOD_KEY}.yaml'),
          NL.join(['MutagenObjectType: GlobalFloat', f'FormKey: {g_fid}:{MOD_KEY}', f'EditorID: {g_edid}',
                   f'Data: {g_val}']) + NL)

    # --- plugin header: masters from every FormKey written ---------------------------------------
    used = set()
    top = os.path.join(os.path.normpath(ESP), 'RecordData.yaml')
    for dirpath, _, files in os.walk(os.path.normpath(ESP)):
        for f in files:
            path = os.path.join(dirpath, f)
            if f.endswith('.yaml') and path != top:
                used |= set(re.findall(r'[0-9A-F]{6}:([^\r\n:]+?\.(?:esm|esp|esl))', read(path)))
    used.discard(MOD_KEY)
    order = [ln[1:].strip() for ln in open(PLUGINS, encoding='utf-8') if ln.startswith('*')]
    extra = sorted(used - set(BASE_MASTERS), key=lambda p: order.index(p))
    masters = BASE_MASTERS + extra
    lines = ['SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', f'ModKey: {MOD_KEY}',
             'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
             '  Author: Zenderal',
             '  Description: Goblins as their own creature (requires the Goblins mod), in packs across Vyn.',
             '  MasterReferences:']
    for m in masters:
        lines += [f'  - Master: {m}', '    FileSize: 0']
    lines += ['  INTV: 1']
    write(os.path.join(ESP, 'RecordData.yaml'), NL.join(lines) + NL)
    write(os.path.join(ESP, 'spriggit-meta.json'), json.dumps(
        {'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.40.0', 'Release': 'EnderalSE', 'ModKey': MOD_KEY},
        indent=2) + '\n')
    print('masters: ' + ', '.join(masters))
    with open(PLAN, 'w', encoding='utf-8', newline='\n') as fh:   # plan gains each pack's ref FormIDs
        json.dump(plan, fh, indent=1)
        fh.write('\n')


if __name__ == '__main__':
    main()
