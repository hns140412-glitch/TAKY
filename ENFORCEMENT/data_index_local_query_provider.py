#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
from typing import Any

MODEL_SCHEMA='TAKY_LOCAL_NEURAL_QUERY_MODEL_V1'
QUERY_SCHEMA='TAKY_NEURAL_QUERY_VECTOR_V1'
TOKEN_RE=re.compile(r'[0-9A-Za-z_\-\.]+|[가-힣]+')

class QueryProviderError(ValueError):
    pass

def _base_tokens(text:str)->list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or '')]

def _tokenize(text:str, ngrams:list[int])->list[str]:
    out=[]
    for w in _base_tokens(text):
        out.append('w:'+w)
        for n in ngrams:
            if len(w)>=n:
                for i in range(min(len(w)-n+1,8)):
                    out.append(f'c{n}:'+w[i:i+n])
    return out

def load_model(path:Path, *, allow_experimental:bool=False)->dict[str,Any]:
    p=json.loads(path.read_text(encoding='utf-8'))
    if p.get('schema')!=MODEL_SCHEMA:
        raise QueryProviderError('QUERY_MODEL_SCHEMA_INVALID')
    provider=p.get('provider') or {}
    if provider.get('neural_embedding_verified') is not True:
        raise QueryProviderError('QUERY_MODEL_NOT_NEURAL_VERIFIED')
    quality=p.get('quality_status') or provider.get('quality_status') or 'UNSPECIFIED'
    if quality != 'APPROVED_FOR_NEURAL_RETRIEVAL' and not allow_experimental:
        raise QueryProviderError('QUERY_MODEL_NOT_APPROVED_FOR_NEURAL_RETRIEVAL')
    model_id=str(provider.get('model_id') or '').strip(); dim=provider.get('dimension')
    if not model_id or not isinstance(dim,int) or dim<2:
        raise QueryProviderError('QUERY_MODEL_METADATA_INVALID')
    vocab=p.get('vocab'); vectors=p.get('vectors')
    if not isinstance(vocab,list) or not isinstance(vectors,list) or len(vocab)!=len(vectors):
        raise QueryProviderError('QUERY_MODEL_VOCAB_VECTOR_MISMATCH')
    for row in vectors:
        if not isinstance(row,list) or len(row)!=dim:
            raise QueryProviderError('QUERY_MODEL_VECTOR_DIMENSION_MISMATCH')
    p['_vocab_index']={t:i for i,t in enumerate(vocab)}
    return p

def embed_query(model:dict[str,Any], query:str)->list[float]:
    idx=model['_vocab_index']; dim=model['provider']['dimension']
    ngrams=((model.get('tokenizer') or {}).get('word_plus_char_ngrams') or [2,3])
    ids=[idx[t] for t in _tokenize(query,ngrams) if t in idx and idx[t] != 0]
    if not ids:
        raise QueryProviderError('QUERY_HAS_NO_MODEL_TOKENS')
    out=[0.0]*dim
    for i in ids:
        row=model['vectors'][i]
        for j,v in enumerate(row): out[j]+=float(v)
    inv=1.0/len(ids); out=[x*inv for x in out]
    norm=math.sqrt(sum(x*x for x in out))
    if not norm: raise QueryProviderError('QUERY_VECTOR_ZERO')
    return [x/norm for x in out]

def make_query_vector(model:dict[str,Any], query:str)->dict[str,Any]:
    provider=model['provider']
    return {
        'schema':QUERY_SCHEMA,
        'model_id':provider['model_id'],
        'dimension':provider['dimension'],
        'neural_embedding_verified':True,
        'quality_status':model.get('quality_status') or provider.get('quality_status') or 'UNSPECIFIED',
        'vector':embed_query(model,query),
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--model',type=Path,required=True)
    ap.add_argument('--query',required=True)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--allow-experimental',action='store_true')
    a=ap.parse_args()
    payload=make_query_vector(load_model(a.model,allow_experimental=a.allow_experimental),a.query)
    text=json.dumps(payload,ensure_ascii=False,indent=2)
    if a.out: a.out.write_text(text+'\n',encoding='utf-8')
    else: print(text)
    return 0

if __name__=='__main__': raise SystemExit(main())
