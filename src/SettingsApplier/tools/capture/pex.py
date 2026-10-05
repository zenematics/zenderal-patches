import struct
class B:
    def __init__(s,d): s.d=d; s.p=0
    def u8(s): v=s.d[s.p]; s.p+=1; return v
    def u16(s): v=struct.unpack_from('>H',s.d,s.p)[0]; s.p+=2; return v
    def u32(s): v=struct.unpack_from('>I',s.d,s.p)[0]; s.p+=4; return v
    def i32(s): v=struct.unpack_from('>i',s.d,s.p)[0]; s.p+=4; return v
    def f32(s): v=struct.unpack_from('>f',s.d,s.p)[0]; s.p+=4; return v
    def u64(s): s.p+=8
    def ws(s): n=s.u16(); v=s.d[s.p:s.p+n].decode('latin1'); s.p+=n; return v
def defaults(path):
    r=B(open(path,'rb').read())
    assert r.u32()==0xFA57C0DE
    r.u8(); r.u8(); r.u16(); r.u64(); r.ws(); r.ws(); r.ws()
    n=r.u16(); S=[r.ws() for _ in range(n)]
    if r.u8():
        r.u64(); fc=r.u16()
        for _ in range(fc):
            r.u16(); r.u16(); r.u16(); r.u8(); ic=r.u16(); r.p+=2*ic
    uf=r.u16(); r.p+=3*uf
    oc=r.u16(); out={}
    for _ in range(oc):
        name=S[r.u16()]; size=r.u32(); start=r.p
        r.u16(); r.u16(); r.u32(); r.u16()
        nv=r.u16()
        for _ in range(nv):
            vn=S[r.u16()]; vt=S[r.u16()]; r.u32(); t=r.u8()
            if t==0: v=None
            elif t==1: v=('ident',S[r.u16()])
            elif t==2: v=S[r.u16()]
            elif t==3: v=r.i32()
            elif t==4: v=round(r.f32(),6)
            elif t==5: v=bool(r.u8())
            else: raise ValueError(t)
            out[vn.lower()]=(vt,v)
        r.p=start+size-4
    return out
