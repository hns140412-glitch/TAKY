import re,json
s=open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-korean-inventory-view.html',encoding='utf-8').read()
srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)',s)
print(json.dumps([x for x in srcs if 'inv' in x.lower() or 'org' in x.lower() or 'tree' in x.lower()],ensure_ascii=True,indent=2))
print(json.dumps(srcs,ensure_ascii=True,indent=2))
