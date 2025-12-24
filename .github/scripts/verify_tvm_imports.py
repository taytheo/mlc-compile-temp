#!/usr/bin/env python3
"""Verify that `tvm` and `tvm_ffi` can be imported and print their locations.
This script is intended to be run inside the CI workspace and write to stdout.
"""
import importlib
import sys

modules = ('tvm', 'tvm_ffi')
any_failed = False
for m in modules:
    try:
        mod = importlib.import_module(m)
        location = getattr(mod, '__file__', 'package')
        print(f"{m} present at: {location}")
    except Exception as e:
        print(f"{m} import failed: {e}")
        any_failed = True

# Exit with non-zero code if any import fails to make the workflow fail fast
sys.exit(1) if any_failed else sys.exit(0)
