#!/usr/bin/env node

const path = require("path");
const runtime = require("./runtime-lib");

function parseArgs(argv) {
  const parsed = {
    command: "",
    positionals: [],
    inputs: [],
    outputDir: runtime.OUTPUT_DIR,
    title: "",
    limit: 10,
    maxChapters: 0,
    format: "text",
    help: false,
  };

  if (argv.length > 0 && !argv[0].startsWith("-")) {
    parsed.command = argv[0];
    argv = argv.slice(1);
  }

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--output-dir" || arg === "-o") {
      parsed.outputDir = argv[++i];
      continue;
    }
    if (arg === "--title" || arg === "-t") {
      parsed.title = argv[++i] || "";
      continue;
    }
    if (arg === "--limit") {
      parsed.limit = Number(argv[++i] || 10);
      continue;
    }
    if (arg === "--max-chapters") {
      parsed.maxChapters = Number(argv[++i] || 0);
      continue;
    }
    if (arg === "--format") {
      parsed.format = argv[++i] || "text";
      continue;
    }
    if (arg === "--json") {
      parsed.format = "json";
      continue;
    }
    if (arg === "--input") {
      parsed.inputs.push(argv[++i] || "");
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      parsed.help = true;
      continue;
    }
    parsed.positionals.push(arg);
  }

  return parsed;
}

function usage() {
  return [
    "Usage:",
    "  node skills/shidianguji-fetcher/scripts/cli.js search <query> [--limit 10] [--json]",
    "  node skills/shidianguji-fetcher/scripts/cli.js context <query> [--limit 10] [--json]",
    "  node skills/shidianguji-fetcher/scripts/cli.js resolve <input> [--json]",
    "  node skills/shidianguji-fetcher/scripts/cli.js download <input> [--title 书名] [--output-dir DIR] [--max-chapters N]",
    "  node skills/shidianguji-fetcher/scripts/cli.js batch --input <query_or_url> --input <query_or_url> [--output-dir DIR] [--max-chapters N]",
    "",
    "Input supports:",
    "  - 关键词（如 论语 / 皇极经世）",
    "  - book URL",
    "  - chapter URL",
    "  - book ID",
  ].join("\n");
}

function printJson(payload) {
  console.log(JSON.stringify(payload, null, 2));
}

function printSearchResults(query, results, limit) {
  console.log(`# 搜索结果: ${query}`);
  console.log("");
  console.log(`共找到 ${results.length} 条候选，展示前 ${Math.min(results.length, limit)} 条。`);
  console.log("");
  results.slice(0, limit).forEach((item, index) => {
    console.log(`${index + 1}. ${item.title}`);
    console.log(`   - bookId: ${item.bookId}`);
    console.log(`   - sourceType: ${item.sourceType}`);
    if (item.matchedChapterTitle) {
      console.log(`   - matchedChapterTitle: ${item.matchedChapterTitle}`);
    }
    console.log(`   - canonicalUrl: ${item.canonicalUrl}`);
    console.log("");
  });
}

function printResolved(detail, mode, searchCandidates) {
  console.log(`# 解析结果`);
  console.log("");
  console.log(`- mode: ${mode}`);
  console.log(`- title: ${detail.title}`);
  console.log(`- bookId: ${detail.bookId}`);
  console.log(`- canonicalUrl: ${detail.canonicalUrl}`);
  console.log(`- chapterCount: ${detail.chapterCount}`);
  console.log(`- seedChapterUrl: ${detail.seedChapterUrl || ""}`);
  if (searchCandidates.length > 0) {
    console.log(`- searchCandidates: ${searchCandidates.length}`);
  }
}

async function handleSearch(args) {
  const query = args.positionals.join(" ").trim();
  if (!query) {
    throw new Error("search 需要关键词");
  }
  const results = await runtime.searchBooksByKeyword(query);
  if (args.format === "json") {
    printJson(results);
    return;
  }
  printSearchResults(query, results, args.limit);
}

async function handleResolve(args) {
  const input = args.positionals.join(" ").trim();
  if (!input) {
    throw new Error("resolve 需要输入书名、链接或 bookId");
  }
  const resolved = await runtime.resolveBookInput(input);
  if (args.format === "json") {
    printJson(resolved);
    return;
  }
  printResolved(resolved.detail, resolved.mode, resolved.searchCandidates);
}

async function handleContext(args) {
  const query = args.positionals.join(" ").trim();
  if (!query) {
    throw new Error("context 需要关键词");
  }
  const results = await runtime.searchLocalCorpus(query, {
    outputDir: args.outputDir,
    limit: args.limit,
  });
  if (args.format === "json") {
    printJson(results);
    return;
  }
  console.log(`# 上下文检索: ${query}`);
  console.log("");
  if (!results.length) {
    console.log("未在本地已下载古籍中找到匹配片段。");
    return;
  }
  results.forEach((item, index) => {
    console.log(`${index + 1}. ${item.fileName}:${item.line}`);
    console.log(item.snippet);
    console.log("");
  });
}

async function handleDownload(args) {
  const input = args.positionals.join(" ").trim();
  if (!input) {
    throw new Error("download 需要输入书名、链接或 bookId");
  }
  const resolved = await runtime.resolveBookInput(input);
  const exported = await runtime.exportBookMarkdown(
    resolved.detail.bookId,
    resolved.detail.seedChapterUrl,
    args.title || resolved.detail.title,
    {
      maxChapters: args.maxChapters > 0 ? args.maxChapters : undefined,
    },
  );
  const filePath = await runtime.writeMarkdownFile(exported, args.outputDir);
  if (args.format === "json") {
    printJson({
      mode: resolved.mode,
      detail: exported.detail,
      chapterCount: exported.chapters.length,
      filePath,
    });
    return;
  }
  console.log(`TITLE: ${exported.detail.title}`);
  console.log(`BOOK_ID: ${exported.detail.bookId}`);
  console.log(`CHAPTERS: ${exported.chapters.length}`);
  console.log(`FILEPATH:${filePath}`);
}

async function handleBatch(args) {
  const inputs = [...args.inputs, ...args.positionals].map((item) => item.trim()).filter(Boolean);
  if (inputs.length === 0) {
    throw new Error("batch 至少需要一个 --input");
  }
  const books = [];
  for (const input of inputs) {
    const resolved = await runtime.resolveBookInput(input);
    const exported = await runtime.exportBookMarkdown(
      resolved.detail.bookId,
      resolved.detail.seedChapterUrl,
      resolved.detail.title,
      {
        maxChapters: args.maxChapters > 0 ? args.maxChapters : undefined,
      },
    );
    books.push(exported);
  }
  const zip = await runtime.writeBatchZip(books, {
    outputDir: args.outputDir,
  });
  if (args.format === "json") {
    printJson({
      bookCount: books.length,
      books: books.map((book) => ({
        bookId: book.detail.bookId,
        title: book.detail.title,
        chapterCount: book.chapters.length,
      })),
      filePath: zip.filePath,
    });
    return;
  }
  console.log(`BOOKS: ${books.length}`);
  books.forEach((book, index) => {
    console.log(`${index + 1}. ${book.detail.title} (${book.detail.bookId}) - ${book.chapters.length} chapters`);
  });
  console.log(`FILEPATH:${zip.filePath}`);
}

async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (args.help || !args.command) {
    console.log(usage());
    return 0;
  }

  if (args.command === "search") {
    await handleSearch(args);
    return 0;
  }
  if (args.command === "resolve") {
    await handleResolve(args);
    return 0;
  }
  if (args.command === "context") {
    await handleContext(args);
    return 0;
  }
  if (args.command === "download" || args.command === "fetch") {
    await handleDownload(args);
    return 0;
  }
  if (args.command === "batch") {
    await handleBatch(args);
    return 0;
  }

  throw new Error(`未知命令: ${args.command}`);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`ERROR: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
}
