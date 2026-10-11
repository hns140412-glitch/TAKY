import re,json
s=open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-korean-inventory-view.html',encoding='utf-8').read()
nums=sorted(set(re.findall(r'10069\d{3}',s)))
print(json.dumps(nums,ensure_ascii=True))
for n in nums:
 i=s.find(n); print(n,repr(s[max(0,i-180):i+260]))
