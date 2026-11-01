"""Build the Goblin creature of `Zenderal - Goblins`: Arp meshes restored, goblin meshes moved to their own
path, and the race / skins / NPCs YAML. Never hand-edit what this writes.

Why: the `Goblins` mod (Nexus Enderal 238, Viltuska's goblins, open permissions; REQUIRED, never edited)
replaces every Falmer body nif (`actors\\falmer\\character assets\\falmer01-06.nif`, `falmer_male.nif`),
so all of Enderal's Arps (vanilla FalmerRace 0131F4) turned into goblins. The curator wants both.

1. Meshes (written into the MO2 mod, generated from the user's install, never committed):
   - the vanilla Falmer bodies, extracted from `Skyrim - Meshes0.bsa`, at the Falmer paths. The MO2 mod
     must sort ABOVE `Goblins`, so Arps render as Arps again (no other mod ships those files);
   - the four distinct goblin bodies, copied from the Goblins mod to `meshes\\Zenderal\\Goblins\\`. Their
     textures stay the Goblins mod's own (`textures\\actors\\viltuska_goblin\\`).
2. Records, copied from the WINNING records (EGO's for the race and the Arp NPCs; only EGO overrides
   them in the Ultra load order, full scan 2026-10-21) and edited:
   - `ZEN_GoblinRace`: FalmerRace verbatim (skeleton, behaviour graph, attacks, body part data), own
     EditorID so Dismembering Framework can key goblin limbs by race without touching the Arps';
   - four skins (ARMO + ARMA), one per goblin body, copied from the Arp skin/body ARMAs with the race and
     model swapped (texture-hash `Data` dropped: it described the Falmer textures);
   - five NPCs copied from Arps: weaker by design (Level 6, base health 70 vs 160, no health offset,
     weapon/magic skill offsets 15 vs 25-45, 40 EP vs 150), Arp faction kept (via their Template), Respawn kept,
     plus ZEN_GoblinRespawn (back 3 in-game days after death, global ZEN_GoblinRespawnDays).

Usage:  python 01-build-creature.py [<modlist root>]       (default E:/Zenderal)
"""
import glob
import importlib.util
import json
import os
import struct
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goblin_gear  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'E:/Zenderal'
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF_BASE = os.path.join(REPO, 'reference', 'base', 'Skyrim')
REF_EGO = os.path.join(REPO, 'reference', 'mods', 'EGO')
ESP = os.path.join(HERE, '..', 'GoblinsESP')
MOD_KEY = 'Zenderal - Goblins.esp'
OUT_MOD = os.path.join(ROOT, 'mods', 'Zenderal - Goblins')
GOBLINS = os.path.join(ROOT, 'mods', 'Goblins', 'meshes', 'actors', 'falmer', 'character assets')
MESHES0 = os.path.join(ROOT, 'Stock Game', 'Data', 'Skyrim - Meshes0.bsa')
BS = chr(92)
NL = '\r\n'
FALMER_REL = BS.join(['meshes', 'actors', 'falmer', 'character assets'])
FALMER_NIFS = ['falmer01.nif', 'falmer02.nif', 'falmer03.nif', 'falmer04.nif', 'falmer05.nif',
               'falmer06.nif', 'falmer_male.nif']
GOBLIN_DIR = BS.join(['Zenderal', 'Goblins'])
PYNIFLY = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))['pynifly']
# Shapes whose textures the Goblins mod never shipped (Viltuska's armor textures; seen white in game on the
# chieftain, 2026-10-21): (mesh variant, shape) -> (diffuse, normal), vanilla textures in the game BSAs.
# The pelt cape's UVs span the whole square, so a full-frame pelt; the feathers are alpha-tested.
RETEXTURE = {
    ('Chief', 'Armor_Variation_01'): (r'textures\clutter\wolfpelts\wolfpelt.dds', r'textures\clutter\wolfpelts\wolfpelt_n.dds'),
    ('Chief', 'feathers'): (r'textures\clutter\ingredients\hagfeathers.dds', r'textures\clutter\ingredients\hagfeathers_n.dds'),
}

RACE = ('000800', '0131F4', 'ZEN_GoblinRace', 'Goblin')
# variant -> (ARMA fid, ARMO fid, Goblins mod nif, Arp ARMO copied, Arp ARMA copied)
SKINS = {
    'Plain': ('000801', '000805', 'falmer02.nif', '0B526F', '050F31'),     # loincloth only
    'Scout': ('000802', '000806', 'falmer01.nif', '0B526F', '050F2F'),     # wraps, cap, bag
    'Witch': ('000803', '000807', 'falmer05.nif', '0B526E', '050F37'),     # witch body, bones, piercings
    'Chief': ('000804', '000808', 'falmer06.nif', '0B526D', '050F39'),     # goat-skull helmet, feathers
}
# NPC fid -> (EditorID, Name, Arp copied (EGO winner), skin variant)
NPCS = {
    '000810': ('ZEN_Goblin', 'Goblin', '0B5270', 'Plain'),
    '000811': ('ZEN_GoblinScout', 'Goblin', '0B5272', 'Scout'),
    '000812': ('ZEN_GoblinArcher', 'Goblin Archer', '0EB408', 'Scout'),
    '000813': ('ZEN_GoblinShaman', 'Goblin Shaman', '0B5266', 'Witch'),
    '000814': ('ZEN_GoblinChief', 'Goblin Chieftain', '0B5270', 'Chief'),
}
ROLE = {'000810': 'Goblin', '000811': 'Scout', '000812': 'Archer', '000813': 'Shaman', '000814': 'Chief'}  # goblin_gear
LEVEL = {'000814': 9}            # the chieftain leads a pack: a little tougher than the rest
DEFAULT_LEVEL = 6
# NPC `Health` is only the CK's stored display value: these NPCs are not AutoCalcStats, so the game uses
# race Starting Health (100) + HealthOffset (0). Seen in game 2026-10-21: the chieftain had 100, not 110.
# Real health is cut at runtime instead (ZEN_GoblinRespawn: base health x DEFENSE, every goblin type).
HEALTH = {'000814': 110}
DEFAULT_HEALTH = 70
# Defenses x0.65 (curator, 2026-10-21: still too tanky): skin armor ratings here, Mihail's in 01b, and the
# race ability AbFalmer (magic resist 5, poison resist 40) + _00E_AbMagieres10 (magic resist 10) become
# one copy, ZEN_AbGoblin, with magic resist 10 and poison resist 26; its blindness (25) is not a defense.
DEFENSE = 0.65
ABILITY = ('000821', '052FF4', 'ZEN_AbGoblin', '13CB1D')     # new fid, AbFalmer, EditorID, ability folded in
ABILITY_MAGNITUDES = {'0AA024': 26, '053124': 10}           # AbResistPoison 40 -> 26, AbResistMagic 5+10 -> 10
# The race's 8 power attacks carry the Arps' crFalmerPoisonedWeapon02 (109D7E), whose EGO effect crArpPoison
# (0008C9:EGO, Health poison 30 s) runs MagicImodOnPlayerHitScript: PoisonHitImod 10E3D2 / PoisonEndImod 10E3D3,
# a screen blur on the player. Curator 2026-10-22: keep the poison, lose the blur, goblins only (Arps keep it).
# Goblin copies: the spell -> our effect, the effect = EGO's minus its script.
POISON_SPELL = ('000824', '109D7E', 'ZEN_GoblinPoisonedWeapon')
POISON_EFFECT = ('000825', '0008C9', 'ZEN_GoblinPoison')
SKILL_OFFSET = 15
REWARD_EXP = {'000814': 80}
DEFAULT_EXP = 40
# appended to each NPC's script list (Scripts/source/ZEN_GoblinRespawn.psc; the global is 03's)
RESPAWN_SCRIPT = NL.join(['  - Name: ZEN_GoblinRespawn', '    Properties:',
                          '    - MutagenObjectType: ScriptObjectProperty', '      Name: GameDaysPassed',
                          '      Object: 000039:Skyrim.esm',
                          '    - MutagenObjectType: ScriptObjectProperty', '      Name: ZEN_GoblinRespawnDays',
                          f'      Object: 000820:{MOD_KEY}']) + NL
COMBAT_SKILLS = ('OneHanded', 'TwoHanded', 'Archery', 'Block', 'Destruction', 'Alteration', 'Restoration')


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\n', NL)


def write(folder, edid, fid, text):
    d = os.path.join(ESP, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f'{edid} - {fid}_{MOD_KEY}.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def find(ref, folder, fid, plugin='Skyrim.esm'):
    hits = [f for f in os.listdir(os.path.join(ref, folder)) if f.endswith(f'{fid}_{plugin}.yaml')]
    assert len(hits) == 1, (ref, folder, fid, hits)
    return read(os.path.join(ref, folder, hits[0]))


def sub(pattern, repl, text, what, count=1):
    out, n = re.subn(pattern, lambda _: repl, text, flags=re.M)
    assert n == count, (what, pattern, n)
    return out


def rekey(text, fid, edid):
    text = sub(r'^FormKey: .+?(?=\r?$)', f'FormKey: {fid}:{MOD_KEY}', text, 'formkey')   # plugin names have spaces
    return sub(r'^EditorID: \S+(?=\r?$)', f'EditorID: {edid}', text, 'edid')


def race_key():
    return f'{RACE[0]}:{MOD_KEY}'


def build_race():
    fid, src, edid, name = RACE
    t = rekey(find(REF_EGO, 'Races', src), fid, edid)
    t = sub(r'(?<=^Name:\r\n  TargetLanguage: English\r\n  Value: )Falmer(?=\r?$)', name, t, 'name')
    t = sub(r'^Skin: \S+(?=\r?$)', f'Skin: {SKINS["Plain"][1]}:{MOD_KEY}', t, 'skin')
    a_fid, a_src, _, a_folded = ABILITY
    t = sub(r'^ActorEffect:\r\n- ' + a_src + r':Skyrim\.esm\r\n- ' + a_folded + r':Skyrim\.esm\r\n',
            f'ActorEffect:{NL}- {a_fid}:{MOD_KEY}{NL}', t, 'race abilities')
    t = sub(r'(?<=^    Spell: )' + POISON_SPELL[1] + r':Skyrim\.esm(?=\r?$)', f'{POISON_SPELL[0]}:{MOD_KEY}', t,
            'attack poison', count=8)
    write('Races', edid, fid, t)


def build_poison():
    """The goblins' poisoned-weapon attack spell and effect, as EGO's minus the screen blur (see POISON_*)."""
    s_fid, s_src, s_edid = POISON_SPELL
    e_fid, e_src, e_edid = POISON_EFFECT
    ego = goblin_gear.EGO
    s = rekey(find(REF_EGO, 'Spells', s_src), s_fid, s_edid)
    s = sub(r'(?<=^- BaseEffect: )' + e_src + ':' + re.escape(ego) + r'(?=\r?$)', f'{e_fid}:{MOD_KEY}', s, 'spell effect')
    write('Spells', s_edid, s_fid, s)
    e = rekey(find(REF_EGO, 'MagicEffects', e_src, ego), e_fid, e_edid)
    i, j = e.index('VirtualMachineAdapter:' + NL), e.index(NL + 'Name:' + NL)
    assert 'MagicImodOnPlayerHitScript' in e[i:j] and e[i:j].count('  - Name: ') == 1, 'unexpected script list'
    e = e[:i] + e[j + len(NL):]
    assert 'Imod' not in e and '10E3D2' not in e and '10E3D3' not in e, 'blur still referenced'
    write('MagicEffects', e_edid, e_fid, e)


def build_ability():
    fid, src, edid, _ = ABILITY
    t = rekey(find(REF_EGO, 'Spells', src), fid, edid)
    t = sub(r'(?<=^Name:\r\n  TargetLanguage: English\r\n  Value: )Falmer Abilities(?=\r?$)', 'Goblin Abilities', t, 'name')
    for mgef, value in ABILITY_MAGNITUDES.items():
        t = sub(r'(?<=^- BaseEffect: ' + mgef + r':Skyrim\.esm\r\n  Data:\r\n    Magnitude: )\d+(?=\r?$)', str(value), t, (edid, mgef))
    write('Spells', edid, fid, t)


def scale_armor(text, what):
    """ArmorRating x DEFENSE, rounded half up."""
    m = re.findall(r'^ArmorRating: (\d+)(?=\r?$)', text, re.M)
    assert len(m) == 1, (what, m)
    return sub(r'^ArmorRating: \d+(?=\r?$)', f'ArmorRating: {int(int(m[0]) * DEFENSE + 0.5)}', text, (what, 'armor'))


def build_skins():
    for var, (arma_fid, armo_fid, nif, src_armo, src_arma) in SKINS.items():
        a = rekey(find(REF_BASE, 'ArmorAddons', src_arma), arma_fid, f'ZEN_Goblin{var}AA')
        a = sub(r'^Race: 0131F4:Skyrim\.esm(?=\r?$)', f'Race: {race_key()}', a, 'arma race')
        a = sub(r'^    File: .*(?=\r?$)', f'    File: {GOBLIN_DIR}{BS}Goblin_{var}.nif', a, 'arma model')
        a = sub(r'^    Data: 0x[0-9A-F]+\r?\n', '', a, 'arma texture hashes')
        write('ArmorAddons', f'ZEN_Goblin{var}AA', arma_fid, a)

        s = rekey(find(REF_BASE, 'Armors', src_armo), armo_fid, f'ZEN_SkinGoblin{var}')
        s = sub(r'^Race: 0131F4:Skyrim\.esm(?=\r?$)', f'Race: {race_key()}', s, 'armo race')
        s = sub(r'^Armature:\r?\n(- \S+\r?\n)+', f'Armature:{NL}- {arma_fid}:{MOD_KEY}{NL}', s, 'armature')
        s = scale_armor(s, var)
        write('Armors', f'ZEN_SkinGoblin{var}', armo_fid, s)


def build_npcs():
    for fid, (edid, name, src, var) in NPCS.items():
        t = rekey(find(REF_EGO, 'Npcs', src), fid, edid)
        t = sub(r'^Race: 0131F4:Skyrim\.esm(?=\r?$)', f'Race: {race_key()}', t, 'race')
        t = sub(r'^WornArmor: \S+(?=\r?$)', f'WornArmor: {SKINS[var][1]}:{MOD_KEY}', t, 'skin')
        t = sub(r'^    Level: \d+(?=\r?$)', f'    Level: {LEVEL.get(fid, DEFAULT_LEVEL)}', t, 'level')
        t = sub(r'^  HealthOffset: \d+(?=\r?$)', '  HealthOffset: 0', t, 'health offset')
        t = sub(r'^  Health: \d+(?=\r?$)', f'  Health: {HEALTH.get(fid, DEFAULT_HEALTH)}', t, 'health')
        t = sub(r'(?<=^Name:\r\n  TargetLanguage: English\r\n  Value: ).*(?=\r?$)', name, t, 'name')
        t = sub(r'(?<=      Name: RewardExp\r\n      Data: )\d+(?=\r?$)', str(REWARD_EXP.get(fid, DEFAULT_EXP)), t, 'exp')
        assert t.count(NL + 'ObjectBounds:') == 1, edid
        assert t.index('VirtualMachineAdapter:' + NL + '  Scripts:') < t.index('ObjectBounds:'), edid
        t = t.replace(NL + 'ObjectBounds:', NL + RESPAWN_SCRIPT + 'ObjectBounds:', 1)
        offsets = t.index('  SkillOffsets:')
        head, tail = t[:offsets], t[offsets:]
        end = tail.index('\r\n  Health:')
        block = tail[:end]
        for skill in COMBAT_SKILLS:                      # lowered to SKILL_OFFSET, never raised
            pat = r'(?<=  - Key: ' + skill + r'\r\n    Value: )(\d+)(?=\r?$)'
            m = re.findall(pat, block, re.M)
            assert len(m) == 1, (edid, skill, m)
            block = re.sub(pat, str(min(int(m[0]), SKILL_OFFSET)), block, flags=re.M)
        t, dropped = goblin_gear.set_weapons(head + block + tail[end:], ROLE[fid])
        write('Npcs', edid, fid, t)


def build_iron_lists():
    template = find(REF_EGO, 'LeveledItems', '001E46', goblin_gear.EGO)
    for fid, edid, weapons in (goblin_gear.IRON_1H, goblin_gear.IRON_2H):
        write('LeveledItems', edid, fid, goblin_gear.leveled_list(template, fid, edid, weapons))


def extract_falmer():
    spec = importlib.util.spec_from_file_location(
        'etr', os.path.join(REPO, 'src', 'EnderalTextureRestores', 'tools', '01-extract-enderal-textures.py'))
    etr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etr)
    out = os.path.join(OUT_MOD, *FALMER_REL.split(BS))
    os.makedirs(out, exist_ok=True)
    for nif in FALMER_NIFS:
        blob = etr.read_from_bsa(MESHES0, (FALMER_REL + BS + nif).lower())
        assert blob[:20].startswith(b'Gamebryo File Format'), nif
        with open(os.path.join(out, nif), 'wb') as fh:
            fh.write(blob)
    print(f'{len(FALMER_NIFS)} vanilla Falmer bodies <- {os.path.basename(MESHES0)} -> {out}')


def bsa_names(path):
    """Every file path in a BSA (v105), lower case."""
    with open(path, 'rb') as fh:
        head = fh.read(36)
        _, _, fro, _, fcount, filecount, tfnl, tfil, _ = struct.unpack_from('<4sIIIIIIII', head, 0)
        fh.seek(0)
        d = fh.read(fro + fcount * 24 + tfnl + filecount * 16 + fcount + tfil + 64)
    p, counts = fro, []
    for _ in range(fcount):
        counts.append(struct.unpack_from('<QIIQ', d, p)[1])
        p += 24
    dirs = []
    for c in counts:
        ln = d[p]
        dirs += [d[p + 1:p + ln].rstrip(b'\0').decode('latin1')] * c
        p += 1 + ln + 16 * c
    names = d[p:p + tfil].split(b'\0')
    return {(a + BS + b.decode('latin1')).lower() for a, b in zip(dirs, names)}


def available_textures():
    """Lower-case texture paths the game can load: loose in an enabled Ultra mod, or in a game BSA."""
    have = set()
    mods = [ln[1:].strip() for ln in open(os.path.join(ROOT, 'profiles', 'Ultra', 'modlist.txt'), encoding='utf-8')
            if ln.startswith('+')]
    for m in mods:
        root = os.path.join(ROOT, 'mods', m)
        tex = [d for d in (os.listdir(root) if os.path.isdir(root) else []) if d.lower() == 'textures']
        for t in tex:
            for dp, _, files in os.walk(os.path.join(root, t)):
                rel = os.path.relpath(dp, root).replace('/', BS)
                have |= {(rel + BS + f).lower() for f in files}
    for b in glob.glob(os.path.join(ROOT, 'Stock Game', 'Data', '*.bsa')):
        have |= {n for n in bsa_names(b) if n.startswith('textures')}
    return have


def copy_goblins():
    sys.path.insert(0, PYNIFLY)
    from pyn.pynifly import NifFile, nifly
    out = os.path.join(OUT_MOD, 'meshes', *GOBLIN_DIR.split(BS))
    os.makedirs(out, exist_ok=True)
    have = available_textures()
    for var, (_, _, nif, _, _) in SKINS.items():
        src = os.path.join(GOBLINS, nif)
        assert os.path.isfile(src), src
        dst = os.path.join(out, f'Goblin_{var}.nif')
        fixes = {shape: tex for (v, shape), tex in RETEXTURE.items() if v == var}
        if not fixes:
            shutil.copyfile(src, dst)
        else:
            n = NifFile(src)
            done = 0
            for sh in n.shapes:
                if sh.name in fixes:
                    for slot, path in enumerate(fixes[sh.name]):
                        nifly.setShaderTextureSlot(n._handle, sh._handle, slot, path.encode('utf-8'))
                    done += 1
            assert done == len(fixes), (var, done, fixes)
            n.filepath = dst
            n.save()
        missing = []
        for sh in NifFile(dst).shapes:                # every texture each shape asks for must exist
            for slot, path in sh.textures.items():
                if path and slot in ('Diffuse', 'Normal') and path.lower() not in have                         and ('textures' + BS + path).lower() not in have:
                    missing.append(f'{sh.name}:{slot}={path}')
        assert not missing, (var, missing)
    print(f'{len(SKINS)} goblin bodies <- Goblins -> {out} ({len(RETEXTURE)} shapes retextured; all textures present)')


def main():
    for folder in ('Races', 'ArmorAddons', 'Armors', 'Npcs', 'Spells', 'LeveledItems', 'MagicEffects'):
        shutil.rmtree(os.path.join(ESP, folder), ignore_errors=True)
    build_race()
    build_ability()
    build_poison()
    build_iron_lists()
    build_skins()
    build_npcs()
    extract_falmer()
    copy_goblins()
    print(f'race {RACE[2]}, {len(SKINS)} skins, {len(NPCS)} NPCs -> {os.path.normpath(ESP)}')


if __name__ == '__main__':
    main()
