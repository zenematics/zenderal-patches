r"""Generate src/MoonsteelPretty/MoonsteelPrettyESP/ -- never hand-edit Weapons/, Ammunitions/ or Projectiles/.

Why: EGO renames base Enderal's Silver Steel line to "Moonsteel" and repoints every item at vanilla
Dragonborn's Nordic meshes (DLC02\Weapons\Nordic\*), and gives its new Silver Arrow the Nordic quiver.
Pretty Common Armory replaces the meshes at base Enderal's paths (Weapons\NordHero\*,
Enderal\weapons\Silberstahldolch.nif), so none of its Moonsteel meshes are ever loaded. Pretty only
overrides the battleaxe records -- with base Enderal's, which reverts EGO's work on those three.

Each override = EGO's record verbatim with ObjectBounds, Model and FirstPersonModel taken from the
base-Enderal record whose mesh Pretty replaces. EGO's mace and warhammer (no base counterpart, no Pretty
mesh) and Tharael's Bow (a unique) are deliberately left on EGO's meshes.

Usage:  python 01-build-moonsteel-overrides.py
"""
import os, re, glob, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
EGO = os.path.join(REPO, 'reference', 'mods', 'EGO')
BASE = [os.path.join(REPO, 'reference', 'base', d) for d in ('EnderalFS', 'Skyrim')]  # FS wins over base
OUT = os.path.join(REPO, 'src', 'MoonsteelPretty', 'MoonsteelPrettyESP')
EGO_SUF = 'Enderal SE - Gameplay Overhaul.esp'

# (group, EGO record FormKey, base-Enderal template FormKey). Same key = EGO overrides that base record.
JOBS = [('Weapons', f'{k}:Skyrim.esm', f'{k}:Skyrim.esm') for k in (
    '0909D4', '148A62',                      # dagger
    '07C99F', '148A5E', '129735',            # sword
    '07C99E', '148A61',                      # greatsword
    '07C9A0', '148A60', '12EBC4',            # war axe
    '07C99C', '148A5F', '12E1DE',            # battleaxe (Pretty currently wins these with base Enderal's)
    '07C99D', '13CB17', '13C190',            # bow
)] + [
    ('Weapons', f'001F42:{EGO_SUF}', '0909D4:Skyrim.esm'),   # Moonsteel Dagger of Frost Wrath
    ('Weapons', f'001F41:{EGO_SUF}', '07C99F:Skyrim.esm'),   # Moonsteel Sword of Poison
    ('Weapons', f'001F94:{EGO_SUF}', '07C99F:Skyrim.esm'),   # Moonsteel Sword of Light
    ('Weapons', f'001F74:{EGO_SUF}', '07C9A0:Skyrim.esm'),   # Moonsteel War Axe of Poison
    ('Ammunitions', f'001D03:{EGO_SUF}', '08F3AC:Skyrim.esm'),  # Silver Arrow <- Fine Steel Arrow (NordHeroArrow)
    ('Projectiles', f'001D02:{EGO_SUF}', '0EAFE0:Skyrim.esm'),  # its projectile <- NordHeroArrowProjectile
]
SWAP = {'Weapons': ('ObjectBounds', 'Model', 'FirstPersonModel'),
        'Ammunitions': ('ObjectBounds', 'Model'),
        'Projectiles': ('ObjectBounds', 'Model')}
EXPECTED = 22


def find(roots, group, fk):
    hexid, plugin = fk.split(':', 1)
    for r in roots:
        hits = glob.glob(os.path.join(r, group, f'* - {hexid}_{plugin}.yaml'))
        if hits:
            assert len(hits) == 1, hits
            return hits[0]
    raise SystemExit(f'not found: {group} {fk}')


def blocks(path):
    """Split a record file into ordered [key, text] top-level blocks (keeps CRLF verbatim)."""
    with open(path, 'rb') as fh:
        lines = fh.read().decode('utf-8').splitlines(keepends=True)
    out = []
    for ln in lines:
        if ln[:1] not in (' ', '-') and ':' in ln:
            out.append([ln.split(':', 1)[0], ln])
        else:
            out[-1][1] += ln
    return out


def main():
    if os.path.isdir(OUT):
        for g in SWAP:
            shutil.rmtree(os.path.join(OUT, g), ignore_errors=True)
    n = 0
    for group, ego_fk, base_fk in JOBS:
        src = find([EGO], group, ego_fk)
        rec = blocks(src)
        base = dict(blocks(find(BASE, group, base_fk)))
        keys = [k for k, _ in rec]
        model_before = dict(rec)['Model']
        assert 'DLC02' in model_before, (src, model_before)       # still on EGO's Nordic mesh
        for field in SWAP[group]:
            if field == 'ObjectBounds' and field not in keys:
                # Spriggit omits all-zero bounds. Insert base's after EditorID, or keep both absent.
                if field in base:
                    rec.insert(keys.index('EditorID') + 1, [field, base[field]])
                    keys = [k for k, _ in rec]
                continue
            assert field in keys, (ego_fk, field)
            if field not in base:
                assert field == 'ObjectBounds', (base_fk, field)
                rec[keys.index(field)][1] = ''
                continue
            rec[keys.index(field)][1] = base[field]
        model_after = dict(rec)['Model']
        assert 'DLC0' not in model_after and re.search(r'NordHero|Silberstahldolch', model_after), model_after
        dst = os.path.join(OUT, group, os.path.basename(src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as fh:
            fh.write(''.join(t for _, t in rec).encode('utf-8'))
        n += 1
        print(f'{ego_fk:45s} <- {base_fk}  {model_after.splitlines()[1].strip()}')
    assert n == EXPECTED, n
    print(f'{n} overrides written')


if __name__ == '__main__':
    main()
