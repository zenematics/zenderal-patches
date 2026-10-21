"""Shared goblin weapons for 01-build-creature.py and 01b-build-mihail.py (curator, 2026-10-21: "replace all
goblin weapons to Iron").

The Arp inventories the goblins inherit arm them with EGO's `02E_MOB_RuneWeapon_Arp` (rune axe/sword), a
rune sword, an oak bow and old rune arrows; Mihail's shaman also carries his goblin staff. All of those are
dropped and each role gets iron (tier `_01E_02`, Enderal's own records):
  one-handed  -> ZEN_GoblinIron1H: Iron Sword / War Axe / Mace / Dagger (one at random)
  two-handed  -> ZEN_GoblinIron2H: Iron Claymore / Battleaxe / Warhammer (Mihail's Berserker and Warlord)
  archers     -> Longbow (_01E_02_Longbow; there is no iron bow, and Enderal retired the Hunting Bow as
                 `_00E_HuntingBow_unused`) + 20 Iron Arrows + an Iron Dagger
Everything else (Arp loot list, Mihail's shields, clothes, ingredients) stays.
"""
import re

MOD_KEY = 'Zenderal - Goblins.esp'
EGO = 'Enderal SE - Gameplay Overhaul.esp'
NL = '\r\n'

IRON_1H = ('000822', 'ZEN_GoblinIron1H', ['0028CF', '0028D5', '0028D4', '0028D2'])
IRON_2H = ('000823', 'ZEN_GoblinIron2H', ['0028D3', '0028D1', '0028D6'])
LONGBOW = '014F7F:Skyrim.esm'
IRON_ARROW = '0457D8:Skyrim.esm'
IRON_DAGGER = '0028D2:Skyrim.esm'
DROP = {f'001E46:{EGO}', '07C9A4:Skyrim.esm', '07C9A5:Skyrim.esm', '07C97F:Skyrim.esm', '08659D:Skyrim.esm'}

ONE_HANDED = [(f'{IRON_1H[0]}:{MOD_KEY}', 1)]
ROLE_GEAR = {
    'Goblin': ONE_HANDED, 'Scout': ONE_HANDED, 'Chief': ONE_HANDED, 'Shaman': ONE_HANDED,
    'MGoblin': ONE_HANDED, 'MSkirmisher': ONE_HANDED, 'MShaman': ONE_HANDED,
    'MBerserker': [(f'{IRON_2H[0]}:{MOD_KEY}', 1)], 'MWarlord': [(f'{IRON_2H[0]}:{MOD_KEY}', 1)],
    'Archer': [(LONGBOW, 1), (IRON_ARROW, 20), (IRON_DAGGER, 1)],
    'MArcher': [(LONGBOW, 1), (IRON_ARROW, 20), (IRON_DAGGER, 1)],
}


def leveled_list(template_text, fid, edid, weapons):
    """A one-of-these LVLI built on an existing LVLI's YAML (EGO's rune-weapon list): new key, new entries."""
    head = template_text[:template_text.index('Entries:')]
    head = re.sub(r'^FormKey: .+', f'FormKey: {fid}:{MOD_KEY}', head, count=1, flags=re.M)
    head = re.sub(r'^EditorID: \S+', f'EditorID: {edid}', head, count=1, flags=re.M)
    entries = ''.join(f'- Data:{NL}    Level: 1{NL}    Reference: {w}:Skyrim.esm{NL}    Count: 1{NL}' for w in weapons)
    return head + 'Entries:' + NL + entries


def set_weapons(text, role, extra_drop=()):
    """Drop every listed weapon item from the NPC's Items, then add the role's iron gear first."""
    drop = DROP | set(extra_drop)
    lines = text.split(NL)
    start = lines.index('Items:')
    out, i, dropped = lines[:start + 1], start + 1, []
    while i < len(lines) and (lines[i].startswith('- Item:') or lines[i].startswith('    ')):
        block = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].startswith('    '):
            block.append(lines[i])
            i += 1
        item = re.search(r'^    Item: (.+)$', block[1]).group(1).strip()
        if item in drop:
            dropped.append(item)
        else:
            out += block
    gear = []
    for item, count in ROLE_GEAR[role]:
        gear += ['- Item:', f'    Item: {item}', f'    Count: {count}']
    out[start + 1:start + 1] = gear
    assert dropped, (role, 'no weapon found to replace')
    return NL.join(out + lines[i:]), dropped
