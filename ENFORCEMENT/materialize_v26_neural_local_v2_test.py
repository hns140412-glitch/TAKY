#!/usr/bin/env python3
import py_compile
from pathlib import Path

def test_local_v26_runner_v2_compiles():
    target = Path(__file__).with_name("materialize_v26_neural_local_v2.py")
    py_compile.compile(str(target), doraise=True)
