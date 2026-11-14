"""Minimal Skyrim SE NIF (20.2.0.7, user 12, BS 100) block-level reader/writer.

The SE sibling of src/ClockworkThunder/tools/nifsplice.py (LE only). Enough to append blocks to an existing
mesh without touching its other blocks: every original block is written back byte for byte
(Nif(raw).tobytes() == raw is asserted by the callers), plus a BSTriShape codec for unskinned shapes and
field access for the handful of block types Sting and Rise edit.

Layouts are Skyrim SE's (nif.xml, BS 100), each checked against vanilla blocks by the size asserts below."""
import struct

import numpy as np

VF_VERTEX, VF_UV, VF_UV2, VF_NORMAL, VF_TANGENT, VF_COLORS, VF_SKINNED = (1 << i for i in range(7))


class Nif:
    def __init__(self, data):
        i = data.index(b'\n') + 1
        self.headline = data[:i]
        self.version, self.endian, self.user, nblocks = struct.unpack_from('<IBII', data, i)
        i += 13
        assert self.version == 0x14020007 and self.user == 12, hex(self.version)
        self.bsver = struct.unpack_from('<I', data, i)[0]
        i += 4
        assert self.bsver == 100, self.bsver
        self.export = []
        for _ in range(3):
            n = data[i]
            self.export.append(data[i + 1:i + 1 + n])
            i += 1 + n
        nt = struct.unpack_from('<H', data, i)[0]
        i += 2
        self.types = []
        for _ in range(nt):
            n = struct.unpack_from('<I', data, i)[0]
            self.types.append(data[i + 4:i + 4 + n].decode())
            i += 4 + n
        self.type_idx = list(struct.unpack_from('<%dH' % nblocks, data, i))
        i += 2 * nblocks
        sizes = struct.unpack_from('<%dI' % nblocks, data, i)
        i += 4 * nblocks
        ns, self.maxlen = struct.unpack_from('<II', data, i)
        i += 8
        self.strings = []
        for _ in range(ns):
            n = struct.unpack_from('<I', data, i)[0]
            self.strings.append(data[i + 4:i + 4 + n])
            i += 4 + n
        assert struct.unpack_from('<I', data, i)[0] == 0, 'groups'
        i += 4
        self.blocks = []
        for s in sizes:
            self.blocks.append(bytearray(data[i:i + s]))
            i += s
        nroots = struct.unpack_from('<I', data, i)[0]
        self.roots = list(struct.unpack_from('<%di' % nroots, data, i + 4))
        assert i + 4 + 4 * nroots == len(data), 'trailing bytes'

    def btype(self, k):
        return self.types[self.type_idx[k]]

    def find(self, typename):
        return [k for k in range(len(self.blocks)) if self.btype(k) == typename]

    def string(self, k):
        return None if k < 0 else self.strings[k].decode('latin1')

    def add_string(self, s):
        b = s.encode('latin1')
        if b in self.strings:
            return self.strings.index(b)
        self.strings.append(b)
        return len(self.strings) - 1

    def add_block(self, typename, payload):
        if typename not in self.types:
            self.types.append(typename)
        self.type_idx.append(self.types.index(typename))
        self.blocks.append(bytearray(payload))
        return len(self.blocks) - 1

    def tobytes(self):
        out = bytearray(self.headline)
        out += struct.pack('<IBII', self.version, self.endian, self.user, len(self.blocks))
        out += struct.pack('<I', self.bsver)
        for e in self.export:
            out += bytes([len(e)]) + e
        out += struct.pack('<H', len(self.types))
        for t in self.types:
            out += struct.pack('<I', len(t)) + t.encode()
        out += struct.pack('<%dH' % len(self.type_idx), *self.type_idx)
        out += struct.pack('<%dI' % len(self.blocks), *[len(b) for b in self.blocks])
        out += struct.pack('<II', len(self.strings), max([self.maxlen] + [len(s) for s in self.strings]))
        for s in self.strings:
            out += struct.pack('<I', len(s)) + s
        out += struct.pack('<I', 0)
        for b in self.blocks:
            out += b
        out += struct.pack('<I', len(self.roots)) + struct.pack('<%di' % len(self.roots), *self.roots)
        return bytes(out)


# ---- NiObjectNET / NiAVObject / NiNode -------------------------------------------------------------------

def net_end(b, at=0):
    """Offset just past NiObjectNET (name, extra data list, controller) starting at `at`."""
    n = struct.unpack_from('<I', b, at + 4)[0]
    return at + 8 + 4 * n + 4


def av_fields(b):
    """Offsets of NiAVObject fields (SE: flags uint, no property list)."""
    o = net_end(b)
    return dict(name=0, nextra=4, ctrl=o - 4, flags=o, translation=o + 4, rotation=o + 16, scale=o + 52,
                coll=o + 56, end=o + 60)


def transform(b):
    f = av_fields(b)
    t = np.array(struct.unpack_from('<3f', b, f['translation']))
    R = np.array(struct.unpack_from('<9f', b, f['rotation'])).reshape(3, 3)
    s = struct.unpack_from('<f', b, f['scale'])[0]
    return t, R, s


def set_transform(b, t, R, s=1.0):
    f = av_fields(b)
    b = bytearray(b)
    struct.pack_into('<3f', b, f['translation'], *[float(x) for x in t])
    struct.pack_into('<9f', b, f['rotation'], *[float(x) for x in np.asarray(R).reshape(-1)])
    struct.pack_into('<f', b, f['scale'], float(s))
    return b


def node_children(b):
    o = av_fields(b)['end']
    n = struct.unpack_from('<I', b, o)[0]
    return o, list(struct.unpack_from('<%di' % n, b, o + 4))


def set_children(b, refs):
    o, old = node_children(b)
    tail = b[o + 4 + 4 * len(old):]
    return bytearray(b[:o]) + struct.pack('<I', len(refs)) + struct.pack('<%di' % len(refs), *refs) + tail


# ---- BSTriShape ------------------------------------------------------------------------------------------

def _layout(desc):
    return desc >> 44, (lambda k: ((desc >> (4 * k)) & 0xF) * 4), (desc & 0xF) * 4


def _ub(v):
    return np.clip(np.round((np.asarray(v, float) + 1.0) * 0.5 * 255.0), 0, 255).astype(np.uint8)


def _fb(u):
    return np.asarray(u, np.float64) / 255.0 * 2.0 - 1.0


def read_trishape(b):
    """Unskinned SE BSTriShape -> dict(fields offsets, refs, desc, arrays)."""
    f = av_fields(b)
    o = f['end']
    out = dict(av=f, bound_at=o, skin=struct.unpack_from('<i', b, o + 16)[0],
               shader=struct.unpack_from('<i', b, o + 20)[0], alpha=struct.unpack_from('<i', b, o + 24)[0],
               shader_at=o + 20, alpha_at=o + 24)
    desc = struct.unpack_from('<Q', b, o + 28)[0]
    ntri, nvert, dsize = struct.unpack_from('<HHI', b, o + 36)
    out.update(desc=desc, ntri=ntri, nvert=nvert)
    flags, off, vs = _layout(desc)
    assert out['skin'] == -1 and not flags & VF_SKINNED, 'skinned shapes unsupported'
    assert dsize == nvert * vs + ntri * 6, (dsize, nvert, vs, ntri)
    p = o + 44
    buf = np.frombuffer(bytes(b[p:p + nvert * vs]), np.uint8).reshape(nvert, vs)
    out['pos'] = buf[:, 0:12].copy().view('<f4').reshape(nvert, 3).astype(np.float64)
    out['w'] = buf[:, 12:16].copy().view('<f4').reshape(nvert).astype(np.float64)
    if flags & VF_UV:
        out['uv'] = buf[:, off(2):off(2) + 4].copy().view('<f2').reshape(nvert, 2).astype(np.float64)
    if flags & VF_NORMAL:
        out['normal'] = _fb(buf[:, off(4):off(4) + 3])
        out['bity'] = _fb(buf[:, off(4) + 3])
    if flags & VF_NORMAL and flags & VF_TANGENT:
        out['tangent'] = _fb(buf[:, off(5):off(5) + 3])
        out['bitz'] = _fb(buf[:, off(5) + 3])
        out['bitangent'] = np.stack([out['w'], out['bity'], out['bitz']], 1)
    if flags & VF_COLORS:
        out['color'] = buf[:, off(6):off(6) + 4].copy()
    p += nvert * vs
    out['tris'] = np.frombuffer(bytes(b[p:p + ntri * 6]), '<u2').reshape(ntri, 3).astype(np.int64)
    p += ntri * 6
    assert struct.unpack_from('<I', b, p)[0] == 0 and p + 4 == len(b), 'particle data / trailing bytes'
    return out


def write_trishape(name_idx, av_flags, xf, desc, pos, uv, normal, tangent, bitangent, color, tris, shader, alpha):
    """A new unskinned BSTriShape: NiAVObject (name, no extra data, no controller, `av_flags`, transform
    xf = (translation, rotation, scale), no collision), then geometry, shader and alpha refs."""
    t, R, s = xf
    head = struct.pack('<iIiI', name_idx, 0, -1, av_flags) + struct.pack('<3f', *[float(x) for x in t])
    head += struct.pack('<9f', *[float(x) for x in np.asarray(R).reshape(-1)]) + struct.pack('<fi', float(s), -1)
    flags, off, vs = _layout(desc)
    n = len(pos)
    assert n < 65536 and len(tris) < 65536
    need = VF_VERTEX | VF_UV | VF_NORMAL | VF_TANGENT
    assert flags & need == need and not flags & (VF_UV2 | VF_SKINNED), hex(flags)
    buf = np.zeros((n, vs), np.uint8)
    buf[:, 0:12] = np.asarray(pos, '<f4').view(np.uint8).reshape(n, 12)
    buf[:, 12:16] = np.asarray(bitangent[:, 0], '<f4').view(np.uint8).reshape(n, 4)
    buf[:, off(2):off(2) + 4] = np.asarray(uv, '<f2').view(np.uint8).reshape(n, 4)
    buf[:, off(4):off(4) + 3] = _ub(normal)
    buf[:, off(4) + 3] = _ub(bitangent[:, 1])
    buf[:, off(5):off(5) + 3] = _ub(tangent)
    buf[:, off(5) + 3] = _ub(bitangent[:, 2])
    if flags & VF_COLORS:
        buf[:, off(6):off(6) + 4] = np.asarray(color, np.uint8)
    pos = np.asarray(pos, float)
    centre = (pos.min(0) + pos.max(0)) / 2
    radius = float(np.linalg.norm(pos - centre, axis=1).max())
    out = head + struct.pack('<4f', *centre, radius) + struct.pack('<3i', -1, shader, alpha)
    out += struct.pack('<QHHI', desc, len(tris), n, n * vs + len(tris) * 6)
    out += buf.tobytes() + np.asarray(tris, '<u2').tobytes() + struct.pack('<I', 0)
    return bytes(out)


# ---- copying a lighting shader (with its controllers) between files -------------------------------------

LSP_CTRL, LSP_TEXSET = 12, 40     # BSLightingShaderProperty, no extra data: controller ref, texture-set ref


def set_triangles(b, tris):
    """An unskinned SE BSTriShape with its triangle list replaced (vertices, bound and every other field kept)."""
    o = av_fields(b)['end']
    desc = struct.unpack_from('<Q', b, o + 28)[0]
    ntri, nvert, dsize = struct.unpack_from('<HHI', b, o + 36)
    _, _, vs = _layout(desc)
    assert dsize == nvert * vs + ntri * 6
    p = o + 44 + nvert * vs
    tris = np.asarray(tris, '<u2')
    assert tris.max() < nvert and len(tris) < 65536
    head = bytearray(b[:o + 36]) + struct.pack('<HHI', len(tris), nvert, nvert * vs + len(tris) * 6)
    return head + bytes(b[o + 44:p]) + tris.tobytes() + bytes(b[p + ntri * 6:])


def texture_paths(b):
    """BSShaderTextureSet -> its texture paths (int count, then SizedStrings)."""
    n = struct.unpack_from('<i', b, 0)[0]
    o, out = 4, []
    for _ in range(n):
        size = struct.unpack_from('<I', b, o)[0]
        out.append(bytes(b[o + 4:o + 4 + size]).decode('latin1'))
        o += 4 + size
    assert o == len(b), 'not a BSShaderTextureSet'
    return out


def texture_set(paths):
    out = bytearray(struct.pack('<i', len(paths)))
    for p in paths:
        e = p.encode('latin1')
        out += struct.pack('<I', len(e)) + e
    return out


def copy_lighting_shader(dst, src, shader_i):
    """Copy a BSLightingShaderProperty, its texture set and its float-controller chain (controllers,
    interpolators, key data) from `src` into `dst`. Returns the new shader index. Every copied block is
    byte-identical except its block refs, which are remapped."""
    b = src.blocks[shader_i]
    assert src.btype(shader_i) == 'BSLightingShaderProperty'
    assert struct.unpack_from('<i', b, 4)[0] == -1 and struct.unpack_from('<I', b, 8)[0] == 0, 'named / extra data'
    chain = [shader_i, struct.unpack_from('<i', b, LSP_TEXSET)[0]]
    c = struct.unpack_from('<i', b, LSP_CTRL)[0]
    while c >= 0:
        assert src.btype(c) == 'BSLightingShaderPropertyFloatController', src.btype(c)
        cb = src.blocks[c]
        assert len(cb) == 34
        interp = struct.unpack_from('<i', cb, 26)[0]
        assert src.btype(interp) == 'NiFloatInterpolator' and len(src.blocks[interp]) == 8
        data = struct.unpack_from('<i', src.blocks[interp], 4)[0]
        chain += [c, interp] + ([data] if data >= 0 else [])
        if data >= 0:
            assert src.btype(data) == 'NiFloatData'
        c = struct.unpack_from('<i', cb, 0)[0]
    new = {}
    for k in chain:
        new[k] = dst.add_block(src.btype(k), src.blocks[k])

    def remap(i, at):
        old = struct.unpack_from('<i', dst.blocks[i], at)[0]
        if old >= 0:
            struct.pack_into('<i', dst.blocks[i], at, new[old])

    for k in chain:
        t, i = src.btype(k), new[k]
        if t == 'BSLightingShaderProperty':
            remap(i, LSP_CTRL)
            remap(i, LSP_TEXSET)
        elif t == 'BSLightingShaderPropertyFloatController':
            remap(i, 0)       # next controller
            remap(i, 22)      # target
            remap(i, 26)      # interpolator
        elif t == 'NiFloatInterpolator':
            remap(i, 4)
    return new[shader_i]


# ---- particle blocks (Skyrim SE layouts; offsets checked by block size) ---------------------------------

MOD_BASE = 13      # NiPSysModifier: name, order, target, active


def box_emitter(b):
    assert len(b) == 85
    v = struct.unpack_from('<6f4f4fi3f', b, MOD_BASE)
    return dict(speed=v[0], speedvar=v[1], decl=v[2], declvar=v[3], planar=v[4], planarvar=v[5],
                color=v[6:10], radius=v[10], radiusvar=v[11], life=v[12], lifevar=v[13], obj=v[14], whd=v[15:18])


def set_box_emitter(b, e):
    b = bytearray(b)
    struct.pack_into('<6f4f4fi3f', b, MOD_BASE, e['speed'], e['speedvar'], e['decl'], e['declvar'], e['planar'],
                     e['planarvar'], *e['color'], e['radius'], e['radiusvar'], e['life'], e['lifevar'], e['obj'],
                     *e['whd'])
    return b


def set_spawn_life(b, life, lifevar):
    assert len(b) == 39
    b = bytearray(b)
    struct.pack_into('<2f', b, MOD_BASE + 2 + 4 + 2 + 2 + 4 + 4, life, lifevar)
    return b


def simple_color_values(b):
    assert len(b) == 85
    return bytes(b[MOD_BASE:])


def set_simple_color_values(b, values):
    assert len(b) == 85 and len(values) == 72
    return bytearray(b[:MOD_BASE]) + values


def scale_values(b):
    n = struct.unpack_from('<I', b, MOD_BASE)[0]
    assert len(b) == MOD_BASE + 4 + 4 * n
    return list(struct.unpack_from('<%df' % n, b, MOD_BASE + 4))


def set_scale_values(b, vals):
    return bytearray(b[:MOD_BASE]) + struct.pack('<I', len(vals)) + struct.pack('<%df' % len(vals), *vals)


def set_rotation_speed(b, speed, var):
    assert len(b) == 43
    b = bytearray(b)
    struct.pack_into('<4f', b, MOD_BASE, speed, var, 0.0, 0.0)
    return b


def set_gravity(b, axis, strength, world):
    assert len(b) == 50
    b = bytearray(b)
    struct.pack_into('<3f2f', b, MOD_BASE + 4, *axis, 0.0, strength)       # axis, decay, strength
    struct.pack_into('<I2fB', b, MOD_BASE + 24, 1, 0.0, 1.0, world)          # planar, no turbulence, aligned
    return b


def particle_system_fields(b):
    """NiParticleSystem (SE): NiAVObject, bound, skin, shader, alpha, vertex desc, far/near LOD, data ref,
    world space, modifiers."""
    o = av_fields(b)['end']
    shader, alpha = struct.unpack_from('<2i', b, o + 20)
    data = struct.unpack_from('<i', b, o + 44)[0]
    nm = struct.unpack_from('<I', b, o + 49)[0]
    mods = list(struct.unpack_from('<%di' % nm, b, o + 53))
    assert o + 53 + 4 * nm == len(b), 'NiParticleSystem layout'
    return dict(shader=shader, alpha=alpha, data=data, world=b[o + 48], mods=mods)
