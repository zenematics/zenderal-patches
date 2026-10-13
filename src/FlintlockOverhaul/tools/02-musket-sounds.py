"""Zenderal - Flintlock Overhaul: Ordo Legionis musket fire sounds, as the mod authored them, playable in
Enderal. GENERATED - never hand-edit SoundDescriptors/; re-run this instead.

History: on 2026-10-12 these four SNDRs were briefly replaced with the flintlock pistol's gun1.wav at the
curator's request; the same day the curator asked for Ordo's own sounds back. What remains is a bug fix:
two of Ordo's four fire SNDRs (OLM_WPNBiggunFire 0197F7 - the double-barrel rifles and the Heavy Wheellock
Arquebus - and OLM_WPNBlunderbussFire 00F5B8 - the blunderbuss and both musketoons) route through
OutputModel 01686B:Dawnguard.esm, which in Enderal is an empty stub, so that reference resolves to nothing.
Each override is Ordo's (Enderal add-on) record verbatim with only OutputModel set to 10E425:Skyrim.esm,
the model Ordo's other two musket fire sounds already use. The two that are fine are not overridden.

Run from the repo root: python -I src/FlintlockOverhaul/tools/02-musket-sounds.py
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ORDO = os.path.join(ROOT, 'reference', 'mods', 'OrdoEnderal', 'SoundDescriptors')
OUT = os.path.join(ROOT, 'src', 'FlintlockOverhaul', 'FlintlockOverhaulESP', 'SoundDescriptors')
STUB = 'OutputModel: 01686B:Dawnguard.esm'
GOOD = 'OutputModel: 10E425:Skyrim.esm'

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
fixed = []
for f in sorted(os.listdir(ORDO)):
    with open(os.path.join(ORDO, f), encoding='utf-8') as fh:
        t = fh.read().replace('\r\n', '\n')
    if STUB not in t:
        continue
    if t.count(STUB) != 1:
        sys.exit('%s: unexpected OutputModel shape' % f)
    with open(os.path.join(OUT, f), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t.replace(STUB, GOOD))
    fixed.append(re.search(r'EditorID: (\S+)', t).group(1))
if sorted(fixed) != ['OLM_WPNBiggunFire', 'OLM_WPNBlunderbussFire']:
    sys.exit('expected exactly the big-gun and blunderbuss fire sounds, got %r' % fixed)
print('OutputModel fixed on:', ', '.join(fixed))
