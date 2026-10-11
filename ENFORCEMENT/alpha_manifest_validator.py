#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate(manifest_path: Path) -> list[str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    errors = []
    files = data.get("files")
    if not isinstance(files, list) or not files:
        return ["MANIFEST_FILES_MISSING"]
    if data.get("file_count") != len(files):
        errors.append(f"FILE_COUNT_MISMATCH:{data.get('file_count')}!={len(files)}")
    seen = set()
    for item in files:
        rel = str(item.get("path") or "")
        if not rel:
            errors.append("EMPTY_PATH")
            continue
        if rel in seen:
            errors.append(f"DUPLICATE_PATH:{rel}")
            continue
        seen.add(rel)
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"MISSING_FILE:{rel}")
            continue
        expected_size = item.get("bytes")
        actual_size = path.stat().st_size
        if expected_size != actual_size:
            errors.append(f"SIZE_MISMATCH:{rel}:{expected_size}!={actual_size}")
        expected_hash = str(item.get("sha256") or "").lower()
        actual_hash = sha256(path)
        if expected_hash != actual_hash:
            errors.append(f"HASH_MISMATCH:{rel}")
    return errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    args = ap.parse_args()
    manifest = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    errors = validate(manifest)
    if errors:
        print("FAIL: Alpha manifest validation")
        for e in errors:
            print(e)
        return 1
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    print(f"PASS: Alpha manifest {data.get('file_count')} files hash/size verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
