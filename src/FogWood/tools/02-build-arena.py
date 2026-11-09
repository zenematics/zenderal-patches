"""Generate the Fog Wood arena records into src/FogWood/FogWoodESP/: the quest, the Fogbound Stone, the arena
faction, the wave THEMES (one creature kind per wave) grouped into tiers, the two werewolf bases, the potions,
the pack-size globals, the wave globals and the message boxes.

The space itself (worldspace, navmesh, markers, the exit stone's placed ref) comes from tools/01; the scripts in
Scripts/source/ carry the logic (ZFW_ArenaQuest, ZFW_PlayerAlias, ZFW_StoneScript). IDs 0x804-0x816 (arena
core), 0x4000-0x40FF (themes: 5 records each), 0x4100-0x4101 (werewolves). The cells/refs end at 0x337A.

A theme (curator, 2026-11-05: "waves should all be part of the same faction - skeleton wave, goblin wave etc",
"Liches when the waves are Lost One / undead, Arp shamans with goblins, werewolves with wolves") is a FormList of
five entries the script reads by index: [0] regulars (one kind), [1] elites, [2] bosses, [3] a MESG whose name is
shown ("Wave 4: 22 Fleshless Lost Ones"), [4] a GlobalVariable scaling the pack size (trolls, bears, giants come
in smaller packs). Tier FormLists hold the themes a wave number may draw from; a theme may sit in several tiers.

The roster is Enderal's own wilderness creatures by level (the EditorID's _NNE_ prefix), all of them placed-type
bases Enemy Density already spawns across Vyn, none tied to a quest or a story character (curator: nothing that
can spoil the main quest), plus the Goblins mod's goblins (Zenderal - Goblins.esp is a master). Enderal has no
werewolf creature base (the NQ29 boss is a human who transforms), so ZFW_Werewolf / ZFW_WerewolfAlpha are new
records on Skyrim's WerewolfBeastRace, which Enderal's Skyrim.esm keeps with its skin, skeleton, behaviour graph,
csWerewolf, EncClassWerewolf(Boss), CrWerewolfVoice and AbWerewolf (the Theriantrophist form proves the assets
load). Enderal's lich is the Lord of the Lost Ones (dragon-priest body): the undead themes' elite.

No elementals among elites or bosses until the musket-vs-Ice-Elemental hit registration is understood (curator
2026-11-05: most direct musket shots at an elite Ice Elemental did no damage). No goblin shamans: a goblin
shaman's lightning bolt freeing a dead Havok body is an open crash (memory, 2026-10-26).

Mihail skeletons: Lost Ones Revised re-races most of Enderal's Fleshless Lost Ones onto mihailancientskeletons'
race, whose weapon attach crashed twice in Enemy Density's hordes (EnemyDensity.md; Enemy Density refuses them).
This generator reports every regular base whose WINNING record is on that race, so the risk is a known one.

Run from the repo root: python -I src/FogWood/tools/02-build-arena.py
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'FogWoodESP'))
PLUGIN = 'Zenderal - Fog Wood.esp'
WOLF_SRC = os.path.join(ROOT, 'reference', 'base-2.1.4.4', 'Skyrim', 'Npcs', '_35E_Schneewolf - 15017E_Skyrim.esm.yaml')
MIHAIL = 'mihailancientskeletons.esp'
# plugins that override creature bases, in load order (later wins); only the NPC folders are read
OVERRIDERS = ['EGO', 'UndeadCreaturesReplacer', 'LostOnesRevised', 'LostOnesRevisedEGOPatch']

ID_QUEST, ID_STONE, ID_FACTION = 0x804, 0x805, 0x806
ID_TIERS = [0x807, 0x808, 0x809, 0x80A, 0x80B]
ID_POTIONS = 0x80D
ID_BEST, ID_WAVE = 0x80E, 0x80F
ID_ENTER_MSG, ID_LEAVE_MSG = 0x810, 0x811
# 0x80C (ZFW_Bosses) and 0x812 (ZFW_Elites) were the first arena's flat lists: retired, never reuse
ID_PACKS = {1.0: (0x813, 'ZFW_PackFull'), 0.5: (0x814, 'ZFW_PackHalf'), 0.35: (0x815, 'ZFW_PackThird'), 0.7: (0x816, 'ZFW_PackMost')}
# 0x80D ZFW_HealthPotions (was ZFW_Potions), 0x817 ZFW_ManaPotions
ID_THEMES_ALL, ID_WAVE_SIZE = 0x818, 0x819   # every theme in order (objective index = theme index); the wave's pack size
# Quest objectives = the wave banner (curator, 2026-11-06: "large in the centre screen like the quest text"): the
# script shows objective OBJ_WAVE0 + theme index (or OBJ_BOSS0 + index on a boss wave) with text replacement
# <Global=ZFW_CurrentWave>, <Global=ZFW_WaveSize> and <Alias=ZFW_Spawn01> (the boss fills alias 1).
OBJ_CLEARED, OBJ_START, OBJ_WAVE0, OBJ_BOSS0 = 1, 2, 10, 50
# Fogbound Caches (curator, 2026-11-06: random chests through the wood with potions): CONT ZFW_Chest, a copy of
# Skyrim's ChestSmall02EMPTY 0EF052 (Chest01.nif) named Fogbound Cache, placed and stocked by the script at run
# start and after every boss wave; the resistance potions are every tier Enderal ships (Protection from Fire
# Cheap/Exclusive, Frost Cheap, Shock Cheap/Enhanced, Magic: only the Rancid one exists).
ID_CHEST, ID_CACHE_POTIONS = 0x81A, 0x81B
ID_QUEST_VERSION, ID_PERSIST = 0x81C, 0x81D   # the one-time quest restart (see ZFW_StoneScript) and what survives it
CHEST_SRC = os.path.join(ROOT, 'reference', 'base-2.1.4.4', 'Skyrim', 'Containers', 'ChestSmall02EMPTY - 0EF052_Skyrim.esm.yaml')
ID_THEME0, THEME_STRIDE = 0x4000, 5
ID_WEREWOLF, ID_WEREWOLF_ALPHA, ID_WEREWOLF_YOUNG = 0x4100, 0x4101, 0x4102
ID_WRLD, ID_ENTRY, ID_SPAWN0, SPAWN_COUNT = 0x800, 0x954, 0x955, 12
ID_CACHE0, CACHE_COUNT = 0x962, 40      # tools/01's cache markers: clear lattice vertices, no tree within a vertex

SK = ':Skyrim.esm'
FS = ':Enderal - Forgotten Stories.esm'
GB = ':Zenderal - Goblins.esp'

PLAYER = '000007' + SK
PLAYER_REF = '000014' + SK
EP_FACTION = '039DCE' + SK            # EPFaction: _00E_EPOnDeath pays kill EP only to a killer in it
PLAYER_FACTION = '000DB1' + SK
# The stone stands in the north-Heartland pine forest (curator, 2026-11-06: the Fog Wood is a pine wood, so its door
# belongs in Enderal's), cell (-18, 8) between the Tower Encampment and Castle Bleakstar: the navmesh vertex with the
# most clearance from every placed ref there (369 units; Castle Bleakstar's refs 4,283 away, the nearest Goblins
# pack 1,343). Until 2026-11-06 it stood in Whisperwood at (-83776, 16832, 4452), cell (-21, 4); the script moves an
# already placed stone when STONE_VERSION changes.
# The script carries the spot and the anchor as AutoReadOnly constants (STONE_X/Y/Z, STONE_ANCHOR_ID): quest script
# property values live in the save, so a rebuilt plugin could never move a placed stone through them. StoneAnchor
# below is only the fallback the script uses when GetFormFromFile fails.
STONE_ANCHOR = '132F43' + SK          # Tower Encampment map marker, a persistent Vyn ref 5,143 units from the spot
STONE_POS = (-72640.0, 33856.0, 642.0)   # documentation only: the script constants are the truth
STONE_ANGLE = 0.0
STONE_MODEL = r'Clutter\PowerShrines\PowerShrine01\ShadowStone.nif'   # Skyrim - Meshes0.bsa, in the list

WEREWOLF = '%06X:%s' % (ID_WEREWOLF, PLUGIN)
WEREWOLF_ALPHA = '%06X:%s' % (ID_WEREWOLF_ALPHA, PLUGIN)
WEREWOLF_YOUNG = '%06X:%s' % (ID_WEREWOLF_YOUNG, PLUGIN)
LORD30, LORD38, LORD55 = '1278CD' + SK, '13CA4B' + SK, '036531' + SK     # Lord of the Lost Ones (the lich)
ARP_SHAMAN = '0B5266' + SK            # _18E_ArpSchamane_Aggressive
GROTESQUE20, GROTESQUE50 = '150387' + SK, '02320C' + SK
CACHE_POTIONS = ['08A51F' + SK, '13E807' + SK, '0D9199' + SK, '0907BB' + SK, '0907B9' + SK, '014E2C' + SK]
STAMINA_POTION = '11A52F' + SK      # 02E_Ausdauertrank, Fortify Stamina Potion (Enhanced)

# (edid, shown name, tiers, pack scale, regulars, elites, bosses)
THEMES = [
    ('Skeletons', 'Fleshless Lost Ones', [1, 2], 1.0,
     # only bases whose WINNING record keeps the vanilla SkeletonRace (Lost Ones Revised re-races the rest onto
     # Mihail's, which crashed Enemy Density's hordes twice: EnemyDensity.md)
     ['0672C8' + SK, '02F48E' + FS, '0FE46B' + SK, '048388' + SK, '02F4C7' + FS],
     ['107183' + SK],                                   # Conjured Guardian L25 (vanilla race)
     ['107183' + SK]),
    ('LostOnes', 'Lost Ones', [1], 1.0,
     ['046EDC' + SK, '046EEC' + SK, '0849A3' + SK, '09286C' + SK, '092873' + SK],
     [LORD30],
     [GROTESQUE20, LORD38]),
    ('Goblins', 'Goblins', [1], 1.0,
     ['000810' + GB, '000811' + GB, '000812' + GB, '000833' + GB, '000835' + GB, '00083A' + GB],
     [ARP_SHAMAN],
     ['000814' + GB]),                                  # Goblin Chieftain
    # half the pack are werewolves (curator 2026-11-06: 50/50 split, weaker ones in the pack, the full-grown as the
    # elite or two a wave brings)
    ('Wolves', 'Wolves and Werewolves', [1], 1.0,
     ['07B30B' + SK, '0FE4B3' + SK, WEREWOLF_YOUNG, WEREWOLF_YOUNG],
     [WEREWOLF],
     [WEREWOLF_ALPHA]),
    ('Arps', 'Arps', [2], 1.0,
     ['0B5270' + SK, '0B5272' + SK, '0B5274' + SK, '0EB408' + SK],
     [ARP_SHAMAN],
     ['0ADFA2' + SK]),                                  # Tomb Guardian (L35 Arp)
    ('GoblinWarband', 'Goblin Warband', [2], 1.0,
     ['00083B' + GB, '00083A' + GB, '000812' + GB, '000835' + GB, '000847' + GB, '000847' + GB],   # berserkers, skirmishers, archers, durzogs
     [ARP_SHAMAN, '00083D' + GB],                       # + Goblin Warlord
     ['000814' + GB]),
    ('LostOneWarband', 'Lost One Warband', [2], 1.0,
     ['0C675A' + SK, '0C6762' + SK, '0C6760' + SK, '1105CE' + SK, '1105CC' + SK, '11C3F4' + SK],
     [LORD30],
     [LORD38, GROTESQUE20]),
    ('FleshlessHost', 'Fleshless Host', [2, 3], 1.0,
     ['02F4CB' + FS, '02F4C8' + FS, '02F4CC' + FS, '02F4C6' + FS, '090BBE' + SK, '02F4C9' + FS, '090BBF' + SK, '02F4C7' + FS],
     ['107183' + SK],
     [LORD30]),
    ('Vatyrs', 'Vatyrs', [2], 1.0,
     ['0BF5D1' + SK, '0BF5D0' + SK, '0BF5CF' + SK, '102A1A' + SK, '110623' + SK, '110626' + SK],
     ['102A1B' + SK],                                   # Vatyr Leader L24
     ['12EBEA' + SK]),                                  # Vatyr Leader L35
    ('PusBeetles', 'Pus Beetles', [2], 0.7,
     ['0FEC83' + SK],
     ['1337A8' + SK],
     ['1337A8' + SK]),
    ('WitheredLostOnes', 'Withered Lost Ones', [3, 5], 1.0,
     ['090BB9' + SK, '04BB66' + SK, '090BBA' + SK, '090BBB' + SK, '090BBC' + SK, '090BBD' + SK, '04BB61' + SK, '090A0F' + SK],
     [LORD38],
     [GROTESQUE50]),
    ('Spiders', 'Spiders', [3], 1.0,
     ['06A2DF' + SK, '093C96' + SK],
     ['150248' + SK],                                   # Frost Crawler
     ['06A2E0' + SK]),                                  # Desert Spider Queen
    ('HuntingCats', 'Hunting Cats', [3], 0.7,
     ['08F719' + SK, '13BFB8' + SK, '0FE48B' + SK, '08F71C' + SK],
     ['13E0F9' + SK],                                   # Lion
     ['13E0F9' + SK]),
    ('SnowWolves', 'Snow Wolves and Werewolves', [3, 4, 5], 1.0,
     ['0D942E' + SK, '15017E' + SK, '0D9751' + SK, WEREWOLF, WEREWOLF, WEREWOLF],
     [WEREWOLF_ALPHA],
     [WEREWOLF_ALPHA]),
    ('CaveTrolls', 'Cave Trolls', [3], 0.35,
     ['0316A2' + SK, '0E73E8' + SK, '12EBDC' + SK],
     ['1356A3' + SK],
     ['1356A3' + SK]),
    ('Bears', 'Bears', [3], 0.5,
     ['04D9C6' + SK, '11C3BC' + SK],
     ['0D9404' + SK],                                   # Ice Bear L29
     ['13F526' + SK]),                                  # Powerful Brown Bear
    ('Spirits', 'Spirits', [4], 1.0,
     ['0B631B' + SK, '10A86F' + SK, '1400CB' + SK],     # Ancestral Spirit, Crystal Specters
     ['150190' + SK],
     ['150190' + SK]),
    ('VatyrWarband', 'Vatyr Warband', [4], 1.0,
     ['12E284' + SK, '12E287' + SK, '12EBD5' + SK],
     ['12EBEA' + SK],
     ['022B8B' + SK]),                                  # Vatyr Leader L55
    # the lords are casters too: one lord to three Withered Lost Ones (melee) in the pool
    ('LostOneLords', 'Lords of the Lost Ones and their Dead', [4, 5], 0.5,
     [LORD30, '090BB9' + SK, '090BBB' + SK, '090BBD' + SK],
     [LORD38],
     [LORD55]),
    ('ElderVatyrs', 'Elder Vatyrs', [5], 1.0,
     ['022B83' + SK, '022B84' + SK, '022B85' + SK],
     ['022B8B' + SK],
     ['022B8B' + SK]),
    ('IceBears', 'Ice Bears', [5], 0.5,
     ['0D9404' + SK, '150126' + SK],
     ['150126' + SK],
     ['152B49' + SK]),                                  # Glacier Hound
    ('Grotesques', 'Grotesque Lost Ones', [5], 0.35,
     [GROTESQUE20],
     [GROTESQUE50],
     [GROTESQUE50]),
    # humans (curator, 2026-11-06: "unless it won't take long"): Enderal's generic bandits, Wild Mages, mercenaries
    # and the Apothecarius ghosts; the _RangeNNNN / _Aggressive suffix is only the base's aggro variant. Never the
    # NoRespawn (Unique) bandits, Nehrimese soldiers or Rhalata (main-quest factions).
    ('BanditRaid', 'Bandits', [1, 2], 1.0,
     ['02F43C' + FS, '02F450' + FS, '02F451' + FS, '02F478' + FS, '02F48C' + FS, '02F44A' + FS,   # L10 melee
      '02F477' + FS, '02F442' + FS, '080C70' + SK],                                                 # L10 archers
     ['02F44F' + FS, '02F547' + FS],                   # L17 / L20 bandits
     ['02F48D' + FS, '02F554' + FS]),                  # L20 bandits
    ('Marauders', 'Marauders', [3], 1.0,
     ['02F48D' + FS, '02F4A0' + FS, '02F547' + FS, '02F554' + FS, '12912A' + SK,                    # L20 melee
      '02F553' + FS, '02F48B' + FS],                                                                 # L20 archers
     ['095DAF' + SK, '095DB1' + SK],                   # Mercenaries
     ['095E13' + SK]),                                 # Mercenary (High Elf)
    # a coven, not a firing line (curator 2026-11-06: a whole wave of mages blasting is too much): 4 bandit thralls
    # to 3 mages in the regulars pool, and a 0.7 pack; the mages L12/L26, the thralls L20 melee
    ('WildMages', 'Wild Mages and Thralls', [2, 3], 0.7,
     ['02F48D' + FS, '02F4A0' + FS, '02F547' + FS, '02F554' + FS,                                   # L20 bandit melee
      '048387' + SK, '02F4D4' + FS, '02F4FC' + FS],                                                 # L12 / L26 Wild Mages
     ['1357B7' + SK, '13C1A2' + SK],                   # L30 / L33 Wild Mages
     ['047D92' + SK]),                                 # L30 Wild Mage who summons Oorbayas
    # casters behind melee, like the mages (curator 2026-11-06: the spectral wave was all mages too): 3 Conjured
    # Guardians (melee ghost skeletons, vanilla race) to 2 Spectral Apothecarii in the pool
    ('RestlessSpirits', 'Restless Spirits', [3, 4], 0.7,
     ['107183' + SK, '107183' + SK, '107183' + SK, '106869' + SK, '106866' + SK],   # Conjured Guardian L25 x3, Apothecarius L23 x2
     ['141FEE' + SK],                                  # Monk (ghost) L40
     ['141FF0' + SK]),
]
# Enderal's Health / Mana Potions Cheap, Standard, Quality, Exclusive (02E-05E_Genesungstrank / _Manatrank): the
# script indexes them by wave (one tier every 4 waves). 01E_Lebenstrank is the Rancid one: never again.
HEALTH_POTIONS = ['0028C5' + SK, '0028C6' + SK, '0028C7' + SK, '0028C9' + SK]
MANA_POTIONS = ['019E3B' + SK, '090892' + SK, '09B6CB' + SK, '1037F7' + SK]
AMBROSIA = '0FEC69' + SK          # _00E_Ambrosia
ID_MANA_POTIONS = 0x817
SPAWN_SLOTS = 40                  # spawn aliases ZFW_Spawn01-40 (alias IDs 1-40), script ZFW_SpawnAlias
# Every spawn alias carries this package (alias PackageData), which outranks the actor's own package list. The
# Vagrant _10E_Bandit05_Range2500 02F48C (the one base of 145 in THEMES) has no AIPackages template flag and its own
# package is _DefaultSitLinkedRef 0DD723, whose InterruptOverride is Combat: it runs INSTEAD of the combat behaviour,
# and a spawned copy has no linked chair, so she stood in combat, target set, never moving (curator, 2026-11-09;
# Enderal places her with a linked ref at the Eisbrecherwarte). _DefaultSandboxEditorLocation512: no override, so the
# combat behaviour runs in combat and a sandbox round the spawn point otherwise. combat_override_packages() lists
# such bases at build time.
SPAWN_PACKAGE = '01B217:Skyrim.esm'

# ZFW_Werewolf / ZFW_WerewolfAlpha: Skyrim's werewolf records Enderal's Skyrim.esm keeps
WW_RACE = '0CDD84' + SK           # WerewolfBeastRace (skin SkinNakedWerewolfBeast, WerewolfBeastProject.hkx)
WW_VOICE = '01F2E6' + SK          # CrWerewolfVoice
WW_STYLE = '0A199D' + SK          # csWerewolf
WW_CLASS, WW_CLASS_BOSS = '0A1993' + SK, '0A1995' + SK   # EncClassWerewolf, EncClassWerewolfBoss
WW_ABILITY = '0A1A3E' + SK        # AbWerewolf
WEREWOLVES = [  # (id, edid, name, class, level, health offset, height)
    (ID_WEREWOLF_YOUNG, 'ZFW_WerewolfYoung', 'Young Werewolf', WW_CLASS, 15, 100, 0.95),
    (ID_WEREWOLF, 'ZFW_Werewolf', 'Werewolf', WW_CLASS, 30, 350, 1.0),
    (ID_WEREWOLF_ALPHA, 'ZFW_WerewolfAlpha', 'Werewolf Alpha', WW_CLASS_BOSS, 45, 700, 1.15),
]


def fk(local):
    return '%06X:%s' % (local, PLUGIN)


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(('\n'.join(lines) + '\n').replace('\n', '\r\n').encode('utf-8'))


def obj(name, key):
    return ['    - MutagenObjectType: ScriptObjectProperty', '      Name: ' + name, '      Object: ' + key]


def flt(name, value):
    return ['    - MutagenObjectType: ScriptFloatProperty', '      Name: ' + name, '      Data: ' + repr(float(value))]


def objlist(name, keys):
    out = ['    - MutagenObjectType: ScriptObjectListProperty', '      Name: ' + name, '      Objects:']
    for k in keys:
        out += ["      - Name: ''", '        Object: ' + k]
    return out


def formlist(local, edid, items):
    if not items:
        return ['FormKey: ' + fk(local), 'EditorID: ' + edid, 'Items: []']   # a bare 'Items:' is null and stops Mutagen
    return ['FormKey: ' + fk(local), 'EditorID: ' + edid, 'Items:'] + ['- ' + k for k in items]


def quoted(text):
    """A single-quoted YAML scalar: a plain one breaks on ': ' inside the text."""
    return "'" + text.replace("'", "''") + "'"


def message(local, edid, text, buttons, name=None):
    """A message box with buttons, or (no buttons) a plain named MESG whose Name the script shows."""
    out = ['FormKey: ' + fk(local), 'EditorID: ' + edid]
    if name is not None:
        out += ['Name:', '  TargetLanguage: English', '  Value: ' + quoted(name)]
    out += ['Description:', '  TargetLanguage: English', '  Value: ' + quoted(text), 'INAM: 0x00000000']
    if buttons:
        out += ['Flags:', '- MessageBox', 'MenuButtons:']
        for b in buttons:
            out += ['- Text:', '    TargetLanguage: English', '    Value: ' + quoted(b)]
    else:
        out += ['Flags: []', 'MenuButtons: []']
    return out


def werewolf_yaml(local, edid, name, cls, level, health, height):
    """The Snow Wolf's record (a plain Enderal creature base) with every wolf-specific field replaced: the
    werewolf race supplies skin, skeleton, behaviour, attack data (with werewolfKnockbackSpell) and voice."""
    s = open(WOLF_SRC, 'rb').read().decode('utf-8').replace('\r\n', '\n')

    def cut(block_re):
        nonlocal s
        s2 = re.sub(block_re, '', s, count=1, flags=re.M)
        assert s2 != s, block_re
        s = s2

    def sub(old_re, new, count=1):
        nonlocal s
        s2, n = re.subn(old_re, new, s, flags=re.M)
        assert n == count, (old_re, n)
        s = s2

    sub(r'^FormKey: .*$', 'FormKey: ' + fk(local))
    sub(r'^EditorID: .*$', 'EditorID: ' + edid)
    cut(r'^VirtualMachineAdapter:\n(?:  .*\n)+')                  # _00E_EPOnDeath: no EP from arena kills anyway
    sub(r'^ObjectBounds:\n  First: .*\n  Second: .*$', 'ObjectBounds:\n  First: -37, -37, 0\n  Second: 37, 37, 135')
    sub(r'^  Flags:\n  - Respawn\n', '  Flags: []\n')
    sub(r'^    Level: 35$', '    Level: %d' % level)
    sub(r'^  HealthOffset: 400$', '  HealthOffset: %d' % health)
    cut(r'^Factions:\n(?:- .*\n|  .*\n)+')                         # the script gives the arena faction
    cut(r'^DeathItem: .*\n')
    sub(r'^Voice: .*$', 'Voice: ' + WW_VOICE)
    sub(r'^Race: .*$', 'Race: %s\nActorEffect:\n- %s' % (WW_RACE, WW_ABILITY))
    cut(r'^WornArmor: .*\n')                                       # race skin
    sub(r'^AttackRace: .*$', 'AttackRace: ' + WW_RACE)
    cut(r'^Attacks:\n(?:- .*\n|  .*\n)+')                          # wolf attack events: the race carries the werewolf ones
    sub(r'^Class: .*$', 'Class: ' + cls)
    sub(r'^Name:\n  TargetLanguage: English\n  Values:\n(?:  - .*\n|    .*\n)+', 'Name:\n  TargetLanguage: English\n  Value: %s\n' % name)
    sub(r'^CombatStyle: .*$', 'CombatStyle: ' + WW_STYLE)
    sub(r'^Height: .*$', 'Height: %s' % height)
    assert 'Schneewolf' not in s and '01320A' not in s and (chr(10) + '  Values:') not in s, 'wolf data left in the werewolf record'
    lines = s.split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def chest_yaml():
    """Skyrim's empty small chest record (verbatim: bounds, model data, flags) under our FormKey and name."""
    s = open(CHEST_SRC, 'rb').read().decode('utf-8').replace(chr(13) + chr(10), chr(10))
    out = []
    skip = False
    for line in s.split(chr(10)):
        if line.startswith('FormKey: '):
            line = 'FormKey: ' + fk(ID_CHEST)
        elif line.startswith('EditorID: '):
            line = 'EditorID: ZFW_Chest'
        elif line.startswith('Name:'):
            out += ['Name:', '  TargetLanguage: English', '  Value: Fogbound Cache']
            skip = True
            continue
        elif skip and line.startswith('  '):
            continue
        skip = False
        if line != '':
            out.append(line)
    assert 'Clutter' in chr(10).join(out) and 'ChestSmall02EMPTY' not in chr(10).join(out)
    return out


def winning_race(key):
    """The Race of the winning record of an Enderal base among the list's creature overriders (reference/mods),
    else the base's own; '' when nothing is serialized for it."""
    local, master = key.split(':', 1)
    pattern = ' - %s_%s.yaml' % (local, master)
    found = ''
    roots = [os.path.join(ROOT, 'reference', 'base-2.1.4.4', 'Skyrim' if master == 'Skyrim.esm' else 'EnderalFS', 'Npcs')]
    roots += [os.path.join(ROOT, 'reference', 'mods', m, 'Npcs') for m in OVERRIDERS]
    for d in roots:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(pattern):
                text = open(os.path.join(d, fn), 'rb').read().decode('utf-8')
                m = re.search(r'^Race: (.+?)\r?$', text, re.M)
                found = m.group(1) if m else found
    return found


def _ref_text(sub, key):
    """The winning serialized record of a FormKey among the list's overriders (reference/mods), else the base's."""
    local, master = key.split(':', 1)
    pattern = ' - %s_%s.yaml' % (local, master)
    roots = [os.path.join(ROOT, 'reference', 'base-2.1.4.4', 'Skyrim' if master == 'Skyrim.esm' else 'EnderalFS', sub)]
    roots += [os.path.join(ROOT, 'reference', 'mods', m, sub) for m in OVERRIDERS]
    found = ''
    for d in roots:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(pattern):
                found = open(os.path.join(d, fn), 'rb').read().decode('utf-8').replace('\r\n', '\n')
    return found


def combat_override_packages(key, depth=0):
    """[(package EditorID, InterruptOverride)] of the base's effective packages (its own, or the template's when the
    AIPackages template flag is set) whose InterruptOverride is not None: such a package runs instead of that behaviour."""
    text = _ref_text('Npcs', key)
    if not text or depth > 6:
        return []
    flags = re.search(r'^  TemplateFlags:\n((?:  - .*\n)+)', text, re.M)
    flags = re.findall(r'^  - (\w+)', flags.group(1), re.M) if flags else []
    template = re.search(r'^Template: (.+?)$', text, re.M)
    if 'AIPackages' in flags and template:
        return combat_override_packages(template.group(1), depth + 1)
    packages = re.search(r'^Packages:\n((?:- .*\n)+)', text, re.M)
    out = []
    for pkey in re.findall(r'^- (.+?)$', packages.group(1), re.M) if packages else []:
        ptext = _ref_text('Packages', pkey)
        if not ptext:
            continue
        edid = re.search(r'^EditorID: (.*)$', ptext, re.M)
        override = re.search(r'^InterruptOverride: (\w+)', ptext, re.M)
        if override:
            out.append((edid.group(1) if edid else pkey, override.group(1)))
    return out


def main():
    for sub in ('Quests', 'Activators', 'Factions', 'FormLists', 'Globals', 'Messages', 'Npcs', 'Containers'):
        if os.path.isdir(os.path.join(OUT, sub)):
            shutil.rmtree(os.path.join(OUT, sub))
    assert os.path.isfile(WOLF_SRC), WOLF_SRC

    props = obj('PlayerRef', PLAYER_REF) + obj('EPFaction', EP_FACTION) + obj('ArenaFaction', fk(ID_FACTION))
    props += obj('FogStone', fk(ID_STONE)) + obj('StoneAnchor', STONE_ANCHOR)
    # no StoneX/Y/Z properties: the spot is the script's constants (saved properties cannot move an existing stone)
    props += obj('EntryMarker', fk(ID_ENTRY)) + objlist('SpawnMarkers', [fk(ID_SPAWN0 + i) for i in range(SPAWN_COUNT)])
    props += obj('FogWoodWorld', fk(ID_WRLD))
    for i, t in enumerate(ID_TIERS):
        props += obj('Tier%d' % (i + 1), fk(t))
    props += obj('HealthPotions', fk(ID_POTIONS)) + obj('ManaPotions', fk(ID_MANA_POTIONS)) + obj('Ambrosia', AMBROSIA)
    props += obj('Themes', fk(ID_THEMES_ALL)) + obj('WaveSize', fk(ID_WAVE_SIZE))
    props += obj('ChestBase', fk(ID_CHEST)) + obj('CachePotions', fk(ID_CACHE_POTIONS)) + obj('StaminaPotion', STAMINA_POTION)
    props += objlist('CacheMarkers', [fk(ID_CACHE0 + i) for i in range(CACHE_COUNT)])
    props += obj('QuestVersion', fk(ID_QUEST_VERSION)) + obj('Persist', fk(ID_PERSIST))
    props += obj('BestWave', fk(ID_BEST)) + obj('CurrentWave', fk(ID_WAVE))
    props += obj('EnterMsg', fk(ID_ENTER_MSG)) + obj('LeaveMsg', fk(ID_LEAVE_MSG))
    def alias_binding(alias_id, script):
        return ['  - Property:', "      Name: ''", '      Object: ' + fk(ID_QUEST), '      Alias: %d' % alias_id,
                '    Scripts:', '    - Name: ' + script, '      Properties:',
                '      - MutagenObjectType: ScriptObjectProperty', '        Name: Arena', '        Object: ' + fk(ID_QUEST)]
    bindings = alias_binding(0, 'ZFW_PlayerAlias')
    aliases = ['- ID: 0', '  Name: ZFW_Player', '  Flags: []', '  UniqueActor: ' + PLAYER, '  VoiceTypes: Null']
    for n in range(1, SPAWN_SLOTS + 1):
        bindings += alias_binding(n, 'ZFW_SpawnAlias')
        aliases += ['- ID: %d' % n, '  Name: ZFW_Spawn%02d' % n, '  Flags:', '  - Optional',
                    '  PackageData:', '  - ' + SPAWN_PACKAGE, '  VoiceTypes: Null']
    def objective(index, text):
        return ['- Index: %d' % index, '  Flags: []', '  DisplayText:', '    TargetLanguage: English',
                '    Value: ' + quoted(text), '  Targets: []']
    objectives = ['Objectives:']
    objectives += objective(OBJ_CLEARED, 'Wave <Global=ZFW_CurrentWave> cleared. The fog stirs...')
    objectives += objective(OBJ_START, 'The Fog Wood. The first wave comes.')
    objectives += objective(3, 'The fog has left new caches in the wood.')
    for n, theme in enumerate(THEMES):
        objectives += objective(OBJ_WAVE0 + n, 'Wave <Global=ZFW_CurrentWave>: <Global=ZFW_WaveSize> %s' % theme[1])
    for n, theme in enumerate(THEMES):
        objectives += objective(OBJ_BOSS0 + n, 'Wave <Global=ZFW_CurrentWave>: <Alias=ZFW_Spawn01> leads <Global=ZFW_WaveSize> %s' % theme[1])
    write(os.path.join(OUT, 'Quests', 'ZFW_Arena - %06X_%s.yaml' % (ID_QUEST, PLUGIN)), [
        'FormKey: ' + fk(ID_QUEST), 'EditorID: ZFW_Arena', 'VirtualMachineAdapter:', '  Scripts:',
        '  - Name: ZFW_ArenaQuest', '    Properties:'] + props + ["  FileName: ''", '  Aliases:'] + bindings + [
        'Name:', '  TargetLanguage: English', '  Value: The Fog Wood', 'Flags:', '- StartGameEnabled', 'Type: Misc',
        # QTGL: the globals the <Global=...> tags may read, captured into the quest instance when it starts (every
        # SureAI quest with such tags lists them: MQ04 0A5820/0A581F); without it the tag is never replaced
        'TextDisplayGlobals:', '- ' + fk(ID_WAVE), '- ' + fk(ID_WAVE_SIZE), '- ' + fk(ID_BEST),
        'NextAliasID: %d' % (SPAWN_SLOTS + 1)] + objectives + ['Aliases:'] + aliases)

    write(os.path.join(OUT, 'Activators', 'ZFW_FogStone - %06X_%s.yaml' % (ID_STONE, PLUGIN)), [
        'FormKey: ' + fk(ID_STONE), 'EditorID: ZFW_FogStone', 'VirtualMachineAdapter:', '  Scripts:',
        '  - Name: ZFW_StoneScript', '    Properties:'] + obj('Arena', fk(ID_QUEST)) + [
        'ObjectBounds:', '  First: -64, -64, -16', '  Second: 64, 64, 320',
        'Name:', '  TargetLanguage: English', '  Value: Fogbound Stone',
        'Model:', '  File: ' + STONE_MODEL, '  Data: 0x020000000000000000000000',
        "MarkerColor: '#00CC4C33'", 'Flags: []'])

    # Members of one faction are NOT allies by default: every SureAI creature faction declares an Ally relation to
    # ITSELF (UndeadFaction, AnimalFaction; Creature_WolfFaction's only relation is itself). Without it the spawns
    # were neutral to each other and a neutral's stray hit is an attack (third test, 2026-11-06).
    write(os.path.join(OUT, 'Factions', 'ZFW_ArenaFaction - %06X_%s.yaml' % (ID_FACTION, PLUGIN)), [
        'FormKey: ' + fk(ID_FACTION), 'EditorID: ZFW_ArenaFaction', 'Name:', '  TargetLanguage: English',
        '  Value: Fog Wood Horde', 'Relations:', '- Target: ' + fk(ID_FACTION), '  Reaction: Ally',
        '- Target: ' + PLAYER_FACTION, '  Reaction: Enemy', 'Flags: []'])

    for scale, (local, edid) in ID_PACKS.items():
        write(os.path.join(OUT, 'Globals', '%s - %06X_%s.yaml' % (edid, local, PLUGIN)),
              ['MutagenObjectType: GlobalFloat', 'FormKey: ' + fk(local), 'EditorID: ' + edid, 'Data: ' + repr(float(scale))])

    tiers = {t: [] for t in range(1, 6)}
    seen = set()
    mihail = []
    overriding = []
    for n, (edid, shown, in_tiers, pack, regulars, elites, bosses) in enumerate(THEMES):
        assert edid not in seen, edid
        seen.add(edid)
        assert pack in ID_PACKS, (edid, pack)
        for key in regulars + elites + bosses:
            if key.endswith(SK) or key.endswith(FS):
                race = winning_race(key)
                if race.endswith(':' + MIHAIL):
                    mihail.append((edid, key))
                for pedid, override in combat_override_packages(key):
                    overriding.append((edid, key, pedid, override))
        base = ID_THEME0 + THEME_STRIDE * n
        t_id, r_id, e_id, b_id, m_id = base, base + 1, base + 2, base + 3, base + 4
        write(os.path.join(OUT, 'FormLists', 'ZFW_Theme_%s_Regulars - %06X_%s.yaml' % (edid, r_id, PLUGIN)),
              formlist(r_id, 'ZFW_Theme_%s_Regulars' % edid, regulars))
        write(os.path.join(OUT, 'FormLists', 'ZFW_Theme_%s_Elites - %06X_%s.yaml' % (edid, e_id, PLUGIN)),
              formlist(e_id, 'ZFW_Theme_%s_Elites' % edid, elites))
        write(os.path.join(OUT, 'FormLists', 'ZFW_Theme_%s_Bosses - %06X_%s.yaml' % (edid, b_id, PLUGIN)),
              formlist(b_id, 'ZFW_Theme_%s_Bosses' % edid, bosses))
        write(os.path.join(OUT, 'Messages', 'ZFW_Theme_%s_Name - %06X_%s.yaml' % (edid, m_id, PLUGIN)),
              message(m_id, 'ZFW_Theme_%s_Name' % edid, shown, [], name=shown))
        write(os.path.join(OUT, 'FormLists', 'ZFW_Theme_%s - %06X_%s.yaml' % (edid, t_id, PLUGIN)),
              formlist(t_id, 'ZFW_Theme_%s' % edid, [fk(r_id), fk(e_id), fk(b_id), fk(m_id), fk(ID_PACKS[pack][0])]))
        for t in in_tiers:
            tiers[t].append(fk(t_id))
    for t, local in enumerate(ID_TIERS, 1):
        assert tiers[t], 'tier %d has no theme' % t
        write(os.path.join(OUT, 'FormLists', 'ZFW_Tier%d - %06X_%s.yaml' % (t, local, PLUGIN)),
              formlist(local, 'ZFW_Tier%d' % t, tiers[t]))
    write(os.path.join(OUT, 'FormLists', 'ZFW_CachePotions - %06X_%s.yaml' % (ID_CACHE_POTIONS, PLUGIN)),
          formlist(ID_CACHE_POTIONS, 'ZFW_CachePotions', CACHE_POTIONS))
    write(os.path.join(OUT, 'Containers', 'ZFW_Chest - %06X_%s.yaml' % (ID_CHEST, PLUGIN)), chest_yaml())
    write(os.path.join(OUT, 'FormLists', 'ZFW_Themes - %06X_%s.yaml' % (ID_THEMES_ALL, PLUGIN)),
          formlist(ID_THEMES_ALL, 'ZFW_Themes', [fk(ID_THEME0 + THEME_STRIDE * n) for n in range(len(THEMES))]))
    write(os.path.join(OUT, 'FormLists', 'ZFW_HealthPotions - %06X_%s.yaml' % (ID_POTIONS, PLUGIN)), formlist(ID_POTIONS, 'ZFW_HealthPotions', HEALTH_POTIONS))
    write(os.path.join(OUT, 'FormLists', 'ZFW_ManaPotions - %06X_%s.yaml' % (ID_MANA_POTIONS, PLUGIN)), formlist(ID_MANA_POTIONS, 'ZFW_ManaPotions', MANA_POTIONS))

    for local, edid, name, cls, level, health, height in WEREWOLVES:
        write(os.path.join(OUT, 'Npcs', '%s - %06X_%s.yaml' % (edid, local, PLUGIN)),
              werewolf_yaml(local, edid, name, cls, level, health, height))

    # shorts, so <Global=...> text replacement prints whole numbers
    write(os.path.join(OUT, 'FormLists', 'ZFW_Persist - %06X_%s.yaml' % (ID_PERSIST, PLUGIN)), formlist(ID_PERSIST, 'ZFW_Persist', []))
    for local, edid in ((ID_BEST, 'ZFW_BestWave'), (ID_WAVE, 'ZFW_CurrentWave'), (ID_WAVE_SIZE, 'ZFW_WaveSize'), (ID_QUEST_VERSION, 'ZFW_QuestVersion')):
        write(os.path.join(OUT, 'Globals', '%s - %06X_%s.yaml' % (edid, local, PLUGIN)),
              ['MutagenObjectType: GlobalShort', 'FormKey: ' + fk(local), 'EditorID: ' + edid, 'Data: 0'])

    write(os.path.join(OUT, 'Messages', 'ZFW_EnterMsg - %06X_%s.yaml' % (ID_ENTER_MSG, PLUGIN)), message(
        ID_ENTER_MSG, 'ZFW_EnterMsg',
        'The stone hums under your hand. Beyond it lies the Fog Wood, where the fog sends wave after wave against '
        'whoever stands in it. Nothing you kill there feeds you: no experience, no loot but what you need to keep fighting. '
        'Fall, and the fog returns you here. The fog sweeps the ground before every wave: keep what you mean to keep on you.',
        ['Enter the Fog Wood', 'Not now']))
    write(os.path.join(OUT, 'Messages', 'ZFW_LeaveMsg - %06X_%s.yaml' % (ID_LEAVE_MSG, PLUGIN)), message(
        ID_LEAVE_MSG, 'ZFW_LeaveMsg', 'Leave the Fog Wood? The run ends here.', ['Leave', 'Stay']))
    print('arena records written: quest 0x%X (%d spawn aliases), stone 0x%X, faction 0x%X, %d themes (0x%X-0x%X) in %s, %d werewolf bases, %d+%d potions, messages, globals'
          % (ID_QUEST, SPAWN_SLOTS, ID_STONE, ID_FACTION, len(THEMES), ID_THEME0, ID_THEME0 + THEME_STRIDE * len(THEMES) - 1,
             ' / '.join('T%d:%d' % (t, len(v)) for t, v in sorted(tiers.items())), len(WEREWOLVES), len(HEALTH_POTIONS), len(MANA_POTIONS)))
    if overriding:
        print('NOTE: %d base(s) whose own package overrides a behaviour; the spawn aliases\' PackageData (%s) outranks it:' % (len(overriding), SPAWN_PACKAGE))
        for edid, key, pedid, override in overriding:
            print('  %s: %s has %s [InterruptOverride %s]' % (edid, key, pedid, override))
    if mihail:
        print('WARNING: %d bases whose winning record is on the Mihail skeleton race (Enemy Density refuses these):' % len(mihail))
        for edid, key in mihail:
            print('  %-20s %s' % (edid, key))
    return 0


if __name__ == '__main__':
    sys.exit(main())
