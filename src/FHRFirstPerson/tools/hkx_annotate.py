"""Add annotations to a Skyrim SE animation packfile (hk_2010.2.0-r1, 64-bit) without touching anything else.

Used by 01-build-fhr-first-person.py. A round trip through an XML converter (hkxconv/HKX2) rewrites every float as
text and the whole object graph; this edits the binary instead, so the compressed animation data, the binding and
every other byte of the original stay as they were:

  - the chosen annotation track's array is copied to the end of the __data__ section with the new entries appended,
    followed by the new annotation strings;
  - the track's array pointer is re-pointed there (its local fixup), its size/capacity raised, and one local fixup
    added per new string pointer;
  - the fixup tables are rewritten after the grown data and the section header offsets moved.

A clip with no annotation tracks at all (Enhanced 1stperson Parry Animation's) gets one unnamed track, written the
same way. The old array stays in the file unreferenced. Layout facts (64-bit, little endian): hkaAnimation.annotationTracks is
the hkArray at object offset 40; hkaAnnotationTrack is 24 bytes (trackName ptr, annotations hkArray at +8);
hkaAnnotationTrack::Annotation is 16 bytes (float time, 4 pad, text ptr at +8).
"""
import struct

MAGIC = (0x57E0E057, 0x10C0C010)
HEADER = 64
SECTION = 48
ANIMATION_CLASSES = (b'hkaSplineCompressedAnimation', b'hkaInterleavedUncompressedAnimation',
                     b'hkaDeltaCompressedAnimation', b'hkaWaveletCompressedAnimation')
TRACKS_AT = 40     # hkaAnimation.annotationTracks
TRACK_SIZE = 24
ANNOTATION_SIZE = 16
DONT_DEALLOCATE = 0x80000000


def _align(n, a):
    return (n + a - 1) // a * a


def _table(raw, width):
    """Fixup table -> list of tuples, stopping at the 0xFFFFFFFF padding."""
    out = []
    for i in range(0, len(raw) - 4 * width + 1, 4 * width):
        entry = struct.unpack_from('<%dI' % width, raw, i)
        if entry[0] == 0xFFFFFFFF:
            break
        out.append(entry)
    return out


def _pack_table(entries, width):
    raw = b''.join(struct.pack('<%dI' % width, *e) for e in entries)
    return raw + b'\xff' * (_align(len(raw), 16) - len(raw))


class Packfile:
    def __init__(self, blob):
        self.blob = bytearray(blob)
        m0, m1, _tag, version = struct.unpack_from('<4i', blob, 0)
        if (m0 & 0xFFFFFFFF, m1 & 0xFFFFFFFF) != MAGIC or version != 8:
            raise ValueError('not a version-8 Havok packfile')
        if struct.unpack_from('<4B', blob, 16) != (8, 1, 0, 1):
            raise ValueError('not a 64-bit little-endian packfile')
        self.num_sections = struct.unpack_from('<i', blob, 20)[0]
        self.sections = []
        for i in range(self.num_sections):
            o = HEADER + i * SECTION
            tag = bytes(blob[o:o + 20]).split(b'\0')[0]
            start, *offs = struct.unpack_from('<7I', blob, o + 20)
            self.sections.append({'tag': tag, 'start': start, 'local': offs[0], 'global': offs[1],
                                  'virtual': offs[2], 'exports': offs[3], 'imports': offs[4], 'end': offs[5]})
        self.data_index = next(i for i, s in enumerate(self.sections) if s['tag'] == b'__data__')
        self.names_index = next(i for i, s in enumerate(self.sections) if s['tag'] == b'__classnames__')
        if self.data_index != self.num_sections - 1:
            raise ValueError('__data__ is not the last section')
        d = self.sections[self.data_index]
        if d['exports'] != d['end'] or d['imports'] != d['end']:
            raise ValueError('packfile has exports/imports')
        base = d['start']
        self.data = bytearray(blob[base:base + d['local']])
        self.local = _table(blob[base + d['local']:base + d['global']], 2)
        self.glob = _table(blob[base + d['global']:base + d['virtual']], 3)
        self.virt = _table(blob[base + d['virtual']:base + d['exports']], 3)
        names = self.sections[self.names_index]
        self.class_names = bytes(blob[names['start']:names['start'] + names['end']])

    def _class_at(self, name_offset):
        return self.class_names[name_offset:self.class_names.index(b'\0', name_offset)]

    def _ptr(self, src):
        hit = [dst for s, dst in self.local if s == src]
        return hit[0] if hit else None

    def _cstr(self, offset):
        return bytes(self.data[offset:self.data.index(b'\0', offset)]).decode('utf-8', 'replace')

    def animation(self):
        objs = [src for src, sec, name in self.virt
                if sec == self.names_index and self._class_at(name) in ANIMATION_CLASSES]
        if len(objs) != 1:
            raise ValueError(f'expected one animation object, found {len(objs)}')
        return objs[0]

    def duration(self):
        return struct.unpack_from('<f', self.data, self.animation() + 20)[0]

    def tracks(self):
        """[(track offset, [(time, text), ...]), ...]"""
        anim = self.animation()
        arr = self._ptr(anim + TRACKS_AT)
        count = struct.unpack_from('<i', self.data, anim + TRACKS_AT + 8)[0]
        out = []
        for t in range(count):
            track = arr + t * TRACK_SIZE
            ann_arr = self._ptr(track + 8)
            n = struct.unpack_from('<i', self.data, track + 16)[0]
            items = []
            for a in range(n):
                entry = ann_arr + a * ANNOTATION_SIZE
                text = self._ptr(entry + 8)
                items.append((struct.unpack_from('<f', self.data, entry)[0], self._cstr(text) if text is not None else ''))
            out.append((track, items))
        return out

    def annotations(self):
        return [a for _, items in self.tracks() for a in items]

    def add_track(self):
        """Give an animation with no annotation tracks one empty, unnamed track."""
        anim = self.animation()
        if struct.unpack_from('<i', self.data, anim + TRACKS_AT + 8)[0] != 0:
            raise ValueError('animation already has annotation tracks')
        arr = _align(len(self.data), 16)
        self.data += b'\0' * (arr - len(self.data) + TRACK_SIZE)
        self.data += b'\0' * (_align(len(self.data), 16) - len(self.data))
        self.local = [(s, d) for s, d in self.local if s != anim + TRACKS_AT]
        self.local.append((anim + TRACKS_AT, arr))
        struct.pack_into('<iI', self.data, anim + TRACKS_AT + 8, 1, 1 | DONT_DEALLOCATE)

    def add(self, new):
        """Append [(time, text), ...] to the track that already carries annotations (else track 0)."""
        tracks = self.tracks()
        if not tracks:
            self.add_track()
            tracks = self.tracks()
        track = max(tracks, key=lambda t: len(t[1]))[0]
        old_arr = self._ptr(track + 8)
        n_old = struct.unpack_from('<i', self.data, track + 16)[0]
        old_entries = [bytes(self.data[old_arr + i * ANNOTATION_SIZE:old_arr + (i + 1) * ANNOTATION_SIZE])
                       for i in range(n_old)] if n_old else []
        old_text = [self._ptr(old_arr + i * ANNOTATION_SIZE + 8) for i in range(n_old)]

        arr = _align(len(self.data), 16)
        self.data += b'\0' * (arr - len(self.data))
        for raw in old_entries:
            self.data += raw
        for time, _ in new:
            self.data += struct.pack('<f4xQ', time, 0)
        strings = []
        for _, text in new:
            # Each string on a 16-byte boundary, as Havok writes them: hkStringPtr keeps an "owned" flag in bit 0
            # of the pointer, so a string at an odd address is read from one byte earlier - the previous string's
            # NUL - and the annotation arrives as an empty event (LSdFHighStance 2026-11-10: every appended tag at
            # an odd offset never fired in game; every one at an even offset did).
            self.data += b'\0' * (_align(len(self.data), 16) - len(self.data))
            pos = len(self.data)
            self.data += text.encode('utf-8') + b'\0'
            strings.append(pos)
        self.data += b'\0' * (_align(len(self.data), 16) - len(self.data))

        # re-point the track's array; copied old entries keep their strings, new entries point at theirs
        self.local = [(s, d) for s, d in self.local if s != track + 8]
        self.local.append((track + 8, arr))
        for i, dst in enumerate(old_text):
            if dst is not None:
                self.local.append((arr + i * ANNOTATION_SIZE + 8, dst))
        for i, dst in enumerate(strings):
            self.local.append((arr + (n_old + i) * ANNOTATION_SIZE + 8, dst))
        total = n_old + len(new)
        struct.pack_into('<iI', self.data, track + 16, total, total | DONT_DEALLOCATE)

    def save(self):
        d = self.sections[self.data_index]
        local = _pack_table(self.local, 2)
        glob = _pack_table(self.glob, 3)
        virt = _pack_table(self.virt, 3)
        body = bytes(self.data) + local + glob + virt
        o_local = len(self.data)
        o_global = o_local + len(local)
        o_virtual = o_global + len(glob)
        end = o_virtual + len(virt)
        head = bytearray(self.blob[:d['start']])
        o = HEADER + self.data_index * SECTION
        struct.pack_into('<7I', head, o + 20, d['start'], o_local, o_global, o_virtual, end, end, end)
        return bytes(head) + body


def annotate(src, dst, new):
    with open(src, 'rb') as fh:
        pf = Packfile(fh.read())
    pf.add(new)
    out = pf.save()
    check = Packfile(out)
    have = check.annotations()
    for item in new:
        if not any(abs(t - item[0]) < 1e-6 and x == item[1] for t, x in have):
            raise AssertionError(f'{dst}: {item} missing after write')
    check_string_alignment(check, dst)
    if len(have) != len(pf.annotations()):
        raise AssertionError(f'{dst}: annotation count changed on re-read')
    with open(dst, 'wb') as fh:
        fh.write(out)


def check_string_alignment(pf, label):
    """Every annotation text must start at an even offset (hkStringPtr's bit 0 is a flag, see Packfile.add)."""
    ptr = dict(pf.local)
    for track, items in pf.tracks():
        arr = ptr.get(track + 8)
        for i in range(len(items)):
            s = ptr.get(arr + i * ANNOTATION_SIZE + 8)
            if s is not None and s % 2:
                raise AssertionError(f'{label}: annotation {items[i]} text at odd offset {s}: the game reads it empty')


def read(path):
    with open(path, 'rb') as fh:
        pf = Packfile(fh.read())
    return pf.duration(), pf.annotations()
