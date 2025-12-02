#!/usr/bin/env python3
import site
import os

def main():
    sampler_path = f'{site.getsitepackages()[0]}/mlc_llm/compiler_pass/attach_sampler.py'
    
    print(f"Patching: {sampler_path}")
    
    with open(sampler_path, 'r') as f:
        content = f.read()
    
    # 원본 라인 찾기
    original_line = 'bb.add_func(batch_spec_verify(vocab_size), "batch_verify_on_gpu_single_kernel"),'
    
    if original_line in content:
        print("Found the problematic line")
        
        # 기본값으로 모든 매개변수 제공
        fixed_line = 'bb.add_func(batch_spec_verify(T.buffer_decl((4,), "int64"), T.int64(0), T.int64(0), T.int64(4096)), "batch_verify_on_gpu_single_kernel"),'
        
        content = content.replace(original_line, fixed_line)
        print("Line patched successfully")
    else:
        print("Searching for similar pattern...")
        # 다른 패턴 찾기
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'batch_spec_verify(' in line and 'batch_verify_on_gpu_single_kernel' in line:
                print(f"Found at line {i+1}: {line}")
                # 기본 매개변수로 교체
                lines[i] = line.replace(
                    'batch_spec_verify(vocab_size)',
                    'batch_spec_verify(T.buffer_decl((4,), "int64"), T.int64(0), T.int64(0), T.int64(4096))'
                )
                print(f"Replaced with: {lines[i]}")
        
        content = '\n'.join(lines)
    
    # 변경된 내용 저장
    with open(sampler_path, 'w') as f:
        f.write(content)
    
    print("attach_sampler.py patched")

if __name__ == "__main__":
    main()
