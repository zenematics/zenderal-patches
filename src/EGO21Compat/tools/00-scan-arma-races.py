r"""List every winning ARMA in the live load order that lost 2.1's playable races -- read only.

Why: Enderal 2.1 moved the playable Half Arazealean / Half Qyranian onto 013746 NordRace / 013748
RedguardRace and added both to its armor addons. A 2.0-era override (EGO) that still lists only the
old 033899 / 033898 hides that armor on a 2.1 player: it equips, nothing renders.

For each ARMA that Skyrim.esm or FS defines, this compares the WINNING override's races (RNAM + MODL)
with the defining record's. It reports each winner missing 013746 or 013748 that the base record has.
Feed the result to 02-build-armor-addons.py's ADDONS (only records whose winner we have YAML for).

Usage:  python -I 00-scan-arma-races.py
"""
import os, struct, zlib

PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'
BASE = ('skyrim.esm', 'enderal - forgotten stories.esm')
NEW_RACES = {0x013746: 'NordRace', 0x013748: 'RedguardRace'}


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


def subrecords(body):
    p = 0
    while p + 6 <= len(body):
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        yield typ, body[p + 6:p + 6 + size]
        p += 6 + size


def records(data, start, end):
    p = start
    while p < end:
        typ = data[p:p + 4]
        size = struct.unpack_from('<I', data, p + 4)[0]
        if typ == b'GRUP':
            yield from records(data, p + 24, p + size)
            p += size
        else:
            yield typ, p, size
            p += 24 + size


def resolve(fid, mast, name):
    """(owning plugin lower-case, object id) for a raw FormID in a plugin with masters `mast`."""
    i = fid >> 24
    return (mast[i] if i < len(mast) else name.lower()), fid & 0xFFFFFF


base, winner = {}, {}
for name, path in plugin_paths():
    data = open(path, 'rb').read()
    hdr = struct.unpack_from('<I', data, 4)[0]
    mast = [d.rstrip(b'\0').decode('cp1252').lower() for t, d in subrecords(data[24:24 + hdr]) if t == b'MAST']
    for typ, p, size in records(data, 24 + hdr, len(data)):
        if typ != b'ARMA':
            continue
        key = resolve(struct.unpack_from('<I', data, p + 12)[0], mast, name)
        if key[0] not in BASE:
            continue
        body = data[p + 24:p + 24 + size]
        if struct.unpack_from('<I', data, p + 8)[0] & 0x40000:
            body = zlib.decompress(body[4:])
        races = set()
        for t, d in subrecords(body):
            if t in (b'RNAM', b'MODL') and len(d) == 4:
                owner, oid = resolve(struct.unpack('<I', d)[0], mast, name)
                if owner == 'skyrim.esm':
                    races.add(oid)
        if name.lower() == key[0]:
            base[key] = races
        winner[key] = (name, races)

hits = 0
for key in sorted(winner):
    name, races = winner[key]
    missing = [f'{r:06X}' for r in NEW_RACES if r in base.get(key, ()) and r not in races]
    if missing:
        hits += 1
        print(f'{key[1]:06X}:{key[0]}  winner {name}  missing {" ".join(missing)}')
print(f'{hits} winning ARMAs missing a 2.1 playable race ({len(winner)} base ARMAs scanned)')
