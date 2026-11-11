"""Enemies' twins of the third-person pistol reload submods (2026-11-11).

Enemies reload the player's way (ZP_PistolReloadArmNPCEffect, an ability tools/02 builds and SPID hands out): their
shot leaves the pistol empty and the script starts the reload's cast with no bullet. The player's submods (tools/01)
are gated on the hand's request variable (`fZenPistolReloadL/R` == 1, `requested()`), which the script sets on the NPC
too, but traced 2026-11-11 that condition never held for an enemy: its reload casts played Loop's plain shot (each
ended after ~0.9 s and the next was asked for at once), while the same submods gated on "not the player" alone had
played for those same Marauders the test before. So each player submod `Reload <...>` gets a twin `Reload <...>, NPC`:
the same clips, priority + NPC_STEP (each tools/01 band uses fewer than 100), the request condition replaced by
NOT_PLAYER and that hand's item charge under EMPTY_BELOW: only the script's reload cast, which runs at 0.5 (a loaded
pistol is at 2, an empty one rests at 1; 1.5 let a real cast at 1 play the reload while it fired, 2026-11-11).

Item charge is an actor value: `RightItemCharge` 64, `LeftItemCharge` 82 (CommonLibSSE-NG `RE::ActorValue`, whose
Health 24 / Stamina 26 match the list's own OAR configs), read as `actorValueType` "Value".

Run after tools/01 (which empties the OAR folder) and tools/04 (which skips these: their names end NPC_SUFFIX).
Usage:  python src/PistolRamrodReload/tools/08-build-npc-reload.py [<modlist root>]
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = _load('pistol_reload', os.path.join(HERE, '01-build-pistol-reload.py'))
ADS = PR.ADS

NPC_SUFFIX = ', NPC'
NPC_STEP = 500
NOT_PLAYER = {'condition': 'IsActorBase', 'requiredVersion': '1.0.0.0', 'negated': True,
              'Actor base': {'pluginName': 'Skyrim.esm', 'formID': '7'}}   # the musket reload's player test (FO tools/09)
CHARGE_AV = {PR.REQUEST[True]: 82, PR.REQUEST[False]: 64}                 # kLeftItemCharge, kRightItemCharge
EMPTY_BELOW = 0.75    # only the reload's own cast (0.5); 1.5 let a real cast at 1 play the reload (11th test)


def empty(av):
    """That hand's item charge under EMPTY_BELOW."""
    return {'condition': 'CompareValues', 'requiredVersion': '1.0.0.0',
            'Value A': {'actorValue': av, 'actorValueType': 'Value'}, 'Comparison': '<',
            'Value B': {'value': EMPTY_BELOW}}


def twin_config(cfg):
    req = [c for c in cfg['conditions'] if c.get('condition') == 'CompareValues'
           and c.get('Value B', {}).get('graphVariable') in CHARGE_AV]
    if len(req) != 1:
        sys.exit('%s: not exactly one reload request among its conditions' % cfg['name'])
    conds = []
    for c in cfg['conditions']:
        conds += [NOT_PLAYER, empty(CHARGE_AV[c['Value B']['graphVariable']])] if c is req[0] else [c]
    return {'name': cfg['name'] + NPC_SUFFIX,
            'description': cfg['description'] + ' Enemies: played when the pistol is empty (item charge under %.2f), '
                                                'for the reload ZP_PistolReloadArmNPCEffect starts.' % EMPTY_BELOW,
            'priority': cfg['priority'] + NPC_STEP, 'conditions': conds}


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else ADS.TOOLS['modlistRoot']
    oar = os.path.join(root, 'mods', PR.DEPLOY, *PR.OAR)
    if not os.path.isdir(oar):
        sys.exit('run tools/01 first: no %s' % oar)
    for d in os.listdir(oar):
        if d.endswith(NPC_SUFFIX):
            shutil.rmtree(os.path.join(oar, d))
    subs = sorted(d for d in os.listdir(oar) if os.path.isdir(os.path.join(oar, d)) and d.startswith('Reload '))
    priorities = []
    for s in subs:
        src = os.path.join(oar, s)
        cfg = json.load(open(os.path.join(src, 'config.json'), encoding='utf-8'))
        twin = twin_config(cfg)
        dst = os.path.join(oar, s + NPC_SUFFIX)
        os.makedirs(dst)
        clips = [f for f in os.listdir(src) if f.lower().endswith('.hkx')]
        if not any('release' in f.lower() for f in clips):
            sys.exit('%s has no shot clip' % s)
        for f in clips:
            shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
        ADS.write_config(dst, twin)
        priorities += [cfg['priority'], twin['priority']]
    if len(set(priorities)) != len(priorities):
        sys.exit('%d duplicate priorities' % (len(priorities) - len(set(priorities))))
    print('%d enemy twins next to %d player reload submods in %s (charge under %.2f, priority + %d)'
          % (len(subs), len(subs), oar, EMPTY_BELOW, NPC_STEP))


if __name__ == '__main__':
    main()
