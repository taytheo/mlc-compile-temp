#!/usr/bin/env python3
"""Debug helper: report mlc_llm package layout and scan for json_ffi sources.
Gracefully handles missing `mlc_llm` imports and inspects common locations:
 - installed site-packages under sys.prefix
 - repo-local `mlc-llm-source` (when present)
 - `.github/patches` fallback
Prints the head of any found `json_ffi_engine.cc` files (up to 80 lines).
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import mlc_llm
    mlc_llm_file = getattr(mlc_llm, '__file__', 'unknown')
    mlc_llm_root = mlc_llm.__path__[0] if hasattr(mlc_llm, '__path__') else None
    print('mlc_llm package file:', mlc_llm_file)
    print('mlc_llm root:', mlc_llm_root)
except Exception:
    print('mlc_llm import failed; will search known locations instead')
    mlc_llm_root = None

candidates = []
# sys.prefix/site-packages
site_pkg = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
if site_pkg.exists():
    candidates.append(str(site_pkg))
# mlc_llm root if import succeeded
if mlc_llm_root:
    candidates.append(str(mlc_llm_root))
# repo-local possible source
local_source = REPO_ROOT / 'mlc-llm-source'
if local_source.exists():
    candidates.append(str(local_source))
# fallback patch file location
patch_dir = REPO_ROOT / '.github' / 'patches'
if patch_dir.exists():
    candidates.append(str(patch_dir))

seen = set()
print('\nScanning candidate roots for json_ffi_engine.cc...')
for p in candidates:
    if not p or p in seen:
        continue
    seen.add(p)
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
