#!/usr/bin/env python3
import site
import re
import sys

def main():
    file_path = f'{site.getsitepackages()[0]}/mlc_llm/op/batch_spec_verify.py'
    
    print(f"=== Patching {file_path} ===")
    
    # Before patch check
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            print("=== ORIGINAL CODE SAMPLE ===")
            lines = content.split('\n')
            for i, line in enumerate(lines[110:125], 110):  # 문제 발생 영역 주변
                print(f"{i}: {line}")
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Apply comprehensive patches
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. alloc_buffer 패치
    content = re.sub(
        r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*\"bool\"\s*\)', 
        'T.alloc_buffer((1,), "int32")', 
        content
    )
    
    # 2. done 변수 타입 패치 (더 강력하게)
    content = content.replace('done[0] = False', 'done[0] = 0')
    content = content.replace('done[0] = True', 'done[0] = 1')
    
    # 3. while 조건 패치
    content = re.sub(r'while\s+T\.Not\(done\[0\]\)\s*:', 'while done[0] == 0:', content)
    
    # 4. 추가 패치: 변수 선언 찾아서 수정
    # done = T.alloc_buffer((1,), "bool") 패턴 찾기
    content = re.sub(
        r'done\s*=\s*T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*\"bool\"\s*\)',
        'done = T.alloc_buffer((1,), "int32")',
        content
    )
    
    # 5. done 변수에 대한 모든 참조 확인
    # done[0]을 int32로 명시적으로 캐스팅하는 코드 추가
    content = re.sub(
        r'done\[0\]\s*=\s*0',
        'done[0] = T.int32(0)',
        content
    )
    content = re.sub(
        r'done\[0\]\s*=\s*1',
        'done[0] = T.int32(1)',
        content
    )
    
    # 6. while 조건도 명시적으로 int32 비교
    content = re.sub(
        r'while done\[0\] == 0',
        'while T.cast(done[0], "bool") == False',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print('\n=== Patch applied ===')
    
    # After patch verification
    with open(file_path, 'r') as f:
        content = f.read()
        print("=== PATCHED CODE SAMPLE ===")
        lines = content.split('\n')
        for i, line in enumerate(lines[110:125], 110):
            print(f"{i}: {line}")
        
        # Verify patches
        checks = [
            ('alloc_buffer.*int32', 'int32 alloc_buffer'),
            ('done\[0\] = T\.int32\(0\)', 'done[0] = T.int32(0)'),
            ('done\[0\] = T\.int32\(1\)', 'done[0] = T.int32(1)'),
            ('T\.cast\(done\[0\].*bool.*', 'T.cast for bool conversion'),
        ]
        
        for pattern, desc in checks:
            matches = re.findall(pattern, content)
            print(f"{desc}: {len(matches)} found")

if __name__ == "__main__":
    main()
