"""Every armor in the live load order, its winner, and how it is crafted. Read-only.

Master-aware binary scan of the MO2 profile's enabled plugins (same approach as
src/MaceSpeed/tools/00-scan-maces.py): walks each plugin's ARMO, KYWD and COBJ groups and records, for every
ARMO, every plugin that defines/overrides it plus the winning armor rating, weight, value, armor type, slots
and keywords (EditorIDs), and for every COBJ that creates an armor its winning items, workbench and
conditions (decoded as Smithing >= N / blueprint / perk / function number).

Writes tools/armor.json and prints every playable armor a non-base plugin added, with its recipe gates,
next to the base game's range for the same slot and armor type. EGO's forged cuirass ladder (what a mod
armor should be measured against): Leather 16.4 (blueprint) / Firm 19.8 (Smithing 20) / Fine 21.6 (25) /
Pyrean 25.9 (38) / Assassin 28.8 (45) / Aeterna 33.3 (60), each also needing its blueprint.

Run from the repo root: python -I src/ArmorBalance/tools/00-scan-armor.py
"""
import json
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding='utf-8')
PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'
OUT = os.path.join(os.path.dirname(__file__), 'armor.json')
BASE = {'Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'}
ARMOR_TYPE = {0: 'light', 1: 'heavy', 2: 'clothing'}
SLOTS = [(0x4, 'body'), (0x1, 'head'), (0x2, 'head'), (0x1000, 'head'), (0x8, 'hands'), (0x80, 'feet'),
         (0x200, 'shield')]
FUNCTIONS = {14: 'GetActorValue', 47: 'GetItemCount', 448: 'HasPerk'}
SMITHING = 10          # actor value index


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


def load_strings(name):
    p = os.path.join(GAME_DATA, 'Strings', os.path.splitext(name)[0].lower() + '_english.strings')
    if not os.path.exists(p):
        return {}
    d = open(p, 'rb').read()
    n = struct.unpack_from('<I', d, 0)[0]
    base = 8 + n * 8
    s = {}
    for i in range(n):
        sid, off = struct.unpack_from('<II', d, 8 + i * 8)
        s[sid] = d[base + off:d.index(b'\x00', base + off)].decode('cp1252', 'replace')
    return s


def subrecords(b):
    pos, big = 0, None
    while pos + 6 <= len(b):
        t = b[pos:pos + 4].decode('ascii', 'replace')
        sz = struct.unpack_from('<H', b, pos + 4)[0]
        pos += 6
        if t == 'XXXX':
            big = struct.unpack_from('<I', b, pos)[0]
            pos += sz
            continue
        if big is not None:
            sz, big = big, None
        yield t, b[pos:pos + sz]
        pos += sz


def zs(b):
    return b.split(b'\x00', 1)[0].decode('cp1252', 'replace')


def condition(v, fk):
    op = ['==', '!=', '>', '>=', '<', '<='][v[0] >> 5]
    value = struct.unpack_from('<f', v, 4)[0]
    fn = struct.unpack_from('<H', v, 8)[0]
    p1 = struct.unpack_from('<I', v, 12)[0]
    if fn == 14 and p1 == SMITHING:
        return 'Smithing %s %g' % (op, value)
    if fn == 47:
        return 'has %s' % fk(p1)
    if fn == 448:
        return 'perk %s' % fk(p1)
    return 'function %d %s %g' % (fn, op, value)


def main():
    armor, chains, recipes, kywd = {}, {}, {}, {}
    for name, path in plugin_paths():
        data = open(path, 'rb').read()
        hdr_size = struct.unpack_from('<I', data, 4)[0]
        flags = struct.unpack_from('<I', data, 8)[0]
        masters = [zs(v) for t, v in subrecords(data[24:24 + hdr_size]) if t == 'MAST']
        strings = load_strings(name) if flags & 0x80 else {}

        def fk(fid):
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            return '%06X:%s' % (local, owner)

        pos = 24 + hdr_size
        while pos < len(data):
            typ = data[pos:pos + 4]
            size = struct.unpack_from('<I', data, pos + 4)[0]
            if typ == b'GRUP':
                if struct.unpack_from('<i', data, pos + 12)[0] == 0 and data[pos + 8:pos + 12] not in (b'ARMO', b'KYWD', b'COBJ'):
                    pos += size
                    continue
                pos += 24
                continue
            rflags, fid = struct.unpack_from('<II', data, pos + 8)
            body = data[pos + 24:pos + 24 + size]
            pos += 24 + size
            if rflags & 0x40000:
                body = zlib.decompress(body[4:])
            key = fk(fid)
            if typ == b'KYWD':
                kywd[key] = next((zs(v) for t, v in subrecords(body) if t == 'EDID'), key)
                continue
            if typ == b'COBJ':
                r = {'winner': name, 'items': [], 'conditions': [], 'deleted': bool(rflags & 0x20)}
                for t, v in subrecords(body):
                    if t == 'EDID':
                        r['editorId'] = zs(v)
                    elif t == 'CNAM':
                        r['creates'] = fk(struct.unpack_from('<I', v)[0])
                    elif t == 'BNAM':
                        r['bench'] = fk(struct.unpack_from('<I', v)[0])
                    elif t == 'CNTO':
                        r['items'].append([fk(struct.unpack_from('<I', v)[0]), struct.unpack_from('<i', v, 4)[0]])
                    elif t == 'CTDA':
                        r['conditions'].append(condition(v, fk))
                recipes[key] = r
                continue
            prev = armor.get(key)
            r = {'winner': name, 'deleted': bool(rflags & 0x20), 'nonPlayable': bool(rflags & 0x4), 'keywords': []}
            if prev and 'name' in prev:
                r['name'] = prev['name']       # an override that drops FULL keeps the name shown so far
            for t, v in subrecords(body):
                if t == 'EDID':
                    r['editorId'] = zs(v)
                elif t == 'FULL':
                    r['name'] = strings.get(struct.unpack('<I', v)[0], '') if strings and len(v) == 4 else zs(v)
                elif t == 'DATA' and len(v) >= 8:
                    r['value'], r['weight'] = struct.unpack_from('<if', v, 0)
                elif t == 'DNAM' and len(v) >= 4:
                    r['armor'] = struct.unpack_from('<i', v, 0)[0] / 100.0
                elif t == 'BOD2':
                    r['slots'], r['armorType'] = struct.unpack_from('<II', v, 0)
                elif t == 'BODT':
                    r['slots'] = struct.unpack_from('<I', v, 0)[0]
                    if len(v) >= 12:
                        r['armorType'] = struct.unpack_from('<I', v, 8)[0]
                elif t == 'KWDA':
                    r['keywords'] = [fk(x) for x in struct.unpack('<%dI' % (len(v) // 4), v)]
            chains.setdefault(key, []).append(name)
            armor[key] = r
    for key, r in armor.items():
        r['chain'] = chains[key]
        r['keywords'] = [kywd.get(k, k) for k in r['keywords']]
    # recipes that make an armor, plus every recipe of a plugin that adds armor (Grievous Rose's craft book)
    adds_armor = {k.split(':', 1)[1] for k in armor} - BASE
    recipes = {k: r for k, r in recipes.items() if r.get('creates') in armor or k.split(':', 1)[1] in adds_armor}
    json.dump({'armor': armor, 'recipes': recipes}, open(OUT, 'w', encoding='utf-8', newline='\n'),
              indent=1, sort_keys=True, ensure_ascii=False)
    report(armor, recipes)


def slot(r):
    for bit, n in SLOTS:
        if r.get('slots', 0) & bit:
            return n
    return 'other'


def report(armor, recipes):
    made_by = {}
    for r in recipes.values():
        if not r['deleted']:
            made_by.setdefault(r['creates'], []).append(r)
    shown = {k: r for k, r in armor.items()
             if not r['deleted'] and not r['nonPlayable'] and r.get('name') and r.get('armor', 0) > 0}
    ranges = {}
    for k, r in shown.items():
        if k.split(':', 1)[1] in BASE:
            ranges.setdefault((slot(r), r.get('armorType')), []).append(r['armor'])
    print('%-30s %-6s %-8s %6s %5s  %-15s %s' % ('plugin', 'slot', 'type', 'armor', 'wt', 'base range', 'name / crafted'))
    for k, r in sorted(shown.items(), key=lambda x: (x[0].split(':', 1)[1], slot(x[1]), x[1]['armor'])):
        owner = k.split(':', 1)[1]
        if owner in BASE or r.get('armorType') == 2:
            continue
        rng = ranges.get((slot(r), r.get('armorType')), [])
        gates = ['/'.join(c['conditions']) or 'no conditions' for c in made_by.get(k, [])
                 if not c.get('bench', '').startswith('0ADB78')]        # 0ADB78 = armor workbench (tempering)
        print('%-30s %-6s %-8s %6.1f %5.1f  %-15s %s%s' % (
            owner[:30], slot(r), ARMOR_TYPE.get(r.get('armorType'), '?'), r['armor'], r.get('weight', 0),
            '%.1f-%.1f' % (min(rng), max(rng)) if rng else '-', r['name'][:40],
            (' | crafted: ' + '; '.join(gates)) if gates else ''))


if __name__ == '__main__':
    sys.exit(main())
