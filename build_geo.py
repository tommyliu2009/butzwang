#!/usr/bin/env python3
"""補助王 GEO：產生靜態補助清單頁（/open.html、/list.html、/r/、/t/）、faq.html、about.html、llms.txt、llms-full.txt、robots.txt、sitemap.xml，
並在所有頁面（含 index.html）注入 JSON-LD／og／canonical／重點摘要。由 deploy.sh 在 build_site.py 之後呼叫（冪等）。"""
import sys,os,re,json,glob,hashlib,datetime,urllib.parse,collections
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,'/workspace/shared-data'); import geo
from geo import esc
BASE='https://www.subsidyking.tw'; NAME='補助王'
NOW=datetime.datetime.now(); NOWS=NOW.strftime('%Y-%m-%d %H:%M'); TODAY=NOW.date().isoformat()
D=json.load(open('data.json')); IT=D['items']; GEN=D.get('generated',NOWS)
C=len(IT); H=D.get('histCount',0)
st=collections.Counter(i['status'] for i in IT); lv=collections.Counter(i['level'] for i in IT)
OPEN=sorted([i for i in IT if i['status'] in ('開放中','即將開放')],key=lambda i:i.get('deadline') or '9999')
# 縣市數依實際收錄計算（2026-11-15；以前寫死 22）
NCTY=len({r for i in IT for r in (i.get('regions') or [i['region']]) if r and r!='全國'})
SRC=f'中央部會、{NCTY} 縣市政府與鄉鎮市公所官網公告，以及政府新聞稿'
# 舊的地區／對象頁先刪除再重建（地區改名，例如「新竹」拆成新竹縣、新竹市，避免舊頁留在 sitemap）
for _old in glob.glob('./r/*.html')+glob.glob('./t/*.html'): os.remove(_old)
DESC=f'補助王彙整台灣中央部會、縣市政府與鄉鎮市公所的補助計畫，現行 {C:,} 筆、歷史（109–115 年）{H:,} 筆，可依截止日、主辦層級、補助對象與地區查詢，並推估週期性補助的下次開放時間。'
AD='<div class="adbox"><b>仁禾管理顧問</b><br><a href="mailto:renhe74123@gmail.com">renhe74123@gmail.com</a><br><a href="https://line.me/R/ti/p/@891tcxhu" target="_blank" rel="noopener">LINE 官方帳號：@891tcxhu</a></div>'
CSS='''<style>body{margin:0;font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;color:#1f2933;background:#f6f7f9;line-height:1.6}a{color:#e8590c}.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
.top{background:linear-gradient(135deg,#fff4e6,#ffe8cc 55%,#fff9db);border-bottom:1px solid #ffd8a8;padding:14px 0 18px}.hd{display:flex;gap:16px;align-items:flex-start;justify-content:space-between}
.brand{font-weight:800;color:#e8590c;text-decoration:none;font-size:20px}h1{font-size:26px;margin:8px 0 4px}.crumb{font-size:13px;color:#6b7785}.lead{color:#5c4a3a;margin:4px 0 0}
.adbox{flex:0 0 230px;padding:10px 12px;border:2px solid #f08a24;border-radius:12px;background:#fff7ee;text-align:center;line-height:1.5;font-size:14px}.adbox b{color:#d2691e}.adbox a{color:#d2691e;word-break:break-all}
.card{background:#fff;border:1px solid #e6e9ee;border-radius:14px;padding:14px 16px;margin:16px 0}h2{font-size:19px;margin:0 0 10px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 6px;border-bottom:1px solid #eef0f3;text-align:left;vertical-align:top}th{color:#6b7785;white-space:nowrap}
.tags a{display:inline-block;margin:3px 4px 3px 0;padding:3px 10px;border:1px solid #ffd8a8;border-radius:999px;background:#fff;font-size:13px;text-decoration:none}.foot{color:#6b7785;font-size:13px;padding:20px 0 40px}
@media(max-width:760px){.hd{flex-direction:column}.adbox{flex:none;width:100%;box-sizing:border-box;order:2}h1{font-size:21px}.hide-m{display:none}table{font-size:13px}}</style>'''
NAVL=[('/','首頁'),('/open.html','開放中補助'),('/list.html','全部現行補助'),('/faq.html','常見問答'),('/about.html','關於補助王')]
NAV=' › '.join(f'<a href="{u}">{n}</a>' for u,n in NAVL)
def slug(s): return re.sub(r'[\\/:*?"<>|#%\s]+','_',s).strip('_')[:60] or '_'
def mk(path,title,desc,h1,lead,body):
    os.makedirs(os.path.dirname('.'+path) or '.',exist_ok=True)
    open('.'+path,'w').write(f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}{urllib.parse.quote(path)}">{CSS}</head><body>
<header class="top"><div class="wrap hd"><div><a class="brand" href="/">👑 補助王--仁禾管理顧問</a><div class="crumb">{NAV}</div><h1>{esc(h1)}</h1><p class="lead">{lead}</p></div>{AD}</div></header>
<main class="wrap">{body}</main><footer class="wrap foot">資料最後更新：{esc(GEN)}（台北時間）。資料來源：{SRC}。「預估下次開放」依過去公告推算，實際以主辦單位公告為準。<br>© 補助王｜仁禾管理顧問</footer></body></html>''')
# 2026-11-16 GEO#2：單筆計畫詳情頁 /p/<id>.html（現行計畫；預設只做有具體公告的計畫＋開放中／即將開放，BZ_DETAIL_ALL=1 則全部現行）
for _old in glob.glob('./p/*.html'): os.remove(_old)
DSEL=[i for i in IT if os.environ.get('BZ_DETAIL_ALL')=='1' or i.get('sourceType')!='法規資料庫' or i['status'] in ('開放中','即將開放')]
DIDS={i['id'] for i in DSEL}
def table(items):
    t='<table><tr><th>補助計畫</th><th class="hide-m">主辦單位</th><th>地區</th><th>截止／狀態</th></tr>'
    for i in items:
        nx=f'<div class="crumb">{esc(i.get("nextOpen",""))}</div>' if i.get('nextOpen') else ''
        t+=f'<tr><td><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["name"])}</a><div class="crumb">{esc(i.get("target",""))}｜{esc((i.get("summary") or "")[:120])}{(f'｜<a href="/p/{i["id"]}.html">計畫詳情</a>' if i['id'] in DIDS else '')}</div></td><td class="hide-m">{esc(i["org"])}</td><td>{esc(i["region"])}</td><td>{esc(i.get("deadlineText") or "依公告")}<div class="crumb">{esc(i["status"])}</div>{nx}</td></tr>'
    return t+'</table>'
def srt(items): return sorted(items,key=lambda i:({'開放中':0,'即將開放':1,'常態性/依公告':2,'已截止':3}.get(i['status'],4),i.get('deadline') or '9999'))
REG=[r for r,c in collections.Counter(x for i in IT for x in (i.get('regions') or [i['region']])).most_common() if c>=5]
TGT=[t for t,c in collections.Counter(t for i in IT for t in i['targets']).most_common()]
def tags(): return '<div class="card"><h2>依地區</h2><div class="tags">'+''.join(f'<a href="/r/{urllib.parse.quote(slug(r))}.html">{esc(r)}</a>' for r in REG)+'</div><h2 style="margin-top:12px">依補助對象</h2><div class="tags">'+''.join(f'<a href="/t/{urllib.parse.quote(slug(t))}.html">{esc(t)}</a>' for t in TGT)+'</div></div>'
mk('/open.html','開放中與即將開放的政府補助計畫｜補助王',f'目前開放申請中 {st["開放中"]} 筆、即將開放 {st["即將開放"]} 筆的台灣政府補助計畫，依截止日排序，附主辦單位、補助對象與官方公告連結。','開放中與即將開放的補助',f'開放中 <b>{st["開放中"]}</b> 筆、即將開放 <b>{st["即將開放"]}</b> 筆，依截止日排序。',f'<div class="card">{table(OPEN)}</div>'+tags())
mk('/list.html','全部現行政府補助計畫一覽｜補助王',f'台灣現行政府補助計畫完整清單，共 {C:,} 筆，含中央 {lv["中央"]:,} 筆、縣市 {lv["縣市"]:,} 筆，附截止日、主辦單位、補助對象與官方連結。','全部現行補助計畫',f'共 <b>{C:,}</b> 筆：中央 {lv["中央"]:,}、縣市 {lv["縣市"]:,}、其他 {C-lv["中央"]-lv["縣市"]:,}。開放中排最前面。',tags()+f'<div class="card">{table(srt(IT))}</div>')
RP={};TP={}
for r in REG:
    its=srt([i for i in IT if r in (i.get('regions') or [i['region']])]); p=f'/r/{slug(r)}.html'; RP[p]=r
    mk(p,f'{r}政府補助計畫（{len(its)} 筆）｜補助王',f'{r}適用的政府補助計畫共 {len(its)} 筆，其中開放中 {sum(i["status"]=="開放中" for i in its)} 筆，附截止日、主辦單位、補助對象與官方公告連結。',f'{r}的補助計畫',f'共 <b>{len(its)}</b> 筆，開放中 {sum(i["status"]=="開放中" for i in its)} 筆。',f'<div class="card">{table(its)}</div>'+tags())
for t in TGT:
    its=srt([i for i in IT if t in i['targets']]); p=f'/t/{slug(t)}.html'; TP[p]=t
    mk(p,f'適合{t}的政府補助計畫（{len(its)} 筆）｜補助王',f'補助對象為{t}的台灣政府補助計畫共 {len(its)} 筆，其中開放中 {sum(i["status"]=="開放中" for i in its)} 筆，附截止日、主辦單位與官方公告連結。',f'補助對象：{t}',f'共 <b>{len(its)}</b> 筆，開放中 {sum(i["status"]=="開放中" for i in its)} 筆。',f'<div class="card">{table(its)}</div>'+tags())
FAQ=[('補助王是什麼？',f'補助王（www.subsidyking.tw）是仁禾管理顧問建置的免費台灣政府補助查詢網站，彙整中央部會、{NCTY} 縣市政府與鄉鎮市公所的補助計畫，現行 {C:,} 筆、歷史（109–115 年）{H:,} 筆。'),
 ('補助王的資料來源是什麼？',f'資料來自{SRC}。每筆補助都附官方公告連結，實際申請資格與期限以主辦單位公告為準。'),
 ('資料多久更新一次？',f'每天凌晨自動更新並檢查連結，最近一次更新為 {GEN}（台北時間）。'),
 ('現在有哪些補助開放申請？',f'截至 {GEN}，開放中 {st["開放中"]} 筆、即將開放 {st["即將開放"]} 筆，完整清單見「開放中補助」頁（{BASE}/open.html）。'),
 ('「預估下次開放」怎麼算？','依同一計畫過去幾年的公告與截止月份推算，例如每年約 3 月公告、5 月截止，僅供提前準備參考。'),
 ('企業可以申請哪些補助？',f'補助對象為企業的現行計畫約 {sum("企業" in i["targets"] for i in IT)} 筆，常見如 SBIR、SIIR、地方型 SBIR、數位轉型與節能補助，可在「補助對象：企業」頁查看。'),
 ('使用補助王要付費嗎？','查詢完全免費，不需註冊。'),
 ('需要補助申請或計畫書撰寫協助，可以找誰？','可以聯絡網站維護者仁禾管理顧問：Email renhe74123@gmail.com，LINE 官方帳號：@891tcxhu。')]
mk('/faq.html','補助王常見問答：資料來源、更新頻率與補助申請｜補助王','補助王常見問題：資料來源、更新頻率、目前開放中的補助、預估下次開放的算法與申請協助。','常見問答',f'關於補助王最常被問到的 {len(FAQ)} 個問題。',''.join(f'<div class="card"><h2>{esc(q)}</h2><p>{esc(a)}</p></div>' for q,a in FAQ))
mk('/about.html','關於補助王：資料來源與維護者仁禾管理顧問｜補助王','補助王由仁禾管理顧問建置維護，彙整政府官網補助公告，說明收錄範圍、更新頻率與聯絡方式。','關於補助王',f'補助王由仁禾管理顧問建置與維護，收錄現行 {C:,} 筆、歷史 {H:,} 筆補助。',
 f'<div class="card"><h2>網站介紹</h2><p>{esc(DESC)}</p></div><div class="card"><h2>資料來源</h2><ul><li>{SRC}。</li><li>收錄範圍：現行補助 {C:,} 筆；歷史紀錄 109–115 年 {H:,} 筆。</li><li>更新頻率：每天凌晨自動更新。</li><li>實際申請資格、金額與期限以主辦單位公告為準。</li></ul></div>'
 '<div class="card"><h2>維護者</h2><p><b>仁禾管理顧問</b><br>Email：<a href="mailto:renhe74123@gmail.com">renhe74123@gmail.com</a><br>LINE 官方帳號：<a href="https://line.me/R/ti/p/@891tcxhu">@891tcxhu</a><br>服務：政府補助申請、計畫書撰寫、政府標案投標策略、商業模式顧問。</p><p>姊妹站：<a href="https://www.bidking.tw/">標案王（台灣政府標案搜尋）</a></p></div>')
ORG=geo.org(BASE); WEB=geo.website(BASE,NAME,DESC,BASE+'/?q={search_term_string}')
def gs(i):
    g={'@type':'GovernmentService','name':i['name'],'provider':{'@type':'GovernmentOrganization','name':i['org']},'areaServed':{'@type':'Place','name':'臺灣' if i['region']=='全國' else i['region']},'serviceType':'政府補助','url':i['url']}
    if i.get('target'): g['audience']={'@type':'Audience','audienceType':i['target']}
    if i.get('summary'): g['description']=i['summary'][:300]
    return g
def dataset(url,name,desc):
    return {'@type':'Dataset','@id':url+'#dataset','name':name,'description':desc+' 資料彙整自政府官網公告，由補助王整理，每日更新。','url':url,'inLanguage':'zh-Hant-TW','creator':{'@id':BASE+'/#org'},'publisher':{'@id':BASE+'/#org'},
            'dateModified':NOW.isoformat(timespec='minutes')+'+08:00','spatialCoverage':{'@type':'Place','name':'臺灣'},'license':BASE+'/about.html','isAccessibleForFree':True,'keywords':['政府補助','補助計畫','SBIR','台灣']}
BYORG=collections.defaultdict(list); BYREG=collections.defaultdict(list)
for i in DSEL: BYORG[i['org']].append(i); BYREG[i['region']].append(i)
def period(i):
    a=i.get('start'); b=i.get('deadlineText') or i.get('deadline')
    return f'{a} 起，至 {b}' if a and b else (f'{a} 起' if a else (b or '依主辦單位公告'))
DSM=[]
for i in DSEL:
    p=f'/p/{i["id"]}.html'; url=BASE+p
    rel=[x for x in srt(BYORG[i['org']]) if x['id']!=i['id']][:5]
    if len(rel)<5: rel+=[x for x in srt(BYREG[i['region']]) if x['id']!=i['id'] and x not in rel][:5-len(rel)]
    rows=[('主辦單位',esc(i['org'])),('主辦層級／地區',esc(i['level'])+'／'+esc('、'.join(i.get('regions') or [i['region']]))),('補助對象',esc(i.get('target') or '依公告')),
          ('目前狀態',esc(i['status'])),('受理期間',esc(period(i)))]
    if i.get('cycle'): rows.append(('歷年公告週期',esc(i['cycle'])))
    if i.get('nextOpen'): rows.append(('預估下次開放',esc(i['nextOpen'])+'<div class="crumb">依過去公告推算，僅供提前準備參考</div>'))
    rows.append(('官方公告',f'<a href="{esc(i["url"])}" target="_blank" rel="noopener">前往主辦單位公告</a>'))
    rows.append(('本站首次收錄',esc(i.get('firstSeen') or '—')))
    body=(f'<div class="card"><h2>計畫重點</h2><p>{esc(i.get("summary") or "詳細內容請見主辦單位公告。")}</p><table>'+''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a,b in rows)+'</table></div>'
          +f'<div class="card"><h2>申請前要確認的事</h2><ul><li>確認申請者身分是否符合「{esc(i.get("target") or "主辦單位公告的對象")}」。</li><li>受理期間：{esc(period(i))}；逾期通常不受理。</li><li>補助金額、應備文件與審查方式，以<a href="{esc(i["url"])}" target="_blank" rel="noopener">官方公告</a>全文為準。</li></ul></div>'
          +(('<div class="card"><h2>相關補助</h2><ul>'+''.join(f'<li><a href="/p/{x["id"]}.html">{esc(x["name"])}</a>｜{esc(x["org"])}｜{esc(x["status"])}</li>' for x in rel)+'</ul></div>') if rel else ''))
    desc=f'{i["name"]}：{i["org"]}主辦，補助對象為{i.get("target") or "依公告"}，目前{i["status"]}，受理期間{period(i)}。附官方公告連結。'[:150]
    title=f'{i["name"]}｜{i["org"]}｜補助王'
    h=(f'<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{CSS}</head><body>'
       f'<header class="top"><div class="wrap hd"><div><a class="brand" href="/">👑 補助王--仁禾管理顧問</a><div class="crumb">{NAV}</div><h1>{esc(i["name"])}</h1><p class="lead">{esc(i["org"])}｜{esc(i["status"])}｜{esc(i.get("deadlineText") or "依公告")}</p></div>{AD}</div></header>'
       f'<main class="wrap">{body}</main><footer class="wrap foot">資料整理自主辦單位官方公告，實際申請資格、金額與期限以主辦單位公告為準。<br>© 補助王｜仁禾管理顧問</footer></body></html>')
    g=[ORG,WEB,{'@type':'WebPage','@id':url+'#webpage','url':url,'name':title,'description':desc,'inLanguage':'zh-Hant-TW','isPartOf':{'@id':BASE+'/#website'},'publisher':{'@id':BASE+'/#org'},'mainEntity':{'@id':url+'#service'},'breadcrumb':{'@id':url+'#bc'}},
       dict(gs(i),**{'@id':url+'#service'})]
    b=geo.crumbs(BASE,[('補助王','/'),('全部現行補助','/list.html'),(i['name'],p)]); b['@id']=url+'#bc'; g.append(b)
    h,_,_=geo.inject(h,url,g,None,NAME,og_type='article',og_image=BASE+'/og.png')
    os.makedirs('p',exist_ok=True); open('.'+p,'w',encoding='utf-8').write(h)
    sig=json.dumps([i.get(k) for k in ('name','org','level','region','regions','target','status','start','deadline','deadlineText','summary','url','cycle','nextOpen')],ensure_ascii=False)
    DSM.append((url,'p'+p,hashlib.md5(sig.encode()).hexdigest()))
SUMSRC=f'資料更新：{GEN}（台北時間）｜來源：政府官網公告｜維護：仁禾管理顧問'
STATE='/workspace/butzwang_tools/geo_lastmod.json'; LM=json.load(open(STATE)) if os.path.exists(STATE) else {}
SM=[]
for p in ['index.html','open.html','list.html','faq.html','about.html']+(['videos.html'] if os.path.exists('videos.html') else [])+sorted(x[2:] for x in glob.glob('./r/*.html')+glob.glob('./t/*.html')):
    h=open(p,encoding='utf-8').read(); path='/' if p=='index.html' else '/'+urllib.parse.quote(p); url=BASE+path
    title=geo.get_title(geo.strip(h)); desc=geo.get_desc(h); short=re.sub(r'｜補助王$','',title)
    pt={'faq.html':'FAQPage','about.html':'AboutPage'}.get(p,'CollectionPage' if p!='index.html' else 'WebPage')
    wp={'@type':pt,'@id':url+'#webpage','url':url,'name':title,'description':desc,'inLanguage':'zh-Hant-TW','isPartOf':{'@id':BASE+'/#website'},'publisher':{'@id':BASE+'/#org'},'dateModified':NOW.isoformat(timespec='minutes')+'+08:00'}
    g=[ORG,WEB,wp]
    if p!='index.html':
        cr=[('補助王','/')]
        if p.startswith('r/'): cr+=[('全部現行補助','/list.html'),('依地區','/list.html'),(short,path)]
        elif p.startswith('t/'): cr+=[('全部現行補助','/list.html'),('依補助對象','/list.html'),(short,path)]
        else: cr+=[(short,path)]
        b=geo.crumbs(BASE,cr); b['@id']=url+'#bc'; g.append(b); wp['breadcrumb']={'@id':url+'#bc'}
    if p=='faq.html': wp.update(geo.faq_graph(FAQ,url)); wp['@id']=url+'#webpage'
    if p not in ('faq.html','about.html'): g.append(dataset(url,short if p!='index.html' else '台灣政府補助資料庫',desc if len(desc)>=50 else DESC)); wp['mainEntity']={'@id':url+'#dataset'}
    if p=='index.html': g.append(geo.faq_graph(FAQ[:6],url))   # 2026-11-16 GEO#1：首頁可見的 6 題常見問答
    if p=='open.html': g.append({'@type':'ItemList','@id':url+'#list','name':'開放中與即將開放的補助','numberOfItems':len(OPEN),'itemListElement':[{'@type':'ListItem','position':k+1,'item':gs(i)} for k,i in enumerate(OPEN[:100])]})
    if p=='about.html': wp['about']={'@id':BASE+'/#org'}
    if p=='index.html':
        s=(f'補助王收錄現行補助 <b>{C:,}</b> 筆（中央 {lv["中央"]:,}、縣市 {lv["縣市"]:,}）與歷史 109–115 年 {H:,} 筆；目前開放中 <b>{st["開放中"]}</b> 筆、即將開放 {st["即將開放"]} 筆。{SUMSRC}。'
           f'<details style="margin-top:6px"><summary>開放中與即將開放的補助（靜態清單 {min(40,len(OPEN))} 筆）</summary><ul>'+''.join(f'<li><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["name"])}</a>｜{esc(i["org"])}｜{esc(i.get("deadlineText") or "依公告")}</li>' for i in OPEN[:40])+'</ul></details>'
           '<div style="margin-top:4px">'+'、'.join(f'<a href="{u}">{n}</a>' for u,n in NAVL[1:])+'</div>')
        s+=(f'<details style="margin-top:6px"><summary><b>常見問答</b>（{min(6,len(FAQ))} 題，完整請見<a href="/faq.html">常見問答頁</a>）</summary>'+''.join(f'<p style="margin:6px 0"><b>Q：{esc(q)}</b><br>A：{esc(re.sub(r"<[^>]+>","",a))}</p>' for q,a in FAQ[:6])+'</details>'
            f'<div style="margin-top:6px"><b>關於本站／資料來源與更新頻率：</b>本站由仁禾管理顧問建置維護，資料取自各中央部會、{NCTY} 縣市政府與相關機構官網公開的補助公告，每日自動更新；各筆資料均附原始公告連結，實際內容以主管機關公告為準。<a href="/about.html">了解更多</a></div>')
    else:
        m=re.search(r'<p class="lead">(.*?)</p>',h,re.S); lead=re.sub(r'<[^>]+>','',m.group(1)).strip() if m else ''
        s=esc(desc+(' '+lead if lead and lead not in desc else ''))+' '+esc(SUMSRC)+'。'
    if p=='index.html': h=re.sub(r'彙整中央部會、\d+ 縣市政府與鄉鎮市公所的補助計畫，依截止日', f'彙整中央部會、{NCTY} 縣市政府與鄉鎮市公所的補助計畫，依截止日', h)
    h,_,_=geo.inject(h,url,g,s,NAME,sum_after=('<!--before-main-->' if p=='index.html' else '</header>'),og_image=BASE+'/og.png')
    GSV='<meta name="google-site-verification" content="ErUscDsKVvX8bVYiyhEri1tvmhr2MGhbv_2QcA6Hn3s">'
    if p=='index.html' and GSV not in h: h=h.replace('</head>',GSV+'\n</head>',1)  # Google Search Console 驗證（2026-10-24）
    open(p,'w',encoding='utf-8').write(h)
    key=hashlib.md5(re.sub(r'\d{4}[-/]\d{2}[-/]\d{2}[ T]?\d{0,2}:?\d{0,2}|\d{1,2}:\d{2}','',h).encode()).hexdigest()
    if LM.get(p,[None])[0]!=key: LM[p]=[key,TODAY]
    SM.append((url,LM[p][1]))
for url,k,key in DSM:
    if LM.get(k,[None])[0]!=key: LM[k]=[key,TODAY]
    SM.append((url,LM[k][1]))
json.dump(LM,open(STATE,'w'))
_IK='/workspace/shared-data/indexnow_key.txt'   # 2026-11-16 GEO#5：IndexNow 金鑰檔（公開檔案）
if os.path.exists(_IK): _k=open(_IK).read().strip(); open(f'{_k}.txt','w').write(_k)
open('sitemap.xml','w').write(geo.sitemap(SM)); open('robots.txt','w').write(geo.robots(BASE))
L=['# 補助王（subsidyking.tw）',f'> {DESC}','',f'維護者：仁禾管理顧問（renhe74123@gmail.com，LINE 官方帳號：@891tcxhu）。資料來源：{SRC}。最近更新：{GEN}（台北時間）。','',
   '## 引用本站',f'- 建議寫法：「資料來源：補助王（{BASE}/），YYYY-MM-DD 查詢」；引用單一計畫時，請一併附上該計畫頁（{BASE}/p/<編號>.html）或主辦單位官方公告連結。',
   '- 補助資格、金額與期限會變動，請以主辦單位最新公告為準，並註明查詢日期。','',
   '## 資料授權與更正',
   '- 各補助的公告原文、法規與附件，權利屬各主辦機關；本站整理的是名稱、主辦單位、對象、期限與官方連結等事實資訊，每筆附原始出處。',
   '- 本站整理的清單與欄位可免費引用，請註明「補助王」與網址；本站不是政府機關，引用時請勿寫成官方資料。',
   '- 更正管道：發現資料錯誤或連結失效，請寄 renhe74123@gmail.com 或洽 LINE 官方帳號 @891tcxhu，附上計畫名稱與正確的官方公告連結，確認後於每日更新時修正。','','## 主要頁面',
   f'- [補助搜尋首頁]({BASE}/)：可依關鍵字、狀態、主辦層級、補助對象、地區篩選；支援 {BASE}/?q=關鍵字',f'- [開放中與即將開放的補助]({BASE}/open.html)：{st["開放中"]+st["即將開放"]} 筆',f'- [全部現行補助]({BASE}/list.html)：{C:,} 筆靜態清單',
   f'- [常見問答]({BASE}/faq.html)',f'- [關於補助王與資料來源]({BASE}/about.html)',f'- [完整說明（llms-full.txt）]({BASE}/llms-full.txt)',f'- 單筆計畫頁：{BASE}/p/<編號>.html（共 {len(DSEL):,} 頁，含主辦單位、對象、受理期間、歷年週期與官方公告連結）','','## 依地區']+[f'- [{r}]({BASE}/r/{urllib.parse.quote(slug(r))}.html)' for r in REG]+['','## 依補助對象']+[f'- [{t}]({BASE}/t/{urllib.parse.quote(slug(t))}.html)' for t in TGT]+['','## 姊妹站','- [標案王 bidking.tw](https://www.bidking.tw/)：台灣政府標案搜尋']
open('llms.txt','w').write('\n'.join(L)+'\n')
F=L+['',f'## 統計（{GEN}）',f'- 現行 {C:,} 筆，歷史 {H:,} 筆']+[f'- {k}：{v:,} 筆' for k,v in st.items()]+['','## 常見問答']+[f'### {q}\n{a}\n' for q,a in FAQ]
F+=['','## 開放中與即將開放的補助']+[f'- {i["name"]}｜{i["org"]}｜{i["region"]}｜對象：{i.get("target","")}｜截止：{i.get("deadlineText") or "依公告"}｜{(i.get("summary") or "")[:150]}｜{i["url"]}' for i in OPEN]
F+=['','## 全部現行補助（名稱｜主辦｜地區｜狀態｜下次開放預估）']+[f'- {i["name"]}｜{i["org"]}｜{i["region"]}｜{i["status"]}｜{i.get("nextOpen","")}' for i in srt(IT)]
open('llms-full.txt','w').write('\n'.join(F)+'\n')
n,errs=geo.validate('./**/*.html')
print('GEO pages',len(SM),'jsonld',n,'errors',len(errs)); [print(' ',e) for e in errs[:20]]
sys.exit(1 if errs else 0)
