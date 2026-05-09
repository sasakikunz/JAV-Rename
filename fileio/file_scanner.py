from pathlib import Path


def scan_directory(directory, extensions=None):
    if extensions is None:
        extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.ts', '.m2ts', '.webm'}
    
    results = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise ValueError(f"目录不存在: {directory}")
    
    for item in dir_path.iterdir():
        if item.is_file() and item.suffix.lower() in extensions:
            results.append({
                'name': item.name,
                'type': 'file',
                'path': str(item.resolve())
            })
        elif item.is_dir():
            results.append({
                'name': item.name,
                'type': 'folder',
                'path': str(item.resolve())
            })
    
    return results


def get_files_from_directory(directory, extensions=None):
    if extensions is None:
        extensions = {'.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.ts', '.m2ts', '.webm'}
    
    files = []
    for p in Path(directory).iterdir():
        if p.is_file() and p.suffix.lower() in extensions:
            files.append(p.name)
    return files