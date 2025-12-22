#!/usr/bin/env bash
set -euo pipefail
TARGET="$1"
LOG="$2"

if [ ! -f "$TARGET" ]; then
  echo "Target $TARGET does not exist; skipping marker append" >> "$LOG" || true
  exit 0
fi

if grep -q "MLCJSONFFIEngineForceLink_v1" "$TARGET" >/dev/null 2>&1; then
  echo "Marker already present in $TARGET" >> "$LOG" || true
  exit 0
fi

cat >> "$TARGET" <<'EOF'

// Fallback: ensure a stable marker symbol is present so CI can verify builds
extern "C" {
__attribute__((used)) __attribute__((visibility("default")))
const char* MLCJSONFFIEngineForceLink = "MLCJSONFFIEngineForceLink_v1";
}
EOF

echo "Appended force-link marker to $TARGET" >> "$LOG" || true
exit 0
