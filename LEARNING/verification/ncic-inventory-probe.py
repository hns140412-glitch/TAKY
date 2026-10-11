import requests, json
u='https://ncic.re.kr/api/inv/invOrgList.do'
r=requests.get(u,timeout=20)
r.encoding='utf-8'
j=r.json()
rows=j.get('data',{}).get('orgList',[])
print('rows',len(rows))
for x in rows:
    if str(x.get('openYear'))=='2022':
        print(json.dumps({k:x.get(k) for k in ['orgInvNo','degreeCode','degreeName','classCode','subjectCode','openYear','openMonth','invName','ref','step','orgNo']},ensure_ascii=False))
