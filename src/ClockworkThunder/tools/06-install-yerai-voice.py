"""Voice the "buy it from Yerai" responses with Yerai's own recordings (curator 2026-11-16: "reuse his own lines").

Copies three of his .fuz files (audio + lip sync, unedited) from Enderal's L - Voices.bsa to the voice paths of
02-build-records.py's sale responses:
    sound\\voice\\Zenderal - Clockwork Thunder.esp\\VT_Yerai\\<quest>_<topic>_<response FormID>_<n>.fuz
The engine builds that name from the quest EditorID (first 10 characters), the topic EditorID (to 25 characters in
all) and the response's FormID with the plugin index as 00 (an ESL's local ID padded to 8 digits); 02 keeps both
EditorIDs short so nothing is cut. Written into Zenderal - Patch Collection (SureAI's audio: not committed).

Usage:  python src/ClockworkThunder/tools/06-install-yerai-voice.py [--mods <MO2 mods>] [--target <mod>]
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
sys.path.insert(0, os.path.join(ROOT, 'src', 'Prophecy', 'tools'))
import _bsa  # noqa: E402

_spec = importlib.util.spec_from_file_location('ct02', os.path.join(HERE, '02-build-records.py'))
ct02 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ct02)

BSA = os.path.join(TOOLS['gameDataDir'], 'L - Voices.bsa')
SRC_DIR = 'sound\\voice\\skyrim.esm\\vt_yerai\\'


def voice_name(info_formid, n):
    quest = ct02.SALE_QUEST_EDID[:10]
    topic = ct02.SALE_TOPIC_EDID[:25 - len(quest)]
    assert quest == ct02.SALE_QUEST_EDID and topic == ct02.SALE_TOPIC_EDID, 'an EditorID would be cut: keep them short'
    return ('%s_%s_%08X_%d.fuz' % (quest, topic, int(info_formid, 16), n)).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(TOOLS['modlistRoot'], 'mods'))
    ap.add_argument('--target', default='Zenderal - Patch Collection')
    args = ap.parse_args()
    root = os.path.join(args.mods, args.target)
    assert os.path.isdir(root), root
    data, listing = _bsa.listing(BSA)
    out_dir = os.path.join(root, 'sound', 'voice', ct02.ME, 'VT_Yerai')
    os.makedirs(out_dir, exist_ok=True)
    for info, lines in ct02.SALE_LINES.items():
        for n, (text, src) in enumerate(lines, 1):
            key = SRC_DIR + src
            assert key in listing, ('not in L - Voices.bsa', key)
            raw = _bsa.read(data, listing[key])
            assert raw[:4] == b'FUZE', src
            dst = os.path.join(out_dir, voice_name(info, n))
            open(dst, 'wb').write(raw)
            print('%-48s <- %s (%d bytes)  "%s"' % (os.path.basename(dst), src, len(raw), text))


if __name__ == '__main__':
    main()
