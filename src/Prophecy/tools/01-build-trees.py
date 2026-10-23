"""Build the four Prophecy perk trees (Faith, Gunslinger, Gadgets, Martial Arts).

Regenerates, from the serialized source mods in reference/mods/:
  ProphecyESP/{Perks,Spells,MagicEffects,...}/   every record a picked perk needs, renumbered into
                                                  Zenderal - Prophecy.esp (block 0x810+)
  Scripts/compiled/*.pex                          the source mods' compiled scripts those records use
  assets/                                         meshes/textures those records use (from the BSAs)
  csf/Prophecy.json                               the Custom Skills Framework menu: 4 trees, 5 nodes each

Sources (both allow modification/redistribution with credit; see arch-docs/ordinator/README.md):
  Ordinator - Perks of Skyrim (Enai Siaion)  reference/mods/Ordinator, raw BSA in reference/mods/_raw/Ordinator
  Subclasses of Skyrim 2 (Darenii)            reference/mods/SubclassesOfSkyrim, raw in reference/mods/_raw/SubclassesOfSkyrim

Rules the copy follows (asserted, the script fails loudly otherwise):
  * a reference to a copied record is repointed to its new FormKey;
  * a reference to a source PERK we did not pick is repointed to ZP_Prophecy_Never (never owned), so every
    "has perk X" condition on an unpicked perk evaluates exactly as it would for a player who lacks it;
  * any other reference into a source plugin, or to a base-game form Enderal does not define, is an error.
Never hand-edit what this script writes - edit the SPEC below and re-run, then 02 (fever tax) is folded in here.
"""
import os, re, sys, json, glob, shutil, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from _closure import index, FK
import _bsa

PATCH = os.path.join(REPO, 'src', 'Prophecy')
ESP = os.path.join(PATCH, 'ProphecyESP')
MOD = 'Zenderal - Prophecy.esp'
ORD = 'Ordinator - Perks of Skyrim.esp'
SOS = 'SubclassesOfSkyrim.esp'
REF = os.path.join(REPO, 'reference')
SRC = {ORD: os.path.join(REF, 'mods', 'Ordinator'), SOS: os.path.join(REF, 'mods', 'SubclassesOfSkyrim')}
RAW = {ORD: os.path.join(REF, 'mods', '_raw', 'Ordinator'), SOS: os.path.join(REF, 'mods', '_raw', 'SubclassesOfSkyrim')}
BSAS = {ORD: ['Ordinator - Perks of Skyrim.bsa', 'Ordinator - Perks of Skyrim - Textures.bsa'], SOS: ['SubclassesOfSkyrim.bsa']}

FIRST_ID = 0x810                   # 0x800-0x807 are the prototype's hand-written records
NEVER = f'000808:{MOD}'            # ZP_Prophecy_Never            # ZP_Prophecy_Never, written below
FEVER = '11A4B6:Skyrim.esm'        # _00E_IncreaseArcaneFeverFFSelf - Enderal's healing-magic tax
WEAPTYPEBOW = '01E715:Skyrim.esm'  # muskets carry it (arch-docs/patches/MusketHandling.md)
FIRE_ENCH = '04605A:Skyrim.esm'    # EnchFireDamageFFContact

o = lambda h: f'{h}:{ORD}'
s = lambda h: f'{h}:{SOS}'

# id, name, description, source seed, perks folded INTO this node (their FormKeys alias to it), parents
TREES = [
  ('Faith', 'Light Magic, healing and sustain.', [
    ('faith1', 'Descending Light', 'When you enter combat, you rapidly regenerate Magicka equal to half your Light Magic skill per second. The effect fades over 15 seconds and does not stop while casting.', o('01435F'), [], []),
    ('faith2', 'Respite', 'Healing spells also restore Stamina equal to their power.', '0581F9:Skyrim.esm', [], ['faith1']),
    ('faith3', 'Edgewalker', 'Light Magic healing is up to 30% more powerful if the recipient is below half Health. The bonus increases as Health decreases.', '0581F8:Skyrim.esm', [], ['faith1']),
    ('faith4', 'Healing Presence', 'In combat you heal yourself and nearby allies for 25 Health every 10 seconds, at a cost of 1 Arcane Fever.', s('000820'), [], ['faith2', 'faith3']),
    ('faith5', 'Templar', 'Once every 90 seconds, falling below 25% Health makes you immune to damage for 6 seconds and heals you for 100 Health afterwards, at a cost of 4 Arcane Fever.', s('000849'), [], ['faith4']),
  ]),
  ('Gunslinger', 'Muskets, powder and lead.', [
    ('gun1', 'Quick Reload', 'Draw a bow and reload a crossbow or musket 30% faster.', '105F19:Skyrim.esm', [], []),
    ('gun2', 'Elemental Rounds', 'Your musket, crossbow and bow hits also deal 10 points of fire damage.', None, [], ['gun1']),
    ('gun3', 'Bleeding Shot', 'Your musket, crossbow and bow hits make living targets bleed for 50 damage over 5 seconds.', None, [], ['gun1']),
    ('gun4', 'Run and Gun', 'You move at full speed with a drawn bow or a raised musket.', '058F63:Skyrim.esm', [], ['gun2', 'gun3']),
    ('gun5', 'Deadeye', None, o('0064C0'), [], ['gun4']),
  ]),
  ('Gadgets', 'Traps, smoke and clockwork.', [
    ('gad1', 'Explosive Tripwire', 'Grants the "Explosive Tripwire" power. At will, places a tripwire in front of you for 120 seconds. It snaps when tripped, knocking all targets hit by it to the floor, and an enemy who trips it sets off an explosion that deals 40 damage.', o('0379AA'), [], []),
    ('gad2', 'Smokescreen', None, o('037419'), [], ['gad1']),
    # gad3 was Bear Traps (Ordinator 0306CB + Lockjaw 030C45). Utility Droid replaced it 2026-10-23; the seed and the
    # folded perk stay so the copy closure, and every ID after it, is unchanged. The perk itself is rewritten (DROID_NODE).
    ('gad3', 'Utility Droid', 'Grants the "Utility Droid" power. Deploy a mechanical spider that follows you, heals you and staggers enemies around it. It lasts until destroyed; building another costs 10 Spare Parts.', o('0306CB'), [o('030C45')], ['gad1']),
    ('gad4', 'Clockwork Turret', 'You can build Clockwork Turrets at a forge. Use the "Clockwork Turret" power to deploy one: it fires parallel to your crosshair for 30 seconds while you stay within 12 feet, dealing damage equal to 30% of your Handicraft skill.', o('056C92'), [], ['gad2', 'gad3']),
    ('gad5', 'Overclock', 'Your Clockwork Turret deploys two turrets side by side, and they fire 2% faster with every shot, up to 200%.', None, [o('056C9F'), o('056CA7')], ['gad4']),
  ]),
  ('Martial Arts', 'Fists, footwork and timing.', [
    ('ma1', 'Iron Fist', 'Increases unarmed damage by 15% of your current Stamina. Requires two free hands.', '058F6E:Skyrim.esm', [], []),
    ('ma2', 'Hissing Dragon', None, o('04D4E3'), [], ['ma1']),
    ('ma3', 'Stunning Blows', 'Your unarmed attacks have a 15% chance to stagger enemies, and deal 25% more damage to staggered enemies.', s('000851'), [], ['ma1']),
    ('ma4', 'Breaking Waves', 'Unarmed attacks have a 15% chance of a critical strike that deals critical damage equal to 40% of your current Stamina. Requires two free hands.', o('04D4DA'), [], ['ma2', 'ma3']),
    ('ma5', 'Flow State', 'Dodging in combat slows time to a crawl for a moment, once every 10 seconds, and releases a Shock Nova that deals 40 shock damage to nearby enemies, once every 15 seconds.', None, [], ['ma4']),
  ]),
  # Glory (2026-10-21, curator's design): all hand-built - see write_glory. Its records sit AFTER every other
  # block (GLORY_FIRST_ID) so adding it did not renumber the four older trees in existing saves.
  ('Glory', 'Charges, banners and hard-won grit.', [
    ('glo1', 'Seismic Stomp', 'Grants the "Seismic Stomp" power: stomp the ground and send out a shockwave that hurls every enemy within 19 feet up and away and makes them bleed for 50 damage over 5 seconds, as time slows for a moment. Usable every 30 seconds.', None, [], []),
    ('glo2', 'Second Wind', 'While at or below half Health, every hit you take restores 20 Stamina.', None, [], ['glo1']),
    ('glo3', 'Dragon Scale', 'You gain 25% resistance to Fire, Frost and Lightning.', None, [], ['glo1']),
    ('glo4', 'War Banner', 'Grants the "War Banner" power: plant a banner for 15 seconds. While you stand near it you heal 20 Health per second, and enemies who come close are bound in chains as by a Stave of Binding. Usable once every 5 minutes.', None, [], ['glo2', 'glo3']),
    ('glo5', 'Surrounded', 'While 3 or more enemies are close to you, your Stamina regenerates 2 points per second.', None, [], ['glo2', 'glo3']),
  ]),
]
GLORY = 'Glory'
GLORY_FIRST_ID = 0x916
# Glory nodes added after the Glory block was laid out get IDs at the END (after GLORY_RECORDS_5), so nothing that
# existing saves point at moves. glo5 (2026-10-22) = 0x93A: first Death or Glory (power attacks stronger below 75%
# Health), replaced the same day by Surrounded on the same perk, so a save that took one now has the other.
GLORY_LATE_NODES = ('glo5',)
# Surrounded (curator, 2026-10-22): an ability whose script restores Stamina once a second while enough living hostile
# actors stand close. Radius 400 = Seismic Stomp's.
SURROUNDED = {'Radius': 400.0, 'MinEnemies': 3, 'StaminaPerSecond': 2.0}
# Records copied for hand-built nodes (their closures come along)
EXTRA_SEEDS = [s('00084F'),          # Monk - its bleed spell/MGEF become Bleeding Shot's
               o('07B101')]          # ORD_Bck_QuickReflexes_Spell_Self - the slow-time spell Flow State casts
# Plain numeric edits on copied perk effects: (node, EntryPoint, old value, new value)
VALUE_EDITS = [('ma1', 'ModAttackDamage', '0.05', '0.15')]
# Skyrim forms a copied record names that Enderal lacks (or has at that ID as something else). A target
# of None removes the YAML list entry/line carrying the reference; the DUMMY_* are inert records of ours.
DUMMY_QUEST, DUMMY_LOC, DUMMY_SPELL = f'00080A:{MOD}', f'00080B:{MOD}', f'00080C:{MOD}'
SUBST = {
    '0BC0BD:Skyrim.esm': DUMMY_QUEST,          # C00JorrvaskrFight (Iron Fist/Descending Light: "not brawling");
                                               #   in Enderal 0BC0BD is a placed ref
    '01F877:Skyrim.esm': DUMMY_LOC,            # WhiterunJorrvaskrLocation
    '047AE6:Skyrim.esm': '11A493:Skyrim.esm',  # DGIntimidateQuest -> Enderal's own brawl quest
    '064D68:Skyrim.esm': DUMMY_SPELL,          # VoiceMakeEthereal (no shouts in Enderal)
    '01397D:Skyrim.esm': '0800E4:Skyrim.esm',  # Bear Trap recipe's 20x (vanilla-only item) -> Leather Strips
    '09E0C9:Skyrim.esm': None,                 # Hunt Together wolf's faction (wolf never spawns: perk unpicked)
    '0A85C7:Skyrim.esm': None,                 # ... and its InheritsSoundsFrom
}
# A node renamed after release keeps its EditorID (the thumbnail file and the menu's Images path follow it).
EDITORID = {'gad1': 'ZP_Prophecy_Tripwire', 'glo5': 'ZP_Prophecy_DeathorGlory'}   # gad3 follows its name: ZP_Prophecy_UtilityDroid
# Exact display strings renamed on the copied records (the power, its effect, the wire, its quest).
RENAME = {'Tripwire': 'Explosive Tripwire'}


def perk_edid(node):
    return EDITORID.get(node[0], 'ZP_Prophecy_' + re.sub(r'\W', '', node[1]))


LORE = [('Dwemer Autocannon', 'Clockwork Turret'), ('Dwarven Autocannon', 'Clockwork Turret'),
        ('Dwemer', 'Clockwork'), ('Dwarven', 'Clockwork'), ('Skyrim', 'Vyn'), ('Light Armor experience', 'nothing')]


def ed(t):
    m = re.search(r'^EditorID: (.+?)\s*$', t, re.M); return m.group(1) if m else None


def enderal_formkeys():
    have = {f'000014:Skyrim.esm', '000007:Skyrim.esm'}
    for d, mk in [('base/Skyrim', 'Skyrim.esm'), ('base/Update', 'Update.esm'), ('base/EnderalFS', None), ('mods/EGO', None)]:
        for root, _, fs in os.walk(os.path.join(REF, d)):
            for f in fs:
                m = re.search(r' - ([0-9A-F]{6})_(.+?\.es[mp])\.yaml$', f)
                if m: have.add(f'{m.group(1)}:{m.group(2)}')
    return have


def main():
    idx = {p: index(SRC[p]) for p in SRC}
    rec = {}
    for p in idx: rec.update(idx[p])           # FormKey -> (type, path, text); vanilla-ID Ordinator records included
    def owner(fk):
        for p in idx:
            if fk in idx[p]: return p
    # --- closure over source records (stop at perks: perks are only copied when picked)
    nodes = {n[0]: n for _, _, ns in TREES for n in ns}
    picked = {n[3]: n[0] for n in nodes.values() if n[3]}
    alias = {a: nid for nid, n in nodes.items() for a in n[4]}
    seeds = list(picked) + list(alias) + EXTRA_SEEDS
    copy, q = [], list(seeds)
    while q:
        fk = q.pop()
        if fk in copy: continue
        assert fk in rec, f'seed/ref {fk} not in any source tree'
        copy.append(fk)
        ty, _, t = rec[fk]
        for h, f in FK.findall(t):
            r = f'{h}:{f}'
            if r in rec and r not in copy and (rec[r][0] != 'Perks' or r in picked or r in alias):
                q.append(r)
    # COBJ recipes that unlock on a picked perk (Bear Traps, the turret) - reverse refs
    for fk, (ty, _, t) in rec.items():
        if ty == 'ConstructibleObjects' and any(p in t for p in seeds) and fk not in copy:
            copy.append(fk); q = [fk]
            while q:
                x = q.pop()
                for h, f in FK.findall(rec[x][2]):
                    r = f'{h}:{f}'
                    if r in rec and r not in copy and rec[r][0] != 'Perks': copy.append(r); q.append(r)
    copy = [fk for fk in copy if fk not in alias]          # folded perks contribute effects, not records
    # Scenes that belong to a copied quest, and what they use (Tripwire's kneel: scene 0379A9 runs package 0379A7).
    # Only quest -> scene is a reverse ref, so the forward closure missed them until 2026-10-21 (no placing
    # animation). Allocated after the Glory block, so adding them renumbered nothing.
    late = []
    for fk, (ty, _, t) in rec.items():
        qm = re.search(r'^Quest: (.+?)\s*$', t, re.M)
        if ty == 'Scenes' and qm and qm.group(1) in copy and fk not in copy:
            q = [fk]
            while q:
                x = q.pop()
                if x in copy or x in late: continue
                late.append(x)
                for h, f in FK.findall(rec[x][2]):
                    r = f'{h}:{f}'
                    if r in rec and rec[r][0] != 'Perks': q.append(r)
    # --- allocate
    newid, nxt = {}, FIRST_ID
    nodeperk = {}
    glory_all = [n[0] for t, _, ns in TREES if t == GLORY for n in ns]
    glory_nodes = [nid for nid in glory_all if nid not in GLORY_LATE_NODES]
    for nid, n in nodes.items():                         # perks first, in tree order, for readable IDs
        if nid in glory_all: continue
        if n[3]: newid[n[3]] = f'{nxt:06X}:{MOD}'
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    for a, nid in alias.items(): newid[a] = nodeperk[nid]
    for fk in copy:
        if fk not in newid: newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    gunhit = f'{nxt:06X}:{MOD}'; nxt += 1
    flowab, flowme = f'{nxt:06X}:{MOD}', f'{nxt+1:06X}:{MOD}'; nxt += 2
    blast = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('exp', 'mgef', 'glob'))}; nxt += 3
    assert nxt <= GLORY_FIRST_ID, f'older trees grew into the Glory block (next 0x{nxt:03X})'
    nxt = GLORY_FIRST_ID
    for nid in glory_nodes:
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    glory = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS)}; nxt += len(GLORY_RECORDS)
    for fk in late:
        newid[fk] = f'{nxt:06X}:{MOD}'; nxt += 1
    copy += late
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_2)}); nxt += len(GLORY_RECORDS_2)
    psound = {}
    for key, *_ in POWER_SOUNDS:                          # 3 records each, in table order (append new ones last)
        psound[key] = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(('sound', 'marker', 'mgef'))}; nxt += 3
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_3)}); nxt += len(GLORY_RECORDS_3)
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_4)}); nxt += len(GLORY_RECORDS_4)
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_5)}); nxt += len(GLORY_RECORDS_5)
    for nid in GLORY_LATE_NODES:                          # in order; append new late nodes last
        nodeperk[nid] = f'{nxt:06X}:{MOD}'; nxt += 1
    assert nodeperk['glo5'] == f'00093A:{MOD}', nodeperk['glo5']
    glory.update({k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(GLORY_RECORDS_6)}); nxt += len(GLORY_RECORDS_6)
    nova = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(FLOW_NOVA_RECORDS)}; nxt += len(FLOW_NOVA_RECORDS)
    droid = {k: f'{nxt + i:06X}:{MOD}' for i, k in enumerate(DROID_RECORDS)}; nxt += len(DROID_RECORDS)
    glory['quickreflexes_me'] = newid[f'07B100:{ORD}']     # ORD_Bck_QuickReflexes_Effect_Self

    assert nxt <= 0xFFF, 'out of ESL range'
    have = enderal_formkeys()
    bad = collections.Counter()

    def remap(t, where):
        def sub(m):
            r = f'{m.group(1)}:{m.group(2)}'
            if r in newid: return newid[r]
            if m.group(2) in (ORD, SOS) or r in rec:
                if r in rec and rec[r][0] == 'Perks': return NEVER
                bad[f'{r} (source record not copied) in {where}'] += 1; return r
            if m.group(2) == MOD: return r
            if r in SUBST: return SUBST[r] or '@@DROP@@'
            if r not in have: bad[f'{r} (not in Enderal) in {where}'] += 1
            return r
        t = FK.sub(sub, t)
        # drop whole YAML list items / lines that referenced a SUBST None
        t = re.sub(r'^- [A-Za-z]+: @@DROP@@\n(?:  .*\n)*', '', t, flags=re.M)
        t = re.sub(r'^.*@@DROP@@.*\n', '', t, flags=re.M)
        t = re.sub(r'^\w+:\n(?=[A-Za-z]|\Z)', '', t, flags=re.M)     # a list emptied by the drop
        return t

    # --- wipe generated folders (keep the prototype's hand-written 0x800-0x807 files)
    keep = {f'{i:06X}' for i in range(0x800, 0x808)} | {'000809', '00080D'}     # + 809 PointsEarned, 80D ZP_ProphecyMenu
    for p in glob.glob(os.path.join(ESP, '*', '*.yaml')):
        m = re.search(r' - ([0-9A-F]{6})_', os.path.basename(p))
        if m and m.group(1) not in keep: os.remove(p)
    for p in glob.glob(os.path.join(ESP, '*', '*ZP_Prophecy_TestPerk*')): os.remove(p)

    def write(ty, t):
        fk = re.search(r'^FormKey: (.+?)\s*$', t, re.M).group(1)
        h = fk.split(':')[0]
        os.makedirs(os.path.join(ESP, ty), exist_ok=True)
        open(os.path.join(ESP, ty, f'{ed(t)} - {h}_{MOD}.yaml'), 'w', encoding='utf-8', newline='\r\n').write(t)

    def setstr(t, key, val):
        val = val.replace("'", "''")
        block = f"{key}:\n  TargetLanguage: English\n  Value: '{val}'\n"
        pat = re.compile(rf'^{key}:\n(?:  .*\n)+', re.M)
        if pat.search(t): return pat.sub(lambda m: block, t, count=1)
        return t.replace('\nEditorID: ', f'\nEditorID: ', 1).replace(f'EditorID: {ed(t)}\n', f'EditorID: {ed(t)}\n{block}', 1)

    def lore(t):
        # display strings only ("Value:"/"String:" lines) - never FormKeys or EditorIDs
        def fix(m):
            line = m.group(0)
            for a, b in LORE: line = line.replace(a, b)
            return line
        return re.sub(r'^\s*(?:Value|String): .*$', fix, t, flags=re.M)

    def prereq(parents):
        if not parents: return ''
        out = 'Conditions:\n'
        for i, pnode in enumerate(parents):
            flag = '  Flags:\n  - OR\n' if i < len(parents) - 1 else ''
            out += ('- MutagenObjectType: ConditionFloat\n' + flag +
                    '  Data:\n    MutagenObjectType: HasPerkConditionData\n'
                    f'    Perk: {nodeperk[pnode]}\n  ComparisonValue: 1\n')
        return out

    models, scripts = set(), set()
    # --- copied records
    for fk in copy:
        ty, _, t = rec[fk]
        t = t.replace('\r\n', '\n')
        for f in re.findall(r'^\s+File: (.+?)\s*$', t, re.M): models.add((owner(fk), f.strip("'\"").lower()))
        for n in re.findall(r'^\s+- Name: (\S+)\s*$', t, re.M): scripts.add((owner(fk), n.lower()))
        if ty == 'Perks': continue                       # perks are written per node below
        t = remap(t, ed(t))
        t = re.sub(r'^EditorID: (?:ZP_)?', 'EditorID: ZP_', t, count=1, flags=re.M)
        t = lore(t)
        for old, new in RENAME.items():
            t = re.sub(rf'^(\s*Value: ){re.escape(old)}\s*$', lambda m: m.group(1) + new, t, flags=re.M)
        if ty == 'ConstructibleObjects':
            # Bear Traps' forge recipes stay copied (IDs) but can no longer unlock: Utility Droid owns that perk now
            t = t.replace(nodeperk[DROID_NODE], NEVER)
        write(ty, t)

    # --- perks, one per node
    for nid, n in nodes.items():
        _, name, desc, seed, folded, parents = n
        if seed:
            t = rec[seed][2].replace('\r\n', '\n')
            # effects of folded perks are appended to this node's
            for a in folded:
                ft = rec[a][2].replace('\r\n', '\n')
                m = re.search(r'^Effects:\n((?:[- ].*\n)*)', ft, re.M)
                if m:
                    if re.search(r'^Effects:\n', t, re.M):
                        t = re.sub(r'^(Effects:\n(?:[- ].*\n)*)', lambda mm: mm.group(1) + m.group(1), t, count=1, flags=re.M)
                    else:
                        t += 'Effects:\n' + m.group(1)
            t = remap(t, name)
        else:
            t = f'FormKey: {nodeperk[nid]}\nEditorID: x\nNumRanks: 1\nPlayable: True\n'
        t = re.sub(r'^FormKey: .*$', f'FormKey: {nodeperk[nid]}', t, count=1, flags=re.M)
        t = re.sub(r'^EditorID: .*$', 'EditorID: ' + perk_edid(n), t, count=1, flags=re.M)
        t = re.sub(r'^NextPerk: .*\n', '', t, flags=re.M)
        t = re.sub(r'^Conditions:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
        t = re.sub(r'^(NumRanks: .*\n)', lambda m: prereq(parents) + m.group(1), t, count=1, flags=re.M) if 'NumRanks:' in t else t + prereq(parents)
        t = setstr(t, 'Name', name)
        if desc: t = setstr(t, 'Description', desc)
        elif 'Description:' in t: t = lore(t)
        for vn, ep, old, new in VALUE_EDITS:
            if vn == nid:
                t2 = re.sub(rf'(EntryPoint: {ep}\n(?:  .*\n)*?  Value: ){re.escape(old)}\n', lambda m: m.group(1) + new + '\n', t, count=1)
                assert t2 != t, (nid, ep); t = t2
        if nid == 'ma3':     # Stunning Blows: Saboteur restricted to unarmed (right hand item type 0)
            t = add_unarmed(t)
        if nid in ('gun2', 'gun3'):
            t = t.rstrip('\n') + '\n' + gun_hit_effect(gunhit)
        if nid == 'ma5':
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + flowab + '\n'
        if nid == DROID_NODE:      # Bear Traps' (and Lockjaw's) entry points out, the Utility Droid power in
            t, n_eff = re.subn(r'^Effects:\n(?:[- ].*\n)*', '', t, count=1, flags=re.M)
            assert n_eff == 1 and 'Effects:' not in t, 'Bear Traps perk effects not where expected'
            # ...and its perk-script fragment (the "pick up a bear trap" activate entry it hooked is gone)
            t, n_vm = re.subn(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', t, count=1, flags=re.M)
            assert n_vm == 1 and 'PRKF_ORD' not in t, 'Bear Traps perk script not where expected'
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + droid['power'] + '\n'
        if nid in GLORY_ABILITY:
            t = t.rstrip('\n') + '\nEffects:\n- MutagenObjectType: PerkAbilityEffect\n  Ability: ' + glory[GLORY_ABILITY[nid]] + '\n'
        if nid == 'glo1':      # the player keeps full speed in Seismic Stomp's slow time (as Ordinator's Quick Reflexes)
            t += ('- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n  - RunOnTabIndex: 1\n    Conditions:\n'
                  '    - MutagenObjectType: ConditionFloat\n      Data:\n        MutagenObjectType: EPMagic_SpellHasKeywordConditionData\n'
                  f"        Keyword: {glory['slowkw']}\n      ComparisonValue: 1\n  EntryPoint: ModPlayerMagicSlowdown\n"
                  '  PerkConditionTabCount: 2\n  Value: 1\n')
        write('Perks', t)

    # --- hand-built records
    write_gunhit(gunhit, newid, nodeperk, write)
    write_flow(flowab, flowme, newid, write, nova)
    write_droid(droid, write)
    write_never(write)
    write_dummies(write)
    add_fever(newid, write, rec)
    add_tripwire_blast(newid, write, blast)
    write_glory(glory, write)
    for key, spell_src, name, wav in POWER_SOUNDS:
        add_power_sound(newid, write, psound[key], key, spell_src, name, wav)

    if bad:
        for k, v in sorted(bad.items()): print('UNRESOLVED', v, k)
        sys.exit('unresolved references - fix SPEC or the source trees')
    copy_assets(models, scripts)
    write_menu(nodes, nodeperk, write, {})
    print(f'records copied {len(copy)}, perks {len(nodes)}, next free ID 0x{nxt:03X}, models {len(models)}, scripts {len(scripts)}')


def add_unarmed(t):
    cond = ('  Conditions:\n  - Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            '        MutagenObjectType: GetEquippedItemTypeConditionData\n        ItemSource: Right\n'
            '      ComparisonValue: 0\n')
    out, n = re.subn(r'(- MutagenObjectType: PerkEntryPointSelectSpell\n)(  EntryPoint: ApplyCombatHitSpell\n)',
                     lambda m: m.group(1) + cond + m.group(2), t)
    assert n == 1, 'Saboteur hit-spell entry not found'
    # the damage bonus vs staggered enemies: the same unarmed condition on its owner tab (tab 0)
    tab0 = ('  - Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            '        MutagenObjectType: GetEquippedItemTypeConditionData\n        ItemSource: Right\n'
            '      ComparisonValue: 0\n')
    out, n = re.subn(r'(- MutagenObjectType: PerkEntryPointModifyValue\n  Conditions:\n)(  - RunOnTabIndex: 2\n)',
                     lambda m: m.group(1) + tab0 + m.group(2), out, count=1)
    assert n == 1, 'Saboteur damage entry not found'
    return out


def gun_hit_effect(spell):
    return ('Effects:\n- MutagenObjectType: PerkEntryPointSelectSpell\n  Conditions:\n  - RunOnTabIndex: 1\n'
            '    Conditions:\n    - MutagenObjectType: ConditionFloat\n      Data:\n'
            f'        MutagenObjectType: HasKeywordConditionData\n        Keyword: {WEAPTYPEBOW}\n'
            '      ComparisonValue: 1\n  EntryPoint: ApplyCombatHitSpell\n  PerkConditionTabCount: 3\n'
            f'  Spell: {spell}\n')


def write_gunhit(gunhit, newid, nodeperk, write):
    """One hit spell for both gun perks (ApplyCombatHitSpell applies a single spell per hit): Monk's bleed
    effect gated on Bleeding Shot, Enderal's weapon fire-enchant effect gated on Elemental Rounds."""
    monk_spell = newid[f'000879:{SOS}']
    t = open(glob.glob(os.path.join(ESP, 'Spells', f'* - {monk_spell.split(":")[0]}_*'))[0], encoding='utf-8').read().replace('\r\n', '\n')
    bleed = re.search(r'^  - BaseEffect: (.+?)\s*$|^- BaseEffect: (.+?)\s*$', t, re.M)
    be = (bleed.group(1) or bleed.group(2))
    t = re.sub(r'^FormKey: .*$', f'FormKey: {gunhit}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_GunHitSpell', t, count=1, flags=re.M)
    t = re.sub(r'^(Name:\n  TargetLanguage: English\n  Value: ).*$', r'\1Gunslinger', t, count=1, flags=re.M)
    def gate(perk):
        # MutagenObjectType must be the first key under Data or Spriggit fails to read it
        return ('  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n      MutagenObjectType: HasPerkConditionData\n'
                '      RunOnType: Reference\n      Reference: 000014:Skyrim.esm\n'
                f'      Perk: {perk}\n    ComparisonValue: 1\n')
    eff = re.search(r'^Effects:\n((?:[- ].*\n)*)', t, re.M)
    assert eff, 'Monk spell has no Effects'
    body = eff.group(1)
    body = re.sub(r'(- BaseEffect: .*\n(?:  Data:\n(?:    .*\n)*)?)', lambda m: m.group(1) + gate(nodeperk['gun3']), body, count=1)
    body += (f'- BaseEffect: {FIRE_ENCH}\n  Data:\n    Magnitude: 10\n    Duration: 0\n' + gate(nodeperk['gun2']))
    t = t[:eff.start(1)] + body + t[eff.end(1):]
    write('Spells', t)


def write_flow(ab, me, newid, write, nova):
    slow = newid[f'07B101:{ORD}']
    write('Spells', f"""FormKey: {ab}
EditorID: ZP_Prophecy_FlowStateAbility
Name:
  TargetLanguage: English
  Value: Flow State
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {me}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {me}
EditorID: ZP_Prophecy_FlowStateEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_FlowStateEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: SlowTime
      Object: {slow}
    - MutagenObjectType: ScriptObjectProperty
      Name: Nova
      Object: {nova['novaexp']}
    - MutagenObjectType: ScriptFloatProperty
      Name: NovaCooldown
      Data: {FLOW_NOVA['Cooldown']}
Name:
  TargetLanguage: English
  Value: Flow State
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    # Shock Nova (curator, 2026-10-23): Enderal's shock-mass blast at the player's feet on a combat dodge, own cooldown.
    # The explosion drops its full-screen ISM (the list strips screen flashes) and gets a wider radius; its damage is a
    # copy of the weapon shock enchantment (shared, so not edited in place) at FLOW_NOVA['Damage'], gated to actors
    # hostile to the player so the player and followers standing in the blast are spared.
    t = open(SHOCK_MASS_EXP, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {nova['novaexp']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_FlowStateNova', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n = re.subn(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    assert n == 2, 'shock-mass explosion ISM lines not where expected'
    t, n1 = re.subn(r'^ObjectEffect: .*$', f"ObjectEffect: {nova['novaench']}", t, count=1, flags=re.M)
    t, n2 = re.subn(r'^Radius: .*$', f"Radius: {FLOW_NOVA['Radius']}", t, count=1, flags=re.M)
    assert n1 == n2 == 1, 'shock-mass explosion fields not where expected'
    write('Explosions', t)
    t = open(SHOCK_DAMAGE_ENCH, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {nova['novaench']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_FlowStateNovaEnch', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n1 = re.subn(r'^Name:\n(?:  .*\n)+', 'Name:\n  TargetLanguage: English\n  Value: Shock Nova\n', t, count=1, flags=re.M)
    t, n2 = re.subn(r'^(    Magnitude: )20$', lambda m: m.group(1) + str(FLOW_NOVA['Damage']), t, count=1, flags=re.M)
    assert n1 == n2 == 1 and t.count('- BaseEffect:') == 1, 'shock enchantment not as expected'
    t = t.rstrip('\n') + ('\n  Conditions:\n  - MutagenObjectType: ConditionFloat\n    Data:\n'
                          '      MutagenObjectType: IsHostileToActorConditionData\n      TargetNpc: 000014:Skyrim.esm\n'
                          '    ComparisonValue: 1\n')
    write('ObjectEffects', t)


def write_droid(d, write):
    """Utility Droid (Gadgets node 3, curator 2026-10-23; replaced Bear Traps). A lesser power deploys a mechanical
    spider - Enderal's own Starling Spider (the friendly Starship-cave spider, DwarvenSpiderRace) - that follows the
    player on SureAI's _DefaultFollowPlayer package, heals them and staggers enemies around it, until it is destroyed.
    The first droid is free (once per save, flag d['free']); each later one costs DROID['Cost'] Spare Parts. One droid
    at a time: casting while it lives calls it back. The live droid is remembered in FormList d['list']."""
    # --- the droid: the Starling Spider record, re-purposed
    t = open(DROID_BASE_NPC, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {d['npc']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_UtilityDroid', t, count=1, flags=re.M)
    for pat, rep in [
            (r'^Factions:\n(?:- .*\n(?:  .*\n)*)', f'Factions:\n- Faction: {PLAYER_FACTION}\n  Fluff: 0x000000\n'),
            (r'^DeathItem: .*\n', ''),                                   # no farmable loot
            (r'^AIData:\n(?:  .*\n)*', 'AIData:\n  Aggression: Aggressive\n  Confidence: Brave\n  EnergyLevel: 50\n'
                                       '  Responsibility: NoCrime\n  Assistance: HelpsFriendsAndAllies\n'),
            (r'^Packages:\n(?:- .*\n)*', f'Packages:\n- {FOLLOW_PLAYER}\n'),
            (r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Utility Droid\n')]:
        t, n = re.subn(pat, rep, t, count=1, flags=re.M)
        assert n == 1, f'Starling Spider record changed: {pat}'
    t = re.sub(r'^(Race: .*\n)', lambda m: m.group(1) + f"ActorEffect:\n- {d['ab']}\n", t, count=1, flags=re.M)
    assert 'ActorEffect:' in t and t.count('ActorEffect:') == 1
    write('Npcs', t)

    # --- its ability: heal the player, stagger nearby enemies (script on the droid)
    write('Spells', f"""FormKey: {d['ab']}
EditorID: ZP_Prophecy_UtilityDroid_Ability
Name:
  TargetLanguage: English
  Value: Utility Droid
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Type: Ability
CastType: ConstantEffect
Effects:
- BaseEffect: {d['abme']}
  Data: {{}}
""")
    write('MagicEffects', f"""FormKey: {d['abme']}
EditorID: ZP_Prophecy_UtilityDroid_Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_UtilityDroidEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: StaggerSpell
      Object: {d['stg']}
    - MutagenObjectType: ScriptFloatProperty
      Name: HealAmount
      Data: {DROID['HealAmount']}
    - MutagenObjectType: ScriptIntProperty
      Name: HealInterval
      Data: {DROID['HealInterval']}
    - MutagenObjectType: ScriptFloatProperty
      Name: HealRadius
      Data: {DROID['HealRadius']}
    - MutagenObjectType: ScriptIntProperty
      Name: StaggerInterval
      Data: {DROID['StaggerInterval']}
    - MutagenObjectType: ScriptFloatProperty
      Name: StaggerRadius
      Data: {DROID['StaggerRadius']}
Name:
  TargetLanguage: English
  Value: Utility Droid
Flags:
- HideInUI
- NoMagnitude
- NoArea
- NoDuration
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: ConstantEffect
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")

    # --- the stagger it casts: Enderal's contact stagger (StaggerAttackFFContact 07809B) as a target-actor effect,
    # so a script can apply it to each enemy (Seismic Stomp's bleed pattern). Magnitude 0.5 (Stunning Blows uses 0.25).
    t = open(STAGGER_CONTACT_MGEF, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f"FormKey: {d['stgme']}", t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_UtilityDroid_StaggerEffect', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t, n1 = re.subn(r'^Name:\n(?:  .*\n)*', 'Name:\n  TargetLanguage: English\n  Value: Utility Droid\n', t, count=1, flags=re.M)
    t, n2 = re.subn(r'^TargetType: Touch$', 'TargetType: TargetActor', t, count=1, flags=re.M)
    t = re.sub(r'^Description:\n(?:  .*\n)*', "Description:\n  TargetLanguage: English\n  Value: ''\n", t, count=1, flags=re.M)
    assert n1 == n2 == 1 and 'Type: Stagger' in t, 'StaggerAttackFFContact not as expected'
    write('MagicEffects', t)
    write('Spells', f"""FormKey: {d['stg']}
EditorID: ZP_Prophecy_UtilityDroid_Stagger
Name:
  TargetLanguage: English
  Value: Utility Droid
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 013F44:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- NoAbsorbOrReflect
CastType: FireAndForget
TargetType: TargetActor
Effects:
- BaseEffect: {d['stgme']}
  Data:
    Magnitude: {DROID['StaggerMagnitude']}
""")

    # --- the power: deploy (free once, then Spare Parts) or call the living droid back
    write('Spells', f"""FormKey: {d['power']}
EditorID: ZP_Prophecy_UtilityDroid_Power
Name:
  TargetLanguage: English
  Value: Utility Droid
MenuDisplayObject: 0435A5:Skyrim.esm
EquipmentType: 025BEE:Skyrim.esm
Description:
  TargetLanguage: English
  Value: ''
Flags:
- IgnoreResistance
- NoAbsorbOrReflect
Type: LesserPower
CastType: FireAndForget
Effects:
- BaseEffect: {d['powerme']}
  Data:
    Duration: 1
""")
    write('MagicEffects', f"""FormKey: {d['powerme']}
EditorID: ZP_Prophecy_UtilityDroid_PowerEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_UtilityDroidPowerEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Droid
      Object: {d['npc']}
    - MutagenObjectType: ScriptObjectProperty
      Name: SpareParts
      Object: {SPARE_PARTS}
    - MutagenObjectType: ScriptObjectProperty
      Name: DroidList
      Object: {d['list']}
    - MutagenObjectType: ScriptObjectProperty
      Name: FreeUsed
      Object: {d['free']}
    - MutagenObjectType: ScriptIntProperty
      Name: Cost
      Data: {DROID['Cost']}
    - MutagenObjectType: ScriptFloatProperty
      Name: BaseHealth
      Data: {DROID['BaseHealth']}
    - MutagenObjectType: ScriptFloatProperty
      Name: HealthPerLevel
      Data: {DROID['HealthPerLevel']}
Name:
  TargetLanguage: English
  Value: Utility Droid
Flags:
- NoMagnitude
- NoArea
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    write('FormLists', f"FormKey: {d['list']}\nEditorID: ZP_Prophecy_UtilityDroid_Current\n")
    write('Globals', f"MutagenObjectType: GlobalShort\nFormKey: {d['free']}\nEditorID: ZP_Prophecy_UtilityDroid_FreeUsed\nData: 0\n")


def write_dummies(write):
    write('Quests', f"FormKey: {DUMMY_QUEST}\nEditorID: ZP_Prophecy_DummyQuest\nNextAliasID: 0\n")
    write('Locations', f"FormKey: {DUMMY_LOC}\nEditorID: ZP_Prophecy_DummyLocation\n")
    write('Spells', f"FormKey: {DUMMY_SPELL}\nEditorID: ZP_Prophecy_DummySpell\nEquipmentType: 013F44:Skyrim.esm\nType: Ability\nCastType: ConstantEffect\n")


def write_never(write):
    write('Perks', f"""FormKey: {NEVER}
EditorID: ZP_Prophecy_Never
Name:
  TargetLanguage: English
  Value: ''
NumRanks: 1
Hidden: True
""")


TRIPWIRE_PROC = f'0379A1:{ORD}'      # ORD_Sne_Tripwire_Spell_Proc - Ordinator's script remote-casts it on whoever trips
FIREBALL_EXP = os.path.join(REF, 'base', 'Skyrim', 'Explosions', 'FireBallExp01 - 0439C0_Skyrim.esm.yaml')
TRIPWIRE_DAMAGE = 40
# Flow State's Shock Nova (curator, 2026-10-23): Enderal's shock-mass blast + its weapon shock-damage enchantment, copied
SHOCK_MASS_EXP = os.path.join(REF, 'base', 'Skyrim', 'Explosions', 'ExplosionShockMass01ShockDamage - 03BC85_Skyrim.esm.yaml')
SHOCK_DAMAGE_ENCH = os.path.join(REF, 'base', 'Skyrim', 'ObjectEffects', 'EnchWeaponShockDamage06 - 045F9E_Skyrim.esm.yaml')
FLOW_NOVA = {'Damage': 40, 'Radius': 300, 'Cooldown': 15.0}


def add_tripwire_blast(newid, write, blast):
    """Tripwire (Gadgets): a snap by an enemy also sets off a fireball explosion at their feet (curator's request
    2026-10-21). Enderal's FireBallExp01 copied with Damage set and its full-screen flash (ISM 0439C1) removed - the
    list strips screen flashes (NoScreenFlashes). Placed by ZP_TripwireBlastEffect, an extra effect on Tripwire Snap
    gated to actors hostile to the player; Ordinator's own tripwire script is untouched."""
    t = open(FIREBALL_EXP, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {blast["exp"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_TripwireBlast', t, count=1, flags=re.M)
    t = re.sub(r'^Version2: .*\n', '', t, flags=re.M)
    t = re.sub(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    t2 = re.sub(r'^(Force: .*\n)', lambda m: m.group(1) + f'Damage: {TRIPWIRE_DAMAGE}\n', t, count=1, flags=re.M)
    assert t2 != t, 'FireBallExp01 has no Force line'
    write('Explosions', t2)
    write('Globals', f'MutagenObjectType: GlobalFloat\nFormKey: {blast["glob"]}\nEditorID: ZP_Prophecy_TripwireBlastTime\nData: 0\n')
    write('MagicEffects', f"""FormKey: {blast['mgef']}
EditorID: ZP_Prophecy_TripwireBlastEffect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_TripwireBlastEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: Blast
      Object: {blast['exp']}
    - MutagenObjectType: ScriptObjectProperty
      Name: LastBlast
      Object: {blast['glob']}
Name:
  TargetLanguage: English
  Value: Tripwire Blast
Flags:
- Hostile
- Detrimental
- NoMagnitude
- NoDuration
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
Conditions:
- MutagenObjectType: ConditionFloat
  Data:
    MutagenObjectType: IsHostileToActorConditionData
    TargetNpc: 000014:Skyrim.esm
  ComparisonValue: 1
""")
    h = newid[TRIPWIRE_PROC].split(':')[0]
    p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    assert blast['mgef'] not in t
    t = t.rstrip('\n') + f"\n- BaseEffect: {blast['mgef']}\n  Data:\n    Area: 8\n"
    assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(blast['mgef']), t + '\n', re.M), 'Effects is not the last block'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


# Sounds on using a power that ships silent (curator's files, 2026-10-22): (key, source power, display name, file).
# The .wav files are loose and not committed - tools/03-install-sounds.py. Append new entries LAST (IDs follow order).
POWER_SOUNDS = [
    ('Tripwire_Ratchet', f'0379A4:{ORD}', 'Explosive Tripwire', r'Data\Sound\FX\Zenderal\ZEN_TripwireRatchet_01.wav'),
    ('Smokescreen_Burst', f'036EB3:{ORD}', 'Smokescreen', r'Data\Sound\FX\Zenderal\ZEN_SmokescreenBurst_01.wav'),
]


def add_power_sound(newid, write, r, key, spell_src, name, wav):
    """A sound when a power is used (Explosive Tripwire's ratchet as the player kneels, Smokescreen's burst; both
    ship silent from Ordinator). An extra effect on the power whose script plays one sound - Ordinator's own scripts
    stay untouched."""
    write('SoundDescriptors', f"""FormKey: {r['sound']}
EditorID: ZP_Prophecy_{key}Sound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {wav}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {r['marker']}\nEditorID: ZP_Prophecy_{key}Marker\nSoundDescriptor: {r['sound']}\n")
    write('MagicEffects', f"""FormKey: {r['mgef']}
EditorID: ZP_Prophecy_{key}Effect
VirtualMachineAdapter:
  Scripts:
  - Name: ZP_PlaySoundEffect
    Properties:
    - MutagenObjectType: ScriptObjectProperty
      Name: SoundToPlay
      Object: {r['marker']}
Name:
  TargetLanguage: English
  Value: {name}
Flags:
- NoMagnitude
- NoArea
- NoDuration
- HideInUI
- Painless
Archetype:
  MutagenObjectType: MagicEffectArchetype
  Type: Script
CastType: FireAndForget
DualCastScale: 1
CastingSoundLevel: Silent
Sounds: []
Description:
  TargetLanguage: English
  Value: ''
""")
    h = newid[spell_src].split(':')[0]
    p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    assert r['mgef'] not in t
    t = t.rstrip('\n') + f"\n- BaseEffect: {r['mgef']}\n  Data: {{}}\n"
    assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(r['mgef']), t + '\n', re.M), 'Effects is not the last block'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def add_fever(newid, write, rec):
    """Arcane Fever on the two free heals (Enderal's rule: ~26 HP per fever point)."""
    for spell_src, mag in [(f'000E0F:{SOS}', 1), (f'000E37:{SOS}', 4)]:   # Healing Presence / Templar heals
        h = newid[spell_src].split(':')[0]
        p = glob.glob(os.path.join(ESP, 'Spells', f'* - {h}_*'))[0]
        t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        assert 'TargetType:' not in t, 'heal spell is not self-delivered'
        assert FEVER not in t
        t = t.rstrip('\n') + f'\n- BaseEffect: {FEVER}\n  Data:\n    Magnitude: {mag}\n    Duration: 1\n'
        assert re.search(r'^Effects:\n(?:[- ].*\n)+- BaseEffect: ' + re.escape(FEVER), t + '\n', re.M), 'Effects is not the last block'
        open(p, 'w', encoding='utf-8', newline='\r\n').write(t)


def copy_assets(models, scripts):
    import struct
    comp = os.path.join(PATCH, 'Scripts', 'compiled')
    for f in glob.glob(os.path.join(comp, '*.pex')):
        if not os.path.basename(f).lower().startswith('zp_'): os.remove(f)
    assets = os.path.join(PATCH, 'assets')
    for sub in ('meshes', 'textures'):   # interface/ProphecyPics comes from 02-convert-thumbnails.py - keep it
        shutil.rmtree(os.path.join(assets, sub), ignore_errors=True)
    for plugin, bsas in BSAS.items():
        lst = {}
        for b in bsas:
            d, l = _bsa.listing(os.path.join(RAW[plugin], b))
            for k, v in l.items(): lst[k] = (d, v)
        want_pex = {n for p, n in scripts if p == plugin}
        # script dependencies: any other script of this mod named in a pex string table
        allpex = {k.split('\\')[-1][:-4]: k for k in lst if k.endswith('.pex')}
        todo = [n for n in want_pex if n in allpex]; done = set()
        while todo:
            n = todo.pop()
            if n in done: continue
            done.add(n); data = _bsa.read(*lst[allpex[n]])
            for other in allpex:
                if other not in done and other.encode() in data.lower(): todo.append(other)
        for n in done:
            open(os.path.join(comp, n + '.pex'), 'wb').write(_bsa.read(*lst[allpex[n]]))
        missing = [n for n in want_pex if n not in allpex and not n.startswith('zp_')]
        if missing: print(f'  scripts not in {plugin} BSA (engine/base scripts?):', sorted(missing))
        # meshes + every texture they name
        todo = ['meshes\\' + m.replace('/', '\\') for p, m in models if p == plugin]
        for k in todo:
            if k not in lst: continue
            data = _bsa.read(*lst[k])
            out = os.path.join(assets, k.replace('\\', os.sep)); os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(data)
            for tex in set(re.findall(rb'[\w\\/ .-]+?\.dds', data, re.I)):
                tk = tex.decode('latin1').lower().replace('/', '\\').lstrip('\\')
                if not tk.startswith('textures\\'): tk = 'textures\\' + tk
                if tk in lst:
                    o2 = os.path.join(assets, tk.replace('\\', os.sep)); os.makedirs(os.path.dirname(o2), exist_ok=True)
                    open(o2, 'wb').write(_bsa.read(*lst[tk]))


# ------------------------------------------------------------------------------------------------ Glory
# 'shout', 'word', 'dashspell', 'dashme' (0x91A-0x91D) were Gap Closer's; retired 2026-10-22 for Seismic Stomp and
# kept as unused names so the later Glory records keep their IDs. Never reuse them: older saves still point at them.
GLORY_RECORDS = ('shout', 'word', 'dashspell', 'dashme', 'swab', 'swme', 'dsab', 'banner', 'bannerme', 'cdspell', 'cdme')
GLORY_RECORDS_2 = ('hornsound', 'hornmarker')     # added 2026-10-22, after the Tripwire scene block
GLORY_RECORDS_3 = ('stompspell', 'stompme', 'stompexp', 'stompsound', 'bleedspell', 'bleedme', 'stompcd', 'stompcdme')
GLORY_RECORDS_4 = ('slowspell', 'slowme')     # Seismic Stomp's slow time, added 2026-10-22
STOMP_SLOW = (0.3, 10)                         # world speed, seconds
GLORY_RECORDS_5 = ('slowkw',)                  # the stomp slow time's own keyword, added 2026-10-22
GLORY_RECORDS_6 = ('surab', 'surme')           # Surrounded's ability + effect, after the late glo5 perk (0x93B-0x93C)
FLOW_NOVA_RECORDS = ('novaexp', 'novaench')     # Flow State's Shock Nova explosion + enchantment (0x93D-0x93E), 2026-10-23
# Utility Droid (Gadgets node 3, curator 2026-10-23), 0x93F-0x947: the droid NPC, its heal/stagger ability, the stagger
# spell it casts, the power and its effect, the one-droid list and the free-first-droid flag.
DROID_NODE = 'gad3'
DROID_RECORDS = ('npc', 'ab', 'abme', 'stgme', 'stg', 'power', 'powerme', 'list', 'free')
DROID = {'Cost': 10, 'HealAmount': 15.0, 'HealInterval': 4, 'HealRadius': 640.0, 'StaggerInterval': 6,
         'StaggerRadius': 300.0, 'StaggerMagnitude': 0.5, 'BaseHealth': 100.0, 'HealthPerLevel': 10.0}
DROID_BASE_NPC = os.path.join(REF, 'mods', 'EGO - Enderal Gameplay Overhaul', 'Npcs',
                              '_00E_StarshipCaveHelpfulSpiderPatrol01 - 130AE8_Skyrim.esm.yaml')   # Starling Spider
STAGGER_CONTACT_MGEF = os.path.join(REF, 'base', 'Skyrim', 'MagicEffects', 'StaggerAttackFFContact - 07809B_Skyrim.esm.yaml')
SPARE_PARTS = '0773ED:Skyrim.esm'           # _00E_CraftingPieces, "Spare Parts"
FOLLOW_PLAYER = '04B037:Skyrim.esm'         # _DefaultFollowPlayer (Follow template, target PlayerRef; SureAI's scenes)
PLAYER_FACTION = '000DB1:Skyrim.esm'
STOMP_SOUND = r'Data\Sound\FX\Zenderal\ZEN_SeismicStomp_01.wav'    # loose, not committed: tools/03-install-sounds.py
SHOCKWAVE = os.path.join(REF, 'mods', 'Apocalypse - Magic of Skyrim', 'Explosions',
                         'WB_AlterationEarth_Explosion_ThrummingStone_Shockwave - 07FE7C_Apocalypse - Magic of Skyrim.esp.yaml')
WARHORN = r'Data\Sound\FX\Zenderal\ZEN_WarBannerHorn_01.wav'    # loose, not committed: tools/03-install-sounds.py
GLORY_ABILITY = {'glo1': 'stompspell', 'glo2': 'swab', 'glo3': 'dsab', 'glo4': 'banner', 'glo5': 'surab'}     # perk -> record its PerkAbilityEffect grants
TRIUMVIRATE = 'Triumvirate - Mage Archetypes.esp'


def write_glory(g, write):
    """Glory's records (curator's design, 2026-10-21; Gap Closer became Seismic Stomp 2026-10-22).
    Seismic Stomp follows Enderal's own stomp beat (_00E_MQ15_Functions.TealorBreakWall: PlayIdle _00E_IdleStomp,
    wait 0.5 s, PlaceAtMe a shockwave, ShakeCamera) - the idle is Enderal's FNIS basic idle "Stomp" (stomp.hkx in
    FNIS_Enderal_Behavior, which Pandora's 0_Master links) and Enderal plays it on the player too (Theriantrophist).
    The shockwave is Apocalypse's Thrumming Stone shockwave explosion copied with its model (Apocalypse's BSA mesh),
    without its ISM, with the curator's stomp sound and Enderal's FXDragonTailstompImpactSet. Knockback is the script's
    PushActorAway on every hostile in range; the bleed is a target-delivered copy of Bleeding Shot's (Monk) bleed.
    War Banner is a lesser power with Templar's cooldown pattern (a script-less effect checked by HasMagicEffect).
    Its chains are Triumvirate's Stave of Binding proc (TVR_Shaman_Spell_StaveBinding_Proc 423DA8), read at runtime
    with GetFormFromFile, so the plugin does not master Triumvirate."""
    def mgef(fk, edid, name, desc, flags, archetype, cast='FireAndForget', vmad='', extra=''):
        return (f'FormKey: {fk}\nEditorID: {edid}\n' + vmad +
                f"Name:\n  TargetLanguage: English\n  Value: {name}\n" + extra +
                'Flags:\n' + ''.join(f'- {x}\n' for x in flags) +
                f'Archetype:\n  MutagenObjectType: MagicEffectArchetype\n{archetype}'
                f'CastType: {cast}\nDualCastScale: 1\nCastingSoundLevel: Silent\nSounds: []\n'
                f"Description:\n  TargetLanguage: English\n  Value: '{desc}'\n")
    def script(name, props):
        out = f'VirtualMachineAdapter:\n  Scripts:\n  - Name: {name}\n    Properties:\n'
        for pn, kind, val in props:
            key = 'Object' if kind == 'Object' else 'Data'
            out += f'    - MutagenObjectType: Script{kind}Property\n      Name: {pn}\n      {key}: {val}\n'
        return out
    def spell(fk, edid, name, typ, cast, effects, equip='013F44:Skyrim.esm', extra=''):
        t = (f'FormKey: {fk}\nEditorID: {edid}\nName:\n  TargetLanguage: English\n  Value: {name}\n'
             f'MenuDisplayObject: 0435A5:Skyrim.esm\nEquipmentType: {equip}\n'
             "Description:\n  TargetLanguage: English\n  Value: ''\n" + extra)
        if typ: t += f'Type: {typ}\n'
        return t + f'CastType: {cast}\nEffects:\n' + effects

    # --- Seismic Stomp: lesser power -> scripted stomp (idle, shockwave, knockback, bleed); 60 s cooldown effect
    write('Spells', spell(g['stompspell'], 'ZP_Prophecy_SeismicStomp_Power', 'Seismic Stomp', 'LesserPower', 'FireAndForget',
                          f'- BaseEffect: {g["stompme"]}\n  Data:\n    Duration: 6\n', equip='025BEE:Skyrim.esm',   # outlasts the script's waits, even slowed
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['stompme'], 'ZP_Prophecy_SeismicStomp_Effect', 'Seismic Stomp', '',
                               ['NoMagnitude', 'NoArea', 'HideInUI', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_SeismicStompEffect', [
                                   ('StompIdle', 'Object', '146675:Skyrim.esm'),        # _00E_IdleStomp
                                   ('Shockwave', 'Object', g['stompexp']),
                                   ('Bleed', 'Object', g['bleedspell']),
                                   ('SlowTime', 'Object', g['slowspell']),
                                   ('Cooldown', 'Object', g['stompcd']),
                                   ('CooldownEffect', 'Object', g['stompcdme'])])))
    t = open(SHOCKWAVE, encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {g["stompexp"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_Explosion', t, count=1, flags=re.M)
    t = re.sub(r'^(?:ImageSpaceModifier|ISRadius): .*\n', '', t, flags=re.M)
    t = re.sub(r'^Sound1: .*$', f'Sound1: {g["stompsound"]}', t, count=1, flags=re.M)
    t = re.sub(r'^ImpactDataSet: .*$', 'ImpactDataSet: 03F819:Skyrim.esm', t, count=1, flags=re.M)   # FXDragonTailstompImpactSet
    assert 'Apocalypse' not in t and 'AlterationEarth_Explosion_Massive.nif' in t, 'shockwave copy still names Apocalypse'
    write('Explosions', t)
    write('SoundDescriptors', f"""FormKey: {g['stompsound']}
EditorID: ZP_Prophecy_SeismicStomp_Sound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {STOMP_SOUND}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    bleed_src = glob.glob(os.path.join(ESP, 'MagicEffects', '* - 000829_*'))
    assert len(bleed_src) == 1 and 'Monk' in os.path.basename(bleed_src[0]), "Bleeding Shot's bleed MGEF moved"
    t = open(bleed_src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = re.sub(r'^FormKey: .*$', f'FormKey: {g["bleedme"]}', t, count=1, flags=re.M)
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_BleedEffect', t, count=1, flags=re.M)
    t2 = re.sub(r'^TargetType: Touch$', 'TargetType: TargetActor', t, count=1, flags=re.M)
    assert t2 != t, 'bleed MGEF is no longer Touch'
    write('MagicEffects', t2)
    write('Spells', spell(g['bleedspell'], 'ZP_Prophecy_SeismicStomp_Bleed', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["bleedme"]}\n  Data:\n    Magnitude: 10\n    Duration: 5\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n') .replace('CastType: FireAndForget\n', 'CastType: FireAndForget\nTargetType: TargetActor\n'))
    # slow time: Quick Reflexes' self effect (Flow State's) copied, its dispel-after-delay script set to STOMP_SLOW[1]
    src = glob.glob(os.path.join(ESP, 'MagicEffects', f"* - {g['quickreflexes_me'].split(':')[0]}_*"))
    assert len(src) == 1 and 'QuickReflexes_Effect_Self' in os.path.basename(src[0]), 'Quick Reflexes self effect moved'
    t = open(src[0], encoding='utf-8').read().replace('\r\n', '\n')
    t = t.replace(g['quickreflexes_me'], g['slowme'])                 # FormKey + its own no-recast condition
    t = re.sub(r'^EditorID: .*$', 'EditorID: ZP_Prophecy_SeismicStomp_SlowTimeEffect', t, count=1, flags=re.M)
    # its own keyword, not PerkQuickReflexesKeyword 046BB3: Enderal's Keeper perks (Fast Reflexes, Steadfast) set
    # the player's slowdown to 0.5 for anything carrying 046BB3, and Flow State keeps 046BB3 for itself
    assert t.count('- 046BB3:Skyrim.esm\n') == 1, 'Quick Reflexes keyword not where expected'
    t = t.replace('- 046BB3:Skyrim.esm\n', f"- {g['slowkw']}\n")
    # no screen blur (curator, 2026-10-22): drop Quick Reflexes' MagicImodBasicScript, which applies QuickReflexesImod
    # 10C761 (radial blur, double vision, depth of field) for the whole effect. Flow State keeps it.
    t, n = re.subn(r'^  - Name: MagicImodBasicScript\n    Properties:\n(?:    .*\n)+?(?=  - Name: )', '', t, count=1, flags=re.M)
    assert n == 1 and '10C761' not in t, 'Quick Reflexes blur script not found on the slow-time copy'
    t2 = re.sub(r'(Name: ORD_DelayUntilDispel\n      Data: )\S+', lambda m: m.group(1) + str(STOMP_SLOW[1]), t, count=1)
    assert t2 != t and t2.count(g['slowme']) == 2, 'slow-time copy not as expected'
    write('MagicEffects', t2)
    write('Keywords', f"FormKey: {g['slowkw']}\nEditorID: ZP_Prophecy_SeismicStompSlowKeyword\nColor: '#00000000'\n")
    write('Spells', spell(g['slowspell'], 'ZP_Prophecy_SeismicStomp_SlowTime', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["slowme"]}\n  Data:\n    Magnitude: {STOMP_SLOW[0]}\n    Duration: {STOMP_SLOW[1]}\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('Spells', spell(g['stompcd'], 'ZP_Prophecy_SeismicStomp_Cooldown', 'Seismic Stomp', None, 'FireAndForget',
                          f'- BaseEffect: {g["stompcdme"]}\n  Data:\n    Duration: 30\n', extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['stompcdme'], 'ZP_Prophecy_SeismicStomp_CooldownEffect', 'Seismic Stomp',
                               'Seismic Stomp can be used again in <dur> seconds.', ['Recover'], '  Type: Script\n'))

    # --- Second Wind: an ability whose script restores Stamina on hits taken at half Health or less
    write('Spells', spell(g['swab'], 'ZP_Prophecy_SecondWind_Ability', 'Second Wind', 'Ability', 'ConstantEffect',
                          f'- BaseEffect: {g["swme"]}\n  Data: {{}}\n'))
    write('MagicEffects', mgef(g['swme'], 'ZP_Prophecy_SecondWind_Effect', 'Second Wind',
                               'While at or below half Health, every hit you take restores 20 Stamina.',
                               ['NoMagnitude', 'NoArea', 'NoDuration', 'Painless'], '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_SecondWindEffect', [('Stamina', 'Float', 20), ('HealthThreshold', 'Float', 0.5)])))

    # --- Surrounded: an ability whose script restores Stamina each second while enough enemies are close
    write('Spells', spell(g['surab'], 'ZP_Prophecy_Surrounded_Ability', 'Surrounded', 'Ability', 'ConstantEffect',
                          f'- BaseEffect: {g["surme"]}\n  Data: {{}}\n'))
    write('MagicEffects', mgef(g['surme'], 'ZP_Prophecy_Surrounded_Effect', 'Surrounded',
                               'While 3 or more enemies are close to you, your Stamina regenerates 2 points per second.',
                               ['NoMagnitude', 'NoArea', 'NoDuration', 'Painless'], '  Type: Script\n', cast='ConstantEffect',
                               vmad=script('ZP_SurroundedEffect', [('Radius', 'Float', SURROUNDED['Radius']),
                                                                   ('MinEnemies', 'Int', SURROUNDED['MinEnemies']),
                                                                   ('StaminaPerSecond', 'Float', SURROUNDED['StaminaPerSecond'])])))

    # --- Dragon Scale: Enderal's own resist abilities' effects at 25
    write('Spells', spell(g['dsab'], 'ZP_Prophecy_DragonScale_Ability', 'Dragon Scale', 'Ability', 'ConstantEffect',
                          ''.join(f'- BaseEffect: {fx}\n  Data:\n    Magnitude: 25\n'
                                  for fx in ('024314:Skyrim.esm', '024315:Skyrim.esm', '024318:Skyrim.esm'))))  # AbResistFire/Frost/Shock

    # --- War Banner: lesser power -> 15 s scripted banner; 300 s cooldown effect
    write('Spells', spell(g['banner'], 'ZP_Prophecy_WarBanner_Power', 'War Banner', 'LesserPower', 'FireAndForget',
                          f'- BaseEffect: {g["bannerme"]}\n  Data:\n    Duration: 15\n', equip='025BEE:Skyrim.esm',
                          extra='Flags:\n- IgnoreResistance\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['bannerme'], 'ZP_Prophecy_WarBanner_Effect', 'War Banner',
                               'Near your banner you heal 20 Health per second; enemies who come close are bound in chains.',
                               ['NoMagnitude', 'NoArea', 'Painless'], '  Type: Script\n',
                               vmad=script('ZP_WarBannerEffect', [
                                   ('Banner', 'Object', '060165:Skyrim.esm'),          # CivilWarBanner02: Enderal's camp banner frame (no cloth)
                                   ('Cloth', 'Object', '0EAC23:Skyrim.esm'),           # _00E_BannerNehrimesian, hung from the frame's crossbar
                                   ('HornSound', 'Object', g['hornmarker']),
                                   ('Cooldown', 'Object', g['cdspell']),
                                   ('CooldownEffect', 'Object', g['cdme']),
                                   ('Radius', 'Float', 400), ('HealPerSecond', 'Float', 20)])))
    write('SoundDescriptors', f"""FormKey: {g['hornsound']}
EditorID: ZP_Prophecy_WarBanner_HornSound
Type: Standard
Category: 01A0BD:Skyrim.esm
SoundFiles:
- {WARHORN}
OutputModel: 0B6463:Skyrim.esm
LoopAndRumble: {{}}
Priority: 128
""")
    write('SoundMarkers', f"FormKey: {g['hornmarker']}\nEditorID: ZP_Prophecy_WarBanner_HornMarker\nSoundDescriptor: {g['hornsound']}\n")
    write('Spells', spell(g['cdspell'], 'ZP_Prophecy_WarBanner_Cooldown', 'War Banner', None, 'FireAndForget',
                          f'- BaseEffect: {g["cdme"]}\n  Data:\n    Duration: 300\n',
                          extra='Flags:\n- NoAbsorbOrReflect\n'))
    write('MagicEffects', mgef(g['cdme'], 'ZP_Prophecy_WarBanner_CooldownEffect', 'War Banner',
                               'War Banner can be raised again in <dur> seconds.', ['Recover'], '  Type: Script\n'))


def perk_powers(esp, perk_fks):
    """(perk index, spell FormKey) for every perk whose PerkAbilityEffect is a Power/LesserPower. AddPerk from a
    script does not hand out power-type abilities (Explosive Tripwire, 2026-10-21), so the menu AddSpells them."""
    idx, spells = [], []
    for k, fk in enumerate(perk_fks):
        t = open(glob.glob(os.path.join(esp, 'Perks', f'* - {fk.split(":")[0]}_*'))[0], encoding='utf-8').read()
        for ab in re.findall(r'MutagenObjectType: PerkAbilityEffect\r?\n(?:  .*\r?\n)*?  Ability: ([^\r\n]+)', t):
            sp = glob.glob(os.path.join(esp, 'Spells', f'* - {ab.split(":")[0]}_*')) if ab.endswith(MOD) else []
            if sp and re.search(r'^Type: (Power|LesserPower|Voice)\s*$', open(sp[0], encoding='utf-8').read(), re.M):
                idx.append(k); spells.append(ab)
    assert len(idx) == len(set(idx)), 'a perk grants more than one power'
    return idx, spells


# Items handed out ONCE per save when a perk is owned (2026-10-22, curator: the turret power was useless until a
# turret was crafted from rare scrap). (perk node, item EditorID); the forge recipe stays for replacements.
GIFTS = [('gad4', 'ZP_ORD_Smh_DwarvenAutocannon_Misc')]


def gift_props(esp, perk_index):
    """(GiftPerk ints, GiftItem FormKeys) for the menu quest; items found by EditorID so v2 can call it too."""
    idx, items = [], []
    for nid, edid in GIFTS:
        hit = [p for p in glob.glob(os.path.join(esp, 'MiscItems', '*.yaml')) if os.path.basename(p).startswith(edid + ' - ')]
        assert len(hit) == 1, f'gift item {edid} not found'
        idx.append(perk_index[nid])
        items.append(re.search(r'^FormKey: (.+?)\s*$', open(hit[0], encoding='utf-8').read(), re.M).group(1))
    return idx, items


def write_menu(nodes, nodeperk, write, grants):
    """The perk menu is Enderal's UIExtensions list menu, run by ZP_ProphecyMenu on quest ZP_ProphecyInit 0x807.
    Custom Skills Framework was dropped 2026-10-21: the Skyrim perk screen it draws on does not work in Enderal 2.1
    (four in-game tests, see arch-docs/patches/Prophecy.md). Writes one description box per perk, the quest's
    script properties, and points the power's effect at the quest.
    2026-10-21: the menu is B612's traits card menu (the one Biggie Traits uses) - one card per perk with a
    thumbnail at Interface/ProphecyPics/<perk EditorID>.dds (art: see arch-docs/patches/Prophecy.md)."""
    order = [n[0] for _, _, ns in TREES for n in ns]
    descs, images = [], []
    for nid in order:
        p = glob.glob(os.path.join(ESP, 'Perks', f'* - {nodeperk[nid].split(":")[0]}_*'))[0]
        t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        val = lambda key: re.search(rf'^{key}:\n  TargetLanguage: English\n  Value: (.*)$', t, re.M).group(1)
        unq = lambda v: v[1:-1].replace("''", "'") if v.startswith("'") else v
        descs.append(unq(val('Description')))
        images.append(f'ProphecyPics/{ed(t)}.dds')
    strs = lambda xs: ''.join("      - '" + x.replace("'", "''") + "'\n" for x in xs)
    pos = {nid: k for k, nid in enumerate(order)}
    pa = [pos[nodes[n][5][0]] if nodes[n][5] else -1 for n in order]
    pb = [pos[nodes[n][5][1]] if len(nodes[n][5]) > 1 else -1 for n in order]
    objs = lambda fks: ''.join(f"      - Name: ''\n        Object: {fk}\n" for fk in fks)
    ints = lambda xs: ''.join(f'      - {x}\n' for x in xs)
    prop = lambda name, fk: (f'    - MutagenObjectType: ScriptObjectProperty\n      Name: {name}\n      Object: {fk}\n')
    # points already handed out (AwardPoints pays level/5 minus this). Written here: it was once lost from the YAML,
    # the property resolved to None and every open paid the full level/5 again.
    for p in glob.glob(os.path.join(ESP, 'Globals', '* - 000809_*')): os.remove(p)
    write('Globals', f'MutagenObjectType: GlobalShort\nFormKey: 000809:{MOD}\nEditorID: ZP_ProphecyPointsEarned\nData: 0\n')
    pw_i, pw_s = perk_powers(ESP, [nodeperk[n] for n in order])
    for nid, form in grants.items():             # extra forms granted like the powers (a Shout needs this; none today)
        pw_i.append(pos[nid]); pw_s.append(form)
    print('powers granted by the menu:', pw_s)
    gift_i, gift_s = gift_props(ESP, pos)
    # tree choice box + where each tree starts in the tree-major arrays (last entry = total)
    starts, k = [], 0
    for _, _, ns in TREES:
        starts.append(k); k += len(ns)
    starts.append(k)
    btn = lambda s: f'- Text:\n    TargetLanguage: English\n    Value: {s}\n'
    for p in glob.glob(os.path.join(ESP, 'Messages', '* - 00080D_*')): os.remove(p)
    write('Messages', f'FormKey: 00080D:{MOD}\nEditorID: ZP_ProphecyMenu\nDescription:\n  TargetLanguage: English\n'
                      '  Value: Which prophecy will you read?\nINAM: 0x00000000\nFlags:\n- MessageBox\nMenuButtons:\n' +
                      ''.join(btn(t) for t, _, _ in TREES) + btn('Cancel'))
    # The menu arrays go on the quest (what a new save starts with) AND on the power's effect, whose instance is
    # created from the plugin on every cast and passed to ZP_ProphecyMenu.Refresh: a running quest keeps its old
    # property values in the save, so without this new perks never reached existing saves (2026-10-22).
    arrays = ('    - MutagenObjectType: ScriptObjectListProperty\n      Name: Perks\n      Objects:\n' + objs(nodeperk[n] for n in order) +
              '    - MutagenObjectType: ScriptStringListProperty\n      Name: Descriptions\n      Data:\n' + strs(descs) +
              '    - MutagenObjectType: ScriptStringListProperty\n      Name: Images\n      Data:\n' + strs(images) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: ParentA\n      Data:\n' + ints(pa) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: ParentB\n      Data:\n' + ints(pb) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: PowerPerk\n      Data:\n' + ints(pw_i) +
              '    - MutagenObjectType: ScriptObjectListProperty\n      Name: PowerSpell\n      Objects:\n' + objs(pw_s) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: TreeStart\n      Data:\n' + ints(starts) +
              '    - MutagenObjectType: ScriptIntListProperty\n      Name: GiftPerk\n      Data:\n' + ints(gift_i) +
              '    - MutagenObjectType: ScriptObjectListProperty\n      Name: GiftItem\n      Objects:\n' + objs(gift_s))
    write('Quests',
          f'FormKey: 000807:{MOD}\nEditorID: ZP_ProphecyInit\nVirtualMachineAdapter:\n  Scripts:\n'
          '  - Name: ZP_ProphecyInit\n    Properties:\n' + prop('ZP_ProphecyPower', f'000805:{MOD}') +
          '  - Name: ZP_ProphecyMenu\n    Properties:\n' +
          prop('ZP_ProphecyMenuMsg', f'00080D:{MOD}') + prop('ZP_ProphecyPoints', f'000802:{MOD}') +
          prop('ZP_ProphecyPointsEarned', f'000809:{MOD}') + arrays +
          "  FileName: ''\nFlags:\n- StartGameEnabled\n- RunOnce\nNextAliasID: 0\n")
    p = glob.glob(os.path.join(ESP, 'MagicEffects', '* - 000806_*'))[0]
    t = open(p, encoding='utf-8').read().replace('\r\n', '\n')
    t2 = re.sub(r'(  - Name: ZP_ProphecyPowerEffect\n    Properties:\n)(?:    - .*\n(?:      .*\n)*)+',
                lambda m: m.group(1) + prop('MenuQuest', f'000807:{MOD}') + arrays, t, count=1)
    assert t2 != t or 'Name: MenuQuest' in t, 'power effect VMAD not rewritten'
    open(p, 'w', encoding='utf-8', newline='\r\n').write(t2)
    csf = os.path.join(PATCH, 'csf')
    if os.path.isdir(csf): shutil.rmtree(csf)


if __name__ == '__main__':
    main()
