#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识典古籍采集脚本 — Agent 友好版

核心原理:
    识典古籍的「章节页面」是服务端渲染的，包含完整正文和侧边栏章节列表。
    只要给定任意一个章节 URL，即可发现整本书全部章节并逐章下载。

    而「书籍首页」是 SPA 客户端渲染，直接 HTTP GET 拿不到章节列表。
    所以本脚本的入口是 **章节 URL**，由 Agent 通过搜索网站获得。

Agent 工作流:
    1. 用户给出书名
    2. Agent 在 https://www.shidianguji.com/ 搜索书名，找到任意章节 URL
       （格式: https://www.shidianguji.com/book/{BOOK_ID}/chapter/{CHAPTER_ID}）
    3. 运行: python fetch_book.py <chapter_url> [--title 书名] [--output dir]
    4. 脚本从该章节页面发现所有章节 → 逐章下载 → 合并为 Markdown

用法:
    python fetch_book.py <chapter_url> [options]

示例:
    python fetch_book.py "https://www.shidianguji.com/book/DZ1040/chapter/1k1r7oqmxaxaz" --title 皇极经世
    python fetch_book.py "https://www.shidianguji.com/book/SBCK004/chapter/abc123" -t 论语 -o ./books
"""

import argparse
import re
import os
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shidianguji.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
NOISE = frozenset(["", "下一篇", "上一章", "目录", "返回", "书库", "首页", "登录", "注册"])


def parse_chapter_url(url: str) -> tuple[str, str]:
    """从章节 URL 提取 book_id 和 chapter_id"""
    m = re.search(r"/book/([^/]+)/chapter/([^/?#]+)", url)
    if not m:
        print(f"[ERR] URL 不是章节格式: {url}", file=sys.stderr)
        print("      需要: https://www.shidianguji.com/book/XXXX/chapter/YYYY", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2)


def get_html(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.content, "html.parser")


# ── chapter discovery ─────────────────────────────────────────────

def discover_chapters(session: requests.Session, chapter_url: str, book_id: str) -> list[dict]:
    """从一个章节页面的侧边栏/链接发现整本书的全部章节"""
    print(f"  Discovering from: {chapter_url}")
    soup = get_html(session, chapter_url)

    seen = set()
    chapters = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/chapter/" not in href or book_id not in href:
            continue
        title = a.get_text(strip=True)
        if title in NOISE or len(title) < 2:
            continue
        full = f"{BASE_URL}{href}" if href.startswith("/") else href
        if full not in seen:
            seen.add(full)
            chapters.append({"url": full, "title": title})

    return chapters


# ── content extraction ────────────────────────────────────────────

def fetch_chapter(session: requests.Session, url: str) -> str:
    """从章节页面提取正文文本"""
    soup = get_html(session, url)
    for tag in soup(["script", "style"]):
        tag.decompose()

    article = soup.find("article")
    if article:
        text = article.get_text("\n", strip=True)
    else:
        sels = [".content", ".main-content", ".text-content",
                "#content", "[class*='content']", "[class*='chapter']"]
        elems = []
        for s in sels:
            elems.extend(soup.select(s))
        if elems:
            text = max(elems, key=lambda e: len(e.get_text())).get_text("\n", strip=True)
        else:
            for junk in soup.find_all(["nav", "header", "footer", "aside"]):
                junk.decompose()
            text = soup.get_text("\n", strip=True)

    # cleanup
    for pat in [r"登录后阅读更方便", r"下一篇.*$", r"上一章.*$", r"^目录$"]:
        text = re.sub(pat, "", text, flags=re.MULTILINE)
    return "\n\n".join(ln.strip() for ln in text.splitlines() if ln.strip())


# ── markdown output ───────────────────────────────────────────────

def save_markdown(chapters: list[dict], title: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fp = os.path.join(output_dir, f"{title}_{ts}.md")

    toc = "\n".join(
        f"{i}. [{c['title']}](#{c['title'].replace(' ', '-')})"
        for i, c in enumerate(chapters, 1)
    )
    body = "\n\n".join(
        f"## {i}. {c['title']}\n\n**来源:** {c['url']}\n\n---\n\n{c['content']}\n\n---"
        for i, c in enumerate(chapters, 1)
    )
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(fp, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**来源:** https://www.shidianguji.com/\n")
        f.write(f"**时间:** {now}\n\n---\n\n")
        f.write(f"## 目录\n\n{toc}\n\n---\n\n{body}\n")

    return fp


# ── main ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="从识典古籍章节页面批量下载整本书并生成 Markdown",
        epilog="Agent 需先在网站上搜到任意章节 URL，再传给本脚本。",
    )
    ap.add_argument("url", help="任意章节 URL (含 /book/XX/chapter/YY)")
    ap.add_argument("--title", "-t", default="", help="书名 (用于文件名)")
    ap.add_argument("--output", "-o", default="output", help="输出目录 (默认: output)")
    ap.add_argument("--delay", "-d", type=float, default=1.0, help="章节间隔秒数 (默认: 1)")
    args = ap.parse_args()

    book_id, _ = parse_chapter_url(args.url)
    title = args.title or book_id

    session = requests.Session()
    session.headers["User-Agent"] = UA

    print(f">> {title}")

    # 1. discover
    chapters = discover_chapters(session, args.url, book_id)
    if not chapters:
        print("[ERR] 未发现任何章节", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(chapters)} chapters found")

    # 2. fetch
    data = []
    for i, ch in enumerate(chapters, 1):
        print(f"  [{i}/{len(chapters)}] {ch['title']}")
        try:
            content = fetch_chapter(session, ch["url"])
        except Exception as e:
            print(f"    skip: {e}")
            continue
        if len(content) > 50:
            data.append({**ch, "content": content})
        time.sleep(args.delay)

    if not data:
        print("[ERR] 未下载到任何内容", file=sys.stderr)
        sys.exit(1)

    # 3. save
    fp = save_markdown(data, title, args.output)
    print(f"[OK] {len(data)} chapters -> {fp}")


if __name__ == "__main__":
    main()
