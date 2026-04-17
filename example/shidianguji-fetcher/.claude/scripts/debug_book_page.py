#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

url = "https://www.shidianguji.com/book/SBCK087"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

r = requests.get(url, headers=headers, timeout=30)
r.raise_for_status()

soup = BeautifulSoup(r.content, "html.parser")

# 查找所有链接
links = soup.find_all("a", href=True)
print(f"Found {len(links)} links")

# 查找 /chapter/ 链接
chapter_links = [a for a in links if "/chapter/" in a["href"]]
print(f"Found {len(chapter_links)} chapter links")

# 显示前 10 个
for i, a in enumerate(chapter_links[:10], 1):
    print(f"{i}. {a['href']} - {a.get_text(strip=True)[:50]}")

# 查找 JSON 数据
scripts = soup.find_all("script")
for i, script in enumerate(scripts):
    if script.string and ("chapter" in script.string.lower() or "SBCK087" in script.string):
        print(f"\n=== Script #{i} ===")
        print(script.string[:500])
