#!/usr/bin/env python3
"""Build the site: index.html from src/the-dosage.html, one page per story under
stories/<slug>/index.html (own title, description, share image, canonical URL),
plus sitemap.xml and robots.txt. Run from the repo root."""
import re, html, os, datetime
ROOT=os.path.dirname(os.path.abspath(__file__))
SITE='https://thedosagemag.com/'
src=open(os.path.join(ROOT,'src/the-dosage.html'),encoding='utf-8').read()
# make or refresh the search/share cards for every story first (needs Playwright; skipped if unavailable)
import subprocess, sys as _sys
try: subprocess.run([_sys.executable,os.path.join(ROOT,'tools/share_cards.py')],check=True)
except Exception as _e: print('share cards skipped:',_e)
HEAD='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
'''
IMG={'post-nasa-satellites-show-years':'posts/img/news/nasa-satellites-show-years/hero.jpg','post-all-20-free-womens':'posts/img/news/all-20-free-womens/hero.jpg','post-severe-storms-likely-eastern':'posts/img/news/severe-storms-likely-eastern/hero.jpg','post-arden-get-more-than':'posts/img/news/arden-get-more-than/hero.jpg','post-more-than-36-8':'posts/img/news/more-than-36-8/hero.jpg','post-fibre-broadband-coming-more':'posts/img/news/fibre-broadband-coming-more/hero.jpg','post-planning-rules-protect-melbournes':'posts/img/news/planning-rules-protect-melbournes/hero.jpg','post-139-5-million-victorias':'posts/img/news/139-5-million-victorias/hero.jpg','post-planning-starts-two-jobs':'posts/img/news/planning-starts-two-jobs/hero.jpg','post-contract-awarded-remove-anderson':'posts/img/news/contract-awarded-remove-anderson/hero.jpg','post-sec-apprenticeship-academy-pilot':'posts/img/news/sec-apprenticeship-academy-pilot/hero.jpg','post-volunteer-mark-edmonds-named':'posts/img/news/volunteer-mark-edmonds-named/hero.jpg','post-nearly-2-000-more':'posts/img/news/nearly-2-000-more/hero.jpg','post-preferred-bidder-named-sunshine':'posts/img/news/preferred-bidder-named-sunshine/hero.jpg','post-macha-app-victorias-maternal':'posts/img/news/macha-app-victorias-maternal/hero.jpg','post-food-relief-grants-refrigerated':'posts/img/news/food-relief-grants-refrigerated/hero.jpg','post-childrens-week-starts-weekend':'posts/img/news/childrens-week-starts-weekend/hero.jpg','post-victorian-dairy-farms-bounce':'posts/img/news/victorian-dairy-farms-bounce/hero.jpg','post-heat-hits-mums-babies':'posts/img/news/heat-hits-mums-babies/hero.jpg','post-free-legal-help-victorians':'posts/img/news/free-legal-help-victorians/hero.jpg','post-wbbl12':'posts/img/news/wbbl12/hero.jpg','post-arrivals-oct':'posts/img/news/arrivals-oct/top10.jpg','post-fuel':'posts/img/news/fuel/hero.jpg','post-phi-blocked':'posts/img/news/n1-phi-blocked.jpg','post-slprices':'posts/img/news/n2-sl-prices.jpg',
 'post-rba':'posts/img/news/n3-rba.jpg','post-budget27':'posts/img/news/n4-budget.jpg','post-tourism':'posts/img/news/n5-tourism.jpg',
 'post-lightning':'posts/img/news/n6-lightning.jpg','post-healthhub':'posts/img/news/n7-health-hub.jpg','post-twoprices':'posts/img/news/n9-two-prices.jpg','post-holidays':'posts/img/news/n10-holidays.jpg','post-transport':'posts/img/news/n12-transport.jpg','post-elina':'posts/img/news/n17-elina.jpg','post-cpr':'posts/img/news/cpr/hero.jpg','post-dengue-vaccine':'posts/img/news/dengue-vaccine/timeline.png','post-trees':'posts/img/news/trees/hero.jpg','post-protein-static':'posts/img/news/protein-static/hero.jpg','post-smart-glasses':'posts/img/news/smart-glasses/hero.jpg','post-mfw':'posts/img/news/n16-mfw.jpg','post-rch':'posts/img/news/n15-rch.jpg','post-retina':'posts/img/news/roadster/tesla-roadster-liftoff.jpg','post-asthma':'posts/img/news/n8-thunderstorm-asthma.jpg','post-dengue':'posts/img/news/n11-dengue.jpg','post-phi':'posts/img/2026-10-13-phi.jpg',
 'post-lovebar':'posts/img/travels/lovebar-hero.jpg','post-jeana':'posts/img/travels/jeana-bolgoda.jpg'}
# per-story search overrides: page title, description, extra share images and topics
SEO={'post-elina':{
 'title':"Elina Gunawardena, Sri Lankan model, walks the Victoria’s Secret Fashion Show 2026",
 'desc':"Sri Lankan model Elina Gunawardena walked the Victoria’s Secret Fashion Show 2026 in Los Angeles. Her path from Colombo, the runway, the headliners and the music.",
 'img':'posts/img/news/elina/elina-share-16x9.jpg','imgw':1200,'imgh':675,
 'alt':"Elina Gunawardena on the Victoria’s Secret Fashion Show 2026 runway. Photo: Courtesy of Victoria’s Secret",
 'images':['posts/img/news/elina/elina-share-16x9.jpg','posts/img/news/elina/elina-share-4x3.jpg','posts/img/news/elina/elina-share-1x1.jpg','posts/img/news/elina/elina-vs-2026.jpg'],
 'section':'Fashion',
 'tags':['Elina Gunawardena','Victoria’s Secret Fashion Show 2026','Sri Lankan model','Ayen Agany','Ravleen Varghese','Neelam Gill','Bella Hadid','Kylie Jenner','KATSEYE','Tate McRae','Megan Thee Stallion','Megan Moroney'],
 'about':['Elina Gunawardena'],
 'mentions':['Ayen Agany','Ravleen Varghese','Neelam Gill','Luna Yohannan','Bella Hadid','Gigi Hadid','Adriana Lima','Kylie Jenner','Candice Swanepoel','Irina Shayk','Barbara Palvin','KATSEYE','Tate McRae','Megan Moroney','Megan Thee Stallion'],
 'modified':'2026-10-21T07:30:00+11:00'}}
DEFAULT_IMG='the-dosage-logo-square.png'
# story pages: one short Press Council line; the full notice and badges stay on the homepage
APC_SHORT='<span class="label" style="flex-basis:100%">Bound by the Australian Press Council’s Standards of Practice · <a href="#standards">Complaints</a></span>'
def wrap(body_src, meta, extra=''):
    b=body_src.replace('\n\n<header class="bar">','\n</head>\n<body>\n\n<header class="bar">',1)
    assert b!=body_src
    return HEAD+meta+extra+b.rstrip('\n')+'\n</body>\n</html>\n'
def ogmeta(title,desc,url,img,typ='article'):
    e=lambda x: html.escape(x,quote=True)
    return (f'<meta name="description" content="{e(desc)}">\n<link rel="canonical" href="{url}">\n'
      f'<meta property="og:site_name" content="The Dosage">\n<meta property="og:type" content="{typ}">\n'
      f'<meta property="og:title" content="{e(title)}">\n<meta property="og:description" content="{e(desc)}">\n'
      f'<meta property="og:url" content="{url}">\n<meta property="og:image" content="{SITE}{img}">\n'
      f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@TheDosageMag">\n')

PAGE_RE=re.compile(r'<(div|article) class="page[^"]*" data-page="([a-z0-9-]+)"[^>]*>')
def page_spans(text):
    """(start,end,id) for every top-level page block, matching nested tags of the same name."""
    out=[]
    for m in PAGE_RE.finditer(text):
        tag=m.group(1); depth=0; i=m.start()
        tok=re.compile(r'<(/?)'+tag+r'\b[^>]*>')
        for t in tok.finditer(text,m.start()):
            depth+= -1 if t.group(1) else 1
            if depth==0: out.append((m.start(),t.end(),m.group(2))); break
    # keep only outermost
    out.sort(); top=[]; last=-1
    for a,b,i in out:
        if a>=last: top.append((a,b,i)); last=b
    return top
def only_page(text,keep):
    spans=page_spans(text); res=[]; pos=0
    for a,b,i in spans:
        res.append(text[pos:a])
        if i==keep: res.append(text[a:b])
        pos=b
    res.append(text[pos:]); return ''.join(res)
def more_stories(pid,n=4):
    picks=[m for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)',cat:'([^']*)'.*?title:(['\"])(.*?)\3",src) if m.group(1)!=pid][:n]
    items=''.join(f'<li><a href="stories/{m.group(1)[5:]}/"><span class="label red">{m.group(2)}</span> {m.group(4)}</a></li>' for m in picks)
    return f'<aside class="more-stories" aria-label="More stories"><h2>More from The Dosage</h2><ul>{items}</ul><p><a href="#stories">All stories →</a></p></aside>'
# home
home_meta=ogmeta('The Dosage','The Dosage. Reality, unfiltered. Health, fitness, lifestyle and the stories that connect Colombo and Melbourne, explained simply.',SITE,DEFAULT_IMG,'website')
open(os.path.join(ROOT,'index.html'),'w',encoding='utf-8').write(wrap(src,home_meta))
# publish dates (needed for story pages and sitemaps)
MON={m:i for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],1)}
pubdate={}
for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)'[^}]*?date:'(\d{1,2}) ([A-Z][a-z]{2}) (\d{4})'",src):
    pubdate[m.group(1)]=datetime.date(int(m.group(4)),MON[m.group(3)],int(m.group(2)))
import json
# automatic search data for every story (SEO entries above override any field)
CATS={m.group(1):html.unescape(m.group(2)) for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)',cat:'([^']*)'",src)}
STOP={'Courtesy','Lankan','The','This','That','These','Those','It','In','On','At','For','And','But','Or','If','When','Where','What','How','Why','A','An','Our','Your','We','You','They','She','He','Her','His','Sources','Source','Photo','Photos','Chart','General','Read','Watch','More','Call','Push','Shock'}
MONTHS={'January','February','March','April','May','June','July','August','September','October','November','December','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'}
def auto_tags(title,cat,body):
    txt=html.unescape(re.sub(r'<[^>]+>',' ',body))
    cands={}
    for m in re.finditer(r"\b([A-Z][a-zA-Z’'-]+(?:\s+(?:of|de|the)?\s*[A-Z][a-zA-Z’'-]+){1,3})\b",txt):
        ph=re.sub(r'(’s|\'s)$','',re.sub(r'\s+',' ',m.group(1)).strip())
        w=ph.split()
        if any(len(x)<=2 and x not in ('of','de') for x in w): continue
        if w[0] in STOP or w[0] in MONTHS or any(x in MONTHS for x in w): continue
        cands[ph]=cands.get(ph,0)+1
    names=[k for k,v in sorted(cands.items(),key=lambda kv:-kv[1]) if v>=2 or k in title][:10]
    out=[cat]
    for n in names:
        if n.lower() not in [x.lower() for x in out]: out.append(n)
    return out
def trim(t,n=160):
    if len(t)<=n: return t
    t=t[:n-1]; return t[:t.rfind(' ')].rstrip(',;:')+'…'
def auto_seo(pid,slug,title,desc,body):
    o={'title':title,'desc':trim(desc) if desc else desc,'section':CATS.get(pid,'Story'),'tags':auto_tags(title,CATS.get(pid,'Story'),body)}
    sh=[f'posts/img/share/{slug}-{k}.jpg' for k in ('16x9','4x3','1x1')]
    if all(os.path.exists(os.path.join(ROOT,f)) for f in sh):
        o.update({'img':sh[0],'imgw':1200,'imgh':675,'alt':title,'images':sh})
    fi=re.search(r'<img[^>]+src="(posts/[^"]+)"[^>]*alt="([^"]*)"',body)
    if fi:
        o['alt']=html.unescape(fi.group(2)) or title
        if 'images' in o: o['images']=o['images']+[fi.group(1)]
    o.update(SEO.get(pid,{}))
    return o
def ld_article(pid,title,desc,url,img,body,sx=None):
    labels=re.findall(r'<span class="label[^"]*">(.*?)</span>',re.search(r'<div class="byline">(.*?)</div>',body,re.S).group(1)) if '<div class="byline">' in body else []
    author=next((html.unescape(re.sub('<[^>]+>','',l)) for l in labels[1:] if not re.search(r'\d{4}|^The Dosage$',l)),None)
    d=pubdate.get(pid)
    o={"@context":"https://schema.org","@type":"NewsArticle","headline":title[:110],"description":desc,
       "mainEntityOfPage":url,"url":url,"image":[SITE+(img or DEFAULT_IMG)],
       "author":({"@type":"Person","name":author} if author else {"@type":"Organization","name":"The Dosage","url":SITE}),
       "publisher":{"@type":"NewsMediaOrganization","name":"The Dosage","url":SITE,"logo":{"@type":"ImageObject","url":SITE+DEFAULT_IMG}}}
    if d: o["datePublished"]=d.isoformat()+"T07:00:00+11:00"
    sx=sx or {}
    if sx:
        if sx.get('images'): o["image"]=[SITE+i for i in sx['images']]
        o["articleSection"]=sx['section']; o["keywords"]=sx['tags']; o["inLanguage"]="en-AU"; o["isAccessibleForFree"]=True
        if sx.get('about'): o["about"]=[{"@type":"Person","name":n} for n in sx['about']]
        if sx.get('mentions'): o["mentions"]=[{"@type":"Person","name":n} for n in sx['mentions']]
        if sx.get('modified'): o["dateModified"]=sx['modified']
    return '<script type="application/ld+json">'+json.dumps(o,ensure_ascii=False)+'</script>\n'
# stories
urls=[SITE]
meta_by_url={}
for m in re.finditer(r'<article class="page article[^"]*" data-page="(post-[a-z0-9-]+)" hidden>(.*?)</article>',src,re.S):
    pid,body=m.group(1),m.group(2)
    slug=pid[5:]
    t=re.search(r'<h1[^>]*>(.*?)</h1>',body,re.S); title=html.unescape(re.sub('<[^>]+>','',t.group(1))).strip() if t else 'The Dosage'
    d=re.search(r'<p class="dek">(.*?)</p>',body,re.S); desc=html.unescape(re.sub('<[^>]+>','',d.group(1))).strip() if d else ''
    url=f'{SITE}stories/{slug}/'
    sx=auto_seo(pid,slug,title,desc,body); ptitle=sx.get('title',title); desc=sx.get('desc',desc)
    page_src=src.replace('<title>The Dosage</title>',f'<title>{html.escape(ptitle)} | The Dosage</title>',1)
    page_src=re.sub(r'<!--APC-FULL-->.*?<!--/APC-FULL-->',APC_SHORT,page_src,count=1,flags=re.S)
    page_src=only_page(page_src,pid)
    page_src=page_src.replace(f'data-page="{pid}" hidden>',f'data-page="{pid}">',1)
    ai=page_src.index(f'data-page="{pid}"'); ce=page_src.index('</article>',ai)
    page_src=page_src[:ce]+more_stories(pid)+page_src[ce:]
    fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); simg=IMG.get(pid) or (fi.group(1) if fi else None)
    meta='<base href="/">\n'+ogmeta(ptitle,desc,url,sx.get('img') or simg or DEFAULT_IMG)
    meta+='<meta name="robots" content="max-image-preview:large">\n'
    if sx:
        e=lambda v: html.escape(v,quote=True)
        if sx.get('imgw'): meta+=f'<meta property="og:image:width" content="{sx["imgw"]}">\n<meta property="og:image:height" content="{sx["imgh"]}">\n'
        if sx.get('alt'): meta+=f'<meta property="og:image:alt" content="{e(sx["alt"])}">\n<meta name="twitter:image:alt" content="{e(sx["alt"])}">\n'
        meta+=f'<meta property="article:section" content="{e(sx["section"])}">\n'+''.join(f'<meta property="article:tag" content="{e(t)}">\n' for t in sx['tags'])
        if sx.get('modified'): meta+=f'<meta property="article:modified_time" content="{sx["modified"]}">\n'
    if pid in pubdate: meta+=f'<meta property="article:published_time" content="{pubdate[pid].isoformat()}T07:00:00+11:00">\n'
    extra=f'<script>window.DOSAGE_PAGE="{pid}";</script>\n'+ld_article(pid,ptitle,desc,url,sx.get('img') or simg,body,sx)
    out=os.path.join(ROOT,'stories',slug); os.makedirs(out,exist_ok=True)
    open(os.path.join(out,'index.html'),'w',encoding='utf-8').write(wrap(page_src,meta,extra))
    urls.append(url); fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); meta_by_url[url]=(pid,ptitle,IMG.get(pid) or (fi.group(1) if fi else None))

# standalone info pages (About, Editorial standards, Privacy, Careers)
static_urls=[]
for pid in ['about','standards','privacy','careers','sport','sport-cricket']:
    blk=[(a,b) for a,b,i in page_spans(src) if i==pid]
    if not blk: continue
    body=src[blk[0][0]:blk[0][1]]
    t=re.search(r'<h1[^>]*>(.*?)</h1>',body,re.S) or re.search(r'<h2[^>]*>(.*?)</h2>',body,re.S)
    title=html.unescape(re.sub('<[^>]+>',' ',t.group(1))).strip() if t else pid.title()
    title=re.sub(r'\s+',' ',title)
    if pid=='about': title='About The Dosage'
    d=re.search(r'<p[^>]*>(.*?)</p>',body,re.S); desc=html.unescape(re.sub('<[^>]+>','',d.group(1))).strip()[:200] if d else ''
    url=f'{SITE}{pid}/'
    ps=src.replace('<title>The Dosage</title>',f'<title>{html.escape(title)} | The Dosage</title>',1)
    if pid!='about': ps=re.sub(r'<!--APC-FULL-->.*?<!--/APC-FULL-->',APC_SHORT,ps,count=1,flags=re.S)
    ps=only_page(ps,pid)
    meta='<base href="/">\n'+ogmeta(title,desc,url,DEFAULT_IMG,'website')
    out=os.path.join(ROOT,pid); os.makedirs(out,exist_ok=True)
    open(os.path.join(out,'index.html'),'w',encoding='utf-8').write(wrap(ps,meta,f'<script>window.DOSAGE_PAGE="{pid}";</script>\n'))
    static_urls.append(url)
for extra in ['#stories','#travels','#original','#about','#standards']:
    pass
today=datetime.date.today().isoformat()
def x(t): return html.escape(t,quote=True)
latest=max(pubdate.values()) if pubdate else datetime.date.today()
entries=[f'  <url><loc>{SITE}</loc><lastmod>{latest.isoformat()}</lastmod><image:image><image:loc>{SITE}{DEFAULT_IMG}</image:loc></image:image></url>\n']
news=[]
for u in urls[1:]:
    pid,title,img=meta_by_url[u]
    d=pubdate.get(pid)
    lm=f'<lastmod>{d.isoformat()}</lastmod>' if d else ''
    im=f'<image:image><image:loc>{SITE}{img}</image:loc></image:image>' if img else ''
    entries.append(f'  <url><loc>{u}</loc>{lm}{im}</url>\n')
    if d and (datetime.date.today()-d).days<=2:
        news.append(f'  <url><loc>{u}</loc><news:news><news:publication><news:name>The Dosage</news:name><news:language>en</news:language></news:publication>'
                    f'<news:publication_date>{d.isoformat()}</news:publication_date><news:title>{x(title)}</news:title></news:news></url>\n')
for u in static_urls: entries.append(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n')
sm=('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'+''.join(entries)+'</urlset>\n')
open(os.path.join(ROOT,'sitemap.xml'),'w').write(sm)
ns=('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'+''.join(news)+'</urlset>\n')
open(os.path.join(ROOT,'news-sitemap.xml'),'w').write(ns)

# RSS feed of the 30 newest stories (added 19 Oct 2026)
import email.utils
items=[]
for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)',cat:'([^']*)'.*?date:'([^']*)',title:(['\"])(.*?)\4,dek:(['\"])(.*?)\6",src):
    pid,cat,_,_,title,_,dek=m.groups()
    d=pubdate.get(pid)
    u=f'{SITE}stories/{pid[5:]}/'
    if not d or u not in meta_by_url: continue
    img=meta_by_url[u][2]
    pd=email.utils.format_datetime(datetime.datetime(d.year,d.month,d.day,7,0,tzinfo=datetime.timezone(datetime.timedelta(hours=11))))
    enc=f'<media:content url="{SITE}{img}" medium="image"/>' if img else ''
    items.append((d,f'  <item><title>{x(html.unescape(title))}</title><link>{u}</link><guid isPermaLink="true">{u}</guid>'
                 f'<pubDate>{pd}</pubDate><category>{x(html.unescape(cat))}</category><description>{x(html.unescape(dek))}</description>{enc}</item>\n'))
items.sort(key=lambda t:t[0],reverse=True)
rss=('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">\n<channel>\n'
     f'  <title>The Dosage</title>\n  <link>{SITE}</link>\n'
     '  <description>Reality, unfiltered. Health, fitness, lifestyle and the stories that connect Colombo and Melbourne, explained simply.</description>\n'
     '  <language>en-au</language>\n'
     f'  <atom:link href="{SITE}feed.xml" rel="self" type="application/rss+xml"/>\n'
     f'  <image><url>{SITE}{DEFAULT_IMG}</url><title>The Dosage</title><link>{SITE}</link></image>\n'
     + ''.join(t for _,t in items[:30]) + '</channel>\n</rss>\n')
open(os.path.join(ROOT,'feed.xml'),'w').write(rss)

# SmartNews SmartFormat feed with full article text (added 19 Oct 2026)
def clean_body(body):
    b=re.sub(r'<a class="back".*?</a>','',body,flags=re.S)
    b=re.sub(r'<h1[^>]*>.*?</h1>','',b,count=1,flags=re.S)
    b=re.sub(r'<p class="dek">.*?</p>','',b,count=1,flags=re.S)
    b=re.sub(r'<div class="byline">.*?</div>','',b,count=1,flags=re.S)
    b=re.sub(r'<figure class="pic fx">.*?</figure>','',b,flags=re.S)   # SVG charts don't render in apps
    b=re.sub(r'<svg.*?</svg>','',b,flags=re.S)
    b=re.sub(r'<(script|style|form|button|iframe)[^>]*>.*?</\1>','',b,flags=re.S)
    b=re.sub(r'\s(class|style|loading|data-[a-z-]+|aria-[a-z-]+|role|id)="[^"]*"','',b)
    b=re.sub(r'(src|href)="(?!https?:|mailto:|#)([^"]+)"',lambda m:f'{m.group(1)}="{SITE}{m.group(2)}"',b)
    b=re.sub(r'href="#[^"]*"',f'href="{SITE}"',b)
    return b.strip()
sitems=[]
for m in re.finditer(r'<article class="page article[^"]*" data-page="(post-[a-z0-9-]+)" hidden>(.*?)</article>',src,re.S):
    pid,body=m.group(1),m.group(2); d=pubdate.get(pid)
    u=f'{SITE}stories/{pid[5:]}/'
    if not d or u not in meta_by_url: continue
    _,title,img=meta_by_url[u]
    dk=re.search(r'<p class="dek">(.*?)</p>',body,re.S); dek=html.unescape(re.sub('<[^>]+>','',dk.group(1))).strip() if dk else ''
    labels=re.findall(r'<span class="label[^"]*">(.*?)</span>',(re.search(r'<div class="byline">(.*?)</div>',body,re.S) or re.search('()','')).group(1))
    author=next((html.unescape(l) for l in labels[1:] if not re.search(r'\d{4}',l)),'The Dosage')
    cat=html.unescape(re.sub('<[^>]+>','',labels[0])) if labels else 'News'
    pd=email.utils.format_datetime(datetime.datetime(d.year,d.month,d.day,7,0,tzinfo=datetime.timezone(datetime.timedelta(hours=11))))
    content=clean_body(body).replace(']]>',']]&gt;')
    thumb=f'<media:thumbnail url="{SITE}{img}"/>' if img else ''
    sitems.append((d,f'<item><title>{x(title)}</title><link>{u}</link><guid isPermaLink="true">{u}</guid><pubDate>{pd}</pubDate>'
        f'<description>{x(dek)}</description><dc:creator>{x(author)}</dc:creator><category>{x(cat)}</category>{thumb}'
        f'<content:encoded><![CDATA[{content}]]></content:encoded></item>\n'))
sitems.sort(key=lambda t:t[0],reverse=True)
sn=('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/" xmlns:snf="http://www.smartnews.be/snf">\n<channel>\n'
    f'<title>The Dosage</title><link>{SITE}</link><description>Independent news, health and lifestyle connecting Colombo and Melbourne.</description>'
    f'<pubDate>{email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))}</pubDate><language>en</language>'
    f'<copyright>The Dosage</copyright><ttl>15</ttl><snf:logo><url>{SITE}the-dosage-logo.png</url></snf:logo>\n'
    + ''.join(t for _,t in sitems[:30]) + '</channel>\n</rss>\n')
open(os.path.join(ROOT,'smartnews.xml'),'w').write(sn)
open(os.path.join(ROOT,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\nSitemap: {SITE}news-sitemap.xml\n')
print(len(urls)-1,'story pages')
