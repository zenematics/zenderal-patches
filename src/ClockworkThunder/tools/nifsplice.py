"""Minimal NIF 20.2.0.7 (Skyrim LE, user 12, BS 83) block-level reader/writer, enough to append an
NiTriShape (+ data, shader, texture set) to an existing mesh without touching its other blocks.

Ordo Legionis' musket meshes are LE-format files with transform controllers, behaviour-graph extra
data and collision. PyNifly would drop the controllers, so the file is rebuilt block by block here
and every original block is written back byte for byte (Nif(raw).tobytes() == raw is asserted)."""
import struct


class Nif:
    def __init__(self, data):
        i = data.index(b'\n') + 1
        self.headline = data[:i]
        self.version, self.endian, self.user, nblocks = struct.unpack_from('<IBII', data, i)
        i += 13
        assert self.version == 0x14020007 and self.user == 12, hex(self.version)
        self.bsver = struct.unpack_from('<I', data, i)[0]
        i += 4
        assert self.bsver == 83, self.bsver
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

    def add_string(self, s):
        b = s.encode()
        self.strings.append(b)
        self.maxlen = max(self.maxlen, len(b))
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
        out += struct.pack('<%dH' % len(self.blocks), *self.type_idx)
        out += struct.pack('<%dI' % len(self.blocks), *[len(b) for b in self.blocks])
        out += struct.pack('<II', len(self.strings), self.maxlen)
        for s in self.strings:
            out += struct.pack('<I', len(s)) + s
        out += struct.pack('<I', 0)
        for b in self.blocks:
            out += b
        out += struct.pack('<I', len(self.roots)) + struct.pack('<%di' % len(self.roots), *self.roots)
        return bytes(out)


# ---- layouts (20.2.0.7, BS 83) --------------------------------------------------------------------------

def avobject_fields(b):
    """Offsets of an NiAVObject's fields; returns (offsets, offset just after the collision ref)."""
    o = {'name': 0, 'extra': 4}
    n = struct.unpack_from('<I', b, 4)[0]
    i = 8 + 4 * n
    o['controller'] = i
    o['flags'] = i + 4
    o['translation'] = i + 8
    o['rotation'] = i + 20
    o['scale'] = i + 56
    o['collision'] = i + 60
    return o, i + 64


def trishape_fields(b):
    o, i = avobject_fields(b)
    o['data'] = i
    o['skin'] = i + 4
    i += 8
    nmat = struct.unpack_from('<I', b, i)[0]
    i += 4 + 8 * nmat      # material names (string idx) + extra data (uint)
    i += 4 + 1             # active material, material needs update
    o['shader'] = i
    o['alpha'] = i + 4
    assert i + 8 == len(b), ('NiTriShape layout', i + 8, len(b))
    return o


def node_children(b):
    """(offset of NumChildren, child refs) for an NiNode / BSFadeNode."""
    _, i = avobject_fields(b)
    n = struct.unpack_from('<I', b, i)[0]
    return i, list(struct.unpack_from('<%di' % n, b, i + 4))


def set_children(b, refs):
    i, old = node_children(b)
    tail = bytes(b[i + 4 + 4 * len(old):])
    return bytearray(bytes(b[:i]) + struct.pack('<I', len(refs)) + struct.pack('<%di' % len(refs), *refs) + tail)


def shader_texset_offset(b):
    """BSLightingShaderProperty (BS 83): shader type, name, extra data, controller, flags 1/2,
    UV offset + scale, then the texture set ref."""
    i = 8
    n = struct.unpack_from('<I', b, i)[0]
    return i + 4 + 4 * n + 4 + 8 + 16


def texture_set(paths):
    out = struct.pack('<I', len(paths))
    for p in paths:
        e = p.encode()
        out += struct.pack('<I', len(e)) + e
    return out


def read_texture_set(b):
    n = struct.unpack_from('<I', b, 0)[0]
    i, out = 4, []
    for _ in range(n):
        k = struct.unpack_from('<I', b, i)[0]
        out.append(bytes(b[i + 4:i + 4 + k]).decode())
        i += 4 + k
    return out


def trishape_data(verts, normals, tangents, bitangents, uvs, tris, center, radius):
    """NiTriShapeData payload: vertices, normals + tangents/bitangents, one UV set, triangles."""
    out = bytearray()
    out += struct.pack('<iHBB', 0, len(verts), 0, 0)   # group id, num vertices, keep, compress
    out += b'\x01' + b''.join(struct.pack('<3f', *v) for v in verts)
    out += struct.pack('<H', 1 | 4096)                 # BS vector flags: 1 UV set, has tangents
    out += struct.pack('<I', 0)                        # material CRC (20.2.0.7+)
    out += b'\x01' + b''.join(struct.pack('<3f', *v) for v in normals)
    out += b''.join(struct.pack('<3f', *v) for v in tangents)
    out += b''.join(struct.pack('<3f', *v) for v in bitangents)
    out += struct.pack('<4f', *center, radius)
    out += b'\x00'                                     # no vertex colours
    out += b''.join(struct.pack('<2f', *uv) for uv in uvs)
    out += struct.pack('<H', 0)                        # consistency flags
    out += struct.pack('<i', -1)                       # additional data
    out += struct.pack('<H', len(tris))
    out += struct.pack('<I', 3 * len(tris)) + b'\x01'
    out += b''.join(struct.pack('<3H', *t) for t in tris)
    out += struct.pack('<H', 0)                        # match groups
    return bytes(out)


def read_trishape_data(b):
    """Parse an NiTriShapeData payload written as above (or the original, if it has the same features)."""
    nv = struct.unpack_from('<H', b, 4)[0]
    i = 8
    assert b[i] == 1
    i += 1
    V = [struct.unpack_from('<3f', b, i + 12 * k) for k in range(nv)]
    i += 12 * nv
    flags = struct.unpack_from('<H', b, i)[0]
    i += 2 + 4             # + material CRC
    hasn = b[i]
    i += 1
    N = T = B = None
    if hasn:
        N = [struct.unpack_from('<3f', b, i + 12 * k) for k in range(nv)]
        i += 12 * nv
        if flags & 4096:
            T = [struct.unpack_from('<3f', b, i + 12 * k) for k in range(nv)]
            i += 12 * nv
            B = [struct.unpack_from('<3f', b, i + 12 * k) for k in range(nv)]
            i += 12 * nv
    center = struct.unpack_from('<3f', b, i)
    radius = struct.unpack_from('<f', b, i + 12)[0]
    i += 16
    hasc = b[i]
    i += 1 + (16 * nv if hasc else 0)
    nuv = flags & 63
    UV = [struct.unpack_from('<2f', b, i + 8 * k) for k in range(nv)] if nuv else []
    i += 8 * nv * nuv
    i += 2 + 4
    ntri = struct.unpack_from('<H', b, i)[0]
    i += 2 + 4
    hast = b[i]
    i += 1
    TR = [struct.unpack_from('<3H', b, i + 6 * k) for k in range(ntri)] if hast else []
    i += 6 * ntri if hast else 0
    nmg = struct.unpack_from('<H', b, i)[0]
    i += 2
    for _ in range(nmg):
        c = struct.unpack_from('<H', b, i)[0]
        i += 2 + 2 * c
    assert i == len(b), ('NiTriShapeData layout', i, len(b))
    return dict(verts=V, normals=N, tangents=T, bitangents=B, center=center, radius=radius, uvs=UV,
                tris=TR, flags=flags, has_colors=hasc)


def replace_triangles(b, tris):
    """An NiTriShapeData payload with its triangle list replaced; every byte before it kept."""
    d = read_trishape_data(b)
    nv = len(d['verts'])
    flags = d['flags']
    i = 8 + 1 + 12 * nv + 2 + 4 + 1
    if d['normals'] is not None:
        i += 12 * nv * (3 if flags & 4096 else 1)
    i += 16 + 1 + (16 * nv if d['has_colors'] else 0) + 8 * nv * (flags & 63) + 2 + 4
    assert struct.unpack_from('<H', b, i)[0] == len(d['tris'])
    out = bytes(b[:i]) + struct.pack('<H', len(tris)) + struct.pack('<I', 3 * len(tris)) + b'\x01'
    out += b''.join(struct.pack('<3H', *t) for t in tris) + struct.pack('<H', 0)
    assert read_trishape_data(out)['tris'] == [tuple(t) for t in tris]
    return out
