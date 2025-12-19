import unittest
import numpy as np
from datetime import datetime, timedelta
from modeling import (
    calculate_topic_probability,
    fit_time_distribution,
    calculate_match_score
)

class TestPhase2Modeling(unittest.TestCase):
    
    def test_calculate_topic_probability_basic(self):
        """测试基础的拉普拉斯平滑概率计算"""
        topics = ["Python", "Python", "JavaScript", "Go"]
        # Total = 4, Categories = 3 (Python, JS, Go)
        # Alpha = 1.0
        # Denominator = 4 + 1*3 = 7
        # P(Python) = (2+1)/7 = 3/7 ≈ 0.4286
        # P(JS) = (1+1)/7 = 2/7 ≈ 0.2857
        
        result = calculate_topic_probability(topics, alpha=1.0)
        
        self.assertIn("Python", result)
        self.assertAlmostEqual(result["Python"]["probability"], 3/7, places=4)
        self.assertAlmostEqual(result["JavaScript"]["probability"], 2/7, places=4)
        self.assertIn("explanation", result["Python"])

    def test_calculate_topic_probability_cold_start(self):
        """测试冷启动场景下的社区融合"""
        topics = ["Python"] # 只有1个项目
        community_avg = {"Python": 0.2, "Java": 0.3}
        confidence_weight = 0.1 # 极低置信度
        
        # P_user(Python) with alpha=1: (1+1)/(1+1) = 1.0 (假设只有1类)
        # 但 calculate_topic_probability 内部会重新统计类别数
        # 这里主要测试融合逻辑是否执行
        
        result = calculate_topic_probability(
            topics, 
            community_average=community_avg,
            confidence_weight=confidence_weight
        )
        
        # 应该包含社区数据中的 Java
        self.assertIn("Java", result)
        # Java 的用户概率为 0 (平滑后非0)，社区概率 0.3
        # 验证融合后的值介于两者之间
        self.assertTrue(result["Java"]["probability"] > 0)

    def test_fit_time_distribution_weibull(self):
        """测试 Weibull 分布拟合"""
        # 生成符合 Weibull 分布的随机数据
        np.random.seed(42)
        # 生成间隔数据
        intervals = np.random.weibull(1.5, 100) * 10 # shape=1.5, scale=10
        
        # 构造时间戳
        base_time = datetime(2023, 1, 1)
        timestamps = []
        current_time = base_time
        for interval in intervals:
            current_time += timedelta(days=interval)
            timestamps.append(current_time.isoformat())
            
        result = fit_time_distribution(timestamps)
        
        self.assertEqual(result["distribution_type"], "Weibull")
        self.assertIn("shape", result["params"])
        self.assertIn("scale", result["params"])
        self.assertTrue(0 <= result["next_active_prob_30d"] <= 1)

    def test_fit_time_distribution_insufficient(self):
        """测试数据不足的情况"""
        timestamps = ["2023-01-01T10:00:00Z"] # 只有一个点，无法计算间隔
        result = fit_time_distribution(timestamps)
        self.assertEqual(result["distribution_type"], "Insufficient Data")

    def test_calculate_match_score(self):
        """测试匹配度打分"""
        tech_tendency = {
            "Python": {"probability": 0.8},
            "JavaScript": {"probability": 0.2}
        }
        active_prob = 0.9
        
        # Target: Python
        # Score = 0.8 * 0.7 + 0.9 * 0.3 = 0.56 + 0.27 = 0.83
        result = calculate_match_score(tech_tendency, "Python", active_prob)
        self.assertAlmostEqual(result["score"], 0.83, places=2)
        self.assertEqual(result["level"], "极高匹配")
        
        # Target: Rust (不存在)
        # Score = 0.0 * 0.7 + 0.9 * 0.3 = 0.27
        result_miss = calculate_match_score(tech_tendency, "Rust", active_prob)
        self.assertAlmostEqual(result_miss["score"], 0.27, places=2)
        self.assertEqual(result_miss["level"], "低度契合")

if __name__ == "__main__":
    unittest.main()
