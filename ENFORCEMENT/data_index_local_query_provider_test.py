import json, tempfile
from pathlib import Path
from data_index_local_query_provider import QueryProviderError, load_model, make_query_vector

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'m.json'
    model={
      'schema':'TAKY_LOCAL_NEURAL_QUERY_MODEL_V1',
      'quality_status':'APPROVED_FOR_NEURAL_RETRIEVAL',
      'provider':{'model_id':'m','dimension':3,'neural_embedding_verified':True},
      'tokenizer':{'word_plus_char_ngrams':[2,3]},
      'vocab':['<unk>','w:hello','c2:he','c2:el','c2:ll','c2:lo'],
      'vectors':[[0,0,0],[1,0,0],[1,0,0],[1,0,0],[1,0,0],[1,0,0]],
    }
    p.write_text(json.dumps(model),encoding='utf-8')
    q=make_query_vector(load_model(p), 'hello')
    assert q['model_id']=='m' and q['dimension']==3 and q['neural_embedding_verified'] is True
    model['quality_status']='REJECTED_NOT_PROMOTED__SEMANTIC_PROBE_QUALITY_INSUFFICIENT'
    p.write_text(json.dumps(model),encoding='utf-8')
    try:
        load_model(p)
        raise AssertionError('rejected model should fail closed')
    except QueryProviderError as e:
        assert str(e)=='QUERY_MODEL_NOT_APPROVED_FOR_NEURAL_RETRIEVAL'
    load_model(p,allow_experimental=True)
print('data_index_local_query_provider: PASS')
