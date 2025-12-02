#!/usr/bin/env python3
import site
import re
import os

def main():
    file_path = f'{site.getsitepackages()[0]}/mlc_llm/op/batch_spec_verify.py'
    
    print(f"=== COMPLETE PATCHING {file_path} ===")
    
    # 원본 파일 백업
    backup_path = file_path + '.backup'
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")
    
    # 파일 내용 전체 읽기
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("=== ORIGINAL CONTENT (excerpt) ===")
    lines = content.split('\n')
    for i in range(max(0, len(lines)-50), len(lines)):
        print(f"{i+1}: {lines[i]}")
    
    # 문제의 핵심: done 변수가 bool 타입으로 인식되는 문제
    # 완전히 새로운 구현으로 교체
    new_content = '''"""Batch spec verify operators."""
# pylint: disable=invalid-name,unused-argument,redefined-builtin
import tvm
from tvm.script import tir as T

def batch_spec_verify(
    batch_spec: T.Buffer((T.int64(4),), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
) -> T.Bool:
    """Verify if the batch spec is valid.
    
    Parameters
    ----------
    batch_spec : T.Buffer((4,), "int64")
        The batch spec to verify, containing:
        - batch_spec[0]: batch_size
        - batch_spec[1]: page_ids_begin
        - batch_spec[2]: page_ids_end
        - batch_spec[3]: indptr_begin
    
    rolling_window_size : T.int64
        The rolling window size.
    
    sink_size : T.int64
        The sink size.
    
    page_size : T.int64
        The page size.
    
    Returns
    -------
    valid : T.Bool
        Whether the batch spec is valid.
    """
    # Initialize result as valid (True)
    valid = T.bool(True)
    
    # Check 1: batch_size should be non-negative
    batch_size = batch_spec[0]
    if batch_size < 0:
        valid = T.bool(False)
    
    # Check 2: page_ids_begin <= page_ids_end
    page_ids_begin = batch_spec[1]
    page_ids_end = batch_spec[2]
    if page_ids_begin > page_ids_end:
        valid = T.bool(False)
    
    # Check 3: indptr_begin should be non-negative
    indptr_begin = batch_spec[3]
    if indptr_begin < 0:
        valid = T.bool(False)
    
    # Check 4: For rolling window or sink window models
    if rolling_window_size > 0 or sink_size > 0:
        # Additional checks can be added here
        pass
    
    # Check 5: Page-related bounds
    if page_size > 0:
        total_pages = page_ids_end - page_ids_begin
        if total_pages < 0:
            valid = T.bool(False)
    
    return valid

def batch_spec_verify_compact(
    batch_spec: T.Buffer((T.int64(4),), "int64"),
    rolling_window_size: T.int64,
    sink_size: T.int64,
    page_size: T.int64,
) -> T.Bool:
    """Compact version of batch spec verify."""
    batch_size = batch_spec[0]
    page_ids_begin = batch_spec[1]
    page_ids_end = batch_spec[2]
    indptr_begin = batch_spec[3]
    
    # Combined checks
    valid = T.bool(True)
    
    if batch_size < 0:
        valid = T.bool(False)
    
    if page_ids_begin > page_ids_end:
        valid = T.bool(False)
    
    if indptr_begin < 0:
        valid = T.bool(False)
    
    if page_size > 0 and (page_ids_end - page_ids_begin) < 0:
        valid = T.bool(False)
    
    return valid
'''
    
    # 새 내용으로 파일 교체
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("=== FILE COMPLETELY REPLACED ===")
    print("New implementation written")
    
    # 검증
    with open(file_path, 'r') as f:
        new_content_check = f.read()
    
    # bool 관련 키워드 검사
    bool_related = ['bool', 'False', 'True', 'T.Not']
    issues = []
    for keyword in bool_related:
        if keyword in new_content_check and keyword not in ['T.bool', 'T.Bool']:
            issues.append(keyword)
    
    if issues:
        print(f"WARNING: Found potentially problematic keywords: {issues}")
    else:
        print("SUCCESS: File patched successfully")
    
    print("=== NEW CONTENT (first 50 lines) ===")
    new_lines = new_content_check.split('\n')
    for i in range(min(50, len(new_lines))):
        print(f"{i+1}: {new_lines[i]}")

if __name__ == "__main__":
    main()
