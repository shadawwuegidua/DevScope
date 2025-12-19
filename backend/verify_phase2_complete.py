import sys
import os
import unittest
from datetime import datetime, timedelta

# 确保可以导入 backend 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modeling import (
    calculate_topic_probability,
    fit_time_distribution,
    calculate_match_score,
    prepare_cold_start_data
)

class Phase2Verification(unittest.TestCase):
    """Phase 2 功能完整性验证"""

    def test_01_tech_tendency_prediction(self):
        """验证技术倾向性预测 (拉普拉斯平滑)"""
        print("\n[验证 1/4] 技术倾向性预测...")
        topics = ["Python", "Python", "JavaScript", "Go", "Python"]
        # Python: 3, JS: 1, Go: 1. Total: 5. Categories: 3.
        # P(Python) = (3+1)/(5+3) = 4/8 = 0.5
        
        result = calculate_topic_probability(topics)
        
        self.assertIn("Python", result)
        self.assertEqual(result["Python"]["probability"], 0.5)
        self.assertIn("explanation", result["Python"])
        print("  ✅ 拉普拉斯平滑计算正确")

    def test_02_time_distribution_fitting(self):
        """验证活跃时间分布拟合 (Weibull/Exponential)"""
        print("\n[验证 2/4] 活跃时间分布拟合...")
        
        # 构造模拟数据 (间隔约 10 天)
        base = datetime(2024, 1, 1)
        timestamps = []
        for i in range(10):
            ts = base + timedelta(days=i*10 + (i%3)) # 引入一点随机性
            timestamps.append(ts.isoformat())
            
        result = fit_time_distribution(timestamps)
        
        self.assertIn(result["distribution_type"], ["Weibull", "Exponential (Fallback)"])
        self.assertTrue(result["expected_interval_days"] > 0)
        self.assertTrue(0 <= result["next_active_prob_30d"] <= 1)
        print(f"  ✅ 分布拟合成功: {result['distribution_type']}")

    def test_03_match_score_model(self):
        """验证匹配度打分模型"""
        print("\n[验证 3/4] 匹配度打分模型...")
        
        tech_tendency = {"Python": {"probability": 0.8}}
        active_prob = 0.5
        
        # Score = 0.8*0.7 + 0.5*0.3 = 0.56 + 0.15 = 0.71
        result = calculate_match_score(tech_tendency, "Python", active_prob)
        
        self.assertAlmostEqual(result["score"], 0.71, places=2)
        self.assertEqual(result["level"], "高度匹配")
        print("  ✅ 打分逻辑正确")

    def test_04_cold_start_integration(self):
        """验证冷启动集成"""
        print("\n[验证 4/4] 冷启动集成...")
        
        # 模拟新用户
        cold_data = prepare_cold_start_data("newbie", project_count=2, primary_language="Python")
        
        self.assertTrue(cold_data["is_cold_start"])
        self.assertLess(cold_data["confidence_weight"], 1.0)
        self.assertIsNotNone(cold_data["community_tendency"])
        
        # 验证融合
        topics = ["Python"]
        probs = calculate_topic_probability(
            topics, 
            community_average=cold_data["community_tendency"],
            confidence_weight=cold_data["confidence_weight"]
        )
        
        # 应该包含社区数据中的其他语言 (如 Java)
        self.assertTrue(len(probs) > 1)
        print("  ✅ 冷启动融合成功")

if __name__ == "__main__":
    print("="*60)
    print("🚀 DevScope Phase 2 - 综合验证脚本")
    print("="*60)
    unittest.main(verbosity=0)
