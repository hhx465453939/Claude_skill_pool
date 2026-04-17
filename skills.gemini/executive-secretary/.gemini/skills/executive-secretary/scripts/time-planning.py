#!/usr/bin/env python3
"""
时间管理规划脚本 - Executive Secretary Skill

用于支持高级行政秘书进行时间规划和任务管理
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 优先级定义
PRIORITY_LEVELS = {
    "P0": "🔥 紧急重要（黄金时间）",
    "P1": "🔥 重要不紧急",
    "P2": "⚠️ 重要不紧急",
    "P3": "🔹 不重要但紧急",
    "P4": "🔹 不紧急不重要",
    "P5": "🌙 个人时间"
}

def print_task_summary(tasks: List[Dict]):
    """打印任务摘要"""
    print(f"\n📊 任务规划摘要")
    print(f"="*60)
    for i, task in enumerate(tasks, 1):
        priority_symbol = PRIORITY_LEVELS.get(task.get("priority", "P2"), "")
        print(f"{i}. [{task.get('id', 'N/A')}] {task.get('name', '未命名任务')}")
        print(f"   优先级: {priority_symbol}")
        print(f"   预计时间: {task.get('estimated_hours', 0)} 小时")
        print(f"   描述: {task.get('description', '无描述')[:50]}")
        print("-" * 60)

def eisenhower_matrix(tasks: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Eisenhower Matrix 分类
    
    象限 1 (Q1): 重要且紧急
    - 必须亲自处理
    - 高优先级
    - 黄金时间处理
    
    象限 2 (Q2): 重要但不紧急
    - 规划时间处理
    - 避免进入紧急状态
    - 防止拖延
    
    象限 3 (Q3): 不重要但紧急
    - 授权他人或快速决策
    - 不占用个人时间
    
    象限 4 (Q4): 不重要且不紧急
    - 消除或委派
    - 不安排专门时间
    - 避免时间浪费
    """
    q1 = [t for t in tasks if t.get("priority") in ["P0", "P1"]]
    q2 = [t for t in tasks if t.get("priority") == "P2"]
    q3 = [t for t in tasks if t.get("priority") == "P3"]
    q4 = [t for t in tasks if t.get("priority") in ["P4", "P5"]]
    
    return {
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4
    }

def create_schedule(tasks: List[Dict], start_date: Optional[str] = None):
    """
    创建日程安排
    
    时间块概念:
    - 黄金时间 (08:00-09:00): P0 任务
    - 深度工作 (09:00-12:00): P1 任务
    - 午休 (12:00-14:00): 个人时间
    - 常规工作 (14:00-17:00): P2 任务
    - 机动时间 (17:00-18:00): P1-P2 任务
    """
    
    schedule = {}
    
    # 时间块定义
    time_blocks = {
        "golden_morning": {"start": "08:00", "end": "09:00", "type": "P0"},
        "deep_work_morning": {"start": "09:00", "end": "12:00", "type": "P1"},
        "lunch_break": {"start": "12:00", "end": "14:00", "type": "P5"},
        "regular_work_afternoon": {"start": "14:00", "end": "17:00", "type": "P2"},
        "flexible": {"start": "17:00", "end": "18:00", "type": "P1-P2"},
        "evening_personal": {"start": "20:00", "end": "22:00", "type": "P5"}
    }
    
    # 将任务分配到时间块
    eisenhower_result = eisenhower_matrix(tasks)
    
    # 按优先级分配
    q1_tasks = eisenhower_result["Q1"]
    q2_tasks = eisenhower_result["Q2"]
    q3_tasks = eisenhower_result["Q3"]
    q4_tasks = eisenhower_result["Q4"]
    
    schedule["golden_morning"] = q1_tasks
    schedule["deep_work_morning"] = q2_tasks
    schedule["regular_work_afternoon"] = q2_tasks
    schedule["flexible"] = q1_tasks + q2_tasks
    
    return {
        "schedule": schedule,
        "time_blocks": time_blocks,
        "unassigned": q4_tasks  # P4 任务默认不安排
    }

def print_schedule(schedule_data: Dict):
    """打印日程安排"""
    print(f"\n📅 日程安排")
    print(f"="*60)
    
    schedule = schedule_data["schedule"]
    time_blocks = schedule_data["time_blocks"]
    
    # 打印每个时间块
    for block_name, block_info in time_blocks.items():
        print(f"\n🕰 {block_name.replace('_', ' ').title()} ({block_info['start']} - {block_info['end']})")
        tasks = schedule.get(block_name, [])
        
        if tasks:
            for i, task in enumerate(tasks, 1):
                priority_symbol = PRIORITY_LEVELS.get(task.get("priority", "P2"), "")
                print(f"  {i}. {task.get('name', '未命名')} {priority_symbol}")
                print(f"     地点: {task.get('location', 'TBD')}")
        else:
            print("  (自由时间)")
    
    # 打印未安排任务
    unassigned = schedule_data["unassigned"]
    if unassigned:
        print(f"\n🔹 未安排的任务 (P4)")
        for i, task in enumerate(unassigned, 1):
            print(f"  {i}. {task.get('name', '未命名')} - {task.get('description', '无描述')[:30]}")

def generate_emergency_response(tasks: List[Dict]]) -> Dict:
    """
    生成应急预案
    
    为突发状况准备多个时间安排方案
    预留缓冲时间应对关键任务
    建立任务优先级调整标准和触发条件
    """
    
    # 识别关键任务
    critical_tasks = [t for t in tasks if t.get("priority") in ["P0", "P1"]]
    
    # 缓冲时间
    buffer_times = {
        "critical": "10-20 分钟",
        "important": "30-60 分钟",
        "general": "1-2 小时"
    }
    
    return {
        "critical_tasks": critical_tasks,
        "buffer_times": buffer_times,
        "adjustment_triggers": [
            "新任务进入 P0-P1 优先级",
            "多个任务冲突时",
            "用户明确要求调整优先级"
        ]
    }

def print_emergency_plan(emergency_data: Dict):
    """打印应急预案"""
    print(f"\n🚨 应急预案")
    print(f"="*60)
    
    print(f"\n关键任务:")
    for task in emergency_data["critical_tasks"][:3]:  # 只显示前 3 个
        print(f"  • {task.get('name', '未命名')} - {task.get('description', '无描述')[:40]}")
    
    print(f"\n缓冲时间:")
    for level, time in emergency_data["buffer_times"].items():
        print(f"  • {level}: {time}")
    
    print(f"\n调整触发条件:")
    for i, trigger in enumerate(emergency_data["adjustment_triggers"], 1):
        print(f"  {i}. {trigger}")

def main():
    parser = argparse.ArgumentParser(description='Executive Secretary - 时间管理规划')
    parser.add_argument('--mode', choices=['plan', 'schedule', 'emergency'], 
                       default='plan', help='模式: plan=任务规划, schedule=日程安排, emergency=应急预案')
    parser.add_argument('--tasks', nargs='+', help='任务列表 (格式: "名称|优先级|预计时间|描述")')
    parser.add_argument('--date', help='开始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--print-summary', action='store_true', help='打印任务摘要')
    
    args = parser.parse_args()
    
    # 示例任务
    if args.mode == "plan" and not args.tasks:
        # 使用示例任务演示
        tasks = [
            {"id": "T001", "name": "项目A 立项报告", "priority": "P1", "estimated_hours": 4, 
             "description": "完成项目A的详细立项报告，包含市场分析、技术方案、风险评估", "location": "办公室"},
            {"id": "T002", "name": "季度总结", "priority": "P1", "estimated_hours": 3, 
             "description": "完成季度工作总结，包括成果、问题、改进计划", "location": "会议室"},
            {"id": "T003", "name": "客户提案准备", "priority": "P0", "estimated_hours": 2, 
             "description": "为客户X准备提案，包含方案和报价", "location": "办公室"},
        ]
    else:
        # 解析任务
        tasks = []
        for task_str in args.tasks:
            parts = task_str.split("|")
            if len(parts) >= 4:
                task = {
                    "id": f"T{len(tasks)+1:03d}",
                    "name": parts[0].strip(),
                    "priority": parts[1].strip(),
                    "estimated_hours": int(float(parts[2].strip())),
                    "description": parts[3].strip(),
                    "location": parts[4].strip() if len(parts) > 4 else "TBD"
                }
                tasks.append(task)
    
    # 执行对应模式
    if args.mode == "plan":
        print("\n" + "="*60)
        print("🎯 时间管理规划模式")
        print("="*60)
        
        # Eisenhower 分类
        eisenhower_result = eisenhower_matrix(tasks)
        print(f"\n📊 Eisenhower Matrix 分类:")
        for quadrant, tasks_list in eisenhower_result.items():
            if tasks_list:
                priority_symbol = PRIORITY_LEVELS.get(tasks_list[0].get("priority", "P2"), "")
                print(f"\n{quadrant} ({len(tasks_list)} 个任务):")
                for i, task in enumerate(tasks_list, 1):
                    print(f"  {i}. {task.get('name', '未命名')} {priority_symbol}")
                    print(f"     预计时间: {task.get('estimated_hours', 0)} 小时")
        
        # 打印任务摘要
        if args.print_summary:
            print_task_summary(tasks)
        
        # 生成应急预案
        emergency_data = generate_emergency_response(tasks)
        print_emergency_plan(emergency_data)
    
    elif args.mode == "schedule":
        print("\n" + "="*60)
        print("📅 日程安排模式")
        print("="*60)
        
        # 创建日程安排
        schedule_data = create_schedule(tasks, args.date)
        print_schedule(schedule_data)
    
    elif args.mode == "emergency":
        print("\n" + "="*60)
        print("🚨 应急预案模式")
        print("="*60)
        
        emergency_data = generate_emergency_response(tasks)
        print_emergency_plan(emergency_data)

if __name__ == "__main__":
    main()
