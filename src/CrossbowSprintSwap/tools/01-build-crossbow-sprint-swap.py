"""Rebuild the `Zenderal - Crossbow Sprint Swap` MO2 mod: crossbow-type weapons (Ordo's muskets and real
crossbows) sprint with Tactical Crossbow Movement (OAR)'s shouldered sprint - and get nothing else from it.

Tactical Crossbow Movement's `Standing` submod (priority 838295: IsWeaponDrawn, not IsSneaking,
IsEquippedType 9) ships `dlc01/crossbowsprintforward.hkx`, but Dynamic Sprint's four crossbow submods
(Combat / Non-Combat x Sprint / Per-Sprint, priorities 93931210-93931240, same weapon gate) outrank it.
This mod ships one OAR `user.json` per Dynamic Sprint crossbow submod - an OAR user.json REPLACES its
submod's config.json, so each is the author's config verbatim + "disabled": true (the DynamicDodgeNoSway
pattern). Dynamic Sprint itself is not edited.

Sprint only (curator, 2026-10-14): none of Tactical's other animations. Its three submods (`Standing` walk/
run, `Sneak`, `Sneak Moving`) get the same user.json treatment, and `Tactical sprint` (Standing's
conditions and priority) plays a copy of Standing's crossbowsprintforward.hkx - the only clip kept. The
copy keeps working if Tactical is later disabled in MO2; re-run this after a Tactical update.

Tactical idle (curator, 2026-10-14): the standing drawn idle (crossbow_idleheld) came from Smooth Combat non
Combat Animation's legacy DAR folders 601901 / 701901 / 702901. `Tactical idle` (838290; drawn, not sneaking,
crossbow) plays Zodd's Tactical Crossbows' crossbow_idleheld (both hands on the gun, pointing forward and
~23 deg down; Vanargand's, low and sideways, was tried and reverted). Chosen from measured candidates after Tactical's own idle (a sneak-moving clip from its `Sneak
Moving` submod) didn't hold the gun right; Smooth Combat 702901 has the left hand off the gun.

History (2026-10-14), all reverted at the curator's request - see arch-docs/patches/CrossbowSprintSwap.md
for the measurements: Dynamic Sprint's 2hw sprint under the crossbow name (musket held backwards; a Weapon-
track splice made it worse); Zodd idles over Smooth Combat; Zodd's sneak aim set with a retimed 0.2 s raise;
DAR 432101 musket sneak aim with a generated raise; a 432101/432102 musket standing set; Tactical-everywhere
and Vanargand-everywhere directional movement. Only the sprint is kept.

Usage:  python -I 01-build-crossbow-sprint-swap.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, json, shutil

MOD = 'Zenderal - Crossbow Sprint Swap'
OAR_REL = ['meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer']
DS = ['Dynamic Sprint'] + OAR_REL + ['Dynamic Sprint']
TCM_ROOT = ['Tactical Crossbow Movement (OAR)'] + OAR_REL + ['Tactical Crossbow Movement']
TCM_SUBMODS = ['Standing', 'Sneak', 'Sneak Moving']
TCM_IDLE = ["Zodd'S Tactiacal Crossbows", 'Meshes', 'actors', 'character', 'animations', 'dlc01', 'crossbow_idleheld.hkx']
IDLE_PRIORITY = 838290  # above Smooth Combat's crossbow idle folders (601901-702901)
VARIANTS = ['Combat Sprint', 'Combat Per-Sprint', 'Non-Combat Sprint', 'Non-Combat Per-Sprint']
OWN = OAR_REL + [MOD]
NL = chr(10)


def gates_on_crossbow(cfg):
    return any(c.get('condition') == 'IsEquippedType' and c.get('Type', {}).get('value') == 9.0
               for c in cfg['conditions'])


def write_json(path, data):
    with open(path, 'w', encoding='utf-8', newline=NL) as fh:
        json.dump(data, fh, indent=4)
        fh.write(NL)


def disable(mods, rel, root):
    """Write <root>/<rel without the mod folder>/user.json = that submod's config + "disabled": true."""
    src = os.path.join(mods, *rel)
    if os.path.isfile(os.path.join(src, 'user.json')):
        sys.exit('%s already has a user.json - merge by hand' % src)
    with open(os.path.join(src, 'config.json'), encoding='utf-8-sig') as fh:
        cfg = json.load(fh)
    if not gates_on_crossbow(cfg):
        sys.exit('%s no longer gates on IsEquippedType 9 - re-check before disabling' % src)
    out = os.path.join(root, *rel[1:])
    os.makedirs(out)
    write_json(os.path.join(out, 'user.json'), dict(cfg, disabled=True))
    return cfg


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    sprint = os.path.join(mods, *TCM_ROOT, 'Standing', 'dlc01', 'crossbowsprintforward.hkx')
    if not os.path.isfile(sprint):
        sys.exit('Tactical Crossbow Movement no longer ships a crossbow sprint at %s' % sprint)

    root = os.path.join(mods, MOD)
    if os.path.isdir(root):
        shutil.rmtree(root)
    for v in VARIANTS:
        cfg = disable(mods, DS + ['CrossBow ' + v], root)
        print('disabled Dynamic Sprint "CrossBow %s" (priority %d)' % (v, cfg['priority']))
    standing = None
    for s in TCM_SUBMODS:
        cfg = disable(mods, TCM_ROOT + [s], root)
        standing = standing or cfg
        print('disabled Tactical Crossbow Movement "%s" (priority %d)' % (s, cfg['priority']))

    own = os.path.join(root, *OWN)
    sub = os.path.join(own, 'Tactical sprint')
    os.makedirs(os.path.join(sub, 'dlc01'))
    write_json(os.path.join(own, 'config.json'),
               {'name': MOD, 'author': 'Zenderal', 'description': "Tactical Crossbow Movement's crossbow sprint only."})
    shutil.copy2(sprint, os.path.join(sub, 'dlc01', 'crossbowsprintforward.hkx'))
    write_json(os.path.join(sub, 'config.json'),
               dict(standing, name='Tactical sprint', description="Tactical Crossbow Movement Standing's sprint clip only."))
    print('Tactical sprint (priority %d): dlc01/crossbowsprintforward.hkx' % standing['priority'])
    tcm_idle = os.path.join(mods, *TCM_IDLE)
    if not os.path.isfile(tcm_idle):
        sys.exit('missing %s' % tcm_idle)
    idle = os.path.join(own, 'Tactical idle')
    os.makedirs(os.path.join(idle, 'dlc01'))
    shutil.copy2(tcm_idle, os.path.join(idle, 'dlc01', 'crossbow_idleheld.hkx'))
    write_json(os.path.join(idle, 'config.json'),
               dict(standing, name='Tactical idle', priority=IDLE_PRIORITY,
                    description="Zodd's Tactical Crossbows standing idle: both hands on the gun."))
    print('Tactical idle (priority %d): dlc01/crossbow_idleheld.hkx from Zodd Tactical Crossbows' % IDLE_PRIORITY)
    print('built %s' % root)


if __name__ == '__main__':
    main()
