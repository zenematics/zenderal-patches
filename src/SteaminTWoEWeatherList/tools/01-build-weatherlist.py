"""Zenderal - Steamin TWoE Weather List: Steamin ENB's per-weather files for The Weathers of Enderal + Diverse Weathers.

Bottled Shaders' Effects 11 runs Steamin ENB's preset and, like ENB, picks a per-weather file from
enbseries/_weatherlist.ini; a weather without an entry falls back to the generic enbseries.ini values. Steamin's list
covers base Enderal's weathers by bare FormID only. 19 weathers that actually occur in the Ultra load order (used by
a winning climate or region, or forced by Foggy Nights) have no entry. This copies Steamin's list and appends each
missing weather's runtime FormID to the section that already uses the matching Steamin file (classification and
Steamin's own picks for sibling weathers decided the file; see arch-docs/patches/SteaminTWoEWeatherList.md).

Runtime FormIDs depend on load order (Effects 11, like ENB, takes full hex IDs, no plugin names): the plugin index
is computed from the profile's loadorder.txt + plugins.txt. RERUN after the load order changes.

Usage: python 01-build-weatherlist.py <MO2 root> <profile> <output mod folder>
  e.g. python 01-build-weatherlist.py E:/Zenderal Ultra "E:/Zenderal/mods/Zenderal - Steamin TWoE Weather List" """
import os
import re
import struct
import sys

MO2, PROFILE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
STEAMIN = os.path.join(MO2, "mods", "Steamin ENB", "Root", "enbseries", "_weatherlist.ini")
IMPLICIT = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]

# (plugin, object ID, EditorID, Steamin file)
ADD = [
    ("Skyrim.esm", 0x13706E, "EnderalClearNoClouds", "!_Enderal_Clearnoclouds.ini"),
    ("Skyrim.esm", 0x043C5C, "_00E_Desert", "!_Enderal_Desert.ini"),
    ("Skyrim.esm", 0x0DB551, "_00E_EnderalRainLightFogged", "!_Enderal_RainLight.ini"),
    ("Skyrim.esm", 0x072B93, "_00E_Ark_NQ_Kor_CaveWeather", "!_Enderal_IsleOfKorWeather.ini"),
    ("Skyrim.esm", 0x076985, "_00E_Farmcoast", "!_ClearWeather_pineforest_E.ini"),
    ("Skyrim.esm", 0x00703C, "_00E_SuncoastSunrise", "!_Enderal_Tropenidylle.ini"),
    ("Skyrim.esm", 0x06877C, "_00E_Thalgard", "!_RainyWeather_E.ini"),
    ("Skyrim.esm", 0x0373C7, "_00E_Thalgard_New", "!_Foggy_Thalgard_E.ini"),
    ("Enderal - Forgotten Stories.esm", 0x02ED52, "SkyrimClear_Aurora_Green", "!_Enderal_Clear_Aurora_Green.ini"),
    ("Enderal - Forgotten Stories.esm", 0x02ED50, "SkyrimClear_Aurora_Red", "!_Enderal_Clear_Aurora_Red.ini"),
    ("Enderal - Forgotten Stories.esm", 0x02ED51, "SkyrimClear_Aurora_Violet", "!_Enderal_Clear_Aurora_Violet.ini"),
    ("Enderal - Forgotten Stories.esm", 0x01FDCF, "_00E_FS_NQR05_SiteWeatherSnow", "!_SnowyWeather_E.ini"),
    ("Enderal - Forgotten Stories.esm", 0x02E501, "_00E_FS_NQR05_TempleWeather", "!_ClearWeather_snow_E.ini"),
    ("Enderal SE - Diverse Weathers.esp", 0x000800, "_00E_GoldenforstRainLight", "!_Enderal_RainLight.ini"),
    ("Enderal SE - Diverse Weathers.esp", 0x000801, "SkyrimKristallwald", "!_CloudyWeather_E.ini"),
    ("Enderal SE - Diverse Weathers.esp", 0x000805, "SkyrimFogMAGoldenforst", "!_FoggyWeather_E.ini"),
    ("Enderal SE - Diverse Weathers.esp", 0x00080A, "_0E_PilzwaldStorm", "!_RainStorm_heavy_E.ini"),
    ("Enderal SE - Diverse Weathers.esp", 0x00080B, "_0E_PilzwaldFog", "!_Enderal_Pilzwald.ini"),
    ("Foggy Nights - Enderal.esp", 0x000800, "NightThickFog", "!_FoggyWeather_E.ini"),
]


def plugin_path(name, mods):
    for m in mods:
        p = os.path.join(MO2, "mods", m, name)
        if os.path.isfile(p):
            return p
    p = os.path.join(MO2, "Stock Game", "Data", name)
    return p if os.path.isfile(p) else None


def flags(name, mods):
    path = plugin_path(name, mods)
    f = struct.unpack_from("<I", open(path, "rb").read(12), 8)[0] if path else 0
    light = name.lower().endswith(".esl") or bool(f & 0x200)
    master = name.lower().endswith((".esm", ".esl")) or bool(f & 0x1)
    return light, master


def game_load_order(mods):
    """The engine's order: the 5 base masters, then Skyrim.ccc's entries present in Data (in .ccc order; Enderal's
    adds Forgotten Stories and SkyUI there), then plugins.txt's enabled plugins in loadorder.txt order; masters (ESM
    flag, .esm/.esl) are sorted ahead of non-masters. Checked against skse64.log's table (tools note in the doc)."""
    data = os.path.join(MO2, "Stock Game", "Data")
    head = [p for p in IMPLICIT[:5]]
    ccc = os.path.join(MO2, "Stock Game", "Skyrim.ccc")
    if os.path.isfile(ccc):
        head += [l.strip() for l in open(ccc, encoding="utf-8", errors="replace") if l.strip() and os.path.isfile(os.path.join(data, l.strip()))]
    seen = {p.lower() for p in head}
    enabled = {l[1:].strip().lower() for l in open(os.path.join(prof, "plugins.txt"), encoding="utf-8") if l.startswith("*")}
    rest = [l.strip() for l in open(os.path.join(prof, "loadorder.txt"), encoding="utf-8")
            if l.strip() and not l.startswith("#") and l.strip().lower() in enabled and l.strip().lower() not in seen]
    info = {p: flags(p, mods) for p in head + rest}
    # the .ccc block keeps its own order (SkyUI_SE.esp, a non-master, sits right after _ResourcePack.esl in game);
    # only plugins.txt's part is sorted masters-first
    return head + [p for p in rest if info[p][1]] + [p for p in rest if not info[p][1]], info


prof = os.path.join(MO2, "profiles", PROFILE)
mods = [l[1:].rstrip("\r\n") for l in open(os.path.join(prof, "modlist.txt"), encoding="utf-8") if l.startswith("+")]
order, info = game_load_order(mods)
full_i = light_i = 0
runtime_prefix = {}
for name in order:
    if info[name][0]:
        runtime_prefix[name.lower()] = (0xFE << 24) | (light_i << 12)
        light_i += 1
    else:
        runtime_prefix[name.lower()] = full_i << 24
        full_i += 1
if "--check" in sys.argv:  # compare with the game's own table in skse64.log
    log = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "My Games", "Skyrim Special Edition", "SKSE", "skse64.log")
    game = {}
    for l in open(log, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*\((\d+) -> \d+\)\s+(.+)$", l.rstrip())
        if m:
            v = int(m.group(1))
            game[m.group(2).strip().lower()] = (0xFE << 24) | ((v - 0xFE000) << 12) if v >= 0xFE000 else v << 24
    common = [p for p in runtime_prefix if p in game]
    bad = [(p, hex(runtime_prefix[p]), hex(game[p])) for p in common if runtime_prefix[p] != game[p]]
    print(f"check vs skse64.log: {len(common)} plugins compared, {len(bad)} differ")
    for b in bad[:10]:
        print("   ", b)
    sys.exit(0)

raw = open(STEAMIN, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
lines = raw.decode("utf-8", errors="replace").split(nl)
existing = {x.lower().lstrip("0") for l in lines if l.strip().lower().startswith("weatherids") for x in re.split(r"[,\s]+", l.split("=", 1)[1].strip()) if x}
cur_file = None
first_ids_line = {}
for i, l in enumerate(lines):
    m = re.match(r"\s*FileName\s*=\s*(.+)", l)
    if m:
        cur_file = m.group(1).strip()
    if re.match(r"\s*WeatherIDs\s*=", l) and cur_file and cur_file.lower() not in first_ids_line:
        first_ids_line[cur_file.lower()] = i
added = []
for plugin, obj, edid, fname in ADD:
    pre = runtime_prefix.get(plugin.lower())
    assert pre is not None, f"{plugin} is not enabled"
    rid = pre | obj if pre < (0xFE << 24) else pre | (obj & 0xFFF)
    hexid = f"{rid:X}"
    assert hexid.lower().lstrip("0") not in existing, (edid, hexid)
    idx = first_ids_line.get(fname.lower())
    assert idx is not None, f"no section uses {fname}"
    lines[idx] = lines[idx].rstrip() + ", " + hexid
    added.append((hexid, edid, plugin, fname))
os.makedirs(os.path.join(OUT, "Root", "enbseries"), exist_ok=True)
dst = os.path.join(OUT, "Root", "enbseries", "_weatherlist.ini")
open(dst, "wb").write(nl.join(lines).encode("utf-8"))
for a in added:
    print(f"  {a[0]:>9}  {a[1]:34} ({a[2]}) -> {a[3]}")
print(f"wrote {dst}: {len(added)} weathers added")
