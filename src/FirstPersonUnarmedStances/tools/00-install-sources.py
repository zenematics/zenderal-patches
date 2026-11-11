"""Install the three first-person unarmed sets UNTOUCHED as their own MO2 mods, from MO2's downloads
(fpu_sources.SOURCES): each archive's data folder (the shallowest folder holding a data folder
such as `meshes`/`sound`/`skse`, or a plugin) copied byte for byte, plus an MO2
meta.ini. The archive's own meta.ini and fomod folder are not copied.

An installed mod is left alone unless --force. Run with MO2 closed (it rewrites the profile on folder changes).

Usage:  python 00-install-sources.py [<modlist root>] [--force]
"""
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpu_sources as fs  # noqa: E402


def seven_zip():
    return shutil.which('7z') or 'C:/Program Files/7-Zip/7z.exe'


DATA_DIRS = {'meshes', 'sound', 'textures', 'skse', 'scripts', 'interface', 'seq'}


def data_root(tmp):
    """The shallowest folder that holds a data folder or a plugin."""
    best = None
    for dp, dn, fn in os.walk(tmp):
        if any(d.lower() in DATA_DIRS for d in dn) or any(f.lower().endswith(('.esp', '.esm', '.esl')) for f in fn):
            depth = os.path.relpath(dp, tmp).count(os.sep)
            if best is None or depth < best[0]:
                best = (depth, dp)
    if best is None:
        raise SystemExit(f'no data folder or plugin in {tmp}')
    return best[1]


def write_meta_ini(path, src, archive):
    mod_id, file_id, version = src['nexus']
    lines = ['[General]', 'gameName=SkyrimSE', f'modid={mod_id}', f'version={version}', f'newestVersion={version}',
             'category="-1,"', 'nexusFileStatus=1', f'installationFile={archive}', 'repository=Nexus',
             'ignoredVersion=', 'comments=', 'notes=Installed by src/FirstPersonUnarmedStances/tools/'
             '00-install-sources.py; gated per stance by ' + fs.OVERLAY_MOD, 'url=', 'hasCustomURL=false',
             'converted=false', 'validated=false', '', '[installedFiles]', f'1\\modid={mod_id}',
             f'1\\fileid={file_id}', 'size=1']
    with open(path, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def main():
    force = '--force' in sys.argv
    for src in fs.SOURCES.values():
        hits = sorted(f for f in fnmatch.filter(os.listdir(fs.DOWNLOADS), src['glob']) if not f.endswith('.meta'))
        if not hits:
            raise SystemExit(f'{src["glob"]} not in {fs.DOWNLOADS}')
        archive = hits[-1]
        dest = os.path.join(fs.MODS, src['mod'])
        if os.path.isdir(dest) and not force:
            print(f'{src["mod"]}: already installed, left alone')
            continue
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        with tempfile.TemporaryDirectory(prefix='zen_fpu_') as tmp:
            subprocess.run([seven_zip(), 'x', '-y', f'-o{tmp}', os.path.join(fs.DOWNLOADS, archive)], check=True,
                           stdout=subprocess.DEVNULL)
            root = data_root(tmp)
            n = 0
            for dp, _dn, fn in os.walk(root):
                for f in fn:
                    rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/')
                    if rel.lower() == 'meta.ini' or rel.lower().startswith('fomod/'):
                        continue
                    out = os.path.join(dest, *rel.split('/'))
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    shutil.copyfile(os.path.join(dp, f), out)
                    n += 1
        write_meta_ini(os.path.join(dest, 'meta.ini'), src, archive)
        print(f'{src["mod"]}: installed {n} files from {archive}')


if __name__ == '__main__':
    main()
