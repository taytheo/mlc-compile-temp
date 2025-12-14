#!/usr/bin/env python3
"""
Fallback helper to compile a GPU-only system lib for iPhone using mlc_llm
This is a Python replacement for the previous inline bash heredoc used in the GitHub workflow.
Usage: compile_gpu_lib_only_fallback.py <model_dir> <out_tar> <system_lib_prefix>

The script:
- validates inputs
- finds mlc-chat-config.json under model_dir
- runs `mlc_llm compile` with GPU-friendly overrides
- writes `compile_iphone_libonly_log.txt` in cwd
- extracts the produced tar and reports presence/size of devc.o and lib0.o

Exit codes:
- 0: script completed (compile may succeed or produce missing objects; workflow will validate presence)
- 1: fatal configuration or compile invocation error
"""

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile


def find_config(model_dir):
    for root, dirs, files in os.walk(model_dir):
        if 'mlc-chat-config.json' in files:
            return os.path.join(root, 'mlc-chat-config.json')
        # limit depth by not recursing too deep
        # We rely on model layouts to be shallow; if nested very deep, fallback to find via 'find' call
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_dir')
    parser.add_argument('out_tar')
    parser.add_argument('system_lib_prefix')
    args = parser.parse_args()

    model_dir = args.model_dir
    out_tar = args.out_tar
    sys_prefix = args.system_lib_prefix

    if not os.path.isdir(model_dir):
        print(f"ERROR: model_dir does not exist: {model_dir}", file=sys.stderr)
        sys.exit(1)

    config = find_config(model_dir)
    if not config:
        # try shell find
        try:
            res = subprocess.run(['find', model_dir, '-maxdepth', '2', '-type', 'f', '-name', 'mlc-chat-config.json', '-print', '-quit'], text=True, capture_output=True)
            found = res.stdout.strip()
            if found:
                config = found
        except Exception:
            config = None

    if not config:
        print(f"ERROR: mlc-chat-config.json not found under model dir: {model_dir}", file=sys.stderr)
        sys.exit(1)

    print("Found config:", config)
    out_dir = os.path.dirname(out_tar)
    os.makedirs(out_dir, exist_ok=True)

    overrides = "tensor_parallel_shards=1;context_window_size=1024;prefill_chunk_size=32;max_batch_size=1"

    # Invoke mlc_llm via the current python interpreter to avoid PATH/entrypoint issues
    cmd = [
        sys.executable, '-m', 'mlc_llm', 'compile',
        config,
        '--device', 'iphone',
        '--system-lib-prefix', sys_prefix,
        '--overrides', overrides,
        '--output', out_tar,
    ]

    print('Running:', ' '.join(cmd))

    # Run compile and capture output
    with open('compile_iphone_libonly_log.txt', 'w') as logf:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        logf.write(proc.stdout)
        # Always print the last part of the compile log for diagnostics
        tail = '\n'.join(proc.stdout.splitlines()[-200:])
        print("--- tail of compile log (last 200 lines) ---")
        print(tail)
        if proc.returncode != 0:
            print("ERROR: mlc_llm compile failed (non-zero exit). See compile_iphone_libonly_log.txt for full details", file=sys.stderr)
            sys.exit(1)

    if not os.path.isfile(out_tar):
        # Try to discover any .tar files in common output locations for debugging
        found = []
        for d in ['./output', '.']:
            try:
                for fname in os.listdir(d):
                    if fname.endswith('.tar'):
                        found.append(os.path.join(d, fname))
            except Exception:
                pass
        print(f"ERROR: Expected output tar not found at {out_tar}", file=sys.stderr)
        if found:
            print("But the following .tar files were found in common locations:")
            for f in found:
                print("  ", f)
        else:
            print("No .tar files were found in ./output or cwd; mlc_llm may have written elsewhere or failed silently.")
        # Also print mlc_llm version and PATH info for debugging
        try:
            v = subprocess.run(['mlc_llm', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            print('mlc_llm --version output:')
            print(v.stdout)
        except Exception:
            print('mlc_llm not found in PATH or --version failed')
        print('PATH=' + os.environ.get('PATH', ''))
        sys.exit(1)

    print("Compile finished. Checking output tar contents ...")
    try:
        with tarfile.open(out_tar, 'r:*') as tf:
            tf.list()
            tmp = tempfile.mkdtemp()
            tf.extractall(tmp)
            devc = os.path.join(tmp, 'devc.o')
            lib0 = os.path.join(tmp, 'lib0.o')
            if os.path.isfile(devc):
                print(f"devc.o found, size: {os.path.getsize(devc)} bytes")
            else:
                print("WARNING: devc.o not found in the tar")
            if os.path.isfile(lib0):
                print(f"lib0.o found, size: {os.path.getsize(lib0)} bytes")
            else:
                print("WARNING: lib0.o not found in the tar")
    except Exception as e:
        print(f"ERROR inspecting tar: {e}", file=sys.stderr)
        sys.exit(1)

    print('Done.')


if __name__ == '__main__':
    main()

