"""Which active plugins define/override the records Sting and Rise copy or reference?

Master-aware header scan of the live load order (profile Ultra): every enabled plugin's records,
nested groups included, FormIDs resolved through the plugin's own MAST list (ESL-flagged plugins
use the light FormID space). Prints the chain per FormKey, last = winner, and writes
tools/overriders.json, which 02-build-records.py checks so it never copies a record that a later
plugin has changed since.

Usage:  python src/StingAndRise/tools/00-scan-overriders.py
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
MO2 = TOOLS['modlistRoot']
PROFILE = os.path.join(MO2, 'profiles', 'Ultra')
MODS = os.path.join(MO2, 'mods')
GAME_DATA = TOOLS['gameDataDir']
OUT = os.path.join(HERE, 'overriders.json')

TARGETS = {
    '13C2AF:Skyrim.esm': "WEAP _04E_30_Unique_YerosLastWords (both daggers copy it)",
    '02A26E:Enderal - Forgotten Stories.esm': "COBJ _04E_Temper_Unique_YerosLastWords (temper copied)",
    '015AA7:Skyrim.esm': "WEAP _01E_05_Unique_BloodNeedle (Sting's model: Pretty's assassin blade)",
    '14483F:Skyrim.esm': "STAT 1stPersonIronUniDagger (Sting's first-person model, referenced)",
    '07C98E:Skyrim.esm': "WEAP _04E_31_AeternaDagger (Rise's model: Pretty's Aeterna dagger)",
    '036BD0:Skyrim.esm': "STAT 1stPersonElvenDagger (Rise's first-person static copied: the gold swap)",
    '0777C3:Skyrim.esm': "TXST Nettlebane (Rise's gold texture set copied)",
    '001F73:Enderal SE - Gameplay Overhaul.esp': "MGEF EnchPoisonNoShader (Sting's poison copied)",
    '067252:Skyrim.esm': "MGEF _00E_A1_FireArrowEnchME, Enderal's Burning (Rise's fire copied)",
    '10A045:Skyrim.esm': "ARTO ChillrendEnchFX (enchant-art record shape copied)",
    '06A18E:Skyrim.esm': "EXPL _00E_FS_MAGGoreExplosion, FS's gore burst (Blood Boil's pop copied)",
    '144758:Skyrim.esm': "EFSH _00E_BloodyFXShader (Blood Boil's splatter copied)",
    '01F82A:Skyrim.esm': "IPDS BloodSprayImpactSetRed (Blood Boil's decals, referenced)",
    '02E28E:Enderal - Forgotten Stories.esm': "SNDR _00E_FS_CorpseExplosion (the gore burst's sound, referenced)",
    '01CB69:Skyrim.esm': "NPC_ _03E_JungerMooskrabbler (the spiderling copied)",
    '01EA6D:Skyrim.esm': "MGEF LightFFAimed, Mage Light (the mote copied)",
    '03FA58:Skyrim.esm': "LIGH MagicLightLightSpell01 (the mote's light copied)",
    '041F06:Skyrim.esm': "ARTO LightSpellActorFX (the mote's art copied)",
    '143325:Skyrim.esm': "EXPL _00E_A1_FireArrowWayfarerExp (the mote's fire nova copied)",
    '046008:Skyrim.esm': "IPDS MAGSpiderSpitImpactSet (the venom burst's splats, referenced)",
    '02E1CD:Skyrim.esm': "EFSH WebbedFXS (the spiderling's web on the body, copied)",
    '10A043:Skyrim.esm': "EFSH FrostChillrendFXShader (copied: the enchant art's invisible carrier shader)",
    '0F8641:Skyrim.esm': "MGEF _00E_A1_ShadowtongueoilSlowME (Sting's slow copied)",
    '10AA1A:Skyrim.esm': "KYWD WeapMaterialSilver (on Rise, referenced)",
}


def plugin_paths():
    mods = [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]
    loc = {}
    for f in os.listdir(GAME_DATA):
        if f.lower().endswith(('.esm', '.esp', '.esl')):
            loc[f.lower()] = os.path.join(GAME_DATA, f)
    for m in reversed(mods):           # modlist.txt is highest priority first; later assignment wins
        d = os.path.join(MODS, m)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(('.esm', '.esp', '.esl')):
                    loc[f.lower()] = os.path.join(d, f)
    order = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm']
    for l in open(os.path.join(PROFILE, 'plugins.txt'), encoding='utf-8'):
        l = l.strip()
        if l.startswith('*') and l[1:] not in order:
            order.append(l[1:])
    return [(p, loc[p.lower()]) for p in order if p.lower() in loc]


def scan(path, want):
    data = open(path, 'rb').read()
    hdr_size = struct.unpack_from('<I', data, 4)[0]
    flags = struct.unpack_from('<I', data, 8)[0]
    masters = [m.decode('utf-8', 'replace') for m in re.findall(rb'MAST..([^\x00]*)\x00', data[24:24 + hdr_size])]
    self_name = os.path.basename(path)
    hits = set()
    pos = 24 + hdr_size
    while pos < len(data):
        typ = data[pos:pos + 4]
        size = struct.unpack_from('<I', data, pos + 4)[0]
        if typ == b'GRUP':
            pos += 24
            continue
        fid = struct.unpack_from('<I', data, pos + 12)[0]
        idx = fid >> 24
        owner = masters[idx] if idx < len(masters) else self_name
        local = fid & 0xFFFFFF
        if idx >= len(masters) and flags & 0x200:
            local = fid & 0xFFF
        fk = '%06X:%s' % (local, owner)
        if fk in want:
            hits.add(fk)
        pos += 24 + size
    return hits


def main():
    result = {fk: [] for fk in TARGETS}
    for name, path in plugin_paths():
        for fk in scan(path, set(TARGETS)):
            result[fk].append(name)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=1, sort_keys=True)
    for fk, chain in sorted(result.items()):
        print('%s  %s\n    %s' % (fk, TARGETS[fk], ' -> '.join(chain) or '(not found)'))


if __name__ == '__main__':
    sys.exit(main())
