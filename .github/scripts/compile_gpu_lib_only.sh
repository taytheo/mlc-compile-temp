#!/usr/bin/env bash
set -euo pipefail

# Compile a GPU (Metal) system library (lib0.o + devc.o) for iPhone that relies
# on the existing shard files in the model directory (so we keep current params_shard_*.bin).
#
# Usage:
#   ./compile_gpu_lib_only.sh /abs/path/to/model_dir /abs/path/to/output/qwen3_q4f16_1-iphone-libonly.tar [system_lib_prefix]
#
# Example:
#   ./compile_gpu_lib_only.sh /Users/user/god_ai/Qwen3_MLC_4bit ./output/qwen3_q4f16_1-iphone-libonly.tar qwen3_q4f16_1

MODEL_DIR=${1:-}
OUT_TAR=${2:-}
SYS_LIB_PREFIX=${3:-auto}
REQUESTED_SHARDS=${4:-}

if [ -z "$MODEL_DIR" ] || [ -z "$OUT_TAR" ]; then
  echo "Usage: $0 /abs/path/to/model_dir /abs/path/to/output/tar [system_lib_prefix]"
  exit 1
fi

if [ ! -d "$MODEL_DIR" ]; then
  echo "Model directory does not exist: $MODEL_DIR" >&2
  exit 1
fi

# Find config
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
echo " - Strict mmap with shards: Ensure TVM_USE_MMAP_CACHE=1 when running the app to use params_shard_* files"

# We pass some overrides to keep memory footprint modest and generate a library
# If a requested shard count is supplied as the 4th argument, honor it so the compile
# will favor shard-based (mmap) outputs and reduce embedded memory usage.
if [ -n "$REQUESTED_SHARDS" ]; then
  echo "Using requested tensor_parallel_shards=$REQUESTED_SHARDS"
  OVERRIDES="tensor_parallel_shards=${REQUESTED_SHARDS};context_window_size=1024;prefill_chunk_size=32;max_batch_size=1"
else
  # default conservative values for iPhone GPU
  OVERRIDES="tensor_parallel_shards=1;context_window_size=1024;prefill_chunk_size=32;max_batch_size=1"
fi

echo "Running mlc_llm compile (this will produce a tar, typically containing lib0.o and devc.o)
"
mlc_llm compile "$CONFIG" \
  --device iphone \
  --host arm64-apple-ios \
  --system-lib-prefix "$SYS_LIB_PREFIX" \
  --overrides "$OVERRIDES" \
  --output "$OUT_TAR" 2>&1 | tee compile_iphone_libonly_log.txt

echo "Compile finished. Checking output tar contents ..."
tar -tf "$OUT_TAR" | sed -n '1,200p'

echo "Attempt to check for lib files and Metal kernels inside devc.o ..."
TMPDIR=$(mktemp -d)
tar -xvf "$OUT_TAR" -C "$TMPDIR"
if [ -f "$TMPDIR/devc.o" ]; then
  echo "devc.o found, size: $(stat -f%z "$TMPDIR/devc.o") bytes"
  # Quick metal string check to show if metal kernels compiled in (best-effort)
  if strings "$TMPDIR/devc.o" | grep -iE 'metal|metallib|MTLDevice|NT_matmul' >/dev/null 2>&1; then
    echo "devc.o contains likely Metal-related symbols/strings"
  else
    echo "devc.o does not seem to contain explicit Metal strings (this may be ok if kernels are JIT or stripped), but compiled device target was iphone"
  fi
else
  echo "devc.o not found in the tar — compile may have produced a different artifact layout"
fi

if [ -f "$TMPDIR/lib0.o" ]; then
  echo "lib0.o found, size: $(stat -f%z "$TMPDIR/lib0.o") bytes"
else
  echo "lib0.o not found in the tar — lib naming may be different or system_lib_prefix controls file name"
fi

echo "Cleaning up temporary extract dir"
rm -rf "$TMPDIR"

echo "If you want to integrate into the iOS Runner, run:"
echo " EXTRACT_FOR_RUNNER=1 SKIP_BUILD=0 RUN_XCODEBUILD=1 ./ios/scripts/integrate_compiled_model.sh $(pwd)/$(dirname "$OUT_TAR")"

echo "Done. Check compile_iphone_libonly_log.txt for details" 
