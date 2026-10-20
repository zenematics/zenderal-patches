r"""Build `Zenderal - 2.1 Texture Rename Fix` from the installed list -- never hand-edit its textures.

Why: Enderal 2.1 renamed four texture-set (TXST) normal-map paths to the standard `_n` suffix
(reference/base vs reference/base-2.1.4.4, 2026-10-20):
    _00E_Sand01 / _00E_Sand02  ground_wet_sand01_n_DXT1.dds   -> ground_wet_sand01_DXT1_n.dds
    _00E_MossRock              rock_moss03_n_DXT1.dds          -> rock_moss03_dxt1_n.dds
    _00E_CrystallPlant01       _00E_CrystallPlant01_g.dds      -> _00E_crystallplant01_n.dds
Texture mods written for 2.0 ship their normal map under the OLD name, so after 2.1 the texture set
reaches some other mod's (or Enderal's) file at the new name, and the retexture's colour map is drawn
with a normal map made for a different image (seen 2026-10-20: SRP's sand colour + ETATU's normal).

For each rename this copies the file that wins the OLD path to the NEW path when that winner is a loose
mod ranked above whatever wins the NEW path, so each retexture keeps its own normal map. Nothing is
copied when the new path is already won by an equal or higher mod. The files are other authors' work,
so they are generated from the user's install, never committed. Re-run after texture mods change.

Usage:  python 01-forward-renamed-textures.py [--modlist <MO2 root>] [--profile Ultra] [--dry-run]
"""
import argparse
import os
import shutil

MOD = 'Zenderal - 2.1 Texture Rename Fix'
RENAMES = [  # (old path, new path), relative to Data
    (r'textures\enderal\landscape\ground_wet_sand01_n_DXT1.dds', r'textures\enderal\landscape\ground_wet_sand01_DXT1_n.dds'),
    (r'textures\enderal\rock_moss03_n_DXT1.dds', r'textures\enderal\rock_moss03_dxt1_n.dds'),
    (r'textures\enderal\flora\_00E_CrystallPlant01_g.dds', r'textures\enderal\flora\_00E_crystallplant01_n.dds'),
]


def enabled_mods(root, profile):
    with open(os.path.join(root, 'profiles', profile, 'modlist.txt'), encoding='utf-8') as f:
        return [l[1:].rstrip('\r\n') for l in f if l.startswith('+')]


def winner(root, mods, rel):
    """(priority index, mod, file) of the highest-priority loose copy, ignoring our own output mod."""
    parts = rel.lower().split('\\')
    for i, m in enumerate(mods):
        if m == MOD:
            continue
        base = os.path.join(root, 'mods', m)
        # case-insensitive walk down the path
        cur = base
        for p in parts:
            try:
                hit = next((e for e in os.listdir(cur) if e.lower() == p), None)
            except (FileNotFoundError, NotADirectoryError):
                hit = None
            if hit is None:
                cur = None
                break
            cur = os.path.join(cur, hit)
        if cur and os.path.isfile(cur):
            return i, m, cur
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default=r'E:\Zenderal')
    ap.add_argument('--profile', default='Ultra')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    mods = enabled_mods(a.modlist, a.profile)
    out = os.path.join(a.modlist, 'mods', MOD)
    if not a.dry_run and os.path.isdir(os.path.join(out, 'textures')):
        shutil.rmtree(os.path.join(out, 'textures'))
    written = 0
    for old, new in RENAMES:
        wo, wn = winner(a.modlist, mods, old), winner(a.modlist, mods, new)
        desc = lambda w: f'{w[1]} (priority {w[0]})' if w else "Enderal's archives"
        if wo and (wn is None or wo[0] < wn[0]):
            print(f'COPY  {old}\n      from {desc(wo)} -> {new} (was won by {desc(wn)})')
            if not a.dry_run:
                dst = os.path.join(out, new)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(wo[2], dst)
            written += 1
        else:
            print(f'KEEP  {new}: won by {desc(wn)}; old name won by {desc(wo)}')
    print(f'{"would write" if a.dry_run else "wrote"} {written} file(s) to {out}')


if __name__ == '__main__':
    main()
