#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import datetime
import shutil

from core.normalizer import MovieNormalizer
from core.matcher import FuzzyMatcher
from fileio.excel_reader import read_excel_mapping, read_normalized_excel, read_movie_list, read_single_column
from fileio.excel_writer import write_normalized_results, write_matched_results, write_single_column_normalize
from fileio.file_scanner import scan_directory


def learn_command(args):
    print(f"正在从 {args.excel} 学习规则...")
    pairs = read_excel_mapping(args.excel)
    normalizer = MovieNormalizer(cache_file=args.cache, example_pairs=pairs)
    print(f"学习完成，共学习 {len(normalizer.known_prefixes)} 个前缀规则")


def normalize_command(args):
    folder = args.folder
    output = args.output
    
    if not os.path.isdir(folder):
        print(f"错误：文件夹 {folder} 不存在")
        return
    
    normalizer = MovieNormalizer(cache_file=args.cache)
    items = scan_directory(folder)
    
    print(f"找到 {len(items)} 个项目（文件和文件夹）")
    
    results = []
    for item in items:
        normalized = normalizer.extract_normalized_id(item['name'])
        results.append({
            '原名称': item['name'],
            '规范名称': normalized,
            '类型': item['type'],
            '路径': item['path']
        })
    
    if not output:
        base = os.path.basename(folder)
        output = f"{base}_normalized.xlsx"
    
    write_normalized_results(results, output)


def normalize_excel_command(args):
    input_file = args.input
    output = args.output
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return
    
    normalizer = MovieNormalizer(cache_file=args.cache)
    filenames = read_single_column(input_file)
    
    print(f"读取到 {len(filenames)} 个文件名")
    
    normalized_names = []
    for filename in filenames:
        if filename:
            normalized = normalizer.extract_normalized_id(filename)
        else:
            normalized = ""
        normalized_names.append(normalized)
    
    if not output:
        base, ext = os.path.splitext(input_file)
        output = f"{base}_normalized{ext}"
    
    write_single_column_normalize(input_file, normalized_names, output)


def match_command(args):
    input_file = args.input
    movie_list_file = args.movie_list
    output = args.output
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return
    
    if not os.path.exists(movie_list_file):
        print(f"错误：电影目录文件 {movie_list_file} 不存在")
        return
    
    normalized_data = read_normalized_excel(input_file)
    movie_list = read_movie_list(movie_list_file)
    
    matcher = FuzzyMatcher(movie_list, threshold=args.threshold)
    
    results = []
    for item in normalized_data:
        match_name, score = matcher.match(item['normalized'])
        results.append({
            '原名称': item['original'],
            '规范名称': item['normalized'],
            '匹配名称': match_name if match_name else '',
            '匹配度': round(score, 4)
        })
    
    if not output:
        base, ext = os.path.splitext(input_file)
        output = f"{base}_matched{ext}"
    
    write_matched_results(results, output)


def rename_command(args):
    folder = args.folder
    input_file = args.input
    
    if not os.path.isdir(folder):
        print(f"错误：文件夹 {folder} 不存在")
        return
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return
    
    normalized_data = read_normalized_excel(input_file)
    
    print(f"{'预览模式' if args.dry_run else '执行模式'}: 准备重命名 {len(normalized_data)} 个项目")
    
    results = []
    for item in normalized_data:
        original = item['original']
        normalized = item['normalized']
        file_type = item.get('type', 'file')
        
        if original == normalized:
            results.append({
                '原名称': original,
                '新名称': normalized,
                '状态': '跳过（名称相同）'
            })
            continue
        
        if file_type == 'file':
            _, ext = os.path.splitext(original)
            if ext and not normalized.lower().endswith(ext.lower()):
                normalized = normalized + ext
        
        old_path = os.path.join(folder, original)
        new_path = os.path.join(folder, normalized)
        
        if not os.path.exists(old_path):
            results.append({
                '原名称': original,
                '新名称': normalized,
                '状态': '跳过（源文件不存在）'
            })
            continue
        
        if os.path.exists(new_path):
            results.append({
                '原名称': original,
                '新名称': normalized,
                '状态': '跳过（目标已存在）'
            })
            continue
        
        if args.dry_run:
            print(f"  {original} -> {normalized}")
            results.append({
                '原名称': original,
                '新名称': normalized,
                '状态': '预览'
            })
        else:
            try:
                os.rename(old_path, new_path)
                print(f"  {original} -> {normalized}")
                results.append({
                    '原名称': original,
                    '新名称': normalized,
                    '状态': '成功'
                })
            except Exception as e:
                print(f"  {original} -> {normalized} [失败: {e}]")
                results.append({
                    '原名称': original,
                    '新名称': normalized,
                    '状态': f'失败: {e}'
                })
    
    if args.output:
        output_path = args.output
        if os.path.isdir(output_path):
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(output_path, f'rename_result_{timestamp}.xlsx')
        write_matched_results(results, output_path)
    
    if args.dry_run:
        print("\n以上为预览结果，未实际执行重命名")
    else:
        print("\n重命名完成")


def rename_enhanced_command(args):
    root = args.folder
    output = args.output
    remove_mode = args.remove
    
    if not os.path.isdir(root):
        print(f"错误：文件夹 {root} 不存在")
        return
    
    log_entries = []
    
    def log(original, new_name, status):
        entry = {
            '时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '原名称': original,
            '新名称': new_name,
            '状态': status
        }
        log_entries.append(entry)
        return entry
    
    def get_item_size(item_path):
        try:
            if os.path.isfile(item_path):
                return os.path.getsize(item_path)
            return 0
        except (OSError, PermissionError):
            return 0
    
    def delete_unrenamed(scan_dir, renamed_name):
        remaining = []
        try:
            for name in os.listdir(scan_dir):
                if name == renamed_name:
                    continue
                remaining.append(name)
        except PermissionError:
            return
        
        if not remaining:
            return
        
        remaining.sort()
        print(f"\n    以下项目未被重命名，将被删除:")
        for name in remaining:
            full_path = os.path.join(scan_dir, name)
            if os.path.isdir(full_path):
                print(f"      {name}  [文件夹]")
            else:
                size = get_item_size(full_path)
                size_str = f" ({size/1024/1024:.1f}MB)" if size > 1024*1024 else f" ({size/1024:.1f}KB)" if size > 0 else ""
                print(f"      {name}{size_str}")
        
        while True:
            confirm = input(f"\n    确认删除以上 {len(remaining)} 个项目？(y/n): ").strip().lower()
            if confirm == 'y':
                for name in remaining:
                    full_path = os.path.join(scan_dir, name)
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                        print(f"      {name} [已删除]")
                        log(name, "", "已删除")
                    except Exception as e:
                        print(f"      {name} [删除失败: {e}]")
                        log(name, "", f"删除失败: {e}")
                break
            elif confirm == 'n':
                print(f"    取消删除，保留所有文件")
                break
            else:
                print("    请输入 y 或 n")
    
    def rename_to_parent(scan_dir, parent_name):
        items = []
        try:
            for name in os.listdir(scan_dir):
                items.append(name)
        except PermissionError:
            print(f"  权限不足，无法访问: {scan_dir}")
            return
        
        if not items:
            print(f"  (空文件夹)")
            return
        
        display_list = []
        for name in items:
            full_path = os.path.join(scan_dir, name)
            item_type = "文件夹" if os.path.isdir(full_path) else "文件"
            size = get_item_size(full_path)
            display_list.append((name, full_path, item_type, size))
        
        display_list.sort(key=lambda x: -x[3])
        
        print(f"\n  {'='*50}")
        print(f"  文件夹: {os.path.basename(scan_dir)}")
        print(f"  {'='*50}")
        
        for idx, (name, full_path, item_type, size) in enumerate(display_list, 1):
            if item_type == "文件":
                size_str = f" ({size/1024/1024:.1f}MB)" if size > 1024*1024 else f" ({size/1024:.1f}KB)" if size > 0 else ""
                print(f"    {idx}.{name}{size_str}")
            else:
                print(f"    {idx}.{name}  [文件夹]")
        
        if remove_mode:
            print(f"    {'-'*40}")
            print(f"    0.不修改（将删除所有未重命名的文件）")
        else:
            print(f"    {'-'*40}")
            print(f"    0.不修改")
        
        while True:
            try:
                user_input = input(f"\n  请输入需要重命名的项目编号(1-{len(display_list)})，输入0表示不修改: ").strip()
                
                if not user_input.isdigit():
                    print("  错误：请输入有效的数字编号")
                    continue
                
                choice = int(user_input)
                
                if choice == 0:
                    print(f"  跳过当前文件夹")
                    return
                
                if choice < 1 or choice > len(display_list):
                    print(f"  错误：编号必须在 1-{len(display_list)} 之间")
                    continue
                
                break
            except (ValueError, EOFError):
                print("  错误：输入无效，请重新输入")
                return
        
        selected = display_list[choice - 1]
        old_name, old_path, item_type, _ = selected
        
        name_part, ext = os.path.splitext(old_name)
        if item_type == "文件":
            new_name = parent_name + ext
        else:
            new_name = parent_name
        
        new_path = os.path.join(scan_dir, new_name)
        
        if old_name == new_name:
            msg = "跳过（名称相同）"
            print(f"    {old_name} -> {new_name} [{msg}]")
            log(old_name, new_name, msg)
            if remove_mode and item_type == "文件":
                delete_unrenamed(scan_dir, new_name)
            return
        
        if os.path.exists(new_path):
            msg = f"跳过（目标已存在）"
            print(f"    {old_name} -> {new_name} [{msg}]")
            log(old_name, new_name, msg)
            return
        
        try:
            os.rename(old_path, new_path)
            msg = "成功"
            print(f"    {old_name} -> {new_name} [{msg}]")
            log(old_name, new_name, msg)
            
            if remove_mode and item_type == "文件":
                delete_unrenamed(scan_dir, new_name)
            
            if item_type == "文件夹":
                rename_to_parent(new_path, parent_name)
        except Exception as e:
            msg = f"失败: {e}"
            print(f"    {old_name} -> {new_name} [{msg}]")
            log(old_name, new_name, msg)
    
    print("开始增强型批量重命名...")
    print(f"根目录: {root}")
    print()
    
    try:
        all_items = sorted(os.listdir(root))
    except PermissionError:
        print(f"权限不足: {root}")
        return
    
    subfolders = []
    for name in all_items:
        full_path = os.path.join(root, name)
        if os.path.isdir(full_path):
            subfolders.append(name)
    
    if not subfolders:
        print("根目录下没有子文件夹")
        return
    
    for folder_name in subfolders:
        folder_path = os.path.join(root, folder_name)
        rename_to_parent(folder_path, folder_name)
    
    print(f"\n{'='*60}")
    print(f"全部处理完成，共 {len(log_entries)} 条操作记录")
    
    if not output:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f'rename_enhanced_log_{timestamp}.log'
    elif os.path.isdir(output):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output = os.path.join(output, f'rename_enhanced_log_{timestamp}.log')
    
    if output.lower().endswith('.log'):
        with open(output, 'w', encoding='utf-8-sig') as f:
            for entry in log_entries:
                f.write(f"[{entry['时间']}] {entry['原名称']} -> {entry['新名称']} ({entry['状态']})\n")
        print(f"日志已保存至: {output}")
    else:
        try:
            import openpyxl
            if not output.lower().endswith('.xlsx'):
                output += '.xlsx'
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "重命名日志"
            ws.append(['时间', '原名称', '新名称', '状态'])
            for entry in log_entries:
                ws.append([entry['时间'], entry['原名称'], entry['新名称'], entry['状态']])
            wb.save(output)
            print(f"日志已保存至: {output}")
        except ImportError:
            log_path = output.replace('.xlsx', '.log') if output.endswith('.xlsx') else output + '.log'
            with open(log_path, 'w', encoding='utf-8-sig') as f:
                for entry in log_entries:
                    f.write(f"[{entry['时间']}] {entry['原名称']} -> {entry['新名称']} ({entry['状态']})\n")
            print(f"日志已保存至: {log_path}")


def build_parser():
    parser = argparse.ArgumentParser(description='影片番号规范化工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    learn_parser = subparsers.add_parser('learn', help='从Excel学习前缀规则（支持单列或两列）')
    learn_parser.add_argument('--excel', '-e', required=True, help='Excel文件路径（单列时直接从第一列提取前缀，两列时从第二列学习）')
    learn_parser.add_argument('--cache', '-c', default='prefix_cache.json', help='缓存文件路径')
    
    normalize_parser = subparsers.add_parser('normalize', help='规范化目录下文件名')
    normalize_parser.add_argument('--folder', '-d', required=True, help='要处理的文件夹路径')
    normalize_parser.add_argument('--output', '-o', help='输出Excel文件路径')
    normalize_parser.add_argument('--cache', '-c', default='prefix_cache.json', help='缓存文件路径')
    
    normalize_excel_parser = subparsers.add_parser('normalize-excel', help='规范化Excel中的文件名')
    normalize_excel_parser.add_argument('--input', '-i', required=True, help='包含文件名的Excel文件（单列）')
    normalize_excel_parser.add_argument('--output', '-o', help='输出Excel文件路径')
    normalize_excel_parser.add_argument('--cache', '-c', default='prefix_cache.json', help='缓存文件路径')
    
    match_parser = subparsers.add_parser('match', help='将规范化名称与电影目录匹配')
    match_parser.add_argument('--input', '-i', required=True, help='包含规范化名称的Excel文件')
    match_parser.add_argument('--movie-list', '-m', required=True, help='电影目录Excel文件')
    match_parser.add_argument('--output', '-o', help='输出匹配结果的Excel文件路径')
    match_parser.add_argument('--threshold', '-t', type=float, default=0.7, help='匹配相似度阈值')
    
    rename_parser = subparsers.add_parser('rename', help='批量重命名文件')
    rename_parser.add_argument('--folder', '-d', required=True, help='要重命名的文件夹路径')
    rename_parser.add_argument('--input', '-i', required=True, help='包含重命名映射的Excel文件')
    rename_parser.add_argument('--output', '-o', help='输出重命名结果的Excel文件路径')
    rename_parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际重命名')
    
    rename_enhanced_parser = subparsers.add_parser('rename-enhanced', help='增强型批量重命名（交互式）')
    rename_enhanced_parser.add_argument('--folder', '-d', required=True, help='根文件夹路径')
    rename_enhanced_parser.add_argument('--output', '-o', help='日志文件输出路径（支持.xlsx或.log）')
    rename_enhanced_parser.add_argument('--remove', '-r', action='store_true', help='删除模式：重命名后自动删除未被重命名的文件')
    
    return parser