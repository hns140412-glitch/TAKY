import requests,re,html,os
s=requests.Session()
h={'User-Agent':'Mozilla/5.0','Accept-Language':'ko-KR,ko;q=0.9'}
g=s.get('https://ncic.re.kr/',headers=h,timeout=30)
g.encoding='utf-8'
m=re.search(r'<form[^>]*name="view_form"[\s\S]*?name="_csrf" value="([^"]+)"',g.text)
csrf=m.group(1)
print('csrf',csrf,'cookies',s.cookies.get_dict())
data={'_csrf':csrf,'nationCd':'1000','orgType':'ogi4','openYear':'2022','location':'','seq':'10069460','menuType':'1'}
r=s.post('https://ncic.re.kr/inv/org/view.do',data=data,headers={**h,'Referer':'https://ncic.re.kr/'},timeout=30)
r.encoding='utf-8'
print('post',r.status_code,r.url,len(r.text))
p=r'D:\Git PWA\TAKY\LEARNING\data\official-snapshots\ncic-middle-korean-inventory-view.html'
open(p,'w',encoding='utf-8').write(r.text)
for needle in ['[9국','성취기준','듣기','말하기','10069460','orgInvNo','국어']:
 i=r.text.find(needle);print(needle,i)
 if i>=0: print(re.sub('<.*?>',' ',r.text[max(0,i-500):i+3000])[:3500])
