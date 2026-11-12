"""Build MO2 mod `Zenderal - Animated Potion Bottles`: the bottle Ultimate Animated Potions NG puts in the hand while
drinking is the potion's own (Less silly potions) bottle, not a vanilla one.

Curator's report (2026-11-12): the potions drunk through Swift Potion / the animated potions didn't match Less silly
potions Enderal SE (Enderal Nexus 85).

How UAPNG picks the prop (read from UAPNG.dll 2.9.1, not its docs): on each potion equip it takes the file name of the
potion's model (everything after the last slash), builds `AnimObjects\\<file name>`, checks that
`Data\\meshes\\AnimObjects\\<file name>` exists (std::filesystem, so loose files only) and sets it as the model of its
drinking anim object; otherwise it uses `Animobjects\\AnimObjectDrinkPotion.nif` (the generic bottle, in the BSA).
UAPNG ships those per-model props as copies of the VANILLA potion meshes. Less silly potions (85) and Visual
consistency for Less silly potions (Enderal Nexus 144) replace only `meshes\\clutter\\potions\\*` (and two meshes
elsewhere), so the world and inventory showed their bottles and the hand UAPNG's vanilla ones (25 drinkable
potion meshes in the Ultra profile). The Less silly poison meshes are built too (harmless: every item using them is a
Poison, applied to a weapon, never drunk).

UAPNG's props and the Less silly patch for the old ZUPA keep the world mesh's frame (identity transforms, bottle
base at z = 0): an anim object here is the world mesh with an NiStringExtraData "Prn" = "AnimObjectR" on its root and
no collision. So for every mesh the two Less silly mods ship, this takes the WINNING loose copy in the profile (so a
later override of the world bottle is matched too), copies its shapes (geometry, UVs, normals, vertex colours,
shader, textures, alpha) under a fresh BSFadeNode, adds the Prn, and drops collision, BSX and the inventory marker.
Every output is read back and compared with its source.

Lift (2026-11-12, curator's recording: "the potions sit too low in the hand"): the drinking clips that play are
JellyFish Ultimate Animated Potions NG's (OAR priority 1, no conditions; standing and sneak, both views), and all four
close the fist at the same place in the prop frame: fingers 7.5-13.1 up the prop's Z, thumb 12.1-12.3 (tools/00).
The Less silly bottles are 8.3-14.6 tall (vanilla's 14.5-30), so only the cork reached the fist and the glass hung
below it. Each bottle is raised along its own axis so the top of its body sits at the thumb (GRIP_TOP): the fist wraps
the upper body, band and cork stand above it. Body top = the top of the `Liquid` shape (the liquid fills the body);
the poison vial has none, so BODY_FALLBACK of its height. The lift is the shapes' translation, vertices untouched.
UAPNG's own third-person walk/run clips (JellyFish ships none) hold the prop at its base (-0.9), so a bottle drunk
while moving in third person sits above the hand; UAPNG's clips never agreed with each other (its 1st person: 4.3).

The meshes are the Less silly authors' work, built from the user's own install: never committed. The MO2 mod must
outrank Ultimate Animated Potions NG and `Less Silly Potions for Zxlice's ultimate potion animation` (both ship
`meshes\\Animobjects\\Potion*.nif`). Rerun after either Less silly mod, a potion mesh mod or UAPNG changes.

Usage: python src/AnimatedPotionBottles/tools/01-build-potion-props.py [--profile Ultra] [--check]
       (--check: report what would be built and every mismatch, write nothing)
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8'))
sys.path.insert(0, TOOLS['pynifly'])
from pyn.pynifly import NifFile, NiStringExtraData, nifly  # noqa: E402
from pyn.nifdefs import BSTriShapeBuf, PynBufferTypes  # noqa: E402
from pyn.structs import TransformBuf  # noqa: E402

ML = TOOLS['modlistRoot']
SOURCE_MODS = ('Less silly potions Enderal SE', 'Visual consistency for Less silly potions')
OUT_NAME = 'Zenderal - Animated Potion Bottles'
OUT_MOD = os.path.join(ML, 'mods', OUT_NAME)
PROP_DIR = ('meshes', 'Animobjects')
PRN = 'AnimObjectR'    # UAPNG's own props and the vanilla potion anim object hang on the right-hand prop bone
GRIP_TOP = 12.2        # JellyFish's thumb, prop Z (tools/00: 12.06-12.28 over its four clips)
# Curator (2026-11-12): "it makes no sense to drink with the cork on". The prop only exists while drinking (JellyFish's
# clips load it at 0.2 s and unload it at 1.57 s), so it is built uncorked. Every Less silly bottle has its cork as
# its own shape over an open glass neck (no glass near the axis at the top); the poison vial's stopper is part of its
# one bottle shape, but every item using it is a Poison (applied, never drunk).
DROP_SHAPES = {'cork'}
BODY_FALLBACK = 0.6    # body top as a fraction of the bottle's height when it has no `Liquid` shape
LIFT_RANGE = (0.0, 9.0)


def enabled_mods(profile):
    """Enabled mods, lowest priority first (modlist.txt lists the highest first)."""
    path = os.path.join(ML, 'profiles', profile, 'modlist.txt')
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if line.startswith('+') and line[1:] != OUT_NAME:
            out.append(line[1:])
    out.reverse()
    return out


def loose_files(mod):
    """{lowercase 'meshes/...' path: real path} of every .nif under a mod's meshes folder."""
    base = os.path.join(ML, 'mods', mod)
    out = {}
    for dp, _dn, fn in os.walk(os.path.join(base, 'meshes')):
        for f in fn:
            if f.lower().endswith('.nif'):
                p = os.path.join(dp, f)
                out[os.path.relpath(p, base).replace('\\', '/').lower()] = p
    return out


def textures(nif, shape):
    return [shape.shader._readtexture(nif._handle, shape._handle, i + 1) for i in range(9)]


def check_flat(path, nif):
    for s in nif.shapes:
        x = s.transform
        rot_ok = all(abs(x.rotation[i][j] - (1.0 if i == j else 0.0)) < 1e-4 for i in range(3) for j in range(3))
        if (s.blockname != 'BSTriShape' or s.parent is None or s.parent.name != nif.rootNode.name
                or not rot_ok or abs(x.scale - 1.0) > 1e-4):
            sys.exit(f'{path}: shape {s.name} is a {s.blockname} under {s.parent and s.parent.name} (rotation ok '
                     f'{rot_ok}, scale {x.scale}); only flat, unrotated BSTriShapes are handled')


def body_top(path):
    """Prop Z of the top of the bottle's body: its `Liquid` shape's top, else BODY_FALLBACK of the bottle's height."""
    nif = NifFile(path)
    check_flat(path, nif)
    top = {s.name.lower(): max(v[2] for v in s.verts) + s.transform.translation[2] for s in nif.shapes}
    if 'liquid' in top:
        return top['liquid'], 'liquid'
    return BODY_FALLBACK * max(top.values()), 'fallback'


def kept(nif):
    return [s for s in nif.shapes if s.name.lower() not in DROP_SHAPES]


def build(src_path, out_path, lift):
    src = NifFile(src_path)
    check_flat(src_path, src)
    dst = NifFile()
    dst.initialize('SKYRIMSE', out_path, 'BSFadeNode', 'Scene Root')
    for s in kept(src):
        props = BSTriShapeBuf()
        props.bufType = PynBufferTypes.BSTriShapeBufType
        d = dst.createShapeFromData(s.name, s.verts, s.tris, s.uvs, s.normals, props=props, parent=dst.rootNode)
        x = TransformBuf()
        t = s.transform.translation
        x.store((t[0], t[1], t[2] + lift), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), [1.0, 1.0, 1.0])
        d.transform = x
        if s.colors:
            d.set_colors(s.colors)
        s.shader.properties.copyto(d.shader.properties)
        d.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
        d.shader.name = s.shader.name
        d.save_shader_attributes()
        for i, t in enumerate(textures(src, s)):
            nifly.setShaderTextureSlot(dst._handle, d._handle, i, t.encode('utf-8'))
        if s.has_alpha_property:
            d.has_alpha_property = True
            d.alpha_property.properties.flags = s.alpha_property.properties.flags
            d.alpha_property.properties.threshold = s.alpha_property.properties.threshold
            d.save_alpha_property()
    NiStringExtraData.New(dst, name='Prn', string_value=PRN, parent=dst.rootNode)
    dst.save()
    verify(src_path, out_path, lift)


def verify(src_path, out_path, lift):
    src, out = NifFile(src_path), NifFile(out_path)
    prn = [e.string_data for e in out.rootNode.extra_data() if e.blockname == 'NiStringExtraData' and e.name == 'Prn']
    problems = []
    if prn != [PRN]:
        problems.append(f'Prn {prn}')
    if [s.name for s in out.shapes] != [s.name for s in kept(src)]:
        problems.append('shape names %s vs %s' % ([s.name for s in out.shapes], [s.name for s in kept(src)]))
    for a, b in zip(kept(src), out.shapes):
        if len(a.verts) != len(b.verts) or len(a.tris) != len(b.tris):
            problems.append(f'{a.name}: {len(b.verts)}/{len(b.tris)} verts/tris, source {len(a.verts)}/{len(a.tris)}')
        if max(abs(p - q) for u, v in zip(a.verts, b.verts) for p, q in zip(u, v)) > 1e-3:
            problems.append(f'{a.name}: vertices moved')
        ta, tb = a.transform.translation, b.transform.translation
        if abs(tb[0] - ta[0]) > 1e-4 or abs(tb[1] - ta[1]) > 1e-4 or abs(tb[2] - (ta[2] + lift)) > 1e-4:
            problems.append(f'{a.name}: translation {tuple(tb)}, expected source {tuple(ta)} + {lift:.3f} up')
        if textures(src, a) != textures(out, b):
            problems.append(f'{a.name}: textures {textures(out, b)} vs {textures(src, a)}')
        pa, pb = a.shader.properties, b.shader.properties
        for f in ('Shader_Type', 'Shader_Flags_1', 'Shader_Flags_2', 'Glossiness', 'Alpha'):
            if getattr(pa, f) != getattr(pb, f):
                problems.append(f'{a.name}: shader {f} {getattr(pb, f)} vs {getattr(pa, f)}')
        if a.has_alpha_property != b.has_alpha_property or (a.has_alpha_property and (
                a.alpha_property.properties.flags != b.alpha_property.properties.flags
                or a.alpha_property.properties.threshold != b.alpha_property.properties.threshold)):
            problems.append(f'{a.name}: alpha property differs')
        if len(a.colors) != len(b.colors):
            problems.append(f'{a.name}: {len(b.colors)} vertex colours, source {len(a.colors)}')
    if problems:
        sys.exit(f'{out_path} does not match {src_path}:\n  ' + '\n  '.join(problems))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    mods = enabled_mods(args.profile)
    missing = [m for m in SOURCE_MODS if m not in mods]
    if missing:
        sys.exit(f'not enabled in profile {args.profile}: {missing}')
    files = {m: loose_files(m) for m in mods}
    wanted = sorted({p for m in SOURCE_MODS for p in files[m]})

    plan = {}   # prop file name (lower) -> (rel path, winning mod, real path)
    for rel in wanted:
        winner = [m for m in mods if rel in files[m]][-1]
        name = os.path.basename(files[winner][rel])
        key = name.lower()
        if key in plan and plan[key][2] != files[winner][rel]:
            sys.exit(f'two meshes named {name}: {plan[key][0]} and {rel} (UAPNG keys props by file name only)')
        plan[key] = (rel, winner, files[winner][rel])

    prop_rel = '/'.join(PROP_DIR).lower() + '/'
    replaced = {k for k in plan if any(prop_rel + k in files[m] for m in mods)}
    by_winner = {}
    for rel, winner, _p in plan.values():
        by_winner[winner] = by_winner.get(winner, 0) + 1
    lifts = {}
    for k, (rel, winner, src_path) in plan.items():
        top, how = body_top(src_path)
        lifts[k] = (GRIP_TOP - top, top, how)
        if not LIFT_RANGE[0] <= lifts[k][0] <= LIFT_RANGE[1]:
            sys.exit(f'{rel}: lift {lifts[k][0]:.2f} outside {LIFT_RANGE} (body top {top:.2f} by {how})')
    print(f'{len(plan)} props from {by_winner}; {len(replaced)} replace an existing loose prop '
          f'(UAPNG / the old ZUPA patch), {len(plan) - len(replaced)} replace the generic fallback bottle; '
          f'lifted {min(v[0] for v in lifts.values()):.2f}-{max(v[0] for v in lifts.values()):.2f} up')
    if args.check:
        for k in sorted(plan):
            rel, winner, _p = plan[k]
            lift, top, how = lifts[k]
            print('  %-36s <- %-52s %-42s body top %5.2f (%s) lift %+5.2f%s' % (
                k, rel, winner, top, how, lift, '' if k in replaced else '  (was generic)'))
        return

    out_dir = os.path.join(OUT_MOD, *PROP_DIR)
    if os.path.isdir(os.path.join(OUT_MOD, 'meshes')):
        shutil.rmtree(os.path.join(OUT_MOD, 'meshes'))
    os.makedirs(out_dir)
    for k in sorted(plan):
        rel, winner, src_path = plan[k]
        build(src_path, os.path.join(out_dir, os.path.basename(src_path)), lifts[k][0])
    uncorked = sum(1 for k in plan if any(s.name.lower() in DROP_SHAPES for s in NifFile(plan[k][2]).shapes))
    print(f'wrote {len(plan)} props to {out_dir} (each read back: Prn, shapes, vertices, shaders, textures, alpha, '
          f'colours match the source; every shape raised by its bottle\'s lift; {uncorked} uncorked)')


if __name__ == '__main__':
    main()
