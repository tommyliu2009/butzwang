#!/usr/bin/env python3
"""獎補助資訊網：用雲端免費模型（router draft）把每筆補助摘要改寫成本站用語，再由另一家免費模型（check）抽核事實。
快取 summary_cache.json（依 id + 原文雜湊），只改寫新/變動項目；失敗則沿用原文。用法：rewrite.py [最多批數]"""
import json,sys,os,hashlib
sys.path.insert(0,'/workspace/shared-data/multi_ai'); sys.path.insert(0,'/workspace/shared-data')
from router import Router, json_of
H=os.path.dirname(os.path.abspath(__file__)); C=f'{H}/summary_cache.json'
cache=json.load(open(C)) if os.path.exists(C) else {}
items=json.load(open('/workspace/butzwang/data.json'))['items']
def hs(i): return hashlib.md5(((i.get('summary') or '')+(i.get('target') or '')).encode()).hexdigest()[:10]
todo=[i for i in items if (i.get('summary') or '').strip() and cache.get(str(i['id']),{}).get('h')!=hs(i)]
todo.sort(key=lambda i:{'開放中':0,'即將開放':1}.get(i['status'],2))
MAXB=int(sys.argv[1]) if len(sys.argv)>1 else 40; B=12
R=Router(site='grantking'); ok=fail=0
for b in range(min(MAXB,(len(todo)+B-1)//B)):
    batch=todo[b*B:(b+1)*B]
    src={str(i['id']):f"{i['name']}｜對象：{i.get('target','')}｜{i['summary']}" for i in batch}
    p=("把下列政府補助的摘要各自改寫成繁體中文的新說法（換句型與用詞，40–120字），只能使用原文已有的事實（日期、金額、對象、梯次），不可新增或推測資訊，不放網址。\n"
       f"輸入：{json.dumps(src,ensure_ascii=False)}\n只輸出 JSON 物件：{{\"id\":\"改寫\",...}}")
    out,mk,err=R.call('draft',p,max_tokens=2500)
    rw=out if isinstance(out,dict) else None
    if not isinstance(rw,dict): fail+=len(batch); continue
    rw={k:v for k,v in rw.items() if k in src and isinstance(v,str) and 15<len(v)<300 and 'http' not in v}
    if not rw: fail+=len(batch); continue
    q=("逐筆比對「原文」與「改寫」，改寫若出現原文沒有的事實（日期、金額、對象、條件）或與原文矛盾，列為 BAD。\n"
       f"{json.dumps({k:{'原文':src[k],'改寫':v} for k,v in rw.items()},ensure_ascii=False)}\n只輸出 JSON：{{\"bad\":[\"id\",...]}}")
    o2,mk2,e2=R.call('check',q,avoid_family=R.family(mk) if mk else None,max_tokens=600)
    chk=o2 if isinstance(o2,dict) else None
    if not isinstance(chk,dict) or not isinstance(chk.get('bad'),list): fail+=len(batch); continue
    bad=set(map(str,chk['bad']))
    for i in batch:
        k=str(i['id'])
        if k in rw and k not in bad: cache[k]={'h':hs(i),'s':rw[k].strip(),'m':mk,'c':mk2}; ok+=1
        else: fail+=1
    json.dump(cache,open(C,'w'),ensure_ascii=False)
print(f'改寫完成 {ok} 筆、未通過/失敗 {fail} 筆、待改寫剩 {max(0,len(todo)-ok)} 筆、快取共 {len(cache)} 筆')
