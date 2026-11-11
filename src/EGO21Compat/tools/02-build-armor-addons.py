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

MOD_ADDONS (2026-11-01): 22 addons that mods define themselves list the old 033899 / 033898 but not
2.1's twin, so the same armor is invisible on a 2.1 player (MadArthur: Kata's Arcanist Robes left him
naked). 00 only compares base-defined addons, so these were found by a scan of every winning ARMA for
"old race present, its 2.1 twin missing". Each is the mod's own record (it wins: nothing overrides
them) with each twin inserted right after its old race; masters of this plugin must include the mod.

2026-11-11: Pretty Enderal Armory 2.1 lists both 2.1 races on its own six addons (Common 000800, Mages
000800, Holy Order 000803/804/805/80F), so they were dropped here (22 -> 16) along with the three Pretty masters.

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

MODS = os.path.join(REPO, 'reference', 'mods')
TWINS = {'033899': '013746', '033898': '013748'}
# (reference/mods folder, plugin, [FormIDs]) -- 2026-11-01 scan of every winning ARMA in Ultra.
MOD_ADDONS = [
    ('KataPUMB', 'KataPUMBSpellPack.esp', ['002E50']),
    ('KataPUMBSpellPackage', 'KataPUMB_SpellPackage.esp',
     ['00223F', '002240', '002241', '002243', '002244', '002245', '00571D', '0098C8', '0098CA', '0098CC', '0098CE']),
    ('EAM', 'EAM SE - Enderal Apothecarii Monastery.esp', ['05041C', '05041D', '05041E', '05041F']),
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

mod_count = 0
for folder, plugin, ids in MOD_ADDONS:
    src = os.path.join(MODS, folder, 'ArmorAddons')
    for fid in ids:
        names = [n for n in os.listdir(src) if n.endswith(f' - {fid}_{plugin}.yaml')]
        if len(names) != 1:
            raise SystemExit(f'{folder}: expected one ArmorAddon {fid}_{plugin}, found {names}')
        name = names[0]
        lines = read(os.path.join(src, name))
        start = lines.index('AdditionalRaces:') + 1
        end = start
        while end < len(lines) and lines[end].startswith('- '):
            end += 1
        races = [l[2:8] for l in lines[start:end] if l.endswith(':Skyrim.esm')]
        twins = [(old, new) for old, new in TWINS.items() if old in races and new not in races]
        if not twins:
            raise SystemExit(f'{name}: no old race missing its 2.1 twin -- rescan and update MOD_ADDONS')
        for old, new in twins:
            i = lines.index(f'- {old}:Skyrim.esm', start, end)
            lines.insert(i + 1, f'- {new}:Skyrim.esm')
            end += 1
            added += 1
        with open(os.path.join(OUT, name), 'wb') as f:
            f.write('\r\n'.join(lines).encode('utf-8'))
        mod_count += 1
        print(f'wrote {name} (+{" ".join(n for _, n in twins)})')

written = len(os.listdir(OUT))
expect_races = len(NEW_RACES) * (len(ADDONS) + mod_count)
if written != len(ADDONS) + mod_count or mod_count != 16 or added != expect_races:
    raise SystemExit(f'expected {len(ADDONS) + 16} addons / {expect_races} races, got {written} / {added}')
print(f'{written} armor addon overrides written to {OUT}')
