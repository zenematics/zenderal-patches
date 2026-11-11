#!/usr/bin/env python3
"""Build the Nexus copy of the patch: Pretty x EGO only, no list-only masters.

The list's build (01 -> 04) keeps whatever wins in Zenderal, so it masters list-only mods: ERA Heavy Leather
(2 visual winners) and Malphas' Blessing (03 forwards Tealor's face). Nexus users may have neither, and a missing
master stops the plugin loading (2026-11-11 report: the old upload still mastered Pretty Enderal Armory - Fixes, which
Pretty 2.x no longer ships). This runs 01 --standalone (chains of base + EGO/donors + Pretty plugins only), 02 and 04
(no 03), deserializes the result into the Nexus archive, then puts the list's record folders back untouched.

Usage: python 05-build-nexus-standalone.py ["<MO2 profile>"]   (default Ultra)
Output: <nexusUploads or E:/Nexus uploads>/Zenderal - Pretty Armory EGO Patch.7z (the previous one is kept as .bak.7z
in the scratch dir printed at the end).
"""
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ESP_DIR = os.path.join(ROOT, "src", "PrettyArmoryEGO", "PrettyArmoryEGOESP")
CHAINS = os.path.join(ROOT, "reference", "mods", "Pretty", "_chains.json")
NAME = "Zenderal - Pretty Armory EGO Patch.esp"
TOOLS = json.load(open(os.path.join(ROOT, ".claude", "config", "tools.json"), encoding="utf-8-sig"))
UPLOADS = TOOLS.get("nexusUploads") or "E:/Nexus uploads"
SEVENZIP = TOOLS.get("sevenZip") or "C:/Program Files/7-Zip/7z.exe"
ALLOWED = {"Skyrim.esm", "Update.esm", "Enderal - Forgotten Stories.esm", "Enderal SE - Gameplay Overhaul.esp"}
profile = sys.argv[1] if len(sys.argv) > 1 else "Ultra"


def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{cmd[1] if len(cmd) > 1 else cmd[0]} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def masters(path):
    d = open(path, "rb").read()
    end, p, out = 24 + struct.unpack_from("<I", d, 4)[0], 24, []
    while p < end:
        n = struct.unpack_from("<H", d, p + 4)[0]
        if d[p:p + 4] == b"MAST":
            out.append(d[p + 6:p + 5 + n].decode("cp1252"))
        p += 6 + n
    return out


tmp = tempfile.mkdtemp(prefix="zen_pea_nexus_")
saved_esp, saved_chains = os.path.join(tmp, "esp"), os.path.join(tmp, "_chains.json")
shutil.copytree(ESP_DIR, saved_esp)
shutil.copyfile(CHAINS, saved_chains)
try:
    py = sys.executable
    print(run(py, "-I", os.path.join(HERE, "01-build-override-chains.py"), profile, "--standalone").strip())
    print(run(py, "-I", os.path.join(HERE, "02-merge-pretty-ego.py")).strip().splitlines()[-1])
    print(run(py, "-I", os.path.join(HERE, "04-restore-pretty-meshes.py")).strip().splitlines()[-1])
    out = os.path.join(tmp, "build", NAME)
    os.makedirs(os.path.dirname(out))
    sp = TOOLS["spriggit"]
    run(TOOLS["spriggitCli"], "deserialize", "--InputPath", ESP_DIR, "--OutputPath", out)
    ms = masters(out)
    bad = [m for m in ms if m not in ALLOWED and not m.startswith("Pretty")]
    if bad or "Pretty Enderal Armory - Fixes.esp" in ms:
        sys.exit(f"standalone build masters list-only plugins: {bad or ms}")
    archive = os.path.join(UPLOADS, "Zenderal - Pretty Armory EGO Patch.7z")
    if os.path.exists(archive):
        shutil.copyfile(archive, os.path.join(tmp, "previous.bak.7z"))
        os.remove(archive)
    run(SEVENZIP, "a", "-t7z", archive, out)
    print(f"{archive}: written; masters = {ms}")
finally:
    shutil.rmtree(ESP_DIR)
    shutil.copytree(saved_esp, ESP_DIR)
    shutil.copyfile(saved_chains, CHAINS)
    print(f"list build restored; scratch (previous archive) in {tmp}")
