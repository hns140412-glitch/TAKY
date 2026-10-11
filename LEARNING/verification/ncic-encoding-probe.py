import requests,re
s=requests.Session();h={'User-Agent':'Mozilla/5.0'}
g=s.get('https://ncic.re.kr/',headers=h,timeout=20)
m=re.search(rb'name="_csrf" value="([^"]+)"',g.content)
csrf=m.group(1).decode()
r=s.post('https://ncic.re.kr/inv/org/view.do',data={'_csrf':csrf,'nationCd':'1000','orgType':'ogi4','openYear':'2022','location':'','seq':'10069460','menuType':'1'},headers={**h,'Referer':'https://ncic.re.kr/'},timeout=30)
print('content-type',r.headers.get('content-type'),'requests-encoding',r.encoding,'apparent',r.apparent_encoding)
for enc in ['utf-8','euc-kr','cp949','latin1']:
  try:
    t=r.content.decode(enc)
    print(enc,'success','성취기준',t.find('성취기준'),'국어',t.find('국어'),'[9국',t.find('[9국'))
  except Exception as e: print(enc,'ERR',type(e).__name__,str(e)[:80])
