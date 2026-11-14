"""Build MO2 mod `Zenderal - EVG Modesty Off`: EVG Conditional Idles' four Modesty submods disabled by OAR user.json.

Player report (2026-11-13): Yuslan Sha'Rim walks "like he is covering himself". EVG Conditional Idles' Modesty
submods (NPC/Player x male/female) play a covering walk for any actor wearing nothing with ArmorCuirass 06C0EC or
ClothingBody 0A8657. Many Enderal robes and outfits carry neither keyword, so dressed NPCs walked as if naked. The
curator chose to turn modesty off for players and NPCs alike.

OAR reads a submod folder's `user.json` in place of its `config.json`. Each user.json written here is the winning
config.json (the compatibility patch's, which outranks EVG Conditional Idles in MO2) with only "disabled" set to true,
so nothing else changes. EVG's own files are untouched. The MO2 mod must outrank both EVG mods.
Usage: python 01-build-modesty-off.py
"""
import json
import os

MODS = r"E:\Zenderal\mods"
SOURCES = ["Compatibility patch for EVG Conditional Idles", "EVG Conditional Idles"]  # winner first
REL = os.path.join("meshes", "actors", "character", "animations", "OpenAnimationReplacer", "EVGCI")
SUBMODS = ["NPC Modesty F", "NPC Modesty M", "Player Modesty F", "Player Modesty M"]
OUT = os.path.join(MODS, "Zenderal - EVG Modesty Off")

for sub in SUBMODS:
    src = next((os.path.join(MODS, m, REL, sub, "config.json") for m in SOURCES
                if os.path.isfile(os.path.join(MODS, m, REL, sub, "config.json"))), None)
    if not src:
        raise SystemExit(f"{sub}: no config.json in {SOURCES}")
    cfg = json.load(open(src, encoding="utf-8"))
    if "conditions" not in cfg:
        raise SystemExit(f"{src}: not an OAR submod config")
    cfg["disabled"] = True
    dst = os.path.join(OUT, REL, sub, "user.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=1)
    print(f"{sub}: disabled (from {os.path.relpath(src, MODS).split(os.sep)[0]})")
