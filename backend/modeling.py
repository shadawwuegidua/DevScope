"""
DevScope Phase 1 & Phase 2 - 数据建模与统计分析模块

此模块实现：
- Phase 1: 冷启动处理、置信度权重计算、社区数据融合
- Phase 2: 技术倾向性预测、活跃时间分布拟合、匹配度打分

所有预测基于统计学原理，强调可解释性，严禁使用黑箱 ML/DL 模型。
"""

from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
from collections import Counter

import numpy as np
from scipy import stats
from dateutil import parser as date_parser

from seed_data import (
    get_community_average_tendency,
    get_community_average_time_params,
    get_developer_from_fame_hall,
    is_developer_in_fame_hall,
)


def calculate_confidence_weight(project_count: int, threshold: int = 10) -> float:
    """
    计算置信度权重，用于冷启动补救。
    
    数学公式：
    $$w = \\min(1.0, \\text{project_count} / threshold)$$
    
    当项目数少于阈值时，权重 < 1.0，说明需要融合社区平均数据。
    
    参数：
        project_count: 用户参与的项目数
        threshold: 充分信息所需的项目数（默认 10）
    
    返回值：
        置信度权重 (0.0 - 1.0)
    """
    if project_count < 0:
        return 0.0
    
    weight = min(1.0, project_count / threshold)
    return round(weight, 3)


def is_cold_start(project_count: int, threshold: int = 5) -> bool:
    """
    判断是否需要启用冷启动逻辑。
    
    定义：当项目数 < threshold 时，认为数据不足，需要冷启动处理。
    
    参数：
        project_count: 用户参与的项目数
        threshold: 冷启动阈值（默认 5）
    
    返回值：
        True 表示需要冷启动处理，False 表示数据充分
    """
    return project_count < threshold


def get_developer_type_guess(primary_language: Optional[str] = None) -> str:
    """
    根据主要编程语言猜测开发者类型，用于冷启动时选择社区平均数据。
    
    参数：
        primary_language: 开发者最常用的编程语言
    
    返回值：
        猜测的开发者类型字符串
    """
    if not primary_language:
        return "Backend Developer"  # 默认后端
    
    language_lower = primary_language.lower()
    
    # 语言到开发者类型的映射
    language_type_map = {
        "python": "AI/ML Developer",
        "javascript": "Frontend Developer",
        "typescript": "Frontend Developer",
        "java": "Backend Developer",
        "go": "DevOps/Infrastructure",
        "rust": "DevOps/Infrastructure",
        "scala": "Data Engineer",
        "r": "Data Engineer",
        "c++": "Backend Developer",
        "c": "Backend Developer",
    }
    
    for lang, dev_type in language_type_map.items():
        if lang in language_lower:
            return dev_type
    
    return "Backend Developer"  # 默认


def blend_user_and_community(
    user_tendency: Dict[str, float],
    community_tendency: Dict[str, float],
    confidence_weight: float,
) -> Dict[str, float]:
    """
    融合用户倾向和社区平均倾向。
    
    数学公式：
    $$P_{final}(T_i) = w \\cdot P_{user}(T_i) + (1-w) \\cdot P_{community}(T_i)$$
    
    其中：
    - $w$ 是置信度权重（取值 0.0 - 1.0）
    - $P_{user}$ 是用户的技术倾向分布
    - $P_{community}$ 是社区平均分布
    
    参数：
        user_tendency: 用户的技术倾向分布
        community_tendency: 社区平均倾向分布
        confidence_weight: 置信度权重 (0.0 - 1.0)
    
    返回值：
        融合后的倾向分布字典
    """
    blended = {}
    
    # 获取所有可能的技术类别
    all_techs = set(user_tendency.keys()) | set(community_tendency.keys())
    
    for tech in all_techs:
        user_prob = user_tendency.get(tech, 0.0)
        community_prob = community_tendency.get(tech, 0.0)
        
        # 融合
        blended[tech] = (
            confidence_weight * user_prob +
            (1 - confidence_weight) * community_prob
        )
    
    return blended


# =============================================================================
# Phase 2: Mathematical Modeling (Core)
# =============================================================================

def calculate_topic_probability(
    topics: List[str],
    alpha: float = 1.0,
    community_average: Optional[Dict[str, float]] = None,
    confidence_weight: float = 1.0,
) -> Dict[str, Dict[str, Any]]:
    """
    计算技术倾向概率，使用拉普拉斯平滑。
    
    数学公式：
    $$P(T_i) = \\frac{n_i + \\alpha}{N + \\alpha K}$$
    
    其中：
    - $n_i$: 技术领域 $T_i$ 的项目数
    - $N$: 总项目数
    - $K$: 技术类别总数
    - $\\alpha$: 平滑参数（通常取 1）
    
    如果提供了 community_average 且 confidence_weight < 1.0，
    则会融合社区均值：
    $$P_{final} = w \\cdot P_{user} + (1-w) \\cdot P_{community}$$
    
    参数：
        topics: 用户参与的项目话题/语言列表
        alpha: 拉普拉斯平滑参数 (默认 1.0)
        community_average: 社区平均倾向分布 (可选，用于冷启动)
        confidence_weight: 置信度权重 (0.0 - 1.0，用于冷启动)
    
    返回值：
        包含各领域概率及解释的字典：
        {
            "Python": {
                "probability": 0.42,
                "count": 12,
                "explanation": "基于历史数据，该开发者参与 Python 项目的概率为 42%"
            },
            ...
        }
    """
    if not topics:
        # 空数据处理
        if community_average:
            # 完全使用社区数据
            result = {}
            for tech, prob in community_average.items():
                result[tech] = {
                    "probability": prob,
                    "count": 0,
                    "explanation": f"无历史数据，基于社区均值推断概率为 {prob:.1%}"
                }
            return result
        return {}

    # 1. 统计频次
    counts = Counter(topics)
    total_projects = len(topics)
    unique_topics = list(counts.keys())
    num_categories = len(unique_topics)
    
    # 2. 计算拉普拉斯平滑概率
    user_probs = {}
    denominator = total_projects + alpha * num_categories
    
    for topic in unique_topics:
        count = counts[topic]
        prob = (count + alpha) / denominator
        user_probs[topic] = prob
        
    # 3. 融合社区数据 (如果需要)
    final_probs = {}
    
    # 获取所有涉及的技术
    all_techs = set(user_probs.keys())
    if community_average:
        all_techs |= set(community_average.keys())
        
    for tech in all_techs:
        u_prob = user_probs.get(tech, 0.0)
        
        if community_average and confidence_weight < 1.0:
            c_prob = community_average.get(tech, 0.0)
            # 融合公式
            final_prob = confidence_weight * u_prob + (1 - confidence_weight) * c_prob
            
            # 生成解释
            if confidence_weight > 0.8:
                expl = f"基于历史数据({counts.get(tech, 0)}次)，参与概率为 {final_prob:.1%}"
            else:
                expl = f"数据较少，融合社区均值后概率为 {final_prob:.1%}"
        else:
            final_prob = u_prob
            expl = f"基于历史数据({counts.get(tech, 0)}次)，参与概率为 {final_prob:.1%}"
            
        final_probs[tech] = {
            "probability": round(final_prob, 4),
            "count": counts.get(tech, 0),
            "explanation": expl
        }
        
    return final_probs


def fit_time_distribution(
    timestamps: List[str],
    fallback_to_exponential: bool = True,
) -> Dict[str, Any]:
    """
    拟合活跃时间分布（Weibull 或 Exponential）。
    
    数学原理：
    1. Weibull 分布 (推荐):
       $$f(t) = \\frac{k}{\\lambda} (\\frac{t}{\\lambda})^{k-1} e^{-(t/\\lambda)^k}$$
       其中 $k$ 是形状参数，$\\lambda$ 是尺度参数。
       
    2. 指数分布 (备选):
       $$f(t) = \\lambda e^{-\\lambda t}$$
       
    3. 累积概率 (CDF) - 未来 30 天活跃概率:
       $$P(T \\le 30) = 1 - e^{-(30/\\lambda)^k}$$
       
    参数：
        timestamps: ISO 格式的时间戳列表
        fallback_to_exponential: 若 Weibull 拟合失败，是否降级为指数分布
        
    返回值：
        包含分布类型、参数、期望间隔、未来30天活跃概率的字典。
    """
    if not timestamps or len(timestamps) < 2:
        return {
            "distribution_type": "Insufficient Data",
            "params": {},
            "expected_interval_days": 0.0,
            "next_active_prob_30d": 0.0,
            "intervals": [],
            "explanation": "数据不足，无法拟合时间分布"
        }
        
    # 1. 解析时间戳并计算间隔
    try:
        dates = [date_parser.parse(ts) for ts in timestamps]
        dates.sort()
        
        intervals = []
        for i in range(len(dates) - 1):
            delta = dates[i+1] - dates[i]
            intervals.append(delta.total_seconds() / 86400.0) # 转换为天
            
        # 过滤掉极小的间隔 (如同一次 push 的多个 commit)
        intervals = [i for i in intervals if i > 0.01]
        
        if len(intervals) < 3:
             return {
                "distribution_type": "Insufficient Intervals",
                "params": {},
                "expected_interval_days": np.mean(intervals) if intervals else 0,
                "next_active_prob_30d": 0.5, # 默认值
                "intervals": intervals,
                "explanation": "有效间隔不足，无法准确拟合"
            }
            
    except Exception as e:
        return {
            "distribution_type": "Error",
            "params": {"error": str(e)},
            "expected_interval_days": 0.0,
            "next_active_prob_30d": 0.0,
            "intervals": [],
            "explanation": f"时间戳解析错误: {str(e)}"
        }

    # 2. 拟合分布
    try:
        # 尝试 Weibull 拟合
        # scipy.stats.weibull_min.fit 返回 (shape, loc, scale)
        # 我们通常固定 loc=0
        shape, loc, scale = stats.weibull_min.fit(intervals, floc=0)
        
        # 计算期望值 (Mean)
        expected_interval = stats.weibull_min.mean(shape, loc=loc, scale=scale)
        
        # 计算未来 30 天活跃概率 (CDF at t=30)
        prob_30d = stats.weibull_min.cdf(30, shape, loc=loc, scale=scale)
        
        return {
            "distribution_type": "Weibull",
            "params": {
                "shape": round(shape, 4),
                "scale": round(scale, 4)
            },
            "expected_interval_days": round(expected_interval, 2),
            "next_active_prob_30d": round(prob_30d, 4),
            "intervals": [round(i, 2) for i in intervals],
            "explanation": f"基于 Weibull 分布拟合(k={shape:.2f})，预测下次活跃倾向于在 {expected_interval:.1f} 天内"
        }
        
    except Exception as e:
        if fallback_to_exponential:
            try:
                # 降级为指数分布
                # scipy.stats.expon.fit 返回 (loc, scale)
                loc, scale = stats.expon.fit(intervals, floc=0)
                
                expected_interval = stats.expon.mean(loc=loc, scale=scale)
                prob_30d = stats.expon.cdf(30, loc=loc, scale=scale)
                
                return {
                    "distribution_type": "Exponential (Fallback)",
                    "params": {
                        "scale": round(scale, 4)
                    },
                    "expected_interval_days": round(expected_interval, 2),
                    "next_active_prob_30d": round(prob_30d, 4),
                    "intervals": [round(i, 2) for i in intervals],
                    "explanation": f"Weibull 拟合失败，降级为指数分布。平均间隔 {expected_interval:.1f} 天"
                }
            except Exception as e2:
                pass
        
        # 最终 Fallback: 简单平均
        mean_val = np.mean(intervals)
        return {
            "distribution_type": "Simple Mean (Fallback)",
            "params": {},
            "expected_interval_days": round(mean_val, 2),
            "next_active_prob_30d": 0.5,
            "intervals": [round(i, 2) for i in intervals],
            "explanation": f"拟合失败，使用简单平均值: {mean_val:.1f} 天"
        }


def calculate_match_score(
    tech_tendency: Dict[str, Any],
    target_tech: str,
    active_prob_30d: float,
    tech_weight: float = 0.7,
    active_weight: float = 0.3,
) -> Dict[str, Any]:
    """
    计算开发者与特定技术栈的匹配度。
    
    数学公式：
    $$Score = (P_{tendency} \\times 0.7) + (P_{active} \\times 0.3)$$
    
    参数：
        tech_tendency: 技术倾向分布 (calculate_topic_probability 的返回值)
        target_tech: 目标技术栈名称 (如 "Python")
        active_prob_30d: 未来30天活跃概率
        tech_weight: 技术倾向权重 (默认 0.7)
        active_weight: 活跃度权重 (默认 0.3)
        
    返回值：
        包含分数、等级和解释的字典。
    """
    # 获取目标技术的倾向概率
    # 注意：tech_tendency 的值可能是 float (Phase 1) 或 dict (Phase 2)
    # 这里做兼容处理
    tech_prob = 0.0
    
    # 尝试模糊匹配 (忽略大小写)
    target_lower = target_tech.lower()
    matched_key = None
    
    for key, value in tech_tendency.items():
        if key.lower() == target_lower:
            matched_key = key
            if isinstance(value, dict):
                tech_prob = value.get("probability", 0.0)
            else:
                tech_prob = float(value)
            break
            
    # 计算加权分数
    score = (tech_prob * tech_weight) + (active_prob_30d * active_weight)
    score = round(score, 4)
    
    # 确定匹配等级
    if score >= 0.8:
        level = "极高匹配"
    elif score >= 0.6:
        level = "高度匹配"
    elif score >= 0.4:
        level = "中等匹配"
    elif score >= 0.2:
        level = "低度契合"
    else:
        level = "不匹配"
        
    # 生成解释
    explanation = (
        f"综合评分 {score:.2f} ({level})。 "
        f"技术契合度贡献: {tech_prob * tech_weight:.2f}, "
        f"活跃度贡献: {active_prob_30d * active_weight:.2f}。"
    )
    
    if not matched_key:
        explanation += f" 注意：未在历史记录中找到 {target_tech} 相关项目。"
        
    return {
        "score": score,
        "level": level,
        "tech_contribution": round(tech_prob * tech_weight, 4),
        "active_contribution": round(active_prob_30d * active_weight, 4),
        "explanation": explanation
    }


def prepare_cold_start_data(
    username: str,
    project_count: int,
    primary_language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    为冷启动场景准备数据。
    
    流程：
    1. 判断是否需要冷启动
    2. 计算置信度权重
    3. 选择合适的社区基准数据
    4. 返回冷启动参数
    
    参数：
        username: GitHub 用户名
        project_count: 用户项目数
        primary_language: 用户主要编程语言（可选）
    
    返回值：
        包含冷启动参数的字典：
        {
            "is_cold_start": bool,
            "confidence_weight": float,
            "developer_type": str,
            "community_tendency": dict,
            "community_time_params": dict,
        }
    """
    cold_start_flag = is_cold_start(project_count)
    
    if not cold_start_flag:
        # 数据充分，无需冷启动处理
        return {
            "is_cold_start": False,
            "confidence_weight": 1.0,
            "developer_type": None,
            "community_tendency": None,
            "community_time_params": None,
        }
    
    # 启用冷启动逻辑
    confidence_weight = calculate_confidence_weight(project_count)
    developer_type = get_developer_type_guess(primary_language)
    community_tendency = get_community_average_tendency(developer_type)
    
    # 根据项目数判断活跃度等级
    activity_level = "active" if project_count > 3 else "sporadic"
    community_time_params = get_community_average_time_params(activity_level)
    
    return {
        "is_cold_start": True,
        "confidence_weight": confidence_weight,
        "developer_type": developer_type,
        "community_tendency": community_tendency,
        "community_time_params": community_time_params,
    }


def fetch_or_generate_developer_analysis(
    username: str,
    user_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    获取开发者分析数据，优先从名人堂，否则生成冷启动数据。
    
    流程：
    1. 检查是否在名人堂中
    2. 如果在，直接返回预置数据
    3. 如果不在，检查项目数
    4. 项目数不足时返回冷启动数据
    
    参数：
        username: GitHub 用户名
        user_data: 用户的基本数据字典（包含 project_count、primary_language 等）
    
    返回值：
        分析数据字典（包含冷启动标记、置信度等）
    """
    # 检查名人堂
    fame_data = get_developer_from_fame_hall(username)
    if fame_data:
        return {
            "source": "fame_hall",
            "is_cold_start": False,
            "confidence_weight": 1.0,
            "data": fame_data,
        }
    
    # 如果不在名人堂，检查用户数据
    if user_data is None:
        user_data = {}
    
    project_count = user_data.get("project_count", 0)
    primary_language = user_data.get("primary_language")
    
    # 准备冷启动数据
    cold_start_data = prepare_cold_start_data(
        username, project_count, primary_language
    )
    
    return {
        "source": "cold_start",
        "user_data": user_data,
        "cold_start_params": cold_start_data,
    }


class DataPreprocessor:
    """
    数据预处理器：集中管理冷启动逻辑和社区融合。
    """
    
    def __init__(self, cold_start_threshold: int = 5):
        """
        初始化预处理器。
        
        参数：
            cold_start_threshold: 触发冷启动的项目数阈值
        """
        self.cold_start_threshold = cold_start_threshold
    
    def process(
        self,
        username: str,
        project_count: int,
        user_tendency: Optional[Dict[str, float]] = None,
        primary_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户数据，应用冷启动逻辑。
        
        参数：
            username: GitHub 用户名
            project_count: 项目数
            user_tendency: 用户的技术倾向分布（可选）
            primary_language: 主要编程语言（可选）
        
        返回值：
            处理后的数据（包含冷启动标记和融合分布）
        """
        if is_cold_start(project_count, self.cold_start_threshold):
            # 冷启动场景
            confidence_weight = calculate_confidence_weight(
                project_count, self.cold_start_threshold
            )
            developer_type = get_developer_type_guess(primary_language)
            community_tendency = get_community_average_tendency(developer_type)
            
            # 如果有用户倾向数据，则融合
            if user_tendency:
                final_tendency = blend_user_and_community(
                    user_tendency, community_tendency, confidence_weight
                )
            else:
                final_tendency = community_tendency
            
            return {
                "username": username,
                "is_cold_start": True,
                "confidence_weight": confidence_weight,
                "developer_type": developer_type,
                "tendency": final_tendency,
                "explanation": f"项目数({project_count})不足，已融合社区数据权重:{confidence_weight:.1%}",
            }
        else:
            # 数据充分，无需冷启动
            return {
                "username": username,
                "is_cold_start": False,
                "confidence_weight": 1.0,
                "developer_type": get_developer_type_guess(primary_language),
                "tendency": user_tendency or {},
                "explanation": "数据充分，使用用户数据",
            }


if __name__ == "__main__":
    # 示例：测试冷启动逻辑
    print("=" * 70)
    print("Phase 1 - 冷启动处理示例")
    print("=" * 70)
    
    # 示例 1：冷启动场景
    print("\n示例 1: 新手开发者（项目数 = 2）")
    cold_start_data = prepare_cold_start_data(
        username="newbie",
        project_count=2,
        primary_language="Python"
    )
    print(json.dumps(cold_start_data, ensure_ascii=False, indent=2))
    
    # 示例 2：名人堂开发者
    print("\n示例 2: 名人堂开发者")
    fame_data = fetch_or_generate_developer_analysis("torvalds")
    print(json.dumps(fame_data, ensure_ascii=False, indent=2))
    
    # 示例 3：数据预处理器
    print("\n示例 3: 使用 DataPreprocessor")
    processor = DataPreprocessor(cold_start_threshold=5)
    
    # 冷启动场景
    result1 = processor.process(
        username="user1",
        project_count=3,
        user_tendency={"Python": 0.5, "JavaScript": 0.3},
        primary_language="Python"
    )
    print("\n冷启动结果:")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 正常场景
    result2 = processor.process(
        username="user2",
        project_count=15,
        user_tendency={"Python": 0.6, "JavaScript": 0.25, "Go": 0.15},
        primary_language="Python"
    )
    print("\n正常场景结果:")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
