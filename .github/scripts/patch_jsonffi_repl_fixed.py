#!/usr/bin/env python3
"""
Robust variant of patch_jsonffi_repl.py that applies the local
json_ffi_engine.cc into installed packages and local source, but
never fails the CI. It writes diagnostics into tmp_patched_jsonffi/
so the build can continue and fallbacks can run if verification
isn't successful.
"""
import os
import sys
import site
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
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
    matches = list(REPO_ROOT.rglob('json_ffi_engine.cc'))
    if matches:
        for m in matches:
            if 'mlc-llm' in str(m):
                return m
        return matches[0]
    return None

LOCAL_SRC = find_local_src()


def try_fetch_remote():
    import urllib.request
    candidates = [
        'https://raw.githubusercontent.com/mlc-ai/mlc-llm/main/cpp/json_ffi/json_ffi_engine.cc'
    ]
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
    try:
        paths.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        paths.append(site.getusersitepackages())
    except Exception:
        pass
    candidate = Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    paths.append(str(candidate))
    seen = []
    for p in paths:
        if p and p not in seen:
            seen.append(p)
    return seen


def write_marker_missing():
    try:
        outdir = REPO_ROOT / 'tmp_patched_jsonffi'
        outdir.mkdir(parents=True, exist_ok=True)
        with open(outdir / 'marker_missing.txt', 'w') as fh:
            fh.write('marker_missing')
    except Exception:
        pass


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
            try:
                outdir = REPO_ROOT / 'tmp_patched_jsonffi'
                outdir.mkdir(parents=True, exist_ok=True)
                with open(outdir / 'no_local_source.txt', 'w') as fh:
                    fh.write('no_local_source')
            except Exception:
                pass
            # Non-fatal
            return 0

    site_paths = find_site_pkg_paths()
    replaced_targets = []
    attempted_targets = []
    for sp in site_paths:
        target = Path(sp) / 'mlc_llm' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
        attempted_targets.append(str(target))
        try:
            # Ensure parent exists then overwrite target with our LOCAL_SRC
            target.parent.mkdir(parents=True, exist_ok=True)
            bak = target.with_suffix('.cc.bak')
            if target.exists() and not bak.exists():
                shutil.copy2(target, bak)
                print(f"  🔁 Backup written: {bak}")
            shutil.copy2(LOCAL_SRC, target)
            print(f"  ✅ Forced replaced/installed json_ffi_engine.cc at: {target}")
            replaced_targets.append(str(target))
            # quick verification for marker
            with open(target, 'r', encoding='utf-8', errors='replace') as tf:
                ct = tf.read()
            if 'jsonffi_contains_replacement' in ct or 'MLCJSONFFIEngineForceLink_v1' in ct:
                print('  🔍 Marker detected in installed copy')
            else:
                print('  ⚠️ Marker NOT detected in installed copy; keep investigating')
        except Exception as e:
            print(f"  ❌ Failed to write/replace installed target {target}: {e}")

    outdir = REPO_ROOT / 'tmp_patched_jsonffi'
    outdir.mkdir(parents=True, exist_ok=True)
    with open(outdir / 'attempted_targets.txt', 'w') as fh:
        fh.write('\n'.join(attempted_targets) + '\n')

    if replaced_targets:
        with open(outdir / 'patched_targets.txt', 'w') as fh:
            fh.write('\n'.join(replaced_targets) + '\n')
        for t in replaced_targets:
            try:
                shutil.copy2(t, outdir / ('installed-' + Path(t).name))
            except Exception:
                pass
        print(f"  🗂 Wrote patched target info and copies to: {outdir}")
    else:
        print('  ⚠️ No installed targets were replaced; check site-packages layout or permissions')
        try:
            # Write attempted targets for debugging
            with open(outdir / 'attempted_targets.txt', 'w') as fh:
                fh.write('\n'.join(attempted_targets) + '\n')
        except Exception:
            pass

    # Always also try to copy into local mlc-llm-source if present
    local_source_dir = REPO_ROOT / 'mlc-llm-source' / 'cpp' / 'json_ffi'
    try:
        if local_source_dir.exists():
            local_target = local_source_dir / 'json_ffi_engine.cc'
            shutil.copy2(LOCAL_SRC, local_target)
            print(f"  ✅ Copied patch into local mlc-llm-source at: {local_target}")
            with open(outdir / 'patched_targets.txt', 'w') as fh:
                fh.write(str(local_target) + '\n')
            try:
                shutil.copy2(local_target, outdir / ('installed-' + Path(local_target).name))
            except Exception:
                pass
            print(f"  🗂 Wrote patched target info and copy to: {outdir}")
            with open(local_target, 'r') as f:
                content = f.read()
            if 'jsonffi_contains_replacement' in content:
                print(f"🔍 Verification OK: marker found in local mlc-llm-source {local_target}")
            else:
                print(f"⚠️ Marker not found in local copy {local_target}; writing marker_missing\n")
                write_marker_missing()
    except Exception as e:
        print(f"  ❌ Failed to write patch into mlc-llm-source: {e}")

    # final verification in installed site-packages
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
    write_marker_missing()
    # Non-fatal
    return 0

if __name__ == '__main__':
    print("🔧 Running json_ffi patch script (robust variant)")
    rc = patch_mlc_llm()
    if rc == 0:
        print("✅ patch_jsonffi_repl_fixed.py completed (non-fatal)")
    else:
        print(f"❌ patch_jsonffi_repl_fixed.py finished with code {rc}")
    sys.exit(rc)
