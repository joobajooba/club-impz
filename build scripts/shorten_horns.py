"""Halve the green_imp horns: 15/13/13 long -> 8/7/6 (whole units), UVs cropped 1:1 so texels don't stretch."""
import json,re,sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / 'godot-game' / 'assets'
import numpy as np
import fix_horns as fh
from render_bb import rot
P=ASSETS/'models'/'impz'/'green_imp.bbmodel'
fh.SIZES=[(9,8,10),(6,7,7),(4,6,4)]
ROOT=(11,86.8,5);RZ=(-58,-30,-8);RX=(0,-4,-8)
KEEP=[('bottom',0),('middle',3),('top',0)]  # which part of each side-face UV stays
NEW={f'horn_{s}_{i+1}':i for s in 'lr' for i in range(3)}
def crop(uv,keep,off,new_h):
    u1,v1,u2,v2=uv;assert v2-v1>new_h
    if keep=='bottom': return [u1,v2-new_h,u2,v2]
    if keep=='top': return [u1,v1,u2,v1+new_h]
    return [u1,v1+off,u2,v1+off+new_h]
def build(raw):
    d=json.loads(raw);L=fh.chain(ROOT,RZ,RX)
    els={e['name']:e for e in d['elements']}
    for n,i in NEW.items():
        e=els[n];f=fh.fields(L[i],n[5]=='r')
        for k in ('from','to','origin'): e[k]=f[k]
        e['rotation']=list(f['rotation'])
        for fn in ('north','east','south','west'):
            e['faces'][fn]['uv']=crop(e['faces'][fn]['uv'],*KEEP[i],fh.SIZES[i][1])
    return d,L
if __name__=='__main__':
    raw=open(P,encoding='utf8',newline='').read();d,L=build(raw)
    # write back text-level so nothing else in the file is reformatted
    out=raw
    for e in d['elements']:
        if e['name'] not in NEW: continue
        m=re.search(r'"uuid":"'+e['uuid'],out);st=out.rindex('"name":"',0,m.start());seg=out[st:m.start()]
        for k in ('from','to','rotation','origin'):
            seg,n=re.subn(r'"%s":\[[^\]]*\]'%k,'"%s":%s'%(k,fh.arr(e[k])),seg,count=1);assert n==1
        for fn in ('north','east','south','west'):
            seg,n=re.subn(r'("%s":\{"uv":)\[[^\]]*\]'%fn,lambda mm:mm.group(1)+fh.arr(e['faces'][fn]['uv']),seg,count=1);assert n==1,fn
        out=out[:st]+seg+out[m.start():]
    assert json.loads(out)==d,'text edit differs from intended data'
    open(P,'w',encoding='utf8',newline='').write(out)
    for c in L: print([round(float(v),3) for v in c['origin']],c['size'],c['rotation'],round(c.get('overlap',0),2))
