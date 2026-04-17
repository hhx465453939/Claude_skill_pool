#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识典古籍智能搜索下载工具

核心思路：
1. 从本地映射搜索书名 → 获取 book_id
2. 用搜索引擎搜索 "书名 site:shidianguji.com /chapter/"
3. 提取章节 URL → 调用 fetch_book.py 下载
"""

import argparse
import json
import os
import sys
import re
import subprocess
from pathlib import Path

DEFAULT_MAPPING = os.path.join(os.path.dirname(__file__), "shidianguji_book_mapping.json")

def load_mapping(mapping_file):
    """加载书名-编号映射"""
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)

def search_book(query, mapping):
    """搜索书籍（支持模糊匹配）"""
    query = query.strip()
    results = []

    # 精确匹配
    for book in mapping:
        if book["title"] == query:
            return [book]

    # 模糊匹配
    for book in mapping:
        if query in book["title"]:
            results.append(book)

    return results

def search_chapter_url(book_title):
    """使用外部工具搜索章节 URL"""
    # 这里假设我们会通过外部搜索工具（如 zhipu-web-search-sse）搜索
    # 为了简化，我们构造一个搜索 URL，让用户复制到搜索引擎中
    search_query = f"{book_title} 识典古籍 site:shidianguji.com"

    print(f"\n请使用搜索引擎搜索：")
    print(f"  {search_query}")
    print(f"\n然后复制任意章节 URL 给我下载。")
    print(f"章节 URL 格式: https://www.shidianguji.com/book/XXX/chapter/YYY")
    print(f"\n或者手动访问书籍页面并复制章节链接。")

    # 返回书籍列表，方便用户查看 book_id
    return None

def download_book(chapter_url, title, output_dir="output"):
    """调用 fetch_book.py 下载书籍"""
    script_path = os.path.join(os.path.dirname(__file__), "fetch_book.py")

    cmd = [
        sys.executable,
        script_path,
        chapter_url,
        "--title", title,
        "--output", output_dir
    ]

    print(f"\nRunning: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser(
        description="识典古籍智能搜索下载工具",
        epilog="""示例:
  搜索书籍:
    python smart_search.py 韩非子
    python smart_search.py 论语

  查看所有书籍:
    python smart_search.py --index

  从章节 URL 下载:
    python smart_search.py --url "https://www.shidianguji.com/book/SBCK070/chapter/xxx" --title 韩非子
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("query", nargs="?", help="书名或关键词")
    ap.add_argument("--mapping", "-m", default=DEFAULT_MAPPING,
                   help=f"映射文件路径（默认: {DEFAULT_MAPPING}）")
    ap.add_argument("--output", "-o", default="output", help="输出目录（默认: output）")
    ap.add_argument("--index", action="store_true",
                   help="显示所有书籍的索引")
    ap.add_argument("--url", help="直接从章节 URL 下载")
    ap.add_argument("--title", help="书籍标题（配合 --url 使用）")
    ap.add_argument("--update", action="store_true",
                   help="更新映射文件（运行 crawl_library.py）")

    args = ap.parse_args()

    # 更新映射
    if args.update:
        print("Updating mapping...")
        crawl_script = os.path.join(os.path.dirname(__file__), "crawl_library.py")
        subprocess.run([sys.executable, crawl_script], check=True)
        return

    # 显示所有索引
    if args.index:
        mapping = load_mapping(args.mapping)
        print(f"\nTotal books: {len(mapping)}\n")
        print("格式: 序号. 书名 [编号]\t作者")
        print("-" * 80)
        for i, book in enumerate(mapping, 1):
            author = book.get("author", "")
            if author:
                print(f"{i:3d}. {book['title']}\t[{book['book_id']}]\t{author}")
            else:
                print(f"{i:3d}. {book['title']}\t[{book['book_id']}]")
        return

    # 直接下载
    if args.url:
        if not args.title:
            print("Error: --title is required when using --url")
            return
        print(f"\nDownloading: {args.title}")
        print(f"Chapter URL: {args.url}")
        download_book(args.url, args.title, args.output)
        return

    # 搜索书籍
    if not args.query:
        print("Error: 请提供书名或使用 --index 查看所有书籍")
        ap.print_help()
        return

    # 加载映射
    mapping = load_mapping(args.mapping)

    # 搜索书籍
    print(f"\n{'='*80}")
    print(f"搜索书籍: {args.query}")
    print(f"{'='*80}\n")

    results = search_book(args.query, mapping)

    if not results:
        print(f"❌ 未找到匹配的书籍: {args.query}")
        print("\n提示:")
        print("  1. 使用 --index 查看所有可用书籍")
        print("  2. 尝试更精确的书名")
        print("  3. 该书可能不在识典古籍数据库中")
        return

    # 显示搜索结果
    print(f"✅ 找到 {len(results)} 本匹配的书籍:\n")
    for i, book in enumerate(results, 1):
        author = book.get("author", "")
        print(f"  {i}. {book['title']}")
        print(f"     编号: {book['book_id']}")
        print(f"     作者: {author}")
        print(f"     URL: {book['url']}")
        print()

    # 选择第一本书
    if len(results) == 1:
        selected_book = results[0]
    else:
        print(f"找到多本匹配的书籍，默认选择第一本: {results[0]['title']}")
        selected_book = results[0]

    print(f"{'='*80}")
    print(f"已选择: {selected_book['title']} [{selected_book['book_id']}]")
    print(f"{'='*80}\n")

    # 搜索章节 URL（通过外部搜索引擎）
    print("正在搜索章节 URL...")
    chapter_url = search_chapter_url(selected_book['title'])

    # 如果有章节 URL，自动下载
    if chapter_url:
        print(f"\n找到章节 URL: {chapter_url}")
        print(f"开始下载: {selected_book['title']}")
        download_book(chapter_url, selected_book['title'], args.output)

if __name__ == "__main__":
    main()
