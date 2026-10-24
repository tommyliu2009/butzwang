#!/usr/bin/env python3
"""獎補助資訊網（grantking.subsidyking.tw）產生器。
讀補助王同一次建置產生的 data.json（同一資料庫），輸出完全不同結構、版面、文字的靜態網站到 /workspace/grant-king。
每頁 canonical 指向本站自身網址。摘要用 rewrite.py 快取的改寫版，沒有則用原文。
用法：python3 build_theme.py [--dry-run]（dry-run 輸出到 /tmp/grant-king-dry）"""
import os,sys,json,re,shutil,html,hashlib,datetime,collections,urllib.parse
H=os.path.dirname(os.path.abspath(__file__)); SRC='/workspace/butzwang'
DRY='--dry-run' in sys.argv; OUT='/tmp/grant-king-dry' if DRY else '/workspace/grant-king'
BASE='https://grantking.subsidyking.tw'; NAME='獎補助資訊網'; GA='G-7374EDFKBH'
D=json.load(open(f'{SRC}/data.json')); IT=D['items']; GEN=D.get('generated','')
CACHE=json.load(open(f'{H}/summary_cache.json')) if os.path.exists(f'{H}/summary_cache.json') else {}
TODAY=datetime.date.today().isoformat(); E=html.escape
def summ(i): return (CACHE.get(str(i['id'])) or {}).get('s') or i.get('summary') or ''
def q(s): return urllib.parse.quote(s)
def oslug(o): return 'org-'+hashlib.md5(o.encode()).hexdigest()[:8]
AUD={'企業':('business','企業與商家'),'民間團體':('nonprofit','協會・社區・民間團體'),'學校/研究':('academic','學校與研究單位'),
     '個人/青年':('individual','個人・青年・學生'),'政府機關':('public','政府機關與公所'),'其他':('others','其他對象')}
ORD={'開放中':0,'即將開放':1,'常態性/依公告':2,'已截止':3}
def srt(x): return sorted(x,key=lambda i:(ORD.get(i['status'],4),i.get('deadline') or '9999'))
ST=collections.Counter(i['status'] for i in IT)
ORGS=collections.defaultdict(list)
for i in IT: ORGS[i['org']].append(i)
BIGORG=sorted([o for o,v in ORGS.items() if len(v)>=3],key=lambda o:-len(ORGS[o]))
AD=('<div class="adbox"><b>仁禾管理顧問</b><br><a href="mailto:renhe74123@gmail.com">renhe74123@gmail.com</a><br>'
    '<a href="https://line.me/R/ti/p/@891tcxhu" target="_blank" rel="noopener">LINE 官方帳號：@891tcxhu</a></div>')
MENU=[('/','首頁'),('/search.html','找獎補助'),('/deadlines.html','截止日曆'),('/agencies/','依主管機關'),('/audiences/','依申請對象'),('/guide.html','申請指南'),('/glossary.html','名詞解釋'),('/qa.html','常見問答'),('/about-data.html','關於本站')]
ORGJ={"@type":"Organization","@id":BASE+"/#publisher","name":"仁禾管理顧問","email":"renhe74123@gmail.com","url":BASE+"/","sameAs":["https://line.me/R/ti/p/@891tcxhu"]}
pages=[]
def ld(*objs): return '<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org","@graph":list(objs)},ensure_ascii=False)+'</script>'
def crumbs(path,trail):
    items=[{"@type":"ListItem","position":1,"name":NAME,"item":BASE+"/"}]+[{"@type":"ListItem","position":k+2,"name":n,"item":BASE+u} for k,(u,n) in enumerate(trail)]
    vis=' / '.join(['<a href="/">首頁</a>']+[f'<a href="{u}">{E(n)}</a>' for u,n in trail[:-1]]+[E(trail[-1][1])]) if trail else ''
    return {"@type":"BreadcrumbList","@id":BASE+path+"#crumbs","itemListElement":items},vis
def page(path,title,desc,body,graph=(),trail=None,lead=''):
    bc,vis=crumbs(path,trail) if trail else (None,'')
    g=[ORGJ]+list(graph)+([bc] if bc else [])
    nav=''.join(f'<a href="{u}"{" class=on" if u==path else ""}>{n}</a>' for u,n in MENU)
    full=f'''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{BASE}{path}"><meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}"><meta property="og:locale" content="zh_TW">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:image" content="{BASE}/og.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/og.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='2' y='2' width='60' height='60' rx='8' fill='%238b6937'/%3E%3Ctext x='32' y='29' font-size='24' font-weight='900' fill='white' text-anchor='middle' font-family='sans-serif'%3E補%3C/text%3E%3Ctext x='32' y='55' font-size='24' font-weight='900' fill='white' text-anchor='middle' font-family='sans-serif'%3E助%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="/gk.css?v={hashlib.md5(open(H+'/gk.css','rb').read()).hexdigest()[:6]}">{ld(*g)}</head><body>
<div class="util"><div class="in"><span>臺灣公部門獎勵・補助計畫整理平台</span><span>資料更新 {E(GEN)}（台北時間）</span></div></div>
<header class="mast"><div class="in"><a class="logo" href="/"><span class="seal" aria-hidden="true"><i>補</i><i>助</i></span><span><b>{NAME}</b><small>GRANT &amp; AWARD DIRECTORY</small></span></a>{AD}</div>
<nav class="menu"><div class="in">{nav}</div></nav></header>
<main class="in body">{('<div class="crumb">'+vis+'</div>') if vis else ''}{('<h1>'+E(title.split(' – ')[0])+'</h1>') if path!='/' else ''}{('<p class="lead">'+lead+'</p>') if lead else ''}{body}</main>
<footer class="foot"><div class="in cols"><div><b>{NAME}</b><p>以主管機關、申請對象與截止日期三種角度整理臺灣中央與地方的獎補助公告，協助企業與團體掌握申請時機。</p></div>
<div><b>瀏覽</b>{''.join(f'<a href="{u}">{n}</a>' for u,n in MENU[1:6])}</div><div><b>說明</b>{''.join(f'<a href="{u}">{n}</a>' for u,n in MENU[6:])}<a href="/sitemap.xml">網站地圖</a></div></div>
<div class="in copy">© {NAME}｜仁禾管理顧問　各計畫內容以主管機關正式公告為準。</div></footer></body></html>'''
    assert '劉靜渡' not in full
    p=OUT+(path+'index.html' if path.endswith('/') else path); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(full); pages.append(path)
def rows(items,show_org=True):
    t='<table class="gt"><thead><tr><th>狀態</th><th>計畫名稱</th>'+('<th class="m-hide">主管機關</th>' if show_org else '')+'<th>收件截止</th></tr></thead><tbody>'
    for i in items:
        t+=(f'<tr><td><span class="st s{ORD.get(i["status"],4)}">{E(i["status"])}</span></td><td><a href="/grants/{i["id"]}.html">{E(i["name"])}</a>'
            f'<div class="sm">{E(i["region"])}・{E(i.get("target") or "")[:40]}</div></td>'+(f'<td class="m-hide"><a href="/agencies/{oslug(i["org"])}.html">{E(i["org"])}</a></td>' if show_org else '')+f'<td class="dl">{E(i.get("deadlineText") or "依公告")}</td></tr>')
    return t+'</tbody></table>'
def itemlist(path,items,name):
    return {"@type":"ItemList","@id":BASE+path+"#list","name":name,"numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":k+1,"url":f"{BASE}/grants/{i['id']}.html","name":i['name']} for k,i in enumerate(items[:50])]}
if os.path.isdir(OUT):
    for d in ('grants','agencies','audiences'): shutil.rmtree(f'{OUT}/{d}',ignore_errors=True)
os.makedirs(OUT,exist_ok=True)
for f in ('gk.css','og.png'): shutil.copy2(f'{H}/{f}',f'{OUT}/{f}')
shutil.copy2(f'{SRC}/data.js',f'{OUT}/data.js')
open(f'{OUT}/CNAME','w').write('grantking.subsidyking.tw\n')
FAQ=[('這個網站整理了哪些獎補助？',f'目前收錄 {len(IT):,} 項仍可查詢的獎勵與補助計畫，主辦單位涵蓋中央各部會、直轄市與縣市政府，以及鄉鎮市區公所。'),
('我要怎麼找到符合自己條件的計畫？','可以從「依申請對象」選擇企業、民間團體、學校或個人，再從「依主管機關」縮小範圍；想掌握時程則看「截止日曆」，依月份排列各計畫的收件截止日。'),
('狀態欄的「開放中」「即將開放」「常態性/依公告」代表什麼？','開放中表示目前在收件期間；即將開放表示已公告但尚未開始收件；常態性/依公告表示全年受理或尚未公布明確時程，需留意主管機關公告。'),
('多久更新一次？','每天清晨自動彙整各機關官網與公開平台的新公告後重新產生網頁，頁首會顯示最後更新時間（台北時間）。'),
('可以直接在這裡送件嗎？','不行。本站只做整理與導覽，每個計畫頁都附主管機關原始公告連結，申請表件與送件方式請依原公告辦理。'),
('「預估下次開放」是怎麼來的？','依同一計畫過去幾年的公告與截止時間推算，只供規劃參考，實際仍以主管機關最新公告為準。'),
('需要有人協助規劃或撰寫申請文件怎麼辦？','可聯繫頁面上的仁禾管理顧問（renhe74123@gmail.com、LINE 官方帳號 @891tcxhu）。')]
def faqld(path): return {"@type":"FAQPage","@id":BASE+path+"#faq","mainEntity":[{"@type":"Question","name":a,"acceptedAnswer":{"@type":"Answer","text":b}} for a,b in FAQ]}
def faqhtml(n=None): return '<div class="faq">'+''.join(f'<details><summary>{E(a)}</summary><p>{E(b)}</p></details>' for a,b in FAQ[:n])+'</div>'
ABOUT=(f'<section class="box" id="about"><h2>關於本站・資料來源與更新頻率</h2><ul><li><b>資料來源：</b>中央部會、各縣市政府與鄉鎮市區公所官方網站公告，並參考政府新聞稿與公開彙整平台。</li>'
       f'<li><b>更新頻率：</b>每日清晨自動更新一次，最近一次為 {E(GEN)}（台北時間）。</li><li><b>收錄規模：</b>現行計畫 {len(IT):,} 項，其中開放收件 {ST["開放中"]} 項、即將開放 {ST["即將開放"]} 項；另保存 109–115 年歷史資料 {D.get("histCount",0):,} 筆。</li>'
       '<li><b>維運：</b>仁禾管理顧問。內容若與主管機關公告不同，以主管機關公告為準。</li></ul></section>')
OPEN=srt([i for i in IT if i['status'] in ('開放中','即將開放')])
NEW=sorted(IT,key=lambda i:i.get('firstSeen') or '',reverse=True)[:10]
DS='WebSite'
web={"@type":"WebSite","@id":BASE+"/#site","url":BASE+"/","name":NAME,"inLanguage":"zh-Hant-TW","publisher":{"@id":BASE+"/#publisher"},"potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint","urlTemplate":BASE+"/search.html?k={kw}"},"query-input":"required name=kw"}}
dset={"@type":"Dataset","@id":BASE+"/#dataset","name":"臺灣公部門獎補助計畫目錄","description":f"整理臺灣中央與地方政府獎勵、補助計畫 {len(IT):,} 項，含主管機關、申請對象、收件截止日與狀態，每日更新。","url":BASE+"/","license":"https://creativecommons.org/licenses/by/4.0/","isAccessibleForFree":True,"creator":{"@id":BASE+"/#publisher"},"dateModified":TODAY,"spatialCoverage":"臺灣","keywords":["獎補助","政府補助","獎勵計畫","補助申請"]}
aud_counts=collections.Counter(t for i in IT for t in i.get('targets',[]))
home=(f'<section class="band"><form action="/search.html"><label>快速搜尋獎補助</label><input name="k" placeholder="輸入關鍵字，例如：數位轉型、文化、青年創業"><button>搜尋</button></form></section>'
 f'<section class="kpi"><div><b>{ST["開放中"]}</b>項 收件中</div><div><b>{ST["即將開放"]}</b>項 即將開放</div><div><b>{len(BIGORG)}</b>個 主管機關分類</div><div><b>{len(IT):,}</b>項 現行計畫</div></section>'
 f'<p class="lead">{NAME}以「誰主辦、誰能申請、何時截止」三個角度，整理臺灣中央與地方政府的獎勵與補助公告，每天更新一次。</p>'
 f'<section class="box"><h2>收件中與即將開放</h2>{rows(OPEN[:15])}<p class="more"><a href="/deadlines.html">查看完整截止日曆 →</a></p></section>'
 '<div class="two"><section class="box"><h2>依申請對象瀏覽</h2><ul class="tiles">'+''.join(f'<li><a href="/audiences/{AUD[k][0]}.html">{AUD[k][1]}<span>{aud_counts[k]}</span></a></li>' for k in AUD if aud_counts[k])+'</ul></section>'
 '<section class="box"><h2>補助件數最多的主管機關</h2><ul class="tiles">'+''.join(f'<li><a href="/agencies/{oslug(o)}.html">{E(o)}<span>{len(ORGS[o])}</span></a></li>' for o in BIGORG[:12])+'</ul><p class="more"><a href="/agencies/">全部主管機關 →</a></p></section></div>'
 f'<section class="box"><h2>最近新增</h2>{rows(NEW)}</section>'
 '<section class="box"><h2>第一次申請？</h2><p>從確認資格、準備公司登記與財務文件，到撰寫計畫書與送件，請看<a href="/guide.html">申請流程與準備文件清單</a>；看不懂公告用語時，可查<a href="/glossary.html">獎補助名詞解釋</a>。</p></section>'
 f'<section class="box"><h2>常見問答</h2>{faqhtml(4)}<p class="more"><a href="/qa.html">更多問答 →</a></p></section>{ABOUT}')
page('/',f'{NAME}｜臺灣政府獎勵與補助計畫查詢・截止日曆','依主管機關、申請對象與截止日期查詢臺灣中央部會與地方政府的獎勵、補助計畫，收件中與即將開放項目一覽，每日更新。',home,[web,dset,itemlist('/',OPEN,'收件中與即將開放的獎補助'),faqld('/')])
# 搜尋頁（前端篩選，資料來自同一份 data.js）
page('/search.html',f'找獎補助 – {NAME}','輸入關鍵字，即時篩選臺灣政府獎勵與補助計畫，可依狀態、主管層級與地區縮小範圍。',
 '<div class="sbar"><input id="k" placeholder="關鍵字"><select id="st"><option value="">全部狀態</option><option>開放中</option><option>即將開放</option><option>常態性/依公告</option><option>已截止</option></select><select id="lv"><option value="">全部層級</option><option>中央</option><option>縣市</option><option>鄉鎮市</option><option>民間/其他</option></select></div><p id="n" class="sm"></p><table class="gt"><thead><tr><th>狀態</th><th>計畫名稱</th><th class="m-hide">主管機關</th><th>收件截止</th></tr></thead><tbody id="tb"></tbody></table>'
 '<script src="/data.js"></script><script>const A=window.BZW_DATA.items,O={"開放中":0,"即將開放":1,"常態性/依公告":2,"已截止":3},e=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));A.sort((a,b)=>(O[a.status]??4)-(O[b.status]??4)||(a.deadline||"9").localeCompare(b.deadline||"9"));'
 'const k=document.getElementById("k");k.value=new URLSearchParams(location.search).get("k")||"";function r(){const w=k.value.trim().toLowerCase(),s=st.value,l=lv.value;const f=A.filter(i=>(!s||i.status==s)&&(!l||i.level==l)&&(!w||(i.name+i.org+(i.target||"")+(i.summary||"")+i.region).toLowerCase().includes(w)));n.textContent="符合 "+f.length+" 項（最多顯示 200 項）";'
 'tb.innerHTML=f.slice(0,200).map(i=>`<tr><td><span class="st s${O[i.status]??4}">${e(i.status)}</span></td><td><a href="/grants/${i.id}.html">${e(i.name)}</a><div class="sm">${e(i.region)}・${e((i.target||"").slice(0,40))}</div></td><td class="m-hide">${e(i.org)}</td><td class="dl">${e(i.deadlineText||"依公告")}</td></tr>`).join("")}[k,st,lv].forEach(x=>x.addEventListener("input",r));r();</script>',
 [{"@type":"SearchResultsPage","@id":BASE+"/search.html#page","name":"找獎補助"}],[('/search.html','找獎補助')])
# 截止日曆
bym=collections.defaultdict(list)
for i in IT:
    d=i.get('deadline') or ''
    if d>=TODAY: bym[d[:7]].append(i)
cal=''.join(f'<section class="box month"><h2>{m[:4]} 年 {int(m[5:])} 月截止（{len(v)} 項）</h2><ol class="tl">'+''.join(f'<li><time>{E(i["deadline"][5:])}</time><a href="/grants/{i["id"]}.html">{E(i["name"])}</a><span class="sm">{E(i["org"])}</span></li>' for i in sorted(v,key=lambda i:i['deadline']))+'</ol></section>' for m,v in sorted(bym.items())[:12])
calitems=sorted([i for v in bym.values() for i in v],key=lambda i:i['deadline'])
page('/deadlines.html',f'獎補助截止日曆 – {NAME}','依月份排列尚未截止的臺灣政府獎勵與補助計畫，掌握每項計畫的收件截止日，提早準備申請文件。',cal or '<p>目前沒有已公告截止日的計畫。</p>',[itemlist('/deadlines.html',calitems,'依截止日排列的獎補助')],[('/deadlines.html','截止日曆')],'只列出已公布截止日期、且尚未截止的計畫；常態受理或未公告日期者請用<a href="/search.html">找獎補助</a>查詢。')
# 主管機關
page('/agencies/',f'依主管機關瀏覽獎補助 – {NAME}','依中央部會、縣市政府與公所等主管機關分類瀏覽獎勵與補助計畫，查看各機關目前受理與即將開放的項目。',
 '<ul class="tiles wide">'+''.join(f'<li><a href="/agencies/{oslug(o)}.html">{E(o)}<span>{len(ORGS[o])}</span></a></li>' for o in BIGORG)+'</ul>',[],[('/agencies/','依主管機關')],f'共 {len(BIGORG)} 個主管機關有 3 項以上計畫；件數較少的機關可用搜尋功能查找。')
for o in BIGORG:
    v=srt(ORGS[o]); op=sum(1 for i in v if i['status']=='開放中'); p=f'/agencies/{oslug(o)}.html'
    rel=[x for x in BIGORG if x!=o and (x[:3]==o[:3])][:6]
    page(p,f'{o}獎補助計畫 – {NAME}',f'{o}主管的獎勵與補助計畫共 {len(v)} 項，目前收件中 {op} 項，附收件截止日與原始公告連結。',
     rows(v,False)+(('<section class="box"><h2>相關機關</h2><ul class="tiles">'+''.join(f'<li><a href="/agencies/{oslug(x)}.html">{E(x)}<span>{len(ORGS[x])}</span></a></li>' for x in rel)+'</ul></section>') if rel else ''),
     [{"@type":"GovernmentOrganization","name":o},itemlist(p,v,f'{o}獎補助')],[('/agencies/','依主管機關'),(p,o)],f'{E(o)}目前列管 {len(v)} 項計畫，其中 {op} 項收件中。')
# 申請對象
for k,(s,lab) in AUD.items():
    v=srt([i for i in IT if k in i.get('targets',[])])
    if not v: continue
    p=f'/audiences/{s}.html'
    page(p,f'適合{lab}的獎補助 – {NAME}',f'整理適合{lab}申請的政府獎勵與補助計畫 {len(v)} 項，依收件狀態與截止日排序。',rows(v[:300]),[itemlist(p,v,f'{lab}可申請的獎補助'),{"@type":"Audience","audienceType":lab}],[('/audiences/','依申請對象'),(p,lab)],f'共 {len(v)} 項，先列收件中與即將開放者（最多顯示 300 項）。')
page('/audiences/',f'依申請對象瀏覽獎補助 – {NAME}','依企業、民間團體、學校研究單位、個人青年等申請身分，找出可以申請的政府獎勵與補助。',
 '<ul class="tiles wide">'+''.join(f'<li><a href="/audiences/{AUD[k][0]}.html">{AUD[k][1]}<span>{aud_counts[k]}</span></a></li>' for k in AUD if aud_counts[k])+'</ul>',[],[('/audiences/','依申請對象')])
# 單筆計畫頁
for i in IT:
    p=f'/grants/{i["id"]}.html'; s=summ(i); sib=[x for x in srt(ORGS[i['org']]) if x['id']!=i['id']][:5]
    kv=[('主管機關',f'<a href="/agencies/{oslug(i["org"])}.html">{E(i["org"])}</a>' if i['org'] in BIGORG else E(i['org'])),('辦理層級',E(i['level'])),('適用地區',E(i['region'])),('申請對象',E(i.get('target') or '')),('收件截止',E(i.get('deadlineText') or '依公告')),('目前狀態',E(i['status']))]
    if i.get('cycle'): kv.append(('歷年辦理週期',E(i['cycle'])))
    if i.get('nextOpen'): kv.append(('下次開放（推估）',E(i['nextOpen'])))
    body=(f'<section class="box"><h2>計畫重點</h2><p>{E(s)}</p></section><table class="kv">'+''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a,b in kv)+'</table>'
          f'<p><a class="btn" href="{E(i["url"])}" target="_blank" rel="noopener nofollow">前往主管機關公告</a>　<a href="/guide.html">申請前準備清單</a></p>'
          +(('<section class="box"><h2>同機關其他計畫</h2><ul>'+''.join(f'<li><a href="/grants/{x["id"]}.html">{E(x["name"])}</a>（{E(x["status"])}）</li>' for x in sib)+'</ul></section>') if sib else ''))
    g={"@type":"MonetaryGrant","@id":BASE+p+"#grant","name":i['name'],"description":s,"url":BASE+p,"funder":{"@type":"GovernmentOrganization","name":i['org']},"sameAs":i['url']}
    page(p,f'{i["name"]}｜{i["org"]} – {NAME}',f'{i["org"]}「{i["name"]}」：{s[:80]}',body,[g],[('/agencies/'+oslug(i['org'])+'.html' if i['org'] in BIGORG else '/search.html',i['org']),(p,i['name'][:30])])
GUIDE='''<section class="box"><h2>一、申請流程</h2><ol class="steps"><li><b>確認資格</b>：核對公告中的申請對象、設立年限、所在地區、產業別與是否有重複申請限制。</li><li><b>確認時程</b>：記下收件起訖日、是否分梯次，以及線上系統或紙本郵寄的截止時間（郵戳或送達為準）。</li><li><b>下載表件</b>：自主管機關公告頁下載最新年度的申請須知、計畫書格式與切結書，不要沿用舊年度格式。</li><li><b>撰寫計畫書</b>：寫清楚現況問題、執行內容、時程、預算編列與預期效益（可量化指標）。</li><li><b>編列經費</b>：區分補助款與自籌款，依須知的科目與比例上限編列。</li><li><b>送件與補件</b>：依指定方式送件，留意補件通知期限。</li><li><b>審查與簽約</b>：可能有書面審查、簡報或實地訪視；核定後依規定簽約、執行與核銷。</li></ol></section>
<section class="box"><h2>二、常見準備文件清單</h2><ul class="check"><li>申請表與計畫書（依當年度格式）</li><li>公司或商業登記證明、立案證書（團體）</li><li>負責人身分證明文件影本</li><li>最近年度財務報表或營業稅申報資料</li><li>無欠稅證明（依主管機關要求）</li><li>勞保或投保人數證明（若資格與員工數有關）</li><li>經費預算表與報價單</li><li>切結書、個資同意書、利益迴避聲明等</li><li>其他佐證：專利、合作意向書、過往成果</li></ul><p class="sm">實際應備文件以各計畫申請須知為準。</p></section>
<section class="box"><h2>三、提高通過率的小提醒</h2><ul><li>提早兩到四週開始準備，預留用印與補件時間。</li><li>計畫目標要對應主管機關的政策方向與評分項目。</li><li>預算合理且有報價佐證，避免集中在單一科目。</li><li>送件前再對一次頁數、格式與簽章。</li></ul></section>'''
page('/guide.html',f'政府補助申請流程與準備文件清單 – {NAME}','從確認資格、時程、撰寫計畫書、編列經費到送件審查，一頁看懂政府獎補助申請流程與常見應備文件。',GUIDE,
 [{"@type":"HowTo","name":"政府獎補助申請流程","step":[{"@type":"HowToStep","name":n} for n in ['確認資格','確認時程','下載表件','撰寫計畫書','編列經費','送件與補件','審查與簽約']]}],[('/guide.html','申請指南')])
GL=[('補助','政府對特定對象或活動提供部分經費，通常需提出計畫並配合自籌款。'),('獎勵','對已有成果或符合條件者給予獎金或獎項，多數不需配合款。'),('捐助','政府對民間團體或財團法人辦理公益事務提供的經費支持。'),
('自籌款','申請者自行負擔的經費，常以占總經費一定比例為門檻。'),('配合款','與自籌款相近，指申請者須搭配補助款投入的資金。'),('梯次','同一年度分次受理收件，每梯次有各自的截止日。'),
('核定','主管機關審查通過並確認補助金額的程序。'),('核銷','計畫執行後，依規定檢附單據與成果報告請領或結算補助款。'),('SBIR','小型企業創新研發計畫，由經濟部及各地方政府辦理，補助中小企業研發。'),
('SIIR','服務業創新研發計畫，協助服務業者開發新服務或新營運模式。'),('計畫書','說明執行內容、時程、預算與預期效益的申請文件，是審查主要依據。'),('KPI／量化指標','可衡量的成果目標，例如營收成長、新增就業或服務人次。'),
('期中／期末報告','執行期間或結束時提交的進度與成果報告。'),('利益迴避','審查或執行人員與申請者有利害關係時應迴避的規定。'),('常態性受理','全年隨到隨審、沒有固定截止日的計畫。')]
page('/glossary.html',f'獎補助名詞解釋 – {NAME}','補助、獎勵、自籌款、梯次、核定、核銷、SBIR 等政府獎補助常見用語的白話解釋。',
 '<dl class="gl">'+''.join(f'<dt id="g{k}">{E(a)}</dt><dd>{E(b)}</dd>' for k,(a,b) in enumerate(GL))+'</dl>',
 [{"@type":"DefinedTermSet","@id":BASE+"/glossary.html#terms","name":"獎補助名詞","hasDefinedTerm":[{"@type":"DefinedTerm","name":a,"description":b} for a,b in GL]}],[('/glossary.html','名詞解釋')])
page('/qa.html',f'常見問答 – {NAME}',f'{NAME}的收錄範圍、更新頻率、狀態說明與使用方式等常見問題。',faqhtml(),[faqld('/qa.html')],[('/qa.html','常見問答')])
page('/about-data.html',f'關於本站與資料來源 – {NAME}',f'{NAME}的資料來源、更新頻率、收錄規模與維運單位說明。',ABOUT+f'<section class="box"><h2>聯絡我們</h2>{AD}</section>',[dset],[('/about-data.html','關於本站')])
# robots / sitemap / llms
open(f'{OUT}/robots.txt','w').write(''.join(f'User-agent: {b}\nAllow: /\n\n' for b in ['GPTBot','OAI-SearchBot','ChatGPT-User','PerplexityBot','ClaudeBot','Claude-SearchBot','anthropic-ai','Google-Extended','Googlebot','Bingbot','Applebot-Extended','CCBot','meta-externalagent','Amazonbot','*'])+f'Sitemap: {BASE}/sitemap.xml\n')
open(f'{OUT}/sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n' for p in pages)+'</urlset>\n')
open(f'{OUT}/llms.txt','w').write(f'''# {NAME}（grantking.subsidyking.tw）
> 臺灣公部門獎勵與補助計畫目錄：以主管機關、申請對象與截止日期整理中央部會、縣市政府與鄉鎮市區公所的公告，現行 {len(IT):,} 項，每日清晨更新（最近：{GEN}，台北時間）。

維運：仁禾管理顧問（renhe74123@gmail.com，LINE 官方帳號：@891tcxhu）。各計畫內容以主管機關公告為準。

## 瀏覽方式
- [找獎補助（關鍵字搜尋）]({BASE}/search.html)
- [截止日曆]({BASE}/deadlines.html)：依月份列出未截止計畫
- [依主管機關]({BASE}/agencies/)：{len(BIGORG)} 個機關分類
- [依申請對象]({BASE}/audiences/)：企業、民間團體、學校研究、個人青年、政府機關
- 單一計畫頁：{BASE}/grants/<編號>.html，含主管機關、對象、截止日、狀態、原始公告連結

## 說明
- [申請流程與準備文件清單]({BASE}/guide.html)
- [獎補助名詞解釋]({BASE}/glossary.html)
- [常見問答]({BASE}/qa.html)
- [關於本站與資料來源]({BASE}/about-data.html)

## 目前收件中（節錄）
'''+''.join(f'- [{i["name"]}]({BASE}/grants/{i["id"]}.html)：{i["org"]}，截止 {i.get("deadlineText") or "依公告"}\n' for i in OPEN[:30]))
print(f'{NAME}：產生 {len(pages)} 頁，改寫摘要使用 {sum(1 for i in IT if str(i["id"]) in CACHE)}/{len(IT)} 筆 → {OUT}'+('（dry-run）' if DRY else ''))
