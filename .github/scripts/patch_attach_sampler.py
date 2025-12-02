#!/usr/bin/env python3
import site
import os

def main():
    sampler_path = f'{site.getsitepackages()[0]}/mlc_llm/compiler_pass/attach_sampler.py'
    
    print(f"Patching: {sampler_path}")
    
    with open(sampler_path, 'r') as f:
        content = f.read()
    
    # 원본 코드 찾아서 수정
    if 'bb.add_func(batch_spec_verify(' in content:
        print("Found batch_spec_verify call")
        
        # 함수 호출 대신 PrimFunc 반환 함수 사용
        content = content.replace(
            'bb.add_func(batch_spec_verify(T.buffer_decl((4,), "int64"), T.int64(0), T.int64(0), T.int64(4096)), "batch_verify_on_gpu_single_kernel"),',
            'bb.add_func(batch_spec_verify, "batch_verify_on_gpu_single_kernel"),'
        )
        print("Patched to use PrimFunc directly")
    
    with open(sampler_path, 'w') as f:
        f.write(content)
    
    print("attach_sampler.py patched")

if __name__ == "__main__":
    main()
