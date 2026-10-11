#!/usr/bin/env python3
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Iterable

from reference_acquisition_adapter import acquire

DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 12

def acquire_batch(
    items: Iterable[dict[str, Any]],
    *,
    destination_dir: Path,
    workers: int = DEFAULT_WORKERS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = 25 * 1024 * 1024,
    acquire_func: Callable[..., dict[str, Any]] = acquire,
) -> dict[str, Any]:
    rows = list(items)
    if workers < 1 or workers > 8:
        return {"pass": False, "detected": ["REFERENCE_BATCH_WORKER_LIMIT_INVALID"]}
    if timeout_seconds < 1:
        return {"pass": False, "detected": ["REFERENCE_BATCH_TIMEOUT_INVALID"]}

    results: list[dict[str, Any] | None] = [None] * len(rows)

    def one(index: int, item: dict[str, Any]) -> dict[str, Any]:
        url = str(item.get("url") or "").strip()
        source_id = str(item.get("source_id") or index)
        target = destination_dir / source_id.replace(":", "_")
        try:
            result = acquire_func(
                url,
                destination_dir=target,
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
            )
            return {"source_id": source_id, "url": url, "terminal": True, "result": result}
        except Exception as exc:
            # One item must never prevent terminal results for the rest of the batch.
            return {
                "source_id": source_id,
                "url": url,
                "terminal": True,
                "result": {
                    "pass": False,
                    "detected": ["REFERENCE_BATCH_ITEM_EXCEPTION"],
                    "error_type": type(exc).__name__,
                },
            }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, i, row): i for i, row in enumerate(rows)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    completed = [x for x in results if isinstance(x, dict) and x.get("terminal") is True]
    return {
        "pass": len(completed) == len(rows),
        "requested": len(rows),
        "terminal_count": len(completed),
        "workers": workers,
        "timeout_seconds": timeout_seconds,
        "results": completed,
        "canonical_promotion": False,
    }
