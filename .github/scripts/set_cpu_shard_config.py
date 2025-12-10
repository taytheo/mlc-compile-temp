#!/usr/bin/env python3
"""
Update mlc-chat-config.json to enable CPU-only sharded compile for iOS
"""
import json
import sys

CONFIG_PATH = './model_weights/Qwen3-4B-q4f16_1-MLC/mlc-chat-config.json'

def main():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"ERROR: Cannot open {CONFIG_PATH}: {e}")
        sys.exit(1)

    cfg.setdefault('model_config', {})
    cfg['model_config'].setdefault('tensor_parallel_shards', 4)
    cfg['model_config'].setdefault('prefill_chunk_size', 32)
    cfg['model_config'].setdefault('context_window_size', 1024)
    cfg['model_config'].setdefault('max_batch_size', 1)

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

    print('✅ Updated mlc-chat-config.json for CPU-only + shard compile')

if __name__ == '__main__':
    main()
