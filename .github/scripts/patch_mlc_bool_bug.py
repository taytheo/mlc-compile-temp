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
    
    # 1. 모든 _var("bool") -> _var("int32")
    content = content.replace('_var("bool")', '_var("int32")')
    
    # 2. 모든 T.alloc_buffer with "bool" -> "int32"
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="shared"\)',
        'T.alloc_buffer((1,), "int32", scope="shared")',
        content
    )
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="local"\)',
        'T.alloc_buffer((1,), "int32", scope="local")',
        content
    )
    
    # 3. 모든 [0] = False -> [0] = T.int32(0)
    content = re.sub(r'\[0\]\s*=\s*False', '[0] = T.int32(0)', content)
    
    # 4. 모든 [0] = True -> [0] = T.int32(1)
    content = re.sub(r'\[0\]\s*=\s*True', '[0] = T.int32(1)', content)
    
    # 5. 모든 T.Not(...[0]) -> ...[0] == T.int32(0)
    content = re.sub(
        r'T\.Not\((\w+)\[0\]\)',
        r'\1[0] == T.int32(0)',
        content
    )
    
    # 6. while 문 내의 T.Not 처리
    content = re.sub(
        r'while\s+T\.Not\((\w+)\[0\]\)\s*:',
        r'while \1[0] == T.int32(0):',
        content
    )
    
    # 7. pred_shared[0] = 비교식 -> T.Cast("int32", 비교식)
    # pred_shared[0] = p_child[0] >= uniform_sample[0] * q_child[0]
    content = re.sub(
        r'pred_shared\[0\]\s*=\s*(.+?)(\s*#.*)?$',
        r'pred_shared[0] = T.Cast("int32", \1)\2',
        content,
        flags=re.MULTILINE
    )
    
    # 8. if pred_local[0]: -> if pred_local[0] != T.int32(0):
    content = re.sub(
        r'if\s+(\w+)\[0\]\s*:',
        r'if \1[0] != T.int32(0):',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ batch_spec_verify.py 패치 완료 (변경됨: {changed})")
    return changed


def patch_top_p_pivot(site_pkg: str) -> bool:
    """batch_spec_verify.py의 bool 타입을 int32로 변환"""
    file_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'batch_spec_verify.py')
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"  📄 패치 중: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. 모든 _var("bool") -> _var("int32")
    content = content.replace('_var("bool")', '_var("int32")')
    
    # 2. 모든 T.alloc_buffer with "bool" -> "int32"
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="shared"\)',
        'T.alloc_buffer((1,), "int32", scope="shared")',
        content
    )
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="local"\)',
        'T.alloc_buffer((1,), "int32", scope="local")',
        content
    )
    
    # 3. 모든 [0] = False -> [0] = T.int32(0)
    content = re.sub(r'\[0\]\s*=\s*False', '[0] = T.int32(0)', content)
    
    # 4. 모든 [0] = True -> [0] = T.int32(1)
    content = re.sub(r'\[0\]\s*=\s*True', '[0] = T.int32(1)', content)
    
    # 5. 모든 T.Not(...[0]) -> ...[0] == T.int32(0)
    content = re.sub(
        r'T\.Not\((\w+)\[0\]\)',
        r'\1[0] == T.int32(0)',
        content
    )
    
    # 6. while 문 내의 T.Not 처리
    content = re.sub(
        r'while\s+T\.Not\((\w+)\[0\]\)\s*:',
        r'while \1[0] == T.int32(0):',
        content
    )
    
    # 7. pred_shared[0] = 비교식 -> T.Cast("int32", 비교식)
    # pred_shared[0] = p_child[0] >= uniform_sample[0] * q_child[0]
    content = re.sub(
        r'pred_shared\[0\]\s*=\s*(.+?)(\s*#.*)?$',
        r'pred_shared[0] = T.Cast("int32", \1)\2',
        content,
        flags=re.MULTILINE
    )
    
    # 8. if pred_local[0]: -> if pred_local[0] != T.int32(0):
    content = re.sub(
        r'if\s+(\w+)\[0\]\s*:',
        r'if \1[0] != T.int32(0):',
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
    
    # 1. 모든 _var("bool") -> _var("int32")
    content = content.replace('_var("bool")', '_var("int32")')
    
    # 2. 모든 T.alloc_buffer with "bool" -> "int32"
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="shared"\)',
        'T.alloc_buffer((1,), "int32", scope="shared")',
        content
    )
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*"bool"\s*,\s*scope="local"\)',
        'T.alloc_buffer((1,), "int32", scope="local")',
        content
    )
    
    # 3. 모든 [0] = False -> [0] = T.int32(0)
    content = re.sub(r'\[0\]\s*=\s*False', '[0] = T.int32(0)', content)
    
    # 4. 모든 [0] = True -> [0] = T.int32(1)
    content = re.sub(r'\[0\]\s*=\s*True', '[0] = T.int32(1)', content)
    
    # 5. 모든 T.Not(...[0]) -> ...[0] == T.int32(0)
    content = re.sub(
        r'T\.Not\((\w+)\[0\]\)',
        r'\1[0] == T.int32(0)',
        content
    )
    
    # 6. bool 비교 결과를 int32로 캐스팅
    # es[0] = 1 - total_sum_reduce[0] < pivot[pN - 1] -> T.Cast("int32", ...)
    content = re.sub(
        r'es\[0\]\s*=\s*1\s*-\s*total_sum_reduce\[0\]\s*<\s*pivot\[pN\s*-\s*1\]',
        'es[0] = T.Cast("int32", 1 - total_sum_reduce[0] < pivot[pN - 1])',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ top_p_pivot.py 패치 완료 (변경됨: {changed})")
    return changed


def patch_tvm_sampling(site_pkg: str) -> bool:
    """TVM sampling.py의 bool 타입을 int32로 변환"""
    file_path = os.path.join(site_pkg, 'tvm', 'relax', 'backend', 'gpu_generic', 'sampling.py')
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"  📄 패치 중: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. 모든 T.alloc_buffer with "bool" -> "int32"
    # shared_buf = T.alloc_buffer((TX * TY,), "bool", scope="shared")
    content = re.sub(
        r'T\.alloc_buffer\(\s*\([^)]+\)\s*,\s*"bool"\s*,\s*scope="shared"\)',
        lambda m: m.group(0).replace('"bool"', '"int32"'),
        content
    )
    content = re.sub(
        r'T\.alloc_buffer\(\s*\([^)]+\)\s*,\s*"bool"\s*,\s*scope="local"\)',
        lambda m: m.group(0).replace('"bool"', '"int32"'),
        content
    )
    
    # 2. compare_bool_not_equal 함수의 반환 타입 및 비교 수정
    # def compare_bool_not_equal(a: T.bool, b: T.bool) -> T.bool:
    content = re.sub(
        r'def compare_bool_not_equal\(a:\s*T\.bool,\s*b:\s*T\.bool\)\s*->\s*T\.bool:',
        'def compare_bool_not_equal(a: T.int32, b: T.int32) -> T.int32:',
        content
    )
    
    # 3. T.Cast("int8", a) != T.Cast("int8", b) -> T.Cast("int32", a != b)
    # 이 부분은 int32 버퍼이므로 직접 비교 가능
    content = re.sub(
        r'return T\.Cast\("int8", a\) != T\.Cast\("int8", b\)',
        'return T.Cast("int32", a != b)',
        content
    )
    
    # 4. source_local[0] 반환을 int32로 캐스팅
    # output_local[0] = ... source_local[0]
    # 이미 버퍼가 int32이므로 추가 작업 불필요
    
    # 5. valid[v] = prob_local > threshold and idx < vocab_size
    # bool 표현식을 int32로 캐스팅
    content = re.sub(
        r'valid\[v\]\s*=\s*prob_local\s*>\s*threshold\s*and\s*idx\s*<\s*vocab_size',
        'valid[v] = T.Cast("int32", prob_local > threshold and idx < vocab_size)',
        content
    )
    
    # 6. greater_than_u[v] = (...) 여러 줄 표현식 처리
    # 직접 문자열 치환으로 처리
    old_greater = '''greater_than_u[v] = (
                        cumsum[ty * warp_elem + tx * thread_elem + v] + aggregate[()]
                        >= uniform_sample - eps
                    )'''
    new_greater = '''greater_than_u[v] = T.Cast("int32",
                        cumsum[ty * warp_elem + tx * thread_elem + v] + aggregate[()]
                        >= uniform_sample - eps
                    )'''
    content = content.replace(old_greater, new_greater)
    
    # 7. mask[v] = mask[v] and valid[v] -> T.Cast("int32", ...)
    content = re.sub(
        r'mask\[v\]\s*=\s*mask\[v\]\s*and\s*valid\[v\]',
        'mask[v] = T.Cast("int32", mask[v] != 0 and valid[v] != 0)',
        content
    )
    
    # 8. if mask_local[i]: -> if mask_local[i] != 0:
    content = re.sub(
        r'if mask_local\[i\]:',
        'if mask_local[i] != 0:',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ tvm/sampling.py 패치 완료 (변경됨: {changed})")
    return changed


def patch_low_batch_specialization(site_pkg: str) -> bool:
    """low_batch_specialization.py의 True를 tir.IntImm으로 변환"""
    file_path = os.path.join(site_pkg, 'mlc_llm', 'compiler_pass', 'low_batch_specialization.py')
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  파일을 찾을 수 없습니다: {file_path}")
        return False
    
    print(f"  📄 패치 중: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # tir.BlockRealize([], True, body) -> tir.BlockRealize([], tir.IntImm("bool", 1), body)
    content = content.replace(
        'tir.BlockRealize([], True, body)',
        'tir.BlockRealize([], tir.IntImm("bool", 1), body)'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    changed = original != content
    print(f"  ✅ low_batch_specialization.py 패치 완료 (변경됨: {changed})")
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
            # 어디에 남아있는지 출력
            for i, line in enumerate(content.split('\n'), 1):
                if '"bool"' in line:
                    print(f"     Line {i}: {line.strip()}")
        else:
            print("  ✅ bool 타입이 모두 제거되었습니다")
        
        # T.Not 체크
        if 'T.Not(' in content:
            print("  ❌ T.Not()가 남아있습니다!")
            for i, line in enumerate(content.split('\n'), 1):
                if 'T.Not(' in line:
                    print(f"     Line {i}: {line.strip()}")
        else:
            print("  ✅ T.Not()가 모두 제거되었습니다")
        
        int32_count = content.count('int32')
        print(f"  📊 int32 사용 횟수: {int32_count}")
        
        # 핵심 패치 확인
        print("\n  🔍 핵심 패치 확인:")
        checks = [
            ('_var("int32")', 'done = _var("int32")'),
            ('T.alloc_buffer((1,), "int32"', 'pred_shared/pred_local 버퍼'),
            ('T.Cast("int32"', 'pred_shared 비교 결과 캐스팅'),
            ('!= T.int32(0)', 'if pred_local[0] 조건'),
            ('== T.int32(0)', 'while done[0] 조건'),
        ]
        for pattern, desc in checks:
            if pattern in content:
                print(f"     ✅ {desc}")
            else:
                print(f"     ❌ {desc} - 패턴 없음: {pattern}")
    
    # top_p_pivot.py 검증
    tpp_path = os.path.join(site_pkg, 'mlc_llm', 'op', 'top_p_pivot.py')
    if os.path.exists(tpp_path):
        with open(tpp_path, 'r') as f:
            content = f.read()
        
        print("\n--- top_p_pivot.py 검증 ---")
        if '"bool"' in content:
            print("  ❌ 아직 bool 타입이 남아있습니다!")
            for i, line in enumerate(content.split('\n'), 1):
                if '"bool"' in line:
                    print(f"     Line {i}: {line.strip()}")
        else:
            print("  ✅ bool 타입이 모두 제거되었습니다")
        
        if 'T.Not(' in content:
            print("  ❌ T.Not()가 남아있습니다!")
            for i, line in enumerate(content.split('\n'), 1):
                if 'T.Not(' in line:
                    print(f"     Line {i}: {line.strip()}")
        else:
            print("  ✅ T.Not()가 모두 제거되었습니다")
        
        int32_count = content.count('int32')
        print(f"  📊 int32 사용 횟수: {int32_count}")
    
    # tvm/sampling.py 검증
    sampling_path = os.path.join(site_pkg, 'tvm', 'relax', 'backend', 'gpu_generic', 'sampling.py')
    if os.path.exists(sampling_path):
        with open(sampling_path, 'r') as f:
            content = f.read()
        
        print("\n--- tvm/sampling.py 검증 ---")
        bool_buffers = re.findall(r'T\.alloc_buffer\([^)]+,\s*"bool"', content)
        if bool_buffers:
            print(f"  ❌ 아직 bool 버퍼가 {len(bool_buffers)}개 남아있습니다!")
            for buf in bool_buffers[:5]:
                print(f"     {buf}")
        else:
            print("  ✅ bool 버퍼가 모두 int32로 변환되었습니다")
        
        int32_count = content.count('"int32"')
        print(f"  📊 int32 버퍼 사용 횟수: {int32_count}")


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
    print("[1/4] batch_spec_verify.py 패치")
    bsv_changed = patch_batch_spec_verify(site_pkg)
    
    print()
    print("[2/4] top_p_pivot.py 패치")
    tpp_changed = patch_top_p_pivot(site_pkg)
    
    print()
    print("[3/4] tvm/sampling.py 패치")
    sampling_changed = patch_tvm_sampling(site_pkg)
    
    print()
    print("[4/4] low_batch_specialization.py 패치")
    lbs_changed = patch_low_batch_specialization(site_pkg)
    
    # 검증
    verify_patch(site_pkg)
    
    print()
    print("=" * 50)
    if bsv_changed or tpp_changed or sampling_changed or lbs_changed:
        print("🎉 MLC-LLM Bool 타입 버그 패치 완료!")
    else:
        print("ℹ️  이미 패치가 적용되어 있거나 변경사항이 없습니다")
    print("=" * 50)


if __name__ == '__main__':
    main()
