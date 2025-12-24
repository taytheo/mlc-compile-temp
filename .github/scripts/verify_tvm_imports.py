#!/usr/bin/env python3
"""Verify that `tvm` and `tvm_ffi` can be imported and print their locations.
This script is intended to be run inside the CI workspace and write to stdout.
"""
import importlib
import sys

modules = ('tvm', 'tvm_ffi')
for m in modules:
    try:
        mod = importlib.import_module(m)
        location = getattr(mod, '__file__', 'package')
        print(f"{m} present at: {location}")
    except Exception as e:
        print(f"{m} import failed: {e}")

# Exit successfully even if imports fail; workflow handles logging
sys.exit(0)
