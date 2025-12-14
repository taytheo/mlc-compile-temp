#!/usr/bin/env bash
set -euo pipefail

# Wrapper variant for the GitHub-side helper that ensures we invoke mlc_llm via
# the active Python interpreter to avoid CLI path issues in CI environments.

MODEL_DIR=${1:-}
OUT_TAR=${2:-}
SYS_LIB_PREFIX=${3:-auto}
REQUESTED_SHARDS=${4:-}

if [ -z "$MODEL_DIR" ] || [ -z "$OUT_TAR" ]; then
  echo "Usage: $0 /abs/path/to/model_dir /abs/path/to/output/tar [system_lib_prefix]" >&2
  exit 1
fi

if [ ! -d "$MODEL_DIR" ]; then
  echo "Model directory does not exist: $MODEL_DIR" >&2
  exit 1
fi

CONFIG=$(find "$MODEL_DIR" -maxdepth 2 -type f -name "mlc-chat-config.json" -print -quit || true)
if [ -z "$CONFIG" ]; then
  echo "ERROR: mlc-chat-config.json not found under model dir: $MODEL_DIR" >&2
  exit 1
fi

echo "Found config: $CONFIG"
mkdir -p "$(dirname "$OUT_TAR")"

echo "Compiling GPU-only system library for iPhone (Metal) ..."
echo " - model_dir: $MODEL_DIR"
echo " - out_tar: $OUT_TAR"
echo " - system_lib_prefix: $SYS_LIB_PREFIX"

if [ -n "$REQUESTED_SHARDS" ]; then
  echo "Using requested tensor_parallel_shards=$REQUESTED_SHARDS"
  OVERRIDES="tensor_parallel_shards=${REQUESTED_SHARDS};context_window_size=1024;prefill_chunk_size=32;max_batch_size=1"
else
  OVERRIDES="tensor_parallel_shards=1;context_window_size=1024;prefill_chunk_size=32;max_batch_size=1"
fi

echo "Running mlc_llm compile (via python -m mlc_llm)"
python -m mlc_llm compile "$CONFIG" \
  --device iphone \
  --host arm64-apple-ios \
  --system-lib-prefix "$SYS_LIB_PREFIX" \
  --overrides "$OVERRIDES" \
  --output "$OUT_TAR" 2>&1 | tee compile_iphone_libonly_log.txt || {
    echo "ERROR: mlc_llm compile failed. See compile_iphone_libonly_log.txt" >&2
    exit 1
  }

echo "Compile finished. Checking output tar contents ..."
tar -tf "$OUT_TAR" | sed -n '1,200p'

TMPDIR=$(mktemp -d)
tar -xvf "$OUT_TAR" -C "$TMPDIR"
if [ -f "$TMPDIR/devc.o" ]; then
  echo "devc.o found, size: $(stat -f%z "$TMPDIR/devc.o") bytes"
else
  echo "devc.o not found in the tar"
fi

if [ -f "$TMPDIR/lib0.o" ]; then
  echo "lib0.o found, size: $(stat -f%z "$TMPDIR/lib0.o") bytes"
else
  echo "lib0.o not found in the tar"
fi

rm -rf "$TMPDIR"
echo "Done."
