import requests,re,json,html
base='https://ncic.re.kr'
paths={
 'SOCIAL':'/inv/org/list.do?step1=_1&step2=_15&step3=_28',
 'SCIENCE':'/inv/org/list.do?step1=_1&step2=_15&step3=_30',
 'KOREAN':'/inv/org/list.do?step1=_1&step2=_15&step3=_25',
 'MATH':'/inv/org/list.do?step1=_1&step2=_15&step3=_26',
 'ENGLISH':'/inv/org/list.do?step1=_1&step2=_15&step3=_27',
}
s=requests.Session(); h={'User-Agent':'Mozilla/5.0','Accept-Language':'ko-KR,ko;q=0.9'}
for sub,p in paths.items():
 r=s.get(base+p,headers=h,timeout=30); r.encoding='utf-8'
 open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\\ncic-middle-'+sub.lower()+'-list.html','w',encoding='utf-8').write(r.text)
 rows=[]
 for m in re.finditer(r"move_view\('org',\s*'([^']+)',\s*'([^']+)',\s*'([^']*)',\s*'([^']+)'\)",r.text):
  near=r.text[max(0,m.start()-1200):m.end()+1200]
  txt=html.unescape(re.sub(r'<[^>]+>',' ',near))
  txt=re.sub(r'\s+',' ',txt).strip()
  rows.append({'seq':m.group(4),'year':m.group(2),'near':txt[-1000:]})
 print('\n###',sub,'status',r.status_code,'rows',len(rows))
 for x in rows[:40]: print(json.dumps(x,ensure_ascii=True))
