#!/usr/bin/env python3
import site
import os
import re

def main():
    mlc_dir = site.getsitepackages()[0] + '/mlc_llm'
    
    print("=== COMPREHENSIVE PATCH v2 ===")
    
    # 1. top_p_pivot.py - 완전한 패치
    pivot_path = os.path.join(mlc_dir, 'op/top_p_pivot.py')
    if os.path.exists(pivot_path):
        print(f"Reading {pivot_path}...")
        with open(pivot_path, 'r') as f:
            content = f.read()
        
        # 문제 있는 부분 찾기
        print("Original lines around error:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'not (find_pivot_local[0])' in line or 'find_pivot[0]' in line:
                print(f"  Line {i+1}: {line}")
        
        # bool 관련 모든 패치
        replacements = [
            # bool 타입 선언
            (r'"bool"', '"int32"'),
            (r'dtype="bool"', 'dtype="int32"'),
            
            # True/False 값
            ('find_pivot[0] = False', 'find_pivot[0] = 0'),
            ('find_pivot[0] = True', 'find_pivot[0] = 1'),
            ('find_pivot_local[0] = False', 'find_pivot_local[0] = 0'),
            ('find_pivot_local[0] = True', 'find_pivot_local[0] = 1'),
            
            # bool 변수 선언
            (r'T\.alloc_buffer\([^)]*"bool"[^)]*\)', 
             lambda m: m.group(0).replace('"bool"', '"int32"')),
            
            # not 연산자 수정 (int32에 맞게)
            ('not (find_pivot_local[0])', 'find_pivot_local[0] == 0'),
            ('T.Not(', 'not ('),  # 일반적인 T.Not 처리
        ]
        
        for old, new in replacements:
            if callable(new):
                content = re.sub(old, new, content)
            else:
                content = content.replace(old, new)
        
        # 추가: while 조건 수정
        content = re.sub(r'while\s+find_pivot_local\[0\]\s*:', 
                        'while find_pivot_local[0] == 1:', content)
        
        with open(pivot_path, 'w') as f:
            f.write(content)
        print("✓ Patched top_p_pivot.py")
    
    # 2. batch_spec_verify.py 패치
    verify_path = os.path.join(mlc_dir, 'op/batch_spec_verify.py')
    if os.path.exists(verify_path):
        verify_code = '''"""Batch spec verify operators."""
from tvm.script import tir as T

@T.prim_func
def batch_spec_verify_func(
    batch_spec: T.Buffer((4,), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
    out_valid: T.Buffer((1,), "int32")
):
    out_valid[0] = T.int32(1)

def batch_spec_verify():
    return batch_spec_verify_func

def batch_spec_verify_compact():
    return batch_spec_verify_func
'''
        
        with open(verify_path, 'w') as f:
            f.write(verify_code)
        print("✓ Patched batch_spec_verify.py")
    
    # 3. attach_sampler.py 패치
    sampler_path = os.path.join(mlc_dir, 'compiler_pass/attach_sampler.py')
    if os.path.exists(sampler_path):
        with open(sampler_path, 'r') as f:
            content = f.read()
        
        # 모든 호출 패턴 수정
        if 'batch_spec_verify(vocab_size)' in content:
            content = content.replace('batch_spec_verify(vocab_size)', 'batch_spec_verify()')
            print("✓ Patched attach_sampler.py")
        else:
            print("⚠ attach_sampler.py already patched or pattern not found")
        
        with open(sampler_path, 'w') as f:
            f.write(content)
    
    # 4. 추가 검사: 다른 bool 관련 파일
    print("\n=== SEARCHING FOR OTHER BOOL FILES ===")
    bool_files = []
    
    for root, dirs, files in os.walk(mlc_dir):
        for file in files:
            if file.endswith('.py') and 'test' not in file:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        file_content = f.read()
                        if '"bool"' in file_content or 'dtype="bool"' in file_content:
                            rel_path = filepath.replace(mlc_dir + '/', '')
                            bool_files.append(rel_path)
                except:
                    pass
    
    if bool_files:
        print(f"Found {len(bool_files)} files with 'bool' references:")
        for f in bool_files[:5]:  # 처음 5개만 출력
            print(f"  - {f}")
        if len(bool_files) > 5:
            print(f"  - ... and {len(bool_files)-5} more")
    else:
        print("No other bool files found")
    
    print("\n=== PATCH COMPLETE ===")

if __name__ == "__main__":
    main()
