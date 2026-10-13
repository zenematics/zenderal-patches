"""Rebuild the `Zenderal - Staff Draw Fix` MO2 mod: an OAR submod restoring the vanilla magic equip clips
while a staff is in the right hand.

Smooth Magic Casting Animation 4.2 ships a legacy DAR folder `_CustomConditions/996` whose condition is
always true (`IsActorBase(Player) OR NOT IsActorBase(Player)`). Its `mrh_and_mlh_equip` / `mlh_equip`
therefore also replace the clips the behaviour graph activates right after `StaffRight_Equip`, and the
third-person staff draw (reach over the shoulder) never shows: the staff pops into the hand. Verified with
OAR's animation log 2026-10-13. Dynamic Random Spell Idle replaces the same clips but excludes a right-hand
staff in every equip submod, so this submod only needs to beat `996`.

The clips are Bethesda's, extracted from the user's own `Skyrim - Animations.bsa`, never committed.

Usage:  python 01-build-staff-draw-fix.py [<mods dir>]     (default E:/Zenderal/mods)
"""
import os, sys, json, hashlib
import importlib.util

_spec = importlib.util.spec_from_file_location(
    'restores', os.path.join(os.path.dirname(__file__), '..', '..', 'EnderalTextureRestores', 'tools',
                             '01-extract-enderal-textures.py'))
_restores = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_restores)
read_from_bsa = _restores.read_from_bsa

MOD = 'Zenderal - Staff Draw Fix'
OAR = ['meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer', 'Zenderal - Staff Draw Fix']
SUBMOD = 'Vanilla magic equip with staff'
CLIPS = ['mlh_equip.hkx', 'mrh_and_mlh_equip.hkx', 'mlh_unequip.hkx', 'mrh_and_mlh_unequip.hkx']
PRIORITY = 8300000  # above Smooth Magic Casting's 996 (DRSI's 8210000+ submods exclude staffs anyway)

MOD_CONFIG = {
    'name': 'Zenderal - Staff Draw Fix',
    'author': 'Zenderal',
    'description': 'Vanilla magic equip/unequip clips while a staff is in the right hand, so Smooth Magic '
                   'Casting no longer hides the third-person staff draw.',
}
SUBMOD_CONFIG = {
    'name': SUBMOD,
    'description': 'Right hand holds a staff: play the vanilla magic equip/unequip clips.',
    'priority': PRIORITY,
    'conditions': [
        {'condition': 'IsEquippedType', 'requiredVersion': '1.0.0.0', 'Type': {'value': 8.0}, 'Left hand': False},
    ],
}


def main():
    mods = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal/mods'
    bsa = os.path.join(os.path.dirname(mods.rstrip('/\\')), 'Stock Game', 'Data', 'Skyrim - Animations.bsa')
    mod_dir = os.path.join(mods, MOD, *OAR)
    sub_dir = os.path.join(mod_dir, SUBMOD)
    os.makedirs(sub_dir, exist_ok=True)
    with open(os.path.join(mod_dir, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(MOD_CONFIG, fh, indent=4)
    with open(os.path.join(sub_dir, 'config.json'), 'w', encoding='utf-8') as fh:
        json.dump(SUBMOD_CONFIG, fh, indent=4)
    for clip in CLIPS:
        blob = read_from_bsa(bsa, 'meshes\\actors\\character\\animations\\' + clip)
        with open(os.path.join(sub_dir, clip), 'wb') as fh:
            fh.write(blob)
        print(f'{len(blob):>8}  {hashlib.sha1(blob).hexdigest()[:12]}  {clip}')
    print(f'{len(CLIPS)} clips -> {sub_dir}')


if __name__ == '__main__':
    main()
