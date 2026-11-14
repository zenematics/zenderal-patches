"""Read the winning NPC and faction data Enemy Threat needs, with Enderal's template chains resolved.

Sources, in load order (later wins per record): Enderal 2.1.4.4's Skyrim.esm, Update.esm and Forgotten Stories
(reference/base-2.1.4.4/), then EGO (reference/mods/EGO). EGO is the only list plugin that re-tiers enemies
(levels, factions, keywords on ~1100 NPCs). Undead Creatures Replacer and Lost Ones Revised (+ its EGO patch) follow,
as in Fog Wood's arena: Lost Ones Revised moves some undead onto Mihail's skeleton race, which crashed Enemy Density's
hordes, so the race those records win with matters.

The YAML is read line by line (no PyYAML here): only the fields below are needed, and they all sit at fixed
indentation in Spriggit's NPC/FACT layout.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(REPO, 'reference')
SOURCES = [
    os.path.join(REF, 'base-2.1.4.4', 'Skyrim'),
    os.path.join(REF, 'base-2.1.4.4', 'Update'),
    os.path.join(REF, 'base-2.1.4.4', 'EnderalFS'),
    os.path.join(REF, 'mods', 'EGO'),
    os.path.join(REF, 'mods', 'UndeadCreaturesReplacer'),
    os.path.join(REF, 'mods', 'LostOnesRevised'),            # its ModKey is mihailancientskeletons.esp
    os.path.join(REF, 'mods', 'LostOnesRevisedEGOPatch'),
    # this repo's own NPC overrides, in Ultra's load order: Undead Creatures Replacer drops ActorTypeBoss from
    # Zu-Sherath, Krustis Darkhand and Ea, and our UCR x EGO patch (loading after it) puts it back
    os.path.join(REPO, 'src', 'UndeadCreaturesReplacerEGO', 'UndeadCreaturesReplacerEGOESP'),
    os.path.join(REPO, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP'),
    os.path.join(REPO, 'src', 'MalphasFixesMerge', 'MalphasFixesMergeESP'),
    os.path.join(REPO, 'src', 'LostOneArcherAmmo', 'LostOneArcherAmmoESP'),
    os.path.join(REPO, 'src', 'JesparMerge', 'JesparMergeESP'),
    os.path.join(REPO, 'src', 'UnresolvedRefsCleanup', 'UnresolvedRefsCleanupESP'),
]

BOSS_KEYWORD = '090CA9:Skyrim.esm'      # ActorTypeBoss (boss music in _00E_CombatSoundtrackScript)
BOSSES_FACTION = '03C755:Skyrim.esm'    # BossesFaction

# TemplateFlags bit -> the fields that bit hands over to the template
TEMPLATE_FIELDS = {
    'Stats': ('level', 'health_offset'),
    'Factions': ('factions',),
    'Keywords': ('keywords',),
    'Script': ('scripts', 'reward'),
    'Traits': ('race', 'name'),
    'BaseData': ('flags',),
    'AIPackages': ('packages',),
}


def _english_name(lines, i):
    # Name:\n  TargetLanguage: English\n  Value: X   or   Values: [... Language: English\n String: X]
    for j in range(i + 1, min(i + 40, len(lines))):
        s = lines[j]
        if not s.startswith(' '):
            break
        m = re.match(r'\s+Value: (.*)$', s)
        if m:
            return m.group(1).strip().strip("'\"")
        if s.strip() == '- Language: English' and j + 1 < len(lines):
            m = re.match(r'\s+String: (.*)$', lines[j + 1])
            if m:
                return m.group(1).strip().strip("'\"")
    return ''


def read_npc(path):
    text = open(path, encoding='utf-8-sig').read()
    lines = text.splitlines()
    r = {'path': path, 'scripts': [], 'factions': [], 'keywords': [], 'flags': [], 'template_flags': [],
         'level': None, 'health_offset': 0, 'packages': [], 'reward': None, 'template': None, 'race': None, 'name': '',
         'edid': '', 'fk': ''}
    section = None
    sub = None
    for i, s in enumerate(lines):
        if not s.startswith(' ') and not s.startswith('-'):
            key = s.split(':', 1)[0]
            section = key
            if key == 'FormKey':
                r['fk'] = s.split(': ', 1)[1].strip()
            elif key == 'EditorID':
                r['edid'] = s.split(': ', 1)[1].strip()
            elif key == 'Template':
                r['template'] = s.split(': ', 1)[1].strip()
            elif key == 'Race':
                r['race'] = s.split(': ', 1)[1].strip()
            elif key == 'Name':
                r['name'] = _english_name(lines, i)
            continue
        if section == 'VirtualMachineAdapter':
            m = re.match(r'  - Name: (\S+)', s)
            if m:
                r['scripts'].append(m.group(1))
            m = re.match(r'\s+Name: RewardExp$', s)
            if m:
                for j in range(i + 1, i + 3):
                    mm = re.match(r'\s+Data: (-?\d+)', lines[j])
                    if mm:
                        r['reward'] = int(mm.group(1))
        elif section == 'Configuration':
            m = re.match(r'    Level: (\d+)', s)
            if m:
                r['level'] = int(m.group(1))
            m = re.match(r'  HealthOffset: (-?\d+)', s)
            if m:
                r['health_offset'] = int(m.group(1))
            if s.startswith('  Flags:'):
                sub = 'flags'
            elif s.startswith('  TemplateFlags:'):
                sub = 'template_flags'
            elif re.match(r'  \S', s):
                sub = None
            m = re.match(r'  - (\S+)$', s)
            if m and sub:
                r[sub].append(m.group(1))
        elif section == 'Factions':
            m = re.match(r'- Faction: (\S+)', s)
            if m:
                r['factions'].append(m.group(1))
        elif section == 'Packages':
            m = re.match(r'- (\S+:\S.*)$', s)
            if m:
                r['packages'].append(m.group(1).strip())
        elif section == 'Keywords':
            m = re.match(r'- (\S+:\S.*)$', s)
            if m:
                r['keywords'].append(m.group(1).strip())
    return r


def load_npcs():
    npcs = {}
    for src in SOURCES:
        for p in glob.glob(os.path.join(src, 'Npcs', '*.yaml')):
            r = read_npc(p)
            npcs[r['fk']] = r
    return npcs


def resolve(npcs, fk, depth=0):
    """The NPC as the game sees it: each TemplateFlags bit takes its fields from the template's resolved record."""
    r = dict(npcs[fk])
    t = r.get('template')
    if t and t in npcs and depth < 10:
        base = resolve(npcs, t, depth + 1)
        for flag, fields in TEMPLATE_FIELDS.items():
            if flag in r['template_flags']:
                for f in fields:
                    r[f] = base[f]
    return r


def load_factions():
    """FormKey -> {'edid', 'self_ally'}: members of a faction are only allies when it lists itself as Ally."""
    out = {}
    for src in SOURCES:
        for p in glob.glob(os.path.join(src, 'Factions', '*.yaml')):
            text = open(p, encoding='utf-8-sig').read()
            fk = re.search(r'^FormKey: (\S+)', text, re.M).group(1)
            edid = (re.search(r'^EditorID: (\S+)', text, re.M) or [None, ''])[1]
            self_ally = bool(re.search(r'- Target: %s\r?\n\s+Reaction: Ally' % re.escape(fk), text))
            out[fk] = {'edid': edid, 'self_ally': self_ally}
    return out


def load_package_overrides():
    """Package FormKey -> InterruptOverride for every package that has one: such a package runs instead of combat
    (Fog Wood's Vagrant stood still in its sandbox-sit package, 2026-11-09)."""
    out = {}
    for src in SOURCES:
        for p in glob.glob(os.path.join(src, 'Packages', '*.yaml')):
            text = open(p, encoding='utf-8-sig').read()
            fk = re.search(r'^FormKey: (\S+)', text, re.M).group(1)
            m = re.search(r'^InterruptOverride: (\w+)', text, re.M)
            if m:
                out[fk] = m.group(1)
            else:
                out.pop(fk, None)
    return out


def load_races():
    """Race FormKey -> (EditorID, has ActorTypeNPC 013794): Enderal's people races carry it, its creatures don't."""
    out = {}
    for src in SOURCES:
        for p in glob.glob(os.path.join(src, 'Races', '*.yaml')):
            text = open(p, encoding='utf-8-sig').read()
            fk = re.search(r'^FormKey: (\S+)', text, re.M).group(1)
            edid = (re.search(r'^EditorID: (\S+)', text, re.M) or [None, ''])[1]
            out[fk] = (edid, '013794:Skyrim.esm' in text)
    return out
