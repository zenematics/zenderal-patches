"""Which active plugins override the Default Object Manager or any MUSC, and which still use the 2.0 combat script?

Master-aware binary scan of the live Ultra load order (plugins.txt + modlist.txt). For every enabled
plugin it lists each DOBJ / MUSC record by FormKey, and whether the plugin's bytes name
`_00E_CombatSoundtrackScript` (Enderal 2.0's per-NPC combat-music script, gone from 2.1's BSAs).
Also lists every loose `_00E_CombatSoundtrackScript.pex` in an enabled mod.

Run from the repo root: python -I src/NoCombatMusic/tools/00-scan-music.py
"""
import os
import re
import struct
import sys
import zlib

PROFILE = r'E:/Zenderal/profiles/Ultra'
MODS = r'E:/Zenderal/mods'
GAME_DATA = r'E:/Zenderal/Stock Game/Data'
TYPES = (b'DOBJ', b'MUSC')


def enabled_mods():
    return [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]


def plugin_paths():
    loc = {}
    for f in os.listdir(GAME_DATA):
        if f.lower().endswith(('.esm', '.esp', '.esl')):
            loc[f.lower()] = os.path.join(GAME_DATA, f)
    for m in reversed(enabled_mods()):  # modlist.txt is highest-priority first; later assignment wins
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


def scan(path):
    data = open(path, 'rb').read()
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    flags = struct.unpack_from('<I', data, 8)[0]
    masters = [m.decode('utf-8', 'replace') for m in re.findall(rb'MAST..([^\x00]*)\x00', data[24:24 + hdr_size])]
    self_name = os.path.basename(path)
    hits = []
    pos = 24 + hdr_size
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if typ == b'GRUP':
            label = data[pos + 8:pos + 12]
            gtype = struct.unpack_from('<i', data, pos + 12)[0]
            if gtype == 0 and label not in TYPES:
                pos += size
                continue
            pos += 24
            continue
        rflags, fid = struct.unpack_from('<II', data, pos + 8)
        if typ in TYPES:
            idx = fid >> 24
            owner = masters[idx] if idx < len(masters) else self_name
            local = fid & 0xFFFFFF
            if idx >= len(masters) and flags & 0x200:
                local = fid & 0xFFF
            body = data[pos + 24:pos + 24 + size]
            if rflags & 0x40000:
                body = zlib.decompress(body[4:])
            edid = re.search(rb'EDID..([^\x00]*)\x00', body, re.S)
            hits.append((typ.decode(), '%06X:%s' % (local, owner), edid.group(1).decode('latin1') if edid else ''))
        pos += 24 + size
    script = b'_00e_combatsoundtrackscript' in data.lower()
    return hits, script


def main():
    for name, path in plugin_paths():
        hits, script = scan(path)
        for typ, fk, edid in hits:
            print('%-4s %-30s %-45s %s' % (typ, fk, edid, name))
        if script:
            print('SCRIPT _00E_CombatSoundtrackScript named in', name)
    for m in enabled_mods():
        d = os.path.join(MODS, m, 'Scripts')
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower() == '_00e_combatsoundtrackscript.pex':
                    print('PEX', os.path.join(d, f))


if __name__ == '__main__':
    sys.exit(main())
