from pathlib import Path
import json
ROOT=Path(r'D:\Git PWA\TAKY_ALPHA_20261003')
carry_path=ROOT/'ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json'
map_path=ROOT/'MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json'
carry=json.loads(carry_path.read_text(encoding='utf-8'))
m=json.loads(map_path.read_text(encoding='utf-8'))
constraints=[]
shared=m.get('layers',{}).get('SHARED_TECHNICAL_CAPABILITY',{})
if 'HOLD' in str(shared.get('state','')):
    constraints.append({'source':'MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json#layers.SHARED_TECHNICAL_CAPABILITY','state':shared.get('state'),'finding':'shared technical capability auth extraction remains held; mechanism sharing does not transfer domain identity/authority'})
for i,row in enumerate(m.get('capability_classification',[])):
    state=str(row.get('state',''))
    if 'HOLD' in state:
        constraints.append({'source':f'MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json#capability_classification[{i}]','item':row.get('item'),'state':state,'boundary':row.get('boundary') or row.get('note'),'owner':row.get('owner')})
for i,row in enumerate(m.get('review_findings',[])):
    if row.get('state')=='HOLD':
        constraints.append({'source':f'MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json#review_findings[{i}]','gap_id':row.get('gap_id'),'priority':row.get('priority'),'state':'HOLD','finding':row.get('finding'),'direction':row.get('direction')})
carry['repository_constraints_source']='MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json'
carry['repository_hold_constraints']=constraints
carry['coverage_claim']='FROZEN_MANIFEST_OPEN_FULLY_PRESERVED__REPOSITORY_HOLD_IMPORTED_SEPARATELY'
carry_path.write_text(json.dumps(carry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'repository_hold_constraints':len(constraints)},ensure_ascii=False))