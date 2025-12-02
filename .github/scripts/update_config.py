#!/usr/bin/env python3
import json
import os

def main():
    config_path = './model_weights/Qwen3-4B-q4f16_1-MLC/mlc-chat-config.json'
    
    # Backup original config
    if os.path.exists(config_path):
        import shutil
        shutil.copy2(config_path, config_path + '.bak')
        print(f"Backup created: {config_path}.bak")
    
    # Load and update config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update configuration
    config['prefill_chunk_size'] = 128
    config['context_window_size'] = 4096
    config['model_config']['prefill_chunk_size'] = 128
    config['model_config']['context_window_size'] = 4096
    config['model_config']['max_batch_size'] = 1
    config['model_config']['dtype'] = 'float16'
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print('Config updated:')
    print(f'  prefill_chunk_size: {config["prefill_chunk_size"]}')
    print(f'  context_window_size: {config["context_window_size"]}')
    print(f'  max_batch_size: {config["model_config"]["max_batch_size"]}')
    print(f'  dtype: {config["model_config"]["dtype"]}')

if __name__ == "__main__":
    main()
