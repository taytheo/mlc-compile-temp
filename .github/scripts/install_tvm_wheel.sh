#!/usr/bin/env bash
set -euo pipefail
LOG="$1"

echo "--- install_tvm_wheel.sh: attempting to install tvm wheels ---" >> "$LOG" || true
# Try common PyPI names
for pkg in tvm apache-tvm; do
  echo "Trying pip install $pkg" >> "$LOG" || true
  if pip install -U "$pkg" >> "$LOG" 2>&1; then
    echo "Installed $pkg from PyPI" >> "$LOG" || true
    exit 0
  else
    echo "pip install $pkg failed, continuing" >> "$LOG" || true
  fi
done

# Try custom wheel index (mlc.ai) which may host prebuilt macOS wheels
echo "Trying pip install --pre -f https://mlc.ai/wheels tvm" >> "$LOG" || true
if pip install --pre -U -f https://mlc.ai/wheels tvm >> "$LOG" 2>&1; then
  echo "Installed tvm from mlc.ai wheels" >> "$LOG" || true
  exit 0
else
  echo "mlc.ai wheel install failed" >> "$LOG" || true
fi

# Last resort: try to build minimal tvm wheel from the submodule if present
if [ -d mlc-llm-source/3rdparty/tvm/python ]; then
  echo "Attempting editable install from mlc-llm-source/3rdparty/tvm/python" >> "$LOG" || true
  if pip install -e ./mlc-llm-source/3rdparty/tvm/python >> "$LOG" 2>&1; then
    echo "Installed local TVM python from submodule" >> "$LOG" || true
    exit 0
  else
    echo "Editable install of TVM from submodule failed" >> "$LOG" || true
  fi
fi

echo "All TVM install attempts failed; TVM may still be present in system site-packages or CI may proceed with fallbacks." >> "$LOG" || true
exit 1
