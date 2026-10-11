import re,json
p=r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-social-list.html'
s=open(p,encoding='utf-8').read()
print('len',len(s))
apis=sorted(set(re.findall(r"['\"](/api/inv/[^'\"]+)",s)))
print(json.dumps(apis,ensure_ascii=True,indent=2))
for needle in ['fancytree','source:','ajax','step1','step2','step3','tree','orgList','api/inv']:
 print('\nNEEDLE',needle)
 for m in list(re.finditer(re.escape(needle),s,re.I))[:12]:
  print(m.start(),repr(s[max(0,m.start()-600):m.start()+1800]))
