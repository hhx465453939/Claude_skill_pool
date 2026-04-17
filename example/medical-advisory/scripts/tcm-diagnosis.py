#!/usr/bin/env python3
"""
中医诊断脚本 - TCM Constitution and Syndrome Differentiation

用于 Medical Advisor Skill，支持中医体质辨识、辨证论治、整体调理方案
"""

import argparse
from typing import List, Dict, Optional
from datetime import datetime

class TCMDiagnoser:
    """中医诊断器"""
    
    def __init__(self):
        self.constitutions = {
            "平和质": {"characteristics": ["面色红润", "精力充沛", "适应力强"], "susceptibility": []},
            "气虚质": {"characteristics": ["气短懒言", "神疲乏力", "自汗", "易感冒"], "susceptibility": ["易感冒", "易疲劳", "易出虚汗"]},
            "阳虚质": {"characteristics": ["怕冷", "手脚不温", "容易腹泻"], "susceptibility": ["易受寒邪", "易腹泻", "水湿内停"]},
            "阴虚质": {"characteristics": ["口干咽燥", "手足心热", "易烦躁失眠", "便秘"], "susceptibility": ["易生内热", "便秘", "失眠"]},
            "痰湿质": {"characteristics": ["体形肥胖", "腹部肥满", "口黏苔腻"], "susceptibility": ["易患高血压", "易患糖尿病", "易患高血脂"]},
            "湿热质": {"characteristics": ["面垢油光", "易生痤疮", "口苦口臭"], "susceptibility": ["易患皮肤病", "易患黄疸", "易患泌尿系统感染"]},
            "血瘀质": {"characteristics": ["面色晦暗", "容易有瘀斑", "口唇紫暗"], "susceptibility": ["易患肿瘤", "易患心脑血管疾病", "痛经"]},
            "气郁质": {"characteristics": ["神情抑郁", "多愁善虑", "胸胁胀痛"], "susceptibility": ["易患抑郁症", "易患乳腺增生", "易患失眠"]}
        }
        
        self.syndromes = {
            "表证": {"location": "皮毛、肌表", "nature": "浅", "treatment": "解表法", "herbs": ["麻黄", "桂枝", "防风", "荆芥"]},
            "里证": {"location": "脏腑、气血、骨髓", "nature": "深", "treatment": "温里、清里、补里", "herbs": ["附子", "干姜", "人参", "黄芪"]},
            "寒证": {"characteristics": ["恶寒", "蜷卧", "无汗", "舌淡苔白"], "treatment": "温法", "herbs": ["附子", "肉桂", "干姜"]},
            "热证": {"characteristics": ["发热", "口渴", "烦躁", "舌红苔黄"], "treatment": "清热法", "herbs": ["石膏", "知母", "栀子"]},
            "虚证": {"characteristics": ["气短懒言", "神疲乏力", "自汗", "脉虚无力"], "treatment": "补法", "herbs": ["人参", "黄芪", "当归", "白术"]},
            "实证": {"characteristics": ["发热腹胀", "疼痛拒按", "舌红苔厚", "脉实有力"], "treatment": "泻法", "herbs": ["大黄", "芒硝", "枳实"]},
            "阴证": {"characteristics": ["面色苍白", "畏寒肢冷", "精神萎靡"], "treatment": "滋阴法", "herbs": ["生地", "麦冬", "玄参"]},
            "阳证": {"characteristics": ["面色潮红", "发热喜饮", "烦躁不安"], "treatment": "温阳法", "herbs": ["附子", "桂枝", "干姜"]}
        }

    def identify_constitution(self, symptoms: List[str]) -> Dict:
        """
        体质辨识
        
        基于用户症状辨识中医体质（九种体质）
        """
        print(f"\n🔬 中医体质辨识")
        print(f"=" * 60)
        
        scores = {}
        for constitution, data in self.constitutions.items():
            score = 0
            matches = []
            for symptom in symptoms:
                if symptom in data["characteristics"]:
                    score += 1
                    matches.append(symptom)
            scores[constitution] = {
                "score": score,
                "matches": matches,
                "susceptibility": data["susceptibility"]
            }
        
        # 找到得分最高的体质
        sorted_constitutions = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # 输出结果
        print(f"\n📊 体质辨识结果:")
        top_constitution = sorted_constitutions[0][0]
        top_score = sorted_constitutions[0][1]["score"]
        top_matches = sorted_constitutions[0][1]["matches"]
        
        print(f"  主要体质: {top_constitution}")
        print(f"  匹配症状数: {top_score}")
        print(f"  匹配症状: {', '.join(top_matches)}")
        
        # 输出体质特征
        print(f"\n🔹 {top_constitution} 特征:")
        for char in self.constitutions[top_constitution]["characteristics"]:
            print(f"  • {char}")
        
        # 输出易患疾病
        print(f"\n🏥 易患疾病:")
        for sus in self.constitutions[top_constitution]["susceptibility"]:
            print(f"  • {sus}")
        
        return {
            "primary_constitution": top_constitution,
            "score": top_score,
            "matches": top_matches
        }

    def differentiate_syndrome(self, symptoms: List[str]) -> Dict:
        """
        辨证论治
        
        基于用户症状进行辨证（八纲辨证）
        """
        print(f"\n🔬 中医辨证论治")
        print(f"=" * 60)
        
        syndrome_scores = {}
        
        # 表里辨证
        if any("表" in s for s in symptoms):
            syndrome_scores["表证"] = 3
        if any("恶寒" in s or "发热" in s for s in symptoms):
            syndrome_scores["表证"] = 2
        
        # 寒热辨证
        cold_count = sum(1 for s in symptoms if "寒" in s or "冷" in s or "畏寒" in s)
        hot_count = sum(1 for s in symptoms if "热" in s or "发烧" in s or "口苦" in s)
        if cold_count > hot_count:
            syndrome_scores["寒证"] = cold_count
        elif hot_count > cold_count:
            syndrome_scores["热证"] = hot_count
        
        # 虚实辨证
        weak_count = sum(1 for s in symptoms if "虚" in s or "乏" in s or "无力" in s)
        excess_count = sum(1 for s in symptoms if "实" in s or "腹胀" in s or "疼痛" in s)
        if weak_count > excess_count:
            syndrome_scores["虚证"] = weak_count
        elif excess_count > weak_count:
            syndrome_scores["实证"] = excess_count
        
        # 阴阳辨证
        yin_count = sum(1 for s in symptoms if "阴" in s or "寒" in s or "汗" in s)
        yang_count = sum(1 for s in symptoms if "阳" in s or "热" in s or "烦躁" in s)
        if yin_count > yang_count:
            syndrome_scores["阴证"] = yin_count
        elif yang_count > yin_count:
            syndrome_scores["阳证"] = yang_count
        
        # 输出辨证结果
        print(f"\n📊 八纲辨证结果:")
        sorted_syndromes = sorted(syndrome_scores.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True)
        
        for syndrome, score in sorted_syndromes[:3]:
            if isinstance(score, int):
                print(f"  {syndrome}: {score} 分")
        
        return {
            "syndrome_scores": syndrome_scores,
            "diagnosis": "需要结合临床望闻问切进一步确诊"
        }

    def recommend_tcm_regimen(self, constitution: str, syndrome: str) -> Dict:
        """
        中医调理方案
        
        基于体质和辨证推荐调理方案
        """
        print(f"\n🔬 中医调理方案")
        print(f"=" * 60)
        
        print(f"\n体质: {constitution}")
        print(f"辨证: {syndrome}")
        
        # 根据体质和辨证推荐调理方法
        recommendations = []
        
        # 饮食调理
        if "湿热质" in constitution:
            recommendations.append({
                "category": "食疗",
                "advice": "避免辛辣油腻食物，多吃清热利湿食物（如绿豆、苦瓜、冬瓜）",
                "herbs": ["金银花", "菊花", "茯苓", "薏苡仁"]
            })
        elif "阳虚质" in constitution:
            recommendations.append({
                "category": "食疗",
                "advice": "避免生冷寒凉食物，多吃温补食物（如羊肉、生姜、羊肉）",
                "herbs": ["当归", "生姜", "红枣", "桂圆"]
            })
        elif "阴虚质" in constitution:
            recommendations.append({
                "category": "食疗",
                "advice": "避免辛辣燥热食物，多吃滋阴润燥食物（如百合、银耳、梨）",
                "herbs": ["麦冬", "玉竹", "百合", "银耳"]
            })
        
        # 起居调养
        if "气郁质" in constitution:
            recommendations.append({
                "category": "起居",
                "advice": "保持心情舒畅，多运动，多与人交流",
                "exercise": ["慢跑", "瑜伽", "游泳"]
            })
        elif "气虚质" in constitution:
            recommendations.append({
                "category": "起居",
                "advice": "保证充足睡眠，避免过度劳累，适当运动",
                "exercise": ["散步", "太极拳", "气功"]
            })
        
        # 情志调节
        recommendations.append({
            "category": "情志",
            "advice": "保持平和心态，避免七情内伤（喜、怒、忧、思、悲、恐、惊）",
            "methods": ["冥想", "深呼吸", "听音乐"]
        })
        
        # 输出调理方案
        print(f"\n📋 调理建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['category'].upper()}")
            print(f"   建议: {rec['advice']}")
            if 'herbs' in rec:
                print(f"   推荐食材/中药: {', '.join(rec['herbs'][:5])}")
            if 'exercise' in rec:
                print(f"   推荐运动: {', '.join(rec['exercise'][:3])}")
        
        return {
            "constitution": constitution,
            "syndrome": syndrome,
            "recommendations": recommendations
        }

    def print_diagnosis_summary(self, diagnosis_data: Dict):
        """打印诊断摘要"""
        print(f"\n📊 中医诊断摘要")
        print(f"=" * 60)
        
        if "primary_constitution" in diagnosis_data:
            print(f"  体质: {diagnosis_data['primary_constitution']}")
        
        if "syndrome_scores" in diagnosis_data:
            print(f"  辨证: {diagnosis_data['diagnosis']}")
        
        if "recommendations" in diagnosis_data:
            print(f"  调理建议: {len(diagnosis_data['recommendations'])} 项")


def main():
    parser = argparse.ArgumentParser(description='TCM Diagnosis - 中医体质辨识与辨证论治')
    parser.add_argument('--mode', choices=['constitution', 'syndrome', 'regimen', 'all'], 
                       default='all', help='模式: constitution=体质辨识, syndrome=辨证论治, regimen=调理方案, all=全部')
    parser.add_argument('--symptoms', nargs='+', help='症状列表')
    parser.add_argument('--constitution', help='体质（用于 regimen 模式）')
    parser.add_argument('--syndrome', help='辨证（用于 regimen 模式）')
    
    args = parser.parse_args()
    
    # 示例症状
    if args.mode in ['constitution', 'syndrome', 'all'] and not args.symptoms:
        args.symptoms = [
            "气短懒言", "神疲乏力", "自汗", "易感冒",  # 气虚
            "口干咽燥", "手足心热", "易烦躁失眠", "便秘"  # 阴虚
        ]
    
    diagnoser = TCMDiagnoser()
    
    if args.mode in ['constitution', 'all']:
        constitution_result = diagnoser.identify_constitution(args.symptoms)
    
    if args.mode in ['syndrome', 'all']:
        syndrome_result = diagnoser.differentiate_syndrome(args.symptoms)
    
    if args.mode in ['regimen', 'all']:
        constitution = args.constitution if args.constitution else "平和质"
        syndrome = args.syndrome if args.syndrome else "平和质"
        regimen_result = diagnoser.recommend_tcm_regimen(constitution, syndrome)
    
    if args.mode == 'all':
        diagnosis_data = {
            **constitution_result,
            **syndrome_result,
            **regimen_result
        }
        diagnoser.print_diagnosis_summary(diagnosis_data)


if __name__ == "__main__":
    main()
