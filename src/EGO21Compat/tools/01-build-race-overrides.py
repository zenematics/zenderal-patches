r"""Generate src/EGO21Compat/EGO21CompatESP/Races/ -- never hand-edit it.

Why: Enderal 2.1 moved its playable Half Arazealean / Half Qyranian off 033899 NordRace / 033898
RedguardRace onto the vanilla FormIDs 013746 NordRace / 013748 RedguardRace (changelog line 139).
The old records survive as NordRaceOBSOLETE / RedguardRaceOBSOLETE, identical except that they lost
the Playable flag (only string order differs; checked against reference/base-2.1.4.4 on 2026-10-20).

EGO was written for 2.0, so all three of its race plugins (Gameplay Overhaul, Increased Carry
Weight, DS Movement Stamina UNIQUE RACES) still override 033899/033898 with Playable set. Chargen
then lists each race twice: the 2.1 one with vanilla Enderal stats, and EGO's obsolete one.

Per race this writes two overrides of the winning EGO record (DS Movement Stamina UNIQUE RACES,
which loads last of the three and so is what 2.0 players got):
  * onto the 2.1 playable FormID: verbatim, with the 2.1 EditorID -> EGO's stats on the race chargen
    now offers;
  * onto the obsolete FormID: verbatim minus Playable, with the 2.1 EditorID -> one entry in chargen,
    and any NPC EGO still points at the old race keeps EGO's stats.

Source: reference/mods/EGODSRaces (Spriggit 0.40.0 serialization of the installed plugin; equal to a
fresh serialization on 2026-10-20). Re-serialize it and re-run this after the mod updates.

Usage:  python 01-build-race-overrides.py
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(REPO, 'reference', 'mods', 'EGODSRaces', 'Races')
BASE21 = os.path.join(REPO, 'reference', 'base-2.1.4.4', 'Skyrim', 'Races')
OUT = os.path.join(REPO, 'src', 'EGO21Compat', 'EGO21CompatESP', 'Races')

# (EGO's source file, old FormKey, 2.1 obsolete EditorID, 2.1 playable FormKey, 2.1 playable EditorID)
RACES = [
    ('NordRace - 033899_Skyrim.esm.yaml', '033899', 'NordRaceOBSOLETE', '013746', 'NordRace'),
    ('RedguardRace - 033898_Skyrim.esm.yaml', '033898', 'RedguardRaceOBSOLETE', '013748', 'RedguardRace'),
]


def read(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8').split('\r\n')


def write(lines, name):
    with open(os.path.join(OUT, name), 'wb') as f:
        f.write('\r\n'.join(lines).encode('utf-8'))
    print(f'wrote {name}')


def retarget(lines, formkey, editorid):
    out = list(lines)
    if not out[0].startswith('FormKey: ') or not out[1].startswith('EditorID: '):
        raise SystemExit(f'unexpected header: {out[:2]}')
    out[0] = f'FormKey: {formkey}:Skyrim.esm'
    out[1] = f'EditorID: {editorid}'
    return out


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
for src, old, old_edid, new, new_edid in RACES:
    # The 2.1 records this relies on must exist with the EditorIDs assumed above.
    for fk, edid in ((old, old_edid), (new, new_edid)):
        if not os.path.exists(os.path.join(BASE21, f'{edid} - {fk}_Skyrim.esm.yaml')):
            raise SystemExit(f'{edid} {fk} not in {BASE21} -- serialize Enderal 2.1 Skyrim.esm there first')
    lines = read(os.path.join(SRC, src))
    if lines[0] != f'FormKey: {old}:Skyrim.esm':
        raise SystemExit(f'{src}: unexpected FormKey {lines[0]}')
    flag = lines.index('Flags:')
    playable = [i for i in range(flag + 1, len(lines)) if lines[i] == '- Playable']
    if len(playable) != 1 or any(not l.startswith('- ') for l in lines[flag + 1:playable[0]]):
        raise SystemExit(f'{src}: expected exactly one Playable flag in its Flags list')

    write(retarget(lines, new, new_edid), f'{new_edid} - {new}_Skyrim.esm.yaml')
    obsolete = retarget(lines, old, old_edid)
    del obsolete[playable[0]]
    write(obsolete, f'{old_edid} - {old}_Skyrim.esm.yaml')

written = len(os.listdir(OUT))
if written != 2 * len(RACES):
    raise SystemExit(f'expected {2 * len(RACES)} race overrides, wrote {written}')
print(f'{written} overrides written to {OUT}')
