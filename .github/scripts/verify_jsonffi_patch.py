#!/usr/bin/env python3
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def find_candidate_files():
    candidates = []
    # Search common site-packages/sys.prefix layout
    for root_dir, dirs, files in os.walk(sys.prefix):
        for name in files:
            if name == 'json_ffi_engine.cc':
                candidates.append(os.path.join(root_dir, name))
    # Also check common packagelocations
    site_pkg = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    for root_dir, dirs, files in os.walk(site_pkg):
        for name in files:
            if name == 'json_ffi_engine.cc':
                candidates.append(os.path.join(root_dir, name))
    # Repo-local fallback (mlc-llm-source or .github/patches)
    local1 = REPO_ROOT / 'mlc-llm-source' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
    local2 = REPO_ROOT / '.github' / 'patches' / 'json_ffi_engine.cc'
    for p in (local1, local2):
        if p.exists():
            candidates.append(str(p))
    # Deduplicate
    seen = set()
    res = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            res.append(p)
    return res


def check_marker_in_file(path, marker='jsonffi_contains_replacement'):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            data = fh.read()
            return marker in data
    except Exception:
        return False


def main():
    try:
        import mlc_llm
        print('mlc_llm package file:', getattr(mlc_llm, '__file__', 'unknown'))
    except Exception:
        print('mlc_llm import failed; proceeding with path search')

    found = find_candidate_files()
    if not found:
        print(f'ERROR: json_ffi_engine.cc not found under sys.prefix ({sys.prefix}) or repo-local locations')
        return 1

    print('Found candidate files:')
    for p in found:
        print(' -', p)

    for p in found:
        print('\n--- Inspecting file:', p, '---')
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                for i, l in enumerate(fh):
                    if i >= 40:
                        break
                    print(l.rstrip())
        except Exception as e:
            print('  read failed:', e)
        if check_marker_in_file(p, marker='jsonffi_contains_replacement'):
            print('🔍 Verification OK: marker "jsonffi_contains_replacement" found in:', p)
            return 0
        else:
            print('Marker not found in:', p)

    print('ERROR: Patched json_ffi_engine.cc with marker not found in any candidate locations.')
    return 2


if __name__ == '__main__':
    sys.exit(main())
