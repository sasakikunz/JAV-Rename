import os
import json
from pathlib import Path


class Config:
    def __init__(self, config_file='config.yaml'):
        self.cache_file = 'prefix_cache.json'
        self.similarity_threshold = 0.7
        self.default_output_suffix = '_normalized'
        self.supported_extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.ts', '.m2ts', '.webm'}
        
        if os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'cache_file' in config:
                    self.cache_file = config['cache_file']
                if 'similarity_threshold' in config:
                    self.similarity_threshold = config['similarity_threshold']
                if 'default_output_suffix' in config:
                    self.default_output_suffix = config['default_output_suffix']
                if 'supported_extensions' in config:
                    self.supported_extensions = set(config['supported_extensions'])
        except Exception as e:
            print(f"警告：加载配置文件失败 ({e})")
    
    def save_to_file(self, config_file='config.yaml'):
        config = {
            'cache_file': self.cache_file,
            'similarity_threshold': self.similarity_threshold,
            'default_output_suffix': self.default_output_suffix,
            'supported_extensions': list(self.supported_extensions)
        }
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告：保存配置文件失败 ({e})")