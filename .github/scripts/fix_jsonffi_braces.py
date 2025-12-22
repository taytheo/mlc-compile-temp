#!/usr/bin/env python3
"""
Attempt to repair unbalanced braces in json_ffi_engine.cc by counting braces
after removing string literals and comments. This is a conservative, best-effort
repair: if there are more unclosed '{' than '}', it appends closing braces at the end
and records a backup in tmp_patched_jsonffi.
"""
import re
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / 'mlc-llm-source' / 'cpp' / 'json_ffi' / 'json_ffi_engine.cc'
OUT_DIR = REPO_ROOT / 'tmp_patched_jsonffi'
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not SRC.exists():
    print(f"Source file not found: {SRC}")
    sys.exit(0)

text = SRC.read_text(encoding='utf-8', errors='replace')
# remove // comments
no_line_comments = re.sub(r'//.*', '', text)
# remove /* */ comments
no_block_comments = re.sub(r'/\*.*?\*/', '', no_line_comments, flags=re.DOTALL)
# remove string literals (basic)
no_strings = re.sub(r'"(?:\\.|[^"\\])*"', '""', no_block_comments)
# count braces
opens = no_strings.count('{')
closes = no_strings.count('}')
print(f"Brace counts: opens={opens} closes={closes}")
if opens <= closes:
    print("Braces appear balanced or too many closing braces; nothing to do.")
    sys.exit(0)
missing = opens - closes
print(f"Detected {missing} missing closing brace(s); appending to {SRC}")
# backup
bak = OUT_DIR / (SRC.name + '.bak')
SRC.replace(SRC)  # noop to ensure path exists
SRC.write_text(text, encoding='utf-8')
# write backup copy
with open(bak, 'w', encoding='utf-8') as f:
    f.write(text)
# append closing braces with comment
append_lines = '\n' + ('}' + '\n') * missing
with open(SRC, 'a', encoding='utf-8') as f:
    f.write('\n// Appended by fix_jsonffi_braces.py to close unbalanced namespaces\n')
    f.write(append_lines)
print(f"Appended {missing} closing brace(s) to {SRC}; backup at {bak}")
# write marker file
with open(OUT_DIR / 'brace_fix_applied.txt', 'w') as f:
    f.write(str(missing))

sys.exit(0)
