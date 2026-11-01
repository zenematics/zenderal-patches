r"""Generate src/Fuse00ArmorRaces/Fuse00ArmorRacesESP/ArmorAddons/ -- never hand-edit it.

Why: Fuse00's Adventurer Armor lists the vanilla playable races on every armor addon
(ARMA). In Enderal the playable Nord and Redguard are NOT the vanilla 013746/013748 (those are the
unplayable NordRaceSkyrim/RedguardRaceSkyrim) but 033899 NordRace "Half Arazealean" and
033898 RedguardRace "Half Qyranian". A player of either race matches no addon, so the armor renders
as nothing.

Each override = the mod's ARMA verbatim with 033899 and 033898 appended to AdditionalRaces. No other
plugin in the list overrides these 8 addons (checked 2026-10-17), so verbatim is the winning record.

Helga armor (_Fuse00_ArmorHelga.esp) is deliberately NOT covered: overriding its addons made it a
master of this patch (dropped 2026-10-18).

Source: reference/mods/Fuse00AdventurerArmor (Spriggit 0.40.0 serialization of the installed plugin).
Re-serialize it and re-run this after the mod updates.

Usage:  python 01-build-race-overrides.py
"""
import os, glob, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SOURCES = [os.path.join(REPO, 'reference', 'mods', d) for d in ('Fuse00AdventurerArmor',)]
OUT = os.path.join(REPO, 'src', 'Fuse00ArmorRaces', 'Fuse00ArmorRacesESP', 'ArmorAddons')
ADD = ['033899:Skyrim.esm', '033898:Skyrim.esm']  # NordRace Half Arazealean, RedguardRace Half Qyranian
EXPECTED = 8  # Adventurer addons

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
done = 0
for src in SOURCES:
    files = sorted(glob.glob(os.path.join(src, 'ArmorAddons', '*.yaml')))
    if not files:
        raise SystemExit(f'no ArmorAddons in {src} -- serialize the plugin into reference/mods first')
    for path in files:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8').split('\r\n')
        start = lines.index('AdditionalRaces:')
        end = start + 1
        while end < len(lines) and lines[end].startswith('- '):
            end += 1
        races = [l[2:] for l in lines[start + 1:end]]
        if '013746:Skyrim.esm' not in races or any(r in races for r in ADD):
            raise SystemExit(f'unexpected race list in {os.path.basename(path)}: {races}')
        lines[end:end] = ['- ' + r for r in ADD]
        with open(os.path.join(OUT, os.path.basename(path)), 'wb') as f:
            f.write('\r\n'.join(lines).encode('utf-8'))
        done += 1
        print(f'{os.path.basename(path)}: {len(races)} -> {len(races) + len(ADD)} races')

if done != EXPECTED:
    raise SystemExit(f'expected {EXPECTED} addons, wrote {done}')
print(f'{done} overrides written to {OUT}')
