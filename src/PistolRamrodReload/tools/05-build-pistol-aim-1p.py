"""First-person pistol aiming (2026-11-02, curator: "arms extended like this", a held pistol straight out low in the
view, its barrel on the crosshair; third person already aims, Loop's clips). Into `Zenderal - Pistol Ramrod Reload`, an
OAR mod of its own (AIM_MOD), so tools/04's rebuilds leave it alone.

First person plays vanilla's staff clips for the pistols (tools/04). A shot is an aimed fire-and-forget cast, and with
the Flintlock Overhaul's ChargeTime 0 the engine sends `M?h_SpellAimedStart` and `M?h_SpellReady_event` in the same
frame (traced 2026-11-02), every aimed-cast transition a cut (no blend, read from the graph):
  - left hand: MLh_AimedFireAndForgetBehavior starts in PreCharge, the ready event takes it to PreReady
    (`stfmagic_preready`, 0.333 s, its end trigger -> ReadyLoop `stfmagic_readyloop`): the raise is PreReady's;
  - right hand: MRh_AimedFireAndForgetBehavior has no PreReady: PreCharge -> ReadyState (`stfmagicright_readyloop`,
    looping) at once, so its ready loop opens with the raise and then holds the aim for READY_HOLD;
  - the release (`stfmagic_release` / `stfmagicright_release`, 0.667 s, the bullet at 0.334: the release clip
    generator's trigger) holds the aim, kicks at KICK_AT and lowers into the idle (the release ends on `M?h_Equipped`,
    a cut to the idle);
  - precharge and charge loop (never seen at ChargeTime 0) raise and hold too, so a charge time shows the same.
Every clip keeps vanilla's length (the graph's triggers are at its times) and float tracks (tools/hkx_floats), and
starts with AnimObjectUnequip like the reload's copies of these clips.

The pose: the pistol hand on GRIP in the first-person camera's frame (x right, y forward, z up; the left hand
mirrored), the gun turned so its bore points at CONVERGE units down the view axis, upright (the mesh's up: away from
its butt). The gun sits in the hand as in Loop's third-person ready loop (its attach node's track, `Shield` / `Weapon`):
vanilla's first-person staff idle holds it by the back end like a staff, the wrist over its top (measured in the gun
mesh: (-5.4, -4.9) vs Loop's (0.3, -7.1), behind the butt with the hand along the barrel), so the raise turns it into
Loop's grip and the release back. The arm is solved shoulder-elbow-hand (tools/10's Retarget.solve_arm), the elbow
toward ELBOW; every other bone is vanilla's first-person idle for that hand (frame 0), the graph's masks give the other
arm to its own idle. The hand's magic node (`NPC L/R MagicNode`, a child of the hand) sits on the gun's muzzle: the shot
launches from it (ZenSpellAimTrace: 'launch node NPC L MagicNode'), and vanilla's idle keeps it where a staff's tip
would be, (-50.5, -9.3, 54.7) in the hand, which with the arm out put the shots 100 units ahead and 26 above the eye
(curator 2026-11-02: "the bullets don't come from the barrels"). Hit Where You Aim then aims the shot at the crosshair.

OAR: `Aim 1P <pistol group>[ (right hand)]`, drawn with one of the group's pistols in that hand, PRIORITY_AIM (below
the reload's, which win when a reload is asked for). Run after tools/01 (pistol groups), any time.
Usage:  python src/PistolRamrodReload/tools/05-build-pistol-aim-1p.py [<modlist root>] [--preview <out.png>]
"""
import copy
import importlib.util
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P1 = _load('pistol_reload_1p', os.path.join(HERE, '04-build-pistol-reload-1p.py'))
PR, R10, ADS = P1.PR, P1.R10, P1.ADS
anim_skyrim, QRS, _bsa = ADS.anim_skyrim, ADS.QRS, ADS._bsa
smooth, blend, split = PR.smooth, R10.blend, R10.split

AIM_MOD = 'Zenderal - Pistol Aim 1P'
OAR_AIM = ADS.ANIMS_1P + ['OpenAnimationReplacer', AIM_MOD]
PRIORITY_AIM = 1000010000           # below the reload's submods (1000020000+), above anything else in first person
GRIP = np.array([13.0, 35.5, -9.0])  # the right hand in the camera frame; the left at (-x, y, z)
CONVERGE = 1000.0                   # the bores meet on the view axis this far ahead (HWYA aims the shot itself)
ELBOW = np.array([1.0, -0.4, -1.0])  # the right elbow bends this way (camera frame), the left mirrored
RAISE = 0.25                        # idle -> aim
READY_HOLD = 30.0                   # the right hand's ready loop: the raise, then the aim this long (it loops)
KICK_AT, KICK_RISE, KICK_FALL = 0.334, 0.04, 0.22   # the shot's kick: at the bullet, up in KICK_RISE, back over KICK_FALL
KICK_DEG, KICK_BACK = 12.0, 1.5     # the gun pitches up this much about the hand, the hand comes back this far
LOWER = (0.45, 0.667)               # the release lowers into the idle over this span (ending on it: the cut to idle)
FPS = 30.0
HANDS = {'left': dict(idle=PR.IDLE, gun='Shield', arm=R10.ARM_SIDES[0], side=-1.0, suffix='', grip='stfmagic_readyloop.hkx',
                      magic='NPC L MagicNode [LMag]',
                      clips={'stfmagic_precharge.hkx': 'raise', 'stfmagic_chargeloop.hkx': 'hold',
                             'stfmagic_preready.hkx': 'raise', 'stfmagic_readyloop.hkx': 'hold',
                             'stfmagic_release.hkx': 'shot'}),
         'right': dict(idle=PR.IDLE_RIGHT, gun='Weapon', arm=R10.ARM_SIDES[1], side=1.0, suffix=' (right hand)',
                       grip='stfmagicright_readyloop.hkx', magic='NPC R MagicNode [RMag]',
                       clips={'stfmagicright_precharge.hkx': 'raise', 'stfmagicright_chargeloop.hkx': 'hold',
                              'stfmagicright_readyloop.hkx': 'raise_hold', 'stfmagicright_release.hkx': 'shot'})}


def mesh_up(V, c, axis):
    """The gun's up in its mesh: away from the butt (the vertex farthest from the bore line), square to the bore. The
    mesh's centroid did not do: the lock and barrel carry enough vertices to put it above the bore (pistool03)."""
    a = PR.unit(axis)
    off = V - c
    perp = off - np.outer(off @ a, a)
    return -PR.unit(perp[int(np.argmax(np.linalg.norm(perp, axis=1)))])


class Aim:
    """The aim pose for one hand and one pistol group, on that hand's first-person idle."""

    def __init__(self, rt, idle, h, c, axis, V, grip):
        """`grip`: the gun node's local (to the hand) in Loop's ready loop, 4x4."""
        self.rt, self.h = rt, h
        self.base = rt.locals1(idle, 0)
        w = rt.world1(self.base)
        self.cam = PR.unscaled(w[rt.cam1])
        self.arm = tuple(rt.i1[n] for n in h['arm'])
        self.gun, self.magic = rt.i1[h['gun']], rt.i1[h['magic']]
        for node in (self.gun, self.magic):
            if rt.sk1.parents[node] != self.arm[2]:
                sys.exit('%s does not hang on %s in the first-person skeleton' % (rt.sk1.bones[node], h['arm'][2]))
        self.grip = grip
        self.c, self.axis, self.up = np.asarray(c, float), PR.unit(axis), mesh_up(V, c, axis)

    def locals(self, kick=0.0):
        """The idle with the gun arm on the aim, kicked `kick` (0..1) of the shot's kick. Returns (locals, miss)."""
        s = self.h['side']
        grip = np.array([GRIP[0] * s, GRIP[1], GRIP[2]])
        bore = PR.unit(np.array([0.0, CONVERGE, 0.0]) - grip)
        up = np.array([0.0, 0.0, 1.0])
        up = PR.unit(up - bore * (up @ bore))
        if kick:
            r = PR.rot_axis(np.cross(bore, up), KICK_DEG * kick)     # muzzle up about the hand's side axis
            bore, up = r @ bore, r @ up
            grip = grip - bore * KICK_BACK * kick
        frm = np.column_stack([self.axis, self.up, np.cross(self.axis, self.up)])
        to = np.column_stack([bore, up, np.cross(bore, up)])
        g_cam = np.eye(4)
        g_cam[:3, :3] = to @ frm.T                                   # the gun node in the camera frame
        hand_cam = g_cam @ np.linalg.inv(PR.unscaled(self.grip))
        hand_cam[:3, 3] = grip
        target = self.cam @ hand_cam
        loc = [m.copy() for m in self.base]
        loc[self.gun] = self.grip.copy()
        loc[self.magic][:3, 3] = (self.grip @ np.r_[self.c, 1])[:3]        # the shot leaves from the muzzle
        w1 = self.rt.world1(loc)
        S = w1[self.arm[0]][:3, 3]
        elbow = self.cam[:3, :3] @ (ELBOW * np.array([s, 1.0, 1.0]))
        self.rt.solve_arm(loc, w1, self.arm, target, S + 20.0 * PR.unit(elbow))
        miss = float(np.linalg.norm(self.rt.world1(loc)[self.arm[2]][:3, 3] - target[:3, 3]))
        return loc, miss


def build(aim, template, kind, n_frames):
    """One clip of `kind` (raise / hold / raise_hold / shot) on `template`'s track layout. Returns (anim, worst miss)."""
    idle = aim.base
    held, miss = aim.locals()
    out = anim_skyrim.load_skyrim_animation(template)
    for t in out.tracks:
        t.translations, t.rotations, t.scales = [], [], []
    worst = miss
    for f in range(n_frames):
        t = f / FPS
        if kind == 'hold':
            pose = held
        elif kind in ('raise', 'raise_hold'):
            pose = blend(idle, held, smooth(t / RAISE))
        else:     # shot
            if t < KICK_AT:
                k = 0.0
            elif t < KICK_AT + KICK_RISE:
                k = smooth((t - KICK_AT) / KICK_RISE)
            else:
                k = 1.0 - smooth((t - KICK_AT - KICK_RISE) / KICK_FALL)
            pose, m = aim.locals(k) if k > 1e-4 else (held, miss)
            worst = max(worst, m)
            pose = blend(pose, idle, smooth((t - LOWER[0]) / (LOWER[1] - LOWER[0])))
        for tr, m in zip(out.tracks, pose):
            tt, q, sc = split(m)
            if tr.rotations and sum(x * y for x, y in zip(q, tr.rotations[-1])) < 0:
                q = [-x for x in q]
            tr.translations.append(tt)
            tr.rotations.append(q)
            tr.scales.append([sc, sc, sc])
    out.num_frames, out.frame_duration = n_frames, 1.0 / FPS
    out.duration = (n_frames - 1) / FPS
    out.annotations = [anim_skyrim.Annotation(time=0.0, text=PR.UNEQUIP)]
    return ADS.havok_blocks(out), worst


def preview(rt, aims, V, path):
    """Both hands' aim, drawn as the first-person camera sees it (85 deg wide), skeleton and gun vertices."""
    from PIL import Image, ImageDraw
    W, H, fov = 800, 450, 85.0
    fpx = (W / 2) / math.tan(math.radians(fov / 2))
    img = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(img)
    for aim in aims:
        loc, _ = aim.locals()
        w = rt.world1(loc)
        inv = np.linalg.inv(aim.cam)

        def proj(p):
            q = (inv @ np.r_[p, 1])[:3]
            return None if q[1] < 1.0 else (W / 2 + fpx * q[0] / q[1], H / 2 - fpx * q[2] / q[1])
        for i, p in enumerate(rt.sk1.parents):
            if p >= 0 and i in aim.arm + (rt.sk1.parents[aim.arm[0]],):
                a, b = proj(w[p][:3, 3]), proj(w[i][:3, 3])
                if a and b:
                    d.line([a, b], fill=(60, 60, 200), width=3)
        g = w[aim.gun]
        for v in V[::3]:
            q = proj((g @ np.r_[v, 1])[:3])
            if q:
                d.point(q, fill=(0, 120, 0))
        m = proj((g @ np.r_[aim.c, 1])[:3])
        if m:
            d.ellipse([m[0] - 3, m[1] - 3, m[0] + 3, m[1] + 3], outline=(200, 0, 0))
    d.line([W / 2 - 6, H / 2, W / 2 + 6, H / 2], fill=(0, 0, 0))
    d.line([W / 2, H / 2 - 6, W / 2, H / 2 + 6], fill=(0, 0, 0))
    img.save(path)
    print('wrote', path)


def main():
    args = sys.argv[1:]
    out_png = None
    if '--preview' in args:
        i = args.index('--preview')
        out_png = args[i + 1]
        del args[i:i + 2]
    root = args[0] if args else ADS.TOOLS['modlistRoot']
    mods_dir = os.path.join(root, 'mods')
    bsa = _bsa.listing(os.path.join(root, 'Stock Game', 'Data', 'Skyrim - Animations.bsa'))
    tmp = os.path.join(os.environ.get('TEMP', '.'), '_pistol_aim_1p.hkx')
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][ADS.SKELETON]))
    sk1 = anim_skyrim.load_skyrim_skeleton(tmp)
    with open(tmp, 'wb') as fh:
        fh.write(_bsa.read(bsa[0], bsa[1][R10.R3P.SKELETON]))
    sk3 = anim_skyrim.load_skyrim_skeleton(tmp)
    rt = R10.Retarget(sk1, sk3)
    profile, mods = QRS.profile_mods(root)
    vanilla, floats = {}, {}
    for name in sorted({n for h in HANDS.values() for n in [h['idle']] + list(h['clips'])}):
        src, data = QRS.winner(mods_dir, mods, bsa, ADS.ANIMS_1P + [name])
        if not src.startswith('Skyrim - '):
            sys.exit('%s comes from %s: tools/05 builds on vanilla\'s first-person staff clips' % (name, src))
        vanilla[name] = P1.clip(tmp, data)
        floats[name] = PR.HF.read(data)
    groups = PR.pistol_groups(mods_dir, mods)
    ctx = PR.Ctx(root)
    ctx.right                                   # finds Loop's right-hand set (ctx.right_dir)
    grips = {}
    for hand, h in HANDS.items():
        a = anim_skyrim.load_skyrim_animation(os.path.join(ctx.right_dir if hand == 'right' else ctx.loop_dir, h['grip']))
        tr = a.tracks[ctx.ix[h['gun']]]
        grips[hand] = ADS.trs(tr.translations[0], tr.rotations[0], tr.scales[0][0])
    if out_png:
        label, _, _, (c, axis, _), V = groups[0]
        aims = [Aim(rt, vanilla[h['idle']], h, c, axis, V, grips[hand]) for hand, h in HANDS.items()]
        for a in aims:
            print('%s: hand misses its aim by %.2f' % (a.h['gun'], a.locals()[1]))
        preview(rt, aims, V, out_png)
        return
    oar = os.path.join(mods_dir, PR.MOD, *OAR_AIM)
    if os.path.isdir(oar):
        shutil.rmtree(oar)
    written = 0
    for i, (label, path, weapons, (c, axis, radius), V) in enumerate(groups):
        for hand, h in HANDS.items():
            aim = Aim(rt, vanilla[h['idle']], h, c, axis, V, grips[hand])
            name = 'Aim 1P %s%s' % (label, h['suffix'])
            sub = os.path.join(oar, name)
            os.makedirs(sub)
            worst = 0.0
            for clip, kind in h['clips'].items():
                van = vanilla[clip]
                n = int(round(READY_HOLD * FPS)) + 1 if kind == 'raise_hold' else van.num_frames
                tpl = os.path.join(os.environ.get('TEMP', '.'), '_pistol_aim_tpl.hkx')
                with open(tpl, 'wb') as fh:
                    fh.write(_bsa.read(bsa[0], bsa[1]['\\'.join(ADS.ANIMS_1P).lower() + '\\' + clip]))
                anim, miss = build(aim, tpl, kind, n)
                os.remove(tpl)
                worst = max(worst, miss)
                out = os.path.join(sub, clip)
                PR.write_clip(out, anim, floats[clip], reference=True)
                ADS.check_blocks(out)
                written += 1
            if worst > 0.5:
                sys.exit('%s %s: the hand misses its aim by %.2f (out of reach: move GRIP)' % (hand, label, worst))
            ADS.write_config(sub, {'name': name,
                                   'description': 'First person: the %s-hand pistol held out at aim (%s), tools/05.'
                                                  % (hand, ', '.join('%s %s' % w for w in weapons)),
                                   'priority': PRIORITY_AIM + 10 * i + (1 if hand == 'right' else 0),
                                   'conditions': [PR.LOOP.DRAWN,
                                                  PR.LOOP.any_of([PR.LOOP.equipped(p, f, hand == 'left')
                                                                  for p, f in weapons])]})
            print('1P aim %-5s %-18s hand on its aim (worst %.3f)' % (hand, label, worst))
    ADS.write_config(oar, {'name': AIM_MOD, 'author': 'Zenderal',
                           'description': 'First-person aiming for the flintlock pistols, either hand (tools/05).'})
    os.remove(tmp)
    print('built %s: %d clips' % (oar, written))


if __name__ == '__main__':
    main()
