"""Orthographic textured renderer for .bbmodel files (ZYX Euler, nested group rotation)."""
import json, base64, io, math, sys
import numpy as np
from PIL import Image
def rot(r):
    x,y,z=[math.radians(a) for a in (r or [0,0,0])]
    cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz@Ry@Rx
def affine(r,o):
    M=np.eye(4);R=rot(r);o=np.array(o,float);M[:3,:3]=R;M[:3,3]=o-R@o;return M
def cube_world(d):
    """uuid -> world matrix incl. group + cube rotation"""
    els={e['uuid']:e for e in d['elements']};grp={g['uuid']:g for g in d['groups']};out={}
    def walk(n,P):
        for c in n:
            if isinstance(c,str):
                e=els[c];out[c]=P@affine(e.get('rotation'),e.get('origin',[0,0,0]))
            else:
                g=grp[c['uuid']];walk(c.get('children',[]),P@affine(g.get('rotation'),g['origin']))
    walk(d['outliner'],np.eye(4));return out
# corners per face: top-left, top-right, bottom-left as seen from outside (uv orientation)
def face_corners(a,b):
    x0,y0,z0=a;x1,y1,z1=b
    return {'south':((x0,y1,z1),(x1,y1,z1),(x0,y0,z1),(0,0,1)),'north':((x1,y1,z0),(x0,y1,z0),(x1,y0,z0),(0,0,-1)),
     'east':((x1,y1,z1),(x1,y1,z0),(x1,y0,z1),(1,0,0)),'west':((x0,y1,z0),(x0,y1,z1),(x0,y0,z0),(-1,0,0)),
     'up':((x0,y1,z0),(x1,y1,z0),(x0,y1,z1),(0,1,0)),'down':((x0,y0,z1),(x1,y0,z1),(x0,y0,z0),(0,-1,0))}
def load_tex(d,fallback=None):
    t=d['textures'][0];s=t.get('source','')
    if s.startswith('data:'): im=Image.open(io.BytesIO(base64.b64decode(s.split(',',1)[1])))
    else: im=Image.open(fallback)
    return np.array(im.convert('RGBA')),t.get('uv_width',im.width),t.get('uv_height',im.height)
def render(d,tex,view,ppu=6,bounds=(-48,48,-4,132),only=None,tint=None,hide=()):
    """view: 3x3 matrix mapping world to (screen-right, screen-up, toward-viewer)"""
    T,uw,uh=tex;tw,th=T.shape[1],T.shape[0];W=cube_world(d);l,r,b,t=bounds
    w,h=int((r-l)*ppu),int((t-b)*ppu);img=np.zeros((h,w,3),np.uint8);img[:]=(40,42,48);zb=np.full((h,w),-1e9)
    L=np.array([.25,.45,.85]);L/=np.linalg.norm(L)
    for e in d['elements']:
        if e['uuid'] in hide or e.get('visibility') is False: continue
        M=W[e['uuid']];R=M[:3,:3]
        for fn,(tl,tr,bl,n) in face_corners(e['from'],e['to']).items():
            f=e['faces'].get(fn)
            if not f or f.get('texture') is None or f['uv'][0]==f['uv'][2]==0==f['uv'][1]==f['uv'][3]: continue
            N=view@R@np.array(n,float)
            if N[2]<=1e-6: continue
            pts=[view@(M[:3,:3]@np.array(p,float)+M[:3,3]) for p in (tl,tr,bl)]
            o,ex,ey=pts[0],pts[1]-pts[0],pts[2]-pts[0]
            A=np.array([[ex[0],ey[0]],[ex[1],ey[1]]])
            if abs(np.linalg.det(A))<1e-9: continue
            Ai=np.linalg.inv(A);c=[o,o+ex,o+ey,o+ex+ey]
            x0=max(0,int((min(p[0] for p in c)-l)*ppu)-1);x1=min(w,int((max(p[0] for p in c)-l)*ppu)+2)
            y0=max(0,int((t-max(p[1] for p in c))*ppu)-1);y1=min(h,int((t-min(p[1] for p in c))*ppu)+2)
            if x0>=x1 or y0>=y1: continue
            xs,ys=np.meshgrid(np.arange(x0,x1),np.arange(y0,y1));wx=l+(xs+.5)/ppu;wy=t-(ys+.5)/ppu
            s=Ai[0,0]*(wx-o[0])+Ai[0,1]*(wy-o[1]);q=Ai[1,0]*(wx-o[0])+Ai[1,1]*(wy-o[1])
            mask=(s>=0)&(s<1)&(q>=0)&(q<1);
            if not mask.any(): continue
            z=o[2]+s*ex[2]+q*ey[2]
            u1,v1,u2,v2=f['uv'];rt=f.get('rotation',0) or 0
            ss,qq=s,q
            if rt==90: ss,qq=q,1-s
            elif rt==180: ss,qq=1-s,1-q
            elif rt==270: ss,qq=1-q,s
            uu=(u1+(u2-u1)*ss)*tw/uw;vv=(v1+(v2-v1)*qq)*th/uh
            tx=np.clip(uu.astype(int),0,tw-1);ty=np.clip(vv.astype(int),0,th-1);col=T[ty,tx]
            nw=R@np.array(n,float);sh=.72+.28*max(0,float(nw@L))
            m=mask&(col[...,3]>32)&(z>zb[y0:y1,x0:x1])
            sub=img[y0:y1,x0:x1];rgb=(col[...,:3]*sh).astype(np.uint8)
            if tint and e['uuid'] in tint: rgb=(rgb*.5+np.array(tint[e['uuid']])*.5).astype(np.uint8)
            sub[m]=rgb[m];zb[y0:y1,x0:x1][m]=z[m]
    return Image.fromarray(img)
FRONT=np.eye(3)
SIDE=np.array([[0,0,1],[0,1,0],[-1,0,0]],float)  # viewer on the imp's +X side; +Z (front) is screen-right
SIDE_L=SIDE
def yaw(deg,pitch=0):
    a=math.radians(deg);p=math.radians(pitch)
    Y=np.array([[math.cos(a),0,-math.sin(a)],[0,1,0],[math.sin(a),0,math.cos(a)]])
    X=np.array([[1,0,0],[0,math.cos(p),-math.sin(p)],[0,math.sin(p),math.cos(p)]]);return X@Y
