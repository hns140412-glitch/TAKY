#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"PROJECTIONS"))

from data_delta_discovery import classify_candidate

known={"A","B"}
hashes={"HASH1"}

x=classify_candidate({"id":"C","title":"new.pdf"},known_source_ids=known,in_inbox=True)
assert x["classification"]=="NEW_SOURCE"
assert x["priority"]=="HIGH"
assert x["accepted_for_incremental_index"] is True

x=classify_candidate({"id":"A","title":"existing.pdf","modified_since_baseline":True},known_source_ids=known)
assert x["classification"]=="UPDATED_SOURCE"

x=classify_candidate({"id":"X","title":"HANDOFF/foo"},known_source_ids=known)
assert x["classification"]=="DERIVED_NOT_SOURCE"
assert x["accepted_for_incremental_index"] is False

x=classify_candidate({"id":"X","title":"same.pdf","content_hash":"HASH1"},known_source_ids=known,known_content_hashes=hashes)
assert x["classification"]=="EXACT_DUPLICATE"

x=classify_candidate({"id":"X","title":"guide_rev2.pdf","version_hint":True},known_source_ids=known)
assert x["classification"]=="VERSION_CANDIDATE"

print("data_delta_discovery: PASS")
