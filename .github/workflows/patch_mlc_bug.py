#!/usr/bin/env python3
"""
Patch for MLC-LLM batch_spec_verify.py bug
Fixes: "cannot make const for type bool" error during iOS compilation
"""

import site
import os
import re

def main():
    site_packages = site.getsitepackages()[0]
    buggy_file = os.path.join(site_packages, "mlc_llm", "op", "batch_spec_verify.py")
    
    if not os.path.exists(buggy_file):
        print(f"File not found: {buggy_file}")
        return
    
    print(f"Patching: {buggy_file}")
    
    with open(buggy_file, "r") as f:
        content = f.read()
    
    print("=== Before patch (relevant lines) ===")
    for i, line in enumerate(content.split('\n'), 1):
        if 'alloc_buffer' in line or 'done[' in line:
            print(f"{i}: {line}")
    
    # Fix 1: Change bool buffer to int32
    content = re.sub(
        r'T\.alloc_buffer\s*\(\s*\(\s*1\s*,\s*\)\s*,\s*["\']bool["\']\s*\)',
        'T.alloc_buffer((1,), "int32")',
        content
    )
    
    # Fix 2: Change boolean values to integers
    content = re.sub(r'done\[0\]\s*=\s*False', 'done[0] = 0', content)
    content = re.sub(r'done\[0\]\s*=\s*True', 'done[0] = 1', content)
    
    with open(buggy_file, "w") as f:
        f.write(content)
    
    print("\n=== After patch (relevant lines) ===")
    for i, line in enumerate(content.split('\n'), 1):
        if 'alloc_buffer' in line or 'done[' in line:
            print(f"{i}: {line}")
    
    print("\nPatch applied successfully!")

if __name__ == "__main__":
    main()
