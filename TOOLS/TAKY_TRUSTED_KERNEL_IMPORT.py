"""Load only the pinned local TAKY2 package without prepending repo to sys.path.

Avoid standard-library shadowing from arbitrary repository modules. This
bootstrap itself never mutates signed authority/runtime and never calls AI.
"""
from __future__ import annotations
from importlib.machinery import PathFinder
from importlib.util import module_from_spec
from pathlib import Path
import sys

ROOT = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")


def ensure_trusted_taky2(root: Path = ROOT):
    expected_dir = (root / "TAKY2").resolve(strict=True)
    expected_init = (expected_dir / "__init__.py").resolve(strict=True)
    already = sys.modules.get("TAKY2")
    if already is not None:
        current_file = getattr(already, "__file__", None)
        if current_file is None or Path(current_file).resolve() != expected_init:
            raise RuntimeError("UNTRUSTED_TAKY2_ALREADY_LOADED")
        return already
    spec = PathFinder.find_spec("TAKY2", [str(root.resolve(strict=True))])
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected_init:
        raise RuntimeError("PINNED_TAKY2_MODULE_NOT_FOUND")
    if spec.loader is None:
        raise RuntimeError("PINNED_TAKY2_LOADER_MISSING")
    package = module_from_spec(spec)
    sys.modules["TAKY2"] = package
    try:
        spec.loader.exec_module(package)
    except BaseException:
        sys.modules.pop("TAKY2", None)
        raise
    return package
