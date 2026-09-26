#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def extract_ids(payload):
    if isinstance(payload,dict):
        for key in ('source_entries','entries','sources','records'):
            v=payload.get(key)
            if isinstance(v,list) and v and isinstance(v[0],dict) and 'source_id' in v[0]:
                return [str(x['source_id']) for x in v if x.get('source_id')]
    if isinstance(payload,list): return [str(x['source_id']) for x in payload if isinstance(x,dict) and x.get('source_id')]
    raise ValueError('SOURCE_IDS_NOT_FOUND')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--index',type=Path,required=True); ap.add_argument('--vector-index',type=Path,required=True); a=ap.parse_args()
    src=json.loads(a.index.read_text(encoding='utf-8-sig')); vi=json.loads(a.vector_index.read_text(encoding='utf-8'))
    sids=extract_ids(src); entries=vi.get('entries') or []; vids=[str(x.get('source_id')) for x in entries]
    dup=len(vids)!=len(set(vids)); missing=sorted(set(sids)-set(vids)); extra=sorted(set(vids)-set(sids))
    p=vi.get('provider') or {}
    result={
      'source_count':len(sids),'source_unique':len(sids)==len(set(sids)),'vector_count':len(vids),'vector_unique':not dup,
      'missing_count':len(missing),'extra_count':len(extra),'model_id':p.get('model_id'),'dimension':p.get('dimension'),
      'neural_embedding_verified':p.get('neural_embedding_verified') is True,
      'pass':len(sids)==len(vids) and not dup and not missing and not extra and p.get('neural_embedding_verified') is True,
    }
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['pass'] else 2
if __name__=='__main__': raise SystemExit(main())
