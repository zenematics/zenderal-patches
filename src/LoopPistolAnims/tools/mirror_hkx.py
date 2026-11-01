"""Mirror a Skyrim SE character animation left <-> right (used by 01-build-loop-pistol-anims.py).

Loop's clips are left-hand clips. The right hand plays its OWN files (vanilla ships stfmagicright_*,
staffright_idle, staffmagicright_*arm next to the left-hand stfmagic_* set), so a right-hand pistol needs
mirrored copies.

Method, per frame: forward kinematics to model space, reflect across the body's centre plane (model X), take
each bone's pose from its mirror partner (L <-> R names, Shield <-> Weapon: the left and right weapon attach
nodes), correct by the rest pose so the skeleton's asymmetric local axes do not twist anything, and convert
back to parent-local. At the rest pose the result is the rest pose. Exception: the right attach node
`Weapon` takes the reflected `Shield` frame turned 180 deg about +Y, because the pistol mesh itself is not
mirrored (plain reflection would put its grip up). Read/written with PyNifly's
hkx/anim_skyrim.py (`pynifly` in tools.json); tracks map 1:1 to the XPMSSE skeleton's bones.
"""
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(TOOLS['pynifly'], 'hkx'))
import anim_skyrim  # noqa: E402  (PyNifly, no Blender dependency)

SKELETON = ['XP32 Maximum Skeleton Special Extended', 'meshes', 'actors', 'character', 'character assets',
            'skeleton.hkx']


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qinv(q):
    return (-q[0], -q[1], -q[2], q[3])


def qrot(q, v):
    x, y, z, w = q
    t = (2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0]))
    return (v[0] + w * t[0] + y * t[2] - z * t[1], v[1] + w * t[1] + z * t[0] - x * t[2],
            v[2] + w * t[2] + x * t[1] - y * t[0])


def qmirror(q):
    """S R S for S = diag(-1, 1, 1): reflection across the model YZ plane."""
    return (q[0], -q[1], -q[2], q[3])


def partners(bones):
    """bone index -> mirror partner index (itself when it has none)."""
    index = {b: i for i, b in enumerate(bones)}
    out = []
    for b in bones:
        if b == 'Shield':
            cand = 'Weapon'
        elif b == 'Weapon':
            cand = 'Shield'
        else:
            cand = (b.replace(' L ', ' \0 ').replace(' R ', ' L ').replace(' \0 ', ' R ')
                     .replace('[L', '[\0').replace('[R', '[L').replace('[\0', '[R'))
        out.append(index.get(cand, index[b]))
    return out


class Mirror:
    def __init__(self, mods_dir):
        self.sk = anim_skyrim.load_skyrim_skeleton(os.path.join(mods_dir, *SKELETON))
        self.pair = partners(self.sk.bones)
        ref = [(tuple(p.translation), tuple(p.rotation)) for p in self.sk.reference_pose]
        self.ref_world = self._fk(lambda i: ref[i])
        n = len(self.sk.bones)
        # rest correction: mirrored partner rest -> own rest
        self.corr = [qmul(qinv(qmirror(self.ref_world[self.pair[i]][1])), self.ref_world[i][1]) for i in range(n)]
        self.ref = ref
        self.weapon = self.sk.bones.index('Weapon')
        self.pelvis = next(i for i, b in enumerate(self.sk.bones) if b.startswith('NPC Pelvis'))
        spine = next(i for i, b in enumerate(self.sk.bones) if b.startswith('NPC Spine ['))
        clav = {i for i, b in enumerate(self.sk.bones) if b.startswith(('NPC L Clavicle', 'NPC R Clavicle'))}
        self.arm = []
        for i, parent in enumerate(self.sk.parents):  # both clavicles and their descendants
            self.arm.append(i in clav or (parent >= 0 and self.arm[parent]))
        self.upper = []
        for i, parent in enumerate(self.sk.parents):  # spine and its descendants (parents precede children)
            self.upper.append(i == spine or (parent >= 0 and self.upper[parent]))

    def _fk(self, local):
        world = []
        for i, parent in enumerate(self.sk.parents):
            t, r = local(i)
            if parent < 0:
                world.append((t, r))
            else:
                pt, pr = world[parent]
                v = qrot(pr, t)
                world.append(((pt[0] + v[0], pt[1] + v[1], pt[2] + v[2]), qmul(pr, r)))
        return world

    def mirror(self, src, dst, upper_only=False, half_cycle=False):
        """upper_only: keep the hips and legs exactly as in the source (no mirror, no time shift) and mirror only
        the spine and everything above it, relative to the pelvis. v8 in game: fully mirrored locomotion made the
        legs snap into splits/crouches while running, because other layers (Smooth Moveset base locomotion,
        TDM) drive the legs on the ORIGINAL clips' timing; a mirrored lower body fights them.
        half_cycle (with upper_only): the upper body is taken from half a stride later (the clip is one looping
        stride whose last frame closes the loop), so the free arm swings against the opposite leg again."""
        anim = anim_skyrim.load_skyrim_animation(src)
        n_tracks = anim.num_tracks
        if n_tracks > len(self.sk.bones):
            raise SystemExit(f'{src}: {n_tracks} tracks > {len(self.sk.bones)} skeleton bones')
        frames = max(len(t.rotations) for t in anim.tracks)
        period = frames - 1
        shift = int(round(period / 2.0)) if half_cycle else 0

        def local_at(f):
            def local(i):
                if i < n_tracks:
                    tr = anim.tracks[i]
                    return (tuple(tr.translations[min(f, len(tr.translations) - 1)]),
                            tuple(tr.rotations[min(f, len(tr.rotations) - 1)]))
                return self.ref[i]
            return local

        new_t = [[] for _ in range(n_tracks)]
        new_r = [[] for _ in range(n_tracks)]
        for f in range(frames):
            world = self._fk(local_at(f))
            fs = (f + shift) % period if shift else f
            src_world = self._fk(local_at(fs)) if fs != f else world
            if upper_only:
                # move the source upper body onto the rest pelvis, mirror there, put it back on this frame's pelvis
                pp, pq = src_world[self.pelvis]
                rp, rq = self.ref_world[self.pelvis]
                cq = qmul(rq, qinv(pq))
                canon = []
                for t, r in src_world:
                    v = qrot(cq, (t[0] - pp[0], t[1] - pp[1], t[2] - pp[2]))
                    canon.append(((v[0] + rp[0], v[1] + rp[1], v[2] + rp[2]), qmul(cq, r)))
                ap, aq = world[self.pelvis]
                aq2 = qmul(aq, qinv(rq))
            else:
                canon = src_world
            mworld = []
            for i in range(len(self.sk.bones)):
                if upper_only and not self.upper[i]:
                    mworld.append(world[i])
                    continue
                pt, pr = canon[self.pair[i]]
                if i == self.weapon:
                    # the gun hangs from this node and is not mirrored: reflecting the frame flips its grip axis
                    # (+X) up, so turn it 180 deg about the barrel axis (+Y) -> barrel and grip as on the left
                    rot = qmul(qmirror(pr), (0.0, 1.0, 0.0, 0.0))
                else:
                    rot = qmul(qmirror(pr), self.corr[i])
                pos = (-pt[0], pt[1], pt[2])
                if upper_only:
                    v = qrot(aq2, (pos[0] - rp[0], pos[1] - rp[1], pos[2] - rp[2]))
                    pos = (v[0] + ap[0], v[1] + ap[1], v[2] + ap[2])
                    rot = qmul(aq2, rot)
                mworld.append((pos, rot))
            for i in range(n_tracks):
                parent = self.sk.parents[i]
                t, r = mworld[i]
                if parent >= 0:
                    pt, pr = mworld[parent]
                    inv = qinv(pr)
                    t = qrot(inv, (t[0] - pt[0], t[1] - pt[1], t[2] - pt[2]))
                    r = qmul(inv, r)
                if r[3] < 0:
                    r = tuple(-c for c in r)
                new_t[i].append(list(t))
                new_r[i].append(list(r))
        for i in range(n_tracks):
            tr = anim.tracks[i]
            tr.translations, tr.rotations = new_t[i], new_r[i]
            if len(tr.scales) != frames:
                tr.scales = [tr.scales[min(f, len(tr.scales) - 1)] for f in range(frames)]
        # keep the source's spline block header (Havok: blockDuration = (maxFramesPerBlock - 1) * frameDuration).
        # Zeroing it made PyNifly write blockDuration = clip length, and right-handed running hopped (v11, 2026-10-17).
        anim_skyrim.write_skyrim_animation(dst, anim, ptr_size=8)
        return anim_skyrim.load_skyrim_animation(dst)

    def mirror_arms(self, src, dst, half_cycle=False):
        """Vanilla's way (v11): Bethesda's right-hand staff clips (stfmagicright_readyloop, staffright_idle,
        stfmagicright_release) have pelvis, legs AND spine identical to the left-hand clips (0.0 deg) and differ
        only in the arms. So keep every bone outside the two clavicle subtrees exactly as in the source and mirror
        only the arms: each arm bone takes its partner's model-space rotation, reflected (rest-corrected; the
        `Weapon` node turned 180 deg about +Y as in mirror()), and keeps its own local translation (bone length).
        half_cycle: the arms come from half a stride later (looping strides), so the free arm swings against the
        opposite leg."""
        anim = anim_skyrim.load_skyrim_animation(src)
        n_tracks = anim.num_tracks
        frames = max(len(t.rotations) for t in anim.tracks)
        period = frames - 1
        shift = int(round(period / 2.0)) if half_cycle else 0

        def local_at(f):
            def local(i):
                if i < n_tracks:
                    tr = anim.tracks[i]
                    return (tuple(tr.translations[min(f, len(tr.translations) - 1)]),
                            tuple(tr.rotations[min(f, len(tr.rotations) - 1)]))
                return self.ref[i]
            return local

        new_r = [[] for _ in range(n_tracks)]
        new_t = [[] for _ in range(n_tracks)]
        for f in range(frames):
            here = local_at(f)
            fs = (f + shift) % period if shift else f
            src_world = self._fk(local_at(fs))
            world_rot = []
            for i, parent in enumerate(self.sk.parents):
                t, r = here(i)
                if self.arm[i]:
                    pr = src_world[self.pair[i]][1]
                    if i == self.weapon:
                        wr = qmul(qmirror(pr), (0.0, 1.0, 0.0, 0.0))
                    else:
                        wr = qmul(qmirror(pr), self.corr[i])
                    lr = qmul(qinv(world_rot[parent]), wr) if parent >= 0 else wr
                else:
                    lr = r
                    wr = qmul(world_rot[parent], r) if parent >= 0 else r
                world_rot.append(wr)
                if i < n_tracks:
                    if lr[3] < 0:
                        lr = tuple(-c for c in lr)
                    new_r[i].append(list(lr))
                    new_t[i].append(list(t))
        for i in range(n_tracks):
            tr = anim.tracks[i]
            tr.translations, tr.rotations = new_t[i], new_r[i]
            if len(tr.scales) != frames:
                tr.scales = [tr.scales[min(f, len(tr.scales) - 1)] for f in range(frames)]
        # keep the source's spline block header (Havok: blockDuration = (maxFramesPerBlock - 1) * frameDuration).
        # Zeroing it made PyNifly write blockDuration = clip length, and right-handed running hopped (v11, 2026-10-17).
        anim_skyrim.write_skyrim_animation(dst, anim, ptr_size=8)
        return anim_skyrim.load_skyrim_animation(dst)
