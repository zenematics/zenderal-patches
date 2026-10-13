"""Rebuild the live `Apocalypse - Magic of Skyrim.esp` WITHOUT its leftover Skyrim NAVI record.

Why: the plugin carries vanilla Skyrim's NavigationMeshInfoMap at FormID 012FB4:Skyrim.esm. In Enderal
that ID is a placed REFR - the Forgotten Temple floor tile `DweRmLgMid01` at (-2560, 8576, 2368) in
cell `ForgottenTemple 012C3B`. The NAVI override replaces the tile, so the floor never loads (no render,
no collision) and players fall through a hole. The NAVI only indexes navmeshes in Skyrim's Tamriel
(00003C, which is MQP01Home in Enderal) and two of Apocalypse's own cells, so dropping it loses nothing.

HOTFIX: the real fix belongs in the enderal-mods repo's Apocalypse tree. Retire this once that ships.

Output is a separate MO2 mod holding only the rebuilt .esp; it must sort ABOVE `Apocalypse - Enderal
Patch` (the current winner of the filename) so it wins the file conflict. Apocalypse's BSAs keep loading
because the filename is unchanged.

Usage: python 01-rebuild-without-navi.py [<source esp>] [<mods dir>]
"""
import filecmp, json, os, shutil, struct, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOLS = json.load(open(os.path.join(REPO, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
CLI = TOOLS['spriggitCli']
ESP = 'Apocalypse - Magic of Skyrim.esp'
MOD = 'Zenderal - Apocalypse NAVI Fix'
NAVI = os.path.join('NavigationMeshInfoMaps', '012FB4_Skyrim.esm.yaml')

src = sys.argv[1] if len(sys.argv) > 1 else f'E:/Zenderal/mods/Apocalypse - Enderal Patch/{ESP}'
mods = sys.argv[2] if len(sys.argv) > 2 else 'E:/Zenderal/mods'
out_esp = os.path.join(mods, MOD, ESP)


def spriggit(*args):
    r = subprocess.run([CLI, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'spriggit {args[0]} failed:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}')


def serialize(esp, outdir):
    spriggit('serialize', '--InputPath', esp, '--OutputPath', outdir, '--GameRelease', 'EnderalSE',
             '--PackageName', 'Spriggit.Yaml.Skyrim', '--PackageVersion', '0.40.0')


def header(path):
    d = open(path, 'rb').read(4096)
    size, flags = struct.unpack_from('<II', d, 4)
    hedr = d.find(b'HEDR')
    ver, nrec, nextid = struct.unpack_from('<fII', d, hedr + 6)
    masters, q = [], 24
    while q < 24 + size:
        t, sz = d[q:q + 4], struct.unpack_from('<H', d, q + 4)[0]
        if t == b'MAST':
            masters.append(d[q + 6:q + 6 + sz].rstrip(b'\0').decode('latin1'))
        q += 6 + sz
    return dict(flags=hex(flags), version=round(ver, 2), records=nrec, nextid=hex(nextid), masters=masters)


def tree(root):
    return {os.path.relpath(os.path.join(dp, f), root) for dp, dn, fn in os.walk(root) for f in fn}


tmp = tempfile.mkdtemp(prefix='apocnavi-')
try:
    a = os.path.join(tmp, 'orig'); serialize(src, a)
    assert os.path.isfile(os.path.join(a, NAVI)), f'{NAVI} not in source - already fixed upstream?'
    navdir = os.path.join(a, 'NavigationMeshInfoMaps')
    assert os.listdir(navdir) == [os.path.basename(NAVI)], os.listdir(navdir)
    shutil.rmtree(navdir)

    os.makedirs(os.path.dirname(out_esp), exist_ok=True)
    spriggit('deserialize', '--InputPath', a, '--OutputPath', out_esp)

    # Prove the rebuild: re-serialize it and require the tree to match the edited one file-for-file.
    b = os.path.join(tmp, 'rebuilt'); serialize(out_esp, b)
    ta, tb = tree(a), tree(b)
    assert ta == tb, f'file sets differ: only-orig={sorted(ta - tb)[:10]} only-rebuilt={sorted(tb - ta)[:10]}'
    diff = [f for f in sorted(ta) if not filecmp.cmp(os.path.join(a, f), os.path.join(b, f), shallow=False)]
    assert not diff, f'{len(diff)} files differ after round trip: {diff[:10]}'

    ho, hn = header(src), header(out_esp)
    print('source :', ho); print('rebuilt:', hn)
    assert ho['flags'] == hn['flags'] and ho['version'] == hn['version'] and ho['masters'] == hn['masters'], 'header changed'
    raw = open(out_esp, 'rb').read()
    assert b'NAVI' not in raw, 'a NAVI record survived'
    print(f'OK: {len(ta)} record files round-trip identically; NAVI 012FB4 removed -> {out_esp}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
