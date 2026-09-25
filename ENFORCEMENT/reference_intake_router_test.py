#!/usr/bin/env python3
from reference_intake_router import route

def check(name, record, expected_type, expected_consumer=None, expected_write=None):
    out = route(record)
    assert out["pass"], (name, out)
    assert out["route_type"] == expected_type, (name, out)
    if expected_consumer is not None:
        assert out.get("consumer") == expected_consumer, (name, out)
    if expected_write is not None:
        assert out.get("write_authorized") is expected_write, (name, out)

def main():
    check("plain slash review", {"intent_text": "/검토"}, "PLAIN_REVIEW", expected_write=False)
    check("source read only", {"intent_text": "이거 검토해", "source_url": "https://example.com/a"},
          "PLAIN_SOURCE_REVIEW", expected_write=False)
    check("learning reference intake",
          {"intent_text": "이 자료 학습에 참고하게 하고 싶은데 검토해", "source_url": "https://example.com/a"},
          "REFERENCE_INTAKE_REVIEW", expected_consumer="LEARNING_ENGINE", expected_write=True)
    check("generic domain reference intake",
          {"intent_text": "이 자료 참고해", "source_id": "source-1", "domain": "architecture"},
          "REFERENCE_INTAKE_REVIEW", expected_consumer="DOMAIN_ENGINE", expected_write=True)
    out = route({"intent_text": "검토해"})
    assert not out["pass"]
    assert "REFERENCE_INTAKE_NOT_ESTABLISHED" in out["detected"]
    out = route({"intent_text": "이 자료 참고하게 하고 싶어. 검토해",
                 "source_locator": "drive:abc", "domain": "learning"})
    assert out["full_corpus_reindex"] is False
    assert out["canonical_promotion_authorized"] is False
    assert "INDEXED != APPROVED_POLICY" in out["guards"]
    print("6/6 PASS")

if __name__ == "__main__":
    main()
