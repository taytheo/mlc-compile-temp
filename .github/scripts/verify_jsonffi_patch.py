#!/usr/bin/env python3
import os
import sys
import subprocess
import mlc_llm


def main():
    print("mlc_llm package file:", getattr(mlc_llm, '__file__', 'unknown'))
    found_paths = []
    for root_dir, dirs, files in os.walk(sys.prefix):
        for name in files:
            if name == 'json_ffi_engine.cc':
                found_paths.append(os.path.join(root_dir, name))
    if not found_paths:
        print(f'ERROR: json_ffi_engine.cc not found under sys.prefix ({sys.prefix})')
        return 1
    for p in found_paths:
        print('Found patch candidate:', p)
        try:
            out = subprocess.check_output(['grep', '-n', 'jsonffi_contains_replacement', p])
            print('Marker string found in:', p)
            return 0
        except subprocess.CalledProcessError:
            print('Marker not found in:', p)
    print('ERROR: Patched json_ffi_engine.cc with marker not found in site-packages (searched sys.prefix).')
    return 2


if __name__ == '__main__':
    sys.exit(main())
