r"""Build cleaned copies of Kittytails' spell-pack plugins that Enderal SE can load safely -- never hand-edit a copy.

Prophecy masters four of Kittytails' packs (installed, not copied - the curator's choice, so nothing of hers is
redistributed): Abyssal Wind Magic (Aero.esl, Druid's Twister) and, for Sorcerer, Obscure Magic
(KittySpellPack01.esl), Elemental Mastery Magic (KittySpellPack02.esl) and Constellation Magic (Supernova.esl).
Three of them carry Skyrim content that is wrong in Enderal, so each gets a same-name copy minus whole top-level
groups, cut at the binary level (Aero.esl's test cell stops Mutagen, so Spriggit cannot round-trip it):

  * Aero.esl - CELL: its override of Skyrim cell MarkarthUnderStoneKeep 016DF2 is a PLACED REFERENCE in Enderal
    (PilzwaldNord 001F15): a record-type collision (as src/IronGolemClean). Plus the author's test cell.
  * KittySpellPack01.esl - CELL + WRLD: its tomes placed in 14 Skyrim/Dawnguard cells and Tamriel 00003C, which in
    Enderal is the prologue worldspace MQP01Home; at least two of the cell IDs (Mzulft01 01523F, IlinaltasDeep02
    03FC8F) are placed references in Enderal.
  * Supernova.esl - GMST: fWeatherTransAccel 4 -> 16, which made every weather change in the list four times faster
    (Supernova's sky effect wants it; Prophecy does not use that spell).
KittySpellPack02.esl needs nothing. The HEDR record count of each copy is lowered by what was dropped; nothing else
changes. Each pack's Nexus install must leave out its *_DISTR.ini (SPID): Aero's class filters exist in Enderal, and
the others' are Skyrim forms. Their tome injectors target vanilla leveled lists Enderal does not have (no-ops).

Writes one NEW mod folder per cleaned pack from the user's install; the original mods stay enabled for their BSAs.
Each new folder must sit ABOVE its original in MO2's mod list. Third-party content, generated on the user's machine,
never committed.

Usage: python 01-build-cleaned-packs.py [--modlist E:\Zenderal]
"""
import argparse
import os
import struct
import sys

# plugin -> (MO2 mod it comes from, groups to drop, (records, subgroups) dropped as of the version named)
PACKS = {
    'Aero.esl': ('Abyssal Wind Magic', ('CELL',), (5, 8), '1.5'),
    'KittySpellPack01.esl': ('Obscure Magic', ('CELL', 'WRLD'), (59, 54), '1.43'),
    'Supernova.esl': ('Constellation Magic', ('GMST',), (1, 0), '1.3'),
    # A Dark Warrior's Tale (2026-10-27, Prophecy's Rage): a whole Skyrim class questline. Kept: its combat kit (spells,
    # effects, projectiles, hazards, art, NPCs). Dropped: navmesh info map 012FB4 (a floor tile in Enderal - see
    # ApocalypseNaviFix), its 22 exterior cells in Tamriel 00003C (= Enderal's MQP01Home) and its own worldspace,
    # interiors, locations (FortSungardLocation 019185 override), and the Skyrim story: quests, dialogue, scenes.
    "KittyClass_DarkWarrior.esp": ("A Dark Warrior's Tale",
                                   ('NAVI', 'CELL', 'WRLD', 'LCTN', 'QUST', 'DIAL', 'DLBR', 'DLVW', 'SCEN'), (3078, 155), '1.39'),
}
# single records to drop from a group that stays: plugin -> {(group, raw FormID as stored, master index included)}.
# KittySpellPack01's override of Skyrim NPC dunHagsEndHagraven 09D257 - a placed reference in Enderal (cell
# MQ11bCaveEntrance 001D8C): the same record-type collision as the cells.
DROP_RECORDS = {'KittySpellPack01.esl': {('NPC_', 0x0009D257)}}


def count(data):
    """(records, groups) inside a run of records/groups."""
    recs = grps = 0
    i = 0
    while i < len(data):
        typ, size = data[i:i + 4], struct.unpack('<I', data[i + 4:i + 8])[0]
        if typ == b'GRUP':
            r, g = count(data[i + 24:i + size])
            recs, grps = recs + r, grps + g + 1
            i += size
        else:
            recs += 1
            i += 24 + size
    return recs, grps


def clean(modlist, plugin, src_mod, drop, expected, version):
    src = os.path.join(modlist, 'mods', src_mod, plugin)
    out_dir = os.path.join(modlist, 'mods', f'{src_mod} - Enderal cleaned plugin (Zenderal)')
    d = open(src, 'rb').read()
    assert d[:4] == b'TES4', f'{plugin}: not a plugin'
    hsize = 24 + struct.unpack('<I', d[4:8])[0]
    head, body = bytearray(d[:hsize]), d[hsize:]
    out, found, found_records, recs, grps, i = [], [], [], 0, 0, 0
    while i < len(body):
        assert body[i:i + 4] == b'GRUP', f'{plugin}: top level at {hsize + i:#x} is not a group'
        size, label, gtype = struct.unpack('<I4sI', body[i + 4:i + 16])
        if gtype == 0 and label.decode() in drop:
            r, g = count(body[i + 24:i + size])
            recs, grps = recs + r, grps + g + 1          # the dropped group itself counts too
            found.append(label.decode())
        elif gtype == 0 and any(g == label.decode() for g, _ in DROP_RECORDS.get(plugin, ())):
            ids = {f for g, f in DROP_RECORDS[plugin] if g == label.decode()}
            kept, j, g = [], i + 24, body[i:i + 24]
            while j < i + size:
                assert body[j:j + 4] != b'GRUP', f'{plugin}: {label} holds subgroups'
                rsize, fid = struct.unpack('<I', body[j + 4:j + 8])[0], struct.unpack('<I', body[j + 12:j + 16])[0]
                if fid in ids:
                    ids.discard(fid); recs += 1
                    found_records.append(f'{label.decode()} {fid:08X}')
                else:
                    kept.append(body[j:j + 24 + rsize])
                j += 24 + rsize
            assert not ids, f'{plugin}: {sorted(hex(x) for x in ids)} not found in {label} - check the mod again'
            kept = b''.join(kept)
            out.append(g[:4] + struct.pack('<I', 24 + len(kept)) + g[8:] + kept)
        else:
            out.append(body[i:i + size])
        i += size
    assert sorted(found) == sorted(drop), f'{plugin}: dropped {found}, expected {drop} - the mod changed, check it again'
    recs -= len(found_records)            # single records are reported apart from the groups' counts
    if expected:
        assert (recs, grps - len(drop)) == expected, \
            f'{plugin}: {recs} records / {grps - len(drop)} subgroups dropped, expected {expected} - check the mod again'
    h = head.find(b'HEDR')
    n = struct.unpack('<i', head[h + 10:h + 14])[0]
    gone = recs + grps + len(found_records)
    head[h + 10:h + 14] = struct.pack('<i', n - gone)
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, plugin), 'wb').write(bytes(head) + b''.join(out))
    meta = os.path.join(out_dir, 'meta.ini')
    if not os.path.exists(meta):
        open(meta, 'w', encoding='utf-8', newline='\r\n').write(f'[General]\nmodid=0\nversion={version}\ninstalled=true\n')
    print(f'{plugin}: dropped {"+".join(found)} ({recs} records, {grps - len(drop)} subgroups)'
          f'{" + " + ", ".join(found_records) if found_records else ""}; HEDR records {n} -> {n - gone}; wrote {out_dir}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default=r'E:\Zenderal')
    a = ap.parse_args()
    for plugin, (src_mod, drop, expected, version) in PACKS.items():
        clean(a.modlist, plugin, src_mod, drop, expected, version)


if __name__ == '__main__':
    sys.exit(main())
