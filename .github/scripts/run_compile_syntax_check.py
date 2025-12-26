#!/usr/bin/env python3
"""
Run a robust syntax-only check for json_ffi_engine.cc using build/compile_commands.json
Writes diagnostics to ${GITHUB_WORKSPACE:-$PWD}/tmp_ci_diagnostics/outputs/json_ffi_syntax_check.txt
Exits 0 always (non-fatal); writes rc and output to the diagnostics file.
"""
import json
import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / 'tmp_ci_diagnostics' / 'outputs' / 'json_ffi_syntax_check.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

def write(msg: str):
    with open(OUT, 'a') as f:
        f.write(msg + "\n")
    print(msg)

cc = Path('build') / 'compile_commands.json'
if not cc.exists():
    write(f"compile_commands.json not found at {cc}; skipping exact syntax check")
    raise SystemExit(0)

with open(cc, 'r') as f:
    try:
        cmds = json.load(f)
    except Exception as e:
        write(f"Failed to load compile_commands.json: {e}")
        raise SystemExit(0)

found = False
for entry in cmds:
    fn = entry.get('file','')
    if fn.endswith('cpp/json_ffi/json_ffi_engine.cc') or fn.endswith('cpp\\json_ffi\\json_ffi_engine.cc'):
        found = True
        # Prefer arguments if available
        cmd = entry.get('command')
        if cmd:
            args = shlex.split(cmd)
        else:
            args = entry.get('arguments', [])
        # Transform args: replace -c SOURCE or -c and source with -fsyntax-only -x c++ SOURCE
        out_args = []
        i = 0
        while i < len(args):
            a = args[i]
            if a == '-c' and i+1 < len(args):
                # skip '-c' and keep source but change flags
                src = args[i+1]
                out_args.extend(['-fsyntax-only','-x','c++', src])
                i += 2
                continue
            if a.startswith('-c') and len(a) > 2:
                # like -csource.c
                src = a[2:]
                out_args.extend(['-fsyntax-only','-x','c++', src])
                i += 1
                continue
            if a == '-o' and i+1 < len(args):
                # drop output file
                i += 2
                continue
            # drop any -ooutput form
            if a.startswith('-o') and len(a) > 2:
                i += 1
                continue
            out_args.append(a)
            i += 1
        # ensure we specify language and syntax-only if not already
        if '-fsyntax-only' not in out_args:
            out_args.insert(0, '-fsyntax-only')
            out_args.insert(1, '-x')
            out_args.insert(2, 'c++')
        write(f"Running syntax check command: {' '.join(shlex.quote(x) for x in out_args)}")
        try:
            proc = subprocess.run(out_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            write("--- syntax-check output start ---")
            for line in proc.stdout.splitlines():
                write(line)
            write(f"syntax-check rc: {proc.returncode}")
            with open(REPO_ROOT / 'tmp_ci_diagnostics' / 'outputs' / 'json_ffi_syntax_rc.txt', 'w') as fh:
                fh.write(str(proc.returncode))
            # Don't fail the job; caller will inspect json_ffi_syntax_rc.txt or logs
        except Exception as e:
            write(f"syntax check execution failed: {e}")
        break

if not found:
    write("No compile_commands entry for json_ffi_engine.cc found; skipping exact syntax check")

raise SystemExit(0)
