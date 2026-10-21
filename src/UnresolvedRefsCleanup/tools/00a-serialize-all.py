"""Serialize every enabled plugin of the Ultra profile (except the base masters) with Spriggit 0.40.0 into
<out>/<alphanumeric name>/, skipping ones already done. Logs progress to <out>/_progress.txt."""
import json
import os
import re
import subprocess
import sys
import time

out = sys.argv[1]
root = r"E:\Zenderal"
cli = json.load(open(r"E:\zenderal-patches\.claude\config\tools.json", encoding="utf-8-sig"))["spriggitCli"]
mods = [l[1:].strip() for l in open(root + r"\profiles\Ultra\modlist.txt", encoding="utf-8") if l.startswith("+")]
plugins = [l[1:].strip() for l in open(root + r"\profiles\Ultra\plugins.txt", encoding="utf-8") if l.startswith("*")]
os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, "_progress.txt"), "a", encoding="utf-8")


def find(p):
    for m in mods:
        f = os.path.join(root, "mods", m, p)
        if os.path.isfile(f):
            return f
    return None


t0 = time.time()
for i, p in enumerate(plugins, 1):
    f = find(p)
    if not f:
        continue
    d = os.path.join(out, re.sub(r"[^A-Za-z0-9]", "", p))
    if os.path.isfile(os.path.join(d, "RecordData.yaml")):
        continue
    r = subprocess.run([cli, "serialize", "--InputPath", f, "--OutputPath", d, "--GameRelease", "EnderalSE",
                        "--PackageName", "Spriggit.Yaml.Skyrim", "--PackageVersion", "0.40.0"],
                       capture_output=True, text=True)
    log.write(f"{i}/{len(plugins)} {time.time() - t0:6.0f}s exit {r.returncode} {p}\n")
    log.flush()
log.write("DONE\n")
