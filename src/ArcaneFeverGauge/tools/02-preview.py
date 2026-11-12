"""Write an HTML page that plays the built widget movie in Ruffle (a Flash emulator), for a look without the game.

Standalone, the movie centres itself, draws at 1.6x and cycles the fever 0 -> 100 in 12.5 steps (its own preview
branch: no HUD, so no Vel'dun bars to follow). Ruffle is not Scaleform: this checks the drawing code and the look,
not the HUD placement or SkyUI's calls.

Usage: python -I src/ArcaneFeverGauge/tools/02-preview.py <out.html> [player size in px, default 400]
"""
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SWF = os.path.join(os.path.dirname(HERE), 'data', 'Interface', 'exported', 'widgets', 'zenderal', 'arcanefever.swf')
RUFFLE = 'https://unpkg.com/@ruffle-rs/ruffle@0.8.0-nightly.2026.10.25/ruffle.js'

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Arcane Fever Gauge preview</title>
<style>body{margin:0;background:#2b2018;display:flex;justify-content:center;align-items:center;height:100vh}
#p{width:%(size)dpx;height:%(size)dpx;flex:none}body{overflow:hidden}</style></head>
<body><div id="p"></div>
<script src="%(ruffle)s"></script>
<script>
window.RufflePlayer = window.RufflePlayer || {};
window.addEventListener('load', function () {
  var player = window.RufflePlayer.newest().createPlayer();
  player.style.width = '%(size)dpx'; player.style.height = '%(size)dpx';
  document.getElementById('p').appendChild(player);
  var bin = atob('%(swf)s'), bytes = new Uint8Array(bin.length);
  for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  player.load({data: bytes, swfFileName: 'arcanefever.swf', autoplay: 'on', unmuteOverlay: 'hidden',
               splashScreen: false, letterbox: 'off'});
});
</script></body></html>
"""


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    size = int(sys.argv[2]) if len(sys.argv) == 3 else 400
    data = base64.b64encode(open(SWF, 'rb').read()).decode('ascii')
    open(sys.argv[1], 'w', encoding='utf-8').write(PAGE % {'ruffle': RUFFLE, 'swf': data, 'size': size})
    print('wrote', sys.argv[1])


if __name__ == '__main__':
    main()
