#!/usr/bin/env python3
import py_compile
from pathlib import Path

def test_v26_neural_regression_gate_compiles():
    py_compile.compile(str(Path(__file__).with_name("v26_neural_retrieval_regression.py")), doraise=True)
