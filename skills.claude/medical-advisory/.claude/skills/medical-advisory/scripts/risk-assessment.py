#!/usr/bin/env python3
"""
风险评估脚本 - Drug Interaction and Safety Assessment

用于 Medical Advisor Skill，评估药物相互作用、安全性和风险等级
"""

import argparse
from typing import List, Dict, Optional
from datetime import datetime

class RiskAssessor:
    """风险评估器"""
    
    def __init__(self):
        self.severity_levels = {
            "low": "低风险 - 可以安全使用",
            "moderate": "中等风险 - 需要监测",
            "high": "高风险 - 建议咨询医生",
            "severe": "高风险 - 立即停药并咨询医生"
        }
    
    def check_drug_interactions(self, medications: List[str]) -> Dict:
        """
        检查药物相互作用
        
        medications: 药物列表
        """
        print(f"\n⚠️ 药物相互作用检查（Drug Interaction Check）")
        print(f"="*60)
        
        results = []
        interactions_found = []
        
        # 模拟相互作用检查
        if len(medications) > 1:
            # 模拟一些常见的相互作用
            if "他汀" in " ".join(medications):
                interactions_found.append({
                    "type": "与西柚汁的相互作用",
                    "severity": "moderate",
                    "description": "西柚汁会抑制CYP3A4酶，增加他汀类药物的血药浓度，增加肌肉痛等副作用风险",
                    "recommendation": "避免同时大量摄入西柚汁，建议咨询医生调整剂量"
                })
            
            if "抗凝血" in " ".join(medications) and "NSAIDs" in " ".join(medications):
                interactions_found.append({
                    "type": "抗凝血药与NSAIDs的相互作用",
                    "severity": "high",
                    "description": "两者联用会显著增加出血风险",
                    "recommendation": "建议咨询医生，可能需要调整用药方案"
                })
            
            if "ACE抑制剂" in " ".join(medications) and "钾补充剂" in " ".join(medications):
                interactions_found.append({
                    "type": "ACE抑制剂与钾补充剂的相互作用",
                    "severity": "high",
                    "description": "两者联用可能导致高钾血症，心脏传导异常",
                    "recommendation": "定期监测血钾水平，避免过量补钾"
                })
        
        results = {
            "medications_checked": medications,
            "interactions_found": interactions_found,
            "risk_level": self._assess_interaction_risk(interactions_found)
        }
        
        # 输出结果
        if interactions_found:
            print(f"\n📋 检测到 {len(interactions_found)} 个潜在的相互作用")
            for i, interaction in enumerate(interactions_found, 1):
                print(f"\n{i}. {interaction['type']}")
                print(f"   严重性: {interaction['severity']}")
                print(f"   描述: {interaction['description']}")
                print(f"   建议: {interaction['recommendation']}")
        else:
            print("\n✅ 未检测到已知的药物相互作用")
        
        return results
    
    def _assess_interaction_risk(self, interactions: List[Dict]) -> str:
        """评估相互作用风险等级"""
        if not interactions:
            return "low"
        
        severities = [i['severity'] for i in interactions]
        if 'severe' in severities:
            return "severe"
        elif 'high' in severities:
            return "high"
        elif 'moderate' in severities:
            return "moderate"
        else:
            return "low"
    
    def assess_safety_profile(self, medications: List[str]) -> Dict:
        """
        评估药物安全性
        
        medications: 药物列表
        """
        print(f"\n🛡️ 药物安全性评估（Drug Safety Profile）")
        print(f"="*60)
        
        safety_profile = {
            "medications": [],
            "warnings": [],
            "contraindications": [],
            "monitoring_indicators": []
        }
        
        # 模拟安全性评估
        for med in medications:
            med_safety = {
                "name": med,
                "warnings": [],
                "contraindications": [],
                "monitoring": []
            }
            
            # 他汀类药物安全性
            if "他汀" in med:
                med_safety["warnings"].append("注意肌肉痛、肌肉无力等副作用")
                med_safety["warnings"].append("注意肝功能异常（AST, ALT升高）")
                med_safety["warnings"].append("注意横纹肌溶解（罕见但严重）")
                med_safety["contraindications"].append("活动性肝病或原因不明的转氨酶持续升高禁用")
                med_safety["contraindications"].append("对他汀类药物过敏禁用")
                med_safety["monitoring"] = [
                    "肝功能（ALT, AST）",
                    "肌酸激酶（CK）",
                    "血脂水平"
                ]
            
            # 抗凝血药安全性
            if "抗凝" in med:
                med_safety["warnings"].append("注意出血风险（牙龈、鼻、皮下、消化道出血）")
                med_safety["warnings"].append("注意皮下瘀斑、血肿")
                med_safety["warnings"].append("注意严重出血（颅内、消化道）")
                med_safety["contraindications"].append("活动性出血或出血倾向禁用")
                med_safety["contraindications"].append("严重高血压禁用")
                med_safety["monitoring"] = [
                    "凝血功能（PT, APTT）",
                    "血常规",
                    "血红蛋白"
                ]
            
            # 镇静催眠药安全性
            if "苯二氮" in med:
                med_safety["warnings"].append("注意嗜睡、头晕、平衡障碍")
                med_safety["warnings"].append("注意依赖性和耐受性")
                med_safety["warnings"].append("注意突然停药时的戒断症状")
                med_safety["contraindications"].append("急性闭角型青光眼禁用")
                med_safety["contraindications"].append("重症肌无力禁用")
                med_safety["monitoring"] = [
                    "肝功能",
                    "血常规",
                    "认知功能"
                ]
            
            safety_profile["medications"].append(med_safety)
            safety_profile["warnings"].extend(med_safety["warnings"])
            safety_profile["contraindications"].extend(med_safety["contraindications"])
            safety_profile["monitoring_indicators"].extend(med_safety["monitoring"])
        
        # 输出结果
        print(f"\n📊 安全性评估结果")
        print(f"共评估 {len(safety_profile['medications'])} 种药物")
        print(f"发现 {len(safety_profile['warnings'])} 个安全警告")
        print(f"发现 {len(safety_profile['contraindications'])} 个禁忌症")
        print(f"建议监测 {len(set(safety_profile['monitoring_indicators']))} 个指标")
        
        return safety_profile
    
    def generate_monitoring_plan(self, medications: List[str]) -> Dict:
        """
        生成监测计划
        """
        print(f"\n📋 监测计划（Monitoring Plan）")
        print(f"="*60)
        
        plan = {
            "baseline_tests": [],
            "monitoring_frequency": {},
            "red_line_criteria": [],
            "emergency_criteria": []
        }
        
        # 基线检测
        plan["baseline_tests"] = [
            "血常规（CBC）",
            "肝功能（ALT, AST, ALP, Bilirubin）",
            "肾功能（血肌酐、eGFR）",
            "血脂全套（总胆固醇、LDL-C、HDL-C、甘油三酯）",
            "凝血功能（PT, APTT）",
            "血压测量"
        ]
        
        # 监测频率
        plan["monitoring_frequency"] = {
            "他汀类药物": "开始后4-8周检查一次肝功能和肌酸激酶，之后每6-12个月检查一次",
            "抗凝血药": "开始后1周检查凝血功能，之后根据INR水平调整监测频率（通常每周1-2次）",
            "苯二氮类药物": "开始后1个月评估疗效和副作用，之后根据情况调整",
            "中药方剂": "开始后1-2周评估疗效和副作用，之后每1-2个月评估一次"
        }
        
        # 红线标准（停药标准）
        plan["red_line_criteria"] = [
            "ALT或AST > 3倍正常上限（他汀类药物）",
            "血肌酐 > 2倍正常上限（他汀类或抗凝药）",
            "INR > 4.0或 < 1.5（抗凝药）",
            "出现严重副作用（如过敏反应、横纹肌溶解）"
        ]
        
        # 紧急标准
        plan["emergency_criteria"] = [
            "严重过敏反应（呼吸困难、面部肿胀、荨麻疹等）",
            "颅内出血（剧烈头痛、视力模糊、言语不清）",
            "消化道出血（大量呕血或黑便）",
            "横纹肌溶解（严重肌肉疼痛、酱油色尿液、肌肉无力）"
        ]
        
        # 输出结果
        print(f"\n📋 基线检测:")
        for test in plan["baseline_tests"]:
            print(f"  • {test}")
        
        print(f"\n📋 监测频率:")
        for med, frequency in plan["monitoring_frequency"].items():
            print(f"  • {med}: {frequency}")
        
        print(f"\n🚨 红线标准（需要咨询医生）:")
        for criterion in plan["red_line_criteria"][:3]:
            print(f"  • {criterion}")
        
        print(f"\n🚨 紧急标准（立即就医）:")
        for criterion in plan["emergency_criteria"][:3]:
            print(f"  • {criterion}")
        
        return plan
    
    def print_risk_assessment_summary(self, interaction_result: Dict, safety_profile: Dict, monitoring_plan: Dict):
        """打印风险评估摘要"""
        print(f"\n📊 风险评估摘要（Risk Assessment Summary）")
        print(f"="*60)
        
        # 相互作用风险
        print(f"\n⚠️ 药物相互作用风险: {interaction_result.get('risk_level', 'unknown')}")
        if interaction_result.get('interactions_found'):
            print(f"  检测到 {len(interaction_result['interactions_found'])} 个相互作用")
        
        # 安全性概况
        print(f"\n🛡️ 药物安全性:")
        print(f"  评估药物数: {len(safety_profile.get('medications', []))}")
        print(f"  安全警告: {len(safety_profile.get('warnings', []))}")
        print(f"  禁忌症: {len(safety_profile.get('contraindications', []))}")
        print(f"  需要监测的指标: {len(set(safety_profile.get('monitoring_indicators', [])))}")
        
        # 监测计划
        print(f"\n📋 监测计划:")
        print(f"  基线检测: {len(monitoring_plan.get('baseline_tests', []))} 项")
        print(f"  监测药物: {len(monitoring_plan.get('monitoring_frequency', []))} 类")


def main():
    parser = argparse.ArgumentParser(description='Drug Interaction and Safety Assessment Tool')
    parser.add_argument('--mode', choices=['interactions', 'safety', 'monitoring', 'all'], 
                       default='all', help='模式: interactions=相互作用, safety=安全性, monitoring=监测计划, all=全部')
    parser.add_argument('--medications', nargs='+', help='药物列表')
    
    args = parser.parse_args()
    
    assessor = RiskAssessor()
    
    # 示例药物
    if args.mode in ['interactions', 'all'] and not args.medications:
        medications = ["阿托伐他汀", "阿司匹林", "氯沙坦"]
    else:
        medications = args.medications
    
    if args.mode in ['interactions', 'all']:
        # 相互作用检查
        interaction_result = assessor.check_drug_interactions(medications)
    
    if args.mode in ['safety', 'all']:
        # 安全性评估
        safety_profile = assessor.assess_safety_profile(medications)
    
    if args.mode in ['monitoring', 'all']:
        # 监测计划
        monitoring_plan = assessor.generate_monitoring_plan(medications)
    
    if args.mode == 'all':
        # 打印摘要
        assessor.print_risk_assessment_summary(
            {"risk_level": "low"},
            {"medications": [], "warnings": [], "contraindications": [], "monitoring_indicators": []},
            {"baseline_tests": [], "monitoring_frequency": {}, "red_line_criteria": [], "emergency_criteria": []}
        )


if __name__ == "__main__":
    main()
