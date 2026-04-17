#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识典古籍自动化下载工具

工作流：
1. 从本地映射文件搜索书名 → 获取 book_id
2. 构造书籍 URL → 访问获取第一个章节 URL
3. 调用 fetch_book.py 下载整本书
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path

# 默认映射文件路径
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

def get_first_chapter_url(book_id):
    """获取书籍的第一个章节 URL"""
    import requests
    from bs4 import BeautifulSoup

    book_url = f"https://www.shidianguji.com/book/{book_id}"
    print(f"Fetching book page: {book_url}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    r = requests.get(book_url, headers=headers, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, "html.parser")

    # 查找第一个章节链接
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/chapter/" in href and book_id in href:
            full_url = f"https://www.shidianguji.com{href}" if href.startswith("/") else href
            return full_url

    return None

def download_book(chapter_url, title, output_dir="output"):
    """调用 fetch_book.py 下载书籍"""
    import subprocess

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
        description="识典古籍自动化下载工具 - 从书名搜索到完整下载",
        epilog="示例:\n  python search_and_download.py 韩非子\n  python search_and_download.py 论语 -o ./books",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("query", help="书名或关键词")
    ap.add_argument("--mapping", "-m", default=DEFAULT_MAPPING,
                   help=f"映射文件路径（默认: {DEFAULT_MAPPING}）")
    ap.add_argument("--output", "-o", default="output", help="输出目录（默认: output）")
    ap.add_argument("--update-mapping", action="store_true",
                   help="更新映射文件（运行 crawl_library.py）")
    ap.add_argument("--list", "-l", action="store_true",
                   help="只显示搜索结果，不下载")
    ap.add_argument("--index", action="store_true",
                   help="显示所有书籍的索引")

    args = ap.parse_args()

    # 更新映射
    if args.update_mapping:
        print("Updating mapping...")
        import subprocess
        crawl_script = os.path.join(os.path.dirname(__file__), "crawl_library.py")
        subprocess.run([sys.executable, crawl_script], check=True)
        return

    # 显示所有索引
    if args.index:
        mapping = load_mapping(args.mapping)
        print(f"\nTotal books: {len(mapping)}\n")
        for i, book in enumerate(mapping, 1):
            author = book.get("author", "")
            if author:
                print(f"{i:3d}. {book['title']}\t[{book['book_id']}]\t{author}")
            else:
                print(f"{i:3d}. {book['title']}\t[{book['book_id']}]")
        return

    # 加载映射
    mapping = load_mapping(args.mapping)

    # 搜索书籍
    print(f"\nSearching for: {args.query}")
    results = search_book(args.query, mapping)

    if not results:
        print(f"No results found for: {args.query}")
        print("Use --index to see all available books.")
        return

    # 显示搜索结果
    print(f"\nFound {len(results)} result(s):")
    for i, book in enumerate(results, 1):
        author = book.get("author", "")
        if author:
            print(f"  {i}. {book['title']} [{book['book_id']}] - {author}")
        else:
            print(f"  {i}. {book['title']} [{book['book_id']}]")

    # 只显示结果
    if args.list:
        return

    # 选择第一本书（如果有多本，可以提示用户选择）
    if len(results) == 1:
        selected_book = results[0]
    else:
        print(f"\nMultiple results found. Using the first one: {results[0]['title']}")
        selected_book = results[0]

    print(f"\nSelected: {selected_book['title']} [{selected_book['book_id']}]")

    # 获取第一个章节 URL
    chapter_url = get_first_chapter_url(selected_book["book_id"])

    if not chapter_url:
        print(f"Failed to find chapter URL for: {selected_book['book_id']}")
        return

    print(f"Chapter URL: {chapter_url}")

    # 下载书籍
    download_book(chapter_url, selected_book["title"], args.output)

if __name__ == "__main__":
    main()
