#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent.parent
TASK_SCRIPT_DIR = WORKSPACE_DIR / "scripts"
sys.path.insert(0, str(TASK_SCRIPT_DIR))

import task_session  # noqa: E402


CONFIG_PATH = WORKSPACE_DIR / "config" / "mcporter.json"
CACHE_DIR = WORKSPACE_DIR / "config" / "cache"
DEFAULT_REGISTRY_PATH = CACHE_DIR / "market-alpha-tool-registry.json"
DEFAULT_ACCESS_LOG_PATH = CACHE_DIR / "market-alpha-routing-access.jsonl"
DEFAULT_HEALTH_REPORT_PATH = CACHE_DIR / "market-alpha-health-report.json"
DEFAULT_DASHBOARD_PATH = CACHE_DIR / "market-alpha-routing-dashboard.json"
FINANCE_INSPECT_SCRIPT = SCRIPT_DIR / "inspect-finance-mcp.js"
FINANCE_HTTP_CALL = TASK_SCRIPT_DIR / "finance-mcp-http-call.py"
GENERIC_MCP_RUNNER = TASK_SCRIPT_DIR / "mcp-direct-call-runner.js"

PRIORITY_MAP = {"primary": 1, "secondary": 2, "fallback": 3}
STATUS_SCORES = {"healthy": 20, "configured": 10, "degraded": -10, "missing": -40}
TASK_TYPE_ALIASES = {
    "market_data": {"market_data", "fundamentals", "microstructure", "derivatives"},
    "macro_data": {"macro_data", "market_data", "news"},
    "news": {"news", "web_search", "deep_research"},
    "web_search": {"web_search", "news", "deep_research"},
    "deep_research": {"deep_research", "web_search", "content_extraction", "academic"},
    "academic": {"academic", "web_search"},
    "fundamentals": {"fundamentals", "market_data"},
    "microstructure": {"microstructure", "market_data"},
    "derivatives": {"derivatives", "market_data"},
    "content_extraction": {"content_extraction", "site_intelligence", "web_search"},
}
CATEGORY_ALIASES = {
    "finance_news": {"finance_news", "hot_news_7x24", "webSearchPro", "tavily_search", "metaso_search"},
    "web_search": {"webSearchPro", "tavily_search", "metaso_search", "brave_web_search"},
    "deep_research": {"tavily_research", "tavily_search", "webSearchPro", "metaso_search"},
    "content_extraction": {"tavily_extract", "metaso_reader"},
}
ROUTE_CLASSIFICATION_SEEDS: dict[str, list[str]] = {
    "utility": ["time", "timestamp", "datetime", "clock", "date", "timezone", "时间", "时间戳"],
    "news": ["news", "headline", "breaking", "hot news", "资讯", "快讯", "新闻"],
    "web_search": ["search", "web", "browser", "query", "搜索", "检索"],
    "deep_research": ["research", "investigate", "analysis", "report", "深度研究", "研究"],
    "academic": ["paper", "pubmed", "openalex", "doi", "pmid", "citation", "abstract", "literature", "论文", "文献"],
    "content_extraction": ["extract", "reader", "markdown", "content", "正文", "提取"],
    "site_intelligence": ["crawl", "map", "sitemap", "site", "抓取", "站点"],
    "market_data": ["stock", "quote", "price", "index", "kline", "行情", "指数"],
    "macro_data": ["macro", "econ", "gdp", "cpi", "ppi", "rates", "yield", "宏观", "经济"],
    "fundamentals": ["earnings", "financial", "performance", "balance", "income", "财务", "基本面"],
    "microstructure": ["flow", "order", "block", "margin", "龙虎榜", "资金流", "成交"],
    "derivatives": ["option", "future", "bond", "greeks", "iv", "可转债", "期权", "期货"],
}
CATEGORY_CLASSIFICATION_SEEDS: dict[str, list[str]] = {
    "current_timestamp": ["timestamp", "datetime", "clock", "时间戳"],
    "finance_news": ["finance_news", "财经", "news", "headline"],
    "hot_news_7x24": ["7x24", "hot_news", "快讯"],
    "stock_data": ["stock", "quote", "ohlc", "kline", "price", "行情"],
    "stock_data_minutes": ["minute", "1min", "5min", "分钟"],
    "index_data": ["index", "指数"],
    "macro_econ": ["macro", "econ", "gdp", "cpi", "ppi", "pmi", "经济"],
    "fund_data": ["fund", "基金"],
    "money_flow": ["money_flow", "flow", "资金流"],
    "margin_trade": ["margin", "融资融券"],
    "block_trade": ["block", "大宗"],
    "dragon_tiger_inst": ["dragon", "tiger", "龙虎榜"],
    "convertible_bond": ["convertible", "bond", "可转债"],
}

FINANCE_TOOL_METADATA: dict[str, dict[str, Any]] = {
    "current_timestamp": {
        "route_type": "utility",
        "category": "current_timestamp",
        "markets": ["global"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "realtime",
    },
    "finance_news": {
        "route_type": "news",
        "category": "finance_news",
        "markets": ["cn", "us", "hk", "global"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "hot_news_7x24": {
        "route_type": "news",
        "category": "hot_news_7x24",
        "markets": ["cn", "us", "global"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "stock_data": {
        "route_type": "market_data",
        "category": "stock_data",
        "markets": [
            "cn",
            "us",
            "hk",
            "fx",
            "futures",
            "fund",
            "repo",
            "convertible_bond",
            "options",
            "crypto",
        ],
        "frequencies": ["daily"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "stock_data_minutes": {
        "route_type": "market_data",
        "category": "stock_data_minutes",
        "markets": ["cn", "crypto"],
        "frequencies": ["1MIN", "5MIN", "15MIN", "30MIN", "60MIN"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "index_data": {
        "route_type": "market_data",
        "category": "index_data",
        "markets": ["cn", "us", "hk", "global"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "csi_index_constituents": {
        "route_type": "market_data",
        "category": "csi_index_constituents",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "macro_econ": {
        "route_type": "macro_data",
        "category": "macro_econ",
        "markets": ["cn", "us", "hk", "global"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "company_performance": {
        "route_type": "fundamentals",
        "category": "company_performance",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "company_performance_hk": {
        "route_type": "fundamentals",
        "category": "company_performance_hk",
        "markets": ["hk"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "company_performance_us": {
        "route_type": "fundamentals",
        "category": "company_performance_us",
        "markets": ["us"],
        "languages": ["en"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "fund_data": {
        "route_type": "fundamentals",
        "category": "fund_data",
        "markets": ["cn", "us"],
        "languages": ["zh", "en"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "fund_manager_by_name": {
        "route_type": "fundamentals",
        "category": "fund_manager_by_name",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 2,
        "freshness_sla": "T+1",
    },
    "money_flow": {
        "route_type": "microstructure",
        "category": "money_flow",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+0",
    },
    "margin_trade": {
        "route_type": "microstructure",
        "category": "margin_trade",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "block_trade": {
        "route_type": "microstructure",
        "category": "block_trade",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "dragon_tiger_inst": {
        "route_type": "microstructure",
        "category": "dragon_tiger_inst",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
    },
    "convertible_bond": {
        "route_type": "derivatives",
        "category": "convertible_bond",
        "markets": ["cn"],
        "languages": ["zh"],
        "priority": 1,
        "freshness_sla": "T+1",
        "notes": ["基础可转债非行情数据"],
    },
}
EXPLICIT_TOOL_METADATA: dict[str, dict[str, dict[str, Any]]] = {
    "congress-gov-mcp-server": {
        "congress_search": {
            "route_type": "deep_research",
            "category": "congress_search",
            "languages": ["en"],
            "priority": 2,
            "freshness_sla": "T+0",
            "markets": [],
            "notes": ["Congress.gov collection search"],
        },
        "congress_getSubResource": {
            "route_type": "deep_research",
            "category": "congress_getSubResource",
            "languages": ["en"],
            "priority": 2,
            "freshness_sla": "T+0",
            "markets": [],
            "notes": ["Congress.gov sub-resource fetch"],
        },
    },
}

SERVER_FALLBACK_TOOLS: dict[str, list[dict[str, Any]]] = {
    "zhipu-web-search-sse": [
        {
            "name": "webSearchPro",
            "description": "智谱网页实时检索",
            "route_type": "web_search",
            "category": "webSearchPro",
            "languages": ["zh", "en"],
            "priority": 1,
            "freshness_sla": "T+0",
        }
    ],
    "brave-search-dev": [
        {
            "name": "brave_web_search",
            "description": "Brave 常规网页搜索",
            "route_type": "web_search",
            "category": "brave_web_search",
            "languages": ["zh", "en"],
            "priority": 2,
            "freshness_sla": "T+0",
        }
    ],
    "congress-gov-mcp-server": [
        {
            "name": "congress_search",
            "description": "Congress.gov 集合搜索/列表工具",
            "route_type": "deep_research",
            "category": "congress_search",
            "languages": ["en"],
            "priority": 2,
            "freshness_sla": "T+0",
        },
        {
            "name": "congress_getSubResource",
            "description": "Congress.gov 子资源拉取工具",
            "route_type": "deep_research",
            "category": "congress_getSubResource",
            "languages": ["en"],
            "priority": 3,
            "freshness_sla": "T+0",
        },
    ],
}

SERVER_HINTS: dict[str, dict[str, Any]] = {
    "finance-mcp-local": {"cost_tier": "free", "auth_required": True, "latency_sla_ms": 300},
    "tavily-mcp-local": {"cost_tier": "paid", "auth_required": True, "latency_sla_ms": 3000},
    "metaso-search-mcp": {"cost_tier": "paid", "auth_required": True, "latency_sla_ms": 1500},
    "zhipu-web-search-sse": {"cost_tier": "paid", "auth_required": True, "latency_sla_ms": 2000},
    "brave-search-dev": {"cost_tier": "free", "auth_required": True, "latency_sla_ms": 1000},
    "mcp-pubmed-llm-server": {"cost_tier": "free", "auth_required": False, "latency_sla_ms": 4000},
    "openalex-mcp-server": {"cost_tier": "free", "auth_required": False, "latency_sla_ms": 4000},
    "congress-gov-mcp-server": {"cost_tier": "free", "auth_required": True, "latency_sla_ms": 4000},
}

DEFAULT_ROUTING_RULES = {
    "market_data": {"primary": ["finance-mcp-local"], "fallback": []},
    "macro_data": {"primary": ["finance-mcp-local"], "fallback": ["zhipu-web-search-sse", "tavily-mcp-local"]},
    "news": {
        "primary": ["finance-mcp-local"],
        "fallback": ["zhipu-web-search-sse", "tavily-mcp-local", "metaso-search-mcp", "brave-search-dev"],
    },
    "web_search": {
        "primary": ["zhipu-web-search-sse", "tavily-mcp-local"],
        "fallback": ["metaso-search-mcp", "brave-search-dev"],
    },
    "deep_research": {
        "primary": ["tavily-mcp-local"],
        "fallback": [
            "zhipu-web-search-sse",
            "metaso-search-mcp",
            "openalex-mcp-server",
            "mcp-pubmed-llm-server",
            "congress-gov-mcp-server",
        ],
    },
    "academic": {
        "primary": ["openalex-mcp-server", "mcp-pubmed-llm-server"],
        "fallback": ["tavily-mcp-local", "zhipu-web-search-sse", "congress-gov-mcp-server"],
    },
    "content_extraction": {"primary": ["tavily-mcp-local", "metaso-search-mcp"], "fallback": []},
    "fundamentals": {"primary": ["finance-mcp-local"], "fallback": ["zhipu-web-search-sse"]},
    "microstructure": {"primary": ["finance-mcp-local"], "fallback": []},
    "derivatives": {"primary": ["finance-mcp-local"], "fallback": ["zhipu-web-search-sse"]},
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def rel_to_workspace(path: Path) -> str:
    return f"./{path.relative_to(WORKSPACE_DIR).as_posix()}"


def load_mcporter(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_transport(server_config: dict[str, Any]) -> str:
    if server_config.get("url"):
        return "sse"
    return str(server_config.get("transport") or server_config.get("type") or "stdio")


def resolve_entry_path(server_config: dict[str, Any]) -> Path | None:
    args = server_config.get("args") or []
    for raw in args:
        value = str(raw).strip()
        if not value:
            continue
        if value.startswith("/") or value.endswith((".js", ".mjs", ".cjs", ".ts")):
            return Path(value)
    return None


def command_exists(command: str | None) -> bool:
    if not command:
        return False
    if command.startswith("/"):
        return Path(command).exists()
    return shutil.which(command) is not None


def server_health(server_name: str, server_config: dict[str, Any], discovered_tools: int) -> dict[str, Any]:
    command = str(server_config.get("command") or "").strip()
    entry_path = resolve_entry_path(server_config)
    url = str(server_config.get("url") or "").strip()
    transport = detect_transport(server_config)
    status = "healthy"
    notes: list[str] = []

    if url:
        notes.append("remote endpoint configured")
        status = "configured"
    else:
        if command and not command_exists(command):
            status = "missing"
            notes.append(f"command missing: {command}")
        if entry_path and not entry_path.exists():
            status = "missing"
            notes.append(f"entry missing: {entry_path}")
        elif entry_path:
            notes.append("entry visible on filesystem")
        elif command == "npx":
            status = "configured"
            notes.append("package-based server; no local entry file to inspect")

    if discovered_tools == 0 and status not in {"missing"}:
        status = "degraded"
        notes.append("tool snapshot unavailable; using config-only discovery")

    if server_name == "brave-search-dev" and ((server_config.get("env") or {}).get("BRAVE_API_KEY") or "").strip():
        if status == "missing":
            status = "configured"
        notes.append("direct Brave Search API fallback available")

    return {
        "last_check_utc": iso_now(),
        "status": status,
        "transport": transport,
        "command": command,
        "entry_path": str(entry_path) if entry_path else "",
        "url": url,
        "notes": notes,
    }


def clean_description(text: str) -> str:
    normalized = text.replace("\\n", " ").replace("\\t", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def tokenize_identifier(value: str) -> list[str]:
    parts = re.split(r"[^a-zA-Z0-9]+", value.lower())
    return [part for part in parts if part]


def infer_schema_keys(input_schema: dict[str, Any] | None) -> list[str]:
    if not isinstance(input_schema, dict):
        return []
    properties = input_schema.get("properties")
    if not isinstance(properties, dict):
        return []
    return [str(key).strip().lower() for key in properties.keys() if str(key).strip()]


def contains_keyword(haystack: str, keyword: str) -> bool:
    needle = keyword.lower().strip()
    return bool(needle) and needle in haystack


def learned_keyword_library() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    route_map = {key: set(values) for key, values in ROUTE_CLASSIFICATION_SEEDS.items()}
    category_map = {key: set(values) for key, values in CATEGORY_CLASSIFICATION_SEEDS.items()}
    for tool_name, metadata in FINANCE_TOOL_METADATA.items():
        route_type = str(metadata.get("route_type") or "utility")
        category = str(metadata.get("category") or tool_name)
        name_tokens = tokenize_identifier(tool_name)
        route_map.setdefault(route_type, set()).update(name_tokens)
        category_map.setdefault(category, set()).update(name_tokens)
    for server_tools in SERVER_FALLBACK_TOOLS.values():
        for item in server_tools:
            route_type = str(item.get("route_type") or "utility")
            category = str(item.get("category") or item.get("name") or "unknown")
            name_tokens = tokenize_identifier(str(item.get("name") or ""))
            route_map.setdefault(route_type, set()).update(name_tokens)
            category_map.setdefault(category, set()).update(name_tokens)
    return route_map, category_map


def generic_tool_pairs(source_text: str) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    patterns = [
        re.compile(r'name\s*:\s*"([^"]+)"\s*,\s*description\s*:\s*"((?:\\"|[^"])+)"', re.S),
        re.compile(r"name\s*:\s*'([^']+)'\s*,\s*description\s*:\s*'((?:\\\\'|[^'])+)'", re.S),
        re.compile(r'name\s*:\s*"([^"]+)"\s*,\s*description\s*:\s*`([\s\S]*?)`', re.S),
        re.compile(r"name\s*:\s*'([^']+)'\s*,\s*description\s*:\s*`([\s\S]*?)`", re.S),
    ]
    for pattern in patterns:
        for name, desc in pattern.findall(source_text):
            cleaned_name = str(name).strip()
            cleaned_desc = clean_description(str(desc))
            if cleaned_name and cleaned_desc:
                matches.append((cleaned_name, cleaned_desc))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for name, desc in matches:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, desc))
    return unique


def extract_list_tools_slice(entry_path: Path) -> str:
    text = entry_path.read_text(encoding="utf-8", errors="ignore")
    start = text.find("ListToolsRequestSchema")
    if start == -1:
        start = 0
    end = len(text)
    for marker in [
        "setRequestHandler(CallToolRequestSchema",
        "server.setRequestHandler(CallToolRequestSchema",
        "this.server.setRequestHandler(CallToolRequestSchema",
        "server.connect(",
        "await server.connect",
    ]:
        candidate = text.find(marker, start + 1)
        if candidate != -1:
            end = min(end, candidate)
    return text[start:end]


def resolve_tool_source_path(entry_path: Path) -> Path:
    if not entry_path.exists():
        return entry_path
    text = entry_path.read_text(encoding="utf-8", errors="ignore")
    if "ListToolsRequestSchema" in text:
        return entry_path
    match = re.search(r"""import\((['"])(\./[^'"]+)\1\)""", text)
    if not match:
        match = re.search(r"""require\((['"])(\./[^'"]+)\1\)""", text)
    if match:
        candidate = (entry_path.parent / match.group(2)).resolve()
        if candidate.exists():
            return candidate
    return entry_path


def discover_tools_from_js(entry_path: Path) -> list[dict[str, str]]:
    source_path = resolve_tool_source_path(entry_path)
    if not source_path.exists():
        return []
    snippet = extract_list_tools_slice(source_path)
    return [{"name": name, "description": desc} for name, desc in generic_tool_pairs(snippet)]


def discover_finance_tools(config_path: Path) -> list[dict[str, str]]:
    if not FINANCE_INSPECT_SCRIPT.exists():
        return []
    proc = subprocess.run(
        ["node", str(FINANCE_INSPECT_SCRIPT), "--config", str(config_path), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    payload = json.loads(proc.stdout)
    return [
        {
            "name": str(item.get("name") or "").strip(),
            "description": clean_description(str(item.get("description") or "")),
        }
        for item in payload.get("tools", [])
        if str(item.get("name") or "").strip()
    ]


def try_live_list_tools(server_name: str) -> tuple[list[dict[str, Any]], str]:
    in_container = Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()
    attempts = [False] if in_container else [True, False]
    for use_container in attempts:
        proc = run_generic_mcp_call(
            action="list-tools",
            server=server_name,
            use_container=use_container,
        )
        if proc.returncode != 0:
            continue
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            continue
        tools = []
        for item in ((payload.get("result") or {}).get("tools") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            tools.append(
                {
                    "name": name,
                    "description": clean_description(str(item.get("description") or "")),
                    "input_schema": item.get("inputSchema") if isinstance(item.get("inputSchema"), dict) else {},
                }
            )
        if tools:
            return tools, "live-list-tools"
    return [], ""


def normalize_language(language: str | None) -> str:
    if not language:
        return ""
    lowered = language.lower()
    if "-" in lowered:
        lowered = lowered.split("-", 1)[0]
    return lowered


def market_matches(task_market: str | None, tool_markets: list[str]) -> bool:
    if not task_market or not tool_markets:
        return True
    market = task_market.strip().lower()
    tool_set = {item.lower() for item in tool_markets}
    if "global" in tool_set:
        return True
    if market == "multi":
        return True
    aliases = {market}
    if market in {"cn", "us", "hk"}:
        aliases.add("equity")
    if market in {"fund", "options", "futures", "crypto", "convertible_bond"}:
        aliases.add(market)
    return bool(tool_set & aliases)


def freshness_matches(requirement: str | None, tool_sla: str | None) -> bool:
    if not requirement or not tool_sla:
        return True
    normalized = requirement.upper()
    offered = tool_sla.upper()
    if normalized in {"REALTIME", "T+0"}:
        return offered in {"REALTIME", "T+0"}
    if normalized == "T+1":
        return offered in {"REALTIME", "T+0", "T+1"}
    return True


def auto_classify_tool(
    *,
    tool_name: str,
    description: str,
    input_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_keywords, category_keywords = learned_keyword_library()
    schema_keys = infer_schema_keys(input_schema)
    haystack_parts = [tool_name.lower(), description.lower(), " ".join(schema_keys)]
    haystack = " ".join(part for part in haystack_parts if part).strip()

    route_scores: dict[str, int] = {}
    route_reasons: dict[str, list[str]] = {}
    for route_type, keywords in route_keywords.items():
        score = 0
        reasons: list[str] = []
        for keyword in sorted(keywords):
            if contains_keyword(haystack, keyword):
                score += 2 if len(keyword) > 3 else 1
                reasons.append(f"keyword:{keyword}")
        route_scores[route_type] = score
        route_reasons[route_type] = reasons

    schema_key_set = set(schema_keys)
    if {"query", "q"} & schema_key_set:
        route_scores["web_search"] = route_scores.get("web_search", 0) + 3
        route_reasons.setdefault("web_search", []).append("schema:query")
    if {"search_query"} & schema_key_set:
        route_scores["web_search"] = route_scores.get("web_search", 0) + 4
        route_reasons.setdefault("web_search", []).append("schema:search_query")
    if {"url", "urls"} & schema_key_set:
        route_scores["content_extraction"] = route_scores.get("content_extraction", 0) + 3
        route_reasons.setdefault("content_extraction", []).append("schema:url")
    if {"code", "symbol", "market_type"} & schema_key_set:
        route_scores["market_data"] = route_scores.get("market_data", 0) + 3
        route_reasons.setdefault("market_data", []).append("schema:code")
    if {"pmid", "doi", "work_id", "work_ids"} & schema_key_set:
        route_scores["academic"] = route_scores.get("academic", 0) + 4
        route_reasons.setdefault("academic", []).append("schema:paper-id")
    if {"input"} & schema_key_set and "research" in haystack:
        route_scores["deep_research"] = route_scores.get("deep_research", 0) + 4
        route_reasons.setdefault("deep_research", []).append("schema:input+research")

    ranked_routes = sorted(route_scores.items(), key=lambda item: (-item[1], item[0]))
    best_route, best_score = ranked_routes[0] if ranked_routes else ("utility", 0)
    if best_score <= 0:
        best_route = "utility"

    category_scores: dict[str, int] = {}
    category_reasons: dict[str, list[str]] = {}
    for category, keywords in category_keywords.items():
        score = 0
        reasons: list[str] = []
        for keyword in sorted(keywords):
            if contains_keyword(haystack, keyword):
                score += 2 if len(keyword) > 3 else 1
                reasons.append(f"keyword:{keyword}")
        category_scores[category] = score
        category_reasons[category] = reasons
    ranked_categories = sorted(category_scores.items(), key=lambda item: (-item[1], item[0]))
    best_category, best_category_score = ranked_categories[0] if ranked_categories else (tool_name, 0)
    if best_category_score <= 0:
        best_category = tool_name

    if best_score >= 8:
        confidence = 0.95
    elif best_score >= 5:
        confidence = 0.8
    elif best_score >= 3:
        confidence = 0.65
    elif best_score >= 1:
        confidence = 0.55
    else:
        confidence = 0.3

    reasons = route_reasons.get(best_route, []) + category_reasons.get(best_category, [])
    return {
        "route_type": best_route,
        "category": best_category,
        "priority": 2 if confidence >= 0.8 else 3,
        "freshness_sla": "unknown" if best_route == "utility" else ("T+1" if best_route == "academic" else "T+0"),
        "languages": ["en"] if best_route == "academic" else [],
        "markets": [],
        "notes": [],
        "classification_source": "auto-learned",
        "classification_confidence": confidence,
        "classification_reasons": reasons,
        "needs_review": confidence < 0.75,
    }


def normalize_tool_record(
    server_name: str,
    tool_name: str,
    description: str,
    source: str,
    input_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    explicit_server_tools = EXPLICIT_TOOL_METADATA.get(server_name, {})
    if tool_name in explicit_server_tools:
        metadata = dict(explicit_server_tools[tool_name])
        metadata.setdefault("notes", [])
        return {
            "name": tool_name,
            "description": description,
            "source": source,
            "input_schema": input_schema or {},
            "classification_source": "explicit",
            "classification_confidence": 1.0,
            "classification_reasons": [f"explicit-{server_name}-map"],
            "needs_review": False,
            **metadata,
        }

    if server_name == "finance-mcp-local" and tool_name in FINANCE_TOOL_METADATA:
        metadata = dict(FINANCE_TOOL_METADATA[tool_name])
        metadata.setdefault("notes", [])
        return {
            "name": tool_name,
            "description": description,
            "source": source,
            "input_schema": input_schema or {},
            "classification_source": "explicit",
            "classification_confidence": 1.0,
            "classification_reasons": ["explicit-finance-map"],
            "needs_review": False,
            **metadata,
        }

    fallback_tools = {item["name"]: item for item in SERVER_FALLBACK_TOOLS.get(server_name, []) if "name" in item}
    if tool_name in fallback_tools:
        metadata = dict(fallback_tools[tool_name])
        metadata.setdefault("markets", [])
        metadata.setdefault("languages", [])
        metadata.setdefault("notes", [])
        return {
            "name": tool_name,
            "description": description or str(metadata.get("description") or "").strip(),
            "source": source,
            "input_schema": input_schema or {},
            "classification_source": "explicit",
            "classification_confidence": 1.0,
            "classification_reasons": ["explicit-server-fallback-map"],
            "needs_review": False,
            **metadata,
        }

    name_lower = tool_name.lower()
    route_type = "utility"
    priority = 3
    category = tool_name
    languages: list[str] = []
    markets: list[str] = []
    notes: list[str] = []
    freshness_sla = "unknown"

    if server_name in {"openalex-mcp-server", "mcp-pubmed-llm-server"} or name_lower.startswith(("openalex_", "pubmed_")):
        route_type = "academic"
        priority = 4
        languages = ["en"]
        freshness_sla = "T+1"
        if "quick_search" in name_lower or name_lower.endswith("_search") or name_lower == "openalex_search":
            priority = 1
        elif "get_work" in name_lower or "get_details" in name_lower or "extract_key_info" in name_lower:
            priority = 2
        elif "batch_get" in name_lower or "cross_reference" in name_lower:
            priority = 3
        elif any(token in name_lower for token in ["cache", "system", "status", "download", "fulltext"]):
            priority = 9
    elif "research" in name_lower:
        route_type = "deep_research"
        priority = 1
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "extract" in name_lower or "reader" in name_lower:
        route_type = "content_extraction"
        priority = 2
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "crawl" in name_lower or "map" in name_lower:
        route_type = "site_intelligence"
        priority = 3
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "search" in name_lower or tool_name == "webSearchPro":
        route_type = "web_search"
        priority = 2
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "news" in name_lower:
        route_type = "news"
        priority = 2
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "macro" in name_lower:
        route_type = "macro_data"
        priority = 2
        languages = ["zh", "en"]
        freshness_sla = "T+0"
    elif "stock" in name_lower or "index" in name_lower:
        route_type = "market_data"
        priority = 2
        languages = ["zh", "en"]
        markets = ["cn", "us", "hk", "global"]
        freshness_sla = "T+0"

    if server_name == "metaso-search-mcp":
        languages = ["zh", "en"]
    if server_name == "zhipu-web-search-sse":
        languages = ["zh", "en"]
    if server_name == "tavily-mcp-local":
        languages = ["en", "zh"]
    if tool_name == "webSearchPro":
        priority = 1

    base_record = {
        "name": tool_name,
        "description": description,
        "source": source,
        "input_schema": input_schema or {},
    }
    auto = auto_classify_tool(tool_name=tool_name, description=description, input_schema=input_schema or {})
    if auto.get("classification_confidence", 0) >= 0.55:
        route_type = str(auto.get("route_type") or route_type)
        category = str(auto.get("category") or category)
        priority = int(auto.get("priority", priority))
        freshness_sla = str(auto.get("freshness_sla") or freshness_sla)
        auto_languages = list(auto.get("languages") or [])
        if auto_languages:
            languages = auto_languages
        auto_markets = list(auto.get("markets") or [])
        if auto_markets:
            markets = auto_markets
        notes.extend(list(auto.get("notes") or []))
        base_record.update(
            {
                "classification_source": auto.get("classification_source", "auto-learned"),
                "classification_confidence": auto.get("classification_confidence", 0.5),
                "classification_reasons": auto.get("classification_reasons", []),
                "needs_review": bool(auto.get("needs_review", False)),
            }
        )
    else:
        base_record.update(
            {
                "classification_source": "heuristic-fallback",
                "classification_confidence": auto.get("classification_confidence", 0.3),
                "classification_reasons": auto.get("classification_reasons", []),
                "needs_review": True,
            }
        )

    return {
        **base_record,
        "route_type": route_type,
        "category": category,
        "markets": markets,
        "languages": languages,
        "priority": priority,
        "freshness_sla": freshness_sla,
        "notes": notes,
    }


def aggregate_capabilities(tools: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for tool in tools:
        route_type = str(tool.get("route_type") or "utility")
        category = str(tool.get("category") or tool.get("name") or "unknown")
        grouped[route_type][category] = {
            key: value
            for key, value in tool.items()
            if key not in {"route_type", "category", "source"}
        }
    return {route_type: categories for route_type, categories in grouped.items()}


def build_server_record(server_name: str, server_config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    entry_path = resolve_entry_path(server_config)
    discovery_mode = "fallback"
    raw_tools: list[dict[str, Any]] = []

    if server_name == "finance-mcp-local":
        raw_tools = discover_finance_tools(config_path)
        discovery_mode = "inspect-finance-mcp.js" if raw_tools else "fallback-map"
    else:
        raw_tools, live_mode = try_live_list_tools(server_name)
        if raw_tools:
            discovery_mode = live_mode
    if not raw_tools and entry_path and entry_path.exists():
        raw_tools = discover_tools_from_js(entry_path)
        discovery_mode = "source-parse" if raw_tools else "fallback-map"

    if not raw_tools:
        raw_tools = [
            {
                "name": str(item.get("name") or "").strip(),
                "description": clean_description(str(item.get("description") or "")),
            }
            for item in SERVER_FALLBACK_TOOLS.get(server_name, [])
            if str(item.get("name") or "").strip()
        ]

    tools = [
        normalize_tool_record(
            server_name=server_name,
            tool_name=str(item.get("name") or "").strip(),
            description=clean_description(str(item.get("description") or "")),
            source=discovery_mode,
            input_schema=item.get("input_schema") if isinstance(item.get("input_schema"), dict) else {},
        )
        for item in raw_tools
        if str(item.get("name") or "").strip()
    ]

    hints = dict(SERVER_HINTS.get(server_name, {}))
    env_keys = sorted((server_config.get("env") or {}).keys())
    metadata = {
        "transport": detect_transport(server_config),
        "command": str(server_config.get("command") or ""),
        "entry_path": str(entry_path) if entry_path else "",
        "url": str(server_config.get("url") or ""),
        "configured_env_keys": env_keys,
        "cost_tier": hints.get("cost_tier", "unknown"),
        "auth_required": bool(hints.get("auth_required", bool(env_keys))),
        "latency_sla_ms": int(hints.get("latency_sla_ms", 0) or 0),
        "tool_count": len(tools),
        "discovery_mode": discovery_mode,
    }
    health = server_health(server_name, server_config, len(tools))
    status = "active" if tools else health["status"]
    return {
        "type": "mcp",
        "status": status,
        "health_check": health,
        "metadata": metadata,
        "tools": tools,
        "capabilities": aggregate_capabilities(tools),
    }


def gateway_container_name() -> str | None:
    proc = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    for candidate in ["repo-openclaw-gateway-1", "openclaw-gateway-1"]:
        if candidate in names:
            return candidate
    return None


def run_finance_http_call(tool: str, arguments: dict[str, Any], use_container: bool) -> subprocess.CompletedProcess[str]:
    payload = json.dumps(arguments, ensure_ascii=False)
    if use_container:
        container = gateway_container_name()
        if not container:
            raise SystemExit("OpenClaw gateway container not found for FinanceMCP fallback")
        command = (
            "cd /home/node/.openclaw/workspace && "
            f"python3 scripts/finance-mcp-http-call.py --tool {json.dumps(tool, ensure_ascii=False)} "
            f"--args-json {json.dumps(payload, ensure_ascii=False)}"
        )
        return subprocess.run(
            ["docker", "exec", container, "bash", "-lc", command],
            capture_output=True,
            text=True,
            check=False,
        )

    return subprocess.run(
        [
            "python3",
            str(FINANCE_HTTP_CALL),
            "--tool",
            tool,
            "--args-json",
            payload,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def run_generic_mcp_call(
    *,
    action: str,
    server: str,
    tool: str = "",
    arguments: dict[str, Any] | None = None,
    use_container: bool,
) -> subprocess.CompletedProcess[str]:
    payload = json.dumps(arguments or {}, ensure_ascii=False)
    if use_container:
        container = gateway_container_name()
        if not container:
            raise SystemExit("OpenClaw gateway container not found for MCP runtime call")
        cmd = [
            "docker",
            "exec",
            container,
            "node",
            "/home/node/.openclaw/workspace/scripts/mcp-direct-call-runner.js",
            "--action",
            action,
            "--server",
            server,
        ]
        if tool:
            cmd.extend(["--tool", tool])
        cmd.extend(["--args-json", payload])
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", exc.stderr or "timeout")

    cmd = [
        "node",
        str(GENERIC_MCP_RUNNER),
        "--action",
        action,
        "--server",
        server,
    ]
    if tool:
        cmd.extend(["--tool", tool])
    cmd.extend(["--config", str(CONFIG_PATH), "--args-json", payload])
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", exc.stderr or "timeout")


def build_routing_rules(discovered_servers: set[str]) -> dict[str, dict[str, list[str]]]:
    rules: dict[str, dict[str, list[str]]] = {}
    for task_type, lanes in DEFAULT_ROUTING_RULES.items():
        filtered = {
            lane: [server for server in servers if server in discovered_servers]
            for lane, servers in lanes.items()
        }
        if filtered["primary"] or filtered["fallback"]:
            rules[task_type] = filtered
    return rules


def discover_registry(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = load_mcporter(config_path)
    servers = config.get("mcpServers") or {}
    discovered: dict[str, Any] = {}
    for server_name, server_config in servers.items():
        if not isinstance(server_config, dict):
            continue
        discovered[server_name] = build_server_record(server_name, server_config, config_path)
    return {
        "version": "0.1.0",
        "generated_at_utc": iso_now(),
        "config_path": str(config_path),
        "workspace_path": str(WORKSPACE_DIR),
        "tools": discovered,
        "routing_rules": build_routing_rules(set(discovered)),
    }


class MCPAdapter(ABC):
    def __init__(self, server_name: str, server_record: dict[str, Any]):
        self.server_name = server_name
        self.server_record = server_record
        self.tools = {tool["name"]: tool for tool in server_record.get("tools", [])}

    @abstractmethod
    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        return dict(self.server_record.get("health_check", {}))

    def capabilities(self) -> dict[str, Any]:
        return dict(self.server_record.get("capabilities", {}))


class FinanceMCPAdapter(MCPAdapter):
    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool not in self.tools:
            raise SystemExit(f"Unsupported FinanceMCP tool: {tool}")
        if not FINANCE_HTTP_CALL.exists():
            raise SystemExit(f"FinanceMCP HTTP bridge not found: {FINANCE_HTTP_CALL}")

        proc = run_finance_http_call(tool, arguments, use_container=False)
        if proc.returncode != 0 and not Path("/.dockerenv").exists():
            proc = run_finance_http_call(tool, arguments, use_container=True)
        if proc.returncode != 0:
            raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or "FinanceMCP call failed")
        return json.loads(proc.stdout)


class BraveSearchAdapter(MCPAdapter):
    def _api_key(self) -> str:
        config = load_mcporter(CONFIG_PATH)
        server = (config.get("mcpServers") or {}).get(self.server_name) or {}
        api_key = str(((server.get("env") or {}).get("BRAVE_API_KEY") or "")).strip()
        if not api_key:
            raise SystemExit("BRAVE_API_KEY missing for brave-search-dev")
        return api_key

    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool != "brave_web_search":
            raise SystemExit(f"Unsupported Brave tool: {tool}")
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise SystemExit("brave_web_search requires query")
        count = int(arguments.get("count") or 5)
        count = min(max(count, 1), 20)
        url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
            {
                "q": query,
                "count": count,
            }
        )
        request = urllib.request.Request(
            url,
            headers={"X-Subscription-Token": self._api_key()},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload


class GenericMCPAdapter(MCPAdapter):
    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool not in self.tools:
            raise SystemExit(f"Unsupported MCP tool for {self.server_name}: {tool}")
        if not GENERIC_MCP_RUNNER.exists():
            raise SystemExit(f"Generic MCP runner not found: {GENERIC_MCP_RUNNER}")

        in_container = Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()
        attempts = [False] if in_container else [True, False]

        last_proc: subprocess.CompletedProcess[str] | None = None
        for use_container in attempts:
            proc = run_generic_mcp_call(
                action="call",
                server=self.server_name,
                tool=tool,
                arguments=arguments,
                use_container=use_container,
            )
            last_proc = proc
            if proc.returncode == 0:
                payload = json.loads(proc.stdout)
                return payload.get("result") or {}

        raise SystemExit(
            (last_proc.stderr.strip() if last_proc else "")
            or (last_proc.stdout.strip() if last_proc else "")
            or f"MCP call failed for {self.server_name}:{tool}"
        )


def adapter_for(server_name: str, registry: dict[str, Any]) -> MCPAdapter:
    server_record = (registry.get("tools") or {}).get(server_name)
    if not server_record:
        raise SystemExit(f"Server not found in registry: {server_name}")
    if server_name == "finance-mcp-local":
        return FinanceMCPAdapter(server_name, server_record)
    if server_name == "brave-search-dev":
        return BraveSearchAdapter(server_name, server_record)
    return GenericMCPAdapter(server_name, server_record)


def task_type_matches(request_type: str, tool_route_type: str) -> bool:
    compatible = TASK_TYPE_ALIASES.get(request_type, {request_type})
    return tool_route_type in compatible


def category_matches(request_category: str | None, tool_category: str) -> bool:
    if not request_category:
        return True
    if request_category == tool_category:
        return True
    return tool_category in CATEGORY_ALIASES.get(request_category, set())


class SmartRouter:
    def __init__(self, registry: dict[str, Any], log_path: Path | None = None):
        self.registry = registry
        self.log_path = log_path or DEFAULT_ACCESS_LOG_PATH

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        request_type = str(request.get("type") or "web_search")
        request_category = str(request.get("category") or "").strip() or None
        request_market = str(request.get("market") or "").strip() or None
        request_language = normalize_language(str(request.get("language") or "").strip() or None)
        request_freshness = str(request.get("freshness") or "").strip() or None
        rules = self.registry.get("routing_rules") or {}
        lane_order = rules.get(request_type) or {"primary": [], "fallback": []}
        ordered_servers = [
            ("primary", server_name) for server_name in lane_order.get("primary", [])
        ] + [("fallback", server_name) for server_name in lane_order.get("fallback", [])]
        if not ordered_servers:
            ordered_servers = [
                ("fallback", server_name) for server_name in (self.registry.get("tools") or {}).keys()
            ]

        candidates: list[dict[str, Any]] = []
        for order_index, (lane, server_name) in enumerate(ordered_servers):
            server_record = (self.registry.get("tools") or {}).get(server_name)
            if not server_record:
                continue
            status = str(((server_record.get("health_check") or {}).get("status") or "degraded")).strip()
            if status == "missing":
                continue
            for tool in server_record.get("tools", []):
                route_type = str(tool.get("route_type") or "utility")
                tool_category = str(tool.get("category") or tool.get("name") or "")
                if not task_type_matches(request_type, route_type):
                    continue
                if not category_matches(request_category, tool_category):
                    continue
                if not market_matches(request_market, list(tool.get("markets") or [])):
                    continue
                languages = [normalize_language(item) for item in list(tool.get("languages") or []) if item]
                if request_language and languages and request_language not in languages:
                    continue
                if not freshness_matches(request_freshness, str(tool.get("freshness_sla") or "")):
                    continue
                priority = int(tool.get("priority", 3) or 3)
                lane_score = 70 if lane == "primary" else 40
                score = lane_score
                score += max(0, 20 - (priority - 1) * 5)
                score += STATUS_SCORES.get(status, 0)
                if request_category and request_category == tool_category:
                    score += 20
                elif request_category and tool_category in CATEGORY_ALIASES.get(request_category, set()):
                    score += 8
                if request_market and list(tool.get("markets") or []):
                    score += 8
                if request_language and languages:
                    score += 6
                candidates.append(
                    {
                        "server": server_name,
                        "tool": tool["name"],
                        "lane": lane,
                        "score": score,
                        "status": status,
                        "route_type": route_type,
                        "category": tool_category,
                        "markets": tool.get("markets", []),
                        "languages": tool.get("languages", []),
                        "freshness_sla": tool.get("freshness_sla", ""),
                        "description": tool.get("description", ""),
                        "reason": self._reason(lane, tool, request),
                        "order_index": order_index,
                    }
                )
        candidates.sort(
            key=lambda item: (
                -int(item["score"]),
                int(item.get("order_index", 999)),
                str(item["server"]),
                str(item["tool"]),
            )
        )
        result = {
            "generated_at_utc": iso_now(),
            "request": request,
            "candidates": candidates,
        }
        self._log_event(
            event_type="route",
            payload={
                "request": request,
                "candidate_count": len(candidates),
                "candidates": candidates[:5],
            },
        )
        return result

    def _reason(self, lane: str, tool: dict[str, Any], request: dict[str, Any]) -> str:
        fragments = [f"{lane} lane"]
        route_type = str(tool.get("route_type") or "")
        if route_type:
            fragments.append(f"route={route_type}")
        markets = list(tool.get("markets") or [])
        if request.get("market") and markets:
            fragments.append(f"markets={','.join(markets)}")
        freshness = str(tool.get("freshness_sla") or "").strip()
        if freshness:
            fragments.append(f"freshness={freshness}")
        return "; ".join(fragments)

    def build_arguments(self, request: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = dict(overrides or {})
        category = str(request.get("category") or "").strip()
        symbol = str(request.get("symbol") or request.get("code") or "").strip()
        market = str(request.get("market") or "").strip()
        query = str(request.get("query") or request.get("objective") or "").strip()
        limit = request.get("limit")

        if category in {"stock_data", "stock_data_minutes", "money_flow", "margin_trade", "block_trade", "dragon_tiger_inst"}:
            if symbol and "code" not in arguments:
                arguments["code"] = symbol
            if market and "market_type" not in arguments:
                arguments["market_type"] = market
        elif category == "finance_news":
            if query and "query" not in arguments:
                arguments["query"] = query
            if isinstance(limit, int) and "limit" not in arguments:
                arguments["limit"] = limit
        elif category == "macro_econ":
            indicator = str(request.get("indicator") or "").strip()
            if indicator and "indicator" not in arguments:
                arguments["indicator"] = indicator
        elif category == "fund_data":
            if symbol and "code" not in arguments:
                arguments["code"] = symbol
        elif category == "current_timestamp":
            pass

        return arguments

    def _candidate_arguments(
        self,
        candidate: dict[str, Any],
        request: dict[str, Any],
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        arguments = self.build_arguments(request, overrides)
        tool = str(candidate.get("tool") or "")
        query = str(
            request.get("query")
            or request.get("objective")
            or request.get("prompt")
            or ""
        ).strip()
        limit = request.get("limit")
        if not isinstance(limit, int):
            limit = 5

        if tool == "webSearchPro":
            arguments.setdefault("search_query", query)
            arguments.setdefault("count", limit)
        elif tool == "congress_search":
            arguments.setdefault("collection", str(request.get("collection") or "bill"))
            filters = request.get("filters") if isinstance(request.get("filters"), dict) else {}
            if filters:
                arguments.setdefault("filters", filters)
            query_like = str(request.get("query") or "").strip()
            if query_like:
                arguments.setdefault("query", query_like)
            arguments.setdefault("limit", limit)
        elif tool == "congress_getSubResource":
            parent_uri = str(request.get("parentUri") or request.get("parent_uri") or "").strip()
            sub_resource = str(request.get("subResource") or request.get("sub_resource") or "").strip()
            if parent_uri:
                arguments.setdefault("parentUri", parent_uri)
            if sub_resource:
                arguments.setdefault("subResource", sub_resource)
            arguments.setdefault("limit", limit)
        elif tool == "tavily_search":
            arguments.setdefault("query", query)
            arguments.setdefault("max_results", limit)
            arguments.setdefault("search_depth", str(request.get("search_depth") or "basic"))
        elif tool == "tavily_research":
            arguments.setdefault("input", query)
            arguments.setdefault("model", str(request.get("model") or request.get("depth") or "mini"))
        elif tool == "tavily_extract":
            urls = request.get("urls") if isinstance(request.get("urls"), list) else []
            if urls:
                arguments.setdefault("urls", urls)
            arguments.setdefault("format", str(request.get("format") or "markdown"))
        elif tool == "metaso_search":
            arguments.setdefault("q", query)
            arguments.setdefault("scope", str(request.get("scope") or "webpage"))
            arguments.setdefault("size", limit)
        elif tool == "metaso_reader":
            url = str(request.get("url") or "").strip()
            if url:
                arguments.setdefault("url", url)
            arguments.setdefault("format", str(request.get("format") or "markdown"))
        elif tool == "openalex_search":
            arguments.setdefault("query", query)
            arguments.setdefault("max_results", limit)
        elif tool == "brave_web_search":
            arguments.setdefault("query", query)
            arguments.setdefault("count", limit)
        elif tool == "pubmed_quick_search":
            arguments.setdefault("query", query)
            arguments.setdefault("max_results", limit)
        elif tool == "pubmed_search":
            arguments.setdefault("query", query)
            arguments.setdefault("max_results", limit)
        elif tool == "finance_news":
            arguments.setdefault("query", query)
            arguments.setdefault("limit", limit)

        return arguments

    def build_execution_plan(
        self,
        request: dict[str, Any],
        arguments: dict[str, Any] | None = None,
        *,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        routed = self.route(request)
        attempts = []
        for candidate in routed.get("candidates", [])[:max_attempts]:
            built_arguments = self._candidate_arguments(candidate, request, arguments)
            attempts.append(
                {
                    "server": candidate.get("server"),
                    "tool": candidate.get("tool"),
                    "lane": candidate.get("lane"),
                    "status": "planned",
                    "arguments": built_arguments,
                }
            )
        return {
            "generated_at_utc": iso_now(),
            "request": request,
            "arguments": dict(arguments or {}),
            "attempts": attempts,
        }

    def execute(
        self,
        request: dict[str, Any],
        arguments: dict[str, Any] | None = None,
        *,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        plan = self.build_execution_plan(request, arguments, max_attempts=max_attempts)
        attempts: list[dict[str, Any]] = []
        result_payload: Any = None
        status = "blocked"
        error_message = ""

        for candidate in plan.get("attempts", []):
            server_name = str(candidate.get("server") or "")
            tool_name = str(candidate.get("tool") or "")
            try:
                adapter = adapter_for(server_name, self.registry)
            except SystemExit as exc:
                attempts.append(
                    {
                        **candidate,
                        "status": "unsupported",
                        "error": str(exc),
                    }
                )
                error_message = str(exc)
                continue

            try:
                result_payload = adapter.call(tool_name, dict(candidate.get("arguments") or {}))
                attempts.append({**candidate, "status": "success"})
                status = "success"
                error_message = ""
                break
            except BaseException as exc:  # pragma: no cover - runtime failure path
                compact_error = compact_error_text(exc)
                attempts.append(
                    {
                        **candidate,
                        "status": "failed",
                        "error": compact_error or str(exc),
                    }
                )
                error_message = compact_error or str(exc)
                status = "failed"

        response = {
            "generated_at_utc": iso_now(),
            "request": request,
            "arguments": plan.get("arguments", {}),
            "status": status,
            "attempts": attempts,
            "result": result_payload,
            "error": error_message,
        }
        self._log_event(event_type="execute", payload=response)
        return response

    def _log_event(self, event_type: str, payload: dict[str, Any]) -> None:
        append_jsonl(
            self.log_path,
            {
                "timestamp_utc": iso_now(),
                "event_type": event_type,
                **payload,
            },
        )


def default_language_for_market(market: str) -> str:
    if market in {"us"}:
        return "en"
    return "zh"


def preview_requests(
    *,
    market: str,
    style: str,
    instrument: str,
    horizon: str,
    alpha_mode: str,
    objective: str,
) -> list[dict[str, Any]]:
    language = default_language_for_market(market)
    tasks: list[dict[str, Any]] = [
        {
            "label": "headline-news",
            "type": "news",
            "category": "finance_news",
            "market": market,
            "language": language,
            "freshness": "T+0",
            "priority": "high",
            "objective": objective,
        },
        {
            "label": "deep-research",
            "type": "deep_research",
            "category": "deep_research",
            "market": market,
            "language": language,
            "freshness": "T+0",
            "priority": "normal",
            "objective": objective,
        },
    ]

    primary_category = "stock_data"
    if instrument == "fund" or market == "fund":
        primary_category = "fund_data"
    elif market == "options":
        primary_category = "options"
    elif market == "futures" or instrument == "commodity":
        primary_category = "stock_data"

    tasks.insert(
        0,
        {
            "label": "primary-market-data",
            "type": "market_data",
            "category": primary_category,
            "market": market,
            "language": language,
            "freshness": "T+0",
            "priority": "high",
            "horizon": horizon,
            "alpha_mode": alpha_mode,
            "objective": objective,
        },
    )

    if market in {"cn", "us", "hk", "multi", "futures"}:
        tasks.append(
            {
                "label": "macro-context",
                "type": "macro_data",
                "category": "macro_econ",
                "market": market,
                "language": language,
                "freshness": "T+0",
                "priority": "normal",
                "objective": objective,
            }
        )

    if style == "short" and market in {"cn", "crypto"}:
        tasks.insert(
            1,
            {
                "label": "intraday-market-data",
                "type": "market_data",
                "category": "stock_data_minutes",
                "market": market,
                "language": language,
                "freshness": "T+0",
                "priority": "high",
                "horizon": horizon,
                "alpha_mode": alpha_mode,
                "objective": objective,
            },
        )

    if market == "cn":
        tasks.append(
            {
                "label": "microstructure",
                "type": "microstructure",
                "category": "money_flow",
                "market": market,
                "language": language,
                "freshness": "T+0",
                "priority": "normal",
                "objective": objective,
            }
        )

    return tasks


def registry_summary_lines(registry: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for server_name, info in sorted((registry.get("tools") or {}).items()):
        status = str((info.get("health_check") or {}).get("status") or info.get("status") or "unknown")
        tools = [tool.get("name") for tool in info.get("tools", [])[:5] if tool.get("name")]
        tool_text = ", ".join(tools) if tools else "no tools"
        lines.append(f"- {server_name}: status={status}; tools={tool_text}")
    return lines


def render_selection_prompt(registry: dict[str, Any], request: dict[str, Any]) -> str:
    lines = [
        "# Data Source Selection Prompt",
        "",
        "你是 market-alpha 的数据源选择器。先读可用注册表，再为当前任务选择最稳妥的数据源顺序。",
        "",
        "## Task Request",
        "",
        json.dumps(request, ensure_ascii=False, indent=2),
        "",
        "## Registry Summary",
        "",
    ]
    lines.extend(registry_summary_lines(registry) or ["- No registry entries available."])
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "1. 优先选择 request type 对应的 primary route。",
            "2. 若 primary route 与 market / freshness / language 不匹配，再考虑 fallback。",
            "3. 不要猜不存在的 MCP tool 名称。",
            "4. 如果没有可执行 route，输出 BLOCKED，并说明缺什么适配器或数据源。",
            "",
            "## Output Format",
            "",
            "1. 选中的 primary route",
            "2. fallback route",
            "3. 选择理由",
            "4. 缺口与降级策略",
        ]
    )
    return "\n".join(lines)


def render_orchestration_prompt(plan: dict[str, Any]) -> str:
    lines = [
        "# Data Fetch Orchestration Prompt",
        "",
        "你是 market-alpha 的数据获取编排器。按照给定计划依次尝试数据源，并在失败时切换 fallback。",
        "",
        "## Execution Plan",
        "",
        json.dumps(plan, ensure_ascii=False, indent=2),
        "",
        "## Rules",
        "",
        "1. 严格按 attempts 顺序执行。",
        "2. 每次失败都要记录失败原因、失败源、是否降级。",
        "3. 成功后立即停止后续 attempts，并把结果落到 task-local 文件。",
        "4. 如果所有 attempts 都失败，输出 NOT_EXECUTABLE，并列出缺失数据和已尝试路径。",
        "",
        "## Output Format",
        "",
        "1. execution status",
        "2. selected source",
        "3. failure trail",
        "4. normalized result summary",
        "5. next-step recommendation",
        "",
    ]
    return "\n".join(lines)


def compute_health_report(
    registry: dict[str, Any],
    *,
    probe_finance: bool = False,
) -> dict[str, Any]:
    tools = registry.get("tools") or {}
    summary = {
        "total_servers": len(tools),
        "healthy": 0,
        "configured": 0,
        "degraded": 0,
        "missing": 0,
    }
    alerts: list[str] = []
    servers: dict[str, Any] = {}

    for server_name, info in sorted(tools.items()):
        health = info.get("health_check") or {}
        status = str(health.get("status") or info.get("status") or "unknown")
        if status in summary:
            summary[status] += 1
        elif info.get("tools"):
            summary["healthy"] += 1
        if status in {"degraded", "missing"}:
            alerts.append(f"{server_name}: {status}")
        servers[server_name] = {
            "status": status,
            "tool_count": len(info.get("tools") or []),
            "transport": info.get("metadata", {}).get("transport", ""),
            "discovery_mode": info.get("metadata", {}).get("discovery_mode", ""),
            "notes": list(health.get("notes") or []),
        }
        for tool in info.get("tools") or []:
            if tool.get("needs_review"):
                alerts.append(f"{server_name}:{tool.get('name')}: classification-needs-review")

    finance_probe: dict[str, Any] = {"status": "skipped"}
    if probe_finance and "finance-mcp-local" in tools:
        try:
            adapter = adapter_for("finance-mcp-local", registry)
            adapter.call("current_timestamp", {})
            finance_probe = {"status": "success"}
        except Exception as exc:  # pragma: no cover - runtime-only
            finance_probe = {"status": "failed", "error": str(exc)}
            alerts.append(f"finance runtime probe failed: {exc}")

    route_coverage: dict[str, dict[str, int]] = {}
    for task_type, lanes in (registry.get("routing_rules") or {}).items():
        route_coverage[task_type] = {
            "primary": len(lanes.get("primary") or []),
            "fallback": len(lanes.get("fallback") or []),
        }
        if route_coverage[task_type]["primary"] == 0:
            alerts.append(f"{task_type}: no primary route configured")

    return {
        "generated_at_utc": iso_now(),
        "summary": summary,
        "alerts": alerts,
        "servers": servers,
        "route_coverage": route_coverage,
        "finance_probe": finance_probe,
    }


def compute_dashboard(
    registry: dict[str, Any],
    access_log_path: Path = DEFAULT_ACCESS_LOG_PATH,
) -> dict[str, Any]:
    rows = read_jsonl(access_log_path)
    totals = {"route": 0, "execute": 0}
    success = 0
    failure = 0
    unsupported = 0
    by_server: dict[str, dict[str, int]] = defaultdict(lambda: {"route_hits": 0, "execute_success": 0, "execute_failed": 0})

    for row in rows:
        event_type = str(row.get("event_type") or "")
        if event_type in totals:
            totals[event_type] += 1
        if event_type == "route":
            for candidate in row.get("candidates") or []:
                server = str(candidate.get("server") or "")
                if server:
                    by_server[server]["route_hits"] += 1
        elif event_type == "execute":
            status = str(row.get("status") or "")
            if status == "success":
                success += 1
            elif status == "failed":
                failure += 1
            elif status == "blocked":
                unsupported += 1
            for attempt in row.get("attempts") or []:
                server = str(attempt.get("server") or "")
                attempt_status = str(attempt.get("status") or "")
                if not server:
                    continue
                if attempt_status == "success":
                    by_server[server]["execute_success"] += 1
                elif attempt_status in {"failed", "unsupported"}:
                    by_server[server]["execute_failed"] += 1

    alerts: list[str] = []
    for server_name, info in (registry.get("tools") or {}).items():
        health_status = str((info.get("health_check") or {}).get("status") or info.get("status") or "")
        if health_status in {"degraded", "missing"}:
            alerts.append(f"{server_name}: health={health_status}")

    return {
        "generated_at_utc": iso_now(),
        "log_path": str(access_log_path),
        "totals": totals,
        "execution": {
            "success": success,
            "failed": failure,
            "blocked": unsupported,
        },
        "by_server": dict(sorted(by_server.items())),
        "alerts": alerts,
    }


def compute_classification_audit(registry: dict[str, Any]) -> dict[str, Any]:
    tools = registry.get("tools") or {}
    items: list[dict[str, Any]] = []
    summary = {
        "explicit": 0,
        "auto_learned": 0,
        "heuristic_fallback": 0,
        "needs_review": 0,
        "total_tools": 0,
    }
    for server_name, info in sorted(tools.items()):
        for tool in info.get("tools") or []:
            summary["total_tools"] += 1
            source = str(tool.get("classification_source") or "heuristic-fallback").replace("-", "_")
            if source in {"auto_learned", "heuristic_fallback", "explicit"}:
                summary[source] += 1
            else:
                summary["heuristic_fallback"] += 1
            if tool.get("needs_review"):
                summary["needs_review"] += 1
            items.append(
                {
                    "server": server_name,
                    "tool": tool.get("name"),
                    "route_type": tool.get("route_type"),
                    "category": tool.get("category"),
                    "classification_source": tool.get("classification_source"),
                    "classification_confidence": tool.get("classification_confidence"),
                    "needs_review": tool.get("needs_review"),
                    "classification_reasons": tool.get("classification_reasons") or [],
                }
            )
    return {
        "generated_at_utc": iso_now(),
        "summary": summary,
        "items": items,
    }


def render_alerts_markdown(health_report: dict[str, Any], dashboard: dict[str, Any]) -> str:
    merged_alerts: list[str] = []
    for source in [health_report.get("alerts") or [], dashboard.get("alerts") or []]:
        for item in source:
            if item not in merged_alerts:
                merged_alerts.append(item)
    lines = [
        "# Data Layer Alerts",
        "",
        f"- Generated at: `{iso_now()}`",
        f"- Health summary: `{json.dumps(health_report.get('summary', {}), ensure_ascii=False)}`",
        f"- Dashboard totals: `{json.dumps(dashboard.get('totals', {}), ensure_ascii=False)}`",
        "",
        "## Alerts",
        "",
    ]
    if merged_alerts:
        lines.extend([f"- {item}" for item in merged_alerts])
    else:
        lines.append("- No active alerts.")
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "- 优先修复 `missing` 或 `degraded` 的 primary route server。",
            "- 如果 execute-task 失败，先看 access-log.jsonl 的最近一条 execute 事件。",
            "- 对于 finance 任务，优先保证 FinanceMCP 可调用，再考虑搜索型 fallback。",
        ]
    )
    return "\n".join(lines)


def write_alert_bundle(base_dir: Path, health_report: dict[str, Any], dashboard: dict[str, Any]) -> tuple[Path, Path]:
    alerts_json = base_dir / "alerts.json"
    alerts_md = base_dir / "alerts.md"
    payload = {
        "generated_at_utc": iso_now(),
        "health_alerts": health_report.get("alerts") or [],
        "dashboard_alerts": dashboard.get("alerts") or [],
    }
    write_json(alerts_json, payload)
    write_text(alerts_md, render_alerts_markdown(health_report, dashboard))
    return alerts_json, alerts_md


def compact_error_text(raw: Any) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except Exception:
        return text
    if isinstance(payload, dict):
        direct_error = str(payload.get("error") or "").strip()
        if direct_error:
            if direct_error.startswith("{") or direct_error.startswith("["):
                nested = compact_error_text(direct_error)
                if nested and nested != direct_error:
                    return nested
            return direct_error
        result = payload.get("result")
        if isinstance(result, dict):
            for item in result.get("content") or []:
                if isinstance(item, dict) and str(item.get("text") or "").strip():
                    return str(item.get("text")).strip()
    return text


def build_task_readme(task_dir: Path) -> str:
    return f"""# Dynamic Data Layer Snapshot

## Files

- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "tool-registry.json")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "router-preview.json")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "access-log.jsonl")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "health-report.json")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "routing-dashboard.json")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "alerts.md")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "classification-audit.json")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "source-selection-prompt.md")}`
- `{rel_to_workspace(task_dir / "reports" / "data-layer" / "fetch-orchestration-prompt.md")}`

## Purpose

- `tool-registry.json`: 当前 workspace MCP 配置与源码快照解析出的统一注册表
- `router-preview.json`: 基于 task 市场/风格/标的推导出的默认路由候选
- `access-log.jsonl`: task 级路由/执行访问日志
- `health-report.json`: 数据源健康与覆盖体检
- `routing-dashboard.json`: 路由/执行统计看板
- `alerts.md`: 当前 health/dashboard 告警摘要
- `classification-audit.json`: 新工具自动分类结果、置信度与待复核项
- `source-selection-prompt.md`: LLM 数据源选择 prompt 模板
- `fetch-orchestration-prompt.md`: LLM 数据获取编排 prompt 模板

## Manual Commands

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py discover

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py route \\
  --task-json '{{"type":"market_data","category":"stock_data","market":"cn","freshness":"T+0"}}'

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py execute-task \\
  --task-json '{{"type":"utility","category":"current_timestamp"}}' \\
  --args-json '{{}}'
```
"""


def top_route_snapshot(preview: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for item in preview.get("requests", []):
        request = item.get("request") or {}
        candidates = item.get("candidates") or []
        snapshot.append(
            {
                "label": str(request.get("label") or request.get("type") or "route"),
                "type": str(request.get("type") or ""),
                "category": str(request.get("category") or ""),
                "top_candidates": [
                    {
                        "server": str(candidate.get("server") or ""),
                        "tool": str(candidate.get("tool") or ""),
                        "lane": str(candidate.get("lane") or ""),
                    }
                    for candidate in candidates[:3]
                ],
            }
        )
    return snapshot


def build_data_layer_context(
    *,
    task_dir: Path,
    registry_path: Path,
    task_registry_path: Path,
    preview_path: Path,
    preview: dict[str, Any],
    market: str,
    style: str,
    instrument: str,
    horizon: str,
    alpha_mode: str,
) -> dict[str, Any]:
    return {
        "updated_at_utc": iso_now(),
        "registry_path": rel_to_workspace(registry_path),
        "task_registry_path": rel_to_workspace(task_registry_path),
        "router_preview_path": rel_to_workspace(preview_path),
        "route_snapshot": top_route_snapshot(preview),
        "market_profile": {
            "market": market,
            "style": style,
            "instrument": instrument,
            "horizon": horizon,
            "alpha_mode": alpha_mode,
            "task_path": rel_to_workspace(task_dir),
        },
    }


def resolve_task_log_path(task_slug: str | None) -> Path | None:
    if not task_slug:
        return None
    try:
        task_dir = task_session.resolve_task_dir(task_slug=task_slug, prefer_active=True)
    except SystemExit:
        return None
    bridge = read_json(task_dir / "skill-bridge.json", {})
    data_layer = bridge.get("data_layer") if isinstance(bridge, dict) else {}
    if isinstance(data_layer, dict):
        access_log_path = str(data_layer.get("access_log_path") or "").strip()
        if access_log_path.startswith("./"):
            return WORKSPACE_DIR / access_log_path[2:]
    candidate = task_dir / "reports" / "data-layer" / "access-log.jsonl"
    return candidate


def replace_or_append_marked_block(text: str, marker_key: str, block: str) -> str:
    start = f"<!-- {marker_key}:start -->"
    end = f"<!-- {marker_key}:end -->"
    wrapped = "\n".join([start, block.rstrip(), end]).strip()
    pattern = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end), re.M)
    if pattern.search(text):
        return pattern.sub(wrapped, text).rstrip() + "\n"
    base = text.rstrip()
    if base:
        return base + "\n\n" + wrapped + "\n"
    return wrapped + "\n"


def render_capsule_data_layer_block(context: dict[str, Any]) -> str:
    lines = [
        "## Dynamic Data Layer",
        "",
        "- Router preview: "
        + f"`{context.get('router_preview_path', '')}`",
        "- Tool registry: "
        + f"`{context.get('task_registry_path', context.get('registry_path', ''))}`",
        "- Rule: 优先使用 router preview 的 primary route；只有失败或数据不匹配时才降级到 fallback。",
        "",
        "### Route Snapshot",
        "",
    ]
    for item in context.get("route_snapshot") or []:
        label = str(item.get("label") or "route")
        candidates = item.get("top_candidates") or []
        if candidates:
            rendered = ", ".join(f"{candidate['server']}->{candidate['tool']}" for candidate in candidates)
            lines.append(f"- `{label}`: {rendered}")
        else:
            lines.append(f"- `{label}`: no candidate discovered")
    return "\n".join(lines)


def render_skill_brief_data_layer_block(context: dict[str, Any]) -> str:
    lines = [
        "## Dynamic Data Layer",
        "",
        "- 先读 task-local `reports/data-layer/router-preview.json`，再决定 MCP 工具顺序。",
        "- 不要在 market-alpha 任务里凭印象猜工具名；优先遵守注册表和路由快照。",
        "- 如果 primary route 失败，再切 fallback，并把原因写回 task-local 研究文件。",
        f"- Router preview: `{context.get('router_preview_path', '')}`",
        f"- Tool registry: `{context.get('task_registry_path', context.get('registry_path', ''))}`",
        "",
        "### Preferred Routes",
        "",
    ]
    for item in context.get("route_snapshot") or []:
        label = str(item.get("label") or "route")
        candidates = item.get("top_candidates") or []
        if candidates:
            rendered = ", ".join(f"{candidate['server']}->{candidate['tool']}" for candidate in candidates)
            lines.append(f"- `{label}`: {rendered}")
        else:
            lines.append(f"- `{label}`: no candidate discovered")
    return "\n".join(lines)


def ensure_market_alpha_capsules(
    *,
    task_dir: Path,
    objective: str,
    market: str,
    style: str,
    instrument: str,
    horizon: str,
    alpha_mode: str,
    data_layer_context: dict[str, Any],
) -> None:
    capsules_dir = task_dir / "capsules"
    capsules_dir.mkdir(parents=True, exist_ok=True)
    capsule_json = capsules_dir / "task-capsule.json"
    capsule_md = capsules_dir / "task-capsule.md"
    skill_brief = capsules_dir / "skill-brief.md"

    capsule_payload = read_json(capsule_json, {})
    if not capsule_payload:
        capsule_payload = {
            "skill": "market-alpha-orchestrator",
            "task_dir": str(task_dir),
            "objective": objective or "TBD",
            "deliverable": "market-alpha research plan, routing context, and executable task artifacts",
            "scope": f"market={market}; style={style}; instrument={instrument}; horizon={horizon}; alpha_mode={alpha_mode}",
            "constraints": [
                "FinanceMCP and task-local router preview take precedence over freeform MCP guessing.",
                "Quant claims require task-local scripts and output files.",
            ],
            "sources": [
                rel_to_workspace(task_dir / "reports" / "data-layer" / "tool-registry.json"),
                rel_to_workspace(task_dir / "reports" / "data-layer" / "router-preview.json"),
            ],
            "notes": ["Minimal market-alpha capsule created by dynamic data layer bootstrap."],
        }
    capsule_payload["data_layer"] = data_layer_context
    capsule_payload["market_alpha"] = {
        "market": market,
        "style": style,
        "instrument": instrument,
        "horizon": horizon,
        "alpha_mode": alpha_mode,
    }
    capsule_payload["updated_at_utc"] = iso_now()
    write_json(capsule_json, capsule_payload)

    if not capsule_md.exists():
        lines = [
            "# Task capsule",
            "",
            "- Skill: `market-alpha-orchestrator`",
            f"- Task dir: `{task_dir}`",
            f"- Objective: {objective or 'TBD'}",
            "- Deliverable: market-alpha research plan, routing context, and executable task artifacts",
            f"- Scope: market={market}; style={style}; instrument={instrument}; horizon={horizon}; alpha_mode={alpha_mode}",
            "",
            "## Constraints",
            "",
            "- FinanceMCP and task-local router preview take precedence over freeform MCP guessing.",
            "- Quant claims require task-local scripts and output files.",
            "",
            "## Primary sources / paths",
            "",
            f"- `{rel_to_workspace(task_dir / 'reports' / 'data-layer' / 'tool-registry.json')}`",
            f"- `{rel_to_workspace(task_dir / 'reports' / 'data-layer' / 'router-preview.json')}`",
            f"- Reports directory: `{task_dir / 'reports'}`",
            "",
            "## Working notes",
            "",
            "- Minimal market-alpha capsule created by dynamic data layer bootstrap.",
            "",
            "## Read budget",
            "",
            "- Shared capsule only.",
            "- Skill brief only.",
            "- Task-local route preview before MCP selection.",
        ]
        write_text(capsule_md, "\n".join(lines))

    capsule_md_text = capsule_md.read_text(encoding="utf-8") if capsule_md.exists() else ""
    write_text(
        capsule_md,
        replace_or_append_marked_block(
            capsule_md_text,
            "market-alpha-data-layer",
            render_capsule_data_layer_block(data_layer_context),
        ),
    )

    if not skill_brief.exists():
        lines = [
            "# market-alpha skill brief",
            "",
            "## Load order",
            "",
            "1. `capsules/task-capsule.md`",
            "2. This file",
            "3. Any task-local brief generated later",
            "",
            "Do not guess data tools when the task-local data layer snapshot already exists.",
            "",
            "## Token guardrails",
            "",
            "- Prefer task-local route preview over workspace-wide re-discovery.",
            "- Use task-local quant/data artifacts before freeform narrative.",
        ]
        write_text(skill_brief, "\n".join(lines))

    skill_brief_text = skill_brief.read_text(encoding="utf-8") if skill_brief.exists() else ""
    write_text(
        skill_brief,
        replace_or_append_marked_block(
            skill_brief_text,
            "market-alpha-data-layer",
            render_skill_brief_data_layer_block(data_layer_context),
        ),
    )


def sync_task_context(
    *,
    task_dir: Path,
    objective: str,
    market: str,
    style: str,
    instrument: str,
    horizon: str,
    alpha_mode: str,
    data_layer_context: dict[str, Any],
) -> None:
    bridge_path = task_dir / "skill-bridge.json"
    bridge = read_json(bridge_path, {})
    bridge.setdefault("task_dir", str(task_dir))
    bridge.setdefault("task_slug", task_dir.name.split("-", 3)[-1] if "-" in task_dir.name else task_dir.name)
    bridge.setdefault("skill", bridge.get("skill", "market-alpha-orchestrator"))
    bridge["data_layer"] = data_layer_context
    bridge["market_alpha"] = {
        "market": market,
        "style": style,
        "instrument": instrument,
        "horizon": horizon,
        "alpha_mode": alpha_mode,
        "objective": objective,
    }
    bridge["updated_at_utc"] = iso_now()
    write_json(bridge_path, bridge)

    ensure_market_alpha_capsules(
        task_dir=task_dir,
        objective=objective,
        market=market,
        style=style,
        instrument=instrument,
        horizon=horizon,
        alpha_mode=alpha_mode,
        data_layer_context=data_layer_context,
    )


def register_task_artifact(task_dir: Path, path: Path, kind: str, note: str) -> None:
    payload = {
        "timestamp_utc": iso_now(),
        "path": str(path.resolve()),
        "kind": kind,
        "note": note,
    }
    task_session.append_jsonl(task_dir / "artifacts.jsonl", payload)


def bootstrap_task_snapshot(
    *,
    task_slug: str,
    market: str,
    style: str,
    instrument: str,
    horizon: str,
    alpha_mode: str,
    objective: str,
    registry_path: Path,
) -> dict[str, Any]:
    registry = discover_registry(CONFIG_PATH)
    write_json(registry_path, registry)

    task_dir = task_session.resolve_task_dir(task_slug=task_slug, prefer_active=True)
    out_dir = task_dir / "reports" / "data-layer"
    registry_copy = out_dir / "tool-registry.json"
    preview_path = out_dir / "router-preview.json"
    access_log_path = out_dir / "access-log.jsonl"
    health_report_path = out_dir / "health-report.json"
    dashboard_path = out_dir / "routing-dashboard.json"
    alerts_json_path = out_dir / "alerts.json"
    alerts_md_path = out_dir / "alerts.md"
    classification_audit_path = out_dir / "classification-audit.json"
    selection_prompt_path = out_dir / "source-selection-prompt.md"
    orchestration_prompt_path = out_dir / "fetch-orchestration-prompt.md"
    readme_path = out_dir / "README.md"

    write_json(registry_copy, registry)

    router = SmartRouter(registry, log_path=access_log_path)
    requests = preview_requests(
        market=market,
        style=style,
        instrument=instrument,
        horizon=horizon,
        alpha_mode=alpha_mode,
        objective=objective,
    )
    preview = {
        "generated_at_utc": iso_now(),
        "task_slug": task_slug,
        "task_path": rel_to_workspace(task_dir),
        "requests": [router.route(request) for request in requests],
    }
    write_json(preview_path, preview)
    health_report = compute_health_report(registry, probe_finance=False)
    dashboard = compute_dashboard(registry, access_log_path=access_log_path)
    classification_audit = compute_classification_audit(registry)
    write_json(health_report_path, health_report)
    write_json(dashboard_path, dashboard)
    write_json(classification_audit_path, classification_audit)
    bundle_json_path, bundle_md_path = write_alert_bundle(out_dir, health_report, dashboard)
    first_request = (preview.get("requests") or [{}])[0]
    selection_request = (first_request.get("request") or {}) if isinstance(first_request, dict) else {}
    write_text(selection_prompt_path, render_selection_prompt(registry, selection_request))
    orchestration_plan = router.build_execution_plan(selection_request or {"type": "market_data"}, {})
    write_text(orchestration_prompt_path, render_orchestration_prompt(orchestration_plan))
    write_text(readme_path, build_task_readme(task_dir))

    data_layer_context = build_data_layer_context(
        task_dir=task_dir,
        registry_path=registry_path,
        task_registry_path=registry_copy,
        preview_path=preview_path,
        preview=preview,
        market=market,
        style=style,
        instrument=instrument,
        horizon=horizon,
        alpha_mode=alpha_mode,
    )
    data_layer_context["health_report_path"] = rel_to_workspace(health_report_path)
    data_layer_context["dashboard_path"] = rel_to_workspace(dashboard_path)
    data_layer_context["alerts_json_path"] = rel_to_workspace(bundle_json_path)
    data_layer_context["alerts_md_path"] = rel_to_workspace(bundle_md_path)
    data_layer_context["classification_audit_path"] = rel_to_workspace(classification_audit_path)
    data_layer_context["access_log_path"] = rel_to_workspace(access_log_path)
    data_layer_context["selection_prompt_path"] = rel_to_workspace(selection_prompt_path)
    data_layer_context["orchestration_prompt_path"] = rel_to_workspace(orchestration_prompt_path)
    sync_task_context(
        task_dir=task_dir,
        objective=objective,
        market=market,
        style=style,
        instrument=instrument,
        horizon=horizon,
        alpha_mode=alpha_mode,
        data_layer_context=data_layer_context,
    )

    register_task_artifact(task_dir, registry_copy, "data-layer-registry", "dynamic data layer registry snapshot")
    register_task_artifact(task_dir, preview_path, "data-layer-router", "dynamic data layer router preview")
    register_task_artifact(task_dir, access_log_path, "data-layer-access-log", "dynamic data layer access log")
    register_task_artifact(task_dir, health_report_path, "data-layer-health", "dynamic data layer health report")
    register_task_artifact(task_dir, dashboard_path, "data-layer-dashboard", "dynamic data layer dashboard")
    register_task_artifact(task_dir, bundle_md_path, "data-layer-alerts", "dynamic data layer alert summary")
    register_task_artifact(task_dir, classification_audit_path, "data-layer-classification", "dynamic data layer classification audit")

    return {
        "task_dir": task_dir,
        "registry_path": registry_path,
        "task_registry_path": registry_copy,
        "preview_path": preview_path,
        "access_log_path": access_log_path,
        "health_report_path": health_report_path,
        "dashboard_path": dashboard_path,
        "readme_path": readme_path,
    }


def cmd_discover(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry_out) if args.registry_out else DEFAULT_REGISTRY_PATH
    registry = discover_registry(Path(args.config) if args.config else CONFIG_PATH)
    write_json(registry_path, registry)
    print("MARKET_ALPHA_DATA_REGISTRY_OK")
    print(f"REGISTRY_PATH={registry_path}")
    print(f"SERVER_COUNT={len(registry.get('tools', {}))}")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    request = json.loads(args.task_json)
    log_path = Path(args.log_path) if getattr(args, "log_path", None) else resolve_task_log_path(getattr(args, "task_slug", None)) or DEFAULT_ACCESS_LOG_PATH
    router = SmartRouter(registry, log_path=log_path)
    result = router.route(request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_plan_task(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    request = json.loads(args.task_json)
    overrides = json.loads(args.args_json) if args.args_json else {}
    log_path = Path(args.log_path) if args.log_path else resolve_task_log_path(getattr(args, "task_slug", None)) or DEFAULT_ACCESS_LOG_PATH
    router = SmartRouter(registry, log_path=log_path)
    result = router.build_execution_plan(request, overrides, max_attempts=args.max_attempts)
    if args.output:
        write_json(Path(args.output), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_execute_task(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    request = json.loads(args.task_json)
    overrides = json.loads(args.args_json) if args.args_json else {}
    log_path = Path(args.log_path) if args.log_path else resolve_task_log_path(getattr(args, "task_slug", None)) or DEFAULT_ACCESS_LOG_PATH
    router = SmartRouter(registry, log_path=log_path)
    result = router.execute(request, overrides, max_attempts=args.max_attempts)
    if args.output:
        write_json(Path(args.output), result)
    if args.task_slug:
        task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
        out_dir = task_dir / "reports" / "data-layer"
        dashboard = compute_dashboard(registry, access_log_path=log_path)
        health = compute_health_report(registry, probe_finance=False)
        write_json(out_dir / "routing-dashboard.json", dashboard)
        write_alert_bundle(out_dir, health, dashboard)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "success" else 1


def cmd_bootstrap_task(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry_out) if args.registry_out else DEFAULT_REGISTRY_PATH
    result = bootstrap_task_snapshot(
        task_slug=args.task_slug,
        market=args.market,
        style=args.style,
        instrument=args.instrument,
        horizon=args.horizon,
        alpha_mode=args.alpha_mode,
        objective=args.objective or "",
        registry_path=registry_path,
    )
    print("MARKET_ALPHA_DATA_LAYER_BOOTSTRAP_OK")
    print(f"TASK_DIR={result['task_dir']}")
    print(f"REGISTRY_PATH={result['registry_path']}")
    print(f"TASK_REGISTRY={result['task_registry_path']}")
    print(f"ROUTER_PREVIEW={result['preview_path']}")
    return 0


def cmd_call_finance(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    adapter = adapter_for("finance-mcp-local", registry)
    arguments = json.loads(args.args_json) if args.args_json else {}
    result = adapter.call(args.tool, arguments)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_healthcheck(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    report = compute_health_report(registry, probe_finance=args.probe_finance)
    output = Path(args.output) if args.output else DEFAULT_HEALTH_REPORT_PATH
    write_json(output, report)
    if args.task_slug:
        task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
        out_dir = task_dir / "reports" / "data-layer"
        dashboard = compute_dashboard(registry, access_log_path=resolve_task_log_path(args.task_slug) or DEFAULT_ACCESS_LOG_PATH)
        write_alert_bundle(out_dir, report, dashboard)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    log_path = Path(args.log_path) if args.log_path else resolve_task_log_path(getattr(args, "task_slug", None)) or DEFAULT_ACCESS_LOG_PATH
    dashboard = compute_dashboard(registry, access_log_path=log_path)
    output = Path(args.output) if args.output else DEFAULT_DASHBOARD_PATH
    write_json(output, dashboard)
    if args.task_slug:
        task_dir = task_session.resolve_task_dir(task_slug=args.task_slug, prefer_active=True)
        out_dir = task_dir / "reports" / "data-layer"
        health = compute_health_report(registry, probe_finance=False)
        write_alert_bundle(out_dir, health, dashboard)
    print(json.dumps(dashboard, ensure_ascii=False, indent=2))
    return 0


def cmd_prompt_template(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry) if args.registry else DEFAULT_REGISTRY_PATH
    registry = read_json(registry_path, {})
    if not registry:
        registry = discover_registry(CONFIG_PATH)
    request = json.loads(args.task_json)
    log_path = Path(args.log_path) if args.log_path else resolve_task_log_path(getattr(args, "task_slug", None)) or DEFAULT_ACCESS_LOG_PATH
    router = SmartRouter(registry, log_path=log_path)
    if args.kind == "selection":
        rendered = render_selection_prompt(registry, request)
    else:
        overrides = json.loads(args.args_json) if args.args_json else {}
        plan = router.build_execution_plan(request, overrides, max_attempts=args.max_attempts)
        rendered = render_orchestration_prompt(plan)
    if args.output:
        write_text(Path(args.output), rendered)
    print(rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dynamic data layer bootstrap for market-alpha")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--config", default=str(CONFIG_PATH))
    discover.add_argument("--registry-out")
    discover.set_defaults(func=cmd_discover)

    route = subparsers.add_parser("route")
    route.add_argument("--registry")
    route.add_argument("--task-slug")
    route.add_argument("--log-path")
    route.add_argument("--task-json", required=True, help='JSON object, e.g. {"type":"market_data","category":"stock_data"}')
    route.set_defaults(func=cmd_route)

    plan_task = subparsers.add_parser("plan-task")
    plan_task.add_argument("--registry")
    plan_task.add_argument("--task-slug")
    plan_task.add_argument("--log-path")
    plan_task.add_argument("--task-json", required=True)
    plan_task.add_argument("--args-json")
    plan_task.add_argument("--max-attempts", type=int, default=3)
    plan_task.add_argument("--output")
    plan_task.set_defaults(func=cmd_plan_task)

    execute_task = subparsers.add_parser("execute-task")
    execute_task.add_argument("--registry")
    execute_task.add_argument("--task-slug")
    execute_task.add_argument("--log-path")
    execute_task.add_argument("--task-json", required=True)
    execute_task.add_argument("--args-json")
    execute_task.add_argument("--max-attempts", type=int, default=3)
    execute_task.add_argument("--output")
    execute_task.set_defaults(func=cmd_execute_task)

    bootstrap_task = subparsers.add_parser("bootstrap-task")
    bootstrap_task.add_argument("--task-slug", required=True)
    bootstrap_task.add_argument("--market", default="multi")
    bootstrap_task.add_argument("--style", default="hybrid")
    bootstrap_task.add_argument("--instrument", default="equity")
    bootstrap_task.add_argument("--horizon", default="auto")
    bootstrap_task.add_argument("--alpha-mode", default="normal")
    bootstrap_task.add_argument("--objective", default="")
    bootstrap_task.add_argument("--registry-out")
    bootstrap_task.set_defaults(func=cmd_bootstrap_task)

    call_finance = subparsers.add_parser("call-finance")
    call_finance.add_argument("--registry")
    call_finance.add_argument("--tool", required=True)
    call_finance.add_argument("--args-json")
    call_finance.set_defaults(func=cmd_call_finance)

    healthcheck = subparsers.add_parser("healthcheck")
    healthcheck.add_argument("--registry")
    healthcheck.add_argument("--task-slug")
    healthcheck.add_argument("--probe-finance", action="store_true")
    healthcheck.add_argument("--output")
    healthcheck.set_defaults(func=cmd_healthcheck)

    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("--registry")
    dashboard.add_argument("--task-slug")
    dashboard.add_argument("--log-path")
    dashboard.add_argument("--output")
    dashboard.set_defaults(func=cmd_dashboard)

    prompt_template = subparsers.add_parser("prompt-template")
    prompt_template.add_argument("--kind", choices=["selection", "orchestration"], required=True)
    prompt_template.add_argument("--registry")
    prompt_template.add_argument("--task-slug")
    prompt_template.add_argument("--log-path")
    prompt_template.add_argument("--task-json", required=True)
    prompt_template.add_argument("--args-json")
    prompt_template.add_argument("--max-attempts", type=int, default=3)
    prompt_template.add_argument("--output")
    prompt_template.set_defaults(func=cmd_prompt_template)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
