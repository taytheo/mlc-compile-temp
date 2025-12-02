#!/usr/bin/env python3
import site
import os

def main():
    sampler_path = f'{site.getsitepackages()[0]}/mlc_llm/compiler_pass/attach_sampler.py'
    
    print(f"Patching: {sampler_path}")
    
    with open(sampler_path, 'r') as f:
        content = f.read()
    
    # 라인 371 찾아서 수정
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'batch_spec_verify(vocab_size)' in line:
            print(f"Found at line {i+1}: {line}")
            # 함수 호출 제거하고 PrimFunc 직접 사용
            lines[i] = line.replace(
                'batch_spec_verify(vocab_size)',
                'batch_spec_verify()'  # 인자 없이 호출
            )
            print(f"Changed to: {lines[i]}")
            break
    
    # 변경 사항 저장
    with open(sampler_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print("Patched: Removed arguments from batch_spec_verify() call")

if __name__ == "__main__":
    main()
