import struct,os,sys,re
def lz4_into(src,dst):
    i=0;n=len(src)
    while i<n:
        tok=src[i];i+=1;lit=tok>>4
        if lit==15:
            while True:
                b=src[i];i+=1;lit+=b
                if b!=255:break
        dst+=src[i:i+lit];i+=lit
        if i>=n:break
        off=src[i]|(src[i+1]<<8);i+=2;ml=tok&15
        if ml==15:
            while True:
                b=src[i];i+=1;ml+=b
                if b!=255:break
        ml+=4;st=len(dst)-off
        if off>=ml: dst+=dst[st:st+ml]
        else:
            for k in range(ml): dst.append(dst[st+k])
def lz4_frame(d):
    assert struct.unpack_from('<I',d,0)[0]==0x184D2204
    flg=d[4];p=7+(8 if flg&8 else 0)
    out=bytearray()
    while True:
        bs=struct.unpack_from('<I',d,p)[0];p+=4
        if bs==0:break
        raw=bs&0x80000000;bs&=0x7FFFFFFF
        blk=d[p:p+bs];p+=bs
        if raw: out+=blk
        else: lz4_into(blk,out)
        if flg&0x10:p+=4
    return bytes(out)
def extract(path,pattern,outdir):
    d=open(path,'rb').read()
    magic,ver,fro,aflags,fcount,filecount,tfnl,tfil,ff=struct.unpack_from('<4sIIIIIIII',d,0)
    assert magic==b'BSA\x00' and ver==105,(magic,ver)
    p=fro;folders=[]
    for _ in range(fcount):
        h,c,pad,off=struct.unpack_from('<QIIQ',d,p);p+=24;folders.append(c)
    files=[]
    for c in folders:
        ln=d[p];name=d[p+1:p+ln].rstrip(b'\0').decode('latin1');p+=1+ln
        for _ in range(c):
            h,size,off=struct.unpack_from('<QII',d,p);p+=16;files.append([name,size,off])
    names=d[p:p+tfil].split(b'\0')
    got=[]
    for f,n in zip(files,names):
        full=(f[0]+chr(92)+n.decode('latin1')).lower()
        if not re.search(pattern,full): continue
        size=f[1];off=f[2];comp=bool(aflags&4)^bool(size&0x40000000);size&=0x3FFFFFFF
        q=off
        if aflags&0x100: ln=d[q];q+=1+ln;size-=1+ln
        blob=d[q:q+size]
        data=lz4_frame(blob[4:]) if comp else blob
        if comp: assert len(data)==struct.unpack_from('<I',blob,0)[0]
        o=os.path.join(outdir,os.path.basename(full));open(o,'wb').write(data);got.append(full)
    return got
if __name__=='__main__':
    for b in sys.argv[2:]: print(b.split('/')[-1],extract(b,sys.argv[1],'bsa'))
