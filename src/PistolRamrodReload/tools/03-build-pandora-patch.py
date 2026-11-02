"""Write the Pandora-native patch `zpistolreload` (src/PistolRamrodReload/Pandora_Engine/mod/zpistolreload/patches).

Why (ZenBoneTrace, 2026-11-01): with a pistol (a staff) in the left hand and the right hand empty, the third-person
graph is in `1hm_behavior` -> `1HM_Readied_Staff_State` -> `MLh_1HM_Idle_Blend`, a blend of
  - `1HM_MagicBFR` (the magic graph: our shot clip) with bone weights that give it everything but the right arm
    (right clavicle, upper arm and their twists 0.5; right forearm, hand, fingers, twists, AnimObjectR 0), and
  - the clip `1HM_Idle` (Goetia Enchanted Magic Staves' unarmed + staff idle wins) on the complement,
so the free hand keeps its own idle while the left hand casts. The traced right arm matched exactly that: forearm and
hand from Goetia's idle (0.1 deg), upper arm a 50/50 blend (fit residual 1-3 deg). Our reload could not move the right
forearm or hand.

The patch, applied by Pandora:
  1hm_behavior: a new REAL variable `fZenPistolRightArmIdle` (default 1.0) bound to the `1HM_Idle` child's weight, and
                the magic child's zero right-arm weights raised to RIGHT_ARM_EPSILON. With the variable at 1 the free
                hand looks as before (1% of the magic graph mixed into it); at 0 the magic graph (our clip) owns the
                whole right arm. `ZP_PistolReloadArmScript` sets it to 0 for a reload.
  0_master:     the same variable, so the engine finds it by name from Papyrus (sub-behaviour variables link to the
                root's by name); and the right hand's case (right_hand_blend): a staff in the right hand with the left
                hand empty plays H2H_MRh_Idle_BoneSwitch_3rdP, whose LeftArm mask takes 1HM_Idle whole. Its selector
                slot gets a blender with the same epsilon trick, the idle's weight bound to fZenPistolLeftArmIdle.
  magicbehavior: `AnimObjLoad`, `AnimObjDraw`, `AnimObjectUnequip`, so the clip's prop annotations fire (the 1hm graphs
                list them; the magic graph did not), and the loading sounds' `SoundPlay.<SNDR>` (SOUND_EVENTS, in
                0_master too, both views).

First person (2026-11-02): the first-person project's own graphs (`_1stperson/behaviors`, Pandora's pack files
`firstperson~<name>`, so the patch files carry that prefix) have the same shape with binary masks:
  firstperson~1hm_behavior: `1stP_MLh_1HM_Idle_Blend` = the magic graph (0 on the RightArm bones) + `1HM_1stPUpperBody`
                (the first-person upper-body locomotion, its bone weights bound to the RightArm character property).
                The latter's binding set gets a second binding, its weight to fZenPistolRightArmIdle; the magic child's
                zero weights become RIGHT_ARM_EPSILON.
  firstperson~0_master: `H2H_MRh_IdleMSG`[1] = `H2H_MRh_Idle_BoneSwitch_1stP` (LeftArm mask -> H2H_MRh_1stPUpperBody):
                the same blender as the third person's, in slot 1.
  firstperson~magicbehavior: the prop events.

Dual wielding (2026-11-02): two staves take `LeftHandMagicCast_MSG` (standing, moving and sneaking alike) ->
`LHStaff_RHMagicCast_MSG`[8] = `DualStaff_Blend`, a parametric blend on `CastBlendDamped` (-1 the left hand's graph
with the right arm on the right hand's, 0 both by arm, +1 the mirror), for a cast from either hand. The slot gets a
parametric blender on the new variable fZenPistolDualReload (default 0): -1 `MLh_ReadyCast_Behavior`, 0 the vanilla
`DualStaff_Blend`, +1 `MRh_ReadyCast_Behavior`, every child kept running (so the idle hand's graph never misses an
event); ZP_PistolReloadArmScript sets -1 / +1 for a dual reload, so the firing gun's clip owns the whole body. Same
template IDs in both views (dual_wrapper asserts the shape). The variable is in magicbehavior and 0_master.
And 0_master's root (traced in game 2026-11-02: the tucked gun never left the hand): a hand holding a staff that is not
casting gets its `RHStaffOnly` / `LHStaffOnly` bones (its attach node `Weapon` / `Shield` and magic node) from its
staff idle, above every behaviour (`RHStaff_BoneSwitchMSG` / `LHStaff_BoneSwitchMSG` on IsCastingRight / Left, slot 0
= that bone switch, slot 1 = the same graph without it). Slot 0 becomes a parametric blend on fZenPistolDualReload
(root_staff_release): the right hand's override is off at -1 (the left gun reloading, the right hand tucking), the
left hand's at +1. One child active at a time (flags 16), as vanilla's own selector switches between the two.

Node IDs are the Pandora template's (converted with `--meta`). The script asserts the blend and both masks are the
ones measured, so a changed template fails here instead of silently patching the wrong node.

Usage (after converting Pandora's templates with src/EnderalPairedAnims/tools/hkxconv --meta; the character files are
the Pandora output's, plain):
  python src/PistolRamrodReload/tools/03-build-pandora-patch.py <1hm_behavior meta xml> <0_master meta xml>
         <magicbehavior meta xml> <defaultmale xml> <_1stperson 1hm_behavior meta xml> <_1stperson 0_master meta xml>
         <_1stperson magicbehavior meta xml> <_1stperson FirstPerson xml>
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'Pandora_Engine', 'mod', 'zpistolreload', 'patches')
VAR = 'fZenPistolRightArmIdle'      # left-hand pistol: the free RIGHT arm's idle weight (1hm_behavior)
VAR_LEFT = 'fZenPistolLeftArmIdle'  # right-hand pistol: the free LEFT arm's idle weight (0_master)
VAR_DUAL = 'fZenPistolDualReload'   # two pistols: -1 the left gun's clip owns the body, +1 the right's, 0 vanilla
VAR_STOW = 'fZenPistolLeftStow'     # right-hand pistol, melee weapon / shield left: 1 vanilla, 0 the clip owns that arm
# reload asked for (fire pressed on the empty gun), per hand: 1 for the cast ZP_PistolReloadArmScript starts, read by the
# reload clips' OAR conditions only (tools/01 REQUEST); a shot leaves them 0 and plays Loop's shot alone
VAR_REQ = ('fZenPistolReloadL', 'fZenPistolReloadR')
ONE = 1065353216            # 1.0f as the int Havok stores REAL variables in wordVariableValues
RIGHT_ARM_EPSILON = 0.01
MOD = 'zpistolreload'


def objects(path):
    x = open(path, encoding='utf-8').read()
    objs = {m.group(1): m.group(0) for m in re.finditer(r'<hkobject name="(#\d+)" class="[^"]+".*?\n    </hkobject>', x, re.S)}
    cls = {k: re.search(r'class="([^"]+)"', v).group(1) for k, v in objs.items()}
    return objs, cls


def name(o):
    m = re.search(r'<hkparam name="name">(.*?)</hkparam>', o)
    return m.group(1) if m else ''


def one_of(cls, want):
    ks = [k for k, c in cls.items() if c == want]
    if len(ks) != 1:
        sys.exit('expected one %s, found %s' % (want, ks))
    return ks[0]


def weights(o):
    return [float(v) for v in re.findall(r'-?[\d.]+', re.search(r'name="boneWeights" numelements="\d+">(.*?)</hkparam>', o, re.S).group(1))]


def variable_appends(objs, cls, names=(VAR,), values=None):
    """REAL variables `names`, each with its default (Havok's int bits; 1.0 unless `values` says)."""
    values = values or [ONE] * len(names)
    sd, vv, gd = (one_of(cls, c) for c in ('hkbBehaviorGraphStringData', 'hkbVariableValueSet', 'hkbBehaviorGraphData'))
    for v in names:
        if '<hkcstring>%s</hkcstring>' % v in objs[sd]:
            sys.exit('%s already has %s' % (sd, v))
    info = '\n'.join(['\t\t<hkobject>', '\t\t\t<hkparam name="role">', '\t\t\t\t<hkobject>',
                      '\t\t\t\t\t<hkparam name="role">ROLE_DEFAULT</hkparam>',
                      '\t\t\t\t\t<hkparam name="flags">FLAG_NONE</hkparam>', '\t\t\t\t</hkobject>', '\t\t\t</hkparam>',
                      '\t\t\t<hkparam name="type">VARIABLE_TYPE_REAL</hkparam>', '\t\t</hkobject>'])
    value = lambda v: '\n'.join(['\t\t<hkobject>', '\t\t\t<hkparam name="value">%d</hkparam>' % v, '\t\t</hkobject>'])  # noqa: E731
    return '\n'.join(['\t<Append path="%s/variableNames">' % sd] + ['\t\t<hkcstring>%s</hkcstring>' % v for v in names] +
                     ['\t</Append>', '\t<Append path="%s/variableInfos">' % gd] + [info] * len(names) +
                     ['\t</Append>', '\t<Append path="%s/wordVariableValues">' % vv] + [value(v) for v in values] +
                     ['\t</Append>'])


def binding_set(node, var):
    return '\n'.join([
        '\t\t<hkobject name="%s" class="hkbVariableBindingSet" signature="0x338ad4ff">' % node,
        '\t\t\t<hkparam name="bindings" numelements="1">', '\t\t\t\t<hkobject>',
        '\t\t\t\t\t<hkparam name="memberPath">weight</hkparam>',
        '\t\t\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % var,
        '\t\t\t\t\t<hkparam name="bitIndex">-1</hkparam>',
        '\t\t\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>', '\t\t\t\t</hkobject>', '\t\t\t</hkparam>',
        '\t\t\t<hkparam name="indexOfBindingToEnable">-1</hkparam>', '\t\t</hkobject>'])


def blend_child(node, binding, generator, weights, world):
    return '\n'.join([
        '\t\t<hkobject name="%s" class="hkbBlenderGeneratorChild" signature="0xe2b384b0">' % node,
        '\t\t\t<hkparam name="variableBindingSet">%s</hkparam>' % binding,
        '\t\t\t<hkparam name="generator">%s</hkparam>' % generator,
        '\t\t\t<hkparam name="boneWeights">%s</hkparam>' % weights,
        '\t\t\t<hkparam name="weight">1.000000</hkparam>',
        '\t\t\t<hkparam name="worldFromModelWeight">%.6f</hkparam>' % world, '\t\t</hkobject>'])


def bone_weights(node, values):
    return '\n'.join([
        '\t\t<hkobject name="%s" class="hkbBoneWeightArray" signature="0xcd902b77">' % node,
        '\t\t\t<hkparam name="variableBindingSet">null</hkparam>',
        '\t\t\t<hkparam name="boneWeights" numelements="%d">%s</hkparam>' % (len(values), ' '.join('%.6f' % v for v in values)),
        '\t\t</hkobject>'])


def right_hand_blend(objs, cls, master_xml, character_xml, slot=0, switch_name='H2H_MRh_Idle_BoneSwitch_3rdP',
                     idle_name='1HM_Idle', first=1, blend_name='ZenPistol_H2H_MRh_Idle_Blend'):
    """0_master, a staff in the RIGHT hand and the left hand empty: `H2H_MRh_IdleMSG` (i1stPerson) [0] =
    `H2H_MRh_Idle_BoneSwitch_3rdP`, the magic graph everywhere but the `LeftArm` mask, which plays `1HM_Idle`. Same
    problem as the left hand's, mirrored, but a bone switch has no weight to bind, and referencing the magic graph from
    a second parent would share a live node. So the selector's 3rd-person slot gets a new blender built like vanilla's
    MLh_1HM_Idle_Blend: the magic graph (weights 1, the LeftArm bones RIGHT_ARM_EPSILON) and 1HM_Idle (the LeftArm
    bones 1, its weight bound to VAR_LEFT). The first-person graph: slot 1, its `H2H_MRh_Idle_BoneSwitch_1stP` with
    `H2H_MRh_1stPUpperBody` on the mask; new nodes numbered from `first`. Returns the patch body."""
    sel = [k for k in objs if cls[k] == 'hkbManualSelectorGenerator' and name(objs[k]) == 'H2H_MRh_IdleMSG']
    if len(sel) != 1:
        sys.exit('H2H_MRh_IdleMSG not found once: %s' % sel)
    sel = sel[0]
    gens = re.search(r'name="generators" numelements="2">(.*?)</hkparam>', objs[sel], re.S).group(1).split()
    switch = gens[slot]
    if cls[switch] != 'BSBoneSwitchGenerator' or name(objs[switch]) != switch_name:
        sys.exit('%s[%d] is not %s: %s' % (sel, slot, switch_name, switch))
    magic = re.search(r'pDefaultGenerator">(#\d+)', objs[switch]).group(1)
    child = re.search(r'ChildrenA" numelements="1">(#\d+)', objs[switch]).group(1)
    idle = re.search(r'pGenerator">(#\d+)', objs[child]).group(1)
    if name(objs[magic]) != '1HM_MagicBFR' or name(objs[idle]) != idle_name:
        sys.exit('unexpected bone switch: default %s, child %s' % (name(objs[magic]), name(objs[idle])))
    x = open(master_xml, encoding='utf-8').read()
    props = re.findall(r'<hkcstring>(.*?)</hkcstring>', re.search(r'name="characterPropertyNames" numelements="\d+">(.*?)</hkparam>', x, re.S).group(1))
    bind = re.search(r'<hkparam name="variableIndex">(\d+)</hkparam>', objs[re.search(r'variableBindingSet">(#\d+)', objs[child]).group(1)])
    if props[int(bind.group(1))] != 'LeftArm':
        sys.exit('the child mask is %s, not LeftArm' % props[int(bind.group(1))])
    cobjs, ccls = objects(character_xml)
    cx = open(character_xml, encoding='utf-8').read()
    cnames = re.findall(r'<hkcstring>(.*?)</hkcstring>', re.search(r'name="characterPropertyNames" numelements="\d+">(.*?)</hkparam>', cx, re.S).group(1))
    vs = cobjs[re.search(r'<hkparam name="characterPropertyValues">(#\d+)</hkparam>', cx).group(1)]
    variants = re.search(r'name="variantVariableValues" numelements="\d+">(.*?)</hkparam>', vs, re.S).group(1).split()
    words = re.findall(r'<hkparam name="value">(-?\d+)</hkparam>', re.search(r'name="wordVariableValues" numelements="\d+">(.*?)</hkparam>\s*<hkparam name="quadVariableValues"', vs, re.S).group(1))
    left = weights(cobjs[variants[int(words[cnames.index('LeftArm')])]])
    if not (left[28] == left[29] == left[38] == 1.0 and left[31] == 0.0):
        sys.exit('LeftArm mask unexpected: %s' % left[26:40])
    magic_w = [RIGHT_ARM_EPSILON if v > 0 else 1.0 for v in left]
    idle_w = [v for v in left]
    n = lambda i: '#%s$%d' % (MOD, first - 1 + i)  # noqa: E731
    new = list(gens)
    new[slot] = n(1)
    body = '\n'.join([
        '\t<Append path="">',
        '\t\t<hkobject name="%s" class="hkbBlenderGenerator" signature="0x22df7147">' % n(1),
        '\t\t\t<hkparam name="variableBindingSet">null</hkparam>', '\t\t\t<hkparam name="userData">0</hkparam>',
        '\t\t\t<hkparam name="name">%s</hkparam>' % blend_name,
        '\t\t\t<hkparam name="referencePoseWeightThreshold">0.000000</hkparam>',
        '\t\t\t<hkparam name="blendParameter">1.000000</hkparam>',
        '\t\t\t<hkparam name="minCyclicBlendParameter">0.000000</hkparam>',
        '\t\t\t<hkparam name="maxCyclicBlendParameter">1.000000</hkparam>',
        '\t\t\t<hkparam name="indexOfSyncMasterChild">0</hkparam>', '\t\t\t<hkparam name="flags">0</hkparam>',
        '\t\t\t<hkparam name="subtractLastChild">false</hkparam>',
        '\t\t\t<hkparam name="children" numelements="2">%s %s</hkparam>' % (n(2), n(3)), '\t\t</hkobject>',
        blend_child(n(2), 'null', magic, n(4), 1.0),
        blend_child(n(3), n(6), idle, n(5), 0.0),
        bone_weights(n(4), magic_w), bone_weights(n(5), idle_w),
        binding_set(n(6), VAR_LEFT),
        '\t</Append>',
        '\t<replace>',
        '\t\t<edit path="%s/generators">' % sel,
        '\t\t\t<hkparam name="generators" numelements="2">%s</hkparam>' % ' '.join(new),
        '\t\t</edit>',
        '\t</replace>'])
    return body, sel, switch


def left_hand_1p(objs, cls, hm_xml):
    """firstperson~1hm_behavior: `1stP_MLh_1HM_Idle_Blend`'s upper-body child keeps its RightArm-bound bone weights and
    gets its weight bound to VAR too; the magic child's RightArm zeros become RIGHT_ARM_EPSILON. Returns (body, notes)."""
    blend = [k for k in objs if cls[k] == 'hkbBlenderGenerator' and name(objs[k]) == '1stP_MLh_1HM_Idle_Blend']
    if len(blend) != 1:
        sys.exit('1stP_MLh_1HM_Idle_Blend not found once: %s' % blend)
    children = re.search(r'name="children" numelements="2">(.*?)</hkparam>', objs[blend[0]], re.S).group(1).split()
    by_gen = {}
    for ch in children:
        gen = re.search(r'name="generator">(#\d+)', objs[ch]).group(1)
        by_gen[name(objs[gen])] = (ch, re.search(r'name="boneWeights">(#\d+)', objs[ch]).group(1))
    if set(by_gen) != {'1HM_MagicBFR', '1HM_1stPUpperBody'}:
        sys.exit('unexpected first-person blend children: %s' % by_gen)
    body_child, _ = by_gen['1HM_1stPUpperBody']
    magic_child, magic_bw = by_gen['1HM_MagicBFR']
    bset = re.search(r'name="variableBindingSet">(#\d+)<', objs[body_child])
    if not bset:
        sys.exit('%s has no binding set (its RightArm mask binding was expected)' % body_child)
    bset = bset.group(1)
    x = open(hm_xml, encoding='utf-8').read()
    props = re.findall(r'<hkcstring>(.*?)</hkcstring>', re.search(r'name="characterPropertyNames" numelements="\d+">(.*?)</hkparam>', x, re.S).group(1))
    bound = re.findall(r'<hkparam name="memberPath">(.*?)</hkparam>\s*<hkparam name="variableIndex">(\d+)</hkparam>', objs[bset])
    if bound != [('boneWeights', bound[0][1])] or props[int(bound[0][1])] != 'RightArm' or 'BINDING_TYPE_CHARACTER_PROPERTY' not in objs[bset]:
        sys.exit('%s binds %s, not just boneWeights to RightArm' % (bset, bound))
    mw = weights(objs[magic_bw])
    right = [i for i, v in enumerate(mw) if v == 0.0]
    # the 1P skeleton: right clavicle 30, upper arm 31, forearm 32, hand 39; the left hand 38 stays the magic graph's
    if not (right[:4] == [30, 31, 32, 39] and mw[38] == 1.0 and len(right) == 27):
        sys.exit('the first-person magic mask is not the measured one: zeros at %s' % right)
    new = [RIGHT_ARM_EPSILON if v == 0.0 else v for v in mw]
    body = '\n'.join([
        variable_appends(objs, cls),
        '\t<Append path="%s/bindings">' % bset,
        '\t\t<hkobject>',
        '\t\t\t<hkparam name="memberPath">weight</hkparam>',
        '\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % VAR,
        '\t\t\t<hkparam name="bitIndex">-1</hkparam>',
        '\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>',
        '\t\t</hkobject>',
        '\t</Append>',
        '\t<replace>',
        '\t\t<edit path="%s/boneWeights">' % magic_bw,
        '\t\t\t<hkparam name="boneWeights" numelements="%d">%s</hkparam>' % (len(new), ' '.join('%.6f' % v for v in new)),
        '\t\t</edit>',
        '\t</replace>'])
    return body, (body_child, bset, magic_bw, right)


def dual_wrapper(objs, cls, first):
    """magicbehavior: `LHStaff_RHMagicCast_MSG`[8] (`DualStaff_Blend`) inside a parametric blender on VAR_DUAL: -1 the
    left hand's graph, 0 the vanilla blend, +1 the right hand's; flags 16 (parametric) | 8 (children at weight 0 keep
    running). New nodes numbered from `first`. Returns the patch body."""
    sel = [k for k in objs if cls[k] == 'hkbManualSelectorGenerator' and name(objs[k]) == 'LHStaff_RHMagicCast_MSG']
    if len(sel) != 1:
        sys.exit('LHStaff_RHMagicCast_MSG not found once: %s' % sel)
    sel = sel[0]
    gens = re.search(r'name="generators" numelements="(\d+)">(.*?)</hkparam>', objs[sel], re.S)
    gens = gens.group(2).split()
    dual = gens[8]
    if name(objs[dual]) != 'DualStaff_Blend' or len(gens) != 10:
        sys.exit('%s[8] is not DualStaff_Blend: %s' % (sel, gens))
    left, right = gens[0], None
    for k in objs:
        if name(objs[k]) == 'MRh_ReadyCast_Behavior' and cls[k] == 'hkbStateMachine':
            right = k
    if name(objs[left]) != 'MLh_ReadyCast_Behavior' or not right:
        sys.exit('the hands\' graphs not found: %s %s' % (left, right))
    if 'blendParameter</hkparam>' not in objs[re.search(r'variableBindingSet">(#\d+)', objs[dual]).group(1)]:
        sys.exit('DualStaff_Blend is not bound on its blendParameter')
    n = lambda i: '#%s$%d' % (MOD, first - 1 + i)  # noqa: E731
    new = list(gens)
    new[8] = n(1)
    child = lambda node, gen, w: '\n'.join([  # noqa: E731
        '\t\t<hkobject name="%s" class="hkbBlenderGeneratorChild" signature="0xe2b384b0">' % node,
        '\t\t\t<hkparam name="variableBindingSet">null</hkparam>', '\t\t\t<hkparam name="generator">%s</hkparam>' % gen,
        '\t\t\t<hkparam name="boneWeights">null</hkparam>', '\t\t\t<hkparam name="weight">%.6f</hkparam>' % w,
        '\t\t\t<hkparam name="worldFromModelWeight">1.000000</hkparam>', '\t\t</hkobject>'])
    body = '\n'.join([
        '\t<Append path="">',
        '\t\t<hkobject name="%s" class="hkbBlenderGenerator" signature="0x22df7147">' % n(1),
        '\t\t\t<hkparam name="variableBindingSet">%s</hkparam>' % n(5), '\t\t\t<hkparam name="userData">0</hkparam>',
        '\t\t\t<hkparam name="name">ZenPistol_DualReload_Blend</hkparam>',
        '\t\t\t<hkparam name="referencePoseWeightThreshold">0.000000</hkparam>',
        '\t\t\t<hkparam name="blendParameter">0.000000</hkparam>',
        '\t\t\t<hkparam name="minCyclicBlendParameter">-1.000000</hkparam>',
        '\t\t\t<hkparam name="maxCyclicBlendParameter">1.000000</hkparam>',
        '\t\t\t<hkparam name="indexOfSyncMasterChild">-1</hkparam>', '\t\t\t<hkparam name="flags">24</hkparam>',
        '\t\t\t<hkparam name="subtractLastChild">false</hkparam>',
        '\t\t\t<hkparam name="children" numelements="3">%s %s %s</hkparam>' % (n(2), n(3), n(4)), '\t\t</hkobject>',
        child(n(2), left, -1.0), child(n(3), dual, 0.0), child(n(4), right, 1.0),
        '\t\t<hkobject name="%s" class="hkbVariableBindingSet" signature="0x338ad4ff">' % n(5),
        '\t\t\t<hkparam name="bindings" numelements="1">', '\t\t\t\t<hkobject>',
        '\t\t\t\t\t<hkparam name="memberPath">blendParameter</hkparam>',
        '\t\t\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % VAR_DUAL,
        '\t\t\t\t\t<hkparam name="bitIndex">-1</hkparam>',
        '\t\t\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>', '\t\t\t\t</hkobject>',
        '\t\t\t</hkparam>', '\t\t\t<hkparam name="indexOfBindingToEnable">-1</hkparam>', '\t\t</hkobject>',
        '\t</Append>',
        '\t<replace>',
        '\t\t<edit path="%s/generators">' % sel,
        '\t\t\t<hkparam name="generators" numelements="%d">%s</hkparam>' % (len(new), ' '.join(new)),
        '\t\t</edit>',
        '\t</replace>'])
    return body, (sel, dual, left, right)


def root_staff_release(objs, cls, first):
    """0_master: the staff-idle override on the tucking hand's attach node off during a two-pistol reload (module doc).
    New nodes numbered from `first`. Returns the patch body."""
    n = lambda i: '#%s$%d' % (MOD, first - 1 + i)  # noqa: E731
    parts, edits, node = [], [], 1
    for sel_name, switch_name, off_at in (('RHStaff_BoneSwitchMSG', 'RHStaff_BoneSwitchGen', -1.0),
                                          ('LHStaff_BoneSwitchMSG', 'LHStaff_BoneSwitchGen', 1.0)):
        sel = [k for k in objs if cls[k] == 'hkbManualSelectorGenerator' and name(objs[k]) == sel_name]
        if len(sel) != 1:
            sys.exit('%s not found once: %s' % (sel_name, sel))
        sel = sel[0]
        gens = re.search(r'name="generators" numelements="\d+">(.*?)</hkparam>', objs[sel], re.S).group(1).split()
        switch, plain = gens
        if name(objs[switch]) != switch_name or re.search(r'pDefaultGenerator">(#\d+)', objs[switch]).group(1) != plain:
            sys.exit('%s: slot 0 is not %s over slot 1 (%s)' % (sel, switch_name, gens))
        blend, c_sw, c_plain, bind = n(node), n(node + 1), n(node + 2), n(node + 3)
        node += 4
        child = lambda nd, gen, w: '\n'.join([  # noqa: E731
            '\t\t<hkobject name="%s" class="hkbBlenderGeneratorChild" signature="0xe2b384b0">' % nd,
            '\t\t\t<hkparam name="variableBindingSet">null</hkparam>', '\t\t\t<hkparam name="generator">%s</hkparam>' % gen,
            '\t\t\t<hkparam name="boneWeights">null</hkparam>', '\t\t\t<hkparam name="weight">%.6f</hkparam>' % w,
            '\t\t\t<hkparam name="worldFromModelWeight">1.000000</hkparam>', '\t\t</hkobject>'])
        kids = (child(c_plain, plain, off_at), child(c_sw, switch, 0.0))
        order = (c_plain, c_sw) if off_at < 0 else (c_sw, c_plain)
        parts += [
            '\t\t<hkobject name="%s" class="hkbBlenderGenerator" signature="0x22df7147">' % blend,
            '\t\t\t<hkparam name="variableBindingSet">%s</hkparam>' % bind, '\t\t\t<hkparam name="userData">0</hkparam>',
            '\t\t\t<hkparam name="name">ZenPistol_%s_Release</hkparam>' % switch_name,
            '\t\t\t<hkparam name="referencePoseWeightThreshold">0.000000</hkparam>',
            '\t\t\t<hkparam name="blendParameter">0.000000</hkparam>',
            '\t\t\t<hkparam name="minCyclicBlendParameter">-1.000000</hkparam>',
            '\t\t\t<hkparam name="maxCyclicBlendParameter">1.000000</hkparam>',
            '\t\t\t<hkparam name="indexOfSyncMasterChild">-1</hkparam>', '\t\t\t<hkparam name="flags">16</hkparam>',
            '\t\t\t<hkparam name="subtractLastChild">false</hkparam>',
            '\t\t\t<hkparam name="children" numelements="2">%s %s</hkparam>' % order, '\t\t</hkobject>',
            kids[0], kids[1],
            '\t\t<hkobject name="%s" class="hkbVariableBindingSet" signature="0x338ad4ff">' % bind,
            '\t\t\t<hkparam name="bindings" numelements="1">', '\t\t\t\t<hkobject>',
            '\t\t\t\t\t<hkparam name="memberPath">blendParameter</hkparam>',
            '\t\t\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % VAR_DUAL,
            '\t\t\t\t\t<hkparam name="bitIndex">-1</hkparam>',
            '\t\t\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>', '\t\t\t\t</hkobject>',
            '\t\t\t</hkparam>', '\t\t\t<hkparam name="indexOfBindingToEnable">-1</hkparam>', '\t\t</hkobject>']
        edits += ['\t\t<edit path="%s/generators">' % sel,
                  '\t\t\t<hkparam name="generators" numelements="2">%s %s</hkparam>' % (blend, plain), '\t\t</edit>']
    return '\n'.join(['\t<Append path="">'] + parts + ['\t</Append>', '\t<replace>'] + edits + ['\t</replace>'])


def param_blend(nodes, gens, var, label, flags):
    """A parametric blender (nodes: blender, one child per generator, binding set) on `var`: gens[k] at key k (0, 1),
    linear between. Returns the hkobjects."""
    blend, kids, bind = nodes[0], nodes[1:-1], nodes[-1]
    out = ['\t\t<hkobject name="%s" class="hkbBlenderGenerator" signature="0x22df7147">' % blend,
           '\t\t\t<hkparam name="variableBindingSet">%s</hkparam>' % bind, '\t\t\t<hkparam name="userData">0</hkparam>',
           '\t\t\t<hkparam name="name">%s</hkparam>' % label,
           '\t\t\t<hkparam name="referencePoseWeightThreshold">0.000000</hkparam>',
           '\t\t\t<hkparam name="blendParameter">1.000000</hkparam>',
           '\t\t\t<hkparam name="minCyclicBlendParameter">0.000000</hkparam>',
           '\t\t\t<hkparam name="maxCyclicBlendParameter">1.000000</hkparam>',
           '\t\t\t<hkparam name="indexOfSyncMasterChild">-1</hkparam>', '\t\t\t<hkparam name="flags">%d</hkparam>' % flags,
           '\t\t\t<hkparam name="subtractLastChild">false</hkparam>',
           '\t\t\t<hkparam name="children" numelements="%d">%s</hkparam>' % (len(kids), ' '.join(kids)), '\t\t</hkobject>']
    for k, (node, gen) in enumerate(zip(kids, gens)):
        out += ['\t\t<hkobject name="%s" class="hkbBlenderGeneratorChild" signature="0xe2b384b0">' % node,
                '\t\t\t<hkparam name="variableBindingSet">null</hkparam>',
                '\t\t\t<hkparam name="generator">%s</hkparam>' % gen,
                '\t\t\t<hkparam name="boneWeights">null</hkparam>', '\t\t\t<hkparam name="weight">%.6f</hkparam>' % k,
                '\t\t\t<hkparam name="worldFromModelWeight">1.000000</hkparam>', '\t\t</hkobject>']
    out += ['\t\t<hkobject name="%s" class="hkbVariableBindingSet" signature="0x338ad4ff">' % bind,
            '\t\t\t<hkparam name="bindings" numelements="1">', '\t\t\t\t<hkobject>',
            '\t\t\t\t\t<hkparam name="memberPath">blendParameter</hkparam>',
            '\t\t\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % var,
            '\t\t\t\t\t<hkparam name="bitIndex">-1</hkparam>',
            '\t\t\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>', '\t\t\t\t</hkobject>',
            '\t\t\t</hkparam>', '\t\t\t<hkparam name="indexOfBindingToEnable">-1</hkparam>', '\t\t</hkobject>']
    return out


def stow_release(objs, cls, first):
    """0_master, a right-hand pistol with a melee weapon or a shield in the left hand (2026-11-02): VAR_STOW (default
    1, ZP_PistolReloadArmScript fades it to 0 for a reload) hands the left arm and its item to the shot clip, which
    sheathes / slings the item for the ball and ramrod:
      - `MRh_1HM_IdleMSG` (i1stPerson) [0] `MRh_1HM_Idle_BoneSwitch_3rdP` (DW1HM1HMIdle on the LeftForearm mask) and
        [1] `MRh_1HM_Idle_BoneSwitch_1stP` (the first-person upper body on UpperBodyNoRightArm): each a blend of
        `1HM_MagicBFR` (at 0) and the bone switch (at 1);
      - `MRh_Shield_Ready`'s `MRh_Shd_Blend` (the shield pose over the magic graph): a blend of its `Magic_BFR` (at 0)
        and it (at 1);
      - the root's `DualWieldShieldBoneRootMSG` [1..4] (left one-handers): `DualWieldShieldBone_BoneSwitchGen` sets
        the grip node `Shield` from DW_ShieldAdjustment over every behaviour, so the weapon could not leave the hand
        (the two-pistol tuck's lesson): a blend of the plain graph (at 0) and the switch (at 1), one child at a time.
    Parametric, children kept running (flags 24) but the root's (16, as root_staff_release). New nodes from `first`.
    Returns the patch body."""
    n = lambda i: '#%s$%d' % (MOD, first - 1 + i)  # noqa: E731
    parts, edits, k = [], [], 1

    def one(sel_name):
        sel = [x for x in objs if cls[x] == 'hkbManualSelectorGenerator' and name(objs[x]) == sel_name]
        if len(sel) != 1:
            sys.exit('%s not found once: %s' % (sel_name, sel))
        return sel[0]
    sel = one('MRh_1HM_IdleMSG')
    gens = re.search(r'name="generators" numelements="2">(.*?)</hkparam>', objs[sel], re.S).group(1).split()
    new = list(gens)
    for slot, want in ((0, 'MRh_1HM_Idle_BoneSwitch_3rdP'), (1, 'MRh_1HM_Idle_BoneSwitch_1stP')):
        switch = gens[slot]
        magic = re.search(r'pDefaultGenerator">(#\d+)', objs[switch]).group(1)
        if name(objs[switch]) != want or name(objs[magic]) != '1HM_MagicBFR':
            sys.exit('%s[%d] is not %s over 1HM_MagicBFR' % (sel, slot, want))
        parts += param_blend([n(k), n(k + 1), n(k + 2), n(k + 3)], [magic, switch], VAR_STOW,
                             'ZenPistol_%s_Stow' % want, 24)
        new[slot] = n(k)
        k += 4
    edits += ['\t\t<edit path="%s/generators">' % sel,
              '\t\t\t<hkparam name="generators" numelements="2">%s</hkparam>' % ' '.join(new), '\t\t</edit>']
    shd = [x for x in objs if cls[x] == 'hkbBlenderGenerator' and name(objs[x]) == 'MRh_Shd_Blend']
    states = [x for x in objs if cls[x] == 'hkbStateMachineStateInfo' and name(objs[x]) == 'MRh_Shield_Ready']
    if len(shd) != 1 or len(states) != 1 or re.search(r'name="generator">(#\d+)', objs[states[0]]).group(1) != shd[0]:
        sys.exit('MRh_Shield_Ready -> MRh_Shd_Blend not found once: %s %s' % (shd, states))
    first_child = re.search(r'name="children" numelements="\d+">(#\d+)', objs[shd[0]]).group(1)
    magic = re.search(r'name="generator">(#\d+)', objs[first_child]).group(1)
    if name(objs[magic]) != 'Magic_BFR':
        sys.exit('MRh_Shd_Blend\'s first child is %s, not Magic_BFR' % name(objs[magic]))
    parts += param_blend([n(k), n(k + 1), n(k + 2), n(k + 3)], [magic, shd[0]], VAR_STOW, 'ZenPistol_MRh_Shd_Stow', 24)
    edits += ['\t\t<edit path="%s/generator">' % states[0],
              '\t\t\t<hkparam name="generator">%s</hkparam>' % n(k), '\t\t</edit>']
    k += 4
    sel = one('DualWieldShieldBoneRootMSG')
    gens = re.search(r'name="generators" numelements="(\d+)">(.*?)</hkparam>', objs[sel], re.S).group(2).split()
    switch = gens[1]
    plain = re.search(r'pDefaultGenerator">(#\d+)', objs[switch]).group(1)
    if name(objs[switch]) != 'DualWieldShieldBone_BoneSwitchGen' or gens[1:5] != [switch] * 4 or gens[0] != plain:
        sys.exit('%s[1..4] is not DualWieldShieldBone_BoneSwitchGen over [0]: %s' % (sel, gens))
    parts += param_blend([n(k), n(k + 1), n(k + 2), n(k + 3)], [plain, switch], VAR_STOW, 'ZenPistol_DW_Shield_Stow', 16)
    new = [n(k) if g == switch else g for g in gens]
    edits += ['\t\t<edit path="%s/generators">' % sel,
              '\t\t\t<hkparam name="generators" numelements="%d">%s</hkparam>' % (len(new), ' '.join(new)), '\t\t</edit>']
    return '\n'.join(['\t<Append path="">'] + parts + ['\t</Append>', '\t<replace>'] + edits + ['\t</replace>'])


LOADED_EVENTS = ['ZenPistolLoadedL', 'ZenPistolLoadedR']   # tools/01 LOADED: the Flintlock script loads the gun on them
# tools/01 SOUNDS, by their whole names as vanilla lists its own sound events (0_master: 70 `SoundPlay.<SNDR>`): the
# magic graph lists no bare `SoundPlay`, so the clip's loading sounds never fired (ZenBoneTrace, curator's test
# 2026-11-02: "no reload sounds"). A bare `SoundPlay` there would wake every mod's magic-clip sound annotation too.
SOUND_EVENTS = ['SoundPlay.ZEN_PistolLoadGun5', 'SoundPlay.ZEN_PistolLoadGun9']


def prop_events(objs, cls, events=None):
    """The clip annotations' events appended to the graph's event list (the prop events, the loaded ones and the
    loading sounds by default)."""
    sd, gd = one_of(cls, 'hkbBehaviorGraphStringData'), one_of(cls, 'hkbBehaviorGraphData')
    events = events or ['AnimObjLoad', 'AnimObjDraw', 'AnimObjectUnequip'] + LOADED_EVENTS + SOUND_EVENTS
    for e in events:
        if '<hkcstring>%s</hkcstring>' % e in objs[sd]:
            sys.exit('%s already lists %s' % (sd, e))
    return '\n'.join(['\t<Append path="%s/eventNames">' % sd] + ['\t\t<hkcstring>%s</hkcstring>' % e for e in events] +
                     ['\t</Append>', '\t<Append path="%s/eventInfos">' % gd] +
                     ['\t\t<hkobject>\n\t\t\t<hkparam name="flags">0</hkparam>\n\t\t</hkobject>'] * len(events) + ['\t</Append>'])


def write(fname, comment, body):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('<patch>\n\t<!-- %s -->\n%s\n</patch>\n' % (comment, body))
    print('wrote', os.path.normpath(os.path.join(OUT, fname)))


def main():
    if len(sys.argv) != 9:
        sys.exit(__doc__)
    hm, master, magic, character, hm1, master1, magic1, character1 = sys.argv[1:9]
    objs, cls = objects(hm)
    blend = [k for k in objs if cls[k] == 'hkbBlenderGenerator' and name(objs[k]) == 'MLh_1HM_Idle_Blend']
    if len(blend) != 1:
        sys.exit('MLh_1HM_Idle_Blend not found once: %s' % blend)
    children = re.search(r'name="children" numelements="2">(.*?)</hkparam>', objs[blend[0]], re.S).group(1).split()
    by_gen = {}
    for ch in children:
        gen = re.search(r'name="generator">(#\d+)', objs[ch]).group(1)
        by_gen[name(objs[gen])] = (ch, re.search(r'name="boneWeights">(#\d+)', objs[ch]).group(1))
    if set(by_gen) != {'1HM_MagicBFR', '1HM_Idle'}:
        sys.exit('unexpected blend children: %s' % by_gen)
    idle_child, idle_bw = by_gen['1HM_Idle']
    magic_child, magic_bw = by_gen['1HM_MagicBFR']
    if 'name="variableBindingSet">null<' not in objs[idle_child]:
        sys.exit('%s already has a variable binding' % idle_child)
    mw, iw = weights(objs[magic_bw]), weights(objs[idle_bw])
    right = [i for i in range(len(mw)) if mw[i] == 0.0 and i < len(iw) and iw[i] > 0.0]
    # the measured shape: right forearm 32 and hand 39 idle-only, upper arm 31 and clavicle 30 half and half
    if not (mw[31] == iw[31] == 0.5 and mw[30] == iw[30] == 0.5 and 32 in right and 39 in right and 41 in right):
        sys.exit('the blend masks are not the measured ones: magic %s idle %s' % (mw[28:42], iw[28:42]))
    new = list(mw)
    for i in right:
        new[i] = RIGHT_ARM_EPSILON
    weights_xml = ' '.join('%.6f' % v for v in new)
    body = '\n'.join([
        variable_appends(objs, cls),
        '\t<Append path="">',
        '\t\t<hkobject name="#%s$0" class="hkbVariableBindingSet" signature="0x338ad4ff">' % MOD,
        '\t\t\t<hkparam name="bindings" numelements="1">',
        '\t\t\t\t<hkobject>',
        '\t\t\t\t\t<hkparam name="memberPath">weight</hkparam>',
        '\t\t\t\t\t<hkparam name="variableIndex">$variableID[%s]$</hkparam>' % VAR,
        '\t\t\t\t\t<hkparam name="bitIndex">-1</hkparam>',
        '\t\t\t\t\t<hkparam name="bindingType">BINDING_TYPE_VARIABLE</hkparam>',
        '\t\t\t\t</hkobject>',
        '\t\t\t</hkparam>',
        '\t\t\t<hkparam name="indexOfBindingToEnable">-1</hkparam>',
        '\t\t</hkobject>',
        '\t</Append>',
        '\t<replace>',
        '\t\t<edit path="%s/variableBindingSet">' % idle_child,
        '\t\t\t<hkparam name="variableBindingSet">#%s$0</hkparam>' % MOD,
        '\t\t</edit>',
        '\t\t<edit path="%s/boneWeights">' % magic_bw,
        '\t\t\t<hkparam name="boneWeights" numelements="%d">%s</hkparam>' % (len(new), weights_xml),
        '\t\t</edit>',
        '\t</replace>'])
    write('1hm_behavior.xml',
          'Zenderal - Pistol Ramrod Reload: %s (default 1.0) weights the 1HM_Idle child of MLh_1HM_Idle_Blend (%s); the '
          'magic child (%s) gets %.2f on the right-arm bones it had at 0 (%s). At 0 our shot clip owns the right arm '
          '(ZP_PistolReloadArmScript sets it for a reload). Generated by tools/03.'
          % (VAR, idle_child, magic_bw, RIGHT_ARM_EPSILON, ' '.join(map(str, right))), body)
    objs, cls = objects(master)
    blend, sel, switch = right_hand_blend(objs, cls, master, character)
    write('0_master.xml', 'Zenderal - Pistol Ramrod Reload: %s in the root too, so Papyrus finds it by name; %s for the '
          'right hand: %s[0] (%s, the free left arm on 1HM_Idle) becomes a blend whose 1HM_Idle weight is %s; the '
          'reload requests %s. Generated by tools/03.' % (VAR, VAR_LEFT, sel, switch, VAR_LEFT, ' / '.join(VAR_REQ)),
          variable_appends(objs, cls, (VAR, VAR_LEFT, VAR_DUAL, VAR_STOW) + VAR_REQ, (ONE, ONE, 0, ONE, 0, 0)) + '\n' +
          blend + '\n' +
          root_staff_release(objs, cls, 41) + '\n' + stow_release(objs, cls, 61) + '\n' +
          prop_events(objs, cls, LOADED_EVENTS + SOUND_EVENTS))
    objs, cls = objects(magic)
    wrap, (sel, dual, left, right) = dual_wrapper(objs, cls, 21)
    write('magicbehavior.xml', 'Zenderal - Pistol Ramrod Reload: the prop events the reload clip annotates (the 1hm graphs '
          'list them, the magic graph did not); %s (default 0) and two pistols: %s[8] (%s) inside a blend on it '
          '(-1 %s, +1 %s). Generated by tools/03.' % (VAR_DUAL, sel, dual, left, right),
          prop_events(objs, cls) + '\n' + variable_appends(objs, cls, (VAR_DUAL,), (0,)) + '\n' + wrap)
    # first person: Pandora's pack files `firstperson~<name>`
    objs, cls = objects(hm1)
    body, (body_child, bset, magic_bw, right) = left_hand_1p(objs, cls, hm1)
    write('firstperson~1hm_behavior.xml',
          'Zenderal - Pistol Ramrod Reload, first person: %s (default 1.0) weights 1stP_MLh_1HM_Idle_Blend\'s upper-body '
          'child %s (a second binding in %s); the magic child (%s) gets %.2f on the RightArm bones it had at 0 (%s). '
          'Generated by tools/03.' % (VAR, body_child, bset, magic_bw, RIGHT_ARM_EPSILON, ' '.join(map(str, right))), body)
    objs, cls = objects(master1)
    blend, sel, switch = right_hand_blend(objs, cls, master1, character1, slot=1,
                                          switch_name='H2H_MRh_Idle_BoneSwitch_1stP', idle_name='H2H_MRh_1stPUpperBody',
                                          first=11, blend_name='ZenPistol_H2H_MRh_Idle_Blend_1stP')
    write('firstperson~0_master.xml', 'Zenderal - Pistol Ramrod Reload, first person: %s and %s in the root; %s[1] (%s, '
          'the free left arm on the first-person upper body) becomes a blend whose upper-body weight is %s; the reload '
          'requests %s. Generated by tools/03.' % (VAR, VAR_LEFT, sel, switch, VAR_LEFT, ' / '.join(VAR_REQ)),
          variable_appends(objs, cls, (VAR, VAR_LEFT, VAR_DUAL, VAR_STOW) + VAR_REQ, (ONE, ONE, 0, ONE, 0, 0)) + '\n' +
          blend + '\n' +
          root_staff_release(objs, cls, 51) + '\n' + stow_release(objs, cls, 81) + '\n' +
          prop_events(objs, cls, LOADED_EVENTS + SOUND_EVENTS))
    objs, cls = objects(magic1)
    wrap, (sel, dual, left, right) = dual_wrapper(objs, cls, 31)
    write('firstperson~magicbehavior.xml', 'Zenderal - Pistol Ramrod Reload, first person: the prop events the reload '
          'clip annotates; %s and the two-pistol blend on it around %s[8] (%s). Generated by tools/03.'
          % (VAR_DUAL, sel, dual), prop_events(objs, cls) + '\n' + variable_appends(objs, cls, (VAR_DUAL,), (0,)) + '\n' + wrap)


if __name__ == '__main__':
    main()
