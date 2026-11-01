"""Which enabled plugins in the live profile define/override the given Skyrim.esm-local FormIDs.
Usage: python -I scan_overriders.py 069D52 069E31 ...
"""
import os
import struct
import sys

PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'


def plugin_paths():
    mods = [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]
    loc = {}
    for f in os.listdir(GAME_DATA):
        if f.lower().endswith(('.esm', '.esp', '.esl')):
            loc[f.lower()] = os.path.join(GAME_DATA, f)
    for m in reversed(mods):
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


def masters(data, hdr_size):
    out, p, body = [], 0, data[24:24 + hdr_size]
    while p + 6 <= len(body):
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        if typ == b'MAST':
            out.append(body[p + 6:p + 6 + size].rstrip(b'\0').decode('cp1252'))
        p += 6 + size
    return out


def records(data, start, end):
    p = start
    while p < end:
        typ = data[p:p + 4]
        size = struct.unpack_from('<I', data, p + 4)[0]
        if typ == b'GRUP':
            yield from records(data, p + 24, p + size)
            p += size
        else:
            yield typ.decode('ascii', 'replace'), struct.unpack_from('<I', data, p + 12)[0]
            p += 24 + size


want = {int(x, 16) for x in sys.argv[1:]}
for name, path in plugin_paths():
    data = open(path, 'rb').read()
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    mast = masters(data, hdr_size)
    try:
        sky = [m.lower() for m in mast].index('skyrim.esm')
    except ValueError:
        if name.lower() != 'skyrim.esm':
            continue
        sky = 0
    for typ, fid in records(data, 24 + hdr_size, len(data)):
        if fid >> 24 == sky and (fid & 0xFFFFFF) in want:
            print(f'{fid & 0xFFFFFF:06X} {typ} {name}')
