#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const WORKSPACE_DIR = path.resolve(__dirname, "..", "..", "..");

function parseArgs(argv) {
  const args = {
    config: path.join(WORKSPACE_DIR, "config", "mcporter.json"),
    format: "md",
    write: "",
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--config") {
      args.config = argv[++i];
    } else if (arg === "--format") {
      args.format = argv[++i];
    } else if (arg === "--write") {
      args.write = argv[++i];
    } else if (arg === "--help" || arg === "-h") {
      console.log("Usage: inspect-finance-mcp.js [--config <path>] [--format md|json] [--write <path>]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function classify(name) {
  const groups = [
    { label: "time", values: ["current_timestamp"] },
    { label: "news", values: ["finance_news", "hot_news_7x24"] },
    { label: "market-data", values: ["stock_data", "stock_data_minutes", "index_data", "csi_index_constituents"] },
    { label: "macro", values: ["macro_econ"] },
    { label: "fundamentals", values: ["company_performance", "company_performance_hk", "company_performance_us", "fund_data", "fund_manager_by_name"] },
    { label: "flow-microstructure", values: ["money_flow", "margin_trade", "block_trade", "dragon_tiger_inst"] },
    { label: "special-instruments", values: ["convertible_bond"] },
  ];

  for (const group of groups) {
    if (group.values.includes(name)) {
      return group.label;
    }
  }
  return "other";
}

function extractTool(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  const exportObjectMatch = text.match(/export const [A-Za-z0-9_]+\s*=\s*{([\s\S]*?)};/m);
  const objectBody = exportObjectMatch ? exportObjectMatch[1] : text;
  const nameMatch = objectBody.match(/name:\s*["']([^"']+)["']/);
  const descMatch = objectBody.match(/description:\s*["']([^"']+)["']/);
  if (!nameMatch || !descMatch) {
    return null;
  }
  return {
    file: filePath,
    name: nameMatch[1],
    description: descMatch[1],
    group: classify(nameMatch[1]),
  };
}

function extractInlineTool(entryPath) {
  const text = fs.readFileSync(entryPath, "utf8");
  const blockMatch = text.match(/const timestampTool = {([\s\S]*?)\n};/m);
  if (!blockMatch) {
    return null;
  }
  const body = blockMatch[1];
  const nameMatch = body.match(/name:\s*["']([^"']+)["']/);
  const descMatch = body.match(/description:\s*["']([^"']+)["']/);
  if (!nameMatch || !descMatch) {
    return null;
  }
  return {
    file: entryPath,
    name: nameMatch[1],
    description: descMatch[1],
    group: classify(nameMatch[1]),
  };
}

function toMarkdown(items, configPath, entryPath) {
  const lines = [];
  lines.push("# FinanceMCP Capability Snapshot", "");
  lines.push(`- config: ${configPath}`);
  lines.push(`- entry: ${entryPath}`);
  lines.push(`- tool_count: ${items.length}`);
  lines.push("");

  const groups = Array.from(new Set(items.map((item) => item.group)));
  for (const group of groups) {
    lines.push(`## ${group}`, "");
    for (const item of items.filter((value) => value.group === group)) {
      lines.push(`- \`${item.name}\`: ${item.description}`);
    }
    lines.push("");
  }
  return `${lines.join("\n").trim()}\n`;
}

function main() {
  const args = parseArgs(process.argv);
  const config = JSON.parse(fs.readFileSync(args.config, "utf8"));
  const server = config?.mcpServers?.["finance-mcp-local"];
  if (!server || !Array.isArray(server.args) || server.args.length === 0) {
    throw new Error("finance-mcp-local not found in mcporter.json");
  }

  const entryPath = server.args[0];
  const toolsDir = path.join(path.dirname(entryPath), "tools");
  const files = fs.readdirSync(toolsDir)
    .filter((name) => name.endsWith(".js"))
    .map((name) => path.join(toolsDir, name))
    .sort();

  const items = files.map(extractTool).filter(Boolean);
  const inlineTool = extractInlineTool(entryPath);
  if (inlineTool) {
    items.unshift(inlineTool);
  }

  let output;
  if (args.format === "json") {
    output = `${JSON.stringify({
      config: args.config,
      entry: entryPath,
      tool_count: items.length,
      tools: items,
    }, null, 2)}\n`;
  } else if (args.format === "md") {
    output = toMarkdown(items, args.config, entryPath);
  } else {
    throw new Error(`Unsupported format: ${args.format}`);
  }

  if (args.write) {
    fs.writeFileSync(args.write, output, "utf8");
  }
  process.stdout.write(output);
}

try {
  main();
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
