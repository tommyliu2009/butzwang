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

COUNTIES = ['臺北','新北','桃園','臺中','臺南','高雄','基隆','新竹','嘉義','苗栗','彰化','南投',
            '雲林','屏東','宜蘭','花蓮','臺東','澎湖','金門','連江']

def norm(s): return (s or '').replace('台', '臺').strip()

def level(org):
    o = norm(org)
    if re.search(r'(鄉|鎮|市|區)公所', o): return '鄉鎮市'
    if re.search(r'(縣|市)政府', o): return '縣市'
    if re.search(r'(部|署|委員會)', o): return '中央'
    if re.search(r'(院|局|中心|館|司)', o) and not re.search(r'(信託|基金會|協會|公司)', o): return '中央'
    return '民間/其他'

def region(org, target):
    o = norm(org) + ' ' + norm(target)
    for c in COUNTIES:
        if c in norm(org): return c
    for c in COUNTIES:
        if '設籍' + c in o: return c
    return '全國'

TGT = [('企業', r'企業|公司|業者|商業|工廠|廠商|產業|法人|製造業|服務業|營利事業|雇主|商家|商圈|出版單位|契約容量'), ('民間團體', r'團體|協會|社區|NGO|機構'),
       ('學校/研究', r'學校|校院|研究|大專'), ('個人/青年', r'個人|青年|學生|民眾|農民|新住民'), ('政府機關', r'政府|公所')]
def targets(t):
    r = [k for k, p in TGT if re.search(p, t or '')]
    return r or ['其他']

# ---- 隱私過濾：移除使用者私人雲端檔名、Drive 連結、個人筆記，只保留公開參考 ----
PRIVATE = re.compile(r'使用者|用戶檔案|我的檔案|個人筆記|個人備註|GetGrant|日報|紀錄檔|記錄檔|週期性補助預測|'
                     r'截止時程彙整|彙整報告|地方型SBIR截止彙整|20260920|user_files|'
                     r'drive\.google\.com|docs\.google\.com|googleusercontent', re.I)
PRIV_URL = re.compile(r'https?://(?:drive|docs)\.google\.com/\S*|https?://\S*googleusercontent\.com/\S*')
PRIV_PAREN = re.compile(r'[（(][^（）()]*?(?:使用者|GetGrant|日報|紀錄檔|彙整報告|20260920)[^（）()]*?[）)]')

def scrub(text):
    if not text: return text
    t = PRIV_URL.sub('', text)
    t = PRIV_PAREN.sub('', t)
    parts = re.split(r'(；|;|。)', t)
    keep = []
    for i in range(0, len(parts), 2):
        seg = parts[i]; sep = parts[i+1] if i+1 < len(parts) else ''
        if PRIVATE.search(seg): continue
        if seg.strip(): keep.append(seg.strip() + sep)
    out = ''.join(keep).strip(' ；;')
    return out

def parse_date(s):
    try: return datetime.date.fromisoformat(s.strip())
    except Exception: return None

rows = []
with open(SRC, encoding='utf-8-sig') as f:
    for i, r in enumerate(csv.DictReader(f)):
        if not (r.get('補助名稱') or '').strip(): continue
        dl = parse_date(r.get('截止日期', ''))
        st = (r.get('狀態') or '').strip()
        if dl and dl < today and st == '開放中': st = '已截止'
        rows.append({
            'id': i + 1,
            'name': r['補助名稱'].strip(),
            'org': r.get('主辦單位', '').strip(),
            'level': (r.get('層級') or '').strip() or level(r.get('主辦單位', '')),
            'region': ((lambda g: g if g in ('嘉義市','嘉義縣','新竹市','新竹縣') else g.replace('市','').replace('縣',''))((r.get('地區') or '').strip()) if (r.get('地區') or '').strip() not in ('','全國') else '') or region(r.get('主辦單位', ''), r.get('對象', '')),
            'deadline': dl.isoformat() if dl else None,
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
            'kind': (r.get('資料類型') or '現行').strip(),
        })

for r in rows:
    for k, v in list(r.items()):
        if isinstance(v, str): r[k] = scrub(v)
    if r['url'] and PRIVATE.search(r['url']): r['url'] = ''
    assert not any(isinstance(v, str) and PRIVATE.search(v) for v in r.values()), r['name']

gen = datetime.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
cur = [r for r in rows if r['kind'] != '歷史']
hist = [{k: v for k, v in r.items() if k not in ('cycle','nextOpen','firstSeen','updated','deadlineText','verified','linkStatus') and v not in ('', None, [])} for r in rows if r['kind'] == '歷史']
out = {'generated': gen, 'count': len(cur), 'histCount': len(hist), 'items': cur}
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
print(f'wrote {OUT} ({len(cur)} current, {len(hist)} history, generated {gen})')
