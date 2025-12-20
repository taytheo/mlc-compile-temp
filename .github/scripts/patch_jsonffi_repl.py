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
# Prefer repository-local copy at known locations, but fall back to searching the
# workspace for any matching file so CI runner layouts (where the mlc-llm repo
# may be at the workspace root or nested) still work.
PREFERRED_CANDIDATES = [
    REPO_ROOT / '.github' / 'patches' / 'json_ffi_engine.cc',
    REPO_ROOT / 'mlc-llm' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc',
    REPO_ROOT / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc',
    REPO_ROOT / 'ios' / 'mlc-llm-repo' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc',
]

def find_local_src():
    for p in PREFERRED_CANDIDATES:
        if p.exists():
            return p
    # Last resort: glob-search for any json_ffi_engine.cc under repo
    matches = list(REPO_ROOT.rglob('json_ffi_engine.cc'))
    if matches:
        # Prefer any path that contains 'mlc-llm' in it
        for m in matches:
            if 'mlc-llm' in str(m):
                return m
        return matches[0]
    return None

LOCAL_SRC = find_local_src()


def try_fetch_remote():
    import urllib.request
    candidates = []
    # Primary canonical location
    candidates.append('https://raw.githubusercontent.com/mlc-ai/mlc-llm/main/cpp/json_ffi/json_ffi_engine.cc')
    # Try using the current repo context if available
    gh_repo = os.environ.get('GITHUB_REPOSITORY')
    if gh_repo:
        candidates.append(f'https://raw.githubusercontent.com/{gh_repo}/main/mlc-llm/cpp/json_ffi/json_ffi_engine.cc')
        candidates.append(f'https://raw.githubusercontent.com/{gh_repo}/main/cpp/json_ffi/json_ffi_engine.cc')

    for url in candidates:
        try:
            print(f"Attempting to download json_ffi_engine.cc from: {url}")
            with urllib.request.urlopen(url, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    out = REPO_ROOT / 'tmp_json_ffi_engine.cc'
                    with open(out, 'wb') as f:
                        f.write(data)
                    print(f"Downloaded to: {out}")
                    return out
        except Exception as e:
            print(f"  fetch failed: {e}")
    return None

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
    global LOCAL_SRC
    if LOCAL_SRC is None or not LOCAL_SRC.exists():
        print("❌ Local source not found in workspace (searched for json_ffi_engine.cc)")
        print(f"   Searched under: {REPO_ROOT}")
        print("   Trying to fetch the file from GitHub raw URLs...")
        fetched = try_fetch_remote()
        if fetched is not None and fetched.exists():
            print(f"  ✅ Fetched remote copy: {fetched}")
            LOCAL_SRC = fetched
        else:
            print("   Tip: ensure the repository checkout contains the 'mlc-llm/cpp/json_ffi/json_ffi_engine.cc' file or adjust this script.")
            sys.exit(2)

    site_paths = find_site_pkg_paths()
    replaced = False
    replaced_targets = []
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
                replaced_targets.append(str(target))
            except Exception as e:
                print(f"  ❌ Failed to replace file: {e}")

    # write replaced targets to a file for artifact upload/debugging
    if replaced_targets:
        try:
            outdir = REPO_ROOT / 'tmp_patched_jsonffi'
            outdir.mkdir(parents=True, exist_ok=True)
            with open(outdir / 'patched_targets.txt', 'w') as fh:
                fh.write('\n'.join(replaced_targets) + '\n')
            for t in replaced_targets:
                shutil.copy2(t, outdir / ('installed-' + Path(t).name))
            print(f"  🗂 Wrote patched target info and copies to: {outdir}")
        except Exception as e:
            print(f"  ❌ Failed to write patched target copies: {e}")
    if not replaced:
        print("⚠️ Could not find an installed mlc_llm cpp/json_ffi/json_ffi_engine.cc in site-packages.")
        print("   This runner may not have mlc-llm installed yet or uses a different layout.")
        print("   Attempting to apply patch into local 'mlc-llm-source' checkout if present...")
        local_source_dir = REPO_ROOT / 'mlc-llm-source' / 'cpp' / 'json_ffi'
        try:
            if local_source_dir.exists():
                local_target = local_source_dir / 'json_ffi_engine.cc'
                shutil.copy2(LOCAL_SRC, local_target)
                print(f"  ✅ Copied patch into local mlc-llm-source at: {local_target}")
                # write patched_targets info for debugging/artifact upload
                outdir = REPO_ROOT / 'tmp_patched_jsonffi'
                outdir.mkdir(parents=True, exist_ok=True)
                with open(outdir / 'patched_targets.txt', 'w') as fh:
                    fh.write(str(local_target) + '\n')
                shutil.copy2(local_target, outdir / ('installed-' + Path(local_target).name))
                print(f"  🗂 Wrote patched target info and copy to: {outdir}")
                # Verify marker in the local copy
                marker = 'jsonffi_contains_replacement'
                with open(local_target, 'r') as f:
                    content = f.read()
                if marker in content:
                    print(f"🔍 Verification OK: marker '{marker}' found in local mlc-llm-source {local_target}")
                    return 0
                else:
                    print(f"⚠️ Marker '{marker}' not found in local copy {local_target}; please inspect the source.")
                    return 3
        except Exception as e:
            print(f"  ❌ Failed to write patch into mlc-llm-source: {e}")

        print("⚠️ Could not apply patch to installed site-packages or local mlc-llm-source. The build may still succeed if compile picks up local sources.")
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

    print("⚠️ Patch applied but verification marker not found. Please inspect the installed package or the local source.")
    return 3

if __name__ == '__main__':
    print("🔧 Running json_ffi patch script")
    rc = patch_mlc_llm()
    if rc == 0:
        print("✅ patch_jsonffi_repl.py completed successfully")
    else:
        print(f"❌ patch_jsonffi_repl.py finished with code {rc}")
    sys.exit(rc)
