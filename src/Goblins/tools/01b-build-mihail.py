"""Copy Mihail's goblins and durzog into `Zenderal - Goblins`, fixed up for Enderal. Run after 01 (01
clears the record folders this also writes into). Never hand-edit what this writes.

Source: `Goblins - Mihail Monsters and Animals (SE-AE version)` v4 (Nexus Skyrim SE 24525), a SKYRIM mod.
Its plugin `mihailgoblins.esp` is DISABLED in Ultra since 2026-10-21. It places 530 refs into Tamriel
00003C, which in Enderal is MQP01Home, and some of them override Enderal records of other types: a
placed goblin on FormID 085945, which is the MQ01Campsite navmesh (Jespar's camp); cells on Ark refs. Its
loose meshes, textures and sounds stay installed and are REQUIRED. Serialize the plugin into
reference/mods/MihailGoblins with the spriggit-decompile-reference skill.

Copied: the closure of the six goblin types and the Tamed Durzog over records local to the plugin
(races, skins/ARMAs, shields, staff, death-item LVLI, durzog disease/loot/impacts/sounds, voice dummy).
Factions, form lists, cells and worldspaces are not copied. Each copy gets a new FormID in
`Zenderal - Goblins.esp` (0x830 up, sorted by source FormID) and the EditorID prefix `ZEN_Mihail_`.

Fixes, each asserted:
  * every reference to a form Enderal does not have (vanilla weapons, Dragonborn/Dawnguard forms, Argonian
    race presets, ...) is dropped with its list item; a scalar field that breaks is replaced explicitly:
    Voice (Dragonborn riekling) -> Arp voice 01F1D2 (goblins) / CrSkeeverVoice 019FE5 (durzog);
    InheritsSoundsFrom (Dragonborn) -> 0ADFA2, as the Arps;
  * factions: goblin1 gets Template ZEN_Goblin (Factions flag); Mihail already chains the other types and
    the durzog to goblin1, so all of them are in the Arp faction, allied with our goblins and the Arps;
  * weapons: each type gets the matching Arp's inventory (EGO's winning record) added to its surviving
    items (Mihail's own shields/staff/clothes); the shaman's spells are the Arp shaman's;
  * weak: a fixed level (5-10) instead of PC level x1 (2-22), AutoCalcStats kept;
  * Enderal EP on death (_00E_EPOnDeath, smaller RewardExp) and ZEN_GoblinRespawn, copied from ZEN_Goblin's
    script list.
Writes `mihail-npcs.json` (role -> new NPC FormID; 03 places them).

Usage:  python 01b-build-mihail.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goblin_gear  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference')
MG = os.path.join(REF, 'mods', 'MihailGoblins')
ESP = os.path.join(HERE, '..', 'GoblinsESP')
OUT_JSON = os.path.join(HERE, 'mihail-npcs.json')
SRC_KEY = 'mihailgoblins.esp'
MOD_KEY = 'Zenderal - Goblins.esp'
FIRST_FID = 0x830
LAST_FID = 0x8FF
NL = '\r\n'
SKIP_FOLDERS = {'Factions', 'FormLists', 'Cells', 'Worldspaces'}
ENDERAL_SOURCES = [os.path.join(REF, *p) for p in (('base', 'Skyrim'), ('base', 'EnderalFS'), ('base', 'Update'),
                                                     ('mods', 'EGO'))]
ALLOW = {'000014:Skyrim.esm'}                     # PlayerRef: valid, absent from the serialized base
FK = re.compile(r'(?<![0-9A-F])([0-9A-F]{6}):([^\r\n,\]]+?\.(?:esm|esp|esl))')
ZEN_GOBLIN = f'000810:{MOD_KEY}'
ZEN_GOBLIN_YAML = os.path.join(ESP, 'Npcs', f'ZEN_Goblin - 000810_{MOD_KEY}.yaml')

# role -> (Mihail NPC, level, RewardExp, Arp whose inventory (EGO winner) it gets, replace spells with the Arp's)
ROLES = {
    'MGoblin': ('000803', 5, 30, '0B5270', False),
    'MArcher': ('000805', 5, 30, '0EB408', False),
    'MSkirmisher': ('00080A', 6, 35, '0B5272', False),
    'MBerserker': ('00080B', 7, 40, '0B5270', False),
    'MShaman': ('00080C', 7, 45, '0B5266', True),
    'MWarlord': ('00080D', 10, 80, '0B5270', False),
    'Durzog': ('000942', 5, 25, None, False),
}
GOBLIN_VOICE = '01F1D2:Skyrim.esm'                # FalmerRace's (the Arps') voice type
DURZOG_VOICE = '019FE5:Skyrim.esm'                # CrSkeeverVoice, the durzog race's own
ARP_SOUNDS = '0ADFA2:Skyrim.esm'                  # what Enderal's Arps inherit their sounds from
DEFENSE = 0.65                                    # armor ratings x0.65 (= 01's DEFENSE); health is the script's


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\n', NL)


def index(roots):
    out = {}
    for root in roots:
        for folder in os.listdir(root):
            d = os.path.join(root, folder)
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                m = re.search(r'([0-9A-F]{6})_(.+)\.yaml$', f)
                if m:
                    out[f'{m.group(1)}:{m.group(2)}'] = (folder, os.path.join(d, f))
    return out


def sub(pattern, repl, text, what, count=1):
    out, n = re.subn(pattern, lambda _: repl, text, flags=re.M)
    assert n == count, (what, pattern, n)
    return out


def drop_missing(text, ok, what):
    """Remove every list item that names a form `ok()` rejects. A broken scalar field is an error: the
    caller must have replaced it first."""
    lines = text.split(NL)
    dropped, i = [], 0
    while i < len(lines):
        bad = [f'{a}:{b}' for a, b in FK.findall(lines[i]) if not ok(f'{a}:{b}')]
        if not bad:
            i += 1
            continue
        # the enclosing list item: this line or the nearest line above that starts an item at lower indent
        j = i
        ind = len(lines[i]) - len(lines[i].lstrip(' '))
        while j >= 0 and not lines[j].lstrip(' ').startswith('- '):
            j -= 1
            if j >= 0 and len(lines[j]) - len(lines[j].lstrip(' ')) > ind:
                continue
        assert j >= 0, (what, 'broken scalar', lines[i])
        item_ind = len(lines[j]) - len(lines[j].lstrip(' '))
        assert i - j <= 3, (what, 'item too far above', lines[j], lines[i])
        k = j + 1
        while k < len(lines) and lines[k].strip() and len(lines[k]) - len(lines[k].lstrip(' ')) > item_ind:
            k += 1
        dropped += bad
        head = lines[j - 1] if j > 0 else ''
        del lines[j:k]
        # an emptied list leaves its key behind: drop the key too
        if head.rstrip().endswith(':') and (j >= len(lines) or not lines[j].lstrip(' ').startswith('- ')
                                            or len(lines[j]) - len(lines[j].lstrip(' ')) != item_ind):
            if len(head) - len(head.lstrip(' ')) <= item_ind and not head.lstrip(' ').startswith('- '):
                del lines[j - 1]
                j -= 1
        i = j
    return NL.join(lines), dropped


def main():
    mihail = index([MG])
    enderal = index(ENDERAL_SOURCES)

    # closure over records local to the plugin
    todo = [f'{r[0]}:{SRC_KEY}' for r in ROLES.values()]
    closure = set()
    while todo:
        k = todo.pop()
        if k in closure:
            continue
        folder, path = mihail[k]
        if folder in SKIP_FOLDERS:
            continue
        closure.add(k)
        for a, b in FK.findall(read(path)):
            if b == SRC_KEY and f'{a}:{b}' not in closure:
                todo.append(f'{a}:{b}')
    order = sorted(closure)
    remap = {k: f'{FIRST_FID + n:06X}:{MOD_KEY}' for n, k in enumerate(order)}
    assert FIRST_FID + len(order) - 1 <= LAST_FID, 'block 0x830-0x8FF exhausted'

    def ok(key):
        return key in enderal or key in ALLOW or key.endswith(':' + MOD_KEY) or key in remap

    zen_vmad = read(ZEN_GOBLIN_YAML)
    zen_vmad = zen_vmad[zen_vmad.index('VirtualMachineAdapter:'):zen_vmad.index(NL + 'ObjectBounds:') + len(NL)]
    role_of = {f'{v[0]}:{SRC_KEY}': (r, v) for r, v in ROLES.items()}
    report = []
    for k in order:
        folder, path = mihail[k]
        t = read(path)
        edid = re.search(r'^EditorID: (\S+)', t, re.M).group(1)
        new_edid = 'ZEN_Mihail_' + edid
        if folder == 'Armors':                     # skins and shields: defenses x0.65, as 01's skins
            m = re.findall(r'^ArmorRating: ([\d.]+)(?=\r?$)', t, re.M)
            assert len(m) <= 1, (edid, m)
        if folder == 'Armors' and m:                # Mihail's skins carry none (0)
            t = sub(r'^ArmorRating: [\d.]+(?=\r?$)', f'ArmorRating: {int(float(m[0]) * DEFENSE + 0.5)}', t, (edid, 'armor'))
            report.append(f'    ZEN_Mihail_{edid}: ArmorRating {m[0]} -> {int(float(m[0]) * DEFENSE + 0.5)}')
        if folder == 'Npcs':
            t = re.sub(r'^Voice: \S+(?=\r?$)', lambda _: 'Voice: ' + (DURZOG_VOICE if k.startswith('000942') else GOBLIN_VOICE), t, flags=re.M)
            t = re.sub(r'^(  InheritsSoundsFrom: )\S+:(?:Dragonborn|Dawnguard)\.esm(?=\r?$)', lambda m: m.group(1) + ARP_SOUNDS, t, flags=re.M)
        if k in role_of:
            role, (_, level, exp, arp, arp_spells) = role_of[k]
            t = sub(r'^    MutagenObjectType: PcLevelMult\r\n    LevelMult: [\d.]+\r\n', f'    MutagenObjectType: NpcLevel{NL}    Level: {level}{NL}', t, (edid, 'level'))
            t = sub(r'^  CalcMinLevel: \d+\r\n', '', t, (edid, 'min'))
            t = sub(r'^  CalcMaxLevel: \d+\r\n', '', t, (edid, 'max'))
            if role == 'MGoblin':                     # the faction root of every Mihail NPC
                assert 'Template:' not in t and 'TemplateFlags' not in t, edid
                t = sub(r'(?<=\r\n)(  HealthOffset: )', f'  TemplateFlags:{NL}  - Factions{NL}  HealthOffset: ', t, (edid, 'tflags'))
                t = sub(r'^(Race: )', f'Template: {ZEN_GOBLIN}{NL}Race: ', t, (edid, 'template'))
            else:
                assert re.search(r'^Template: 000803:mihailgoblins\.esp(?=\r?$)', t, re.M) and '  - Factions' in t, edid
            vmad = re.sub(r'(?<=      Name: RewardExp\r\n      Data: )\d+', str(exp), zen_vmad)
            assert 'VirtualMachineAdapter' not in t, edid
            t = sub(r'^(ObjectBounds:)', vmad + 'ObjectBounds:', t, (edid, 'vmad'))
            if arp:
                src = read(enderal[f'{arp}:Skyrim.esm'][1])         # index() keeps the last root: EGO's winner
                assert os.sep + 'EGO' + os.sep in enderal[f'{arp}:Skyrim.esm'][1], arp
                items = re.search(r'^Items:\r\n((?:[- ] .*\r\n)+)', src, re.M).group(1)
                if 'Items:' in t:
                    t = sub(r'^Items:\r\n', 'Items:' + NL + items, t, (edid, 'items'))
                else:
                    t = sub(r'^(AIData:)', 'Items:' + NL + items + 'AIData:', t, (edid, 'items new'))
                if arp_spells:
                    spells = re.search(r'^ActorEffect:\r\n((?:- .*\r\n)+)', src, re.M).group(1)
                    t = re.sub(r'^ActorEffect:\r\n(?:- .*\r\n)+', lambda _: 'ActorEffect:' + NL + spells, t, flags=re.M)
            if role in goblin_gear.ROLE_GEAR:          # iron weapons; the shaman's staff goes too
                t, gone = goblin_gear.set_weapons(t, role, extra_drop={f'00080E:{SRC_KEY}'})
                report.append(f'    {new_edid}: weapons {", ".join(gone)} -> iron')
            report.append(f'{role:12} {remap[k][:6]} {new_edid} level {level} exp {exp}')
        # rekey: own FormKey, EditorID, then every local reference
        t = sub(r'^EditorID: \S+(?=\r?$)', f'EditorID: {new_edid}', t, (edid, 'edid'))
        t = FK.sub(lambda m: remap.get(f'{m.group(1)}:{m.group(2)}', m.group(0)), t)
        t, dropped = drop_missing(t, ok, new_edid)
        if dropped:
            report.append(f'    {new_edid}: dropped {len(dropped)} refs to forms Enderal lacks: {", ".join(sorted(set(dropped)))[:200]}')
        bad = [f'{a}:{b}' for a, b in FK.findall(t) if not ok(f'{a}:{b}')]
        assert not bad, (new_edid, bad)
        d = os.path.join(ESP, folder)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f'{new_edid} - {remap[k].replace(":", "_")}.yaml'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(t)
    with open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({r: remap[f'{v[0]}:{SRC_KEY}'][:6] for r, v in ROLES.items()}, fh, indent=2)
        fh.write('\n')
    print('\n'.join(report))
    print(f'{len(order)} Mihail records -> {FIRST_FID:03X}-{FIRST_FID + len(order) - 1:03X}; roles -> {OUT_JSON}')


if __name__ == '__main__':
    main()
