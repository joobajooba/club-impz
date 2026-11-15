"""The doc's worst cases in REAL Blockbench: a body plus Clothing, Head and Back trait files merged on one texture."""
import base64, copy, glob, io, json, math, os
import numpy as np
from PIL import Image, ImageDraw
from bb import BB
ROOT='C:/Users/lucas/blockbench_models/impz/'
BODY_M='C:/Users/lucas/club-impz/godot-game/assets/models/impz/bodies/body_green.bbmodel'
BODY_T='C:/Users/lucas/club-impz/godot-game/assets/textures/impz/bodies/body_green.png'
COMBOS=[('trench','afro','bone_wings'),('battle_armour','blonde','angel_wings'),('demon_hoodie','straw_hat','cape'),('waterproof_coat','soldier','mechanical_wings'),
        ('puffer','blonde','samurai'),('battle_armour','afro','imp_wings'),('elegant','straw_hat','trident'),('polka_dress','blonde','cape'),('robinhood_hoodie','afro','scythe'),('gi','spiky','sword')]
def merge(c,h,k):
    out=json.load(open(BODY_M,encoding='utf8'))
    atlas=np.zeros((1024,1024,4),np.uint8);atlas[:256,:256]=np.array(Image.open(BODY_T).convert('RGBA'))
    x=256
    for f,png in ((f'clothing/clothing_{c}',0),(f'head/head_{h}',0),(f'back/back_{k}',0)):
        d=json.load(open(ROOT+f+'.bbmodel',encoding='utf8'))
        t=np.array(Image.open(ROOT+f+'.png').convert('RGBA'));hh,w=t.shape[:2]
        atlas[0:hh,x:x+w]=t
        for e in d['elements']:
            for fc in e['faces'].values():
                if fc.get('texture') is not None:
                    u=fc['uv'];fc['uv']=[u[0]+x,u[1],u[2]+x,u[3]]
        out['elements']+=d['elements'];out['groups']+=d['groups'];out['outliner']+=d['outliner']
        x+=w
    b=io.BytesIO();Image.fromarray(atlas).save(b,'PNG')
    tx=out['textures'][0];tx.pop('relative_path',None)
    tx.update(name='combo.png',internal=True,source='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode(),width=1024,height=1024,uv_width=1024,uv_height=1024)
    p=os.path.abspath(f'combo_{c}_{h}_{k}.bbmodel')
    json.dump(out,open(p,'w',encoding='utf8'));return p
b=BB();b.wait_ready();b.load_plugin()
def viewport():
    r=b.call('Page.captureScreenshot',format='png')
    im=Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')
    x,y,w,h=b.js("const r=Preview.selected.canvas.getBoundingClientRect();return [r.x,r.y,r.width,r.height];")
    return im.crop((int(x),int(y),int(x+w),int(y+h)))
# file facts
bad=0
fs=sorted(f for f in glob.glob(ROOT+'back/back_*.bbmodel') if 'showcase' not in f)
for f in fs:
    b.open(f)
    r=b.js("return {cubes:Cube.all.length,groups:Group.all.length,internal:Texture.all.every(t=>t.internal),err:Texture.all.some(t=>t.error),stretched:Cube.all.filter(c=>c.stretch.some(v=>v!=1)).length,fmt:Format.id};")
    ok=r['internal'] and not r['err'] and not r['stretched'] and r['fmt']=='hytale_character' and r['cubes']<=40 and r['cubes']+r['groups']<=255
    bad+=not ok
    print(os.path.basename(f)[5:-8].ljust(18),r['cubes'],r['groups'],'' if ok else 'PROBLEM '+str(r))
print('files',len(fs),'problems',bad)
o=Image.new('RGB',(2*(3*334+6),5*334),(40,40,40))
for i,co in enumerate(COMBOS):
    p=merge(*co)
    print(co,b.open(p)['cubes'])
    for j,(ya,pi) in enumerate(((0,6),(180,10),(50,18))):
        a,q=math.radians(ya),math.radians(pi);c=(0,58,-6);d=190
        b.camera((c[0]+d*math.sin(a)*math.cos(q),c[1]+d*math.sin(q),c[2]+d*math.cos(a)*math.cos(q)),c)
        v=viewport();s=min(v.size)
        v=v.crop(((v.width-s)//2,(v.height-s)//2,(v.width+s)//2,(v.height+s)//2)).resize((330,330),Image.LANCZOS)
        if j==0:ImageDraw.Draw(v).text((4,4),' + '.join(co),fill=(255,255,0))
        o.paste(v,((i%2)*(3*334+6)+j*334,(i//2)*334))
    os.remove(p)
o.save('cloth_sheets/combos.png')
