"""Dakeyras' RaceMenu preset: the curator's "Zen's Joseph Goatee" rewritten for the list, as ZFW_Dakeyras.jslot.

RaceMenu loads the preset onto him at runtime (ZFW_ArenaQuest.ApplyDakeyrasFace). On the first look (2026-11-19) he
had everything but the goatee. The goatee is BoP_new_mustache_01b 000974 of Beards of Power.esp, an ESL-flagged
plugin, and the curator's file names it "Beards of Power.esp|032974" - the light index bits (0x032 on the machine
that saved it) folded into the id - while its modNames list has no Beards of Power.esp at all; the other six parts
are from full plugins and came through. So: every head part from a light plugin gets its identifier written with the
local id alone ("Beards of Power.esp|000974"), the plugin is added to modNames, and the rest of the file is the
curator's, byte for byte in meaning. Written into Zenderal - Patch Collection (not committed); rerun after the
curator changes the preset.

Usage: python src/FogWood/tools/06-build-dakeyras-preset.py [--source <jslot>] [--target <MO2 mod folder>]
"""
import argparse
import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
SOURCE = os.path.join(TOOLS['modlistRoot'], 'overwrite', 'SKSE', 'Plugins', 'CharGen', 'Presets', "Zen's Joseph Goatee.jslot")
OUT_REL = os.path.join('SKSE', 'Plugins', 'CharGen', 'Presets', 'ZFW_Dakeyras.jslot')
ESL_FLAG = 0x200


def plugin_path(name):
    for d in os.listdir(os.path.join(TOOLS['modlistRoot'], 'mods')):
        p = os.path.join(TOOLS['modlistRoot'], 'mods', d, name)
        if os.path.isfile(p):
            return p
    p = os.path.join(TOOLS['gameDataDir'], name)
    return p if os.path.isfile(p) else None


def is_light(name):
    p = plugin_path(name)
    if not p:
        return None
    with open(p, 'rb') as f:
        head = f.read(12)
    return bool(struct.unpack_from('<I', head, 8)[0] & ESL_FLAG) or name.lower().endswith('.esl')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default=SOURCE)
    ap.add_argument('--target', default=os.path.join(TOOLS['modlistRoot'], 'mods', 'Zenderal - Patch Collection'))
    args = ap.parse_args()
    j = json.load(open(args.source, encoding='utf-8'))
    names = list(j.get('modNames', []))
    changed = []
    for part in j['headParts']:
        plugin, hexid = part['formIdentifier'].split('|')
        light = is_light(plugin)
        assert light is not None, 'plugin not in the list: ' + plugin
        local = int(hexid, 16)
        if light and local > 0xFFF:
            part['formIdentifier'] = '%s|%06X' % (plugin, local & 0xFFF)
            changed.append((plugin, hexid, '%06X' % (local & 0xFFF)))
        if plugin not in names:
            names.append(plugin)
            changed.append((plugin, 'added to modNames', ''))
    j['modNames'] = names
    out = os.path.join(args.target, OUT_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(j, open(out, 'w', encoding='utf-8'), indent=None, separators=(',', ':'))
    print('wrote', out, '(%d bytes)' % os.path.getsize(out))
    for c in changed:
        print('  ', *c)
    print('head parts:', ', '.join(p['formIdentifier'] for p in j['headParts']))


if __name__ == '__main__':
    main()
