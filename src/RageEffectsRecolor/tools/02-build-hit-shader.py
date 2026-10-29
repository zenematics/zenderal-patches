r"""Zenderal - Rage Effects.esp: A Dark Warrior's Tale's hit shader without its cloud (curator 2026-10-27).

_CDW_DarknessDamageFXS 00151E is the hit shader Shadow Carve, Shadowbringer, Bloodletter and Soulrender play on what
they hit. Its particles (Effects\SmokeInky01.dds through the vanilla palette GradDisguiseShader02, growing to scale 96,
birth ratio 100) were the big magenta cloud on the target - the side power attack in the curator's screenshot. This
writes the pack's record verbatim (from the cleaned plugin's serialization in reference/mods/DarkWarriorsTale) with
ParticleFullBirthRatio 0: no particles; the membrane (a dark-red glow on the target's surface) stays.

Writes the YAML into src/RageEffectsRecolor/RageEffectsRecolorESP and, with --build, the plugin into the MO2 mod
"Zenderal - Rage Effects Recolor". Load it after KittyClass_DarkWarrior.esp.

Usage: python 02-build-hit-shader.py [--build] [--modlist E:\Zenderal]
"""
import argparse
import colorsys
import glob
import json
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ESP_DIR = os.path.join(REPO, 'src', 'RageEffectsRecolor', 'RageEffectsRecolorESP')
MOD = 'Zenderal - Rage Effects.esp'
PACK = 'KittyClass_DarkWarrior.esp'
SRC = os.path.join(REPO, 'reference', 'mods', 'DarkWarriorsTale', 'EffectShaders',
                   f'_CDW_DarknessDamageFXS - 00151E_{PACK}.yaml')
OUT_MOD = 'Zenderal - Rage Effects Recolor'

HEADER = f"""SpriggitSource:
  PackageName: Spriggit.Yaml.Skyrim
  Version: 0.40
ModKey: {MOD}
GameRelease: EnderalSE
ModHeader:
  Flags:
  - Small
  Stats:
    Version: 1.7
  Author: Zenderal
  Description: >-
    A Dark Warrior's Tale's hit shader without its smoke cloud, for Prophecy's Rage (src/RageEffectsRecolor).
  MasterReferences:
  - Master: Skyrim.esm
    FileSize: 0
  - Master: {PACK}
    FileSize: 0
  INTV: 1
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--modlist', default=r'E:\Zenderal')
    a = ap.parse_args()
    assert os.path.isfile(SRC), f'{SRC}: serialize the cleaned KittyClass_DarkWarrior.esp into reference/mods/DarkWarriorsTale'
    t = open(SRC, encoding='utf-8').read().replace('\r\n', '\n')
    t, n = re.subn(r'^ParticleFullBirthRatio: .*$', 'ParticleFullBirthRatio: 0', t, flags=re.M)
    assert n == 1, 'ParticleFullBirthRatio'
    # _CDW_AbsorbImod 000890: the screen tint Bloodletter's/Soulrender's magicAbsorbFXScript plays (its TrapImod) -
    # tint keys magenta BF007F and purple 8000FF. Every cool '#AARRGGBB' key warmed (alpha and times kept).
    imad_src = os.path.join(os.path.dirname(os.path.dirname(SRC)), 'ImageSpaceAdapters', f'_CDW_AbsorbImod - 000890_{PACK}.yaml')
    imad = open(imad_src, encoding='utf-8').read().replace('\r\n', '\n')
    warmed = 0

    def warm_key(m):
        nonlocal warmed
        a, r, g, b = (int(m.group(i), 16) for i in range(1, 5))
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.12 or not (195 <= h * 360 <= 345):
            return m.group(0)
        warmed += 1
        r2, g2, b2 = colorsys.hsv_to_rgb((20.0 * v) / 360.0, s, v)   # tools/01 HUE_BRIGHT (curator: 32 was too light)
        return f"'#{a:02X}{round(r2 * 255):02X}{round(g2 * 255):02X}{round(b2 * 255):02X}'"
    imad = re.sub(r"'#([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})'", warm_key, imad)
    assert warmed >= 2, f'AbsorbImod: {warmed} keys warmed'
    shutil.rmtree(ESP_DIR, ignore_errors=True)
    os.makedirs(os.path.join(ESP_DIR, 'EffectShaders'))
    os.makedirs(os.path.join(ESP_DIR, 'ImageSpaceAdapters'))
    open(os.path.join(ESP_DIR, 'ImageSpaceAdapters', os.path.basename(imad_src)), 'w', encoding='utf-8', newline='\r\n').write(imad)
    print(f'AbsorbImod: {warmed} colour keys warmed')
    # the drain's absorb visuals (curator: the side power attack's purple cloud was still there after the hit shader):
    # the pack's four VisualEffects, which magicAbsorbFXScript plays on caster and target, each with a vanilla absorb
    # mesh and a vanilla particle shader (AbsorbHealthFXS red, AbsorbBlueFXS blue: MagicCaustic01 particles). Vanilla
    # Absorb spells share those, so the pack's VFX records are emptied here instead - no art, no shader.
    os.makedirs(os.path.join(ESP_DIR, 'VisualEffects'))
    vfx_dir = os.path.join(os.path.dirname(os.path.dirname(SRC)), 'VisualEffects')
    for vid in ('001523', '001525', '00151D', '001522'):
        p = glob.glob(os.path.join(vfx_dir, f'* - {vid}_{PACK}.yaml'))
        assert len(p) == 1, vid
        v = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
        v, n = re.subn(r'^(?:EffectArt|Shader): .*\n', '', v, flags=re.M)
        assert n >= 1, f'{vid}: no art or shader'   # the cast VFX have both, the target VFX art only
        open(os.path.join(ESP_DIR, 'VisualEffects', os.path.basename(p[0])), 'w', encoding='utf-8', newline='\r\n').write(v)
    print('absorb visual effects emptied: 4')
    # the "fake absorb" restores (the drain's heal on the player): their effects play vanilla particle shaders on the
    # player - AbsorbHealthFXS (001587) and AbsorbBlueFXS (001588, blue MagicCaustic01 particles: the purple cloud the
    # curator still saw on side power attacks once the meshes' Vapor01 was gone). HitShader dropped; the restore stays.
    os.makedirs(os.path.join(ESP_DIR, 'MagicEffects'))
    mgef_dir = os.path.join(os.path.dirname(os.path.dirname(SRC)), 'MagicEffects')
    # and every pack effect that puts _CDW_DarknessDamageFXS on the target (the curator's magenta sheet over a Lost One's
    # corpse after a side power attack, with the shader's particles already off: its membrane - ShockTile01 through
    # Dawnguard's GradVampireTrans01 palette, which Glorious Gradients colours): Shadowbringer, Shadow Carve, Bloodletter,
    # Soulrender, the spikes, and their aiming-fix twins. Damage and drain unchanged.
    DARKNESS_SHADER_USERS = ('000FA2', '001584', '000807', '001585', '000806', '001586', '000809', '0008AF', '000805',
                             '000AE3', '0008AA')
    for mid in ('001587', '001588') + DARKNESS_SHADER_USERS:
        p = glob.glob(os.path.join(mgef_dir, f'* - {mid}_{PACK}.yaml'))
        assert len(p) == 1, mid
        v = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
        v, n = re.subn(r'^HitShader: .*\n', '', v, flags=re.M)
        assert n == 1, f'{mid}: hit shader'
        open(os.path.join(ESP_DIR, 'MagicEffects', os.path.basename(p[0])), 'w', encoding='utf-8', newline='\r\n').write(v)
    print(f'effects without hit shader: {2 + len(DARKNESS_SHADER_USERS)}')
    # the pack's own class ability, _CDW_ClassMGEF 00080B ("Vehemence: assumes the mantle of the Dark Warrior"), active on
    # the curator's character (the cloud kept coming on a side power attack where the Rage DLL fired nothing, 2026-10-27):
    # it applies the class perk 000892, whose ApplyCombatHitSpell entries fire the pack's own actions through its wrapper
    # spells (ClassProgression defaults to 1 = the in-place Soulrender, and MCO reports every power attack as standing),
    # its _CDW_ClassAbMonitorScript casts more on hits taken, and it carries its own hit shader 00088A and art 00089F.
    # Rage replaces all of it, so the ability is made inert here: no script, perk, shader or art.
    p = glob.glob(os.path.join(mgef_dir, f'* - 00080B_{PACK}.yaml'))
    assert len(p) == 1, '00080B'
    v = open(p[0], encoding='utf-8').read().replace('\r\n', '\n')
    v, n1 = re.subn(r'^VirtualMachineAdapter:\n(?:  .*\n)*', '', v, count=1, flags=re.M)
    v, n2 = re.subn(r'^(?:HitShader|HitEffectArt|PerkToApply): .*\n', '', v, flags=re.M)
    assert (n1, n2) == (1, 3), f'class ability: script {n1}, fields {n2}'
    open(os.path.join(ESP_DIR, 'MagicEffects', os.path.basename(p[0])), 'w', encoding='utf-8', newline='\r\n').write(v)
    print('class ability 00080B made inert')
    open(os.path.join(ESP_DIR, 'RecordData.yaml'), 'w', encoding='utf-8', newline='\r\n').write(HEADER)
    open(os.path.join(ESP_DIR, 'spriggit-meta.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(
        {'PackageName': 'Spriggit.Yaml.Skyrim', 'Version': '0.40.0', 'Release': 'EnderalSE', 'ModKey': MOD}, indent=2) + '\n')
    open(os.path.join(ESP_DIR, 'EffectShaders', os.path.basename(SRC)), 'w', encoding='utf-8', newline='\r\n').write(t)
    print(f'wrote {ESP_DIR}')
    if a.build:
        tools = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
        dst = os.path.join(a.modlist, 'mods', OUT_MOD, MOD)
        r = subprocess.run([tools['spriggitCli'], 'deserialize', '-i', ESP_DIR, '-o', dst], capture_output=True, text=True)
        assert r.returncode == 0 and os.path.isfile(dst), f'Spriggit failed: {r.stdout[-800:]}{r.stderr[-800:]}'
        print(f'built {dst}')


if __name__ == '__main__':
    main()
