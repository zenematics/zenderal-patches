"""Rebuild the `Zenderal - Silent Power Attack Grunts` MO2 mod from the game's own voice BSA.

The female player's loud power-attack yells are four PlayerDialogue_PowerAttack (0F8590) responses,
played from the race's female voice type: FemaleEvenToned (013ADD; Nord/Imperial/Breton) or
FemaleElfHaughty (013AF1; High Elf, Half Starling's WoodElfRace). This mod ships a silent .fuz loose at
each of those paths, so it beats `L - Voices.bsa`. Normal attack, hit and death grunts are untouched.

The silence is SureAI's own: a 0.19 s, peak-1/32768 XWMA placeholder already in `L - Voices.bsa`
(SILENT_SOURCE), copied verbatim, so nothing is encoded here and nothing is committed.

Usage:  python 01-build-silent-grunts.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, struct, hashlib

MOD = 'Zenderal - Silent Power Attack Grunts'
BS = chr(92)
ARCHIVE = 'L - Voices.bsa'

# A silent line SureAI shipped (a priest's generic line with no audio). 2300 bytes, lip size 0.
SILENT_SOURCE = 'sound\\voice\\skyrim.esm\\vt_male_priest\\genericdia_generic_priest__00111e1b_1.fuz'

VOICE_TYPES = ['femaleeventoned', 'femaleelfhaughty']

# PlayerDialogue_PowerAttack 0F8590 responses. Matched against a recording (2026-10-15): every loud
# yell in it was one of these, at the same playback gain each time.
SILENCE = ['000f85a3', '000f85a4', '000f85a5', '001295b4']


def read_index(path):
    with open(path, 'rb') as fh:
        magic, ver, fro, aflags, fcount, filecount, tfnl, tfil, ff = struct.unpack('<4sIIIIIIII', fh.read(36))
        assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
        counts = [struct.unpack('<QIIQ', fh.read(24))[1] for _ in range(fcount)]
        recs = []
        for c in counts:
            ln = fh.read(1)[0]; name = fh.read(ln).rstrip(b'\0').decode('latin1')
            for _ in range(c):
                h, size, off = struct.unpack('<QII', fh.read(16))
                recs.append((name, size, off))
        names = fh.read(tfil).split(b'\0')
    index = {}
    for (dn, size, off), n in zip(recs, names):
        index[(dn + BS + n.decode('latin1')).lower()] = (size, off)
    return aflags, index


def read_file(path, aflags, index, want):
    if want not in index:
        raise SystemExit(f'{want} not found in {path}')
    size, off = index[want]
    assert not (bool(aflags & 4) ^ bool(size & 0x40000000)), f'{want} is compressed; voices never are'
    size &= 0x3FFFFFFF
    with open(path, 'rb') as fh:
        fh.seek(off)
        blob = fh.read(size)
    if aflags & 0x100:
        ln = blob[0]; blob = blob[1 + ln:]
    return blob


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    data_dir = os.path.join(os.path.dirname(mods.rstrip('/' + BS)), 'Stock Game', 'Data')
    bsa = os.path.join(data_dir, ARCHIVE)
    aflags, index = read_index(bsa)

    silent = read_file(bsa, aflags, index, SILENT_SOURCE)
    assert silent[:4] == b'FUZE' and silent[12 + struct.unpack_from('<I', silent, 8)[0]:][8:12] == b'XWMA', 'bad silent source'

    out_root = os.path.join(mods, MOD)
    n = 0
    for vt in VOICE_TYPES:
        for fid in SILENCE:
            rel = f'sound\\voice\\skyrim.esm\\{vt}\\playerdial_playerdialogue__{fid}_1.fuz'
            assert rel in index, f'{rel} is not in {ARCHIVE}; the IDs or voice types are wrong'
            out = os.path.join(out_root, *rel.split(BS))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, 'wb') as fh:
                fh.write(silent)
            n += 1
            print(f'{len(silent):>6}  {hashlib.sha1(silent).hexdigest()[:12]}  {rel}')
    assert n == len(VOICE_TYPES) * len(SILENCE)
    print(f'{n} files -> {out_root}')


if __name__ == '__main__':
    main()
