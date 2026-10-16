#!/usr/bin/env python3
"""Archi Grow Seoul integrated-review *sample structure* adapter.
REA methodology: source fingerprint -> slide object decomposition -> semantics and
presentation pattern -> scrub sample project data -> create editable GB7 draft.
No AI/API, official authority promotion, external delivery, or model calls.
Uses Python stdlib to preserve exact source OOXML layout/style without extra installs.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
P='{'+NS['p']+'}'
A='{'+NS['a']+'}'
EMU_IN=914400
SOURCE=Path(r'D:\#. BACKUP\다운로드\통합심의서식\통합심의서식\정비사업  통합심의위원회 발표 자료 서식(건축, 경관).pptx')
DEST=Path(r'D:\Git PWA\TAKY_AI_WORKBENCH\10_PROJECTS\TAKY_ARCHI-GROW')
BASE=Path(r'D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE')
FORMING=BASE/'GB7_SEOUL_INTEGRATED_FORMING_20261016.json'
OUT_PPTX=DEST/'GB7_서울시통합심의_원본표현적용_작업초안_20261016.pptx'
OUT_CONTRACT=DEST/'GB7_서울시통합심의_페이지별_표현분석_20261016.json'
PAGE_TITLES={
1:'표지·사례식별',2:'공통·분야 구분',3:'목차·장표 체계',
4:'통합심의 대상·공통목차',5:'사업개요와 상정내용',
6:'항공사진·주변현황',7:'현황 사진·주변도로',8:'사업추진경위 타임라인',
9:'정비계획·토지이용',10:'기정·변경 결정도',11:'토지이용계획 면적표',
12:'사업구역 경계 변화표',13:'획지별 용적률 계획',14:'용적률 적용체계·산식',
15:'금회상정안 주요변경 비교',16:'주택공급·세대 구성 비교',17:'구간 전환',
18:'사전검토 의견 총괄',19:'의견 조치율·페이지 증거',20:'의견·반영 전후 도면',
21:'의견·조치 상세',22:'건축·경관 구간 전환',
23:'건축계획 개념 서사',24:'배치·경관 분석 다이어그램',
25:'특별건축구역/완화 조건',26:'법정 vs 계획 수치 비교',
27:'배치 및 동선 계획',28:'부지 레벨·경사 검토',
29:'발코니·벽면율 완화 근거',30:'주민공동시설 용적률 완화',
31:'기정계획 대비 배치·층수',32:'기준층 평면',
33:'소방·전기차·침수 대응',34:'배치 및 레벨 도면',
35:'대지 종횡 단면 확대',36:'인접지·도로 단면',
37:'고저차·인접 건물 단면',38:'4면 입면·스카이라인',
39:'조감도',40:'외부공간·공동시설 배치',
41:'조경계획 총괄',42:'조경구적도',43:'식재계획',
44:'부서 검토의견 총괄',45:'검토의견 근거페이지',46:'조치 전후 비교',
47:'경관분야 체크리스트',48:'경관전략 목표',
49:'통경축·배치',50:'입면 디자인 평가',
51:'친환경 의무기준',52:'녹색건축 환경성능',
53:'에너지·설비 시스템',54:'소방방재 설비 계획',
55:'벽면율 산출근거',56:'발코니 산출근거',57:'우수디자인 및 완화 체크',
58:'도시 공공성·주요 질문응답',59:'마무리·참고자료'}
SECTION={
'공통':list(range(1,18)),
'사전검토':list(range(18,23))+list(range(44,47)),
'건축·경관':list(range(23,44))+list(range(47,60))}
# Only generic printed labels are retained. The source's example facts are not inherited.
KEEP={x for x in (
'공 통','공통','사전검토','검토의견','주관부서','상정개요','상정내용','위치 및 주변현황',
'사업부지현황','정비계획','주요변경사항','사업추진경위','위치도','주변현황도',
'용적률 계획','용적률 적용체계','허용용적률','상한(정비계획)용적률','구역면적',
'대지면적','위 치','위치','건축용도','건축규모','건축구조','지역지구','법정최고층수',
'기 정','변 경','금회상정안','토지이용계획','주택공급계획','총괄표',
'협 의 의 견','조 치 계 획','반영여부','반 영 전','반 영 후','조치의견','페이지',
'건축/경관','건 축','경 관','건축계획개념','건축심의 완화사항','설계개요',
'부대복리시설 계획','조감도 및 투시도','배치 및 동선계획','입면계획',
'외부공간 및 조경계획','분야별계획','배치도','조감도','조경계획','조경구적도',
'식재계획','공원 조치계획','교육 조치계획','정면도','우측면도','배면도','좌측면도',
'검토항목','친환경','기계설비','전기/통신','소방/방재',
'법정 기준','설계계획','적용내용','적용여부','구 분','구분','면 적','비 고',
'면적(㎡)','비율 (%)','계획','법정','구 역 명'
)}
FORBIDDEN=re.compile('장위|성북|사랑제일|돌곶이|장위초|북서울꿈의숲|상길례|장위시장|상정안건개요 613|정비계획 274\\.38')
SRC_IDENTIFIERS=['장위','성북','사랑제일','돌곶이','장위초','북서울꿈','91,362','94,037','613세대','273.09%','274.38%']

def sha(b):return hashlib.sha256(b).hexdigest()
def s_text(obj):
    return ''.join(e.text or '' for e in obj.iter() if e.tag==A+'t')
def texts(slide):
    return [x.text or '' for x in slide.iter(A+'t') if x.text]
def geom(el):
    xfrm=el.find('./p:spPr/a:xfrm',NS) or el.find('./p:xfrm',NS)
    if xfrm is None:return None
    off=xfrm.find('./a:off',NS); ext=xfrm.find('./a:ext',NS)
    if off is None or ext is None:return None
    return [int(off.get('x','0')),int(off.get('y','0')),int(ext.get('cx','0')),int(ext.get('cy','0'))]
def new_shape(box,name,label,fill='F3F6FA',stroke='B4C5D8',font=1170,textcolor='29465F'):
    x,y,cx,cy=box
    sp=ET.Element(P+'sp')
    n=ET.SubElement(sp,P+'nvSpPr'); nv=ET.SubElement(n,P+'cNvPr')
    nv.set('id','0');nv.set('name',name)
    ET.SubElement(n,P+'cNvSpPr');ET.SubElement(n,P+'nvPr')
    prop=ET.SubElement(sp,P+'spPr'); xx=ET.SubElement(prop,A+'xfrm')
    ET.SubElement(xx,A+'off',{'x':str(x),'y':str(y)})
    ET.SubElement(xx,A+'ext',{'cx':str(cx),'cy':str(cy)})
    pg=ET.SubElement(prop,A+'prstGeom',{'prst':'rect'});ET.SubElement(pg,A+'avLst')
    sf=ET.SubElement(prop,A+'solidFill');ET.SubElement(sf,A+'srgbClr',{'val':fill})
    ln=ET.SubElement(prop,A+'ln',{'w':'12700'})
    ET.SubElement(ET.SubElement(ln,A+'solidFill'),A+'srgbClr',{'val':stroke})
    body=ET.SubElement(sp,P+'txBody')
    ET.SubElement(body,A+'bodyPr',{'wrap':'square','anchor':'ctr','lIns':'76200','rIns':'76200'})
    ET.SubElement(body,A+'lstStyle')
    for line in label.split('\n'):
        ap=ET.SubElement(body,A+'p'); ET.SubElement(ap,A+'pPr',{'algn':'ctr'})
        ar=ET.SubElement(ap,A+'r');rpr=ET.SubElement(ar,A+'rPr',{'lang':'ko-KR','sz':str(font)})
        ET.SubElement(ET.SubElement(rpr,A+'solidFill'),A+'srgbClr',{'val':textcolor})
        ET.SubElement(ar,A+'t').text=line
    return sp

def eligible(txt):
    clean=re.sub(r'\s+',' ',txt).strip()
    return clean in KEEP

def layout_kind(page,root,slide_w,slide_h):
    kinds=[x for x in list(root.find('.//p:spTree',NS) or [])]
    imag=sum(x.tag==P+'pic' for x in kinds)
    tabs=sum(x.tag==P+'graphicFrame' for x in kinds)
    texts_=sum(x.tag==P+'sp' and bool(s_text(x).strip()) for x in kinds)
    # Named purpose derives from source slide + geometry, not from inventing project facts.
    if page in (4,5,11,12,13,14,15,16,19,26,29,30,44,45,47,51,55,56,57): typ='표·숫자 근거형'
    elif page in (6,7,10,24,27,28,31,32,33,34,35,36,37,38,39,40,41,42,43,48,49,50):typ='도면·사진·시각설명형'
    elif page in (18,20,21,46):typ='협의의견·전후비교형'
    elif page in (8,23,53,54,58):typ='흐름·서사·설명형'
    else:typ='구분·전환형'
    return typ, imag, tabs,texts_

PAGE_HINTS={
 5:('좌측: 사업개요/상정내용, 우측: 축척·방위가 있는 위치도','GB7 현행 고시·설계개요 동일 REV'),
 8:('결정일 → 심의결과 → 설계 변경 영향 순으로 시간축 작성','법적 효력 있는 공식 결정고시'),
 11:('기정·변경·증감 면적을 단위와 계산근거까지 나란히','면적 산출 원본 및 정비계획 결정도'),
 14:('허용/상한/계획 용적률을 구분하고 근거 산식을 병기','동일 획지 산식, 공공기여/인센티브 협의'),
 15:('기정·전차 심의·금회 상정안을 같은 행에서 수치비교','각 REV 승인 도서·공식 협의 기록'),
 19:('의견 총괄·반영수·부분반영·미반영 페이지를 증거로 묶기','분야별 의견 공문·조치 회신'),
 20:('의견 원문/조치계획과 도면의 전후 이미지를 병치','의견번호, 동일 축척 전후 도면'),
 24:('건축개념을 한 문장 결론 + 한 장의 도식으로 제시','실제 배치·통경축·건축계획 의도'),
 29:('법정 벽면율·발코니 산출값과 완화 신청을 도해','현행 건축심의 기준·실제 상세도'),
 31:('층수·높이 변화는 피난/소방 대상과 코어·피난구역을 재계산','GB7-FIRE-A03/A04 | 현재 56층·59층 혼재, 소스 잠금 HOLD'),
 32:('기준층 코어: 독립 전실·계단 이격·피난경로·승강장 함께 검토','GB7-FIRE-A03/A05/A07 | 서울시 2024 3-1·3-3'),
 35:('단면: 피난안전구역·제연샤프트·피난층·지하실 침수대책','GB7-FIRE-A03/A04/A08/A09 | 서울시 2024 3-1·3-2·3-5'),
 39:('주요 조망점 실사진과 동일 카메라 조감도를 합성','동일 REV 모델링 및 현황 사진'),
 43:('조경구적·수목/포장/유지관리 항목을 도면 연계','경관·조경 심의 해당 여부'),
 47:('경관 평가 체크리스트/적합근거/조망점을 짝지어','도시경관 지침 적용 범위 확인'),
 51:('녹색건축 의무·권장과 적용계획을 혼동 없이 표시','현행 서울시 녹색건축 설계기준'),
 55:('벽면/창면적 도해와 산식/완화기준을 한 장으로','외피 면적 계산 도면 및 현행 규정'),
 56:('발코니 길이/면적과 삭제비율을 색상으로 비교','단위세대 평면도·현행 심의기준'),
 27:('배치계획: 차량 2방향 접근, 동별 소방차 활동공간을 교통동선과 함께 검증','GB7-FIRE-A01/A02 | 서울시 2024 4-1·4-2 | 최신 적용성 HOLD'),
  33:('소방차, 지하 EV, 침수 및 방화구획의 건축도면 반영 관계','GB7-FIRE-A01/A07/A09 | 배치도·주차계획 동일 REV'),
  34:('배치 평면: 소방차 회차/전용구역/고가차 동선과 구조 하중','GB7-FIRE-A01/A02 | 서울시 2024 4-1·4-2'),
  36:('단면·레벨: 층별 피난 동선/기계실과 피난구역 공간 분리','GB7-FIRE-A04/A06 | 같은 REV 층별 프로그램'),
  37:('피난안전구역 층/면적/외벽구획·복도·수직코어를 검증','GB7-FIRE-A04 | 서울시 2024 3-2 (층수=확정 아님)'),
  38:('입면: 소방관 진입창·피난시설·소방차 접근 면 연계','GB7-FIRE-A02/A06 | 서울시 2024 4-3'),
  40:('옥상: 대피공간과 기계실/태양광·수직피난계단 간섭 검증','GB7-FIRE-A06 | 서울시 2024 3-4'),
  53:('기계·전기: 급수·고가수조·이중화·DA·제연공간 확보','GB7-FIRE-A08 | 건축 단면과 설비계통도 연결'),
  54:('소방방재: 건축 코어/제연/구획/차량 접근/방재실을 추적','GB7-FIRE-A01~A11 | 건축 도면↔사전검토 의견'),
  58:('통합심의 답변: 피난 시뮬레이션의 건축 수정 증거 제시','GB7-FIRE-A10/A11 | 검토의견·수정 REV 연결'),
  58:('위원회 예상질문에 도면 번호와 근거값으로 답하기','건축·경관 사전검토의견 및 협의')
}
def build():
    f=json.loads(FORMING.read_text(encoding='utf-8'))
    if f.get('namespace')!='ARCHI_GROW/GB7':raise ValueError('WRONG_PROJECT')
    if not SOURCE.is_file():raise FileNotFoundError(SOURCE)
    if not f.get('forming_sections') or len(f['forming_sections'])!=11:raise ValueError('MISSING_FORMING')
    fire=f.get('fire_architecture_integration',{})
    if len(fire.get('rules',[]))!=11:raise ValueError('FIRE_ARCHITECTURE_MAPPING_MISSING')
    source_sha=sha(SOURCE.read_bytes())
    if source_sha!='bacd9bc6b539e073acbd63c5c942524346505cff7548961ac7cb03fb04a94bed':
        raise ValueError('OFFICIAL_SOURCE_SHA_CHANGED')
    with zipfile.ZipFile(SOURCE) as inz:
        meta=ET.fromstring(inz.read('ppt/presentation.xml'))
        sz=meta.find('.//p:sldSz',NS)
        width,height=int(sz.get('cx')),int(sz.get('cy'))
        if width<1000000 or height<1000000:raise ValueError('BAD_SLIDE_SIZE')
        records=[]; updated={}
        slides=sorted((k for k in inz.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',k)),key=lambda v:int(re.search(r'(\d+)\.xml$',v).group(1)))
        if len(slides)!=59:raise ValueError('SOURCE_SLIDE_COUNT_CHANGED')
        for page,file in enumerate(slides,1):
            root=ET.fromstring(inz.read(file))
            tree=root.find('.//p:spTree',NS)
            if tree is None:raise ValueError('MISSING_SHAPE_TREE:'+file)
            typ,image_count,table_count,txtcount=layout_kind(page,root,width,height)
            blocks=[]; cleaned=0; preserved=0; pic_replace=0
            colors=Counter();font_sizes=Counter()
            for elem in list(tree):
                tag=elem.tag
                if tag not in {P+'sp',P+'pic',P+'graphicFrame'}:continue
                bb=geom(elem)
                raw=s_text(elem)
                if tag==P+'sp':
                    for pr in elem.iter(A+'rPr'):
                        if pr.get('sz'):font_sizes[int(pr.get('sz'))]+=1
                    for clr in elem.iter(A+'srgbClr'):
                        if clr.get('val'):colors[clr.get('val')]+=1
                    if raw.strip():
                        keep=eligible(raw)
                        tnodes=list(elem.iter(A+'t'))
                        if tnodes:
                            tnodes[0].text=raw if keep else ''
                            for t in tnodes[1:]:t.text=''
                        cleaned+=not keep
                        preserved+=bool(keep)
                else:
                    if not bb:continue
                    # Retain object bounding boxes but remove foreign-site photographs, maps,
                    # captured charts and their embedded table cell data.
                    placeholder=new_shape(bb,'GB7_SOURCE_SLOT_'+str(page)+'_'+str(pic_replace+1),
                        '동일 REV 도면·사진·표 배치' if tag==P+'pic' else '강북7 검증 수치·도표 배치')
                    at=list(tree).index(elem)
                    tree.remove(elem);tree.insert(at,placeholder)
                    pic_replace+=1
                if bb:
                    blocks.append({'kind':tag.split('}')[-1],'box_ratio':[round(bb[0]/width,4),round(bb[1]/height,4),round(bb[2]/width,4),round(bb[3]/height,4)],
                                   'example_text_sample':raw.strip()[:90], 'sample_text_removed':tag!=P+'sp' or not eligible(raw)})
            # Consistent prominent stage title, with original geometry still beneath.
            title=PAGE_TITLES[page]
            overlay=new_shape([width-int(4.65*EMU_IN),0,int(4.45*EMU_IN),int(.62*EMU_IN)],
                              'TAKY_GB7_HEADER','강북7구역 통합심의 검토안 | '+f'{page:02d}',
                              fill='244B75',stroke='244B75',font=1310,textcolor='FFFFFF')
            tree.append(overlay)
            guide=PAGE_HINTS.get(page,('이 페이지는 '+title+'을 위한 공통 표현 규칙을 사용','현재 도면·협의·법정 적용성 원천 대기'))
            callout=new_shape([int(.56*EMU_IN),int(.90*EMU_IN),int(6.3*EMU_IN),int(1.16*EMU_IN)],
                             'TAKY_GB7_EDITING_GUIDE',
                             '표현 | '+typ+' / '+title+'\n'+guide[0]+'\n근거 | '+guide[1],
                             fill='EAF2F7',stroke='96BBCB',font=1310)
            tree.append(callout)
            foot=new_shape([int(.55*EMU_IN),height-int(.72*EMU_IN),width-int(1.1*EMU_IN),int(.30*EMU_IN)],
                           'TAKY_EVIDENCE_GATE',
                           'GB7 작성용 · 현행 원천/도면/법령/협의의견 검증 전 제출 금지',
                           fill='F8F0DC',stroke='ECD39B',font=1030)
            tree.append(foot)
            # Nested slide groups can contain site-specific photos, charts and screenshots.
            # These are NOT reusable architecture layout: neutralize them visually.
            for grp in list(root.iter(P+'grpSp')):
                for child in list(grp):
                    if child.tag in {P+'pic',P+'graphicFrame'}:
                        grp.remove(child)
                        pic_replace+=1
            # Some Office slides nest editable text in groups, not direct spTree.
            # Mask those too; whitelist only generic section/field labels and our own slots.
            for t in root.iter(A+'t'):
                val=t.text or ''
                if val and not (eligible(val) or val.startswith(('강북7구역','동일 REV','작업 초안','GB7 |','GB7 작성용','표현 |','근거 |')) or val in guide):
                    t.text=''
                    cleaned+=1
            for item in root.iter():
                for key,value in list(item.attrib.items()):
                    if key.endswith(('name','descr','title')) and any(s in value for s in SRC_IDENTIFIERS):
                        item.set(key,'GB7_masked_sample_artifact')
            output_xml=ET.tostring(root,encoding='utf-8',xml_declaration=True)
            if any(b.encode('utf-8') in output_xml for b in SRC_IDENTIFIERS):
                raise ValueError('SOURCE_PLACE_NAME_LEAK_ON_SLIDE_'+str(page))
            updated[file]=output_xml
            records.append({
                'source_page':page,'name':title,
                'section':next((k for k,v in SECTION.items() if page in v),'참고/기타'),
                'visual_pattern':typ,'source_text_shapes':txtcount,'source_picture_shapes':image_count,
                'source_table_or_chart_shapes':table_count,
                'masked_text_shapes':cleaned,'retained_generic_labels':preserved,
                'neutralized_picture_or_table_slots':pic_replace,
                'dominant_colors':[{'rgb':c,'count':v} for c,v in colors.most_common(6)],
                'font_sizes_pt':[{'points':round(c/100,1),'count':v} for c,v in font_sizes.most_common(5)],
                'object_positions':blocks[:40],
                'fire_architecture_rule_refs':[x['id'] for x in fire['rules'] if page in x['slides']],
                'data_requirements':{'raw_project_revision':'HOLD','same_rev_drawings':'HOLD','legal_rule_version':'HOLD','approval':'NOT_GRANTED'}
            })
        DEST.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(OUT_PPTX,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zout:
            for z in inz.infolist():
                payload=updated.get(z.filename)
                if payload is None:
                    payload=inz.read(z.filename)
                if re.fullmatch(r'ppt/(slideMasters/slideMaster|slideLayouts/slideLayout)[0-9]+[.]xml',z.filename):
                    design_root=ET.fromstring(payload)
                    changed=False
                    for tag in design_root.iter(A+'t'):
                        val=tag.text or ''
                        if any(s in val for s in SRC_IDENTIFIERS) or '000구역' in val:
                            tag.text='강북7구역 통합심의 검토안'
                            changed=True
                    if changed:
                        payload=ET.tostring(design_root,encoding='utf-8',xml_declaration=True)
                zout.writestr(z,payload)
    contract={
        'schema':'TAKY_ARCHI_GROW_GB7_SEOUL_REA_VISUAL_CONTRACT_V1',
        'mode':'EDITABLE_SAMPLE_LAYOUT_APPLICATION_NOT_OFFICIAL_SUBMISSION',
        'source_file':str(SOURCE),'source_sha256':source_sha,
        'candidate_pptx':str(OUT_PPTX),'candidate_sha256':sha(OUT_PPTX.read_bytes()),
        'size_emu':[width,height],'slide_count':len(records),
        'layout_preservation':'Original OOXML slide and master/layout styles retained; foreign case images/tables converted into outlined slot shapes; sample text redacted',
        'src_example_identity':'장위10구역; NEVER transfer example values to GB7',
        'project_namespace':'ARCHI_GROW/GB7','project_evidence':'GB7_SEOUL_INTEGRATED_FORMING_20261016.json',
        'fire_architecture_binding':{'rules':len(fire['rules']),'sources':len(fire['source_versions']), 'approval':'HOLD','seoul_2024':True,'national_2025_and_2025_12':True},
        'not_a_real_rea_runtime_run':True,
        'source_limitation':'This is REA-inspired static PPTX object reverse engineering, not a REA MCP executable analysis',
        'slides':records,
        'gates':{'SOURCE_VERIFIED':'HOLD','RAW_CALC_MATCH':'HOLD','GEOMETRY_AGREES':'HOLD',
                 'OFFICIAL_LAW_APPLICABLE':'HOLD','A3_OUTPUT':'NOT_TESTED','VISUAL_FIDELITY':'NOT_TESTED',
                 'HUMAN_APPROVAL':'NOT_REQUESTED','PUSH_MERGE_DEPLOY':'NOT_EXECUTED'}
    }
    OUT_CONTRACT.write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT_PPTX) as z:
        cs=z.testzip()
        if cs:raise ValueError('PPTX_ZIP_INVALID:'+str(cs))
        leaked=[]
        for n in slides:
            s=z.read(n)
            if any(x.encode('utf-8') in s for x in SRC_IDENTIFIERS):leaked.append(n)
        if leaked:raise ValueError('SAMPLE_IDENTITY_LEAK:'+repr(leaked))
    readback=json.loads(OUT_CONTRACT.read_text(encoding='utf-8'))
    assert readback['candidate_sha256']==sha(OUT_PPTX.read_bytes())
    assert len(readback['slides'])==59
    print(json.dumps({'result':'PPTX_STRUCTURE_BUILD_PASS','slides':59,
                       'source_images':sum(x['source_picture_shapes'] for x in records),
                       'scrubbed_text':sum(x['masked_text_shapes'] for x in records),
                       'object_slots':sum(x['neutralized_picture_or_table_slots'] for x in records),
                       'output':str(OUT_PPTX),'contract':str(OUT_CONTRACT),
                       'sha256':readback['candidate_sha256']},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--build',action='store_true')
    args=ap.parse_args()
    if not args.build:ap.error('Use --build to create a stage-only local draft')
    build()
