#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path
from data_index_local_embedding_provider import load_payload

def test_bom_prefixed_v26_payload_loads():
    payload={"schema":"TAKY_DATA_UTILIZATION_INDEX_V26","source_entries":[]}
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"v26.json"
        p.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8-sig")
        loaded=load_payload(p)
        assert loaded["schema"]=="TAKY_DATA_UTILIZATION_INDEX_V26"
        assert loaded["source_entries"]==[]

if __name__=="__main__":
    test_bom_prefixed_v26_payload_loads()
    print("V26_BOM_PAYLOAD_REGRESSION_SUCCESS")
