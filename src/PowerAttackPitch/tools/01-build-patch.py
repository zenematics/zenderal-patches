"""Build the Pandora-native patch `zpapitch`: Precision's upper-body pitch also on power attacks.

Precision (ersh1, 2.0.6) bends the attacker's spine (XPMSE bones 24-26 = NPC Spine/Spine1/Spine2) toward the
target during attacks: the DLL writes graph variable Collision_PitchMult (the player: -angle.x in degrees, which TDM's
target lock aims torso to torso; an NPC: its torso to its combat target's torso), and its Nemesis patch `colis` twists
the spine by it, weighted by Collision_Weight. That weight only ramps in (event-driven modifiers in Precision_Mods,
appended to 0_master's RootModifierList #2517) on attackStart, the left-hand / dual-wield / sprint / H2H attack starts,
blockStart and bashStart - none of the 23 power-attack start events. So a power attack that does not follow a
light attack swings at full standing height and misses short enemies.

This patch adds one event-driven modifier per power-attack start event, each running a copy of Precision's own
ramp-in expression until attackStop (Precision's own Pitch_Adjustment_Stop_EDM ramps it back out on attackStop, as
for light attacks). New objects only, appended to #2517/modifiers; no Precision object is referenced or changed.

Everything copied from Precision is read from its installed Nemesis files and asserted, so a Precision update that
changes the mechanism fails here instead of building a dead patch.

Usage:  python 01-build-patch.py [<modlist root>]      (modlist root defaults to E:/Zenderal)
Writes: src/PowerAttackPitch/Pandora_Engine/mod/zpapitch/patches/0_master.xml
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'Pandora_Engine', 'mod', 'zpapitch', 'patches', '0_master.xml')
CODE = 'zpapitch'

# Every power-attack start event in vanilla 0_master (asserted against Precision's copy of the vanilla event list
# below: every event name starting with "attackPower", case-insensitive).
POWER_EVENTS = [
    'attackPowerStartBackward', 'attackPowerStartForward', 'attackPowerStartLeft', 'attackPowerStartRight',
    'attackPowerStartInPlace', 'AttackPowerDirectionalStart',
    'attackPowerStartInPlaceLeftHand', 'attackPowerStartForwardLeftHand', 'attackPowerStartRightLeftHand',
    'attackPowerStartLeftLeftHand', 'attackPowerStartBackLeftHand',
    'attackPowerStartDualWield',
    'attackPowerStartForwardH2HRightHand', 'attackPowerStartForwardH2HLeftHand', 'attackPowerStartH2HCombo',
    'AttackPower2HMForwardSprint', 'AttackPower2HWForwardSprint', 'attackPowerStart_Sprint',
    'attackPowerStart_SprintLeftHand', 'attackPowerStart_2HWSprint', 'attackPowerStart_2HMSprint',
    'attackPowerStart_MC_1HMRight', 'attackPowerStart_MC_1HMLeft',
]
STOP_EVENT = 'attackStop'


def fail(msg):
    raise SystemExit('FAILED: ' + msg)


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def param(obj, name):
    m = re.search(r'<hkparam name="%s">([^<]*)</hkparam>' % re.escape(name), obj)
    return m.group(1).strip() if m else None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
    colis = os.path.join(root, 'mods', 'Precision', 'Nemesis_Engine', 'mod', 'colis', '0_master')
    if not os.path.isdir(colis):
        fail('Precision Nemesis patch not found: ' + colis)

    # Vanilla event list = #0106 with Precision's own insertions removed.
    t = read(os.path.join(colis, '#0106.txt'))
    t = re.sub(r'<!-- MOD_CODE ~colis~ OPEN -->.*?<!-- CLOSE -->', '', t, flags=re.S)
    m = re.search(r'<hkparam name="eventNames" numelements="(\d+)">(.*?)</hkparam>', t, re.S)
    events = re.findall(r'<hkcstring>(.*?)</hkcstring>', m.group(2))
    if len(events) != int(m.group(1)):
        fail('event list length %d != declared %s' % (len(events), m.group(1)))
    power = [e for e in events if e.lower().startswith('attackpower')]
    if sorted(power) != sorted(POWER_EVENTS):
        fail('vanilla power-attack events differ from POWER_EVENTS:\n  missing %s\n  extra %s'
             % (sorted(set(power) - set(POWER_EVENTS)), sorted(set(POWER_EVENTS) - set(power))))
    if STOP_EVENT not in events:
        fail('no attackStop event')

    objs = {}
    for f in os.listdir(colis):
        if f.startswith('#colis$'):
            objs[f[:-4]] = read(os.path.join(colis, f))
    by_name = {param(o, 'name'): (k, o) for k, o in objs.items() if param(o, 'name')}

    # Precision's light-attack ramp: Pitch_Adjustment_Melee_Start_EDM -> list -> EEM -> expression.
    k, edm = by_name['Pitch_Adjustment_Melee_Start_EDM']
    if 'hkbEventDrivenModifier' not in edm:
        fail(k + ' is not an event-driven modifier')
    if events[int(param(edm, 'activateEventId'))] != 'attackStart' or \
            events[int(param(edm, 'deactivateEventId'))] != STOP_EVENT:
        fail('Melee_Start_EDM no longer runs attackStart -> attackStop')
    lst = objs[param(edm, 'modifier')]
    mods = re.search(r'<hkparam name="modifiers" numelements="1">\s*(\S+)\s*</hkparam>', lst).group(1)
    eem = objs[mods]
    if 'hkbEvaluateExpressionModifier' not in eem:
        fail('ramp list does not hold an expression modifier')
    arr = objs[param(eem, 'expressions')]
    exprs = re.findall(r'<hkparam name="expression">([^<]*)</hkparam>', arr)
    if len(exprs) != 1 or 'Collision_Weight' not in exprs[0] or 'TimeDelta' not in exprs[0]:
        fail('unexpected ramp expression(s): %r' % exprs)
    ramp = exprs[0]

    # No power-attack event may already start Precision's ramp (then this patch is not needed for it).
    started = set()
    for name, (k, o) in by_name.items():
        if name.startswith('Pitch_Adjustment_') and name.endswith('_Start_EDM'):
            a = param(o, 'activateEventId')
            started.add(events[int(a)] if a.isdigit() else a)
    overlap = started & set(POWER_EVENTS)
    if overlap:
        fail('Precision already ramps on %s: rebuild POWER_EVENTS' % sorted(overlap))

    # Precision_Mods must still sit in RootModifierList #2517, which we append to.
    r = read(os.path.join(colis, '#2517.txt'))
    if param(r, 'name') != 'RootModifierList' or by_name['Precision_Mods'][0] not in r:
        fail('#2517 is no longer RootModifierList holding Precision_Mods')

    # Emit.
    n = 0
    out = []

    def obj(cls, sig, body):
        nonlocal n
        name = '#%s$%d' % (CODE, n)
        n += 1
        out.append('\t\t<hkobject name="%s" class="%s" signature="%s">\n%s\t\t</hkobject>\n' % (name, cls, sig, body))
        return name

    def p(name, value):
        return '\t\t\t<hkparam name="%s">%s</hkparam>\n' % (name, value)

    arr_name = obj('hkbExpressionDataArray', '0x4b9ee1a2',
                   '\t\t\t<hkparam name="expressionsData" numelements="1">\n\t\t\t\t<hkobject>\n'
                   '\t\t\t\t\t<hkparam name="expression">%s</hkparam>\n'
                   '\t\t\t\t\t<hkparam name="assignmentVariableIndex">-1</hkparam>\n'
                   '\t\t\t\t\t<hkparam name="assignmentEventIndex">-1</hkparam>\n'
                   '\t\t\t\t\t<hkparam name="eventMode">EVENT_MODE_SEND_ONCE</hkparam>\n'
                   '\t\t\t\t</hkobject>\n\t\t\t</hkparam>\n' % ramp)
    eem_name = obj('hkbEvaluateExpressionModifier', '0xf900f6be',
                   p('variableBindingSet', 'null') + p('userData', '2') + p('name', 'ZP_PowerPitch_Start_EEM')
                   + p('enable', 'true') + p('expressions', arr_name))
    ramp_list = obj('hkbModifierList', '0xa4180ca1',
                    p('variableBindingSet', 'null') + p('userData', '1') + p('name', 'ZP_PowerPitch_Start_Mods')
                    + p('enable', 'true')
                    + '\t\t\t<hkparam name="modifiers" numelements="1">\n\t\t\t\t%s\n\t\t\t</hkparam>\n' % eem_name)
    edms = []
    for ev in POWER_EVENTS:
        edms.append(obj('hkbEventDrivenModifier', '0x7ed3f44e',
                        p('variableBindingSet', 'null') + p('userData', '1') + p('name', 'ZP_PowerPitch_%s_EDM' % ev)
                        + p('enable', 'true') + p('modifier', ramp_list)
                        + p('activateEventId', '$eventID[%s]$' % ev)
                        + p('deactivateEventId', '$eventID[%s]$' % STOP_EVENT)
                        + p('activeByDefault', 'false')))
    top = obj('hkbModifierList', '0xa4180ca1',
              p('variableBindingSet', 'null') + p('userData', '1') + p('name', 'ZP_PowerPitch_Mods') + p('enable', 'true')
              + '\t\t\t<hkparam name="modifiers" numelements="%d">\n\t\t\t\t%s\n\t\t\t</hkparam>\n'
              % (len(edms), ' '.join(edms)))

    xml = ('<patch>\n'
           '\t<!-- GENERATED by src/PowerAttackPitch/tools/01-build-patch.py - do not hand-edit.\n'
           '\t     Zenderal - Power Attack Pitch (arch-docs/patches/PowerAttackPitch.md). Precision bends the spine toward the\n'
           '\t     target during attacks (Collision_PitchMult, weighted by Collision_Weight), but ramps that weight in only on\n'
           '\t     light-attack, block and bash starts. These modifiers run Precision\'s own ramp-in expression from every\n'
           '\t     power-attack start until attackStop; Precision\'s Pitch_Adjustment_Stop_EDM ramps it out on attackStop. -->\n'
           '\t<Append path="">\n' + ''.join(out) + '\t</Append>\n'
           '\t<Append path="#2517/modifiers">%s</Append>\n'
           '</patch>\n' % top)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml)
    check(xml, objs)
    print('ramp expression: %s' % ramp)
    print('Precision already ramps on: %s' % ', '.join(sorted(started)))
    print('wrote %s: %d objects, %d power-attack events' % (os.path.normpath(OUT), n, len(edms)))


def check(xml, precision_objs):
    """Well-formed; every #zpapitch$N reference defined and used; each new object has exactly the fields, in the
    same order, as Precision's objects of the same class (which Pandora already builds into this graph)."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml)
    new = root.find('Append').findall('hkobject')
    defined = {o.get('name') for o in new}
    refs = set(re.findall(r'#%s\$\d+' % CODE, xml))
    if refs != defined:
        fail('references %s vs defined %s' % (sorted(refs - defined), sorted(defined - refs)))

    def fields(elem):
        return [c.get('name') for c in elem if c.tag == 'hkparam']

    shapes = {}
    for k, text in precision_objs.items():
        o = ET.fromstring(text.strip())
        shapes.setdefault(o.get('class'), fields(o))
    for o in new:
        want = shapes.get(o.get('class'))
        if want is None:
            fail('Precision has no %s to compare against' % o.get('class'))
        if fields(o) != want:
            fail('%s fields %s != Precision %s' % (o.get('name'), fields(o), want))
    print('check: %d objects well-formed, references closed, fields match Precision\'s' % len(new))


if __name__ == '__main__':
    main()
