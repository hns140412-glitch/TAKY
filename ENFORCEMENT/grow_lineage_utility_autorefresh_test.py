#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from grow_lineage_packet import make_event, materialize

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    ledger=root/"grow-lineage.jsonl"
    raw=make_event(
        grow_domain="ARCHI_GROW",stage="RAW",producer="test",
        source_ref="INDEX:SRC-A",authority="TEST"
    )
    rr=materialize(raw,ledger)
    assert rr["ok"] is True
    assert rr["utility_projection"]["attempted"] is True
    sidecar=root/"data-index-outcome-utility.json"
    assert sidecar.exists()

    out=make_event(
        grow_domain="ARCHI_GROW",stage="OUTCOME",producer="test",
        source_ref="INDEX:SRC-A",parent_refs=[raw["event_id"]],authority="TEST",
        payload={"verified_target":True,"outcome":1}
    )
    r2=materialize(out,ledger)
    assert r2["ok"] is True
    payload=json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["schema"]=="TAKY_DATA_INDEX_OUTCOME_UTILITY_V1"
    assert payload["authoritative"] is False
    assert payload["by_source_id"]["SRC-A"]["verified_success"]==1

    # idempotent replay still leaves sidecar synchronized.
    r3=materialize(out,ledger)
    assert r3["ok"] is True and r3["idempotent"] is True
    assert r3["utility_projection"]["ok"] is True

print("grow_lineage_utility_autorefresh: PASS")
