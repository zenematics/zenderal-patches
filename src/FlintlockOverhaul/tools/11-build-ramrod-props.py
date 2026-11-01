"""Build the ball and ramrod props of `Zenderal - Musket Ramrod Reload`: their meshes and the ANIO records the clips
ask for (`AnimObjLoad.<EditorID>` / `AnimObjDraw.<EditorID>`, unloaded by `AnimObjectUnequip`; tools/09 writes them).

The pattern is the list's own: Eating Animations and Sounds (TaberuAnimation.esp) and JellyFish Animated Potions put
props in hands with exactly these annotations, and both 1hm_behavior graphs (first and third person) list the three
events, so no behavior patch is needed. A prop mesh names its attach bone in an `NiStringExtraData` "Prn" on its
root; both props hang on `AnimObjectL`, whose track tools/09 animates (the pinch for the ball, the rod line for the
ramrod), so the meshes sit at their origin:
  - ball: a dark steel sphere of BALL_RADIUS shaded like the vanilla steel dagger's blade (BALL_SOURCE, BALL_UV)
    with the BALL_CUBEMAP reflection;
  - ramrod, one per musket (ROD_EDID % label): a rod up +Y from its top end at 0 to -(muzzle - ROD_SHORT), with a
    wider ramming head at the far end, shaded like that musket's barrel (its shader, one texel near the muzzle).
Textures are referenced, not copied: Ordo must stay installed (the muskets need it anyway).

Records: `ZEN_RamrodBall` 0x800, the rods 0x801 up in label order; plugin `Zenderal - Musket Ramrod Reload.esp`, ESL,
HEDR 1.7, YAML in src/FlintlockOverhaul/RamrodReloadESP (generated, never hand-edited), built with the pinned
Spriggit CLI into the MO2 mod. Not in build/manifest.json: the mod ships nothing until Zodd agrees (tools/09).

Run order: 06 -> 09 -> 10 -> 11 (09 rebuilds the mod folder).
Usage:  python src/FlintlockOverhaul/tools/11-build-ramrod-props.py [<modlist root>]   (needs numpy)
"""
import glob
import importlib.util
import math
import os
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R3P = _load('ramrod3p', os.path.join(HERE, '09-build-ramrod-reload.py'))
ADS = R3P.ADS
sys.path.insert(0, ADS.TOOLS['pynifly'])
from pyn.pynifly import NifFile, NiStringExtraData, nifly  # noqa: E402
from pyn.nifdefs import BSTriShapeBuf, PynBufferTypes  # noqa: E402

OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'RamrodReloadESP')
MESH_DIR = 'Zenderal\\MusketRamrod'
# Dark metal (curator, 2026-11-01): the vanilla steel dagger's blade shader (environment map, its _m reflection mask).
# Ordo's flying ball had the same shader flags but no cubemap or mask: never showed in game. The first build sampled
# the blade's polished edge (diffuse 231 grey, mask 206) under ShinyBright_e and read white in game.
BALL_SOURCE = ('meshes\\weapons\\steel\\steeldagger.nif', 'SteelDagger:0')
BALL_CUBEMAP = 'textures\\cubemaps\\ShinyDull_e.dds'   # the blade's own
BALL_UV = (0.6084, 0.8955)   # every ball vertex: the blade's flat, its most uniform 5x5 patch of diffuse 55-80 and mask
                             # 90-130 (diffuse 63/64/63, SteelDagger_m.dds 105/255; Textures8.bsa's copies win)
BALL_RADIUS = R3P.BALL_RADIUS   # tools/09 places the ball one radius out from the fingertips
ROD_RADIUS = 0.3
HEAD_RADIUS = 0.42         # the ramming head ...
HEAD_LENGTH = 1.5          # ... this long at the rod's far end
SEGMENTS = 12
CRLF = '\r\n'
SLSF1_SKINNED, SLSF1_ENVMAP, SLSF1_MSN = 0x2, 0x80, 0x1000
SLSF2_VERTEX_COLORS = 0x20
SHADER_DEFAULT, SHADER_ENVMAP = 0, 1


def root_frame(shape):
    v = np.array(shape.verts, dtype=float)
    node = shape
    while node is not None:
        t = node.transform
        v = v @ np.array(t.rotation, dtype=float).T * t.scale + np.array(t.translation, dtype=float)
        node = node.parent
    return v


def lathe(profile, seg):
    """Surface of revolution around +Y with flat end caps. profile: [(y, radius)] from one end to the other."""
    verts, normals, tris = [], [], []
    ring = [(math.cos(2 * math.pi * k / seg), math.sin(2 * math.pi * k / seg)) for k in range(seg)]
    starts = []
    for y, r in profile:
        starts.append(len(verts))
        for cs, sn in ring:
            verts.append((r * cs, y, r * sn))
            normals.append((cs, 0.0, sn))
    for a, b in zip(starts, starts[1:]):
        for k in range(seg):
            k2 = (k + 1) % seg
            tris += [(a + k, b + k, b + k2), (a + k, b + k2, a + k2)]
    for (y, r), sign in ((profile[0], 1.0 if profile[0][0] > profile[-1][0] else -1.0),
                         (profile[-1], 1.0 if profile[-1][0] > profile[0][0] else -1.0)):
        c = len(verts)
        verts.append((0.0, y, 0.0))
        normals.append((0.0, sign, 0.0))
        rim = len(verts)
        for cs, sn in ring:
            verts.append((r * cs, y, r * sn))
            normals.append((0.0, sign, 0.0))
        for k in range(seg):
            tris.append((c, rim + k, rim + (k + 1) % seg))
    return orient(np.array(verts), np.array(normals), tris)


def sphere(r, seg, rings):
    verts, normals, tris = [(0.0, 0.0, r)], [(0.0, 0.0, 1.0)], []
    for i in range(1, rings):
        ph = math.pi * i / rings
        for k in range(seg):
            th = 2 * math.pi * k / seg
            n = (math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))
            verts.append(tuple(r * x for x in n))
            normals.append(n)
    verts.append((0.0, 0.0, -r))
    normals.append((0.0, 0.0, -1.0))
    last = len(verts) - 1
    for k in range(seg):
        tris.append((0, 1 + k, 1 + (k + 1) % seg))
        tris.append((last, 1 + (rings - 2) * seg + (k + 1) % seg, 1 + (rings - 2) * seg + k))
    for i in range(rings - 2):
        a, b = 1 + i * seg, 1 + (i + 1) * seg
        for k in range(seg):
            k2 = (k + 1) % seg
            tris += [(a + k, b + k, b + k2), (a + k, b + k2, a + k2)]
    return orient(np.array(verts), np.array(normals), tris)


def orient(verts, normals, tris):
    """Wind every triangle so its face normal agrees with its vertex normals (outward)."""
    out = []
    for t in tris:
        a, b, c = verts[list(t)]
        if np.cross(b - a, c - a) @ normals[list(t)].sum(0) < 0:
            t = (t[0], t[2], t[1])
        out.append(tuple(int(x) for x in t))
    return verts, normals, out


def write_prop(path, name, verts, normals, tris, uv, src_nif, src_shape, cubemap=None):
    """One-shape prop on a BSFadeNode named `name`, hung on AnimObjectL, shaded like src_shape with every UV on `uv`
    (and `cubemap` in its environment-map slot, if given)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dst = NifFile()
    dst.initialize('SKYRIMSE', path, 'BSFadeNode', name)
    props = BSTriShapeBuf()
    props.bufType = PynBufferTypes.BSTriShapeBufType
    o = dst.createShapeFromData(name + ':0', [tuple(map(float, v)) for v in verts], tris,
                                [tuple(map(float, uv))] * len(verts), [tuple(map(float, n)) for n in normals], props=props)
    src_shape.shader.properties.copyto(o.shader.properties)
    o.shader.properties.bufType = PynBufferTypes.BSLightingShaderPropertyBufType
    o.shader.properties.Shader_Flags_1 &= ~(SLSF1_SKINNED | SLSF1_MSN)
    o.shader.properties.Shader_Flags_2 &= ~SLSF2_VERTEX_COLORS
    textures = [src_shape.shader._readtexture(src_nif._handle, src_shape._handle, i + 1) for i in range(9)]
    if cubemap:
        textures[4] = cubemap
    if o.shader.properties.Shader_Type == SHADER_ENVMAP and not textures[4]:
        # an environment-map shader without a cubemap (Ordo's flying ball) may not render: plain lighting instead
        o.shader.properties.Shader_Type = SHADER_DEFAULT
        o.shader.properties.Shader_Flags_1 &= ~SLSF1_ENVMAP
    o.save_shader_attributes()
    for i, tex in enumerate(textures):
        nifly.setShaderTextureSlot(dst._handle, o._handle, i, tex.encode('utf-8'))
    NiStringExtraData.New(dst, name='Prn', string_value='AnimObjectL', parent=dst.rootNode)
    dst.save()
    back = NifFile(path)
    prn = [e.string_data for e in back.rootNode.extra_data() if e.blockname == 'NiStringExtraData' and e.name == 'Prn']
    if prn != ['AnimObjectL'] or len(back.shapes) != 1 or len(back.shapes[0].verts) != len(verts):
        sys.exit('%s did not read back as written (Prn %s)' % (path, prn))


def barrel_shape(nif):
    """(shape, a UV near its muzzle end): the unskinned shape reaching furthest forward (+Y) is the barrel."""
    best = None
    for s in nif.shapes:
        if s.has_skin_instance:
            continue
        v = root_frame(s)
        if best is None or v[:, 1].max() > best[1][:, 1].max():
            best = (s, v)
    s, v = best
    near = v[:, 1] > v[:, 1].max() - 5.0
    return s, np.median(np.array(s.uvs, dtype=float)[near], axis=0)


def yaml_record(edid, local_id, mesh):
    return CRLF.join(['FormKey: %06X:%s' % (local_id, R3P.PROP_PLUGIN), 'EditorID: ' + edid, 'Model:',
                      '  File: ' + mesh, 'UnloadEvent: ' + R3P.UNEQUIP, ''])


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    _, mods = ADS.QRS.profile_mods(root)
    out_mod = os.path.join(mods_dir, R3P.MOD)
    if not os.path.isdir(os.path.join(out_mod, *R3P.OAR)):
        sys.exit('run tools/09 first: %s has no clips' % out_mod)
    meshes = os.path.join(out_mod, 'meshes', *MESH_DIR.split('\\'))
    records = []

    ball_path = os.path.join(os.environ.get('TEMP', '.'), '_ramrod_ball_source.nif')
    for bsa_path in sorted(glob.glob(os.path.join(root, 'Stock Game', 'Data', '*.bsa'))):
        data, listing = ADS._bsa.listing(bsa_path)
        if BALL_SOURCE[0] in listing:
            with open(ball_path, 'wb') as fh:
                fh.write(ADS._bsa.read(data, listing[BALL_SOURCE[0]]))
            break
    else:
        sys.exit('%s is in no archive under Stock Game/Data' % BALL_SOURCE[0])
    ball_nif = NifFile(ball_path)
    ball_src = [s for s in ball_nif.shapes if s.name == BALL_SOURCE[1]]
    if len(ball_src) != 1:
        sys.exit('%s has no shape %s' % (BALL_SOURCE[0], BALL_SOURCE[1]))
    uv = np.array(BALL_UV)
    v, n, t = sphere(BALL_RADIUS, SEGMENTS, 8)
    write_prop(os.path.join(meshes, 'ZenRamrodBall.nif'), 'ZenRamrodBall', v, n, t, uv, ball_nif, ball_src[0], BALL_CUBEMAP)
    records.append((R3P.BALL_EDID, 0x800, MESH_DIR + '\\ZenRamrodBall.nif'))
    print('ball: radius %.2f, %d triangles, shaded like %s (uv %.3f, %.3f) with %s'
          % (BALL_RADIUS, len(t), BALL_SOURCE[1], uv[0], uv[1], BALL_CUBEMAP))

    for i, (mesh_rel, weapons) in enumerate(sorted(ADS.muskets().items())):
        label = os.path.basename(mesh_rel).replace('_animated.nif', '')
        _, path = ADS.winning_loose(mods_dir, mods, mesh_rel)
        ymuz, _ = R3P.muzzle(ADS.mesh_surface(path))
        length = ymuz - R3P.ROD_SHORT
        nif = NifFile(path)
        src, uv = barrel_shape(nif)
        v, n, t = lathe([(0.0, ROD_RADIUS), (-(length - HEAD_LENGTH - 0.3), ROD_RADIUS),
                         (-(length - HEAD_LENGTH), HEAD_RADIUS), (-length, HEAD_RADIUS)], SEGMENTS)
        rel = '%s\\ZenRamrod_%s.nif' % (MESH_DIR, label)
        write_prop(os.path.join(out_mod, 'meshes', *rel.split('\\')), 'ZenRamrod_' + label, v, n, t, uv, nif, src)
        records.append((R3P.ROD_EDID % label, 0x801 + i, rel))
        print('%-24s rod %.1f units, shaded like %s (uv %.3f, %.3f)' % (label, length, src.name, uv[0], uv[1]))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'AnimatedObjects'))
    with open(os.path.join(OUT, 'RecordData.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(CRLF.join([
            'SpriggitSource:', '  PackageName: Spriggit.Yaml.Skyrim', '  Version: 0.40', 'ModKey: ' + R3P.PROP_PLUGIN,
            'GameRelease: EnderalSE', 'ModHeader:', '  Flags:', '  - Small', '  Stats:', '    Version: 1.7',
            '  Author: Zenderal',
            "  Description: Ball and ramrod props for Zodd's ramrod reload on Ordo Legionis' muskets (Zenderal).",
            '  MasterReferences:', '  - Master: Skyrim.esm', '    FileSize: 0', '  - Master: Update.esm',
            '    FileSize: 0', '  - Master: Enderal - Forgotten Stories.esm', '    FileSize: 0', '  INTV: 1', '']))
    with open(os.path.join(OUT, 'spriggit-meta.json'), 'w', encoding='utf-8', newline='') as fh:
        fh.write('{' + CRLF + '  "PackageName": "Spriggit.Yaml.Skyrim",' + CRLF + '  "Version": "0.40.0",' + CRLF +
                 '  "Release": "EnderalSE",' + CRLF + '  "ModKey": "' + R3P.PROP_PLUGIN + '"' + CRLF + '}')
    for edid, local_id, mesh in records:
        with open(os.path.join(OUT, 'AnimatedObjects', '%s - %06X_%s.yaml' % (edid, local_id, R3P.PROP_PLUGIN)),
                  'w', encoding='utf-8', newline='') as fh:
            fh.write(yaml_record(edid, local_id, mesh))
    esp = os.path.join(out_mod, R3P.PROP_PLUGIN)
    run = subprocess.run([ADS.TOOLS['spriggitCli'], 'deserialize', '--InputPath', OUT, '--OutputPath', esp],
                         capture_output=True, text=True)
    if run.returncode != 0 or not os.path.isfile(esp):
        sys.exit('Spriggit deserialize failed:\n%s\n%s' % (run.stdout, run.stderr))
    data = open(esp, 'rb').read()
    found = [e for e, _, _ in records if e.encode() + b'\0' in data]
    if len(found) != len(records) or data.count(b'ANIO') < len(records):
        sys.exit('%s: expected %d ANIO records, found %d EditorIDs' % (esp, len(records), len(found)))
    print('built %s: %d ANIO records (0x800-0x%03X), %d meshes' % (esp, len(records), 0x800 + len(records) - 1,
                                                                   len(records)))


if __name__ == '__main__':
    main()
