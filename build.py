#!/usr/bin/env python3
"""Build the site: index.html from src/the-dosage.html, one page per story under
stories/<slug>/index.html (own title, description, share image, canonical URL),
plus sitemap.xml and robots.txt. Run from the repo root."""
import re, html, os, datetime
ROOT=os.path.dirname(os.path.abspath(__file__))
SITE='https://thedosagemag.com/'
src=open(os.path.join(ROOT,'src/the-dosage.html'),encoding='utf-8').read()
HEAD='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
'''
IMG={'post-arrivals-oct':'posts/img/news/arrivals-oct/top10.jpg','post-fuel':'posts/img/news/fuel/hero.jpg','post-phi-blocked':'posts/img/news/n1-phi-blocked.jpg','post-slprices':'posts/img/news/n2-sl-prices.jpg',
 'post-rba':'posts/img/news/n3-rba.jpg','post-budget27':'posts/img/news/n4-budget.jpg','post-tourism':'posts/img/news/n5-tourism.jpg',
 'post-lightning':'posts/img/news/n6-lightning.jpg','post-healthhub':'posts/img/news/n7-health-hub.jpg','post-twoprices':'posts/img/news/n9-two-prices.jpg','post-holidays':'posts/img/news/n10-holidays.jpg','post-transport':'posts/img/news/n12-transport.jpg','post-retina':'posts/img/news/roadster/tesla-roadster-liftoff.jpg','post-asthma':'posts/img/news/n8-thunderstorm-asthma.jpg','post-dengue':'posts/img/news/n11-dengue.jpg','post-phi':'posts/img/2026-10-13-phi.jpg',
 'post-lovebar':'posts/img/travels/lovebar-hero.jpg','post-jeana':'posts/img/travels/jeana-bolgoda.jpg'}
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
def ld_article(pid,title,desc,url,img,body):
    labels=re.findall(r'<span class="label[^"]*">(.*?)</span>',re.search(r'<div class="byline">(.*?)</div>',body,re.S).group(1)) if '<div class="byline">' in body else []
    author=next((html.unescape(re.sub('<[^>]+>','',l)) for l in labels[1:] if not re.search(r'\d{4}|^The Dosage$',l)),None)
    d=pubdate.get(pid)
    o={"@context":"https://schema.org","@type":"NewsArticle","headline":title[:110],"description":desc,
       "mainEntityOfPage":url,"url":url,"image":[SITE+(img or DEFAULT_IMG)],
       "author":({"@type":"Person","name":author} if author else {"@type":"Organization","name":"The Dosage","url":SITE}),
       "publisher":{"@type":"NewsMediaOrganization","name":"The Dosage","url":SITE,"logo":{"@type":"ImageObject","url":SITE+DEFAULT_IMG}}}
    if d: o["datePublished"]=d.isoformat()+"T07:00:00+11:00"
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
    page_src=src.replace('<title>The Dosage</title>',f'<title>{html.escape(title)} | The Dosage</title>',1)
    page_src=re.sub(r'<!--APC-FULL-->.*?<!--/APC-FULL-->',APC_SHORT,page_src,count=1,flags=re.S)
    page_src=only_page(page_src,pid)
    page_src=page_src.replace(f'data-page="{pid}" hidden>',f'data-page="{pid}">',1)
    ai=page_src.index(f'data-page="{pid}"'); ce=page_src.index('</article>',ai)
    page_src=page_src[:ce]+more_stories(pid)+page_src[ce:]
    fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); simg=IMG.get(pid) or (fi.group(1) if fi else None)
    meta='<base href="/">\n'+ogmeta(title,desc,url,simg or DEFAULT_IMG)
    if pid in pubdate: meta+=f'<meta property="article:published_time" content="{pubdate[pid].isoformat()}T07:00:00+11:00">\n'
    extra=f'<script>window.DOSAGE_PAGE="{pid}";</script>\n'+ld_article(pid,title,desc,url,simg,body)
    out=os.path.join(ROOT,'stories',slug); os.makedirs(out,exist_ok=True)
    open(os.path.join(out,'index.html'),'w',encoding='utf-8').write(wrap(page_src,meta,extra))
    urls.append(url); fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); meta_by_url[url]=(pid,title,IMG.get(pid) or (fi.group(1) if fi else None))

# standalone info pages (About, Editorial standards, Privacy, Careers)
static_urls=[]
for pid in ['about','standards','privacy','careers']:
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
open(os.path.join(ROOT,'robots.txt'),'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\nSitemap: {SITE}news-sitemap.xml\n')
print(len(urls)-1,'story pages')
