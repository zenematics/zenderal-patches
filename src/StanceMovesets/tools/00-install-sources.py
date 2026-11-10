"""Install the High/Mid/Low stance sources UNTOUCHED as their own MO2 mods, from MO2's downloads (stance_sources.SOURCES):
each archive's data folder copied byte for byte, plus an MO2 meta.ini. Two exceptions, both path-only: Kick Boxing's
DAR folders 40050-40054 go to 40060-40064 (they collide with Muay Thai's; its author says to renumber), and an
archive's own stray meta.ini is not copied. A download without a .meta (the race packs were downloaded outside MO2)
gets one from SOURCES' Nexus ids, so Wabbajack can source it.

An installed mod is left alone unless --force. Run with MO2 closed (it rewrites the profile on folder changes).

Usage:  python 00-install-sources.py [--force]
"""
import fnmatch
import os
import shutil
import subprocess
import sys
import tempfile

import stance_sources as ss

lsdf = ss.lsdf
MODS, DOWNLOADS = lsdf.MODS, lsdf.DOWNLOADS


def seven_zip():
    return shutil.which('7z') or 'C:/Program Files/7-Zip/7z.exe'


def write_meta_ini(path, src, archive):
    mod_id, file_id, version = src['nexus']
    lines = ['[General]', 'gameName=SkyrimSE', f'modid={mod_id}', f'version={version}', f'newestVersion={version}',
             'category="-1,"', 'nexusFileStatus=1', f'installationFile={archive}', 'repository=Nexus',
             'ignoredVersion=', 'comments=', 'notes=Installed by src/StanceMovesets/tools/00-install-sources.py; '
             'gated per stance by Zenderal - Stance Overlays', 'url=', 'hasCustomURL=false', 'converted=false',
             'validated=false', '', '[installedFiles]', f'1\\modid={mod_id}']
    if file_id:
        lines.append(f'1\\fileid={file_id}')
    lines.append('size=1')
    with open(path, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def write_download_meta(path, src, archive):
    mod_id, file_id, version = src['nexus']
    lines = ['[General]', 'gameName=SkyrimSE', f'modID={mod_id}', f'fileID={file_id}', 'url=',
             f'name={os.path.splitext(archive)[0].split("-" + str(mod_id))[0]}', f'modName={src["mod"]}',
             f'version={version}', 'newestVersion=', 'fileCategory=1', 'repository=Nexus', 'installed=true',
             'uninstalled=false', 'paused=false', 'removed=false']
    with open(path, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def main():
    force = '--force' in sys.argv
    for key, src in ss.SOURCES.items():
        hits = sorted(fnmatch.filter(os.listdir(DOWNLOADS), src['glob']))
        if not hits:
            raise SystemExit(f'{src["glob"]} not in {DOWNLOADS}')
        archive = hits[-1]
        meta = os.path.join(DOWNLOADS, archive + '.meta')
        if not os.path.exists(meta):
            if not src['nexus'][1]:
                raise SystemExit(f'{archive} has no .meta and SOURCES has no Nexus file id for it')
            write_download_meta(meta, src, archive)
            print(f'{archive}: wrote missing .meta (Nexus {src["nexus"][0]} file {src["nexus"][1]})')
        dest = os.path.join(MODS, src['mod'])
        if os.path.isdir(dest) and not force:
            print(f'{src["mod"]}: already installed, left alone')
            continue
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        with tempfile.TemporaryDirectory(prefix='zen_src_') as tmp:
            subprocess.run([seven_zip(), 'x', '-y', f'-o{tmp}', os.path.join(DOWNLOADS, archive)], check=True,
                           stdout=subprocess.DEVNULL)
            root = os.path.join(tmp, *src['root'].split('/')) if src['root'] else tmp
            if not os.path.isdir(root):
                raise SystemExit(f'{archive}: no {src["root"]!r} folder')
            n = 0
            for dp, _dn, fn in os.walk(root):
                for f in fn:
                    rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/')
                    if rel.lower() == 'meta.ini' or rel.lower().startswith('fomod/'):
                        continue
                    parts = rel.split('/')
                    for i, p in enumerate(parts[:-1]):
                        if p.isdigit() and int(p) in src.get('remap', {}) and \
                                '/'.join(parts[:i]).lower() == ss.DAR.lower():
                            parts[i] = str(src['remap'][int(p)])
                    out = os.path.join(dest, *parts)
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    shutil.copyfile(os.path.join(dp, f), out)
                    n += 1
        write_meta_ini(os.path.join(dest, 'meta.ini'), src, archive)
        print(f'{src["mod"]}: installed {n} files from {archive}')


if __name__ == '__main__':
    main()
