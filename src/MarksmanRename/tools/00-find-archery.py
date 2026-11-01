"""Every WINNING record in the Ultra load order whose shown text still calls the skill "Archery" (Enderal's own
interface calls it Marksman: translate_english.txt $Archery = Marksman). Read-only.

usage: 00-find-archery.py <serializedRoot> <out.json>
<serializedRoot> = src/UnresolvedRefsCleanup/tools/00a-serialize-all.py's output (every enabled plugin but the base
masters); the base masters come from reference/base/Skyrim and reference/base/EnderalFS.
Winner = the last plugin (plugins.txt order) with a top-level record file for that FormKey. Cells and worldspaces are
skipped (no skill text). A hit is any line naming Archery as a word, except "Arcane Archery" (Prophecy's tree) and
actor-value / EditorID lines (MARKSMAN_ENUM_LINE)."""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
SER, OUTJ = sys.argv[1], sys.argv[2]
REPO = r'E:\zenderal-patches'
ROOT = r'E:\Zenderal'
plugins = [l[1:].strip() for l in open(ROOT + r'\profiles\Ultra\plugins.txt', encoding='utf-8') if l.startswith('*')]
order = ['Skyrim.esm', 'Update.esm', 'Enderal - Forgotten Stories.esm'] + plugins
pos = {re.sub(r'[^A-Za-z0-9]', '', p): k for k, p in enumerate(order)}
dirs = {0: os.path.join(REPO, 'reference', 'base', 'Skyrim'), 2: os.path.join(REPO, 'reference', 'base', 'EnderalFS')}
for d in os.listdir(SER):
    k = pos.get(d)
    if k is not None and os.path.isdir(os.path.join(SER, d)):
        dirs[k] = os.path.join(SER, d)
SKIP = {'Cells', 'Worldspaces', 'DialogTopics'}
ENUM = re.compile(r'^\s*(?:- )?(?:Key|Skill|ActorValue|SecondActorValue|Teaches|MagicSkill|ResistValue|CastingSkill|'
                  r'EditorID|Name|Object|Model|File|Data)\s*:\s*\S*Archery')
HIT = re.compile(r'(?<!Arcane )\bArchery\b')

winner = {}   # FormKey -> (order idx, path, type)
for k in sorted(dirs):
    for ty in os.listdir(dirs[k]):
        full = os.path.join(dirs[k], ty)
        if ty in SKIP or not os.path.isdir(full):
            continue
        for n in os.listdir(full):
            if not n.endswith('.yaml'):
                continue
            m = re.search(r' - ([0-9A-F]{6})_(.+)\.yaml$', n)
            if m:
                winner[f'{m.group(1)}:{m.group(2)}'] = (k, os.path.join(full, n), ty)
hits = []
for fk, (k, p, ty) in winner.items():
    t = open(p, encoding='utf-8').read()
    if 'rchery' not in t:
        continue
    lines = [l.strip() for l in t.replace('\r', '').split('\n') if HIT.search(l) and not ENUM.match(l)]
    # localized base records carry every language: keep English-looking lines only (the German etc. have no "Archery")
    if lines:
        ed = re.search(r'^EditorID: (.+?)\s*$', t, re.M)
        hits.append({'formKey': fk, 'type': ty, 'winner': order[k], 'editorId': ed.group(1) if ed else '', 'path': p,
                     'lines': lines})
hits.sort(key=lambda h: (h['winner'], h['type'], h['editorId']))
json.dump(hits, open(OUTJ, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
by = {}
for h in hits:
    by.setdefault((h['winner'], h['type']), 0)
    by[(h['winner'], h['type'])] += 1
for (w, ty), n in sorted(by.items()):
    print(f'{n:4} {ty:22} {w}')
print(len(hits), 'winning records with shown "Archery"')
