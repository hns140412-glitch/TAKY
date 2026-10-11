import re,json
s=open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-korean-inventory-view.html',encoding='utf-8').read()
paths=sorted(set(re.findall(r"['\"](/api/inv/[^'\"]+)",s)))
print(json.dumps(paths,ensure_ascii=True,indent=2))
for needle in ['tree','subject','invOrg','orgTree','children','treeList']:
  print('NEEDLE',needle)
  for m in list(re.finditer(needle,s,re.I))[:12]:
    print(m.start(),repr(s[max(0,m.start()-300):m.start()+700]))
