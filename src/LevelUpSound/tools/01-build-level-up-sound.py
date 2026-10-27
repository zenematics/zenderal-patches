"""Rebuild the `Zenderal - Level Up Sound` MO2 mod from a user-supplied .wav.

Enderal's level-up (`_00E_EPUpdateFunctions` on the player, property `UILevelUp`) plays sound marker
`UILevelUp 057B45`, whose descriptor is `UILevelUpSD 057B44:Skyrim.esm`. `Zenderal - Level Up Sound.esp` points that
descriptor at this mod's own file, `Sound\\FX\\Zenderal\\ZEN_LevelUp_HolySpellCast.wav`.

The source is a Motion Array SFX the curator picked (`MA_Warp-Efx_Holy_Spell_Cast_4.wav`, 24-bit / 48 kHz stereo).
It is licensed, so neither it nor the output is committed. The conversion (16-bit / 44.1 kHz PCM, windowed-sinc
resample, TPDF dither, never clips) is BloodyCritSound's, reused here.

Usage:  python 01-build-level-up-sound.py <source.wav> [<mods dir>]     (default E:/Zenderal/mods)
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "crit", os.path.join(HERE, "..", "..", "BloodyCritSound", "tools", "01-build-crit-sound.py"))
crit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crit)

crit.MOD = "Zenderal - Level Up Sound"
crit.REL = ["sound", "fx", "zenderal", "zen_levelup_holyspellcast.wav"]  # must match the SNDR's SoundFiles

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    crit.main()
