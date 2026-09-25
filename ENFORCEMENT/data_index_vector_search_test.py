#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from data_index_search import search
from data_index_vector_search import (
    VectorContractError,
    load_query_vector,
    load_vector_index,
    metadata,
    vector_scores,
)

class VectorSearchTest(unittest.TestCase):
    def test_verified_vector_channel_changes_semantic_mode(self):
        records=[
            {"source_id":"A","canonical_title":"alpha","keywords":["unrelated"]},
            {"source_id":"B","canonical_title":"beta","keywords":["other"]},
        ]
        scores={"A":0.1,"B":0.95}
        result=search(
            records,
            "no lexical match",
            semantic_vector_scores=scores,
            semantic_metadata={
                "semantic_mode":"NEURAL_EMBEDDING_VECTOR_VERIFIED",
                "model_id":"test-model",
                "dimension":3,
                "neural_embedding_verified":True,
            },
        )
        self.assertEqual(result["semantic_mode"],"NEURAL_EMBEDDING_VECTOR_VERIFIED")
        self.assertIn("VERIFIED_NEURAL_VECTOR",result["pipeline"])
        self.assertTrue(result["results"][0]["channels"]["verified_neural_vector"])
        self.assertEqual(result["results"][0]["source_id"],"B")

    def test_no_vector_keeps_token_fallback(self):
        records=[{"source_id":"A","canonical_title":"hello","keywords":["hello"]}]
        result=search(records,"hello")
        self.assertEqual(result["semantic_mode"],"TOKEN_COSINE_FALLBACK__NOT_EMBEDDING_SEMANTIC")
        self.assertNotIn("VERIFIED_NEURAL_VECTOR",result["pipeline"])

    def test_contract_requires_verified_same_model(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            vi=root/"vectors.json"
            qv=root/"query.json"
            vi.write_text(json.dumps({
                "schema":"TAKY_NEURAL_VECTOR_INDEX_V1",
                "provider":{
                    "provider_type":"EXPLICIT_PRECOMPUTED_NEURAL_EMBEDDING",
                    "model_id":"model-a",
                    "dimension":3,
                    "neural_embedding_verified":True
                },
                "entries":[
                    {"source_id":"A","vector":[1,0,0]},
                    {"source_id":"B","vector":[0,1,0]}
                ]
            }),encoding="utf-8")
            qv.write_text(json.dumps({
                "schema":"TAKY_NEURAL_QUERY_VECTOR_V1",
                "model_id":"model-a",
                "dimension":3,
                "neural_embedding_verified":True,
                "vector":[0.9,0.1,0]
            }),encoding="utf-8")
            index=load_vector_index(vi)
            query=load_query_vector(qv)
            scores=vector_scores(index,query)
            self.assertGreater(scores["A"],scores["B"])
            self.assertEqual(metadata(index)["semantic_mode"],"NEURAL_EMBEDDING_VECTOR_VERIFIED")

            qv.write_text(json.dumps({
                "schema":"TAKY_NEURAL_QUERY_VECTOR_V1",
                "model_id":"model-b",
                "dimension":3,
                "neural_embedding_verified":True,
                "vector":[1,0,0]
            }),encoding="utf-8")
            with self.assertRaises(VectorContractError):
                vector_scores(index,load_query_vector(qv))

    def test_unverified_index_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"vectors.json"
            p.write_text(json.dumps({
                "schema":"TAKY_NEURAL_VECTOR_INDEX_V1",
                "provider":{
                    "model_id":"m",
                    "dimension":3,
                    "neural_embedding_verified":False
                },
                "entries":[{"source_id":"A","vector":[1,0,0]}]
            }),encoding="utf-8")
            with self.assertRaises(VectorContractError):
                load_vector_index(p)

if __name__=="__main__":
    unittest.main()
