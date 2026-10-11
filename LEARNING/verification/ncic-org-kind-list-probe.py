import requests,json
j=requests.get('https://ncic.re.kr/api/inv/invOrgKindList.do',timeout=30).json()
open(r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-org-kind-list-2026-10-07.json','w',encoding='utf-8').write(json.dumps(j,ensure_ascii=False,indent=2))
print(json.dumps(j,ensure_ascii=True,indent=2)[:60000])
