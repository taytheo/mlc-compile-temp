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
            matches = re.findall(r'alloc_buffer.*bool|done\[0\]|while.*T\.Not', content)
            print(f"Found {len(matches)} patterns to patch")
            if matches:
                print("Sample patterns:", matches[:3])
    except Exception as e:
        print(f"Error reading file: {e}")
    
    # Apply patches
    with open(file_path, 'r') as f:
        content = f.read()
    
    content = re.sub(r'T\.alloc_buffer\(\s*\(\s*1\s*,\s*\)\s*,\s*\"bool\"\s*\)', 'T.alloc_buffer((1,), \"int32\")', content)
    content = content.replace('done[0] = False', 'done[0] = 0')
    content = content.replace('done[0] = True', 'done[0] = 1')
    content = re.sub(r'while\s+T\.Not\(done\[0\]\)\s*:', 'while done[0] == 0:', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print('Patch applied to batch_spec_verify.py')
    
    # After patch verification
    with open(file_path, 'r') as f:
        content = f.read()
        matches = re.findall(r'alloc_buffer.*int32|done\[0\] ==|done\[0\] = 0|done\[0\] = 1', content)
        print(f"Verification: Found {len(matches)} patched patterns")
        if matches:
            print("Sample patched patterns:", matches[:3])

if __name__ == "__main__":
    main()
