import re,json,html
p=r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-korean-inventory-view.html'
s=open(p,encoding='utf-8').read()
rows=[]
for m in re.finditer(r"move_view\('org',\s*'([^']+)',\s*'([^']+)',\s*'([^']*)',\s*'([^']+)'\)",s):
    a=max(0,m.start()-800);b=min(len(s),m.end()+800)
    near=re.sub(r'<[^>]+>',' ',s[a:b])
    near=html.unescape(re.sub(r'\s+',' ',near)).strip()
    rows.append({'args':m.groups(),'near':near[:900]})
print(json.dumps(rows[:100],ensure_ascii=True,indent=2))
