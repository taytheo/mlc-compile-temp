#!/usr/bin/env python3
import importlib, pkgutil, site, os
try:
    m = importlib.import_module('mlc_llm')
    print('installed mlc_llm file:', getattr(m, '__file__', 'unknown'))
    root = getattr(m, '__path__', [None])[0]
    if root and os.path.isdir(root):
        print('\nListing top-level mlc_llm package contents (up to 200 entries):')
        for i, entry in enumerate(sorted(os.listdir(root))):
            if i>=200:
                break
            print('  ', entry)
        # show json_ffi sources if present
        for r, d, files in os.walk(root):
            for f in files:
                if 'json_ffi' in r and f.endswith('.cc'):
                    print('Found json_ffi file:', os.path.join(r, f))
except Exception as e:
    print('mlc_llm import failed after pip install:', e)

# Also list site-packages candidates
print('\nInspecting common site-packages locations...')
for p in site.getsitepackages():
    pdir = os.path.join(p, 'mlc_llm')
    if os.path.isdir(pdir):
        print('site-packages mlc_llm found at:', pdir)
        try:
            for i, entry in enumerate(sorted(os.listdir(pdir))):
                if i>=200:
                    break
                print('  ', entry)
        except Exception as e:
            print('  failed to list:', e)
