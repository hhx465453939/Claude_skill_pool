#!/usr/bin/env python3
"""
方案生成脚本 - Integrated Medicine Protocol Generator

用于 Medical Advisor Skill，生成中西医结合的健康方案和风险评估
"""

import argparse
from typing import List, Dict, Optional
from datetime import datetime

class ProtocolGenerator:
    """中西医结合方案生成器"""
    
    def __init__(self):
        self.protocol_types = {
            "western": "西医方案",
            "tcm": "中医方案",
            "integrated": "中西医结合方案"
        }
    
    def western_protocol(self, diagnosis: str, medications: List[str]) -> Dict:
        """
        西医方案生成
        
        诊断：疾病诊断
        药物：药物列表
        """
        protocol = {
            "type": "western",
            "diagnosis": diagnosis,
            "medications": [],
            "dosage": {},
            "frequency": {},
            "duration": {},
            "monitoring": [],
            "contraindications": [],
            "side_effects": []
        }
        
        # 模拟药物方案
        for i, med in enumerate(medications[:5], 1):
            protocol["medications"].append({
                "name": med,
                "dosage": f"标准剂量（根据医生处方的具体剂量）",
                "frequency": "每日 {1 + i} 次",
                "duration": "根据医生处方确定"
            })
        
        # 监测指标
        protocol["monitoring"] = [
            "血压监测",
            "肝功能（ALT, AST）",
            "肾功能（血肌酐，eGFR）",
            "血钾水平"
        ]
        
        # 禁忌
        protocol["contraindications"] = [
            "严重肾功能不全（eGFR < 30 ml/min/1.73m²）",
            "活动性肝病或转氨酶持续升高",
            "妊娠和哺乳期"
        ]
        
        # 副作用预警
        protocol["side_effects"] = [
            "胃肠道反应（恶心、腹泻、消化不良）",
            "肌肉疼痛（他汀类药物）",
            "肝功能异常（需定期监测）",
            "肾功能异常（需定期监测）"
        ]
        
        return protocol
    
    def tcm_protocol(self, constitution: str, syndrome: str) -> Dict:
        """
        中医方案生成
        
        体质：九种体质之一
        辨证：八纲辨证
        """
        protocol = {
            "type": "tcm",
            "constitution": constitution,
            "syndrome": syndrome,
            "prescription": {
                "decoction": [],
                "dosage": {},
                "preparation": "",
                "administration": ""
            },
            "acupuncture": {
                "points": [],
                "duration": "",
                "frequency": "",
                "treatment_course": ""
            },
            "dietary_therapy": {
                "recommended_foods": [],
                "avoid_foods": []
            },
            "lifestyle_modifications": []
        }
        
        # 模拟中药处方（示例）
        if "湿热质" in constitution:
            protocol["prescription"]["decoction"].append({
                "herb": "茯苓",
                "dosage": "15g",
                "function": "健脾利湿"
            })
            protocol["prescription"]["decoction"].append({
                "herb": "白术",
                "dosage": "10g",
                "function": "健脾燥湿"
            })
            protocol["prescription"]["decoction"].append({
                "herb": "泽泻",
                "dosage": "10g",
                "function": "利水渗湿"
            })
        
        # 针灸穴位（示例）
        if "寒证" in syndrome:
            protocol["acupuncture"]["points"] = [
                "关元（RN4）",
                "气海（RN6）",
                "足三里（ST36）",
                "命门（GV4）"
            ]
            protocol["acupuncture"]["duration"] = "30分钟"
            protocol["acupuncture"]["frequency"] = "每日1次"
            protocol["acupuncture"]["treatment_course"] = "10次为一个疗程"
        
        # 食疗养生
        if "阴虚质" in constitution:
            protocol["dietary_therapy"]["recommended_foods"] = [
                "百合",
                "银耳",
                "梨",
                "山药",
                "桑葚"
            ]
            protocol["dietary_therapy"]["avoid_foods"] = [
                "辛辣燥热食物",
                "羊肉",
                "狗肉",
                "辣椒"
            ]
        
        # 起居养生
        protocol["lifestyle_modifications"] = [
            "保证充足睡眠（7-8小时）",
            "避免过度劳累",
            "保持心情舒畅",
            "适当运动（散步、太极拳）"
        ]
        
        return protocol
    
    def integrated_protocol(self, western: Dict, tcm: Dict) -> Dict:
        """
        中西医结合方案生成
        
        整合西医和中医方案，实现协同治疗
        """
        protocol = {
            "type": "integrated",
            "western_protocol": western,
            "tcm_protocol": tcm,
            "combination_strategy": {
                "western_primary": "西药优先，中药辅助",
                "tcm_primary": "中药优先，西药辅助",
                "simultaneous": "中西药同时使用"
            },
            "timing_strategy": {
                "western_morning": "西药早晨服用",
                "tcm_evening": "中药晚间服用",
                "separate_times": "中西药分开服用"
            },
            "safety_precautions": {
                "drug_interactions": "检查西药与中药的相互作用",
                "dosage_adjustments": "根据中药成分调整西药剂量",
                "monitoring_frequency": "中西医结合时需要更频繁的监测"
            }
        }
        
        # 调整策略（示例）
        if "statins" in str(western.get("medications", "")):
            protocol["timing_strategy"]["western_morning"] = "他汀类药物建议早晨服用"
            protocol["timing_strategy"]["tcm_evening"] = "中药建议晚间服用"
            protocol["safety_precautions"]["drug_interactions"] = "注意中药与他汀类药物的相互作用"
        
        return protocol
    
    def risk_assessment(self, protocol: Dict) -> Dict:
        """
        风险评估
        
        评估方案的安全性、风险等级和监测建议
        """
        assessment = {
            "overall_risk": "low",
            "warnings": [],
            "contraindications": [],
            "required_monitoring": [],
            "red_line_criteria": []
        }
        
        # 评估风险等级
        if protocol.get("type") == "integrated":
            assessment["overall_risk"] = "medium"
            assessment["warnings"].append("中西医结合需要更频繁的监测")
        
        # 检查禁忌
        contraindications = protocol.get("contraindications", [])
        if contraindications:
            assessment["contraindications"] = contraindications
            assessment["warnings"].extend([f"禁忌症: {c}" for c in contraindications])
        
        # 必需监测指标
        if "monitoring" in protocol:
            assessment["required_monitoring"] = protocol["monitoring"]
        
        # 红线标准（停药标准）
        assessment["red_line_criteria"] = [
            "ALT或AST > 3倍正常上限",
            "血肌酐 > 2倍正常上限",
            "出现严重副作用（如过敏反应）",
            "血压持续低于90/60mmHg"
        ]
        
        return assessment
    
    def print_protocol_summary(self, protocol: Dict, risk: Dict):
        """打印方案摘要"""
        print(f"\n💊 健康方案摘要")
        print(f"=" * 60)
        
        # 西医部分
        if protocol.get("type") in ["western", "integrated"]:
            western = protocol.get("western_protocol", {})
            if western:
                print(f"\n🏥 西医方案（Western Medicine Protocol）")
                print(f"  诊断: {western.get('diagnosis', 'N/A')}")
                print(f"  药物: {len(western.get('medications', []))} 种")
                for i, med in enumerate(western.get("medications", [])[:3], 1):
                    print(f"    {i}. {med['name']} - {med['frequency']}")
        
        # 中医部分
        if protocol.get("type") in ["tcm", "integrated"]:
            tcm = protocol.get("tcm_protocol", {})
            if tcm:
                print(f"\n🔬 中医方案（TCM Protocol）")
                print(f"  体质: {tcm.get('constitution', 'N/A')}")
                print(f"  辨证: {tcm.get('syndrome', 'N/A')}")
                if tcm.get("prescription"):
                    print(f"  中药处方: {len(tcm['prescription']['decoction'])} 味")
                    for i, herb in enumerate(tcm['prescription']['decoction'][:3], 1):
                        print(f"    {i}. {herb['herb']} {herb['dosage']} - {herb['function']}")
        
        # 结合策略
        if protocol.get("type") == "integrated":
            combo = protocol.get("combination_strategy", {})
            timing = protocol.get("timing_strategy", {})
            print(f"\n🔄 结合策略（Integration Strategy）")
            print(f"  策略: {combo.get('western_primary', 'N/A')}")
            print(f"  时机: {timing.get('western_morning', 'N/A')}")
        
        # 风险评估
        print(f"\n🛡️ 安全评估（Risk Assessment）")
        print(f"  整体风险: {risk.get('overall_risk', 'N/A')}")
        if risk.get("warnings"):
            print(f"  警告: {', '.join(risk['warnings'][:3])}")
        if risk.get("required_monitoring"):
            print(f"  必需监测:")
            for indicator in risk["required_monitoring"][:3]:
                print(f"    • {indicator}")
        if risk.get("red_line_criteria"):
            print(f"  红线标准: {risk['red_line_criteria'][0]}")


def main():
    parser = argparse.ArgumentParser(description='Integrated Medicine Protocol Generator')
    parser.add_argument('--type', choices=['western', 'tcm', 'integrated', 'all'], 
                       default='all', help='类型: western=西医, tcm=中医, integrated=中西医结合, all=全部')
    parser.add_argument('--diagnosis', help='疾病诊断')
    parser.add_argument('--constitution', help='中医体质')
    parser.add_argument('--syndrome', help='中医辨证')
    parser.add_argument('--medications', nargs='+', help='药物列表')
    
    args = parser.parse_args()
    
    generator = ProtocolGenerator()
    
    if args.type in ['western', 'all']:
        # 示例西医方案
        if not args.medications:
            medications = ["他汀类药物", "抗高血压药", "阿司匹林"]
        else:
            medications = args.medications
        
        western = generator.western_protocol(args.diagnosis if args.diagnosis else "高血压、高血脂", medications)
        risk = generator.risk_assessment(western)
        generator.print_protocol_summary(western, risk)
    
    if args.type in ['tcm', 'all']:
        # 示例中医方案
        if not args.constitution:
            constitution = "湿热质"
        else:
            constitution = args.constitution
        
        if not args.syndrome:
            syndrome = "寒证"
        else:
            syndrome = args.syndrome
        
        tcm = generator.tcm_protocol(constitution, syndrome)
        risk = generator.risk_assessment(tcm)
        generator.print_protocol_summary(tcm, risk)
    
    if args.type in ['integrated', 'all']:
        # 示例中西医结合方案
        western = generator.western_protocol("高脂血症", ["他汀类药物"])
        tcm = generator.tcm_protocol("痰湿质", "寒证")
        integrated = generator.integrated_protocol(western, tcm)
        risk = generator.risk_assessment(integrated)
        generator.print_protocol_summary(integrated, risk)


if __name__ == "__main__":
    main()
