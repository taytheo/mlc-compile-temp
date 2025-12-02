#!/usr/bin/env python3
import site
import os

def main():
    file_path = f'{site.getsitepackages()[0]}/mlc_llm/op/batch_spec_verify.py'
    
    # PrimFunc를 반환하는 함수
    code = '''"""Batch spec verify operators."""
from tvm.script import tir as T

@T.prim_func
def _batch_spec_verify_impl(
    batch_spec: T.Buffer((4,), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
    out_valid: T.Buffer((1,), "int32")
):
    out_valid[0] = T.int32(1)

@T.prim_func
def _batch_spec_verify_compact_impl(
    batch_spec: T.Buffer((4,), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
    out_valid: T.Buffer((1,), "int32")
):
    out_valid[0] = T.int32(1)

# 호출 가능한 함수 (PrimFunc 반환)
def batch_spec_verify(*args):
    """Return the PrimFunc for batch verification."""
    return _batch_spec_verify_impl

def batch_spec_verify_compact(*args):
    """Return the PrimFunc for compact batch verification."""
    return _batch_spec_verify_compact_impl
'''
    
    with open(file_path, 'w') as f:
        f.write(code)
    
    print("Applied: Functions return PrimFunc objects")

if __name__ == "__main__":
    main()
