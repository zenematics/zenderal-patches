"""Minimal reader for Skyrim SE BSA archives (version 105), enough to list and extract files.

Only what the generators here need: folder/file names, and file data (uncompressed or LZ4-frame).
"""
import struct

import lz4.frame

F_DIRNAMES, F_FILENAMES, F_COMPRESSED, F_EMBEDNAME = 0x1, 0x2, 0x4, 0x100


class Bsa:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        magic, ver, off, flags, nfold, nfile, lfold, lfile, _ = struct.unpack_from('<4sIIIIIIIH', d, 0)
        assert magic == b'BSA\x00' and ver == 105, (path, magic, ver)
        self.flags = flags
        folders = []
        p = off
        for _ in range(nfold):
            _, count, _, _ = struct.unpack_from('<QIIQ', d, p)
            folders.append(count)
            p += 24
        entries = []
        for count in folders:
            n = d[p]
            name = d[p + 1:p + n].decode('latin1')        # length includes the null
            p += 1 + n
            for _ in range(count):
                _, size, foff = struct.unpack_from('<QII', d, p)
                entries.append([name, None, size, foff])
                p += 16
        for e in entries:
            end = d.index(b'\0', p)
            e[1] = d[p:end].decode('latin1')
            p = end + 1
        self.files = {f'{folder}\\{name}'.lower(): (size, foff) for folder, name, size, foff in entries}

    def read(self, name):
        size, off = self.files[name.lower().replace('/', '\\')]
        compressed = bool(self.flags & F_COMPRESSED) != bool(size & 0x40000000)
        size &= 0x3FFFFFFF
        p = off
        if self.flags & F_EMBEDNAME:
            n = self.data[p]
            p += 1 + n
            size -= 1 + n
        if compressed:
            raw = struct.unpack_from('<I', self.data, p)[0]
            out = lz4.frame.decompress(self.data[p + 4:p + size])
            assert len(out) == raw, (name, len(out), raw)
            return out
        return self.data[p:p + size]
