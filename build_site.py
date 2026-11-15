#!/usr/bin/env python3
"""補助王 — 由補助資料庫 CSV 產生 data.json。
用法：python3 build_site.py [CSV路徑]   (預設 /workspace/subsidy/補助資料庫.csv)
每日更新資料庫後重新執行即可。"""
import csv, json, re, sys, datetime, os
from zoneinfo import ZoneInfo

SRC = sys.argv[1] if len(sys.argv) > 1 else '/workspace/subsidy/補助資料庫_full.csv'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
TZ = ZoneInfo('Asia/Taipei')
today = datetime.datetime.now(TZ).date()

# 22 縣市（2026-11-15：新竹縣／新竹市、嘉義縣／嘉義市分開）。顯示名稱沿用短名，只有新竹、嘉義保留縣市字樣。
COUNTY_FULL = ['臺北市','新北市','桃園市','臺中市','臺南市','高雄市','基隆市','新竹市','新竹縣','嘉義市','嘉義縣',
               '苗栗縣','彰化縣','南投縣','雲林縣','屏東縣','宜蘭縣','花蓮縣','臺東縣','澎湖縣','金門縣','連江縣']
def short(c): return c if c[:2] in ('新竹', '嘉義') else c[:-1]
COUNTIES = [short(c) for c in COUNTY_FULL]

def norm(s): return (s or '').replace('台', '臺').strip()

def level(org):
    o = re.sub(r'[（(][^）)]*[）)]', '', norm(org))   # 括號內的「轉知」等不影響層級
    if re.search(r'科學園區|竹科|中科|南科', o) and re.search(r'管理局', o): return '中央'
    if re.search(r'(鄉|鎮|市|區)公所', o): return '鄉鎮市'
    if re.search(r'(縣|市)政府|(縣|市)議會', o): return '縣市'
    if re.search(r'(部|署|委員會)', o): return '中央'
    if re.search(r'(院|局|中心|館|司)', o) and not re.search(r'(信託|基金會|協會|公司)', o): return '中央'
    return '民間/其他'

def counties_in(text):
    """依出現順序找出文字中的縣市（回傳顯示名稱）。「新竹」「嘉義」沒寫縣或市時不猜。"""
    t = norm(text); found = []
    for c in COUNTY_FULL:
        i = t.find(c)
        if i >= 0: found.append((i, short(c)))
    for c in COUNTY_FULL:
        sc = c[:2]
        if sc in ('新竹', '嘉義'): continue
        i = t.find(sc)
        if i >= 0 and short(c) not in [f for _, f in found]: found.append((i, short(c)))
    found.sort()
    out = []
    for _, c in found:
        if c not in out: out.append(c)
    return out

def regions(org, area, target, lv):
    a = norm(area)
    if a.startswith('全國'): return ['全國']
    if a:
        cs = counties_in(a)
        if cs: return cs
    if lv == '中央':   # 中央機關（含科學園區管理局）不因機關名稱含地名就歸到縣市
        cs = [c for c in COUNTIES if '設籍' + c in norm(target)]
        return cs or ['全國']
    cs = counties_in(org)
    if cs: return cs[:1]
    cs = [c for c in COUNTIES if '設籍' + c in norm(target)]
    return cs or ['全國']

def region(org, target):   # 舊介面相容
    return '、'.join(regions(org, '', target, level(org)))

TGT = [('企業', r'企業|公司|業者|商業|工廠|廠商|產業|法人|製造業|服務業|營利事業|雇主|商家|商圈|出版單位|契約容量'), ('民間團體', r'團體|協會|社區|NGO|機構'),
       ('學校/研究', r'學校|校院|研究|大專'), ('個人/青年', r'個人|青年|學生|民眾|農民|新住民'), ('政府機關', r'政府|公所')]
def targets(t):
    r = [k for k, p in TGT if re.search(p, t or '')]
    return r or ['其他']

# ---- 隱私過濾（2026-11-15 修正）----
# 私人筆記只會出現在「備註/參考連結」欄，所以一般字眼（使用者、日報、個人筆記…）只在備註欄過濾；
# 以前全欄位過濾，把「長期照顧服務使用者自付額補助」等正式名稱、「實際供農業使用者」等摘要句誤刪。
# Drive／Docs 連結、GetGrant 等明確私人標記則所有欄位都擋。
PRIVATE = re.compile(r'使用者|用戶檔案|我的檔案|個人筆記|個人備註|GetGrant|日報|紀錄檔|記錄檔|週期性補助預測|'
                     r'截止時程彙整|彙整報告|地方型SBIR截止彙整|20260920|user_files|'
                     r'drive\.google\.com|docs\.google\.com|googleusercontent', re.I)
STRONG = re.compile(r'GetGrant|週期性補助預測|彙整報告|地方型SBIR截止彙整|20260920|user_files|'
                    r'drive\.google\.com|docs\.google\.com|googleusercontent', re.I)
PRIV_URL = re.compile(r'https?://(?:drive|docs)\.google\.com/\S*|https?://\S*googleusercontent\.com/\S*')
PRIV_PAREN = re.compile(r'[（(][^（）()]*?(?:使用者|GetGrant|日報|紀錄檔|彙整報告|20260920)[^（）()]*?[）)]')

def scrub(text, pat=PRIVATE, paren=True):
    if not text: return text
    t = PRIV_URL.sub('', text)
    if paren: t = PRIV_PAREN.sub('', t)
    parts = re.split(r'(；|;|。)', t)
    keep = []
    for i in range(0, len(parts), 2):
        seg = parts[i]; sep = parts[i+1] if i+1 < len(parts) else ''
        if pat.search(seg): continue
        if seg.strip(): keep.append(seg.strip() + sep)
    out = ''.join(keep).strip(' ；;')
    return out

def calc_status(st, start, dl, today):
    """狀態自動轉換（2026-11-15）：依「受理開始日」與「截止日期」在 即將開放／開放中／已截止 間切換。
    常態性/依公告、歷史(已結束) 不動（常態性有截止日且已過才改已截止）。"""
    if st == '歷史(已結束)': return st
    if dl and dl < today:
        return '已截止' if st in ('開放中', '即將開放', '常態性/依公告', '') else st
    if start:
        if start > today: return '即將開放' if st in ('開放中', '即將開放', '已截止', '') else st
        if st in ('即將開放', '') or (st == '已截止' and dl and dl >= today): return '開放中'
    return st

def parse_date(s):
    try: return datetime.date.fromisoformat(s.strip())
    except Exception: return None

rows = []
with open(SRC, encoding='utf-8-sig') as f:
    for i, r in enumerate(csv.DictReader(f)):
        if not (r.get('補助名稱') or '').strip(): continue
        dl = parse_date(r.get('截止日期', ''))
        sd = parse_date(r.get('受理開始日', '') or '')
        st = calc_status((r.get('狀態') or '').strip(), sd, dl, today)
        lv = (r.get('層級') or '').strip()
        if lv not in ('中央', '縣市', '鄉鎮市', '民間/其他'): lv = level(r.get('主辦單位', ''))   # 「地方」等非標準值重新判斷
        if level(r.get('主辦單位', '')) == '中央' and re.search(r'科學園區', r.get('主辦單位', '')): lv = '中央'
        rg = regions(r.get('主辦單位', ''), r.get('地區', ''), r.get('對象', ''), lv)
        rows.append({
            'id': i + 1,
            'name': r['補助名稱'].strip(),
            'org': r.get('主辦單位', '').strip(),
            'level': lv,
            'region': '、'.join(rg),
            'regions': rg,
            'deadline': dl.isoformat() if dl else None,
            'start': sd.isoformat() if sd else None,
            'deadlineText': (r.get('截止日期') or '').strip(),
            'target': r.get('對象', '').strip(),
            'targets': targets(r.get('對象', '')),
            'summary': r.get('摘要', '').strip(),
            'url': r.get('原始連結', '').strip(),
            'sourceType': r.get('來源類型', '').strip(),
            'firstSeen': r.get('首次收錄日', '').strip(),
            'updated': r.get('最後更新日', '').strip(),
            'verified': (r.get('最後核實日期') or '').strip(),
            'linkStatus': (r.get('連結狀態') or '').strip(),
            'status': st,
            'cycle': r.get('週期規律', '').strip(),
            'nextOpen': r.get('預估下次開放', '').strip(),
            'notes': r.get('備註/參考連結', '').strip(),
            'year': (r.get('年度') or '').strip(),
            'parent': (r.get('所屬計畫') or '').strip(),
            'kind': (r.get('資料類型') or '').strip() or '現行',
        })

for r in rows:
    for k, v in list(r.items()):
        if not isinstance(v, str): continue
        r[k] = scrub(v) if k == 'notes' else scrub(v, STRONG, paren=False)
    if r['url'] and STRONG.search(r['url']): r['url'] = ''
    assert not (r['notes'] and PRIVATE.search(r['notes'])), r['name']
    assert not any(isinstance(v, str) and STRONG.search(v) for v in r.values()), r['name']
    if not r['name']: print('WARN 名稱空白', r['id'])

gen = datetime.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
# 最後抓取來源時間（由 /workspace/subsidy/daily_fetch.py 或每日例行工作寫入）
fetched = ''
try:
    fetched = json.load(open('/workspace/subsidy/last_fetch.json', encoding='utf-8')).get('time', '')
except Exception: pass
cur = [r for r in rows if r['kind'] != '歷史']
hist = [{k: v for k, v in r.items() if k not in ('cycle','nextOpen','firstSeen','updated','deadlineText','verified','linkStatus','regions','start') and v not in ('', None, [])} for r in rows if r['kind'] == '歷史']
out = {'generated': gen, 'fetched': fetched, 'count': len(cur), 'histCount': len(hist), 'items': cur}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
with open(OUT[:-2], 'w', encoding='utf-8') as f:
    f.write('window.BZW_DATA=' + json.dumps(out, ensure_ascii=False) + ';')
import glob as _g
for old in _g.glob(os.path.join(os.path.dirname(OUT), 'data_hist*.js')): os.remove(old)
years = sorted({h.get('year','') for h in hist if h.get('year')}, reverse=True)
for y in years:
    with open(os.path.join(os.path.dirname(OUT), f'data_hist_{y}.js'), 'w', encoding='utf-8') as f:
        f.write('(window.BZW_HIST=window.BZW_HIST||{})[%s]=' % json.dumps(y) + json.dumps([h for h in hist if h.get('year')==y], ensure_ascii=False, separators=(',',':')) + ';')
out['histYears'] = {y: sum(1 for h in hist if h.get('year')==y) for y in years}
with open(OUT[:-2], 'w', encoding='utf-8') as f:
    f.write('window.BZW_DATA=' + json.dumps(out, ensure_ascii=False) + ';')
rows = cur
# 快取版本號：每次建置自動更新 data.js／app.js／style.css 的 ?v=（2026-11-15）
VER = datetime.datetime.now(TZ).strftime('%Y%m%d%H%M')
for hp in _g.glob(os.path.join(os.path.dirname(OUT), '*.html')):
    h0 = open(hp, encoding='utf-8').read()
    h1 = re.sub(r'((?:data|app|style)\.(?:js|css))\?v=\w+', r'\1?v=' + VER, h0)
    # 頁尾時間直接寫進 HTML（搜尋引擎或 JS 未載入時不再顯示「—」）
    h1 = re.sub(r'<b id="updated">[^<]*</b>', f'<b id="updated">{gen}</b>', h1)
    h1 = re.sub(r'<b id="fetched">[^<]*</b>', f'<b id="fetched">{fetched or "—"}</b>', h1)
    h1 = re.sub(r'<span id="total">[^<]*</span>', f'<span id="total">{len(cur)}</span>', h1)
    if h1 != h0: open(hp, 'w', encoding='utf-8').write(h1)
print(f'wrote {OUT} ({len(cur)} current, {len(hist)} history, generated {gen})')
