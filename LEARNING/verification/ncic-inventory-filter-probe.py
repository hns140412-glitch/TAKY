import requests,json
base='https://ncic.re.kr/api/inv/invOrgList.do'
tests=[
 {},
 {'degreeCode':'1014','classCode':'1003'},
 {'pDegreeCode':'1014','pClassCode':'1003'},
 {'degree':'1014','cls':'1003'},
 {'openYear':'2022','classCode':'1003'},
 {'pageSize':'100','openYear':'2022'},
]
for q in tests:
 r=requests.get(base,params=q,timeout=20);j=r.json();rows=j.get('data',{}).get('orgList',[])
 print('QUERY',q,'COUNT',len(rows))
 for x in rows:
  if str(x.get('openYear'))=='2022':
   print(json.dumps({k:x.get(k) for k in ['orgInvNo','degreeCode','classCode','subjectCode','openYear','invName']},ensure_ascii=True))
