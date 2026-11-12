"""Who decides how fast a ridden mount may turn, in the live load order.

Master-aware binary scan of the MO2 profile's enabled plugins (same approach as
src/MaceSpeed/tools/00-scan-maces.py). Reports, for each record below, every plugin that defines or overrides it
and the WINNING turn rates:
  MOVT (movement types): SPED speeds; turn rates stored in radians (shown in degrees);
  RACE (mount races): the race's own MTYP/SPED per-movement-type speed overrides.

A ridden mount moves on the movement type its behaviour graph names (WolfProject.hkx -> WolfDefault/WolfRun), so
RotateWhileMovingRun = 0 means it cannot turn while moving: it only runs straight.

Run from the repo root: python -I src/WolfMountTurning/tools/00-scan-mount-movement.py
"""
import math
import os
import re
import struct
import sys
import zlib

PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'

MOVT = {
    '055D28:Skyrim.esm': 'Wolf_Default_MT', '0EA64B:Skyrim.esm': 'Wolf_Run_MT',
    '01CF24:Skyrim.esm': 'Horse_Default_MT', '04408D:Skyrim.esm': 'Horse_Sprint_MT',
    '069F74:Skyrim.esm': 'NPC_Horse_MT', '078722:Skyrim.esm': 'Horse_Fall_MT', '0C2EE2:Skyrim.esm': 'Horse_Swim_MT',
}
RACE = {
    '0450F7:Skyrim.esm': 'HorseFluteWolfMountRace', '0131FD:Skyrim.esm': 'HorseRace',
    '0DE505:Skyrim.esm': 'CartHorseRace', '01320A:Skyrim.esm': 'WolfRace',
}
SPED = ('LeftWalk', 'LeftRun', 'RightWalk', 'RightRun', 'ForwardWalk', 'ForwardRun', 'BackWalk', 'BackRun',
        'RotateInPlaceWalk', 'RotateInPlaceRun', 'RotateWhileMovingRun')


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


def subrecords(body):
    p = 0
    while p + 6 <= len(body):
        typ = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        yield typ, body[p + 6:p + 6 + size]
        p += 6 + size


def sped(d):
    n = len(d) // 4
    vals = struct.unpack_from('<%df' % n, d)
    out = {}
    for i, v in enumerate(vals[:len(SPED)]):
        out[SPED[i]] = round(math.degrees(v), 1) if SPED[i].startswith('Rotate') else round(v, 2)
    return out


def decode(typ, body):
    if typ == b'MOVT':
        for t, d in subrecords(body):
            if t == b'SPED':
                return sped(d)
        return None
    overrides = []
    current = None
    for t, d in subrecords(body):
        if t == b'MTYP':
            current = struct.unpack_from('<I', d)[0]
        elif t == b'SPED' and current is not None:
            overrides.append(('%08X' % current, sped(d)))
            current = None
    return overrides


def scan(path, wanted):
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
            if gtype == 0 and label not in (b'MOVT', b'RACE'):
                pos += size
                continue
            pos += 24
            continue
        if typ in (b'MOVT', b'RACE'):
            rflags, fid = struct.unpack_from('<II', data, pos + 8)
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else self_name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            fk = '%06X:%s' % (local, owner)
            if fk in wanted:
                body = data[pos + 24:pos + 24 + size]
                if rflags & 0x40000:
                    body = zlib.decompress(body[4:])
                out[fk] = decode(typ, body)
        pos += 24 + size
    return out


def main():
    wanted = {**MOVT, **RACE}
    chains = {}
    for name, path in plugin_paths():
        for fk, val in scan(path, wanted).items():
            chains.setdefault(fk, []).append((name, val))
    for fk in wanted:
        chain = chains.get(fk, [])
        print('%-26s %s' % (wanted[fk], fk))
        print('   chain:', ' > '.join(n for n, _ in chain) or '(not in load order)')
        if chain:
            print('   winner:', chain[-1][1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
