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
    
    # 기본 설정
    config['prefill_chunk_size'] = 128
    config['context_window_size'] = 4096
    
    # 모델 설정
    if 'model_config' not in config:
        config['model_config'] = {}
    
    config['model_config']['prefill_chunk_size'] = 128
    config['model_config']['context_window_size'] = 4096
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
