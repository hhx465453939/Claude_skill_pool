#!/usr/bin/env python3
"""
Deep Research quant scratchpad template

用法：
1. 优先复制到 `workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/<topic>-analysis.py`
2. 只做当前研究需要的最小脚本改动
3. 运行后把关键输出写回报告，而不是只引用脚本运行成功
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_SCRIPT_DIR = Path(__file__).resolve().parent
if str(SKILL_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPT_DIR))

from research_quant_toolkit import simple_linear_regression


def main() -> None:
    # 示例数据：用你自己的 CSV / API 输出替换
    xs = [1, 2, 3, 4, 5]
    ys = [2.2, 2.8, 3.9, 5.1, 5.8]

    model = simple_linear_regression(xs, ys)
    print(json.dumps({
        "topic": "replace-me",
        "model": model,
        "notes": [
            "Replace xs/ys with your real cleaned data",
            "If you fetch external data, save a copy next to the task report or in the active task scratch/data directory.",
            "Write the interpretation back into the report with uncertainty notes",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
