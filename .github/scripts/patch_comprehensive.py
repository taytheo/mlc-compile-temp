#!/usr/bin/env python3
import site
import os
import re

def main():
    mlc_dir = site.getsitepackages()[0] + '/mlc_llm'
    
    print("=== COMPREHENSIVE BOOL PATCH ===")
    
    # 패치할 파일들 목록
    files_to_patch = [
        ('op/top_p_pivot.py', [
            (r'find_pivot\[0\] = False', 'find_pivot[0] = 0'),
            (r'find_pivot\[0\] = True', 'find_pivot[0] = 1'),
            (r'"bool"', '"int32"'),
        ]),
        ('op/batch_spec_verify.py', [
            (r'"bool"', '"int32"'),
        ]),
    ]
    
    for rel_path, replacements in files_to_patch:
        file_path = os.path.join(mlc_dir, rel_path)
        
        if os.path.exists(file_path):
            print(f"\nPatching {rel_path}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # 추가: T.Not 패치
            content = content.replace('T.Not(', 'not (')
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"  ✓ Patched {rel_path}")
            else:
                print(f"  ⓘ No changes needed for {rel_path}")
        else:
            print(f"  ✗ File not found: {rel_path}")
    
    # attach_sampler.py 패치 (계속 필요)
    sampler_path = os.path.join(mlc_dir, 'compiler_pass/attach_sampler.py')
    if os.path.exists(sampler_path):
        with open(sampler_path, 'r') as f:
            content = f.read()
        
        if 'batch_spec_verify(vocab_size)' in content:
            content = content.replace(
                'batch_spec_verify(vocab_size)',
                'batch_spec_verify()'
            )
            with open(sampler_path, 'w') as f:
                f.write(content)
            print("\n✓ Patched attach_sampler.py")
    
    print("\n=== SEARCHING FOR OTHER BOOL ISSUES ===")
    
    # bool 관련 키워드가 있는 다른 파일 찾기
    bool_keywords = ['= False', '= True', '"bool"', 'dtype="bool"']
    
    for root, dirs, files in os.walk(mlc_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                        issues = []
                        for keyword in bool_keywords:
                            if keyword in content:
                                issues.append(keyword)
                        
                        if issues and 'test' not in filepath:
                            rel_path = filepath.replace(mlc_dir + '/', '')
                            print(f"  ⚠ {rel_path}: {', '.join(issues[:3])}")
                except:
                    pass
    
    print("\n=== PATCH COMPLETE ===")
    print("All known bool-related issues should be resolved")

if __name__ == "__main__":
    main()
