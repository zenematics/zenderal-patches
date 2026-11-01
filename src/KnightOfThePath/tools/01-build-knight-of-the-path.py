"""Build `Zenderal - Knight of the Path`: Enderal Remastered Armory's Righteous Path remaster as its own armor set.

Enderal Remastered Armory Part 1 and Pretty Righteous Path Armory both replace the Righteous Path meshes at
`armor\\ebony\\{m,f}\\` and the shield at `weapons\\ebony\\ebonyshield.nif`, so only one of them can ever be seen.
Pretty keeps those paths (it IS the Righteous Path); this copies ERA's five pieces to
`armor\\zenderal\\knightofthepath\\` and gives them their own records:

  ARMA 0x800-0x803  copies of the winning Righteous Path armor addons, meshes repointed
  ARMO 0x804-0x807  copies of the winning FORGED Righteous Path armors (stats, keywords), renamed, new addon
  COBJ 0x808-0x80B  copies of the winning Forged forge recipes (same blueprint, Smithing 50, materials)
  COBJ 0x80C-0x80F  copies of the Forged temper recipes
  0x810-0x813       the shield's ARMA, ARMO, forge recipe and temper recipe (added second)

Winning versions [scanned 2026-10-27, every enabled plugin]: Forged cuirass 13C54B, Forged shield 13C54D and the
five forge recipes are EGO's; boots addon 145879 is Zenderal - EGO 2.1 Compatibility's; everything else is base
Enderal (EAM only adds its own addon copies, Enderal SE - Bug Fixes only touches weapons). ERA's meshes keep pointing at ERA's own
textures (`textures\\armor_replacer\\ebony\\`, nothing else ships them), so ERA stays required.

The meshes are ERA's work, so they are copied from the user's install into the MO2 mod, never committed.

Usage:  python 01-build-knight-of-the-path.py [<mods dir>] [--dry-run]     (default E:/Zenderal/mods)
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, '..', 'KnightOfThePathESP')
PLUGIN = 'Zenderal - Knight of the Path.esp'
MOD = 'Zenderal - Knight of the Path'
ERA = 'Enderal Remastered Armory Part 1 - Standard Armory'
NEW_DIR = 'armor\\zenderal\\knightofthepath'

BASE = os.path.join(REPO, 'reference', 'base', 'Skyrim')
EGO = os.path.join(REPO, 'reference', 'mods', 'EGO - Enderal Gameplay Overhaul')
COMPAT = os.path.join(REPO, 'src', 'EGO21Compat', 'EGO21CompatESP')

# (piece, name, addon, forged armor, forge recipe, temper recipe, (ARMA, ARMO, recipe, temper) FormIDs)
PIECES = [
    ('Helmet', 'Knight of the Path Helmet',
     (BASE, 'ArmorAddons', '03E_24_HelmetOfTheRighteousPathAA - 05B69A_Skyrim.esm.yaml'),
     (BASE, 'Armors', '_03E_24_HelmetOfTheRighteousPathForged - 13C54C_Skyrim.esm.yaml'),
     (EGO, 'ConstructibleObjects', '_03E_RecipeArmor_24_HelmetOfTheRighteousPathForged - 13C54E_Skyrim.esm.yaml'),
     (BASE, 'ConstructibleObjects', '_03E_Temper_HelmetOfTheRighteousPathForged - 148A48_Skyrim.esm.yaml'),
     (0x800, 0x804, 0x808, 0x80C)),
    ('Cuirass', 'Knight of the Path Cuirass',
     (BASE, 'ArmorAddons', '03E_24_CuirassOfTheRighteousPathAA - 05B69C_Skyrim.esm.yaml'),
     (EGO, 'Armors', '_03E_24_CuirassOfTheRighteousPathForged - 13C54B_Skyrim.esm.yaml'),
     (EGO, 'ConstructibleObjects', '_03E_RecipeArmor_24_CuirassOfTheRighteousPathForged - 13C54F_Skyrim.esm.yaml'),
     (BASE, 'ConstructibleObjects', '_03E_Temper_CuirassOfTheRighteousPathForged - 148A46_Skyrim.esm.yaml'),
     (0x801, 0x805, 0x809, 0x80D)),
    ('Gauntlets', 'Knight of the Path Gauntlets',
     (BASE, 'ArmorAddons', '03E_24_GauntletsOfTheRighteousPathAA - 05B69B_Skyrim.esm.yaml'),
     (BASE, 'Armors', '_03E_24_GauntletsOfTheRighteousPathForged - 13C54A_Skyrim.esm.yaml'),
     (EGO, 'ConstructibleObjects', '_03E_RecipeArmor_24_GauntletsOfTheRighteousPathForged - 13C550_Skyrim.esm.yaml'),
     (BASE, 'ConstructibleObjects', '_03E_Temper_GauntletsOfTheRighteousPathForged - 148A44_Skyrim.esm.yaml'),
     (0x802, 0x806, 0x80A, 0x80E)),
    ('Boots', 'Knight of the Path Boots',
     (COMPAT, 'ArmorAddons', '03E_24_BootsOfTheRighteousPathAA - 145879_Skyrim.esm.yaml'),
     (BASE, 'Armors', '_03E_24_BootsOfTheRighteousPathForged - 13C552_Skyrim.esm.yaml'),
     (EGO, 'ConstructibleObjects', '_03E_RecipeArmor_24_BootsOfTheRighteousPathForged - 13C551_Skyrim.esm.yaml'),
     (BASE, 'ConstructibleObjects', '_03E_Temper_BootsOfTheRighteousPathForged - 148A4B_Skyrim.esm.yaml'),
     (0x803, 0x807, 0x80B, 0x80F)),
    ('Shield', 'Knight of the Path Shield',
     (BASE, 'ArmorAddons', '03E_24_ShieldOfTheRighteousPathAA - 0E400D_Skyrim.esm.yaml'),
     (EGO, 'Armors', '_03E_24_ShieldOfTheRighteousPathForged - 13C54D_Skyrim.esm.yaml'),
     (EGO, 'ConstructibleObjects', '_03E_RecipeArmor_24_ShieldOfTheRighteousPathForged - 13C553_Skyrim.esm.yaml'),
     (BASE, 'ConstructibleObjects', '_03E_Temper_ShieldOfTheRighteousPathForged - 148A49_Skyrim.esm.yaml'),
     (0x810, 0x811, 0x812, 0x813)),
]

# armor\ebony\{m,f}\<file> -> <NEW_DIR>\{m,f}\<file>;  weapons\ebony\<file> -> <NEW_DIR>\<file>
MESH_RE = re.compile(r'(?i)(File: )(?:armor\\ebony\\([mf])\\|weapons\\ebony\\())([A-Za-z0-9_]+\.nif)')


def load(src):
    path = os.path.join(*src)
    raw = open(path, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    return raw.split(nl), nl, path


def one(lines, pattern, path):
    hits = [i for i, l in enumerate(lines) if re.match(pattern, l)]
    assert len(hits) == 1, (path, pattern, hits)
    return hits[0]


def retarget(lines, path, fid, edid):
    lines[one(lines, r'FormKey: ', path)] = f'FormKey: {fid:06X}:{PLUGIN}'
    lines[one(lines, r'EditorID: ', path)] = f'EditorID: {edid}'


def rename(lines, path, name):
    """Replace the (possibly localized) Name block with a plain English value."""
    i = one(lines, r'Name:$', path)
    j = i + 1
    while j < len(lines) and lines[j].startswith(' '):
        j += 1
    lines[i:j] = ['Name:', '  TargetLanguage: English', f'  Value: {name}']


def repoint_meshes(lines, path, meshes):
    """Point every armor\\ebony mesh at the new folder; drop each one's MODT (Data) line."""
    out, n = [], 0
    for l in lines:
        m = MESH_RE.search(l)
        if m:
            sub = (m.group(2) or '').lower()
            name = m.group(4).lower()
            rel = f'{NEW_DIR}\\{sub}\\{name}' if sub else f'{NEW_DIR}\\{name}'
            out.append(l[:m.start()] + m.group(1) + rel)
            meshes.add((sub, name))
            n += 1
            continue
        if n and re.match(r'\s+Data: 0x', l) and re.search(r'File: ', out[-1]):
            continue
        out.append(l)
    assert n, (path, 'no ebony mesh paths')
    assert not any('\\ebony\\' in l.lower() for l in out if 'File:' in l), path
    return out


def swap_ref(lines, path, old, new):
    hits = [i for i, l in enumerate(lines) if l.strip().endswith(old)]
    assert len(hits) == 1, (path, old, hits)
    i = hits[0]
    lines[i] = lines[i][:len(lines[i]) - len(old)] + new


def write(folder, edid, fid, lines, nl, dry):
    d = os.path.join(OUT, folder)
    f = os.path.join(d, f'{edid} - {fid:06X}_{PLUGIN}.yaml')
    if not dry:
        os.makedirs(d, exist_ok=True)
        with open(f, 'wb') as fh:
            fh.write(nl.join(lines).encode('utf-8'))
    print('  ', folder, f'{fid:06X}', edid)


def mesh_variants(sub, name):
    """Both weight-slider halves of a _1 mesh; ground models as they are."""
    m = re.match(r'(.+)_[01]\.nif$', name)
    return [f'{m.group(1)}_0.nif', f'{m.group(1)}_1.nif'] if m else [name]


def find_ci(folder, name):
    for f in os.listdir(folder):
        if f.lower() == name:
            return os.path.join(folder, f)
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    mods = args[0] if args else 'E:/Zenderal/mods'
    for sub in ('ArmorAddons', 'Armors', 'ConstructibleObjects'):
        if not dry and os.path.isdir(os.path.join(OUT, sub)):
            shutil.rmtree(os.path.join(OUT, sub))
    meshes = set()
    for piece, name, aa, armo, recipe, temper, (aa_id, armo_id, cobj_id, temper_id) in PIECES:
        aa_edid = f'ZEN_KnightOfThePath{piece}AA'
        armo_edid = f'ZEN_KnightOfThePath{piece}'
        print(piece)

        lines, nl, path = load(aa)
        old_aa = re.search(r' - ([0-9A-F]{6})_', path).group(1)
        retarget(lines, path, aa_id, aa_edid)
        lines = repoint_meshes(lines, path, meshes)
        write('ArmorAddons', aa_edid, aa_id, lines, nl, dry)

        lines, nl, path = load(armo)
        old_armo = re.search(r' - ([0-9A-F]{6})_', path).group(1)
        retarget(lines, path, armo_id, armo_edid)
        rename(lines, path, name)
        lines = repoint_meshes(lines, path, meshes)
        swap_ref(lines, path, f'- {old_aa}:Skyrim.esm', f'- {aa_id:06X}:{PLUGIN}')
        write('Armors', armo_edid, armo_id, lines, nl, dry)

        for src, fid, edid in ((recipe, cobj_id, f'ZEN_RecipeArmor_KnightOfThePath{piece}'),
                               (temper, temper_id, f'ZEN_Temper_KnightOfThePath{piece}')):
            lines, nl, path = load(src)
            retarget(lines, path, fid, edid)
            swap_ref(lines, path, f'CreatedObject: {old_armo}:Skyrim.esm', f'CreatedObject: {armo_id:06X}:{PLUGIN}')
            write('ConstructibleObjects', edid, fid, lines, nl, dry)

    copied = 0
    for sub, name in sorted(meshes):
        if sub:
            src_dir = find_ci(os.path.join(mods, ERA, 'meshes', 'armor', 'ebony'), sub)
        else:
            src_dir = os.path.join(mods, ERA, 'meshes', 'weapons', 'ebony')
        assert src_dir and os.path.isdir(src_dir), (sub, name)
        for v in mesh_variants(sub, name):
            src = find_ci(src_dir, v)
            assert src, f'ERA has no {src_dir}\\{v}'
            dst = os.path.join(mods, MOD, 'meshes', NEW_DIR.replace('\\', os.sep), sub, v)
            if not dry:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
            copied += 1
    print(f'{copied} meshes {"would be " if dry else ""}copied from {ERA}')


if __name__ == '__main__':
    main()
