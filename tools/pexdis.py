"""Minimal Skyrim .pex disassembler: properties, variables and every function's instructions with resolved names.
Usage: python pexdis.py <file.pex>"""
import struct, sys

OPS = [('nop', 0), ('iadd', 3), ('fadd', 3), ('isub', 3), ('fsub', 3), ('imul', 3), ('fmul', 3), ('idiv', 3),
       ('fdiv', 3), ('imod', 3), ('not', 2), ('ineg', 2), ('fneg', 2), ('assign', 2), ('cast', 2), ('cmp_eq', 3),
       ('cmp_lt', 3), ('cmp_le', 3), ('cmp_gt', 3), ('cmp_ge', 3), ('jmp', 1), ('jmpt', 2), ('jmpf', 2),
       ('callmethod', 3), ('callparent', 2), ('callstatic', 3), ('return', 1), ('strcat', 3), ('propget', 3),
       ('propset', 3), ('array_create', 2), ('array_length', 2), ('array_getelement', 3), ('array_setelement', 3),
       ('array_findelement', 4), ('array_rfindelement', 4)]
VARARG = {'callmethod', 'callparent', 'callstatic'}


class R:
    def __init__(self, b): self.b, self.p = b, 0
    def u(self, fmt):
        v = struct.unpack_from('>' + fmt, self.b, self.p); self.p += struct.calcsize('>' + fmt); return v[0]
    def ws(self):
        n = self.u('H'); s = self.b[self.p:self.p + n].decode('latin-1'); self.p += n; return s


def main(path):
    r = R(open(path, 'rb').read())
    assert r.u('I') == 0xFA57C0DE
    r.u('B'); r.u('B'); r.u('H'); r.u('Q'); r.ws(); r.ws(); r.ws()
    st = [r.ws() for _ in range(r.u('H'))]
    S = lambda: st[r.u('H')]
    if r.u('B'):
        r.u('Q')
        for _ in range(r.u('H')):
            r.u('H'); r.u('H'); r.u('H'); r.u('B'); n = r.u('H'); r.p += 2 * n
    for _ in range(r.u('H')):
        r.u('H'); r.u('B')

    def var():
        t = r.u('B')
        if t == 0: return 'None'
        if t == 1: return S()
        if t == 2: return repr(S())
        if t == 3: return str(r.u('i'))
        if t == 4: return repr(round(r.u('f'), 4))
        if t == 5: return str(bool(r.u('B')))
        raise ValueError(t)

    def func(name):
        ret = S(); S(); r.u('I'); r.u('B')
        params = [(S(), S()) for _ in range(r.u('H'))]
        locs = [(S(), S()) for _ in range(r.u('H'))]
        print(f'\n  {ret} {name}(' + ', '.join(f'{t} {n}' for n, t in params) + ')')
        if locs: print('    locals: ' + ', '.join(f'{t} {n}' for n, t in locs))
        for i in range(r.u('H')):
            op, n = OPS[r.u('B')]
            args = [var() for _ in range(n)]
            if op in VARARG:
                cnt = int(var()); args += [var() for _ in range(cnt)]
            print(f'    {i:3} {op:16} ' + ', '.join(args))

    for _ in range(r.u('H')):
        name = S(); r.u('I')
        parent = S(); doc = S(); r.u('I'); auto = S()
        print(f'Scriptname {name} extends {parent}  (auto state {auto!r})')
        if doc: print('  doc:', doc[:300])
        for _ in range(r.u('H')):
            n, t = S(), S(); r.u('I'); v = var(); print(f'  var {t} {n} = {v}')
        for _ in range(r.u('H')):
            n, t = S(), S(); S(); r.u('I'); fl = r.u('B')
            if fl & 4: print(f'  property {t} {n} (auto -> {S()})')
            else:
                print(f'  property {t} {n} (full)')
                if fl & 1: func(f'{n}.Get')
                if fl & 2: func(f'{n}.Set')
        for _ in range(r.u('H')):
            sname = S()
            print(f'\n state {sname!r}:')
            for _ in range(r.u('H')):
                func(S())


if __name__ == '__main__':
    main(sys.argv[1])
