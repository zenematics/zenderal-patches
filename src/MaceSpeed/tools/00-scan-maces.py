"""Every one-handed mace in the live load order, and which plugin wins it.

Master-aware binary scan of the MO2 profile's enabled plugins (same approach as
src/FlintlockOverhaul/tools/00-scan-overriders.py): walks each plugin's WEAP group, decodes the
DNAM animation type and speed, and records every plugin that defines/overrides each WEAP. A record
counts as a mace when its WINNING DNAM animation type is OneHandMace (4).

Writes tools/maces.json ({FormKey: {"chain": [...], "speed": winning speed, "anim": ...}}).
Run from the repo root: python -I src/MaceSpeed/tools/00-scan-maces.py
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
OUT = os.path.join(os.path.dirname(__file__), 'maces.json')
ONE_HAND_MACE = 4


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


def dnam(body):
    p = 0
    while p + 6 <= len(body):
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        if typ == b'DNAM':
            d = body[p + 6:p + 6 + size]
            return d[0], struct.unpack_from('<f', d, 4)[0]
        p += 6 + size
    return None, None


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
            if gtype == 0 and label != b'WEAP':
                pos += size
                continue
            pos += 24
            continue
        if typ == b'WEAP':
            rflags, fid = struct.unpack_from('<II', data, pos + 8)
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else self_name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            body = data[pos + 24:pos + 24 + size]
            if rflags & 0x20:          # deleted
                pass
            elif rflags & 0x40000:     # compressed
                body = zlib.decompress(body[4:])
            out['%06X:%s' % (local, owner)] = dnam(body)
        pos += 24 + size
    return out


def main():
    chains = {}
    for name, path in plugin_paths():
        for fk, val in scan(path).items():
            chains.setdefault(fk, []).append((name, val))
    result = {}
    for fk, chain in chains.items():
        anim, speed = chain[-1][1]
        if anim == ONE_HAND_MACE:
            result[fk] = {'chain': [n for n, _ in chain], 'anim': anim, 'speed': round(speed, 4)}
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
    winners = {}
    for fk, r in sorted(result.items()):
        winners[r['chain'][-1]] = winners.get(r['chain'][-1], 0) + 1
        print('%-48s speed %-5s %s' % (fk, r['speed'], ' > '.join(r['chain'])))
    print(len(result), 'maces; winners:', winners)


if __name__ == '__main__':
    sys.exit(main())
