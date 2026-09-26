import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SCRIPT=ROOT/'data_index_vector_materialization_validate.py'
with tempfile.TemporaryDirectory() as td:
    td=Path(td); s=td/'s.json'; v=td/'v.json'
    s.write_text(json.dumps({'entries':[{'source_id':'A'},{'source_id':'B'}]}),encoding='utf-8')
    v.write_text(json.dumps({'provider':{'model_id':'m','dimension':2,'neural_embedding_verified':True},'entries':[{'source_id':'A','vector':[1,0]},{'source_id':'B','vector':[0,1]}]}),encoding='utf-8')
    r=subprocess.run([sys.executable,str(SCRIPT),'--index',str(s),'--vector-index',str(v)],capture_output=True,text=True)
    assert r.returncode==0, r.stderr
    assert json.loads(r.stdout)['pass'] is True
    v.write_text(json.dumps({'provider':{'model_id':'m','dimension':2,'neural_embedding_verified':True},'entries':[{'source_id':'A','vector':[1,0]}]}),encoding='utf-8')
    r=subprocess.run([sys.executable,str(SCRIPT),'--index',str(s),'--vector-index',str(v)],capture_output=True,text=True)
    assert r.returncode==2
print('data_index_vector_materialization_validate: PASS')
