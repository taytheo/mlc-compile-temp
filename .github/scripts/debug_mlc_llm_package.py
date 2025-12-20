#!/usr/bin/env python3
"""Debug helper: report mlc_llm package layout and scan for json_ffi sources.
Prints the mlc_llm __file__ and searches a few candidate roots for
`json_ffi_engine.cc`, printing the head of any found files (up to 80 lines).
"""
import os
import sys
import mlc_llm

print('mlc_llm file:', getattr(mlc_llm, '__file__', 'unknown'))
root = mlc_llm.__path__[0] if hasattr(mlc_llm, '__path__') else None
print('mlc_llm root:', root)

candidates = [root, sys.prefix, os.getcwd()]
for p in candidates:
    if not p:
        continue
    if not os.path.exists(p):
        continue
    print('\n=== scanning:', p, '===')
    count = 0
    for r, dirs, files in os.walk(p):
        for name in files:
            if name == 'json_ffi_engine.cc':
                f = os.path.join(r, name)
                print('FOUND:', f)
                try:
                    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                        print('--- head of file ---')
                        for i, l in enumerate(fh):
                            if i >= 80:
                                break
                            print(l.rstrip())
                    count += 1
                except Exception as e:
                    print('  read failed:', e)
        if count > 4:
            break

print('\nDone')
