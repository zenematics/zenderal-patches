"""Generate Zenderal - Flame Shot.esp's Spriggit YAML from the winning source records.

The Rogue talent "Fire Arrow" (Shout _00E_A1_Firearrow 05C233) adds a few fire arrows and force-equips
them. With a musket or crossbow in hand that leaves an unshootable arrow equipped, and SureAI's
_00E_A1_FireArrowSC only restores the old ammo if it is in _00E_A1_FirearrowAmmoFormlist (arrows only),
so the musket ended up with no ammo at all. This patch:

  * adds a Flame Musket Ball (copy of Ordo's Musket Balls) whose projectile (copy of Ordo's ball
    projectile) explodes with the fire arrow's own explosion 066891 - so the fire damage and the
    Swashbuckler (Wayfarer) bonus blast, both carried by that explosion's enchantment, come with it;
  * gives the talent's magic effect 05BD36 a new script property pointing at that ammo (the recompiled
    _00E_A1_FireArrowSC hands it out instead of arrows while a crossbow-type weapon is equipped);
  * forwards EGO's ammo FormList 13E955 plus every bolt-type ammo in the list, so the old ammo comes back;
  * renames the power to "Flame Shot" everywhere the player sees it.

Every override is copied from the plugin that wins it in the live load order (scanned 2026-10-16):
EGO wins 05C233, 05C24D, 069D6E, 14334A, 13E955; base Enderal wins 05BD36, 069CD3, 0BFA3E, 0BFA3D, 0671F7.

Run from the repo root: python -I src/FlameShot/tools/01-build-flame-shot.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
REF = os.path.join(ROOT, 'reference')
OUT = os.path.join(ROOT, 'src', 'FlameShot', 'FlameShotESP')
MOD = 'Zenderal - Flame Shot.esp'

BALL_AMMO = '000801:' + MOD
BALL_PROJ = '000800:' + MOD

# Bolt-type ammo (no NonBolt flag, playable) in the list, appended to the "restore old ammo" FormList.
BOLTS = [
    '002C78:Enderal SE - Gameplay Overhaul.esp',   # XionSteelBolt
    '002C79:Enderal SE - Gameplay Overhaul.esp',   # XionDwarvenBolt
    '002C7A:Enderal SE - Gameplay Overhaul.esp',   # XionSilverBolt
    '000805:Enderal SE - Crossbows.esp',           # XionSteelBolt
    '000806:Enderal SE - Crossbows.esp',           # XionDwarvenBolt
    '002F9D:OrdoLegionisMuskets.esp',              # Musket Balls
    '00F5E1:OrdoLegionisMuskets.esp',              # Minie Balls
    '00F5BE:OrdoLegionisMuskets.esp',              # Blunderbuss Scrapnel
]

DESC_LEAD_OLD = 'Grants you a handful of fire arrows, which explode upon impact and do fire damage.'
DESC_LEAD_NEW = ('Grants you a handful of fire arrows - or flame musket balls while a musket or crossbow '
                 'is equipped - which explode upon impact and do fire damage.')


def find(tree, fk):
    hexid, mod = fk.split(':', 1)
    for dp, _, files in os.walk(os.path.join(REF, tree)):
        for f in files:
            if f.endswith(' - %s_%s.yaml' % (hexid, mod)):
                return os.path.join(dp, f)
    raise SystemExit('not found: %s in %s' % (fk, tree))


def read(path):
    return open(path, encoding='utf-8').read().replace('\r\n', '\n')


def block_span(text, key):
    """Span of a top-level YAML key and its indented body."""
    m = re.search(r'(?m)^%s:.*\n(?:(?:[ \-].*)?\n)*?(?=^[A-Za-z]|\Z)' % re.escape(key), text)
    if not m:
        raise SystemExit('no top-level key %s' % key)
    return m.span()


def set_string(text, key, value):
    """Replace a translated field (localized or not) with a single English value."""
    s, e = block_span(text, key)
    if '\n' in value:
        lines = value.split('\n')
        new = '%s:\n  TargetLanguage: English\n  Value: >-\n' % key + ''.join(
            ('    ' + l if l else '') + '\n' for l in lines)
    else:
        new = "%s:\n  TargetLanguage: English\n  Value: '%s'\n" % (key, value.replace("'", "''"))
    return text[:s] + new + text[e:]


def get_english(text, key):
    """The English text of a translated field, as a plain string."""
    s, e = block_span(text, key)
    body = text[s:e]
    m = re.search(r'(?m)^  Value: ', body)
    if m:
        val = body[m.end():]
        indent = '    '
    else:
        m = re.search(r'(?m)^  - Language: English\n    String: ', body)
        if not m:
            raise SystemExit('no English %s' % key)
        val = body[m.end():]
        val = re.split(r'(?m)^  - Language', val)[0]
        indent = '      '
    first, _, rest = val.partition('\n')
    first = first.strip()
    if first in ('>-', '>+', '|-', '|', '>'):
        out = []
        for l in rest.split('\n'):
            out.append(l[len(indent):] if l.startswith(indent) else l.strip())
        while out and not out[-1]:
            out.pop()
        return '\n'.join(out)
    if first.startswith("'") and first.endswith("'"):
        return first[1:-1].replace("''", "'")
    return first


def replace_once(text, old, new):
    n = text.count(old)
    if n != 1:
        raise SystemExit('expected 1 occurrence of %r, found %d' % (old, n))
    return text.replace(old, new)


def write(folder, edid, fk, text):
    hexid, mod = fk.split(':', 1)
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, '%s - %s_%s.yaml' % (edid, hexid, mod))
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text if text.endswith('\n') else text + '\n')
    return path


def edid_of(text):
    return re.search(r'(?m)^EditorID: (.*)$', text).group(1).strip()


def main():
    written = []

    # --- New: projectile (Ordo's OLM_proj_ball, exploding with the fire arrow explosion) ---
    t = read(find('mods/OrdoEnderal', '002F9E:OrdoLegionisMuskets.esp'))
    t = replace_once(t, 'FormKey: 002F9E:OrdoLegionisMuskets.esp', 'FormKey: ' + BALL_PROJ)
    t = replace_once(t, 'EditorID: OLM_proj_ball\n', 'EditorID: ZP_FlameShot_MusketBallProj\n')
    t = replace_once(t, '  Value: Musket Ball\n', '  Value: Flame Musket Ball\n')
    t = replace_once(t, '- CanBePickedUp\n', '')
    t = replace_once(t, 'Explosion: 007ED3:OrdoLegionisMuskets.esp', 'Explosion: 066891:Skyrim.esm')
    written.append(write('Projectiles', 'ZP_FlameShot_MusketBallProj', BALL_PROJ, t))

    # --- New: ammo (Ordo's Musket Balls) ---
    t = read(find('mods/OrdoEnderal', '002F9D:OrdoLegionisMuskets.esp'))
    t = replace_once(t, 'FormKey: 002F9D:OrdoLegionisMuskets.esp', 'FormKey: ' + BALL_AMMO)
    t = replace_once(t, 'EditorID: OLMusket_ammo_lead\n', 'EditorID: ZP_FlameShot_MusketBall\n')
    t = replace_once(t, '  Value: Musket Balls\n', '  Value: Flame Musket Ball\n')
    t = replace_once(t, '  Value: Black powder charge and iron ball\n',
                     '  Value: Black powder charge and an iron ball wrapped in burning pitch\n')
    t = replace_once(t, 'Projectile: 002F9E:OrdoLegionisMuskets.esp', 'Projectile: ' + BALL_PROJ)
    t = replace_once(t, 'Value: 2\n', 'Value: 0\n')
    # Ordo points these at Dawnguard.esm, an empty stub in Enderal; use the fire arrow's own sounds.
    t = replace_once(t, 'PickUpSound: 00D219:Dawnguard.esm', 'PickUpSound: 03E7B7:Skyrim.esm')
    t = replace_once(t, 'PutDownSound: 00D21A:Dawnguard.esm', 'PutDownSound: 03E877:Skyrim.esm')
    written.append(write('Ammunitions', 'ZP_FlameShot_MusketBall', BALL_AMMO, t))

    # --- Magic effect 05BD36 (base): rename + the new script property ---
    t = read(find('base/Skyrim', '05BD36:Skyrim.esm'))
    t = set_string(t, 'Name', 'Flame Shot')
    t = replace_once(t, '      Name: PlayerRef\n      Object: 000014:Skyrim.esm\n',
                     '      Name: PlayerRef\n      Object: 000014:Skyrim.esm\n'
                     '    - MutagenObjectType: ScriptObjectProperty\n'
                     '      Name: ZP_FlameShotMusketBall\n'
                     '      Object: %s\n' % BALL_AMMO)
    written.append(write('MagicEffects', edid_of(t), '05BD36:Skyrim.esm', t))

    # --- Shout 05C233 + spell 05C24D (EGO): rename ---
    t = read(find('mods/EGO', '05C233:Skyrim.esm'))
    t = set_string(t, 'Name', 'Flame Shot')
    t = set_string(t, 'Description', 'Creates fire arrows in your quiver - or flame musket balls in your '
                   'pouch while a musket or crossbow is equipped - which can set your target on fire.')
    written.append(write('Shouts', edid_of(t), '05C233:Skyrim.esm', t))

    t = read(find('mods/EGO', '05C24D:Skyrim.esm'))
    t = set_string(t, 'Name', 'Flame Shot')
    written.append(write('Spells', edid_of(t), '05C24D:Skyrim.esm', t))

    # --- Talent perks (base) + Hero Menu activator (base) + talent message (EGO) ---
    for fk in ('069CD3:Skyrim.esm', '0BFA3E:Skyrim.esm', '0BFA3D:Skyrim.esm'):
        t = read(find('base/Skyrim', fk))
        desc = get_english(t, 'Description')
        desc = replace_once(desc, DESC_LEAD_OLD, DESC_LEAD_NEW)
        t = set_string(t, 'Name', 'Talent: Flame Shot')
        t = set_string(t, 'Description', desc)
        written.append(write('Perks', edid_of(t), fk, t))

    t = read(find('base/Skyrim', '0671F7:Skyrim.esm'))
    t = set_string(t, 'Name', 'Talent: Flame Shot')
    written.append(write('Activators', edid_of(t), '0671F7:Skyrim.esm', t))

    t = read(find('mods/EGO', '069D6E:Skyrim.esm'))
    desc = replace_once(get_english(t, 'Description'), DESC_LEAD_OLD, DESC_LEAD_NEW)
    t = set_string(t, 'Description', desc)
    t = set_string(t, 'Name', 'Talent: Flame Shot')   # EGO ships it untranslated: 'Talent: Feuerpfeil'
    written.append(write('Messages', edid_of(t), '069D6E:Skyrim.esm', t))

    # --- Swashbuckler ability description (EGO) ---
    t = read(find('mods/EGO', '14334A:Skyrim.esm'))
    desc = replace_once(get_english(t, 'Description'), 'Each fired fire arrow also triggers',
                        'Each fired fire arrow or flame musket ball also triggers')
    t = set_string(t, 'Description', desc)
    written.append(write('Spells', edid_of(t), '14334A:Skyrim.esm', t))

    # --- Ammo FormList 13E955 (EGO) + bolts ---
    t = read(find('mods/EGO', '13E955:Skyrim.esm'))
    for b in BOLTS:
        if '- %s\n' % b in t:
            raise SystemExit('already listed: ' + b)
    t = t.rstrip('\n') + '\n' + ''.join('- %s\n' % b for b in BOLTS)
    written.append(write('FormLists', edid_of(t), '13E955:Skyrim.esm', t))

    for p in written:
        print(os.path.relpath(p, ROOT))
    print(len(written), 'records')


if __name__ == '__main__':
    sys.exit(main())
