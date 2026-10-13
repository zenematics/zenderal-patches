"""Diff the player's saved animation-graph state (active states + every graph variable) between two .ess saves.
Usage: python -I graphdiff.py <broken.ess> <working.ess>   (run from this folder; uses ess.py)"""
import sys,struct,zlib,re
sys.path.insert(0, __import__("os").path.dirname(__file__))
from ess import load,R
def vsval(r):
    b=r.u8(); t=b&3
    if t==0: return b>>2
    if t==1: return (b|r.u8()<<8)>>2
    return (b|r.u8()<<8|r.u8()<<16)>>2
def save(path):
    hdr,body=load(path); b=R(body)
    fv=b.u8(); pis=b.u32(); p0=b.p; cnt=b.u8(); full=[b.ws() for _ in range(cnt)]
    lc=b.u16(); light=[b.ws() for _ in range(lc)]
    b.p=p0+pis
    names=["fida","u3","g1","g2","cf","g3","g1c","g2c","g3c","cfc"]
    flt={n:b.u32() for n in names}
    # delta: find g1
    for o in range(0,400000):
        if body[o:o+4]==b'\0\0\0\0':
            ln=struct.unpack_from('<I',body,o+4)[0]; q=o+8+ln
            if 0<ln<100000 and struct.unpack_from('<I',body,q)[0]==1: delta=flt['g1']-o; break
    r=R(body,flt['fida']-delta); n=r.u32(); fids=[r.u32() for _ in range(n)]
    def fid(ref):
        t=ref>>22; v=ref&0x3FFFFF
        if t==0: return fids[v-1] if v else 0
        if t==1: return v
        return 0xFF000000|v
    def pname(f):
        i=f>>24
        if i==0xFE: return light[(f>>12)&0xFFF]+":%03X"%(f&0xFFF)
        if i==0xFF: return "created:%06X"%(f&0xFFFFFF)
        return (full[i] if i<len(full) else "?%d"%i)+":%06X"%(f&0xFFFFFF)
    # globals table 1 type 3
    r=R(body,flt['g1']-delta); glob={}
    for _ in range(flt['g1c']):
        t=r.u32(); ln=r.u32(); st=r.p
        if t==3:
            rr=R(body,st); c=vsval(rr)
            for _ in range(c):
                ref=rr.u8()<<16|rr.u8()<<8|rr.u8(); v=rr.f32(); glob[pname(fid(ref))]=v
        r.p=st+ln
    # change forms
    r=R(body,flt['cf']-delta); cfs={}
    for _ in range(flt['cfc']):
        ref=r.u8()<<16|r.u8()<<8|r.u8(); fl=r.u32(); ty=r.u8(); ver=r.u8()
        lt=ty>>6
        rd={0:r.u8,1:r.u16,2:r.u32}[lt]
        l1=rd(); l2=rd(); data=r.raw(l1)
        if l2: data=zlib.decompress(data)
        cfs[fid(ref)]=(fl,ty&0x3F,data)
    return hdr,glob,cfs,pname
def gparse(data):
    i=data.find(b"\x04\x00DMKZ"); out={}
    while True:
        n=struct.unpack_from("<H",data,i)[0]; name=data[i+2:i+2+n]
        if name==b"$-NoMoreVariables-$" or n==0: break
        t=data[i+2+n]; p=i+3+n
        if t==1: out[name.decode()]=data[p:p+4]; i=p+4
        elif t==0: out[name.decode()]=data[p:p+16]; i=p+16
        else: break
    return out
def states(data):
    a=data.find(b"BShkbAnimationGraph"); b=data.find(b"\x04\x00DMKZ")
    return [m.group().decode() for m in re.finditer(rb"[ -~]{4,}",data[a:b])]
def show(v):
    if v is None: return "-"
    if len(v)==4:
        i=struct.unpack("<i",v)[0]
        return str(i) if abs(i)<100000 else "%.4g"%struct.unpack("<f",v)[0]
    return " ".join("%.3g"%x for x in struct.unpack("<4f",v))
A=save(sys.argv[1]); B=save(sys.argv[2])
da=A[2][0x14][2]; db=B[2][0x14][2]
print("A",A[0]['saveNumber'],"B",B[0]['saveNumber'])
sa=states(da); sb=states(db)
print("== states A only:",[s for s in sa if s not in sb]); print("== states B only:",[s for s in sb if s not in sa])
va=gparse(da); vb=gparse(db); print(len(va),len(vb))
skip=re.compile(r"Pitch|TDM_|Turn|Speed|Velocity|Time|Direction|Location|Roll|Collision|Head|Look|CPR_|Cam|camera|Blend|blend|Aim|Damped|Sampled")
for k in sorted(set(va)|set(vb)):
    if va.get(k)!=vb.get(k) and not skip.search(k): print("  %-32s A=%-14s B=%s"%(k,show(va.get(k)),show(vb.get(k))))
