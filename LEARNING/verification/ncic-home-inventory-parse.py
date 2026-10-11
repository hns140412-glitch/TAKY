import requests,re,html,json
u='https://ncic.re.kr/'
r=requests.get(u,timeout=20)
r.encoding='utf-8'
s=r.text
pat=re.compile(r"move_view\('org',\s*'([^']+)',\s*'([^']+)',\s*'([^']*)',\s*'([^']+)'\);?[^>]*>.*?<h6>(.*?)</h6>.*?<p>(.*?)</p>",re.S)
rows=[]
for m in pat.finditer(s):
    p=re.sub('<.*?>',' ',m.group(6))
    p=html.unescape(re.sub(r'\s+',' ',p)).strip()
    title=html.unescape(re.sub('<.*?>',' ',m.group(5))).strip()
    rows.append({'orgType':m.group(1),'year':m.group(2),'location':m.group(3),'seq':m.group(4),'title':title,'meta':p})
print('rows',len(rows))
for x in rows:
    print(json.dumps(x,ensure_ascii=False))
