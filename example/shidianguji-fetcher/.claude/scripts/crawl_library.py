#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识典古籍书库爬取脚本

目标：从书库页面提取书名-编号映射
"""

import requests
from bs4 import BeautifulSoup
import json
import re

BASE_URL = "https://www.shidianguji.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def fetch_library_page(page_num=1):
    """获取书库页面"""
    url = f"{BASE_URL}/library?page_from=home_page"
    if page_num > 1:
        url += f"&page={page_num}"

    headers = {"User-Agent": UA}
    print(f"Fetching: {url}")

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text, url

def extract_book_mapping(html, url):
    """从 HTML 中提取书名-编号映射"""
    soup = BeautifulSoup(html, "html.parser")

    # 方案1: 提取 i18n 数据中的书籍信息
    book_map = {}

    # 查找所有 script 标签
    for script in soup.find_all("script"):
        if script.string:
            text = script.string
            # 查找 window._ROUTER_DATA
            if "window._ROUTER_DATA" in text:
                # 提取 JSON 部分
                m = re.search(r'window\._ROUTER_DATA\s*=\s*(\{[^;]+\})', text)
                if m:
                    try:
                        router_data = json.loads(m.group(1))
                        # 从 i18nData 中提取书籍信息
                        i18n_data = router_data.get("loaderData", {}).get("layout", {}).get("i18nData", {}).get("zh", {})

                        # 提取所有 bookName_ 开头的数据
                        for key, value in i18n_data.items():
                            if key.startswith("bookName_"):
                                book_id = key.replace("bookName_", "")
                                if value and book_id:
                                    book_map[book_id] = {
                                        "book_id": book_id,
                                        "title": value.strip(),
                                        "author": i18n_data.get(f"bookAuthor_{book_id}", ""),
                                        "url": f"{BASE_URL}/book/{book_id}"
                                    }
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse JSON: {e}")
                        continue

    # 方案2: 如果 i18n 数据为空，尝试从 a 标签提取
    if not book_map:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/book/" in href:
                # 提取 book_id
                m = re.search(r"/book/([^/]+)", href)
                if m:
                    book_id = m.group(1)
                    title = a.get_text(strip=True)
                    if title and len(title) > 1:  # 过滤掉空标题或太短的
                        full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                        book_map[book_id] = {
                            "title": title,
                            "book_id": book_id,
                            "url": full_url,
                            "href": href
                        }

    # 转换为列表
    return list(book_map.values())

def save_mapping(mapping, output_file="shidianguji_book_mapping.json"):
    """保存映射到 JSON 文件"""
    # 按 book_id 排序
    sorted_mapping = sorted(mapping, key=lambda x: x["book_id"])

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(sorted_mapping)} books to {output_file}")

    # 同时保存为一个简单的文本文件，方便搜索
    txt_file = output_file.replace(".json", ".txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        for book in sorted_mapping:
            author = book.get("author", "")
            if author:
                f.write(f"{book['title']}\t{book['book_id']}\t{author}\n")
            else:
                f.write(f"{book['title']}\t{book['book_id']}\n")
    print(f"Also saved to {txt_file} (searchable text format)")

def main():
    print(">> Crawling Shidianguji Library")

    # 尝试获取第一页
    html, url = fetch_library_page(1)

    # 保存原始 HTML 用于调试
    with open("library_page_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved raw HTML to library_page_debug.html")

    # 提取映射
    mapping = extract_book_mapping(html, url)

    if mapping:
        print(f"\nFound {len(mapping)} books:")
        for book in mapping[:10]:  # 只显示前 10 个
            print(f"  - {book['title']}: {book['book_id']}")

        if len(mapping) > 10:
            print(f"  ... and {len(mapping) - 10} more")

        # 保存映射
        save_mapping(mapping)
    else:
        print("No books found. The page might be a SPA that requires JavaScript.")

        # 尝试查找是否有 JSON 数据嵌入在 script 标签中
        scripts = BeautifulSoup(html, "html.parser").find_all("script")
        for i, script in enumerate(scripts):
            text = script.string
            if text and ("book" in text.lower() or "library" in text.lower()):
                print(f"\nFound potential JSON in script tag #{i}:")
                print(text[:500])  # 只显示前 500 字符

if __name__ == "__main__":
    main()
