"""Build the Nemesis-format companion (`zpairset`) that lets the engine load Enderal's six FNIS
paired/killmove clips under Pandora.

The 0_master patch (`zpaired`, 01-build-paired-patch.py) only routes the events to the clips. SSE
loads a clip only if it is listed in the actor's active animation set in
animationsetdatasinglefile.txt; a clip that is not listed fails to load and both actors stand
still. Enderal's FNIS build listed each clip in dedicated trigger sets (PlayerFNIS1..6Start /
NPCFNIS1..6Start, Calia also in H2HDual/H2HSolo). Pandora 5.0.0-beta's output has none of them,
and Pandora's patch format cannot create new sets - only add clips to existing ones, and only from
a Nemesis-format mod (Pandora-native mods have no animset hook). So, like Pandora's own bundled
killmove pack `snusnu`, this adds the six clips to EVERY set of DefaultMale and DefaultFemale.

Two forms are written, one per Pandora generation:

- 5.0.0-beta reads `animationsetdatasinglefile/<project>/<set file>` (each line a clip path). The
  per-project root-file form (`<project>.txt`) is avoided: PandoraAssembler.AssembleAnimSetDataPatch
  `break`s after the first project file, so only one project would be patched.
- Preview builds since 2c7dace (2026-10-14) skip that reader. Their NemesisCachePatcher reads only
  Nemesis cache files: `animationsetdatasinglefile/<ProjectData>~<Project>/<set file>`, each a full
  `V3` set with the added lines between `<!-- MOD_CODE ~zpairset~ OPEN -->` and `<!-- CLOSE -->`.
  Such a file REPLACES the whole set, so each one is the template set verbatim plus our six
  (folder hash, name hash, extension) triples. 5.0.0-beta skips these folders (no project is
  named `DefaultMaleData~DefaultMale`), and the preview skips the plain lists (no markers), so one
  package serves both.

Input: Pandora's template animationsetdatasinglefile.txt (set names and set contents).
usage: python 02-build-animset-patch.py <Pandora>/Pandora_Engine/Skyrim/Template/animationsetdatasinglefile.txt <out zpairset dir>
"""
import ntpath
import os
import shutil
import sys

CLIPS = [
    r"meshes\actors\character\animations\enderal\paired_calia_massacre.hkx",
    r"meshes\actors\character\animations\enderal\paired_hugb.hkx",
    r"meshes\actors\character\animations\enderal\paired_kiss_2female.hkx",
    r"meshes\actors\character\animations\enderal\paired_kiss_2male.hkx",
    r"meshes\actors\character\animations\enderal\paired_kiss_male_female.hkx",
    r"meshes\actors\character\animations\enderal\paired_kiss_female_male.hkx",
]
# animset project path -> Pandora project identifier (character project file name)
PROJECTS = {
    "DefaultMaleData\\DefaultMale.txt": "DefaultMale",
    "DefaultFemaleData\\DefaultFemale.txt": "DefaultFemale",
}
INFO_INI = (
    "name=Zenderal - Enderal Paired Animations (anim sets)\r\n"
    "author=Zenderal (scenes: SureAI)\r\n"
    "site=null\r\n"
    "auto=null\r\n"
)


MOD_CODE = "zpairset"
CACHE_OPEN = f"<!-- MOD_CODE ~{MOD_CODE}~ OPEN -->"
CACHE_CLOSE = "<!-- CLOSE -->"
EXTENSION = 7891816                 # the engine's 'hkx' (bytes h, k, x read as a little-endian number)
FOLDER_HASH = 679778984             # what 5.0.0-beta wrote for the clips' folder (verified in game)


def bethesda_crc(text):
    """The engine's path CRC32: reflected 0x04C11DB7, initial value 0, no final XOR."""
    c = 0
    for b in text.lower().encode("ascii"):
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ (0xEDB88320 if c & 1 else 0)
    return c


def anim_info_lines():
    """The six clips as cached anim infos, three lines each, as the set file stores them."""
    folder = bethesda_crc(ntpath.dirname(CLIPS[0]))
    if folder != FOLDER_HASH:
        raise SystemExit(f"folder hash {folder} != {FOLDER_HASH}: CRC or clip path changed")
    out = []
    for clip in CLIPS:
        if bethesda_crc(ntpath.dirname(clip)) != folder:
            raise SystemExit(f"{clip}: not in the same folder as the other clips")
        name = ntpath.splitext(ntpath.basename(clip))[0]
        out += [str(folder), str(bethesda_crc(name)), str(EXTENSION)]
    return out


def read_sets(path):
    """Return {project path: [(set file name, [set lines from 'V3' to its last anim info])]}."""
    lines = [x.rstrip("\r") for x in open(path, encoding="ascii").read().split("\n")]
    i = 0

    def nx():
        nonlocal i
        v = lines[i]
        i += 1
        return v

    n = int(nx())
    projects = [nx() for _ in range(n)]
    out = {}
    for pj in projects:
        names = [nx() for _ in range(int(nx()))]
        sets = []
        for name in names:
            start = i
            if nx() != "V3":
                raise SystemExit(f"unexpected set header in {pj}")
            for _ in range(int(nx())):  # triggers
                nx()
            for _ in range(int(nx()) * 3):  # conditions
                nx()
            for _ in range(int(nx())):  # attack entries
                nx()
                nx()
                for _ in range(int(nx())):
                    nx()
            for _ in range(int(nx()) * 3):  # cached anim infos
                nx()
            sets.append((name, lines[start:i]))
        if pj in PROJECTS:
            out[pj] = sets
    if i < len(lines) and any(x.strip() for x in lines[i:]):
        raise SystemExit("trailing data after last project - parse error")
    return out


def set_names(path):
    """Return {project path: [set file names]} for the projects we patch."""
    lines = [x.rstrip("\r") for x in open(path, encoding="ascii").read().split("\n")]
    i = 0

    def nx():
        nonlocal i
        v = lines[i]
        i += 1
        return v

    n = int(nx())
    projects = [nx() for _ in range(n)]
    out = {}
    for pj in projects:
        names = [nx() for _ in range(int(nx()))]
        for _ in names:
            if nx() != "V3":
                raise SystemExit(f"unexpected set header in {pj}")
            for _ in range(int(nx())):  # triggers
                nx()
            for _ in range(int(nx()) * 3):  # conditions
                nx()
            for _ in range(int(nx())):  # attack entries
                nx()
                nx()
                for _ in range(int(nx())):
                    nx()
            for _ in range(int(nx()) * 3):  # cached anim infos
                nx()
        if pj in PROJECTS:
            out[pj] = names
    if i < len(lines) and any(x.strip() for x in lines[i:]):
        raise SystemExit("trailing data after last project - parse error")
    return out


def main():
    template, out_dir = sys.argv[1], sys.argv[2]
    sets = set_names(template)
    if set(sets) != set(PROJECTS):
        raise SystemExit(f"projects missing from template: {set(PROJECTS) - set(sets)}")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    body = "\r\n".join(CLIPS) + "\r\n"
    written = 0
    for pj, names in sets.items():
        if len(names) < 100:
            raise SystemExit(f"{pj}: only {len(names)} sets - template looks wrong")
        d = os.path.join(out_dir, "animationsetdatasinglefile", PROJECTS[pj])
        os.makedirs(d)
        for name in names:
            with open(os.path.join(d, name), "w", encoding="ascii", newline="") as f:
                f.write(body)
            written += 1
    with open(os.path.join(out_dir, "info.ini"), "w", encoding="ascii", newline="") as f:
        f.write(INFO_INI)
    expected = sum(len(v) for v in sets.values())
    if written != expected:
        raise SystemExit(f"wrote {written} set files, expected {expected}")
    print(f"wrote {written} set files ({', '.join(f'{PROJECTS[k]}: {len(v)}' for k, v in sets.items())})")

    # the preview builds' Nemesis cache form: each set in full, our six infos in a marked block
    infos = anim_info_lines()
    full = read_sets(template)
    cached = 0
    for pj, entries in full.items():
        if [n for n, _ in entries] != sets[pj]:
            raise SystemExit(f"{pj}: the two template readers disagree on the set list")
        d = os.path.join(out_dir, "animationsetdatasinglefile", pj[: -len(".txt")].replace("\\", "~"))
        os.makedirs(d)
        for name, body in entries:
            text = body + [CACHE_OPEN] + infos + [CACHE_CLOSE]
            with open(os.path.join(d, name), "w", encoding="ascii", newline="") as f:
                f.write("\r\n".join(text) + "\r\n")
            cached += 1
    if cached != expected:
        raise SystemExit(f"wrote {cached} cache set files, expected {expected}")
    print(f"wrote {cached} cache set files for Pandora preview builds")


if __name__ == "__main__":
    main()
