import re,json
s=open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-social-list.html',encoding='utf-8').read()
urls=sorted(set(re.findall(r"['\"]([^'\"]*(?:\.do|/api/)[^'\"]*)['\"]",s)))
print(json.dumps(urls,ensure_ascii=True,indent=2))
