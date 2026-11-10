"""The High (F1), Mid (F2) and Low (F3) stance sources, shared by 00-install-sources.py, 01-build-stance-overlays.py and
02-verify.py. Each source is a third-party Nexus mod installed UNTOUCHED as its own MO2 mod (00); the stance logic is
only our OAR user.json files over its submod folders (01). Order inside a stance = layer order, low -> high."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'lsdf', os.path.join(HERE, '..', '..', 'LSdFHighStance', 'tools', '01-build-lsdf-high-stance.py'))
lsdf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lsdf)          # shared: paths, DAR parser, OAR condition builders, FHR negations

DAR = 'meshes/actors/character/animations/DynamicAnimationReplacer/_CustomConditions'
OAR = 'meshes/actors/character/animations/OpenAnimationReplacer'
OVERLAY_MOD = 'Zenderal - Stance Overlays'
STANCES_ESP = 'Stances - Dynamic Weapon Movesets SE.esp'

# mod: MO2 folder name; glob: the download; root: the data folder inside the archive; nexus: (mod id, file id,
# version) for meta.ini / a missing download .meta; remap: DAR folder renumbering at install (path only).
SOURCES = {
    # High (F1) since 2026-11-10, replacing the generated Le Sentiment du Fer conversion (LSdFHighStance, shelved)
    'nordic': {'mod': 'Nordic Combat Animations for Nord and Orc',
               'glob': 'Nordic Combat Animations for Nord and Orc-72966-*.7z', 'root': 'Data',
               'nexus': (72966, 378682, '1.3'), 'credit': 'cheming1228'},
    # High layers over Nordic (2026-11-10). Both authors forbid modifying their files or using their assets "under any
    # circumstances": installed untouched, overlay only; ask them before shipping.
    'elden': {'mod': 'Elden Sword Definitive (MCO - SCAR)',
              'glob': 'Elden Sword Definitive (MCO - SCAR)-136573-*.zip', 'root': 'Elden Sword Definitive (MCO - SCAR)',
              'nexus': (136573, 573596, '1.1'), 'credit': 'MoFu, Black, Old Fire, Mathieu'},
    'lothric': {'mod': 'Lothric Fighter - MCO', 'glob': 'Lothric Fighter - MCO-136588-*.zip',
                'root': 'Lothric Fighter (MCO)', 'nexus': (136588, 573437, '1.0'), 'credit': 'MoFu, Black, Mathieu'},
    'desert': {'mod': 'DesertRace Combat Animations for Redguard and Khajiit',
               'glob': 'DesertRace Combat Animations for Redguard and Khajiit-77474-*.7z', 'root': 'Data',
               'nexus': (77474, 378693, '1.1'), 'credit': 'cheming1228'},
    'imperium': {'mod': 'Imperium Combat Animations for Breton and Imperial Races',
                 'glob': 'Imperium Combat Animations for Breton and Imperial Races-88752-*.7z', 'root': 'Data',
                 'nexus': (88752, 378700, '1.1'), 'credit': 'cheming1228'},
    'ec_blade': {'mod': 'Elder Creed - Blade', 'glob': 'Elder Creed - Blade-75533-*.7z', 'root': '00 Data/ADXP-MCO',
                 'nexus': (75533, 503891, '1.2'), 'credit': 'Kars'},
    'ec_axe': {'mod': 'Elder Creed - Axe Moveset AIO', 'glob': 'Elder Creed - Axe Moveset AIO-71937-*.7z', 'root': '',
               'nexus': (71937, None, 'v1'), 'credit': 'Austio'},
    'muay': {'mod': 'Skyrim Martial Arts - Muay thai', 'glob': 'Skyrim Martial Arts Muay thai-77297-*.7z',
             'root': 'Data', 'nexus': (77297, None, '1.0.1'), 'credit': 'cheming1228'},
    # Kick Boxing and Muay Thai both ship DAR folders 40050-40054; the author's page says to change the numbers
    # when 40050 is taken. Installed at 40060-40064 (same files, other folder).
    'kick': {'mod': 'Skyrim Martial Arts - Kick Boxing', 'glob': 'Skyrim Martial Arts Kick Boxing Base-69201-*.7z',
             'root': 'Data', 'nexus': (69201, None, '1.1.0'), 'credit': 'cheming1228',
             'remap': {40050: 40060, 40051: 40061, 40052: 40062, 40053: 40063, 40054: 40064}},
    'merc': {'mod': 'Realistic Mercenary 1H Sword Animation', 'glob': 'Realistic Mercenary 1H Sword Animation-75920-*.zip',
             'root': '', 'nexus': (75920, None, '1.0.1'), 'credit': 'Vector1886'},
    'vana': {'mod': 'Vanargand Animations II - Sword Low Stance',
             'glob': 'Vanargand Animations II Sword Low Stance 187094 *.7z',
             'root': 'Vanargand Animations II - Sword Low Stance', 'nexus': (187094, None, '1.1b'),
             'credit': 'Verolevi'},
}

# Layers per stance, low -> high: (source key, DAR folder numbers or OAR submod paths, right-hand narrowing[, addons]).
# None = every folder of that kind in the source. Folders of a source not named here are disabled by 01.
# addons = {OAR submod path: direction}: a source's directional extra (gated by its author on dTry Key Utils'
# Keytrace effects, which never appear in this list - traced for FHRFirstPerson). 01 regates it on moving that way
# with DMK reading that direction or 0 (FHRFirstPerson's test) and switches it on only where its own source's set
# is the stance's attack set, one priority step above it.
ADDON_DIRECTIONS = {'Forward': (1, 1)}   # name: (DMK DirecionalCycleMoveset value, OAR IsMovementDirection value)
STANCES = [
    {'name': 'High', 'key': 'F1', 'perk': '42518', 'priority': 1_500_030_000, 'layers': [
        ('nordic', 'dar', None, None),
        # sword, off-hand free (or staff/spell/torch); its Keytrace-forward power attack as an addon
        ('elden', 'oar', ['Elden Sword Definitive/Moveset'], None,
         {'Elden Sword Definitive/Extra Power Attack': 'Forward'}),
        # sword + shield; forward power attack = its shield bash. Its back power attack stays off: FHR owns back attacks
        ('lothric', 'oar', ['Lothric Fighter/Moveset'], None, {'Lothric Fighter/Shield Bash': 'Forward'}),
    ]},
    {'name': 'Mid', 'key': 'F2', 'perk': '42519', 'priority': 1_500_010_000, 'layers': [
        ('desert', 'dar', None, None),
        ('ec_axe', 'dar', None, None),
        ('ec_blade', 'oar', ['Elder Creed - Blade/Free Left Hand', 'Elder Creed - Blade/Shield Equipped'], None),
        ('muay', 'dar', None, None),
    ]},
    {'name': 'Low', 'key': 'F3', 'perk': '4251A', 'priority': 1_500_020_000, 'layers': [
        ('imperium', 'dar', None, None),
        ('merc', 'dar', [20003], None),
        ('vana', 'oar', ['Sword low stance/Main', 'Sword low stance/Hip Equip'], {1}),
        ('kick', 'dar', None, None),
    ]},
]
