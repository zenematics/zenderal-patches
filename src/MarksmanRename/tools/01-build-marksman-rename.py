"""Builds Zenderal - Marksman Rename.esp's YAML from 00-find-archery.py's report: each winning record with a shown
"Archery" that names the skill, copied from its winner with the English text changed to "Marksman". Only English
display strings change (a localized base record keeps every other language as it was). Generated - rerun after a
winner changes. usage: 01-build-marksman-rename.py <serializedRoot> <archery.json>"""
import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
SER, REPORT = sys.argv[1], sys.argv[2]
REPO = r'E:\zenderal-patches'
OUT = os.path.join(REPO, 'src', 'MarksmanRename', 'MarksmanRenameESP')
MOD = 'Zenderal - Marksman Rename.esp'
ROOT = r'E:\Zenderal'
plugins = [l[1:].strip() for l in open(ROOT + r'\profiles\Ultra\plugins.txt', encoding='utf-8') if l.startswith('*')]
order = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'] + plugins
lower = {p.lower(): p for p in order}

# Not the skill, or owned elsewhere: our own plugins fix their text in their own generators (one owner per record:
# Flame Shot owns the Wayfarer affinity 14334A, Prophecy its stat talents), and the placeable "Archery Target" names
# the object, not the skill
SKIP_WINNERS = ('Zenderal - ',)
SKIP_RECORDS = {'141014:Skyrim.esm'}   # _00E_Placeable_Static_ArcheryTarget
HIT = re.compile(r'(?<!Arcane )\bArchery\b')

hits = [h for h in json.load(open(REPORT, encoding='utf-8'))
        if not h['winner'].startswith(SKIP_WINNERS) and h['formKey'] not in SKIP_RECORDS]

for d in os.listdir(OUT) if os.path.isdir(OUT) else []:
    if os.path.isdir(os.path.join(OUT, d)):
        shutil.rmtree(os.path.join(OUT, d))
os.makedirs(OUT, exist_ok=True)


def rename(t, what):
    """English display strings only: a 'Value:' line (TargetLanguage English) or the String under '- Language: English'"""
    out, lang, n = [], None, 0
    for line in t.split('\n'):
        s = line.strip()
        m = re.match(r'- Language: (\w+)$', s)
        if m:
            lang = m.group(1)
        else:
            if HIT.search(s) and (s.startswith('Value: ') or (s.startswith('String: ') and lang == 'English')):
                line, k = HIT.subn('Marksman', line)
                n += k
            lang = None   # a String belongs to the '- Language:' line right above it
        out.append(line)
    assert n > 0, f'{what}: nothing renamed'
    return '\n'.join(out), n


FK = re.compile(r'\b([0-9A-F]{6}):([^\r\n,\]\'"]+?\.(?:esm|esp|esl))\b')
masters = set()
total = 0
for h in hits:
    t = open(h['path'], encoding='utf-8').read().replace('\r\n', '\n')
    t, n = rename(t, h['formKey'])
    total += n
    for m in FK.finditer(t):
        masters.add(lower[m.group(2).lower()] if m.group(2).lower() in lower else m.group(2))
        if int(m.group(1), 16) < 0x800 and m.group(2) not in ('Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'):
            print(f'  ! {h["formKey"]} names {m.group(0)} (object ID < 0x800 outside the base masters)')
    os.makedirs(os.path.join(OUT, h['type']), exist_ok=True)
    open(os.path.join(OUT, h['type'], os.path.basename(h['path'])), 'w', encoding='utf-8', newline='\r\n').write(t)
    eng = [l.strip() for l in t.split('\n') if HIT.sub('', l) != l]
    print(f'{h["formKey"]:42} {h["editorId"][:38]:38} {n} renamed')
missing = [m for m in masters if m not in order]
assert not missing, f'masters not in the load order: {missing}'
ms = sorted(masters | {'Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'}, key=order.index)
rd = f"""ModKey: {MOD}
GameRelease: EnderalSE
ModHeader:
  Flags:
  - Small
  Stats:
    Version: 1.7
  Author: Zenderal
  Description: >-
    The skill is called Marksman in Enderal's own interface: every shown "Archery" naming it (learning books,
    Fortify effects and enchantments, potions, affinities, the level-up message) reads Marksman.
  MasterReferences:
""" + ''.join(f'  - Master: {m}\n    FileSize: 0\n' for m in ms) + '  INTV: 1\n'
open(os.path.join(OUT, 'RecordData.yaml'), 'w', encoding='utf-8', newline='\r\n').write(rd)
json.dump({'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.40.0', 'Release': 'EnderalSE', 'ModKey': MOD},
          open(os.path.join(OUT, 'spriggit-meta.json'), 'w', encoding='utf-8'), indent=2)
print(f'{len(hits)} records, {total} strings renamed, masters: {ms}')
