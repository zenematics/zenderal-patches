"""Build the Arcane Fever Gauge's SkyUI widget movie from its ActionScript source.

    src/ArcaneFeverGauge/widget/arcanefever.as  ->  data/Interface/exported/widgets/zenderal/arcanefever.swf

The movie is our own work, built from scratch: this script writes a one-frame SWF 8 skeleton (FileAttributes,
background, one empty DoAction, ShowFrame) and FFDec's AS2 compiler (`tools.json` "ffdec") replaces that DoAction
with the compiled source. Nothing is drawn on the timeline: every shape comes from the drawing API in the script.

Checks after the build:
- the decompiled frame script defines every function SkyUI's widget base and our Papyrus script call;
- the output is a SWF 8 movie with one frame.

The .swf is committed (CI has no FFDec), like the .pex. Rebuild and re-commit after every edit of the .as file.

Usage: python -I src/ArcaneFeverGauge/tools/01-build-widget.py
"""
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PATCH))
SRC = os.path.join(PATCH, 'widget', 'arcanefever.as')
OUT = os.path.join(PATCH, 'data', 'Interface', 'exported', 'widgets', 'zenderal', 'arcanefever.swf')

TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8'))
FFDEC = TOOLS.get('ffdec') or sys.exit('tools.json has no "ffdec" (path to ffdec.jar)')

STAGE_PX = (400, 400)          # only matters for the standalone preview; SkyUI ignores the loaded movie's stage
BACKGROUND = (0x2B, 0x20, 0x18)  # preview only (a dark wood, like the curator's screenshot)
REQUIRED = [
    # SkyUI widget loader + SKI_WidgetBase
    'setRootPath', 'setHudMetrics', 'setClientInfo', 'setModes', 'setHAnchor', 'setVAnchor',
    'setPositionX', 'setPositionY', 'setAlpha', 'tweenTo', 'fadeTo',
    # ZFG_ArcaneFeverWidget
    'setFever', 'setLayout', 'setSuppressed', 'zfgReady', 'setDisplay', 'peek', 'FADE_OUT_S',
    # the widget itself
    'createEmptyMovieClip("widget"', 'HEALTH_TOP_RIGHT', 'MANA_BOTTOM_RIGHT', 'onEnterFrame',
    # the TrueHUD host (the list's visible bars are TrueHUD's player widget)
    'measureTrueHUD', 'playerWidget', 'FRAME_PAD',
]


def tag(code, body=b''):
    if len(body) < 0x3F:
        return struct.pack('<H', (code << 6) | len(body)) + body
    return struct.pack('<HI', (code << 6) | 0x3F, len(body)) + body


def rect(xmin, xmax, ymin, ymax):
    vals = [xmin, xmax, ymin, ymax]
    nb = max(v.bit_length() for v in vals) + 1
    bits = format(nb, '05b') + ''.join(format(v & ((1 << nb) - 1), '0%db' % nb) for v in vals)
    bits += '0' * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def skeleton():
    body = rect(0, STAGE_PX[0] * 20, 0, STAGE_PX[1] * 20) + struct.pack('<HH', 30 << 8, 1)  # 30 fps, 1 frame
    body += tag(69, struct.pack('<I', 0))   # FileAttributes: no flags (AS2, local playback)
    body += tag(9, bytes(BACKGROUND))       # SetBackgroundColor
    body += tag(12, b'\x00')                # DoAction: ActionEnd (replaced by the compiled script)
    body += tag(1) + tag(0)                 # ShowFrame, End
    return b'FWS' + bytes([8]) + struct.pack('<I', 8 + len(body)) + body


def ffdec(*args):
    r = subprocess.run(['java', '-jar', FFDEC] + list(args), capture_output=True, text=True)
    text = (r.stdout or '') + (r.stderr or '')
    if r.returncode != 0 or 'error' in text.lower() or 'exception' in text.lower():
        sys.exit('ffdec %s failed (exit %d):\n%s' % (args[0], r.returncode, text))
    return text


def header(path):
    d = open(path, 'rb').read()
    sig, ver = d[:3], d[3]
    if sig == b'CWS':
        d = d[:8] + zlib.decompress(d[8:])
    elif sig != b'FWS':
        sys.exit('%s: not a SWF (%r)' % (path, sig))
    nb = d[8] >> 3
    off = 8 + (5 + 4 * nb + 7) // 8
    frames = struct.unpack_from('<H', d, off + 2)[0]
    return ver, frames


def main():
    tmp = tempfile.mkdtemp(prefix='zfg_widget_')
    try:
        skel = os.path.join(tmp, 'skeleton.swf')
        open(skel, 'wb').write(skeleton())
        scripts = os.path.join(tmp, 'scripts', 'frame_1')
        os.makedirs(scripts)
        shutil.copyfile(SRC, os.path.join(scripts, 'DoAction.as'))
        built = os.path.join(tmp, 'arcanefever.swf')
        ffdec('-importScript', skel, built, os.path.join(tmp, 'scripts'))
        if not os.path.isfile(built) or os.path.getsize(built) <= len(skeleton()) + 100:
            sys.exit('ffdec produced no script (output %s)' % built)

        dec = os.path.join(tmp, 'dec')
        ffdec('-format', 'script:as', '-export', 'script', dec, built)
        found = []
        for root, _, files in os.walk(dec):
            for f in files:
                found.append(open(os.path.join(root, f), encoding='utf-8', errors='replace').read())
        text = '\n'.join(found)
        missing = [k for k in REQUIRED if k not in text]
        if missing:
            sys.exit('compiled movie lacks: %s' % ', '.join(missing))
        ver, frames = header(built)
        if ver != 8 or frames != 1:
            sys.exit('unexpected movie: SWF %d, %d frames' % (ver, frames))

        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        shutil.copyfile(built, OUT)
        print('built %s (%d bytes, SWF %d, %d frame); all %d interface names present'
              % (os.path.relpath(OUT, REPO), os.path.getsize(OUT), ver, frames, len(REQUIRED)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
