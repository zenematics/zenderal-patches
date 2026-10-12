import struct,sys
def lz4_block(src, out_len):
    dst=bytearray(); i=0; n=len(src)
    while i<n:
        tok=src[i]; i+=1
        lit=tok>>4
        if lit==15:
            while True:
                b=src[i]; i+=1; lit+=b
                if b!=255: break
        dst+=src[i:i+lit]; i+=lit
        if i>=n: break
        off=src[i]|(src[i+1]<<8); i+=2
        ml=tok&15
        if ml==15:
            while True:
                b=src[i]; i+=1; ml+=b
                if b!=255: break
        ml+=4; start=len(dst)-off
        if off>=ml: dst+=dst[start:start+ml]
        else:
            for k in range(ml): dst.append(dst[start+k])
    assert len(dst)==out_len,(len(dst),out_len)
    return bytes(dst)
class R:
    def __init__(s,b,p=0): s.b=b; s.p=p
    def u8(s): v=s.b[s.p]; s.p+=1; return v
    def u16(s): v=struct.unpack_from('<H',s.b,s.p)[0]; s.p+=2; return v
    def u32(s): v=struct.unpack_from('<I',s.b,s.p)[0]; s.p+=4; return v
    def i32(s): v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def u64(s): v=struct.unpack_from('<Q',s.b,s.p)[0]; s.p+=8; return v
    def f32(s): v=struct.unpack_from('<f',s.b,s.p)[0]; s.p+=4; return v
    def raw(s,n): v=s.b[s.p:s.p+n]; s.p+=n; return v
    def ws(s): n=s.u16(); return s.raw(n).decode('utf-8','replace')
def load(path):
    d=open(path,'rb').read(); r=R(d)
    assert r.raw(13)==b'TESV_SAVEGAME'
    hsize=r.u32(); h0=r.p
    hdr=dict(version=r.u32(),saveNumber=r.u32(),name=r.ws(),level=r.u32(),location=r.ws(),gameDate=r.ws(),race=r.ws(),sex=r.u16(),exp=r.f32(),lvlexp=r.f32(),ft=r.u64(),w=r.u32(),hgt=r.u32(),comp=r.u16())
    assert r.p==h0+hsize,(r.p,h0,hsize)
    r.p+=hdr['w']*hdr['hgt']*4
    ulen=r.u32(); clen=r.u32()
    body=lz4_block(d[r.p:r.p+clen],ulen) if hdr['comp']==2 else d[r.p:]
    return hdr,body
if __name__=='__main__':
    hdr,body=load(sys.argv[1]); print(hdr); b=R(body)
    fv=b.u8(); pis=b.u32(); p0=b.p; cnt=b.u8(); plugins=[b.ws() for _ in range(cnt)]
    light=[]
    if b.p<p0+pis: lc=b.u16(); light=[b.ws() for _ in range(lc)]
    assert b.p==p0+pis,(b.p,p0,pis)
    print('formVersion',fv,'full plugins',len(plugins),'light',len(light)); print(plugins[:6],'...',light[:4])
