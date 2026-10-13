"""Install Dint999's hair packs into the Zenderal MO2 instance as HAIRS ONLY.

Both packs ship every hairstyle twice: as a RaceMenu hair (HDPT) and as a wearable wig
(ARMO/ARMA + TXST, crafted at the forge from COBJ recipes gated on BOOK records). Zenderal
wants only the hairs. HairPack02 also overrides Riften's Bee and Barb (CELL 016BDF:Skyrim.esm)
to place its crafting books - that cell does not exist in Enderal, so the override would
inject a broken interior cell.

For each pack this script:
  1. extracts the archive from <modlist>/downloads (Wabbajack sources it from the
     whitelisted Google Drive / MediaFire link recorded in the .meta),
  2. serializes the plugin with Spriggit, deletes every group except HeadParts, and asserts
     the exact group/record counts of the known upstream version,
  3. deserializes it under the ORIGINAL filename (keeps head part FormIDs, so saved
     characters and RaceMenu presets keep their hair) and asserts the rebuilt plugin
     re-serializes to HeadParts only, with the same count,
  4. copies only the assets the head parts reach: HDPT Model/Parts paths, then every
     .nif/.dds/.xml/.tri named inside a kept .nif/.xml, transitively, plus the BodySlide
     projects that build a kept mesh (RaceMenu collision proxies).

Nothing here is committed: the plugins and assets are Dint999's. Wabbajack rebuilds the
stripped .esp as a binary patch against the original in the archive.

Usage: python -I 01-build-hairs-only.py [--modlist E:/Zenderal]
"""
import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile

PACKS = [
    {
        'archive': '[Dint999] BDOR Hairs SSE 0.23.7z',
        'plugin': '[Dint999] BDOr_Hairstyles.esp',
        'mod': '[Dint999] BDOR Hairs - Hairs Only',
        'groups': {'ArmorAddons': 89, 'Armors': 89, 'Books': 1, 'ConstructibleObjects': 177,
                   'HeadParts': 1136, 'TextureSets': 88},
        'selectable': 141,
    },
    {
        'archive': '[Dint999] HairPack02 SSE 1.12 (base).7z',
        'plugin': '[dint999] HairPack02.esp',
        'mod': '[Dint999] HairPack02 - Hairs Only',
        'groups': {'ArmorAddons': 95, 'Armors': 95, 'Books': 2, 'Cells': None,
                   'ConstructibleObjects': 190, 'HeadParts': 2468, 'TextureSets': 86},
        'selectable': 220,
    },
]
SEVEN_ZIP = r'C:\Program Files\7-Zip\7z.exe'
BS = chr(92)


def fail(msg):
    sys.exit('FAIL: ' + msg)


def tools():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    t = json.load(open(os.path.join(root, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
    return t['spriggitCli'], t['spriggit']


def spriggit(cli, cfg, verb, src, dst):
    args = [cli, verb, '--InputPath', src, '--OutputPath', dst,
            '--PackageName', cfg['packageName'], '--PackageVersion', cfg['packageVersion']]
    if verb == 'serialize':  # deserialize reads the release from the tree's spriggit-meta.json
        args += ['--GameRelease', cfg['gameRelease']]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        fail('spriggit %s %s\n%s%s' % (verb, src, r.stdout[-2000:], r.stderr[-2000:]))


def count_groups(tree):
    out = {}
    for g in os.listdir(tree):
        p = os.path.join(tree, g)
        if os.path.isdir(p):
            out[g] = len(glob.glob(p + '/**/*.yaml', recursive=True))
    return out


def selectable(tree):
    n = 0
    for f in glob.glob(tree + '/HeadParts/*.yaml'):
        t = open(f, encoding='utf-8').read()
        fl = re.search(r'^Flags:\n((?:- .*\n)+)', t, re.M)
        fl = fl.group(1) if fl else ''
        if 'Playable' in fl and 'IsExtraPart' not in fl:
            n += 1
    return n


def needed_assets(tree, ex):
    norm = lambda p: p.replace(BS, '/')
    idx = {}
    for r, _, fs in os.walk(ex):
        for f in fs:
            p = norm(os.path.relpath(os.path.join(r, f), ex))
            idx[p.lower()] = p

    def res(path, prefixes):
        p = norm(path).lower().lstrip('/')
        if p.startswith('data/'):
            p = p[5:]
        for pre in prefixes:
            q = p if p.startswith(pre) else pre + p
            if q in idx:
                return idx[q]
        return None

    need, queue = set(), []
    for f in glob.glob(tree + '/HeadParts/*.yaml'):
        for m in re.findall(r'^\s*(?:File|FileName): (.+?)\s*$', open(f, encoding='utf-8').read(), re.M):
            r = res(m, ['meshes/'])
            if r:
                queue.append(r)
    pat = re.compile(rb'[\x20-\x7e]{4,}?\.(?:dds|xml|nif|tri)', re.I)
    while queue:
        p = queue.pop()
        if p in need:
            continue
        need.add(p)
        if p.lower().endswith(('.nif', '.xml')):
            for s in pat.findall(open(os.path.join(ex, p), 'rb').read()):
                s = re.split(r'[\x00-\x1f"<>=]', s.decode('ascii', 'replace'))[-1].strip()
                r = res(s, ['', 'meshes/', 'textures/'])
                if r:
                    queue.append(r)
    for o in glob.glob(ex + '/CalienteTools/**/*.osp', recursive=True):
        t = open(o, encoding='utf-8', errors='replace').read()
        for blk in re.findall(r'<SliderSet.*?</SliderSet>', t, re.S):
            op = re.search(r'<OutputPath>(.*?)</OutputPath>', blk)
            of = re.search(r'<OutputFile[^>]*>(.*?)</OutputFile>', blk)
            if not (op and of):
                continue
            base = norm(op.group(1)) + '/' + of.group(1)
            if any(res(base + s, ['meshes/']) in need for s in ('.nif', '_0.nif', '_1.nif')):
                need.add(norm(os.path.relpath(o, ex)))
                df = re.search(r'<DataFolder>(.*?)</DataFolder>', blk)
                if df:
                    pre = 'calientetools/bodyslide/shapedata/' + norm(df.group(1)).lower() + '/'
                    need |= {v for k, v in idx.items() if k.startswith(pre)}
    need |= {v for k, v in idx.items() if k.startswith('textures/cubemaps/')}
    return need


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modlist', default='E:/Zenderal')
    a = ap.parse_args()
    cli, cfg = tools()
    for pk in PACKS:
        arc = os.path.join(a.modlist, 'downloads', pk['archive'])
        if not os.path.isfile(arc):
            fail('missing download ' + arc)
        work = tempfile.mkdtemp(prefix='dint-')
        try:
            ex = os.path.join(work, 'ex')
            if subprocess.run([SEVEN_ZIP, 'x', '-y', '-o' + ex, arc], capture_output=True).returncode:
                fail('extract ' + arc)
            tree = os.path.join(work, 'yaml')
            spriggit(cli, cfg, 'serialize', os.path.join(ex, pk['plugin']), tree)
            got = count_groups(tree)
            for g, n in pk['groups'].items():
                if g not in got or (n is not None and got[g] != n):
                    fail('%s: group %s has %s records, expected %s (upstream changed?)' % (pk['plugin'], g, got.get(g), n))
            if set(got) != set(pk['groups']):
                fail('%s: unexpected groups %s' % (pk['plugin'], sorted(set(got) - set(pk['groups']))))
            if selectable(tree) != pk['selectable']:
                fail('%s: %d selectable hairs, expected %d' % (pk['plugin'], selectable(tree), pk['selectable']))
            for g in got:
                if g != 'HeadParts':
                    shutil.rmtree(os.path.join(tree, g))
            leftovers = [l for f in glob.glob(tree + '/HeadParts/*.yaml')
                         for l in re.findall(r'\b[0-9A-F]{6}:(.+?\.es[mp])\s*$', open(f, encoding='utf-8').read(), re.M)
                         if l not in ('Skyrim.esm', pk['plugin'])]
            if leftovers:
                fail('head parts reference unexpected plugins: %s' % sorted(set(leftovers)))

            mod = os.path.join(a.modlist, 'mods', pk['mod'])
            if os.path.exists(mod):
                shutil.rmtree(mod)
            os.makedirs(mod)
            spriggit(cli, cfg, 'deserialize', tree, os.path.join(mod, pk['plugin']))
            check = os.path.join(work, 'check')
            spriggit(cli, cfg, 'serialize', os.path.join(mod, pk['plugin']), check)
            if count_groups(check) != {'HeadParts': pk['groups']['HeadParts']}:
                fail('rebuilt %s re-serializes to %s' % (pk['plugin'], count_groups(check)))

            keep = needed_assets(tree, ex)
            for rel in keep:
                dst = os.path.join(mod, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(ex, rel), dst)
            ext = collections.Counter(p.rsplit('.', 1)[-1].lower() for p in keep)
            with open(os.path.join(mod, 'meta.ini'), 'w', encoding='utf-8') as f:
                f.write('[General]\ninstallationFile=%s\ncomments=Zenderal: hairs only, wigs/recipes/books stripped by src/DintHairs/tools/01-build-hairs-only.py\n' % pk['archive'])
            print('%s: %d hairs (%d head parts), %d asset files %s -> %s'
                  % (pk['plugin'], pk['selectable'], pk['groups']['HeadParts'], len(keep), dict(ext), mod))
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
