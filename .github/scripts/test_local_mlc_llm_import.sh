#!/usr/bin/env bash
set -euo pipefail

echo "Listing mlc-llm-source directory tree (top 4 levels)"
if [ -d mlc-llm-source ]; then
  find mlc-llm-source -maxdepth 4 -type f -print | sed -n '1,200p' || true
else
  echo "mlc-llm-source not present"
fi

echo "-- Trying to import mlc_llm with various PYTHONPATHs --"
PY_VARIANTS=( "." "./mlc-llm-source" "./mlc-llm-source/src" "./mlc-llm-source/python" "./mlc-llm-source/python/src" "./mlc-llm-source/src/python" )
IMPORT_OK=0
for p in "${PY_VARIANTS[@]}"; do
  echo "Testing PYTHONPATH=$p"
  PYTHONPATH="$p" python - <<'PY' || true
import importlib
try:
    m = importlib.import_module('mlc_llm')
    print('OK:', getattr(m, '__file__', 'no-file'))
except Exception as e:
    print('FAIL:', e)
PY
  if PYTHONPATH="$p" python - <<'PY'
import importlib
try:
    importlib.import_module('mlc_llm')
    print('IMPORT_OK')
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
PY
  then
    IMPORT_OK=1
    echo "Import succeeded with PYTHONPATH=$p"
    break
  fi
done

# Verify patched file presence in mlc-llm-source
if [ -f mlc-llm-source/cpp/json_ffi/json_ffi_engine.cc ]; then
  echo "Patched file in mlc-llm-source present:"
  head -n 60 mlc-llm-source/cpp/json_ffi/json_ffi_engine.cc || true
  grep -n "MLCJSONFFIEngineForceLink_v1" mlc-llm-source/cpp/json_ffi/json_ffi_engine.cc || true
else
  echo "Patched file not found in mlc-llm-source (mlc-llm-source/cpp/json_ffi/json_ffi_engine.cc)"
fi

if [ "$IMPORT_OK" -eq 0 ]; then
  echo "ERROR: Could not import mlc_llm from local source using tried PYTHONPATH variants; aborting"
  exit 1
fi

echo "Import test passed; proceeding to compile with local source if available."

# Ensure helper deps still installed
pip install huggingface_hub || true
pip show mlc-llm || true
