"""Which active plugins override a set of records? Master-aware binary scan of the live load order.

Reads the MO2 profile's plugins.txt (load order) and modlist.txt (which mod folder wins each file),
walks every enabled plugin's GRUP tree and records, for each record whose FormKey is in TARGETS,
every plugin that defines/overrides it, in load order. Record FormIDs are resolved through each
plugin's own MAST list (index >= masters = the plugin itself), and ESL-flagged plugins use the
light FormID space, so the same FormKey matches across plugins whatever their load positions.

Used by 04-rebuild-npcs.py to find the previous winner of every NPC that A Gentleman's Flintlock
Armoury and Ordo Legionis (Muskets of the Enderal) override. Writes tools/overriders.json.

Run from the repo root: python -I src/FlintlockOverhaul/tools/00-scan-overriders.py
"""
import json
import os
import re
import struct
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PROFILE = r'E:/Zenderal/profiles/Alpha 0.5'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'
REF = os.path.join(ROOT, 'reference', 'mods')
OUT = os.path.join(os.path.dirname(__file__), 'overriders.json')
SOURCES = [('FlintlockPack', 'AdventurerFlintlockPack.esp'), ('OrdoEnderal', 'OrdoLegionisMuskets.esp')]


def targets():
    t = set()
    for tree, _ in SOURCES:
        for f in os.listdir(os.path.join(REF, tree, 'Npcs')):
            m = re.search(r' - ([0-9A-F]{6})_(.+)\.yaml$', f)
            t.add('%s:%s' % (m.group(1), m.group(2)))
    return t


def plugin_paths():
    mods = [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]
    loc = {}
    for f in os.listdir(GAME_DATA):
        if f.lower().endswith(('.esm', '.esp', '.esl')):
            loc[f.lower()] = os.path.join(GAME_DATA, f)
    for m in reversed(mods):           # modlist.txt is highest-priority first; later assignment wins
        d = os.path.join(MODS, m)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(('.esm', '.esp', '.esl')):
                    loc[f.lower()] = os.path.join(d, f)
    order = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm']
    for l in open(os.path.join(PROFILE, 'plugins.txt'), encoding='utf-8'):
        l = l.strip()
        if l.startswith('*') and l[1:] not in order:
            order.append(l[1:])
    return [(p, loc[p.lower()]) for p in order if p.lower() in loc]


def scan(path, want):
    data = open(path, 'rb').read()
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    flags = struct.unpack_from('<I', data, 8)[0]
    masters = [m.decode('utf-8', 'replace') for m in re.findall(rb'MAST..([^\x00]*)\x00', data[24:24 + hdr_size])]
    self_name = os.path.basename(path)
    hits = set()
    pos = 24 + hdr_size
    stack = [len(data)]
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if typ == b'GRUP':
            label = data[pos + 8:pos + 12]
            gtype = struct.unpack_from('<i', data, pos + 12)[0]
            if gtype == 0 and label != b'NPC_':
                pos += size            # skip whole top groups we don't need
                continue
            pos += 24
            continue
        fid = struct.unpack_from('<I', data, pos + 12)[0]
        if typ == b'NPC_':
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else self_name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            fk = '%06X:%s' % (local, owner)
            if fk in want:
                hits.add(fk)
        pos += 24 + size
    return hits


def main():
    want = targets()
    result = {fk: [] for fk in want}
    for name, path in plugin_paths():
        for fk in scan(path, want):
            result[fk].append(name)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
    others = {}
    for fk, chain in result.items():
        for p in chain:
            others[p] = others.get(p, 0) + 1
    print(len(want), 'target NPCs; plugins overriding them (count):')
    for p, c in sorted(others.items(), key=lambda x: -x[1]):
        print('  %4d  %s' % (c, p))


if __name__ == '__main__':
    sys.exit(main())
