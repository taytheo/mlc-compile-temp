#!/usr/bin/env python3
"""
Patch script to copy local json_ffi_engine.cc into the installed mlc-llm package
so that subsequent `mlc_llm compile --device iphone` builds include our C++ changes.

Behavior:
 - Locates the installed `mlc_llm` package in site-packages
 - Replaces `cpp/json_ffi/json_ffi_engine.cc` with the repository version
 - Verifies the replacement and emits diagnostics to stdout

This mirrors the approach used by `.github/scripts/patch_mlc_bool_bug.py`.
"""

import os
import sys
import site
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SRC = REPO_ROOT / 'mlc-llm' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'

def find_site_pkg_paths():
    paths = []
    # site.getsitepackages may not exist in some venvs, try multiple approaches
    try:
        paths.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        paths.append(site.getusersitepackages())
    except Exception:
        pass
    # also include dist-packages like layout
    candidate = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    paths.append(str(candidate))
    # unique
    seen = []
    for p in paths:
        if p and p not in seen:
            seen.append(p)
    return seen

def patch_mlc_llm():
    if not LOCAL_SRC.exists():
        print(f"❌ Local source not found: {LOCAL_SRC}")
        sys.exit(2)

    site_paths = find_site_pkg_paths()
    replaced = False
    for sp in site_paths:
        target = Path(sp) / 'mlc_llm' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
        if target.exists():
            print(f"📍 Found installed mlc_llm source at: {target}")
            # backup original
            bak = target.with_suffix('.cc.bak')
            try:
                if not bak.exists():
                    shutil.copy2(target, bak)
                    print(f"  🔁 Backup written: {bak}")
                shutil.copy2(LOCAL_SRC, target)
                print(f"  ✅ Replaced installed json_ffi_engine.cc with local copy")
                replaced = True
            except Exception as e:
                print(f"  ❌ Failed to replace file: {e}")
    if not replaced:
        print("⚠️ Could not find an installed mlc_llm cpp/json_ffi/json_ffi_engine.cc in site-packages.")
        print("   This runner may not have mlc-llm installed yet or uses a different layout.")
        print("   The build may still succeed if mlc_llm compile picks up local sources from repository.")
        return 1

    # verification: look for a distinctive marker from our local copy
    marker = 'jsonffi_contains_replacement'
    for sp in site_paths:
        target = Path(sp) / 'mlc_llm' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
        if target.exists():
            with open(target, 'r') as f:
                content = f.read()
            if marker in content:
                print(f"🔍 Verification OK: marker '{marker}' found in {target}")
                return 0

    print("⚠️ Patch applied but verification marker not found. Please inspect the installed package.")
    return 3

if __name__ == '__main__':
    print("🔧 Running json_ffi patch script")
    rc = patch_mlc_llm()
    if rc == 0:
        print("✅ patch_jsonffi_repl.py completed successfully")
    else:
        print(f"❌ patch_jsonffi_repl.py finished with code {rc}")
    sys.exit(rc)
