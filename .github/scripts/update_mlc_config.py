#!/usr/bin/env python3
"""
MLC 모델 설정 파일 업데이트 스크립트
iOS 메모리 최적화를 위한 버퍼 설정 적용
"""

import json
import sys

CONFIG_PATH = './model_weights/Qwen3-4B-q4f16_1-MLC/mlc-chat-config.json'

def main():
    print(f"📄 설정 파일 로드: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    # iOS 메모리 최적화 설정 (iPhone 6GB GPU 메모리 타겟)
    # 기존: prefill_chunk_size=128, context=4096 → 버퍼 2.8GB (너무 큼)
    # 변경: prefill_chunk_size=32, context=1024 → 버퍼 ~700MB (적합)
    config['prefill_chunk_size'] = 32
    config['context_window_size'] = 1024
    
    # 모델 설정
    if 'model_config' not in config:
        config['model_config'] = {}
    
    config['model_config']['prefill_chunk_size'] = 32
    config['model_config']['context_window_size'] = 1024
    config['model_config']['max_batch_size'] = 1
    config['model_config']['dtype'] = 'float16'
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ 설정 업데이트 완료:")
    print(f"   prefill_chunk_size: {config['prefill_chunk_size']}")
    print(f"   context_window_size: {config['context_window_size']}")
    print(f"   max_batch_size: {config['model_config']['max_batch_size']}")
    print(f"   dtype: {config['model_config']['dtype']}")

if __name__ == '__main__':
    main()
