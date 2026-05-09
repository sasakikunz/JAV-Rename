#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影片番号规范化工具 v4.0
功能：
1. 规则学习 - 从Excel文件学习影片前缀规则并缓存
2. 文件名规范化 - 扫描目录下文件和文件夹，生成规范化Excel
3. Excel规范化 - 读取Excel中的文件名，规范化后填入第二列
4. 文件匹配 - 将规范化名称与电影目录模糊匹配
5. 批量重命名 - 根据Excel进行实际重命名
"""

import sys

from cli.commands import build_parser, learn_command, normalize_command, normalize_excel_command, match_command, rename_command, rename_enhanced_command


def main():
    parser = build_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    if args.command == 'learn':
        learn_command(args)
    elif args.command == 'normalize':
        normalize_command(args)
    elif args.command == 'normalize-excel':
        normalize_excel_command(args)
    elif args.command == 'match':
        match_command(args)
    elif args.command == 'rename':
        rename_command(args)
    elif args.command == 'rename-enhanced':
        rename_enhanced_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()