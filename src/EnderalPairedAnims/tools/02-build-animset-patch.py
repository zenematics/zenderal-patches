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

Pandora reads `animationsetdatasinglefile/<project>/<set file>` (each line a clip path). The
per-project root-file form (`<project>.txt`) is avoided: PandoraAssembler.AssembleAnimSetDataPatch
`break`s after the first project file, so only one project would be patched.

Input: Pandora's template animationsetdatasinglefile.txt (for the set names).
usage: python 02-build-animset-patch.py <Pandora>/Pandora_Engine/Skyrim/Template/animationsetdatasinglefile.txt <out zpairset dir>
"""
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


if __name__ == "__main__":
    main()
