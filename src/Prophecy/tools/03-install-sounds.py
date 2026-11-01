"""Prophecy's own sounds: copy the curator's .wav files into both Prophecy MO2 mods.

They are stock SFX the curator supplied (2026-10-22), so they are NOT committed (same as BloodyCritSound's).
Each SoundDescriptor tools/01 writes plays Data\\Sound\\FX\\Zenderal\\<target>; this puts the files there.
A source that is already 16-bit / 44.1 kHz PCM is copied as is; anything else (the smoke grenade is a 24-bit / 48 kHz
Motion Array file) is converted with BloodyCritSound's converter (windowed-sinc resample, TPDF dither, never clips).

Usage: python -I src/Prophecy/tools/03-install-sounds.py "<folder holding the source .wav files>" [<MO2 mods dir>]
"""
import os, sys, math, random, shutil, struct, wave, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'critsound', os.path.join(HERE, '..', '..', 'BloodyCritSound', 'tools', '01-build-crit-sound.py'))
_conv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_conv)

# target file (under Sound\FX\Zenderal) -> the curator's source file name
SOUNDS = {
    'ZEN_ProphecyPoint_01.wav': 'MA_Warp-Efx_Holy_Spell_Cast_4.wav',                # a Prophecy point is gained
    'ZEN_WarBannerHorn_01.wav': 'WAR HORN 6.wav',                                     # War Banner, on raising it
    'ZEN_TripwireRatchet_01.wav': '02. Hand Key Ratchet.wav',                         # Explosive Tripwire, setting the wire
    'ZEN_SmokescreenBurst_01.wav': 'MA_SoundsByGFXSounds_SmokeGrenadeExplosion_1.wav',  # Smokescreen, on use
    'ZEN_SeismicStomp_01.wav': 'MA_MotionAudio_SuperheroStompOnConcrete_03.wav',     # Seismic Stomp, the shockwave
    'ZEN_DeadeyeShot_01.wav': 'MA_SoundsByGFXSounds_RocketLauncherFire_3.wav',       # Deadeye, on the triple crit
    'ZEN_BleedingShot_01.wav': 'MA_MikalaiSenkin_BloodyKnife_02.wav',                # Bleeding Shot, a bleed starts
    'ZEN_OwlSpawn_01.wav': 'MA_ebccsfx_Mysterious Owl_5.wav',                        # Send an Owl, the owl arrives
}
MODS = ['Zenderal - Prophecy', 'Zenderal - Prophecy v2 (Sanctum)', 'Zenderal - Prophecy v3 (Constellation)']
RATE = 44100


def convert(src, out):
    ch, rate, chans = _conv.read_pcm(src)
    chans = [_conv.resample(c, rate, RATE) for c in chans]
    peak = max(abs(v) for c in chans for v in c)
    gain = 0.98 / peak if peak > 0.98 else 1.0
    rnd = random.Random(0)
    frames = bytearray()
    for i in range(len(chans[0])):
        for c in chans:
            v = c[i] * gain * 32767 + rnd.random() - rnd.random()
            frames += struct.pack('<h', max(-32768, min(32767, int(round(v)))))
    with wave.open(out, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(bytes(frames))


def main():
    src_dir = sys.argv[1]
    mods = sys.argv[2] if len(sys.argv) > 2 else r'E:\Zenderal\mods'
    for target, name in SOUNDS.items():
        src = os.path.join(src_dir, name)
        with wave.open(src) as w:
            fmt = (w.getsampwidth(), w.getframerate(), w.getcomptype())
            secs = w.getnframes() / w.getframerate()
        tmp = None
        if fmt != (2, RATE, 'NONE'):
            tmp = os.path.join(mods, MODS[0], 'Sound', 'FX', 'Zenderal', target + '.tmp')
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            convert(src, tmp)
        print(f'{name}: {fmt[0] * 8}-bit {fmt[1]} Hz, {secs:.2f} s' + (' -> converted to 16-bit 44100 Hz' if tmp else ''))
        for m in MODS:
            root = os.path.join(mods, m)
            if not os.path.isdir(root):                  # v2 (Sanctum) is not always installed
                assert m != MODS[0], f'MO2 mod folder missing: {root}'
                print('   (skipped, not installed:', m + ')')
                continue
            out =os.path.join(root, 'Sound', 'FX', 'Zenderal', target)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(tmp or src, out)
            print('   ->', out)
        if tmp:
            os.remove(tmp)


if __name__ == '__main__':
    main()
