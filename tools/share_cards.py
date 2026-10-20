#!/usr/bin/env python3
"""Make search and share images for every story: 16:9, 4:3 and 1:1 cards at 1200 px wide,
saved as posts/img/share/<slug>-16x9.jpg etc. The story's own image is shown whole (never
cropped or edited), with its credit underneath. Cards are only remade when a story's title,
category or image changes. Run from the repo root before build.py:

    python3 tools/share_cards.py          # new or changed stories only
    python3 tools/share_cards.py --force  # remake all
"""
import re, os, sys, json, html, hashlib, ast, subprocess, tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'posts/img/share'); os.makedirs(OUT,exist_ok=True)
src=open(os.path.join(ROOT,'src/the-dosage.html'),encoding='utf-8').read()
bp=open(os.path.join(ROOT,'build.py'),encoding='utf-8').read()
IMG=ast.literal_eval(re.search(r'^IMG=(\{.*?\})\n',bp,re.S|re.M).group(1))
cats={m.group(1):m.group(2) for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)',cat:'([^']*)'",src)}
SIZES={'16x9':(1200,675),'4x3':(1200,900),'1x1':(1200,1200)}
hashf=os.path.join(OUT,'.hashes.json')
try: hashes=json.load(open(hashf))
except Exception: hashes={}
force='--force' in sys.argv

def clean(t): return html.unescape(re.sub(r'<[^>]+>','',t)).strip()

CSS='''*{margin:0;box-sizing:border-box}body{margin:0;background:#121212}
.c{position:relative;overflow:hidden;background:#121212;color:#F1EDE4;font-family:'DejaVu Sans Mono',monospace;display:flex;gap:44px;padding:44px 52px}
.c.col{flex-direction:column;align-items:center;text-align:center;gap:24px;padding:44px}
.tx{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center}
.col .tx{flex:none;align-items:center}
.k{font-size:18px;letter-spacing:.2em;text-transform:uppercase;color:#FF4A3F}
.h{font-family:'Inter Display','Inter',sans-serif;font-weight:900;letter-spacing:-.02em;line-height:1.02;margin-top:18px}
.foot{display:flex;align-items:center;gap:14px;margin-top:28px}
.d{width:50px;height:50px;background:#D7261E;color:#fff;font-family:'Inter Display',sans-serif;font-weight:900;font-size:34px;display:flex;align-items:center;justify-content:center}
.url{font-family:'Inter Display',sans-serif;font-weight:900;font-size:28px}
.ph{flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;max-width:52%}
.col .ph{max-width:100%;flex:1;min-height:0}
.ph img{display:block;max-width:100%;max-height:calc(100% - 26px);width:auto;height:auto;object-fit:contain;box-shadow:0 0 30px 2px rgba(215,38,30,.22)}
.cr{font-size:12px;letter-spacing:.12em;color:#9c958b;text-transform:uppercase;margin-top:8px;text-align:center}'''

def card(kind,w,h,cat,title,img,credit):
    n=len(title)
    fs={'16x9':58 if n<60 else 48 if n<90 else 40,'4x3':62 if n<60 else 52 if n<90 else 44,'1x1':54 if n<60 else 46 if n<90 else 40}[kind]
    col=' col' if kind=='1x1' else ''
    ph=(f'<div class="ph" style="height:{h-88}px"><img src="file://{img}">'+(f'<div class="cr">{html.escape(credit)}</div>' if credit else '')+'</div>') if img else ''
    if kind=='1x1' and img: ph=ph.replace(f'height:{h-88}px','height:auto')
    tx=(f'<div class="tx"><div class="k">The Dosage · {html.escape(cat)}</div><div class="h" style="font-size:{fs if img else fs+14}px">{html.escape(title)}</div>'
        +('<div class="foot"><div class="d">D</div><div class="url">thedosagemag.com</div></div>' if kind!='1x1' or not img else '')+'</div>')
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="c{col}" style="width:{w}px;height:{h}px">{tx}{ph}</div></body></html>'

jobs=[]
for m in re.finditer(r'<article class="page article[^"]*" data-page="(post-[a-z0-9-]+)" hidden>(.*?)</article>',src,re.S):
    pid,body=m.group(1),m.group(2); slug=pid[5:]
    t=re.search(r'<h1[^>]*>(.*?)</h1>',body,re.S); title=clean(t.group(1)) if t else 'The Dosage'
    fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); rel=IMG.get(pid) or (fi.group(1) if fi else None)
    img=os.path.join(ROOT,rel) if rel and os.path.exists(os.path.join(ROOT,rel)) else None
    credit=''
    if img and fi and rel==fi.group(1):
        fc=re.search(r'<figcaption>(.*?)</figcaption>',body[fi.start():],re.S)
        if fc:
            c=re.search(r'((?:Photos?|Chart|Illustration|Image):.*)$',clean(fc.group(1)))
            if c: credit=c.group(1).rstrip('.')
    cat=cats.get(pid,'Story')
    key=hashlib.sha1(json.dumps([title,cat,credit,rel,os.path.getmtime(img) if img else 0]).encode()).hexdigest()
    done=all(os.path.exists(os.path.join(OUT,f'{slug}-{k}.jpg')) for k in SIZES)
    if force or not done or hashes.get(slug)!=key:
        for k,(w,h) in SIZES.items(): jobs.append((slug,k,w,h,card(k,w,h,cat,title,img,credit)))
        hashes[slug]=key
if not jobs: print('share cards: nothing to do'); sys.exit(0)
tmp=tempfile.mkdtemp()
spec=[]
for slug,k,w,h,doc in jobs:
    f=os.path.join(tmp,f'{slug}-{k}.html'); open(f,'w',encoding='utf-8').write(doc)
    spec.append([f,os.path.join(OUT,f'{slug}-{k}.jpg'),w,h])
js=os.path.join(tmp,'r.js'); open(js,'w').write('''const {chromium}=require('playwright');const spec=require(process.argv[2]);
(async()=>{const b=await chromium.launch();for(const [f,o,w,h] of spec){const p=await b.newPage({viewport:{width:w,height:h}});
await p.goto('file://'+f);await p.waitForTimeout(250);await p.screenshot({path:o,type:'jpeg',quality:88});await p.close();}await b.close()})();''')
json.dump(spec,open(os.path.join(tmp,'spec.json'),'w'))
env=dict(os.environ); env.setdefault('NODE_PATH','/opt/npm-tools/node_modules')
subprocess.run(['node',js,os.path.join(tmp,'spec.json')],check=True,env=env)
json.dump(hashes,open(hashf,'w'),indent=0)
print(f'share cards: {len(jobs)//3} stories updated')
