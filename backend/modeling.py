"""
DevScope Phase 1 - 数据预处理与冷启动模块

此模块实现 Phase 1 中与数据预置相关的功能：
- 冷启动处理（当用户项目数 < 5 时）
- 置信度权重计算
- 社区数据融合

详细的数学建模（拉普拉斯平滑、Weibull 分布拟合等）
将在 Phase 2 的完整 modeling.py 中实现。
"""

from typing import Dict, List, Optional, Any
import json

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
