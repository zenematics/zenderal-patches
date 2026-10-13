"""Minimal reader for Skyrim SE NIFs (20.2.0.7, user 12, BS 100), just enough to edit skinned
BSTriShape vertex POSITIONS in place.

Only fixed-size fields are ever rewritten, so a file keeps its exact length and every other byte.
Unknown block types are skipped via the header's block-size table.
"""
import struct

import numpy as np

# Vertex-desc attribute flags (bits 44+ of the 64-bit vertex descriptor). Attribute offsets are
# nibbles: 0 vertex size, 1 dynamic, 2 UV1, 3 UV2, 4 normal, 5 tangent, 6 color, 7 skinning.
VF_VERTEX, VF_UV, VF_UV2, VF_NORMAL, VF_TANGENT, VF_COLORS, VF_SKINNED = (1 << i for i in range(7))
VF_FULLPREC = 1 << 10


class Reader:
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos

    def take(self, fmt):
        v = struct.unpack_from('<' + fmt, self.d, self.p)
        self.p += struct.calcsize('<' + fmt)
        return v if len(v) > 1 else v[0]

    def skip(self, n):
        self.p += n


class Nif:
    def __init__(self, path):
        self.path = path
        self.data = bytearray(open(path, 'rb').read())
        r = Reader(self.data)
        nl = self.data.index(b'\n')
        r.p = nl + 1
        ver = r.take('I')
        assert ver == 0x14020007, hex(ver)
        r.skip(1)                                   # endian
        assert r.take('I') == 12                    # user version
        nblocks = r.take('I')
        bsver = r.take('I')
        assert bsver == 100, bsver                  # SSE only
        for _ in range(3):                          # author / process / export short strings
            r.skip(r.take('B'))
        ntypes = r.take('H')
        types = []
        for _ in range(ntypes):
            n = r.take('I')
            types.append(bytes(self.data[r.p:r.p + n]).decode('latin1'))
            r.skip(n)
        tidx = [r.take('H') for _ in range(nblocks)]
        sizes = [r.take('I') for _ in range(nblocks)]
        nstr = r.take('I')
        r.skip(4)                                   # max string length
        self.strings = []
        for _ in range(nstr):
            n = r.take('I')
            self.strings.append(bytes(self.data[r.p:r.p + n]).decode('latin1'))
            r.skip(n)
        ngroups = r.take('I')
        r.skip(4 * ngroups)
        self.blocks = []
        p = r.p
        for i in range(nblocks):
            self.blocks.append((types[tidx[i] & 0x7FFF], p, sizes[i]))
            p += sizes[i]
        assert p == len(self.data) - 8 or p <= len(self.data), (p, len(self.data))

    def string(self, idx):
        return None if idx < 0 else self.strings[idx]

    # --- NiAVObject prefix shared by NiNode and BSTriShape ------------------------------------
    def _avobject(self, r):
        name = self.string(r.take('i'))
        r.skip(4 * r.take('I'))                     # extra data refs
        r.skip(4)                                   # controller
        r.skip(4)                                   # flags (bsver > 26)
        t = np.array(r.take('3f'))
        R = np.array(r.take('9f')).reshape(3, 3)
        s = r.take('f')
        r.skip(4)                                   # collision
        return name, t, R, s

    def nodes(self):
        out = {}
        for i, (typ, p, _) in enumerate(self.blocks):
            if typ in ('NiNode', 'BSFadeNode', 'BSLeafAnimNode', 'NiSwitchNode'):
                name, t, R, s = self._avobject(Reader(self.data, p))
                out[i] = dict(name=name, t=t, R=R, s=s)
        return out

    def shapes(self):
        """Every BSTriShape, with its skin and (for SSE skinned shapes) its global vertex buffer."""
        out = []
        for i, (typ, p, _) in enumerate(self.blocks):
            if typ != 'BSTriShape':
                continue
            r = Reader(self.data, p)
            name, t, R, s = self._avobject(r)
            r.skip(16)                              # bounding sphere
            skin, shader, alpha = r.take('3i')
            desc = r.take('Q')
            ntri, nvert = r.take('HH')
            dsize = r.take('I')
            sh = dict(block=i, name=name, t=t, R=R, s=s, skin=skin, shader=shader, desc=desc,
                      ntri=ntri, nvert=nvert, dsize=dsize, vdata=None, tris=None)
            if dsize:
                sh['vdata'] = r.p
                sh['vsize'] = (desc & 0xF) * 4
                r.skip(nvert * sh['vsize'])
                sh['tris'] = np.frombuffer(bytes(self.data[r.p:r.p + ntri * 6]), '<u2').reshape(-1, 3)
                r.skip(ntri * 6)
            if skin >= 0:
                self._skin(sh)
            out.append(sh)
        return out

    def _skin(self, sh):
        typ, p, _ = self.blocks[sh['skin']]
        assert typ in ('NiSkinInstance', 'BSDismemberSkinInstance'), typ
        r = Reader(self.data, p)
        data_ref, part_ref, root = r.take('3i')
        nb = r.take('I')
        sh['bones'] = [r.take('i') for _ in range(nb)]
        # NiSkinData: skin transform + per-bone bind transforms
        r = Reader(self.data, self.blocks[data_ref][1])
        R = np.array(r.take('9f')).reshape(3, 3); t = np.array(r.take('3f')); s = r.take('f')
        sh['skinT'] = (R, t, s)
        nb2 = r.take('I'); hasw = r.take('B')
        bt = []
        for _ in range(nb2):
            bR = np.array(r.take('9f')).reshape(3, 3); btt = np.array(r.take('3f')); bs = r.take('f')
            r.skip(16)
            nv = r.take('H')
            if hasw:
                r.skip(nv * 6)
            bt.append((bR, btt, bs))
        sh['boneT'] = bt
        # NiSkinPartition (SSE): global vertex buffer lives here when the shape has none.
        if part_ref >= 0 and not sh['dsize']:
            r = Reader(self.data, self.blocks[part_ref][1])
            nparts = r.take('I')
            dsize, vsize = r.take('II')
            desc = r.take('Q')
            sh['desc'] = desc
            sh['vsize'] = vsize
            sh['vdata'] = r.p
            # SSE writes num_vertices = 0 on a shape whose buffer lives in the partition.
            assert dsize % vsize == 0 and sh['nvert'] in (0, dsize // vsize), (dsize, vsize, sh['nvert'])
            sh['nvert'] = dsize // vsize
            sh['part'] = part_ref
            r.skip(dsize)
            sh['tris'] = self._partition_tris(r, nparts)

    def _partition_tris(self, r, nparts):
        """Global triangle list of an SSE NiSkinPartition (SSE indexes the global buffer directly)."""
        tris = []
        for _ in range(nparts):
            nv, ntri, nb, nstrips, nwpv = r.take('5H')
            r.skip(2 * nb)                          # bones
            has_map = r.take('B')
            vmap = np.frombuffer(bytes(self.data[r.p:r.p + 2 * nv]), '<u2') if has_map else None
            if has_map:
                r.skip(2 * nv)
            if r.take('B'):
                r.skip(4 * nv * nwpv)               # vertex weights
            strip_lens = [r.take('H') for _ in range(nstrips)]
            has_faces = r.take('B')
            assert nstrips == 0, 'strips unsupported'
            if has_faces:
                t = np.frombuffer(bytes(self.data[r.p:r.p + 6 * ntri]), '<u2').reshape(-1, 3)
                r.skip(6 * ntri)
                tris.append(t)                      # SSE global VB: already shape indices
            if r.take('B'):
                r.skip(nv * nwpv)                   # bone indices
            r.skip(2)                               # LOD level + global vb flag
            r.skip(8)                               # vertex desc
            r.skip(6 * ntri)                        # triangles copy
        return np.concatenate(tris) if tris else None

    # --- vertex attribute access --------------------------------------------------------------
    @staticmethod
    def _layout(desc):
        flags = desc >> 44
        off = lambda k: ((desc >> (4 * k)) & 0xF) * 4
        return flags, off

    def positions(self, sh):
        flags, off = self._layout(sh['desc'])
        base, vs, n = sh['vdata'], sh['vsize'], sh['nvert']
        buf = np.frombuffer(bytes(self.data[base:base + vs * n]), np.uint8).reshape(n, vs)
        # Skyrim SE always stores full-precision positions; VF_FULLPREC is a Fallout 4 flag.
        return buf[:, 0:12].copy().view('<f4').reshape(n, 3).astype(np.float64)

    def normals(self, sh):
        flags, off = self._layout(sh['desc'])
        assert flags & VF_NORMAL
        o = off(4)
        base, vs, n = sh['vdata'], sh['vsize'], sh['nvert']
        buf = np.frombuffer(bytes(self.data[base:base + vs * n]), np.uint8).reshape(n, vs)
        return buf[:, o:o + 3].astype(np.float64) / 255.0 * 2.0 - 1.0

    def skin_info(self, sh):
        """Per-vertex (weights[4], bone indices[4]) from the vertex buffer."""
        flags, off = self._layout(sh['desc'])
        assert flags & VF_SKINNED
        o = off(7)
        base, vs, n = sh['vdata'], sh['vsize'], sh['nvert']
        buf = np.frombuffer(bytes(self.data[base:base + vs * n]), np.uint8).reshape(n, vs)
        w = buf[:, o:o + 8].copy().view('<f2').astype(np.float64)
        idx = buf[:, o + 8:o + 12].astype(int)
        return w, idx

    def set_positions(self, sh, pos):
        flags, _ = self._layout(sh['desc'])
        base, vs = sh['vdata'], sh['vsize']
        for i, v in enumerate(pos):
            struct.pack_into('<3f', self.data, base + i * vs, *v)

    def save(self, path):
        open(path, 'wb').write(self.data)
