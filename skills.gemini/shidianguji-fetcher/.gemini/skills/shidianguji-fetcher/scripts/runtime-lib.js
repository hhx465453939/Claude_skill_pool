#!/usr/bin/env node

const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");

const SKILL_DIR = path.resolve(__dirname, "..");
const WORKSPACE_DIR = path.resolve(SKILL_DIR, "..", "..");
const OUTPUT_DIR = path.join(WORKSPACE_DIR, "books", "shidianguji-fetcher");
const CACHE_DIR = path.join(WORKSPACE_DIR, "cache", "shidianguji-fetcher");
const BASE_URL = "https://www.shidianguji.com";
const SEARCH_BASE_URL = `${BASE_URL}/search`;
const CHAPTER_SITEMAP_INDEX = `${BASE_URL}/sitemap/chapter-v2/index.xml`;
const REQUEST_DELAY_MS = 120;
const REQUEST_TIMEOUT_MS = 20_000;
const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";
const NOISE_TITLES = new Set(["上一篇", "下一篇", "目录", "返回", "书库", "首页", "登录", "注册"]);

function resolveRepoDir() {
  const candidates = [
    process.env.OPENCLAW_REPO_DIR,
    "/mnt/500G-1/clawdata/repo",
    "/app",
  ].filter(Boolean);

  for (const dir of candidates) {
    if (
      fs.existsSync(path.join(dir, "package.json")) &&
      fs.existsSync(path.join(dir, "node_modules"))
    ) {
      return dir;
    }
  }

  throw new Error(`Cannot resolve OpenClaw repo dir from candidates: ${candidates.join(", ")}`);
}

function requireFromRepo(packageName) {
  const repoDir = resolveRepoDir();
  const resolved = require.resolve(packageName, {
    paths: [repoDir, path.join(repoDir, "node_modules")],
  });
  return require(resolved);
}

const { parseHTML } = requireFromRepo("linkedom");
const JSZip = requireFromRepo("jszip");
const { Agent, EnvHttpProxyAgent, fetch: undiciFetch } = requireFromRepo("undici");

let sharedDispatcher = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getDispatcher() {
  if (sharedDispatcher) {
    return sharedDispatcher;
  }

  const hasProxyEnv = [process.env.HTTP_PROXY, process.env.HTTPS_PROXY, process.env.ALL_PROXY]
    .map((value) => String(value || "").trim())
    .some(Boolean);

  sharedDispatcher = hasProxyEnv
    ? new EnvHttpProxyAgent()
    : new Agent({
        keepAliveTimeout: 10_000,
        keepAliveMaxTimeout: 30_000,
        connections: 8,
      });

  return sharedDispatcher;
}

function normalizeDisplayText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .replace(/\s*([，。；：？！）】》])/g, "$1")
    .replace(/([（【《])\s*/g, "$1")
    .trim();
}

function extractIdsFromInput(input) {
  const trimmed = String(input || "").trim();
  const urlMatch = trimmed.match(
    /^https?:\/\/(?:www\.)?shidianguji\.com\/book\/([^/?#]+)(?:\/chapter\/([^/?#]+))?/i,
  );
  if (urlMatch) {
    return {
      bookId: urlMatch[1],
      chapterId: urlMatch[2],
      kind: urlMatch[2] ? "chapter" : "book",
    };
  }
  if (/^[A-Za-z0-9._-]{4,}$/.test(trimmed)) {
    return {
      bookId: trimmed,
      kind: "bookId",
    };
  }
  return null;
}

function buildBookUrl(bookId) {
  return `${BASE_URL}/book/${bookId}`;
}

function buildChapterUrl(bookId, chapterId) {
  return `${BASE_URL}/book/${bookId}/chapter/${chapterId}`;
}

function chapterIdFromUrl(url) {
  return url.split("/chapter/")[1] ?? url;
}

function fileSafeName(value) {
  return String(value || "")
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, "_")
    .slice(0, 120);
}

function commonPrefix(left, right) {
  const limit = Math.min(left.length, right.length);
  let index = 0;
  while (index < limit && left[index] === right[index]) {
    index += 1;
  }
  return left.slice(0, index);
}

function guessBookTitleFromChapterTitle(title, fallback) {
  const cleaned = normalizeDisplayText(title);
  const patterns = [/^(.+?)(卷第.+)$/, /^(.+?)(卷.+)$/, /^(.+?)(第.+[篇卷章节].*)$/];
  for (const pattern of patterns) {
    const match = cleaned.match(pattern);
    if (match && match[1].length >= 2) {
      return match[1];
    }
  }
  return cleaned.length >= 2 ? cleaned : fallback;
}

function guessBookTitleFromChapterList(titles, fallback) {
  const normalized = titles.map(normalizeDisplayText).filter(Boolean).slice(0, 8);
  if (!normalized.length) {
    return fallback;
  }
  let prefix = normalized[0];
  for (const title of normalized.slice(1)) {
    prefix = commonPrefix(prefix, title);
    if (!prefix) {
      break;
    }
  }
  prefix = prefix.replace(/(卷|第).+$/, "").trim();
  return prefix.length >= 2 ? prefix : fallback;
}

async function fetchText(url, options = {}, attempt = 0) {
  const retries = options.retries ?? 3;
  const acceptCandidates = Array.isArray(options.acceptCandidates) && options.acceptCandidates.length > 0
    ? options.acceptCandidates
    : [options.accept || "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"];
  const refererCandidates = Array.isArray(options.refererCandidates) && options.refererCandidates.length > 0
    ? options.refererCandidates
    : [options.referer || "", BASE_URL];

  let lastError = null;

  for (const acceptValue of acceptCandidates) {
    for (const refererValue of refererCandidates) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), options.timeoutMs || REQUEST_TIMEOUT_MS);
      try {
        const response = await undiciFetch(url, {
          headers: {
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9",
            Accept: acceptValue,
            ...(refererValue ? { Referer: refererValue } : {}),
          },
          cache: "no-store",
          dispatcher: getDispatcher(),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status} ${response.statusText}`);
        }

        const text = await response.text();
        clearTimeout(timeout);
        await sleep(REQUEST_DELAY_MS);
        return text;
      } catch (error) {
        clearTimeout(timeout);
        lastError = error;
      }
    }
  }

  if (attempt < retries) {
    await sleep(REQUEST_DELAY_MS * Math.pow(2, attempt + 1));
    return fetchText(url, options, attempt + 1);
  }

  if (lastError && lastError.name === "AbortError") {
    throw new Error(`Request timeout after ${options.timeoutMs || REQUEST_TIMEOUT_MS}ms: ${url}`);
  }
  throw lastError || new Error(`Unknown request failure: ${url}`);
}

function parseSearchHtml(html) {
  const { document } = parseHTML(html);
  const anchors = Array.from(document.querySelectorAll('#root a[href^="/book/"]'));
  const seen = new Set();
  const candidates = [];

  anchors.forEach((anchor, index) => {
    const href = anchor.getAttribute("href");
    if (!href) {
      return;
    }
    const absoluteUrl = `${BASE_URL}${href}`;
    const ids = extractIdsFromInput(absoluteUrl);
    if (!ids) {
      return;
    }
    const text = normalizeDisplayText(anchor.textContent || "");
    if (!text) {
      return;
    }
    const key = `${ids.bookId}:${ids.chapterId || "book"}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    candidates.push({
      bookId: ids.bookId,
      title: text,
      canonicalUrl: buildBookUrl(ids.bookId),
      sourceType: ids.chapterId ? "chapter" : "book",
      matchedChapterTitle: ids.chapterId ? text : undefined,
      score: ids.chapterId ? index + 10 : index,
    });
  });

  return candidates.sort((left, right) => left.score - right.score);
}

function parseChapterLinksFromHtml(html, bookId) {
  const { document } = parseHTML(html);
  const anchors = Array.from(document.querySelectorAll(`a[href^="/book/${bookId}/chapter/"]`));
  const seen = new Set();
  const items = [];

  anchors.forEach((anchor, index) => {
    const href = anchor.getAttribute("href");
    if (!href) {
      return;
    }
    const url = `${BASE_URL}${href}`;
    const title = normalizeDisplayText(anchor.textContent || "");
    if (!title || NOISE_TITLES.has(title) || seen.has(url)) {
      return;
    }
    seen.add(url);
    items.push({
      chapterId: chapterIdFromUrl(url),
      title,
      url,
      order: index + 1,
    });
  });

  return items;
}

function cleanChapterContent(content) {
  let cleaned = String(content || "");
  cleaned = cleaned.replace(/识典古籍[\s\S]*?版权所有/g, "");
  cleaned = cleaned.replace(/登录后阅读更方便/g, "");
  cleaned = cleaned.replace(/书库/g, "");
  cleaned = cleaned.replace(/目录/g, "");
  cleaned = cleaned.replace(/上一章.*$/gm, "");
  cleaned = cleaned.replace(/下一章.*$/gm, "");

  const lines = cleaned
    .split(/\r?\n/)
    .map((line) => normalizeDisplayText(line))
    .filter(Boolean);

  return lines.join("\n\n").trim();
}

function extractChapterContentFromHtml(html) {
  const { document } = parseHTML(html);
  document.querySelectorAll("script, style").forEach((node) => node.remove());

  const article = document.querySelector("article");
  let content = article?.textContent || "";

  if (!content.trim()) {
    const selectors = [
      ".chapter-reader-content",
      ".content",
      ".main-content",
      ".text-content",
      "#content",
      "[class*='content']",
      "[class*='text']",
      "[class*='chapter']",
    ];
    let best = "";
    for (const selector of selectors) {
      for (const node of document.querySelectorAll(selector)) {
        const text = node.textContent || "";
        if (text.length > best.length) {
          best = text;
        }
      }
    }
    content = best;
  }

  if (!content.trim()) {
    document.querySelectorAll("nav, header, footer, aside").forEach((node) => node.remove());
    content = document.body?.textContent || "";
  }

  return cleanChapterContent(content);
}

function buildMarkdownDocument(detail, chapters) {
  const lines = [
    "---",
    `title: ${detail.title}`,
    `bookId: ${detail.bookId}`,
    `source: ${detail.canonicalUrl}`,
    `retrievedAt: ${new Date().toISOString()}`,
    `retrievalMode: ${detail.retrievalMode}`,
    "---",
    "",
    `# ${detail.title}`,
    "",
    "## 书目信息",
    "",
    `- 书籍 ID：${detail.bookId}`,
    `- 原始链接：${detail.canonicalUrl}`,
  ];

  if (detail.seedChapterUrl) {
    lines.push(`- 章节入口：${detail.seedChapterUrl}`);
  }

  lines.push("", "## 目录", "");
  chapters.forEach((chapter, index) => {
    lines.push(`${index + 1}. ${chapter.title}`);
  });
  lines.push("", "## 正文", "");
  chapters.forEach((chapter, index) => {
    lines.push(`### ${index + 1}. ${chapter.title}`, "", chapter.content, "", "---", "");
  });
  return `${lines.join("\n")}\n`;
}

function extractLocTags(xml) {
  const matches = xml.match(/<loc>([^<]+)<\/loc>/g) || [];
  return matches
    .map((entry) => entry.replace(/^<loc>/, "").replace(/<\/loc>$/, "").trim())
    .filter(Boolean);
}

const chapterCacheFile = path.join(CACHE_DIR, "chapter-cache.json");
let chapterCache = null;
let chapterSitemapIndexUrlsPromise = null;

async function ensureCacheDir() {
  await fsp.mkdir(CACHE_DIR, { recursive: true });
}

async function readChapterCache() {
  if (chapterCache) {
    return chapterCache;
  }
  try {
    chapterCache = JSON.parse(await fsp.readFile(chapterCacheFile, "utf8"));
  } catch {
    chapterCache = {};
  }
  return chapterCache;
}

async function writeChapterCache(cache) {
  chapterCache = cache;
  await ensureCacheDir();
  await fsp.writeFile(chapterCacheFile, JSON.stringify(cache, null, 2), "utf8");
}

async function getChapterSitemapIndexUrls() {
  if (!chapterSitemapIndexUrlsPromise) {
    chapterSitemapIndexUrlsPromise = (async () => {
      const xml = await fetchText(CHAPTER_SITEMAP_INDEX, {
        acceptCandidates: ["application/xml,*/*", "text/xml,*/*", "text/html,*/*"],
      });
      return extractLocTags(xml);
    })();
  }
  return chapterSitemapIndexUrlsPromise;
}

async function getChapterUrlsForBook(bookId) {
  const cache = await readChapterCache();
  if (cache[bookId]) {
    return cache[bookId];
  }

  const urls = [];
  const indexUrls = await getChapterSitemapIndexUrls();
  for (const sitemapUrl of indexUrls) {
    const xml = await fetchText(sitemapUrl, {
      acceptCandidates: ["application/xml,*/*", "text/xml,*/*", "text/html,*/*"],
    });
    for (const loc of extractLocTags(xml)) {
      if (loc.includes(`/book/${bookId}/chapter/`)) {
        urls.push(loc);
      }
    }
  }

  cache[bookId] = urls;
  await writeChapterCache(cache);
  return urls;
}

async function searchBooksByKeyword(query) {
  const html = await fetchText(`${SEARCH_BASE_URL}/${encodeURIComponent(query.trim())}`, {
    refererCandidates: [`${BASE_URL}/`, SEARCH_BASE_URL, ""],
  });
  return parseSearchHtml(html);
}

function fallbackChapterList(urls) {
  return urls.map((url, index) => ({
    chapterId: chapterIdFromUrl(url),
    title: `章节 ${index + 1}`,
    url,
    order: index + 1,
  }));
}

async function guessBookTitle(bookId, firstChapterTitle) {
  const candidates = await searchBooksByKeyword(firstChapterTitle);
  const matched = candidates.find((candidate) => candidate.bookId === bookId);
  if (matched) {
    return matched.title;
  }
  return guessBookTitleFromChapterTitle(firstChapterTitle, bookId);
}

async function discoverChaptersForBook(bookId, seedChapterUrl) {
  const urls = seedChapterUrl ? [seedChapterUrl] : await getChapterUrlsForBook(bookId);
  if (!urls.length) {
    throw new Error(`未在站点索引中找到 ${bookId} 的章节入口`);
  }
  const actualSeed = urls[0];
  const html = await fetchText(actualSeed, {
    refererCandidates: [buildBookUrl(bookId), BASE_URL, ""],
  });
  const parsed = parseChapterLinksFromHtml(html, bookId);
  const chapters = parsed.length > 1 ? parsed : fallbackChapterList(urls);
  const prefixGuess = guessBookTitleFromChapterList(
    chapters.map((chapter) => chapter.title),
    "",
  );
  const guessedTitle = prefixGuess
    ? prefixGuess
    : await guessBookTitle(bookId, normalizeDisplayText(chapters[0]?.title || bookId));

  return {
    bookId,
    seedChapterUrl: actualSeed,
    chapters,
    guessedTitle,
  };
}

async function discoverChaptersFromInput(input) {
  const ids = extractIdsFromInput(input);
  if (!ids) {
    throw new Error("无法从输入中提取书籍信息");
  }
  if (ids.chapterId) {
    return discoverChaptersForBook(ids.bookId, buildChapterUrl(ids.bookId, ids.chapterId));
  }
  return discoverChaptersForBook(ids.bookId);
}

async function resolveInputToBookDetail(input) {
  const ids = extractIdsFromInput(input);
  if (!ids) {
    throw new Error("请输入关键词、book ID，或识典古籍书籍链接");
  }

  const discovery =
    ids.kind === "chapter"
      ? await discoverChaptersFromInput(input)
      : await discoverChaptersForBook(ids.bookId);

  return {
    bookId: discovery.bookId,
    title: discovery.guessedTitle,
    canonicalUrl: buildBookUrl(discovery.bookId),
    chapterCount: discovery.chapters.length,
    status: "ready",
    retrievalMode: "mixed",
    seedChapterUrl: discovery.seedChapterUrl,
  };
}

function selectBestCandidate(query, candidates) {
  const trimmed = normalizeDisplayText(query);
  const exact = candidates.find((candidate) => normalizeDisplayText(candidate.title) === trimmed);
  if (exact) {
    return exact;
  }
  const bookCandidate = candidates.find((candidate) => candidate.sourceType === "book");
  return bookCandidate || candidates[0];
}

async function resolveBookInput(input) {
  const ids = extractIdsFromInput(input);
  if (ids) {
    return {
      mode: "direct",
      detail: await resolveInputToBookDetail(input),
      searchCandidates: [],
    };
  }

  const candidates = await searchBooksByKeyword(input);
  if (!candidates.length) {
    throw new Error(`未找到与「${input}」匹配的识典古籍书目`);
  }
  const selected = selectBestCandidate(input, candidates);
  return {
    mode: "search",
    detail: await resolveInputToBookDetail(selected.canonicalUrl),
    searchCandidates: candidates,
  };
}

async function exportBookMarkdown(bookId, seedChapterUrl, preferredTitle, options = {}) {
  const discovery = await discoverChaptersForBook(bookId, seedChapterUrl);
  const chapters = [];
  const maxChapters =
    Number.isInteger(options.maxChapters) && options.maxChapters > 0
      ? options.maxChapters
      : null;
  const sourceChapters = maxChapters
    ? discovery.chapters.slice(0, maxChapters)
    : discovery.chapters;

  for (const chapter of sourceChapters) {
    const html = await fetchText(chapter.url, {
      refererCandidates: [buildBookUrl(bookId), BASE_URL, ""],
    });
    const content = extractChapterContentFromHtml(html);
    if (!content) {
      continue;
    }
    chapters.push({
      chapterId: chapter.chapterId || chapterIdFromUrl(chapter.url),
      title: chapter.title,
      url: chapter.url,
      order: chapter.order,
      content,
    });
  }

  const detail = {
    bookId,
    title: preferredTitle || discovery.guessedTitle,
    canonicalUrl: buildBookUrl(bookId),
    chapterCount: sourceChapters.length,
    status: chapters.length ? "ready" : "blocked",
    retrievalMode: "mixed",
    seedChapterUrl: discovery.seedChapterUrl,
  };
  const markdown = buildMarkdownDocument(detail, chapters);
  const fileName = `${fileSafeName(detail.title)}_${bookId}.md`;

  return {
    detail,
    chapters,
    markdown,
    fileName,
  };
}

async function ensureOutputDir(outputDir = OUTPUT_DIR) {
  await fsp.mkdir(outputDir, { recursive: true });
  return outputDir;
}

async function writeMarkdownFile(exported, outputDir = OUTPUT_DIR) {
  const dir = await ensureOutputDir(outputDir);
  const filePath = path.join(dir, exported.fileName);
  await fsp.writeFile(filePath, exported.markdown, "utf8");
  return filePath;
}

async function writeBatchZip(books, options = {}) {
  const dir = await ensureOutputDir(options.outputDir || OUTPUT_DIR);
  const jobId = options.jobId || `batch_${Date.now().toString(36)}`;
  const fileName = `shidianguji_batch_${jobId}.zip`;
  const filePath = path.join(dir, fileName);
  const zip = new JSZip();
  zip.file(
    "manifest.json",
    JSON.stringify(
      {
        jobId,
        createdAt: new Date().toISOString(),
        books: books.map((book) => ({
          bookId: book.detail.bookId,
          title: book.detail.title,
          fileName: book.fileName,
          chapterCount: book.chapters.length,
        })),
      },
      null,
      2,
    ),
  );
  zip.file("合集.md", books.map((book) => `# ${book.detail.title}\n\n${book.markdown}`).join("\n\n"));
  books.forEach((book) => {
    zip.file(`books/${book.fileName}`, book.markdown);
  });
  const buffer = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  await fsp.writeFile(filePath, buffer);
  return { filePath, fileName };
}

async function searchLocalCorpus(query, options = {}) {
  const dir = options.outputDir || OUTPUT_DIR;
  const needle = normalizeDisplayText(query);
  if (!needle) {
    return [];
  }
  let files = [];
  try {
    files = (await fsp.readdir(dir))
      .filter((name) => name.endsWith(".md"))
      .map((name) => path.join(dir, name));
  } catch {
    return [];
  }

  const limit = Number.isInteger(options.limit) && options.limit > 0 ? options.limit : 10;
  const results = [];
  for (const filePath of files) {
    const content = await fsp.readFile(filePath, "utf8");
    const lines = content.split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (!normalizeDisplayText(line).includes(needle)) {
        continue;
      }
      const start = Math.max(0, index - 2);
      const end = Math.min(lines.length, index + 3);
      const snippet = lines.slice(start, end).join("\n").trim();
      results.push({
        filePath,
        fileName: path.basename(filePath),
        line: index + 1,
        snippet,
      });
      if (results.length >= limit) {
        return results;
      }
    }
  }
  return results;
}

module.exports = {
  BASE_URL,
  CACHE_DIR,
  OUTPUT_DIR,
  SEARCH_BASE_URL,
  REQUEST_DELAY_MS,
  searchBooksByKeyword,
  resolveInputToBookDetail,
  resolveBookInput,
  discoverChaptersForBook,
  exportBookMarkdown,
  writeMarkdownFile,
  writeBatchZip,
  searchLocalCorpus,
  normalizeDisplayText,
  extractIdsFromInput,
  buildBookUrl,
  buildChapterUrl,
};
