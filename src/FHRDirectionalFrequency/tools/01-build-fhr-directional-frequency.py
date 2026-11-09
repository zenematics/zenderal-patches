"""Zenderal - FHR Directional Frequency: enemies use For Honor Reforged's side attacks, and charge its empowered-attack
arrows (Reforged Directional Combat), more often. Curator's taste (2026-11-08: "I don't ever actually see enemies do
these directional attacks"). Two parts, both generated here:

1. OAR user.json overrides for every enemy side-attack submod in FHR's "* - NPC Addon" movesets (Left/Right Light and
   Power attacks). Each is the submod's own config.json verbatim with its Random thresholds raised (OAR's user.json
   replaces config.json): the plain roll 10 -> SIDE_PLAIN, the roll while the enemy carries that side's arrow
   30 -> SIDE_BUFFED_LIGHT (lights) / 50 -> SIDE_BUFFED_POWER (power attacks). Back attacks are left alone (they are
   reactions to the player blocking, at 50% already). Written into MO2 mod MOD.
2. Plugin FHRDirectionalFrequencyESP: the four side arrow effects 801/802/804/805 (Reforged Directional Combat.esp)
   verbatim with their GetRandomPercent roll raised: light 10 -> ARROW_LIGHT, heavy 15 -> ARROW_HEAVY. The roll runs
   on the enemy's attack window right after an attack of that side (DAC casts EmpoweredDirectionalTrigger 800 on
   MCO_WinOpen/AttackWinStart; each effect needs the side marker that attack's PIE tag put up). The back arrows have
   no icon in FHR's SIF set (Unused/), so they stay as FHR has them.

Usage: python -I 01-build-fhr-directional-frequency.py
Reads reference/mods/FHRDirectional (Spriggit 0.40.0) and the installed For Honor Reforged mod. Rerun after an FHR
update. Evidence: arch-docs/patches/FHRDirectionalFrequency.md."""
import copy
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ESP = os.path.join(HERE, '..', 'FHRDirectionalFrequencyESP')
REF = os.path.join(REPO, 'reference', 'mods', 'FHRDirectional', 'MagicEffects')
MODS = 'E:/Zenderal/mods'
FHR = 'For Honor Reforged'
MOD = 'Zenderal - FHR Directional Frequency'
OAR_REL = ('meshes', 'actors', 'character', 'animations', 'OpenAnimationReplacer')

SIDE_PLAIN = 25.0          # FHR: 10
SIDE_BUFFED_LIGHT = 50.0   # FHR: 30
SIDE_BUFFED_POWER = 60.0   # FHR: 50
ARROW_LIGHT = 30           # FHR: 10
ARROW_HEAVY = 40           # FHR: 15

# effect FormID -> (file stem, FHR's roll, new roll)
ARROWS = {
    '000801': ('EmpoweredRightHeavy', 15, ARROW_HEAVY),
    '000802': ('EmpoweredLeftHeavy', 15, ARROW_HEAVY),
    '000804': ('EmpoweredRightLight', 10, ARROW_LIGHT),
    '000805': ('EmpoweredLeftLight', 10, ARROW_LIGHT),
}
SIDE_SUB = re.compile(r'^(Left|Right) (Light|Power) Attacks?$')


def randoms(node, inside_and_with_effect=False, out=None):
    """Every Random condition, tagged True when it sits in an AND next to a HasMagicEffect (the 'has the arrow' roll)."""
    if out is None:
        out = []
    if isinstance(node, dict):
        if node.get('condition') == 'Random':
            out.append((node, inside_and_with_effect))
        kids = node.get('Conditions')
        if kids is not None:
            buffed = node.get('condition') == 'AND' and any(
                isinstance(k, dict) and k.get('condition') == 'HasMagicEffect' for k in kids)
            for k in kids:
                randoms(k, buffed, out)
    elif isinstance(node, list):
        for k in node:
            randoms(k, inside_and_with_effect, out)
    return out


def build_oar():
    src_root = os.path.join(MODS, FHR, *OAR_REL)
    out_root = os.path.join(MODS, MOD, *OAR_REL)
    if os.path.isdir(os.path.join(MODS, MOD, 'meshes')):
        shutil.rmtree(os.path.join(MODS, MOD, 'meshes'))
    count = 0
    for oar_mod in sorted(os.listdir(src_root)):
        if not oar_mod.endswith('- NPC Addon'):
            continue
        for sub in sorted(os.listdir(os.path.join(src_root, oar_mod))):
            m = SIDE_SUB.match(sub)
            sdir = os.path.join(src_root, oar_mod, sub)
            if not m or not os.path.isfile(os.path.join(sdir, 'config.json')):
                continue
            if os.path.exists(os.path.join(sdir, 'user.json')):
                raise SystemExit(f'{oar_mod}/{sub} already has a user.json; merge by hand')
            cfg = json.load(open(os.path.join(sdir, 'config.json'), encoding='utf-8-sig'))
            new = copy.deepcopy(cfg)
            power = m.group(2) == 'Power'
            buffed_old, buffed_new = (50.0, SIDE_BUFFED_POWER) if power else (30.0, SIDE_BUFFED_LIGHT)
            plain = buffed = 0
            for node, is_buffed in randoms(new.get('conditions', [])):
                if node.get('Comparison') != '<' or node['Minimum random value']['value'] != 0.0 \
                        or node['Maximum random value']['value'] != 100.0:
                    raise SystemExit(f'{oar_mod}/{sub}: unexpected Random shape {node}')
                v = node['Numeric value']['value']
                if is_buffed and v == buffed_old:
                    node['Numeric value']['value'] = buffed_new
                    buffed += 1
                elif not is_buffed and v == 10.0:
                    node['Numeric value']['value'] = SIDE_PLAIN
                    plain += 1
                else:
                    raise SystemExit(f'{oar_mod}/{sub}: unexpected Random {v} (buffed={is_buffed})')
            if (plain, buffed) != (1, 1):
                raise SystemExit(f'{oar_mod}/{sub}: expected one plain and one buffed roll, got {plain}/{buffed}')
            odir = os.path.join(out_root, oar_mod, sub)
            os.makedirs(odir, exist_ok=True)
            with open(os.path.join(odir, 'user.json'), 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(new, fh, indent=4)
            count += 1
    return count


def build_esp():
    out = os.path.join(ESP, 'MagicEffects')
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for fid, (stem, old, new) in ARROWS.items():
        name = f'{stem} - {fid}_Reforged Directional Combat.esp.yaml'
        raw = open(os.path.join(REF, name), 'rb').read().decode('utf-8')
        pat = (r'(    MutagenObjectType: GetRandomPercentConditionData\r?\n  ComparisonValue: )'
               + str(old) + r'(\r?\n)')
        text, n = re.subn(pat, lambda mm: mm.group(1) + str(new) + mm.group(2), raw)
        if n != 1:
            raise SystemExit(f'{name}: expected one GetRandomPercent <= {old}, found {n}')
        open(os.path.join(out, name), 'wb').write(text.encode('utf-8'))
    return len(ARROWS)


if __name__ == '__main__':
    print(f'{build_esp()} arrow effects written')
    print(f'{build_oar()} enemy side-attack user.json overrides written to {MOD}')
