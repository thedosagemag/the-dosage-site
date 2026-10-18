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
# home
home_meta=ogmeta('The Dosage','The Dosage. Reality, unfiltered. Health, fitness, lifestyle and the stories that connect Colombo and Melbourne, explained simply.',SITE,DEFAULT_IMG,'website')
open(os.path.join(ROOT,'index.html'),'w',encoding='utf-8').write(wrap(src,home_meta))
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
    meta='<base href="/">\n'+ogmeta(title,desc,url,IMG.get(pid,DEFAULT_IMG))
    extra=f'<script>window.DOSAGE_PAGE="{pid}";</script>\n'
    out=os.path.join(ROOT,'stories',slug); os.makedirs(out,exist_ok=True)
    open(os.path.join(out,'index.html'),'w',encoding='utf-8').write(wrap(page_src,meta,extra))
    urls.append(url); fi=re.search(r'<img[^>]+src="(posts/[^"]+)"',body); meta_by_url[url]=(pid,title,IMG.get(pid) or (fi.group(1) if fi else None))
for extra in ['#stories','#travels','#original','#about','#standards']:
    pass
today=datetime.date.today().isoformat()
# publish dates from the stories list in the source, e.g. {id:'post-fuel',...,date:'17 Oct 2026',...}
MON={m:i for i,m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],1)}
pubdate={}
for m in re.finditer(r"\{id:'(post-[a-z0-9-]+)'[^}]*?date:'(\d{1,2}) ([A-Z][a-z]{2}) (\d{4})'",src):
    pubdate[m.group(1)]=datetime.date(int(m.group(4)),MON[m.group(3)],int(m.group(2)))
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
