#!/usr/bin/env python3
"""
MLC-LLM Bool 타입 버그 패치 스크립트

GitHub Issue #3389: "IntImm supports only int or uint type, but bool was supplied"
- TVM의 Metal 백엔드에서 bool 타입을 처리하지 못하는 버그 수정
- 영향받는 파일: batch_spec_verify.py, top_p_pivot.py
"""

import site
import re
import os
import sys

def patch_batch_spec_verify(site_pkg: str) -> bool:
    """batch_spec_verify.py의 bool 타입을 int32로 변환"""
    file_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'batch_spec_verify.py')
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"  📄 패치 중: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. _var("bool") -> _var("int32")
    content = content.replace('done = _var("bool")', 'done = _var("int32")')
    
    # 2. T.alloc_buffer((1,), "bool", scope="shared") -> int32
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="shared"\)',
        'T.alloc_buffer((1,), "int32", scope="shared")',
        content
    )
    
    # 3. T.alloc_buffer((1,), "bool", scope="local") -> int32
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="local"\)',
        'T.alloc_buffer((1,), "int32", scope="local")',
        content
    )
    
    # 4. done[0] = False -> done[0] = T.int32(0)
    content = content.replace('done[0] = False', 'done[0] = T.int32(0)')
    
    # 5. done[0] = True -> done[0] = T.int32(1)
    content = content.replace('done[0] = True', 'done[0] = T.int32(1)')
    
    # 6. while T.Not(done[0]): -> while done[0] == T.int32(0):
    content = re.sub(
        r'while\s+T\.Not\(done\[0\]\)\s*:',
        'while done[0] == T.int32(0):',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ batch_spec_verify.py 패치 완료 (변경됨: {changed})")
    return changed


def patch_top_p_pivot(site_pkg: str) -> bool:
    """top_p_pivot.py의 bool 타입을 int32로 변환"""
    file_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'top_p_pivot.py')
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"  📄 패치 중: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. _var("bool") -> _var("int32")
    content = content.replace('es_local = _var("bool")', 'es_local = _var("int32")')
    content = content.replace('find_pivot_local = _var("bool")', 'find_pivot_local = _var("int32")')
    
    # 2. T.alloc_buffer((1,), "bool", scope="shared") -> int32
    content = content.replace(
        'es = T.alloc_buffer((1,), "bool", scope="shared")',
        'es = T.alloc_buffer((1,), "int32", scope="shared")'
    )
    content = content.replace(
        'find_pivot = T.alloc_buffer((1,), "bool", scope="shared")',
        'find_pivot = T.alloc_buffer((1,), "int32", scope="shared")'
    )
    
    # 3. find_pivot[0] = False -> find_pivot[0] = T.int32(0)
    content = content.replace('find_pivot[0] = False', 'find_pivot[0] = T.int32(0)')
    
    # 4. find_pivot[0] = True -> find_pivot[0] = T.int32(1)
    content = content.replace('find_pivot[0] = True', 'find_pivot[0] = T.int32(1)')
    
    # 5. find_pivot_local[0] = False -> find_pivot_local[0] = T.int32(0)
    content = content.replace('find_pivot_local[0] = False', 'find_pivot_local[0] = T.int32(0)')
    
    # 6. find_pivot_local[0] = True -> find_pivot_local[0] = T.int32(1)
    content = content.replace('find_pivot_local[0] = True', 'find_pivot_local[0] = T.int32(1)')
    
    # 7. es_local[0] = False -> es_local[0] = T.int32(0)
    content = content.replace('es_local[0] = False', 'es_local[0] = T.int32(0)')
    
    # 8. T.Not(find_pivot_local[0]) -> find_pivot_local[0] == T.int32(0)
    content = content.replace('T.Not(find_pivot_local[0])', 'find_pivot_local[0] == T.int32(0)')
    
    # 9. T.Not(es_local[0]) -> es_local[0] == T.int32(0)
    content = content.replace('T.Not(es_local[0])', 'es_local[0] == T.int32(0)')
    
    # 10. es[0] = 1 - total_sum_reduce[0] < pivot[pN - 1] -> T.Cast("int32", ...)
    content = content.replace(
        'es[0] = 1 - total_sum_reduce[0] < pivot[pN - 1]',
        'es[0] = T.Cast("int32", 1 - total_sum_reduce[0] < pivot[pN - 1])'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ top_p_pivot.py 패치 완료 (변경됨: {changed})")
    return changed


def verify_patch(site_pkg: str):
    """패치가 제대로 적용되었는지 검증"""
    print("\n📋 패치 검증...")
    
    # batch_spec_verify.py 검증
    bsv_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'batch_spec_verify.py')
    if os.path.exists(bsv_path):
        with open(bsv_path, 'r') as f:
            content = f.read()
        
        print("\n--- batch_spec_verify.py 검증 ---")
        if '"bool"' in content:
            print("  ❌ 아직 bool 타입이 남아있습니다!")
        else:
            print("  ✅ bool 타입이 모두 제거되었습니다")
        
        int32_count = content.count('int32')
        print(f"  📊 int32 사용 횟수: {int32_count}")
    
    # top_p_pivot.py 검증
    tpp_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'top_p_pivot.py')
    if os.path.exists(tpp_path):
        with open(tpp_path, 'r') as f:
            content = f.read()
        
        print("\n--- top_p_pivot.py 검증 ---")
        if '"bool"' in content:
            print("  ❌ 아직 bool 타입이 남아있습니다!")
        else:
            print("  ✅ bool 타입이 모두 제거되었습니다")
        
        int32_count = content.count('int32')
        print(f"  📊 int32 사용 횟수: {int32_count}")


def main():
    print("=" * 50)
    print("🔧 MLC-LLM Bool 타입 버그 패치")
    print("   GitHub Issue #3389 Fix")
    print("=" * 50)
    
    # site-packages 경로 찾기
    site_packages = site.getsitepackages()
    site_pkg = None
    
    for sp in site_packages:
        mlc_path = os.path.join(sp, 'mlc_llm')
        if os.path.exists(mlc_path):
            site_pkg = sp
            break
    
    if site_pkg is None:
        print("❌ MLC-LLM 패키지를 찾을 수 없습니다!")
        print(f"   검색한 경로: {site_packages}")
        sys.exit(1)
    
    print(f"\n📍 MLC-LLM 위치: {site_pkg}/mlc_llm")
    print()
    
    # 패치 적용
    print("[1/2] batch_spec_verify.py 패치")
    bsv_changed = patch_batch_spec_verify(site_pkg)
    
    print()
    print("[2/2] top_p_pivot.py 패치")
    tpp_changed = patch_top_p_pivot(site_pkg)
    
    # 검증
    verify_patch(site_pkg)
    
    print()
    print("=" * 50)
    if bsv_changed or tpp_changed:
        print("🎉 MLC-LLM Bool 타입 버그 패치 완료!")
    else:
        print("ℹ️  이미 패치가 적용되어 있거나 변경사항이 없습니다")
    print("=" * 50)


if __name__ == '__main__':
    main()
