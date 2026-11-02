"""Compare a ZenBoneTrace log with a clip's forward kinematics, frame by frame.

usage: python src/ZenBoneTrace/compare.py <ZenBoneTrace.log> <clip.hkx> [shot time in the clip, default 0.334]

The log's times run from the player's spell-fire action, which the staff shot clip's graph trigger fires at 0.334 s
(MLh_SpellFire_Event), so clip time = log time + shot time. Positions are taken into the 3D root's frame (model space,
what the clip's NPC Root track is relative to); the matrix convention (R or R transposed) is the one that fits Loop's
untouched recoil frames best. Prints, per traced fire, each bone's distance from where the clip puts it, over time,
and the local rotation difference of the right arm bones.
"""
import importlib.util
import math
import os
import re
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
spec = importlib.util.spec_from_file_location('pr', os.path.join(ROOT, 'src', 'PistolRamrodReload', 'tools', '01-build-pistol-reload.py'))
PR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PR)
ADS = PR.ADS


def parse(path):
    fires, cur = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = re.sub(r'^(\[[^\]]*\]\s*)+', '', line).strip()     # spdlog's [time] [thread] [level] prefix
        if line.startswith('FIRE'):
            cur = {'frames': {}, 'events': [], 'locals': {}, 'head': line}
            fires.append(cur)
        elif cur is None:
            continue
        elif line.startswith('ROOT'):
            v = line.split()
            t = float(v[1])
            r = np.array([float(x) for x in v[2:11]]).reshape(3, 3)
            cur['frames'].setdefault(t, {})['root'] = (r, np.array([float(x) for x in v[11:14]]), float(v[14]))
        elif line.startswith('BONE'):
            parts = line.split(' | ')
            t = float(parts[0].split()[1])
            bones = {}
            for p in parts[1:]:
                m = re.match(r'(.+?) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)$', p)
                bones[m.group(1)] = np.array([float(m.group(i)) for i in (2, 3, 4)])
            cur['frames'].setdefault(t, {})['bones'] = bones
        elif line.startswith('LOCAL'):
            m = re.match(r'LOCAL (-?[\d.]+) (.+?\]|Shield) ((?:-?[\d.]+ ){9})', line)
            if m:
                cur['locals'].setdefault(float(m.group(1)), {})[m.group(2)] = np.array([float(x) for x in m.group(3).split()]).reshape(3, 3)
        elif line.startswith('EV'):
            cur['events'].append(line)
    return fires


def main():
    log, clip_path = sys.argv[1], sys.argv[2]
    shot = float(sys.argv[3]) if len(sys.argv) > 3 else 0.334
    ctx = PR.Ctx(ADS.TOOLS['modlistRoot'])
    rig, ix = ctx.rig, ctx.ix
    anim = PR.anim_skyrim.load_skyrim_animation(clip_path)
    fd = anim.frame_duration
    worlds = [rig.world(anim, f) for f in range(anim.num_frames)]

    def clip_pos(name, t):
        x = min(max(t / fd, 0.0), anim.num_frames - 1.0)
        f0 = int(math.floor(x))
        f1 = min(f0 + 1, anim.num_frames - 1)
        a = x - f0
        return worlds[f0][ix[name]][:3, 3] * (1 - a) + worlds[f1][ix[name]][:3, 3] * a

    def clip_local(name, t):
        f = int(round(min(max(t / fd, 0.0), anim.num_frames - 1.0)))
        return ADS.quat_mat(anim.tracks[ix[name]].rotations[f])

    for n, fire in enumerate(parse(log)):
        frames = sorted((t, d) for t, d in fire['frames'].items() if 'root' in d and 'bones' in d)
        print('==== fire %d: %s, %d frames' % (n, fire['head'], len(frames)))
        for e in fire['events'][:40]:
            print('   ', e)
        # pick the convention on Loop's own recoil frames (clip time < KEEP_FRAMES)
        best = None
        for conv in ('R', 'RT'):
            err = []
            for t, d in frames:
                ct = t + shot
                if ct > PR.KEEP_FRAMES * fd:
                    break
                r, tr, s = d['root']
                R = r if conv == 'R' else r.T
                for name in ('NPC L Hand [LHnd]', 'NPC R Hand [RHnd]', 'NPC Head [Head]'):
                    p = R.T @ (d['bones'][name] - tr) / s
                    err.append(np.linalg.norm(p - clip_pos(name, ct)))
            if err and (best is None or np.mean(err) < best[1]):
                best = (conv, float(np.mean(err)))
        print('   convention %s, mean error on Loop\'s frames %.2f units' % best)
        conv = best[0]
        names = ['NPC R UpperArm [RUar]', 'NPC R Forearm [RLar]', 'NPC R Hand [RHnd]', 'AnimObjectR', 'NPC L Hand [LHnd]', 'Shield']
        print('   %-6s %s' % ('clip t', '  '.join('%-14s' % n.split('[')[-1].strip(']')[:14] for n in names)))
        for t, d in frames[::3]:
            ct = t + shot
            r, tr, s = d['root']
            R = r if conv == 'R' else r.T
            row = []
            for name in names:
                if name not in d['bones']:
                    row.append('%-14s' % '-')
                    continue
                p = R.T @ (d['bones'][name] - tr) / s
                row.append('%-14s' % ('%.1f' % np.linalg.norm(p - clip_pos(name, ct))))
            loc = fire['locals'].get(t, {})
            rot = []
            for name in ('NPC R UpperArm [RUar]', 'NPC R Forearm [RLar]', 'NPC R Hand [RHnd]', 'Shield'):
                if name in loc:
                    g = loc[name] if conv == 'R' else loc[name].T
                    c = clip_local(name, ct)
                    ang = math.degrees(math.acos(max(-1, min(1, (np.trace(g.T @ c) - 1) / 2))))
                    rot.append('%s %.0f' % (name.split('[')[-1].strip(']') if '[' in name else name, ang))
            print('   %.3f  %s  | local rot off: %s' % (ct, '  '.join(row), ', '.join(rot)))


if __name__ == '__main__':
    main()
