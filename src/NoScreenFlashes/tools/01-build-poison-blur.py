"""Generate the poison-blur overrides of `Zenderal - No Screen Flashes` -- never hand-edit
NoScreenFlashesESP/MagicEffects/ (the Explosions/ override is hand-copied and stays untouched).

Curator's taste (2026-10-22): no screen blur from poisons. Every poison blur in the list is the same
mechanism: a magic effect runs `MagicImodOnPlayerHitScript` (Enderal's source: on the PLAYER, apply
OnStartImodFX, wait 5 s, apply OnFinishImodFX at the end; nothing else) with `PoisonHitImod 10E3D2` /
`PoisonEndImod 10E3D3`. This takes every WINNING magic effect whose copy of that script points at either
of those two and overrides it verbatim minus that one script entry (and the VirtualMachineAdapter block
when it was the only script). The poison's damage, duration, hit shader and everything else stay.

Users of the script with OTHER image-space modifiers (Apocalypse's Empathy/Nightmare illusions) are not
poisons and are left alone. `Zenderal - Goblins` already ships its own blur-free Arp poison.

Sources, in load order (a later one wins): reference/base/Skyrim, reference/base/EnderalFS, then
<all>/<plugin> for every enabled Ultra plugin (src/UnresolvedRefsCleanup/tools/00a-serialize-all.py).
Asserts that no plugin loading AFTER this one overrides a picked effect, and that no copied record refers
to a sub-0x800 object of a non-base plugin (that would need HEDR 1.71; CLAUDE.md). Masters are computed.
Rerun after any mod that adds or overrides a poison effect changes.

Usage:  python 01-build-poison-blur.py <all dir>
"""
import glob
import json
import os
import re
import shutil
import sys

ALL = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ESP = os.path.join(HERE, '..', 'NoScreenFlashesESP')
MOD_KEY = 'Zenderal - No Screen Flashes.esp'
PLUGINS = os.path.join('E:/Zenderal', 'profiles', 'Ultra', 'plugins.txt')
NL = '\r\n'
SCRIPT = 'MagicImodOnPlayerHitScript'
POISON_IMODS = {'10E3D2:Skyrim.esm': 'PoisonHitImod', '10E3D3:Skyrim.esm': 'PoisonEndImod'}
BASE_MASTERS = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm']
FK = re.compile(r'(?<![0-9A-F])([0-9A-F]{6}):([^\r\n,\]]+?\.(?:esm|esp|esl))')


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\n', NL)


def sources(order):
    out = [('Skyrim.esm', os.path.join(REPO, 'reference', 'base', 'Skyrim')),
           ('Enderal - Forgotten Stories.esm', os.path.join(REPO, 'reference', 'base', 'EnderalFS'))]
    for p in order:
        d = os.path.join(ALL, re.sub(r'[^A-Za-z0-9]', '', p))
        if os.path.isdir(d):
            out.append((p, d))
    return out


def strip_script(text, edid):
    """The record minus the SCRIPT entry of its VirtualMachineAdapter (the whole block if it was alone)."""
    lines = text.split(NL)
    vs = lines.index('VirtualMachineAdapter:')
    ve = vs + 1
    while ve < len(lines) and (lines[ve].startswith(' ') or lines[ve].startswith('- ')):
        ve += 1
    block = lines[vs:ve]
    items, cur = [], None
    for k, ln in enumerate(block):
        if ln.startswith('  - Name: '):
            cur = [k]
            items.append(cur)
        elif cur is not None and ln.startswith('    '):
            cur.append(k)
        elif cur is not None:
            cur = None
    picked = [it for it in items if block[it[0]] == f'  - Name: {SCRIPT}']
    assert len(picked) == 1, (edid, 'script entries', len(picked))
    if len(items) == 1:
        assert block[1] == '  Scripts:' and all(k in picked[0] for k in range(2, len(block))), (edid, block)
        new = []
    else:
        new = [ln for k, ln in enumerate(block) if k not in picked[0]]
    return NL.join(lines[:vs] + new + lines[ve:])


def main():
    order = [ln[1:].strip() for ln in open(PLUGINS, encoding='utf-8') if ln.startswith('*')]
    pos = order.index(MOD_KEY)
    before = sources(order[:pos])
    after = sources(order[pos + 1:])[2:]                 # base sources load before anyway

    win = {}
    for plugin, root in before:
        for f in glob.glob(os.path.join(root, 'MagicEffects', '*.yaml')):
            t = read(f)
            win[re.search(r'^FormKey: (.+?)\s*$', t, re.M).group(1)] = (plugin, os.path.basename(f), t)
    later = set()
    for plugin, root in after:
        for f in glob.glob(os.path.join(root, 'MagicEffects', '*.yaml')):
            later.add(re.search(r'^FormKey: (.+?)\s*$', read(f), re.M).group(1))

    out_dir = os.path.join(ESP, 'MagicEffects')
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    picked = []
    for fk, (plugin, name, t) in sorted(win.items()):
        if SCRIPT not in t:
            continue
        m = re.search(r'  - Name: ' + SCRIPT + r'\r\n((?:    .*\r\n)*)', t)
        props = set(re.findall(r'Object: (.+?)\r\n', m.group(1))) if m else set()
        if not props & set(POISON_IMODS):
            continue
        assert fk not in later, f'{fk} is overridden after {MOD_KEY}; move this plugin later'
        edid = re.search(r'^EditorID: (\S+)', t, re.M).group(1)
        new = strip_script(t, edid)
        assert SCRIPT not in new and not set(POISON_IMODS) & set(f'{a}:{b}' for a, b in FK.findall(new)), edid
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8', newline='') as fh:
            fh.write(new)
        resist = (re.search(r'^ResistValue: (\S+)', t, re.M) or [None, '-'])[1]
        picked.append((edid, fk, plugin, resist, sorted(POISON_IMODS[p] for p in props & set(POISON_IMODS))))

    # masters + the 1.71 light-plugin rule
    used = set()
    for dp, _, files in os.walk(os.path.normpath(ESP)):
        for f in files:
            if f.endswith('.yaml') and f != 'RecordData.yaml':
                used |= {(a, b) for a, b in FK.findall(read(os.path.join(dp, f)))}
    low = sorted(f'{a}:{b}' for a, b in used if b not in BASE_MASTERS and int(a, 16) < 0x800 and b != MOD_KEY)
    assert not low, f'sub-0x800 forms of non-base plugins need HEDR 1.71: {low}'
    masters = BASE_MASTERS + sorted({b for _, b in used} - set(BASE_MASTERS) - {MOD_KEY}, key=order.index)
    head = read(os.path.join(ESP, 'RecordData.yaml'))
    head = re.sub(r'  MasterReferences:\r\n(?:  - Master: .*\r\n    FileSize: \d+\r\n)+',
                  lambda _: '  MasterReferences:' + NL + ''.join(f'  - Master: {m}{NL}    FileSize: 0{NL}' for m in masters),
                  head, count=1)
    head = re.sub(r'  Description: >-\r\n(?:    .*\r\n)+',
                  lambda _: '  Description: >-' + NL + '    Removes full-screen image-space effects: the Wood Elemental '
                  '(spriggan) call-creatures' + NL + '    blast, and the poison blur (PoisonHitImod/PoisonEndImod) '
                  'from every poison effect.' + NL, head, count=1)
    with open(os.path.join(ESP, 'RecordData.yaml'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(head)

    for edid, fk, plugin, resist, imods in picked:
        print(f'  {edid:52} {fk:48} <- {plugin:36} {resist:14} {"+".join(imods)}')
    print(f'{len(picked)} poison effects without their blur; masters: {", ".join(masters)}')
    with open(os.path.join(HERE, 'poison-blur.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump([dict(editor_id=e, form_key=k, winner=p) for e, k, p, _, _ in picked], fh, indent=1)
        fh.write('\n')


if __name__ == '__main__':
    main()
