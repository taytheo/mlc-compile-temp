#!/usr/bin/env python3
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def find_candidate_files():
    candidates = []
    # Search common site-packages/sys.prefix layout (text files in package sources)
    site_pkg = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    for root_dir, dirs, files in os.walk(site_pkg):
        for name in files:
            if name == 'json_ffi_engine.cc':
                candidates.append(os.path.join(root_dir, name))
    # Also scan entire sys.prefix for any copies (venv layouts vary)
    for root_dir, dirs, files in os.walk(sys.prefix):
        for name in files:
            if name == 'json_ffi_engine.cc':
                candidates.append(os.path.join(root_dir, name))
    # Repo-local fallback (mlc-llm-source or .github/patches)
    local1 = REPO_ROOT / 'mlc-llm-source' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
    local2 = REPO_ROOT / '.github' / 'patches' / 'json_ffi_engine.cc'
    for p in (local1, local2):
        if p.exists():
            candidates.append(str(p))
    # Also include debug-patched targets file if present
    patched_targets_file = REPO_ROOT / 'tmp_patched_jsonffi' / 'patched_targets.txt'
    if patched_targets_file.exists():
        with open(patched_targets_file, 'r', encoding='utf-8', errors='replace') as fh:
            for l in fh:
                lp = l.strip()
                if lp:
                    candidates.append(lp)
    # Deduplicate and return
    seen = set()
    res = []
    for p in candidates:
        if p and p not in seen:
            seen.add(p)
            res.append(p)
    return res


def check_marker_in_file(path, markers=None):
    if markers is None:
        markers = ['jsonffi_contains_replacement', 'MLCJSONFFIEngineForceLink_v1']
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            data = fh.read()
            for m in markers:
                if m in data:
                    return m
    except Exception:
        return None
    return None


def main():
    try:
        import mlc_llm
        print('mlc_llm package file:', getattr(mlc_llm, '__file__', 'unknown'))
    except Exception:
        print('mlc_llm import failed; proceeding with path search')

    found = find_candidate_files()
    if not found:
        print(f'ERROR: json_ffi_engine.cc not found under sys.prefix ({sys.prefix}) or repo-local locations')
        print('Hint: ensure .github/patches/json_ffi_engine.cc exists or run .github/scripts/patch_jsonffi_repl.py')
        return 1

    print('Found candidate files:')
    for p in found:
        print(' -', p)

    any_ok = False
    for p in found:
        print('\n--- Inspecting file:', p, '---')
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                for i, l in enumerate(fh):
                    if i >= 80:
                        break
                    print(l.rstrip())
        except Exception as e:
            print('  read failed:', e)
        marker_found = check_marker_in_file(p)
        if marker_found:
            print(f'🔍 Verification OK: marker "{marker_found}" found in: {p}')
            any_ok = True
        else:
            print('Marker not found in:', p)

    if any_ok:
        return 0

    print('ERROR: Patched json_ffi_engine.cc with marker not found in any candidate locations.')
    print('Hint: run .github/scripts/patch_jsonffi_repl.py and re-run this verifier; collect tmp_patched_jsonffi/* for debugging.')
    return 2


if __name__ == '__main__':
    sys.exit(main())
