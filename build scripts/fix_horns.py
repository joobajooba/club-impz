"""Re-angle the six green_imp horn cubes. Sizes, faces, uuids and everything else stay byte-identical."""
import json, math, re, sys
import numpy as np
from render_bb import rot
# (uuid, name) root -> tip. +X is the imp's left, matching L-Arm/L-Calf/L-Foot in this file.
LEFT =[('a17c5e4c-','horn_l_1'),('6126654c-','horn_l_2'),('211cb554-','horn_l_3')]
RIGHT=[('c0ce4266-','horn_r_1'),('c7bf925f-','horn_r_2'),('9840f7a8-','horn_r_3')]
SIZES=[(9,15,10),(6,13,7),(4,13,4)]
def chain(root,rz,rx,extra=0.4):
    """Left horn: every cube pivots on the centre of its base; each base sits on the joint of the one below.
    Overlap = just enough to bury the child's base corners in the parent on the outside of the bend."""
    out=[];o=np.array(root,float)
    for i,(w,h,d) in enumerate(SIZES):
        r=(rx[i],0,rz[i])
        out.append(dict(origin=o.copy(),size=(w,h,d),rotation=r))
        if i<2:
            cw,cd=SIZES[i+1][0],SIZES[i+1][2]
            dz=math.radians(abs(rz[i+1]-rz[i]));dx=math.radians(abs(rx[i+1]-rx[i]))
            ov=cw/2*math.sin(dz)+cd/2*math.sin(dx)+extra
            o=o+rot(r)@np.array([0,h-ov,0])
            out[-1]['overlap']=ov
    return out
def fields(c,mirror=False):
    w,h,d=c['size'];ox,oy,oz=[round(float(v),5) for v in c['origin']];rx,ry,rz=c['rotation']
    if mirror: ox,ry,rz=-ox,-ry,-rz
    fr=[round(ox-w/2,5),oy,round(oz-d/2,5)]
    return dict(origin=[ox,oy,oz],rotation=[rx,ry,rz],**{'from':fr,'to':[round(fr[0]+w,5),round(oy+h,5),round(fr[2]+d,5)]})
def num(v):
    v=float(v);return str(int(v)) if v==int(v) else repr(v)
def arr(a): return '['+','.join(num(v) for v in a)+']'
def apply(raw,root,rz,rx,**kw):
    L=chain(root,rz,rx,**kw)
    for side,mir in ((LEFT,False),(RIGHT,True)):
        for (uid,name),c in zip(side,L):
            m=re.search(r'"uuid":"'+uid,raw);assert m,uid
            st=raw.rindex('"name":"',0,m.start());seg=raw[st:m.start()]
            assert seg.startswith('"name":"Head"'),seg[:30]
            f=fields(c,mir);new=seg.replace('"name":"Head"','"name":"%s"'%name,1)
            for k in ('from','to','rotation','origin'):
                new,n=re.subn(r'"%s":\[[^\]]*\]'%k,'"%s":%s'%(k,arr(f[k])),new,count=1);assert n==1,k
            raw=raw[:st]+new+raw[m.start():]
    return raw,L
