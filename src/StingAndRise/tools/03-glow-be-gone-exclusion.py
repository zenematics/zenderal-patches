"""Keep Sting's and Rise's enchant shader alive under Glow Be Gone Redone - NG.

Glow Be Gone (Nexus 171248, an SKSE plugin in the list) nulls `data.enchantShader` on EVERY magic effect at
kDataLoaded when its toml says `RemoveWeaponFX = true` (the list's setting), unless the effect is "protected"
(Conjuration, bound weapon, summon, reanimate ... archetypes: why Enderal's bound dagger keeps its art) or listed
in its exclusions. It never touches enchant art, but the enchant art of a weapon shows only with an enchant shader
(see arch-docs/patches/StingAndRise.md): so Sting's coat and Rise's flames need 802 and 806 kept.

Writes the winning GlowBeGoneSSE.toml (Glow Be Gone's own) with those two effects appended to its
MagicEffectExclusionList into `Zenderal - Settings` (which outranks Glow Be Gone, and holds the list's third-party
configs). Glow Be Gone reads "<plugin>:<local id>" and keeps the low 12 bits for a light plugin. The file is
derived from a third-party config, so it is generated, not committed: rerun after a Glow Be Gone update.

Usage:  python src/StingAndRise/tools/03-glow-be-gone-exclusion.py [--dry-run]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
MO2 = TOOLS['modlistRoot']
PROFILE = os.path.join(MO2, 'profiles', 'Ultra')
REL = os.path.join('SKSE', 'Plugins', 'GlowBeGoneSSE.toml')
TARGET_MOD = 'Zenderal - Settings'
SOURCE_MOD = 'Glow Be Gone Redone - NG'
ME = 'Zenderal - Sting and Rise.esp'
OWL = 'Zenderal - Owl Bow.esp'
KEEP = [   # (plugin, local id, why)
    (ME, '000802', 'ZP_StingVenomEffect: Sting\'s poison coat (enchant art) needs its enchant shader'),
    (ME, '000806', 'ZP_RiseBurnEffect: Rise\'s flames (enchant art) need their enchant shader'),
    (ME, '00082B', 'ZP_StingWebbedEffect: the spiderling\'s web over the body is its hit shader'),
    (OWL, '000806', 'ZP_OwlBowSlowEffect: the Owl Bow\'s snowfall (enchant art) needs its enchant shader'),
]


def enabled_mods():
    """Enabled mods, highest priority first (modlist.txt order)."""
    return [l[1:].strip() for l in open(os.path.join(PROFILE, 'modlist.txt'), encoding='utf-8') if l.startswith('+')]


def main():
    dry = '--dry-run' in sys.argv
    mods = enabled_mods()
    for need in (TARGET_MOD, SOURCE_MOD):
        if need not in mods:
            sys.exit('%s is not enabled in Ultra' % need)
    if mods.index(TARGET_MOD) > mods.index(SOURCE_MOD):
        sys.exit('%s must outrank %s in MO2' % (TARGET_MOD, SOURCE_MOD))
    # the copy we override: the highest-priority enabled one below our target
    src = None
    for m in mods[mods.index(TARGET_MOD) + 1:]:
        p = os.path.join(MO2, 'mods', m, REL)
        if os.path.isfile(p):
            src = (m, p)
            break
    if not src or src[0] != SOURCE_MOD:
        sys.exit('expected the config to come from %s, found %s' % (SOURCE_MOD, src and src[0]))
    raw = open(src[1], 'rb').read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    if 'RemoveWeaponFX = true' not in text:
        print('note: RemoveWeaponFX is not true in %s; the exclusion is harmless then' % src[0])
    if ME in text or OWL in text:
        sys.exit('%s already names %s / %s - nothing to do' % (src[1], ME, OWL))
    block = re.search(r'^MagicEffectExclusionList = \[(?:.*\r?\n)*?\]', text, re.M)
    if not block:
        sys.exit('no MagicEffectExclusionList in ' + src[1])
    lines = ''.join('    "%s:%s",  # %s%s' % (plug, '00' + fid, note, nl) for plug, fid, note in KEEP)
    end = block.end() - 1                                   # the closing ]
    out = text[:end] + lines + text[end:]
    assert out.count(ME) + out.count(OWL) == len(KEEP)
    dst = os.path.join(MO2, 'mods', TARGET_MOD, REL)
    print('from %s\n  to %s\n  + %s' % (src[1], dst, '\n  + '.join('%s:00%s' % (pl, f) for pl, f, _ in KEEP)))
    if dry:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('written; refresh MO2 (F5) before launching: it is a new file')


if __name__ == '__main__':
    main()
