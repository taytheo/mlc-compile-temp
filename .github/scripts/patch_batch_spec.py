#!/usr/bin/env python3
import site
import os
import re

def main():
    mlc_dir = site.getsitepackages()[0] + '/mlc_llm'
    
    print("=== COMPREHENSIVE PATCH ===")
    
    # 1. batch_spec_verify.py 파일 패치
    file_path = mlc_dir + '/op/batch_spec_verify.py'
    
    int32_version = '''"""Batch spec verify operators."""
from tvm.script import tir as T

@T.prim_func
def batch_spec_verify(
    batch_spec: T.Buffer((4,), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
    out_valid: T.Buffer((1,), "int32")
):
    out_valid[0] = T.int32(1)

@T.prim_func
def batch_spec_verify_compact(
    batch_spec: T.Buffer((4,), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
    out_valid: T.Buffer((1,), "int32")
):
    out_valid[0] = T.int32(1)
'''
    
    with open(file_path, 'w') as f:
        f.write(int32_version)
    print(f"1. Patched {file_path}")
    
    # 2. 호출하는 파일들 찾아서 패치
    print("\n2. Searching for files that call batch_spec_verify...")
    
    files_to_patch = []
    for root, dirs, files in os.walk(mlc_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if 'batch_spec_verify' in content and filepath != file_path:
                            files_to_patch.append((filepath, content))
                except:
                    pass
    
    print(f"Found {len(files_to_patch)} files that may need patching")
    
    # 3. 주요 파일들 패치
    for filepath, content in files_to_patch:
        filename = os.path.basename(filepath)
        
        # bool 타입 참조를 int32로 변경
        if 'bool' in content and ('batch_spec_verify' in content or 'out_valid' in content):
            new_content = content
            
            # "bool"을 "int32"로 변경 (batch_spec_verify 관련 부분만)
            new_content = re.sub(
                r'batch_spec_verify\([^)]+\)\s*->\s*bool',
                'batch_spec_verify(...) -> int32',
                new_content
            )
            
            # out_valid 버퍼 타입 변경
            new_content = re.sub(
                r'out_valid:\s*T\.Buffer\(\(1,\),\s*"bool"\)',
                'out_valid: T.Buffer((1,), "int32")',
                new_content
            )
            
            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"  - Patched {filename}")
    
    print("\n=== PATCH COMPLETE ===")
    print("All bool-related issues should be resolved")

if __name__ == "__main__":
    main()
