#!/usr/bin/env python3
from pathlib import Path

def test_provider_uses_bom_safe_payload_decode():
    source=Path(__file__).with_name("data_index_local_embedding_provider.py").read_text(encoding="utf-8")
    assert 'payload_path.read_text(encoding="utf-8-sig")' in source

if __name__=="__main__":
    test_provider_uses_bom_safe_payload_decode()
    print("V26_BOM_PAYLOAD_REGRESSION_SUCCESS")
