#!/usr/bin/env bash
set -euo pipefail

# CI diagnostics: scan logs, debug-dump, and tmp dirs for jsonffi markers
mkdir -p tmp_ci_diagnostics/objects tmp_ci_diagnostics/snippets tmp_ci_diagnostics/sources

echo "Searching compile_log.txt and tmp_debug_dump for markers..."
if [ -f compile_log.txt ]; then
  grep -n --color=never -E "MLCJSONFFIEngineForceLink_v1|jsonffi_contains_replacement|json_ffi_engine.cc" compile_log.txt || true > tmp_ci_diagnostics/compile_grep.txt
fi
if [ -d tmp_debug_dump ]; then
  grep -R -n --color=never -E "MLCJSONFFIEngineForceLink_v1|jsonffi_contains_replacement|json_ffi_engine.cc" tmp_debug_dump || true >> tmp_ci_diagnostics/compile_grep.txt
fi

echo "Searching /tmp and ~/.cache for object files containing marker..."
# Limit depth to avoid scanning too much; this is best-effort
find /tmp ~/.cache -type f -name '*.o' -print 2>/dev/null || true | while read -r f; do
  if strings "$f" | egrep -i "MLCJSONFFIEngineForceLink_v1|jsonffi_contains_replacement" >/dev/null; then
    echo "FOUND marker in $f"
    mkdir -p tmp_ci_diagnostics/objects tmp_ci_diagnostics/snippets
    cp "$f" tmp_ci_diagnostics/objects/ || true
    strings "$f" | egrep -i "MLCJSONFFIEngineForceLink_v1|jsonffi_contains_replacement" -n > "tmp_ci_diagnostics/snippets/$(basename "$f").txt" || true
  fi
done || true

# Also copy any found_objs.txt or known output artifacts for context
for p in output found_objs.txt tmp_patched_jsonffi compile_log.txt; do
  if [ -e "$p" ]; then
    mkdir -p tmp_ci_diagnostics/outputs
    cp -R "$p" tmp_ci_diagnostics/outputs/ || true
  fi
done

# If there are object files in the workspace output dir, capture snippet context
if [ -d output ]; then
  find output -type f -name '*.o' -print | while read -r f; do
    strings "$f" | egrep -i "MLCJSONFFIEngineForceLink_v1|jsonffi_contains_replacement" -n > "tmp_ci_diagnostics/snippets/$(basename "$f").txt" || true
  done
fi
echo "Searching workspace for json_ffi_engine.cc and copying candidates..."
find . -type f -name 'json_ffi_engine.cc' -print | while read -r p; do
  dest="tmp_ci_diagnostics/sources/$(echo "$p" | sed 's#/#_##g' | sed 's#^\.##')"
  mkdir -p "$(dirname "$dest")"
  cp "$p" "$dest" || true
done || true

echo "Listing diagnostics dir..."
ls -la tmp_ci_diagnostics || true
