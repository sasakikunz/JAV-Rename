import json
import os


class CacheManager:
    def __init__(self, cache_file='prefix_cache.json'):
        self.cache_file = cache_file
        self.prefixes = set()
    
    def load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.prefixes = set(json.load(f))
                print(f"已加载缓存: {self.cache_file} (共 {len(self.prefixes)} 个前缀)")
            except Exception as e:
                print(f"警告：加载缓存失败 ({e})")
        return self.prefixes
    
    def save(self, prefixes):
        self.prefixes = set(prefixes)
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(sorted(list(self.prefixes)), f, ensure_ascii=False, indent=2)
            print(f"缓存已保存至: {self.cache_file} (共 {len(self.prefixes)} 个前缀)")
        except Exception as e:
            print(f"警告：保存缓存失败 ({e})")
    
    def clear(self):
        self.prefixes = set()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print(f"缓存已清除: {self.cache_file}")
    
    def add_prefix(self, prefix):
        self.prefixes.add(prefix.upper())
    
    def has_prefix(self, prefix):
        return prefix.upper() in self.prefixes