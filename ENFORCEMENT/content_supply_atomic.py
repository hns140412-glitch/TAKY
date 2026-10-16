"""Crash-safe, non-overwriting publication of local TAKY candidate/receipt bytes.

Build and fsync a same-directory temporary file, then atomically hard-link it
to the destination. Existing identical bytes are reusable, differing bytes are
never overwritten. Unsupported hard links fail closed rather than weakening.
"""
import hashlib
import os
import tempfile
from pathlib import Path

def publish_bytes(destination, data):
    if not isinstance(data, bytes):
        raise TypeError("BYTES_REQUIRED")
    target=Path(destination)
    if not target.parent.is_dir():
        raise FileNotFoundError("OUTPUT_PARENT_MISSING")
    def identical():
        if target.is_symlink() or not target.is_file():
            return False
        try:
            if target.stat().st_size!=len(data):
                return False
            return hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(data).digest()
        except OSError:
            return False
    if target.exists() or target.is_symlink():
        if identical():
            return "REUSED"
        raise FileExistsError("OUTPUT_CONFLICT")
    fd, tmp_name=tempfile.mkstemp(prefix=".taky-supply-",dir=target.parent)
    try:
        with os.fdopen(fd,"wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.link(tmp_name,target)
            return "PUBLISHED"
        except FileExistsError:
            if identical():
                return "REUSED"
            raise
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
