"""Check patches/firstperson~1hm_behavior.xml against Pandora's first-person 1hm_behavior template (hkxconv --meta XML)
and simulate it on every first-person fist set's light punches.

  - every template node the patch names exists with the expected class / role (the two transition arrays belong to
    1HM_AttackBehavior #4333's AttackRight_State and AttackLeft_State);
  - every $eventID[...]$ is a template event, every expression variable a template variable, every toStateId a
    state of #4333;
  - for each fist set's right and left hook (clip annotations, or the vanilla clip generator triggers when the set's
    submod keeps them), the chain transition's trigger interval opens and its initiate interval opens before attackStop.

Usage:  python 01-verify.py <template XML from: hkxconv --meta "<Pandora>/Pandora_Engine/Skyrim/Template/actors/
        character/_1stperson/behaviors/1hm_behavior.hkx" out.xml>
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.join(HERE, '..', 'Pandora_Engine', 'mod', 'zfistcombo', 'patches', 'firstperson~1hm_behavior.xml')
sys.path.insert(0, os.path.join(HERE, '..', '..', 'FHRFirstPerson', 'tools'))
import hkx_annotate  # noqa: E402

MODS = 'E:/Zenderal/mods'
# FirstPersonUnarmedStances' marked copies of some clips (CLIP_MARKERS) ship in Patch Collection, which outranks the sets
OVERLAY = f'{MODS}/Zenderal - Patch Collection'
OAR = 'meshes/actors/character/_1stperson/animations/OpenAnimationReplacer'
# set -> (folder of its light punches, whether its submod keeps the vanilla clip generator triggers)
SETS = {
    'SIGMA (no stance)': (f'{MODS}/SIGMA - Fisting animations - 1st person/{OAR}/Sigma - fists/h_a', False),
    'JellyFish (F1)': (f'{MODS}/JellyFishFP (un)armed (1st person animations series)/{OAR}/JFFPU/unrmd', False),
    'CFPAO (F2)': (f'{MODS}/Comprehensive First Person Animation Overhaul - CFPAO/{OAR}/CFPAO/UnarmedDefaultH', True),
    'Boxing (F3)': (f'{MODS}/First-Person Boxing Animation/{OAR}/First-Person Boxing Animation/First-Person Boxing', True),
}


def main():
    root = ET.parse(sys.argv[1]).getroot()
    objs = {o.get('name'): o for o in root.iter('hkobject') if o.get('name')}

    def param(o, n):
        for p in o.findall('hkparam'):
            if p.get('name') == n:
                return p

    sd = objs['#0085']
    events = [e.text for e in param(sd, 'eventNames')]
    variables = [e.text for e in param(sd, 'variableNames')]
    ev_lower = {e.lower(): e for e in events}
    sm = objs['#4333']
    assert param(sm, 'name').text == '1HM_AttackBehavior'
    states = {}
    for s in param(sm, 'states').text.split():
        so = objs[s]
        states[int(param(so, 'stateId').text)] = (param(so, 'name').text, param(so, 'transitions').text)
    problems = []
    want = {'#4328': 'AttackRight_State', '#3425': 'AttackLeft_State'}
    for node, state in want.items():
        if not any(n == state and t == node for n, t in states.values()):
            problems.append(f'{node} is not {state}\'s transition array')
    for node, cls in (('#2590', 'hkbBlendingTransitionEffect'), ('#2593', 'hkbBlendingTransitionEffect'),
                      ('#3429', 'hkbExpressionCondition')):
        if node not in objs or objs[node].get('class') != cls:
            problems.append(f'{node} is not a {cls}')
    text = open(PATCH, encoding='utf-8').read()
    for name in re.findall(r'\$eventID\[([^\]]+)\]\$', text):
        if name not in events:
            problems.append(f'event {name} not in the template')
    for expr in re.findall(r'name="expression">([^<]+)<', text):
        for var in re.findall(r'[A-Za-z_]\w*', expr.replace('&amp;', '')):
            if var not in variables:
                problems.append(f'variable {var} not in the template')
    for sid in re.findall(r'name="toStateId">(\d+)<', text):
        if int(sid) not in states:
            problems.append(f'toStateId {sid} not a state of #4333')
    for ref in set(re.findall(r'>(#\d{4})<', text)) - set(want) - {'#2590', '#2593', '#3429'}:
        problems.append(f'unexpected template reference {ref}')

    # vanilla clip generator triggers of the fist hooks (H2H_RightHook / H2H_LeftHook), times from clip end if < 0
    vanilla = {}
    for o in objs.values():
        if o.get('class') == 'hkbClipGenerator' and param(o, 'name').text in ('H2H_RightHook', 'H2H_LeftHook'):
            trs = []
            tref = param(o, 'triggers').text
            for t in param(objs[tref], 'triggers').findall('hkobject'):
                eid = int(param(param(t, 'event').find('hkobject'), 'id').text)
                trs.append((float(param(t, 'localTime').text), events[eid]))
            vanilla['right' if 'Right' in param(o, 'name').text else 'left'] = trs
    chain = {'right': ('preHitFrame', 'AttackWinStart'), 'left': ('preHitFrame', 'AttackWinStartLeft')}
    for name, (folder, keeps_vanilla) in SETS.items():
        for side in ('right', 'left'):
            sub = os.path.join(folder, f'_variants_h2h_attack{side}')
            clips = [os.path.join(sub, f) for f in sorted(os.listdir(sub))] if os.path.isdir(sub) else \
                [os.path.join(folder, f'h2h_attack{side}.hkx')]
            for clip in clips:
                rel = os.path.relpath(clip, MODS).replace(os.sep, '/').split('/', 1)[1]
                winner = os.path.join(OVERLAY, rel)
                clip = winner if os.path.exists(winner) else clip
                dur, anns = hkx_annotate.read(clip)
                evs = [(t, ev_lower.get(x.lower(), x)) for t, x in anns]
                if keeps_vanilla:
                    evs += [(t if t >= 0 else dur + t, e) for t, e in vanilla[side] if (t if t >= 0 else dur + t) <= dur]
                times = {}
                for t, e in sorted(evs):
                    times.setdefault(e, t)
                trig, init = chain[side]
                stop = times.get('attackStop')
                ok = trig in times and init in times and stop is not None and times[trig] < stop and times[init] < stop
                print(f'{name:<18} {side:<5} {os.path.basename(clip):<16} {dur:.2f}s  click from {times.get(trig)}, '
                      f'next punch from {times.get(init)}, until attackStop {stop}  -> {"chains" if ok else "NO CHAIN"}')
    for p in problems:
        print('PROBLEM', p)
    print(f'{len(problems)} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
