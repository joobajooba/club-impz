import base64, io, json, math, sys
from PIL import Image, ImageDraw
from bb import BB
b=BB();b.wait_ready();b.load_plugin()
def viewport():
    r=b.call('Page.captureScreenshot',format='png')
    im=Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')
    x,y,w,h=b.js("const r=Preview.selected.canvas.getBoundingClientRect();return [r.x,r.y,r.width,r.height];")
    return im.crop((int(x),int(y),int(x+w),int(y+h)))
members=json.load(open('back_members.json'))
print(b.open(r'C:\Users\lucas\blockbench_models\impz\back\back_showcase.bbmodel')['cubes'])
names=sys.argv[1:]
o=Image.new('RGB',(3*504,len(names)*504),(40,40,40))
for r,n in enumerate(names):
    m=members[n];ox,_,oz=m['off']
    ids=json.dumps(sorted(m['ids']))
    b.js(f"const s=new Set({ids});Cube.all.forEach(c=>c.visibility=s.has(c.uuid));Canvas.updateVisibility();return 1;")
    for i,(ya,pi) in enumerate(((0,4),(180,4),(35,20))):
        a,p=math.radians(ya),math.radians(pi);c=(ox,68,oz-8);d=135
        b.camera((c[0]+d*math.sin(a)*math.cos(p),c[1]+d*math.sin(p),c[2]+d*math.cos(a)*math.cos(p)),c)
        v=viewport();s=min(v.size)
        v=v.crop(((v.width-s)//2,(v.height-s)//2,(v.width+s)//2,(v.height+s)//2)).resize((500,500),Image.LANCZOS)
        ImageDraw.Draw(v).text((4,4),n,fill=(255,255,0))
        o.paste(v,(i*504,r*504))
o.save('cloth_sheets/back_zoom.png')
