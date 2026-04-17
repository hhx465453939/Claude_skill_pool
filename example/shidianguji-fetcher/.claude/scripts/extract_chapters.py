#!/usr/bin/env python3
"""
从识典古籍书籍页面提取章节列表
"""

import requests
import json
import re

def extract_chapters_from_book_page(book_id):
    """
    尝试从识典古籍书籍页面提取章节列表
    """
    book_url = f"https://www.shidianguji.com/book/{book_id}"

    try:
        response = requests.get(book_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()

        html = response.text

        # 尝试在HTML中查找章节列表的JSON数据
        # 识典古籍可能会在页面中嵌入JSON数据

        # 查找所有<script>标签
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html, re.DOTALL)

        chapters = []

        for script in scripts:
            # 尝试在script中查找包含chapter的JSON
            if 'chapter' in script.lower():
                # 尝试提取JSON对象
                try:
                    # 查找JSON对象（可能包裹在window.__INITIAL_STATE__等变量中）
                    json_pattern = r'\{[^{}]*"[^"]*chapter[^"]*"[^{}]*\}'
                    json_matches = re.findall(json_pattern, script)
                    for json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            if 'chapters' in data or 'chapter' in data:
                                print(f"Found JSON with chapter data!")
                                print(json.dumps(data, indent=2, ensure_ascii=False))
                                return data
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    continue

        # 如果没找到JSON，尝试查找HTML中的章节链接
        link_pattern = r'<a[^>]*href=["\']([^"\']*chapter[^"\']*)["\'][^>]*>([^<]*)</a>'
        links = re.findall(link_pattern, html)
        if links:
            print(f"\nFound {len(links)} chapter links in HTML:")
            for href, text in links:
                print(f"  {text}: {href}")
                chapters.append({'title': text, 'url': href})
            return chapters

        print("\nNo chapters found in book page.")
        print(f"HTML length: {len(html)} characters")
        print(f"First 500 chars:\n{html[:500]}")

        return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == '__main__':
    book_id = "7471275350006169615"  # 五行大义的book_id
    print(f"Extracting chapters from book: {book_id}\n")
    result = extract_chapters_from_book_page(book_id)
    if result:
        print(f"\nExtracted {len(result)} chapters!")
