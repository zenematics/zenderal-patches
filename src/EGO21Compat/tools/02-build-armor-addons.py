r"""Generate src/EGO21Compat/EGO21CompatESP/ArmorAddons/ -- never hand-edit it.

Why: Enderal 2.1 added its relocated playable races 013746 NordRace / 013748 RedguardRace to its
armor addons. EGO's 2.0-era overrides of some addons list only the old 033899 / 033898, and where EGO
wins, the armor is invisible on a 2.1 Half Arazealean / Half Qyranian player (it equips, nothing
renders): Boots of the Righteous Path, reported 2026-10-22.

Per addon this writes EGO's record verbatim with the missing new race(s) inserted into
AdditionalRaces in FormID order, as 2.1's own records have them. Nothing else changes.

ADDONS is the output of 00-scan-arma-races.py (2026-10-22: 4 of 919 base ARMAs, all EGO winners).
13 more EGO addons lack the races too, but a later plugin wins them with both races present
(Audio Overhaul - Enderal patch, Pretty), so they are fine and deliberately not overridden.

Source: reference/mods/EGO (Spriggit 0.40.0 serialization of Enderal SE - Gameplay Overhaul.esp).
Re-run 00 and this after EGO or any armor mod changes.

Usage:  python 02-build-armor-addons.py
"""
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(REPO, 'reference', 'mods', 'EGO', 'ArmorAddons')
BASE21 = os.path.join(REPO, 'reference', 'base-2.1.4.4', 'Skyrim', 'ArmorAddons')
OUT = os.path.join(REPO, 'src', 'EGO21Compat', 'EGO21CompatESP', 'ArmorAddons')

NEW_RACES = ['013746', '013748']
ADDONS = [
    '03E_24_BootsOfTheRighteousPathAA - 145879_Skyrim.esm.yaml',
    '01E_07_SteelShieldAA - 14587A_Skyrim.esm.yaml',
    '02E_18_PyreanShieldAA - 0E35C7_Skyrim.esm.yaml',
    '_50E_LSet_VenturerArmorAA - 14483D_Skyrim.esm.yaml',
]


def read(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8').split('\r\n')


def race_block(lines, src):
    """(start, end) of the '- xxxxxx:Skyrim.esm' lines under AdditionalRaces."""
    start = lines.index('AdditionalRaces:') + 1
    end = start
    while end < len(lines) and lines[end].startswith('- '):
        end += 1
    races = [l[2:] for l in lines[start:end]]
    if not races or any(not r.endswith(':Skyrim.esm') for r in races) or races != sorted(races):
        raise SystemExit(f'{src}: AdditionalRaces is not a sorted Skyrim.esm list: {races}')
    return start, end


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
added = 0
for name in ADDONS:
    lines = read(os.path.join(SRC, name))
    base = read(os.path.join(BASE21, name))
    if lines[0] != base[0]:
        raise SystemExit(f'{name}: FormKey differs from 2.1 ({lines[0]} vs {base[0]})')
    s, e = race_block(lines, name)
    bs, be = race_block(base, 'base ' + name)
    races = [l[2:] for l in lines[s:e]]
    missing = [f'{r}:Skyrim.esm' for r in NEW_RACES if f'- {r}:Skyrim.esm' in base[bs:be] and f'{r}:Skyrim.esm' not in races]
    if not missing:
        raise SystemExit(f'{name}: EGO already has the 2.1 races -- rerun 00-scan-arma-races.py and update ADDONS')
    races = sorted(races + missing)
    lines[s:e] = [f'- {r}' for r in races]
    with open(os.path.join(OUT, name), 'wb') as f:
        f.write('\r\n'.join(lines).encode('utf-8'))
    added += len(missing)
    print(f'wrote {name} (+{" ".join(m[:6] for m in missing)})')

written = len(os.listdir(OUT))
if written != len(ADDONS) or added != len(NEW_RACES) * len(ADDONS):
    raise SystemExit(f'expected {len(ADDONS)} addons / {len(NEW_RACES) * len(ADDONS)} races, got {written} / {added}')
print(f'{written} armor addon overrides written to {OUT}')
