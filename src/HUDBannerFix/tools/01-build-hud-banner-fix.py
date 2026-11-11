"""Build MO2 mod `Zenderal - HUD Banner Fix`: Vel'dun UI's hudmenu.swf whose shout/quest banner always clears.

Player report (iDeeSign, 2026-11-11): a small dark sliver stays on screen right of centre after a Prophecy shout
talent is learned and a menu is opened right away; loading a save does not clear it, relaunching does. The HUD is
Vel'dun UI's (the winning copy is Zenderal - Aspect Layout's static `Interface/hudmenu.swf`, from the Vel'dun Zenderal
patches). Its `QuestNotification` class shows a shout as a text revealed by a sliding mask (`ShowShoutText`, mask _x
-width -> 0 over 1 s) and hides it by sliding the mask on (`HideShoutText`, 0 -> width over 0.5 s, 2 s after the
show), and a quest/talent name as a strip whose mask and background widths are tweened (`ShowQuestText`/
`HideQuestText`/`KillQuestText`). Nothing re-checks the end state, so a hide tween cut short leaves the last letter's
edge (or a sliver of strip) for the rest of the session, and the HUD movie lives until the game exits.

The fix adds a watchdog to that class, nothing else: every 0.5 s, once a banner is 2 s past the moment it should have
finished hiding, the shout text is cleared and its mask moved off, and the strip is made invisible. A banner that
hides normally is never touched. Same element names, same timings, same tweens.

Steps: decompile `QuestNotification` with FFDec, apply the edits below (each asserted to match once), recompile it
into a copy of the SWF with FFDec's AS2 compiler, then decompile the result and check that every other script is
byte-identical in P-code and that the class has the watchdog.

The SWF is Vel'dun's work, so it is generated from the user's own install, never committed.
Usage: python 01-build-hud-banner-fix.py   (paths from .claude/config/tools.json: ffdec, modlistRoot or default)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
FFDEC = TOOLS.get('ffdec') or sys.exit('tools.json has no "ffdec" (path to ffdec.jar)')
MODS = 'E:/Zenderal/mods'
SRC = os.path.join(MODS, 'Zenderal - Aspect Layout', 'Interface', 'hudmenu.swf')
SRC_MD5 = '222ae750462876d0d67c726080c90010'  # Vel'dun Zenderal patches d2026.10.27.0 (all three layouts identical)
OUT_MOD = os.path.join(MODS, 'Zenderal - HUD Banner Fix')
OUT = os.path.join(OUT_MOD, 'Interface', 'hudmenu.swf')
CLASS = 'QuestNotification'

EDITS = [
    # 1. watchdog state
    ('   static var ShoutTextWaitIndex;\n',
     '   static var ShoutTextWaitIndex;\n'
     '   static var ZenStripDeadline = 0;\n'
     '   static var ZenShoutDeadline = 0;\n'
     '   static var ZenWatchIndex = 0;\n'),
    # 2. start it with the HUD
    ('      ShoutTextWaitIndex = 0;\n      this.PositionElements();\n',
     '      ShoutTextWaitIndex = 0;\n      this.PositionElements();\n'
     '      clearInterval(ZenWatchIndex);\n'
     '      ZenWatchIndex = setInterval(QuestNotification.ZenWatch,500);\n'),
    # 3. the strip: shown 0.5 s, held 3 s, hidden over 0.5 s -> deadline 2 s after that
    ('      AnimStripWaitIndex = setInterval(this,"HideQuestText",_loc4_ * 1000 + 3000);\n',
     '      AnimStripWaitIndex = setInterval(this,"HideQuestText",_loc4_ * 1000 + 3000);\n'
     '      ZenStripDeadline = getTimer() + _loc4_ * 1000 + 3000 + 500 + 2000;\n'),
    # 4. the shout text: shown 1 s, held to 3 s, hidden over 0.5 s -> deadline 2 s after that
    ('      ShoutTextWaitIndex = setInterval(this,"HideShoutText",_loc4_ * 1000 + 2000);\n',
     '      ShoutTextWaitIndex = setInterval(this,"HideShoutText",_loc4_ * 1000 + 2000);\n'
     '      ZenShoutDeadline = getTimer() + _loc4_ * 1000 + 2000 + 500 + 2000;\n'),
    # 5. the watchdog itself
    ('   static function RestartAnimations()\n   {\n   }\n',
     '   static function RestartAnimations()\n   {\n   }\n'
     '   static function ZenWatch()\n'
     '   {\n'
     '      var _loc2_ = Instance;\n'
     '      var _loc3_ = getTimer();\n'
     '      if(ZenShoutDeadline > 0 && _loc3_ > ZenShoutDeadline)\n'
     '      {\n'
     '         ZenShoutDeadline = 0;\n'
     '         _loc2_.ShoutTextInstance.ShoutText.textField.text = "";\n'
     '         _loc2_.ShoutTextInstance.ShoutText.textFieldGlow.text = "";\n'
     '         _loc2_.ShoutTextInstance.ShoutText.Mask._x = _loc2_.ShoutTextInstance.ShoutText.textField._width + _loc2_.ShoutTextInstance.ShoutText.Mask._width;\n'
     '      }\n'
     '      if(ZenStripDeadline > 0 && _loc3_ > ZenStripDeadline)\n'
     '      {\n'
     '         ZenStripDeadline = 0;\n'
     '         _loc2_.AnimStrip._visible = false;\n'
     '      }\n'
     '   }\n'),
]


def ffdec(*args):
    r = subprocess.run(['java', '-jar', FFDEC, *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'ffdec {args[0]} failed:\n{r.stdout}\n{r.stderr}')
    return r.stdout


def export(swf, out, fmt):
    ffdec('-format', f'script:{fmt}', '-export', 'script', out, swf)
    return os.path.join(out, 'scripts')


def tree(root):
    files = {}
    for d, _, names in os.walk(root):
        for n in names:
            p = os.path.join(d, n)
            files[os.path.relpath(p, root)] = open(p, 'rb').read()
    return files


md5 = hashlib.md5(open(SRC, 'rb').read()).hexdigest()
if md5 != SRC_MD5:
    sys.exit(f'{SRC}: md5 {md5}, expected {SRC_MD5}. Vel\'dun changed: re-read QuestNotification and update the edits.')

tmp = tempfile.mkdtemp(prefix='zen_hudfix_')
try:
    src_as = export(SRC, os.path.join(tmp, 'as'), 'as')
    cls = os.path.join(src_as, '__Packages', CLASS + '.as')
    text = open(cls, encoding='utf-8').read().replace('\r\n', '\n')
    for old, new in EDITS:
        n = text.count(old)
        if n != 1:
            sys.exit(f'edit not applied: expected 1 match, found {n}:\n{old}')
        text = text.replace(old, new)
    edited = os.path.join(tmp, CLASS + '.as')
    open(edited, 'w', encoding='utf-8', newline='\n').write(text)

    patched = os.path.join(tmp, 'hudmenu.swf')
    bs = chr(92)  # FFDec names AS2 classes \__Packages\<Class> (see -dumpAS2)
    ffdec('-replace', SRC, patched, bs + '__Packages' + bs + CLASS, edited)

    # verify: the class decompiles with the watchdog; every other script's P-code is unchanged
    new_as = tree(export(patched, os.path.join(tmp, 'as2'), 'as'))
    got = new_as[os.path.join('__Packages', CLASS + '.as')].decode('utf-8')
    for marker in ('function ZenWatch()', 'ZenWatchIndex = setInterval', 'ZenStripDeadline = getTimer()',
                   'ZenShoutDeadline = getTimer()', 'AnimStrip._visible = false'):
        if marker not in got:
            sys.exit(f'patched class lacks "{marker}"')
    old_p = tree(export(SRC, os.path.join(tmp, 'p1'), 'pcode'))
    new_p = tree(export(patched, os.path.join(tmp, 'p2'), 'pcode'))
    if set(old_p) != set(new_p):
        sys.exit(f'script set changed: {sorted(set(old_p) ^ set(new_p))}')
    changed = sorted(k for k in old_p if old_p[k] != new_p[k])
    if changed != [os.path.join('__Packages', CLASS + '.pcode')]:
        sys.exit(f'unexpected P-code changes: {changed}')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    shutil.copyfile(patched, OUT)
    print(f'{OUT}: written ({os.path.getsize(OUT)} bytes); only {CLASS} changed, {len(old_p)} scripts checked')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
