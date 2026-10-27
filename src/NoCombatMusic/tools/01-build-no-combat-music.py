"""Zenderal - No Combat Music: battles no longer start music; the area's exploration music keeps playing.

Enderal 2.1 plays generic battle music through the engine: Default Object `BTMS` (Battle Music) =
`_00E_Music_Combat_Regular 0773F1` (Enderal 2.0 left BTMS empty and started it from
`_00E_CombatSoundtrackScript` on NPCs, which 2.1 no longer ships). The override is SureAI's 2.1 record
with three fields changed:
  - Tracks -> only `_00E_SilentTrack 0963BB` (SureAI's own silence pattern: `_NONE`,
    `_00E_SilenceTransitionLowPriority02`);
  - Priority 65 -> 100, below every exploration/dungeon type (84-95; lower number wins), so pushing
    it onto the music stack no longer takes over from the area's music;
  - AbruptTransition / DucksCurrentTrack dropped, so it never cuts or ducks the playing track.
Quest/boss music the scripts add themselves (`_00E_Music_Combat_*_NoCond`, MQP02, arena...) is
separate MUSC records and untouched.

Usage (from the repo root): python -I src/NoCombatMusic/tools/01-build-no-combat-music.py
Reads reference/base-2.1.4.4/Skyrim (Enderal 2.1.4.4's Skyrim.esm, serialized)."""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "reference", "base-2.1.4.4", "Skyrim", "MusicTypes",
                   "_00E_Music_Combat_Regular - 0773F1_Skyrim.esm.yaml")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NoCombatMusicESP", "MusicTypes")

raw = open(SRC, "rb").read()
nl = b"\r\n" if b"\r\n" in raw else b"\n"
lines = raw.split(nl)


def drop(line):
    assert lines.count(line) == 1, line
    lines.remove(line)


assert lines[0] == b"FormKey: 0773F1:Skyrim.esm", lines[0]
drop(b"- AbruptTransition")
drop(b"- DucksCurrentTrack")
i = lines.index(b"  Priority: 65")
lines[i] = b"  Priority: 100"
t = lines.index(b"Tracks:")
old = [l for l in lines[t + 1:] if l.startswith(b"- ")]
assert len(old) == 10, old  # 2.1.4.4's ten battle tracks
lines = lines[:t + 1] + [b"- 0963BB:Skyrim.esm"] + lines[t + 1 + len(old):]

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
open(os.path.join(OUT, os.path.basename(SRC)), "wb").write(nl.join(lines))
print(nl.join(lines).decode())
