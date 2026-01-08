#!/usr/bin/env python3
"""
Update mlc-chat-config.json for GPU-only (iPhone / Metal) compilation.

This script mirrors the CPU config script but applies GPU-friendly defaults.
By default it targets './model_weights/Qwen3-4B-q4f16_1-MLC/mlc-chat-config.json'.
A path may be supplied as the first argument.

Defaults used:
  - tensor_parallel_shards = 1
  - prefill_chunk_size = 128  (GPU can prefill a larger chunk than CPU)
  - context_window_size = 4096 (a moderate GPU context size)
  - max_batch_size = 1
  - dtype = 'float16'

Note: These values are conservative for iPhone GPU. If you target a higher-memory device
or a simulator with more memory, you can increase the values accordingly.
"""

import json
import sys
import os

DEFAULT_CONFIG_PATH = './model_weights/Qwen3-4B-q4f16_1-MLC/mlc-chat-config.json'


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH

    if not os.path.exists(cfg_path):
        print(f"ERROR: Cannot find config at: {cfg_path}")
        sys.exit(1)

    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {cfg_path}: {e}")
        sys.exit(1)

    cfg.setdefault('model_config', {})

    # GPU-friendly defaults optimized for iPhone Metal with ~74 shards (load ~37 at once)
    # Use shard=1 for compile (model already has 74 weight shards)
    # mmap will load shards dynamically at runtime
    cfg['model_config'].setdefault('tensor_parallel_shards', 1)
    cfg['model_config'].setdefault('prefill_chunk_size', 32)  # Reduced for memory efficiency
    cfg['model_config'].setdefault('context_window_size', 1024)  # Reduced for memory efficiency
    cfg['model_config'].setdefault('max_batch_size', 1)
    cfg['model_config'].setdefault('dtype', 'float16')

    # Optionally set a GPU-preferred device (some compile flows accept this), but don't override
    # if already present.
    if 'device' not in cfg or not cfg['device']:
        cfg['device'] = cfg.get('device', 'metal')

    # Persist changes
    try:
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to write updated config: {e}")
        sys.exit(1)

    print('✅ Updated mlc-chat-config.json for GPU compile (metal)')
    print('  - tensor_parallel_shards:', cfg['model_config'].get('tensor_parallel_shards'))
    print('  - prefill_chunk_size:', cfg['model_config'].get('prefill_chunk_size'))
    print('  - context_window_size:', cfg['model_config'].get('context_window_size'))
    print('  - max_batch_size:', cfg['model_config'].get('max_batch_size'))
    print('  - dtype:', cfg['model_config'].get('dtype'))
    print('  - device:', cfg.get('device'))


if __name__ == '__main__':
    main()
