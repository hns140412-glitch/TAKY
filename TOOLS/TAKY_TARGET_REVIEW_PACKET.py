#!/usr/bin/env python3
"""Attach exact signed target result to an existing bounded model review packet.

A single-purpose input packer, NOT a model runner, verifier or new task store.
The genuine TAKY2 provider bridge revalidates this entire attachment immediately
before running the reviewer. Refuse missing/stale/oversized target results.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

from TAKY_TRUSTED_KERNEL_IMPORT import ensure_trusted_taky2
from TAKY_MODEL_REVIEW_PACKET import MAX_PACKET_CHARS


def attach(packet: str, runtime: dict, target_id: str) -> tuple[str, dict]:
    from TAKY2.enforcement import stable_hash
    from TAKY2.bridges import target_review_block
    if (not isinstance(target_id, str)
            or re.fullmatch(r"pf:[A-Za-z0-9:_-]{8,150}", target_id) is None):
        raise ValueError("TARGET_REVIEW_RECEIPT_ID_INVALID")
    target = runtime.get("preflight_receipts", {}).get(target_id)
    call = runtime.get("execution_calls", {}).get(target_id)
    if not isinstance(target, dict) or not isinstance(call, dict):
        raise ValueError("TARGET_REVIEW_RECEIPT_NOT_FOUND")
    if target.get("allowed") is not True:
        raise ValueError("TARGET_REVIEW_TARGET_PREFLIGHT_UNAUTHORIZED")
    result = call.get("result")
    if (call.get("status") != "RETURNED" or not isinstance(result, dict)
            or result.get("returncode") != 0):
        raise ValueError("TARGET_REVIEW_RESULT_NOT_RETURNED")
    digest = stable_hash(result)
    if digest != call.get("result_digest"):
        raise ValueError("TARGET_REVIEW_RESULT_NOT_INTEGRITY_BOUND")
    if "TARGET_REVIEW_EVIDENCE " in packet:
        raise ValueError("TARGET_REVIEW_PACKET_ALREADY_HAS_RESULT")
    block = target_review_block(target_id, result, digest)
    combined = packet + block
    if len(combined) > MAX_PACKET_CHARS:
        raise ValueError("TARGET_REVIEW_PACKET_OVER_BUDGET")
    return combined, {"schema": "TAKY_TARGET_REVIEW_V1",
                      "target_receipt_id": target_id,
                      "target_result_digest": digest}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--packet-file", type=Path, required=True)
    p.add_argument("--target-receipt", required=True)
    ns = p.parse_args()
    ensure_trusted_taky2()
    from TAKY2.state_store import load_bundle
    from TAKY2.enforcement import stable_hash
    _, runtime, _ = load_bundle()
    current = ns.packet_file.read_text(encoding="utf-8")
    combined, binding = attach(current, runtime, ns.target_receipt)
    ns.packet_file.write_text(combined, encoding="utf-8", newline="")
    print(json.dumps({
        "target_review_binding": binding,
        "packet_digest": stable_hash(combined),
        "packet_chars": len(combined),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
