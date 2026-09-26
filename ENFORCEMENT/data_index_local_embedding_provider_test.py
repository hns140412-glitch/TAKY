#!/usr/bin/env python3
from data_index_local_embedding_provider import (
    EXPECTED_DIMENSION, MODEL_ID, QUERY_SCHEMA, VECTOR_SCHEMA, _record_text, _source_id
)

row = {
    "source_id": "SRC-1",
    "title": "국어 기초 어휘",
    "source_family": "NIKL_FOUNDATIONAL_VOCAB_40K",
    "index_l1": {
        "identity": {"source_id": "SRC-1", "canonical_title": "국어 기초 어휘"},
        "classification": {
            "source_family": "NIKL_FOUNDATIONAL_VOCAB_40K",
            "source_type": "VOCABULARY_TABLE",
            "domain_facets": ["EDUCATION", "KOREAN_LANGUAGE"],
        },
        "discovery": {
            "short_summary": "기초 어휘 등급 자료",
            "controlled_terms": ["어휘", "등급"],
            "keywords": ["국어", "기초"],
        },
    },
}
assert MODEL_ID == "dragonkue/multilingual-e5-small-ko"
assert EXPECTED_DIMENSION == 384
assert VECTOR_SCHEMA == "TAKY_NEURAL_VECTOR_INDEX_V1"
assert QUERY_SCHEMA == "TAKY_NEURAL_QUERY_VECTOR_V1"
assert _source_id(row) == "SRC-1"
text = _record_text(row)
assert text.startswith("passage: ")
assert "국어 기초 어휘" in text
assert "NIKL_FOUNDATIONAL_VOCAB_40K" in text
assert "기초 어휘 등급 자료" in text
print("LOCAL_EMBEDDING_PROVIDER_CONTRACT_SUCCESS")
