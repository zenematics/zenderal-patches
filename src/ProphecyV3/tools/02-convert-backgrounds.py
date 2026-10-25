"""Prophecy v3 - tree backgrounds: the curator's PNGs -> the DDS the constellation window draws behind each tree.

Input:  <folder>/<Tree-Name>.png, one per tree ("Martial-Arts.png" for "Martial Arts"); the curator's art, ~1672x941.
Output: src/ProphecyV3/assets/interface/ProphecyBackgrounds/<Tree-Name>.dds - centre-cropped to 16:9 (never
        stretched), 1600x900 BC1, one mip. COMMITTED (CI cannot run texconv). The window crops it again to the
        canvas's own aspect, dims it and lays a vignette over it.

Usage (Pillow is not available under -I):  python src/ProphecyV3/tools/02-convert-backgrounds.py "<folder>"
Then rerun tools/01-build-layout.py, which records each tree's background in ZenProphecyUI.json.
"""
import os, sys, json, subprocess, tempfile, importlib.util
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'src', 'ProphecyV3', 'assets', 'interface', 'ProphecyBackgrounds')
W, H = 1600, 900

_spec = importlib.util.spec_from_file_location('v1', os.path.join(REPO, 'src', 'Prophecy', 'tools', '01-build-trees.py'))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)


def stem(tree):
    return tree.replace(' ', '-')


def texconv():
    tools = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
    p = os.path.join(os.path.dirname(tools.get('xedit', '')), 'Edit Scripts', 'Texconvx64.exe')
    assert os.path.isfile(p), f'texconv not found next to tools.json xedit: {p}'
    return p


def main():
    src = sys.argv[1]
    tc = texconv()
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for tree, _, _ in v1.TREES:
            png = os.path.join(src, stem(tree) + '.png')
            if not os.path.isfile(png):
                print(f'{tree}: no {stem(tree)}.png - skipped (the window draws no background for it)')
                continue
            im = Image.open(png).convert('RGB')
            w, h = im.size
            if w / h > W / H:
                cw = round(h * W / H); im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
            else:
                ch = round(w * H / W); im = im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
            tmp_png = os.path.join(tmp, stem(tree) + '.png')
            im.resize((W, H), Image.LANCZOS).save(tmp_png)
            r = subprocess.run([tc, '-nologo', '-y', '-f', 'BC1_UNORM', '-m', '1', '-o', OUT, tmp_png],
                               capture_output=True, text=True)
            assert r.returncode == 0, f'texconv failed on {tree}: {r.stdout}{r.stderr}'
            for f in os.listdir(OUT):             # texconv writes .DDS; keep the name the JSON uses
                if f.lower() == stem(tree).lower() + '.dds' and f != stem(tree) + '.dds':
                    os.replace(os.path.join(OUT, f), os.path.join(OUT, stem(tree) + '.dds'))
            print(f'{tree}: {w}x{h} -> {W}x{H} BC1')


if __name__ == '__main__':
    main()
