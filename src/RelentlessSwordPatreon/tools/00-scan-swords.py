"""Every one-handed sword in the live load order, ranked by base damage, and whether Relentless Zen
still out-stats them all.

Master-aware binary scan of the MO2 profile's enabled plugins (same approach as
src/MaceSpeed/tools/00-scan-maces.py): walks each plugin's WEAP group and keeps the WINNING record of
each FormKey. A record counts as a sword when its winning DNAM animation type is OneHandSword (1).
Non-playable records (DNAM flag 0x80) are listed apart: NPC-only and summon weapons.

Johnskyrim's own 'Relentless Sword SE - Johnskyrim.esp' is skipped: the port in this folder replaces it.

Writes tools/swords.json. Run from the repo root: python -I src/RelentlessSwordPatreon/tools/00-scan-swords.py
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
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'swords.json')
ZEN_YAML = os.path.join(HERE, '..', 'RelentlessSwordPatreonESP', 'Weapons',
                        'JS_RelentlessSwordZen - 00082A_Zenderal - Relentless Sword.esp.yaml')
SKIP = {'relentless sword se - johnskyrim.esp'}
ONE_HAND_SWORD = 1
NON_PLAYABLE = 0x80


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
    return [(p, loc[p.lower()]) for p in order if p.lower() in loc and p.lower() not in SKIP]


def fields(body):
    out = {}
    p = 0
    while p + 6 <= len(body):
        typ = body[p:p + 4].decode('latin-1')
        size = struct.unpack_from('<H', body, p + 4)[0]
        out.setdefault(typ, body[p + 6:p + 6 + size])
        p += 6 + size
    return out


def decode(body):
    f = fields(body)
    if 'DNAM' not in f or 'DATA' not in f:
        return None
    d = f['DNAM']
    value, weight, damage = struct.unpack_from('<IfH', f['DATA'], 0)
    r = {
        'edid': f.get('EDID', b'').rstrip(b'\x00').decode('latin-1'),
        'anim': d[0],
        'speed': round(struct.unpack_from('<f', d, 4)[0], 4),
        'reach': round(struct.unpack_from('<f', d, 8)[0], 4),
        'nonplayable': bool(struct.unpack_from('<H', d, 12)[0] & NON_PLAYABLE),
        'damage': damage,
        'value': value,
        'weight': round(weight, 3),
        'enchanted': 'EITM' in f,
        'template': 'CNAM' in f,
    }
    if 'CRDT' in f:
        r['crit_damage'] = struct.unpack_from('<H', f['CRDT'], 0)[0]
        r['crit_mult'] = round(struct.unpack_from('<f', f['CRDT'], 4)[0], 4)
    return r


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
            if not rflags & 0x20:
                if rflags & 0x40000:
                    body = zlib.decompress(body[4:])
                r = decode(body)
                if r is not None:
                    out['%06X:%s' % (local, owner)] = r
        pos += 24 + size
    return out


def zen_stats():
    text = open(ZEN_YAML, encoding='utf-8').read()
    damage = re.search(r'^BasicStats:\n(?:  .*\n)*?  Damage: (\d+)', text, re.M)
    crit = re.search(r'^Critical:\n  Damage: (\d+)', text, re.M)
    return int(damage.group(1)), int(crit.group(1))


def obtainable(r):
    # SureAI's _00E_Debug_Sword (75 damage) is a console-only test item
    return not r['nonplayable'] and 'debug' not in r['edid'].lower()


def main():
    chains = {}
    for name, path in plugin_paths():
        for fk, val in scan(path).items():
            chains.setdefault(fk, []).append((name, val))
    swords = {}
    for fk, chain in chains.items():
        r = chain[-1][1]
        if r['anim'] == ONE_HAND_SWORD:
            r = dict(r)
            r['chain'] = [n for n, _ in chain]
            swords[fk] = r
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(swords, f, indent=1, sort_keys=True)

    ranked = sorted(swords.items(), key=lambda kv: (-kv[1]['damage'], -kv[1].get('crit_damage', 0)))
    print('%-44s %-40s %4s %4s %5s %5s %s' % ('FormKey', 'EditorID', 'dmg', 'crit', 'speed', 'reach', 'winner'))
    for playable in (True, False):
        print('--- %s ---' % ('playable' if playable else 'non-playable'))
        n = 0
        for fk, r in ranked:
            if r['nonplayable'] == (not playable):
                print('%-44s %-40s %4d %4s %5s %5s %s%s' % (fk, r['edid'][:40], r['damage'], r.get('crit_damage', '-'),
                                                         r['speed'], r['reach'], r['chain'][-1],
                                                         ' [ench]' if r['enchanted'] else ''))
                n += 1
                if n >= 25:
                    break
    best = max((r['damage'] for r in swords.values() if obtainable(r)), default=0)
    best_crit = max((r.get('crit_damage', 0) for r in swords.values() if obtainable(r)), default=0)
    zen, zen_crit = zen_stats()
    ok = zen > best and zen_crit > best_crit
    print('%d one-handed swords; strongest obtainable: damage %d, crit %d; Relentless Zen %d / %d -> %s'
          % (len(swords), best, best_crit, zen, zen_crit, 'STRONGEST' if ok else 'NOT the strongest'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
