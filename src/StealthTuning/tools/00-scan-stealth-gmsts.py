"""Every stealth/detection game setting in the live load order, and which plugins set it.

Master-aware binary scan of the MO2 profile's enabled plugins (same approach as
src/MaceSpeed/tools/00-scan-maces.py): walks each plugin's GMST group and records every plugin
that defines/overrides each sneak, detection or combat-stealth setting, with its value.

Writes tools/gmsts.json ({EditorID: {"formKey": ..., "chain": [[plugin, value], ...]}}).
Run from the repo root: python -I src/StealthTuning/tools/00-scan-stealth-gmsts.py
"""
import json
import os
import re
import struct
import sys
import zlib

PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'
OUT = os.path.join(os.path.dirname(__file__), 'gmsts.json')
WANTED = re.compile(r'Sneak|Detection|Stealth|LightLevel|TorchLight', re.I)


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


def gmst(body):
    edid = raw = None
    p = 0
    while p + 6 <= len(body):
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        if typ == b'EDID':
            edid = body[p + 6:p + 6 + size].rstrip(b'\x00').decode('utf-8', 'replace')
        elif typ == b'DATA':
            raw = body[p + 6:p + 6 + size]
        p += 6 + size
    if not edid or raw is None or edid[0] not in 'fi':
        return edid, None
    if edid[0] == 'f':
        return edid, round(struct.unpack_from('<f', raw)[0], 4)
    return edid, struct.unpack_from('<i', raw)[0]


def scan(path):
    data = open(path, 'rb').read()
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    flags = struct.unpack_from('<I', data, 8)[0]
    masters = [m.decode('utf-8', 'replace') for m in re.findall(rb'MAST..([^\x00]*)\x00', data[24:24 + hdr_size])]
    self_name = os.path.basename(path)
    out = {}
    pos = 24 + hdr_size
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if typ == b'GRUP':
            label = data[pos + 8:pos + 12]
            gtype = struct.unpack_from('<i', data, pos + 12)[0]
            if gtype == 0 and label != b'GMST':
                pos += size
                continue
            pos += 24
            continue
        if typ == b'GMST':
            rflags, fid = struct.unpack_from('<II', data, pos + 8)
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else self_name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            body = data[pos + 24:pos + 24 + size]
            if not rflags & 0x20:
                if rflags & 0x40000:
                    body = zlib.decompress(body[4:])
                edid, val = gmst(body)
                if edid and WANTED.search(edid) and val is not None:
                    out[edid] = ('%06X:%s' % (local, owner), val)
        pos += 24 + size
    return out


def main():
    # The engine finds a setting by its EditorID, so a mod that adds a NEW GMST under an existing
    # name still overrides it: Stealth Overhaul re-adds EGO's new 000803/007EA2.. as its own 0008xx.
    # Chains are keyed by EditorID; each step keeps the FormKey that plugin used.
    result = {}
    for name, path in plugin_paths():
        for edid, (fk, val) in scan(path).items():
            result.setdefault(edid, {'chain': []})['chain'].append([name, fk, val])
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
    for edid, r in sorted(result.items()):
        print('%-46s %s' % (edid, ' > '.join('%s %s (%s)' % (n, fk.split(':')[0], v) for n, fk, v in r['chain'])))
    print(len(result), 'stealth settings')


if __name__ == '__main__':
    sys.exit(main())
