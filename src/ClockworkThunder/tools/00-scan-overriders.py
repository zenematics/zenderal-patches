"""Which active plugins define/override the records Clockwork Thunder copies or touches?

Master-aware header scan of the live load order (profile Ultra): every enabled plugin's records,
nested groups included, FormIDs resolved through the plugin's own MAST list (ESL-flagged plugins
use the light FormID space). Prints the chain per FormKey, last = winner, and writes
tools/overriders.json, which 02-build-records.py checks so it never copies a record that a later
plugin has changed since.

Usage:  python src/ClockworkThunder/tools/00-scan-overriders.py
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
MO2 = TOOLS['modlistRoot']
PROFILE = os.path.join(MO2, 'profiles', 'Ultra')
MODS = os.path.join(MO2, 'mods')
GAME_DATA = TOOLS['gameDataDir']
OUT = os.path.join(HERE, 'overriders.json')

TARGETS = {
    '002F9B:OrdoLegionisMuskets.esp': 'WEAP OL_Musket_Rifle (copied)',
    '002F9A:OrdoLegionisMuskets.esp': 'STAT OLM_1stPersonMusketRifle (copied)',
    '00F5D6:OrdoLegionisMuskets.esp': 'COBJ OLMTemperMatchlock_AlikrRifle (temper copied)',
    '07336E:Skyrim.esm': 'CELL DesertAltAskamahnL2 (header owned)',
    '07410A:Skyrim.esm': 'REFR RuinsAltarBroken in Askamahn L2 (the rifle lies on it)',
    '000B02:Zenderal - Prophecy.esp': 'SPEL Flow State chain lightning (copied)',
    '000AFD:Zenderal - Prophecy.esp': 'MGEF Invoker shock (copied)',
    '000B01:Zenderal - Prophecy.esp': 'EXPL flash-less chain explosion (copied)',
    '14CEBD:Skyrim.esm': 'MGEF Arcane Archer affinity paralysis (stun copied)',
}


def plugin_paths():
    mods = [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]
    loc = {}
    for f in os.listdir(GAME_DATA):
        if f.lower().endswith(('.esm', '.esp', '.esl')):
            loc[f.lower()] = os.path.join(GAME_DATA, f)
    for m in reversed(mods):           # modlist.txt is highest priority first; later assignment wins
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
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if typ == b'GRUP':
            pos += 24
            continue
        fid = struct.unpack_from('<I', data, pos + 12)[0]
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
    result = {fk: [] for fk in TARGETS}
    for name, path in plugin_paths():
        for fk in scan(path, set(TARGETS)):
            result[fk].append(name)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
    for fk, chain in sorted(result.items()):
        print('%s  %s\n    %s' % (fk, TARGETS[fk], ' -> '.join(chain) or '(not found)'))


if __name__ == '__main__':
    sys.exit(main())
