#!/usr/bin/env python3
"""
搜索日志记录脚本 - 用于系统化记录搜索过程
帮助深度调研的 R 和 E 阶段
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

def create_search_template(topic: str) -> dict:
    """创建搜索模板"""
    return {
        "topic": topic,
        "start_time": datetime.now().isoformat(),
        "searches": [],
        "findings": [],
        "conflicts": [],
        "questions": [],
        "sources": []
    }

def add_search(log: dict, query: str, source_type: str, tool: str, result_count: int = 0, results: list = None):
    """添加搜索记录"""
    search_entry = {
        "query": query,
        "source_type": source_type,  # P1-P7
        "tool": tool,  # brave, pubmed, web_fetch 等
        "timestamp": datetime.now().isoformat(),
        "result_count": result_count,
        "results": results or []
    }
    log["searches"].append(search_entry)
    print(f"✓ 搜索已记录: {query} ({source_type})")

def add_finding(log: dict, description: str, source: str, reliability: str = "medium", evidence: str = ""):
    """添加发现"""
    finding_entry = {
        "description": description,
        "source": source,
        "reliability": reliability,  # high, medium, low
        "evidence": evidence,
        "timestamp": datetime.now().isoformat()
    }
    log["findings"].append(finding_entry)
    print(f"✓ 发现已记录: {description[:50]}...")

def add_conflict(log: dict, description: str, claim_a: str, source_a: str, claim_b: str, source_b: str):
    """添加冲突"""
    conflict_entry = {
        "description": description,
        "claim_a": claim_a,
        "source_a": source_a,
        "claim_b": claim_b,
        "source_b": source_b,
        "timestamp": datetime.now().isoformat()
    }
    log["conflicts"].append(conflict_entry)
    print(f"⚠ 冲突已记录: {description[:50]}...")

def add_question(log: dict, question: str, priority: str = "medium", status: str = "pending"):
    """添加问题"""
    question_entry = {
        "question": question,
        "priority": priority,  # high, medium, low
        "status": status,  # pending, researching, resolved
        "timestamp": datetime.now().isoformat()
    }
    log["questions"].append(question_entry)
    print(f"❓ 问题已记录: {question[:50]}...")

def save_log(log: dict, filepath: str):
    """保存日志到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"✓ 日志已保存: {filepath}")

def print_summary(log: dict):
    """打印摘要"""
    print(f"\n{'='*60}")
    print(f"研究主题: {log['topic']}")
    print(f"搜索次数: {len(log['searches'])}")
    print(f"发现数量: {len(log['findings'])}")
    print(f"冲突数量: {len(log['conflicts'])}")
    print(f"待解决问题: {len(log['questions'])}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description='深度调研搜索日志记录')
    parser.add_argument('--init', help='初始化新的搜索日志')
    parser.add_argument('--topic', required=True, help='研究主题')
    parser.add_argument('--add-search', nargs=4, 
                       metavar=('QUERY', 'SOURCE_TYPE', 'TOOL', 'COUNT'),
                       help='添加搜索 (查询 来源类型 工具 结果数)')
    parser.add_argument('--add-finding', nargs=4,
                       metavar=('DESC', 'SOURCE', 'RELIABILITY', 'EVIDENCE'),
                       help='添加发现 (描述 来源 可靠度 证据)')
    parser.add_argument('--add-conflict', nargs=5,
                       metavar=('DESC', 'CLAIM_A', 'SOURCE_A', 'CLAIM_B', 'SOURCE_B'),
                       help='添加冲突 (描述 说法A 来源A 说法B 来源B)')
    parser.add_argument('--add-question', nargs=3,
                       metavar=('QUESTION', 'PRIORITY', 'STATUS'),
                       help='添加问题 (问题 优先级 状态)')
    parser.add_argument('--save', help='保存日志文件（自动生成文件名）')
    parser.add_argument('--summary', help='打印日志摘要')
    
    args = parser.parse_args()
    
    # 文件路径
    log_dir = Path(f"~/research_logs/{args.topic.replace(' ', '_')}")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"research_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if args.init:
        # 初始化新日志
        log = create_search_template(args.topic)
        save_log(log, str(log_file))
        print(f"✓ 新的搜索日志已初始化: {log_file}")
    
    elif args.add_search:
        # 添加搜索到现有日志
        query, source_type, tool, count = args.add_search
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            add_search(log, query, source_type, tool, int(count))
            save_log(log, str(log_file))
            print_summary(log)
        else:
            print(f"❌ 日志文件不存在: {log_file}")
    
    elif args.add_finding:
        # 添加发现
        desc, source, reliability, evidence = args.add_finding
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            add_finding(log, desc, source, reliability, evidence)
            save_log(log, str(log_file))
            print_summary(log)
        else:
            print(f"❌ 日志文件不存在: {log_file}")
    
    elif args.add_conflict:
        # 添加冲突
        desc, claim_a, source_a, claim_b, source_b = args.add_conflict
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            add_conflict(log, desc, claim_a, source_a, claim_b, source_b)
            save_log(log, str(log_file))
            print_summary(log)
        else:
            print(f"❌ 日志文件不存在: {log_file}")
    
    elif args.add_question:
        # 添加问题
        question, priority, status = args.add_question
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            add_question(log, question, priority, status)
            save_log(log, str(log_file))
            print_summary(log)
        else:
            print(f"❌ 日志文件不存在: {log_file}")
    
    elif args.save:
        # 保存当前日志
        default_log = Path(f"~/research_logs/{args.topic.replace(' ', '_')}/current.json")
        if default_log.exists():
            import shutil
            shutil.copy(default_log, log_file)
            print(f"✓ 当前日志已保存到: {log_file}")
        else:
            print(f"❌ 当前日志不存在: {default_log}")
    
    elif args.summary:
        # 打印摘要
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            print_summary(log)
        else:
            print(f"❌ 日志文件不存在: {log_file}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
