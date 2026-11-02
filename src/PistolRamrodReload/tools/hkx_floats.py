"""Float tracks for clips written with PyNifly's anim_skyrim, which always writes none.

Skyrim's third- and first-person skeletons bind float slots to node visibility:
`hkFade:AnimObjectA/B/L/R`, then `hkVis:Shield`, `hkVis:NPC L MagicNode [LMag]`, `hkVis:NPC R MagicNode [RMag]`,
`hkVis:Weapon`. All of them have reference value 0.

Every frame, the behaviour update hides each hkVis node whose slot reads exactly 0 in the graph's output
(SkyrimSE.exe ID 63835, traced with ZenBoneTrace 1.4.0 on 2026-11-02). A slot that no playing clip carries reads 0.
So a PyNifly clip that owns the whole pose hides both gun nodes: in first person, the right-gun two-pistol reload
made both pistols vanish until the release state ended.

The vanilla staff clips carry slots 4-7 as static 1.0. The layout:
- one mask byte (0x03) per float track, right after the transform masks; the header's maskAndQuantSize counts them;
- the four floats after the transform data, at floatBlockOffsets[block], relative to the block's start.

read(data) -> FloatTracks: the slots, mask bytes and float data of a vanilla clip (static tracks only).
write(path, anim, floats, ptr_size=8): anim_skyrim.write_skyrim_animation, plus those float tracks.
"""
import json
import os
import struct
import sys
from collections import namedtuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
import anim_skyrim as A  # noqa: E402

FloatTracks = namedtuple('FloatTracks', 'slots masks data')


def _layout(ptr):
    """hkaSplineCompressedAnimation / hkaAnimationBinding member offsets, as anim_skyrim reads and writes them."""
    arr = ptr + 8
    base = 2 * ptr
    spline = base + 16 + ptr + arr
    blocks = (spline + 28 + ptr - 1) & ~(ptr - 1)
    return dict(num_float=base + 12, mask_quant=spline + 12, num_blocks=spline + 4, block_offsets=blocks,
                float_block_offsets=blocks + arr, data=blocks + 4 * arr, bind_float_idx=base + 2 * ptr + arr, arr=arr)


def read(data):
    """The float tracks of a clip's bytes, or None when it has none. Exits on a spline-compressed (non-static) float
    track, which nothing here needs."""
    ptr = data[0x10]
    lay = _layout(ptr)
    secs = A._parse_hkx_sections(data)
    dsec = secs['__data__']
    dabs = dsec['offset']
    fix = A._parse_local_fixups(data, dsec)
    objs = A._parse_virtual_fixups(data, dsec, secs['__classnames__']['offset'])
    a = [r for r, c in objs if c == 'hkaSplineCompressedAnimation'][0]
    n_tracks = A._u32(data, dabs + a + 2 * ptr + 8)
    n_float = A._u32(data, dabs + a + lay['num_float'])
    if not n_float:
        return None
    n_blocks = A._u32(data, dabs + a + lay['num_blocks'])
    bo = A._read_hkarray_u32(data, dabs, a, lay['block_offsets'], fix, ptr)
    fbo = A._read_hkarray_u32(data, dabs, a, lay['float_block_offsets'], fix, ptr)
    blob = A._read_hkarray_u8(data, dabs, a, lay['data'], fix, ptr)
    slots = []
    for rel, cls in objs:
        if cls == 'hkaAnimationBinding':
            off = rel + lay['bind_float_idx']
            content = fix.get(off)
            cnt = A._u32(data, dabs + off + ptr)
            slots = [struct.unpack_from('<h', data, dabs + content + 2 * i)[0] for i in range(cnt)] if cnt else []
    if len(slots) != n_float:
        sys.exit('float tracks: %d tracks but %d slot bindings' % (n_float, len(slots)))
    found = None
    for b in range(n_blocks):
        masks = bytes(blob[bo[b] + 4 * n_tracks:bo[b] + 4 * n_tracks + n_float])
        if any(m & 0xF0 for m in masks):
            sys.exit('float tracks: spline-compressed float track (masks %s); only static ones are copied' % masks.hex())
        vals = bytes(blob[bo[b] + fbo[b]:bo[b] + fbo[b] + 4 * n_float])
        if found and found != (masks, vals):
            sys.exit('float tracks differ between blocks')
        found = (masks, vals)
    return FloatTracks(slots, found[0], found[1])


def read_file(path):
    with open(path, 'rb') as fh:
        return read(fh.read())


def _pad(buf, n):
    while len(buf) % n:
        buf.append(0)


def write(path, anim, floats, ptr_size=8):
    """anim_skyrim.write_skyrim_animation with `floats` (a FloatTracks, or None for none) added to every block."""
    if not floats:
        A.write_skyrim_animation(path, anim, ptr_size=ptr_size)
        return
    nf = len(floats.slots)
    # the same defaults write_skyrim_animation fills in
    if not anim.num_blocks:
        fpb = anim.max_frames_per_block or 256
        anim.num_blocks = max(1, (anim.num_frames + fpb - 1) // fpb)
    if not anim.block_duration:
        anim.block_duration = anim.duration / anim.num_blocks if anim.num_blocks > 0 else anim.duration
    if not anim.frame_duration:
        anim.frame_duration = anim.duration / max(1, anim.num_frames - 1) if anim.num_frames > 1 else 1.0 / 30.0
    n = anim.num_tracks
    float_offsets = []
    original = A._compress_all_blocks

    def compress(an, rot_quant=1):
        blob, offsets = original(an, rot_quant=rot_quant)
        out, starts = bytearray(), []
        for s, e in zip(offsets, offsets[1:] + [len(blob)]):
            block = bytearray(blob[s:e][:4 * n]) + floats.masks  # transform masks are 4n bytes, 4-aligned
            _pad(block, 4)
            block += blob[s:e][4 * n:]
            _pad(block, 4)
            float_offsets.append(len(block))
            block += floats.data
            starts.append(len(out))
            out += block
        return bytes(out), starts

    cn_data, name_offs = A._build_anim_classnames_v8()
    A._compress_all_blocks = compress
    try:
        obj, fx = A._build_anim_data_section(anim, name_offs, ptr_size)
    finally:
        A._compress_all_blocks = original
    obj = bytearray(obj)
    lay = _layout(ptr_size)
    spline = [o for o, _, c in fx.virtual if c == name_offs['hkaSplineCompressedAnimation']][0]
    binding = [o for o, _, c in fx.virtual if c == name_offs['hkaAnimationBinding']][0]
    struct.pack_into('<I', obj, spline + lay['num_float'], nf)
    mask_quant = 4 * n + nf
    mask_quant += -mask_quant % 4
    struct.pack_into('<I', obj, spline + lay['mask_quant'], mask_quant)
    fbo = [d for s, d in fx.local if s == spline + lay['float_block_offsets']][0]
    for i, off in enumerate(float_offsets):
        struct.pack_into('<I', obj, fbo + 4 * i, off)
    # binding.floatTrackToFloatSlotIndices: appended after the last object, like any other array content
    _pad(obj, 16)
    idx = len(obj)
    for slot in floats.slots:
        obj += struct.pack('<h', slot)
    _pad(obj, 16)
    arr = binding + lay['bind_float_idx']
    struct.pack_into('<I', obj, arr + ptr_size, nf)
    struct.pack_into('<I', obj, arr + ptr_size + 4, nf | 0x80000000)
    fx.add_local(arr, idx)

    # the rest is write_skyrim_animation's own packing
    local_tbl = fx.build_local_table()
    global_tbl = fx.build_global_table()
    virt_tbl = fx.build_virtual_table()
    cn_start = 0x40 + 3 * A._SEC_HDR_SIZE
    data_start = cn_start + len(cn_data)
    local_abs = data_start + len(obj)
    global_abs = local_abs + len(local_tbl)
    virt_abs = global_abs + len(global_tbl)
    data_end = virt_abs + len(virt_tbl)
    end = cn_start + len(cn_data)
    result = (A._skyrim_file_header(name_offs['hkRootLevelContainer'], ptr_size)
              + A._skyrim_section_header('__classnames__', cn_start, end, end, end, end)
              + A._skyrim_section_header('__types__', data_start, data_start, data_start, data_start, data_start)
              + A._skyrim_section_header('__data__', data_start, local_abs, global_abs, virt_abs, data_end)
              + cn_data + bytes(obj) + local_tbl + global_tbl + virt_tbl)
    with open(path, 'wb') as fh:
        fh.write(result)


def check(path, floats, reference=None):
    """Exits unless `path` carries exactly `floats`, and, when `reference` (the same clip written without them) is
    given, decodes to the same transforms."""
    got = read_file(path)
    if (got or None) != (floats or None):
        sys.exit('%s: float tracks %s, wanted %s' % (path, got, floats))
    if reference is None:
        return
    a, b = A.load_skyrim_animation(path), A.load_skyrim_animation(reference)
    if len(a.tracks) != len(b.tracks) or a.num_frames != b.num_frames:
        sys.exit('%s: %d tracks / %d frames, without float tracks %d / %d' % (path, len(a.tracks), a.num_frames,
                                                                             len(b.tracks), b.num_frames))
    for ta, tb in zip(a.tracks, b.tracks):
        if ta.translations != tb.translations or ta.rotations != tb.rotations or ta.scales != tb.scales:
            sys.exit('%s: adding float tracks changed the decoded transforms' % path)
