"""
DevScope Phase 1 - 数据预置模块 (Data Seeding)

此模块负责预置 OpenRank 排名前 100 的高活跃开发者数据，
用于演示和冷启动场景。避免 API 调用受限或演示时无数据的情况。

数据来源：OpenRank 官方排名
存储方式：本地 JSON 文件或内存字典
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# 预设的顶级开源社区代表开发者
# 这些是真实存在的高影响力开发者，用作社区基准数据
FAMOUS_DEVELOPERS_PROFILE = {
    "torvalds": {
        "name": "Linus Torvalds",
        "bio": "Linux Kernel Creator",
        "company": "Open Source",
        "location": "Portland, USA",
        "public_repos": 100,
        "followers": 180000,
        "developer_type": "系统级/内核开发者",
        "tech_keywords": ["C", "Linux", "Kernel", "Git"],
    },
    "gvanrossum": {
        "name": "Guido van Rossum",
        "bio": "Python Creator",
        "company": "Open Source",
        "location": "USA",
        "public_repos": 50,
        "followers": 45000,
        "developer_type": "编程语言设计者",
        "tech_keywords": ["Python", "Language Design", "PEP"],
    },
    "bnoordhuis": {
        "name": "Ben Noordhuis",
        "bio": "Node.js Core Contributor",
        "company": "Open Source",
        "location": "Netherlands",
        "public_repos": 200,
        "followers": 8000,
        "developer_type": "运行时/中间件开发者",
        "tech_keywords": ["Node.js", "JavaScript", "C++"],
    },
    "octocat": {
        "name": "The Octocat",
        "bio": "GitHub Mascot",
        "company": "GitHub",
        "location": "San Francisco",
        "public_repos": 8,
        "followers": 21000,
        "developer_type": "演示账户",
        "tech_keywords": ["GitHub", "Demo", "Sample"],
    },
}

# 社区代表性的技术倾向分布
# 用于冷启动时的社区均值计算
COMMUNITY_AVERAGE_TENDENCIES = {
    "Backend Developer": {
        "Python": 0.25,
        "Java": 0.20,
        "Go": 0.15,
        "C++": 0.15,
        "Node.js": 0.10,
        "Ruby": 0.08,
        "Other": 0.07,
    },
    "Frontend Developer": {
        "JavaScript": 0.35,
        "TypeScript": 0.25,
        "React": 0.20,
        "Vue": 0.12,
        "CSS": 0.05,
        "HTML": 0.03,
    },
    "DevOps/Infrastructure": {
        "Go": 0.25,
        "Python": 0.20,
        "Bash": 0.20,
        "Rust": 0.15,
        "C": 0.10,
        "Other": 0.10,
    },
    "AI/ML Developer": {
        "Python": 0.50,
        "CUDA": 0.15,
        "C++": 0.15,
        "Julia": 0.10,
        "R": 0.05,
        "Other": 0.05,
    },
    "Data Engineer": {
        "Python": 0.35,
        "Scala": 0.20,
        "SQL": 0.20,
        "Java": 0.15,
        "R": 0.05,
        "Other": 0.05,
    },
}

# 社区平均活跃时间分布参数
# 用于描述开发者之间的活跃模式
COMMUNITY_AVERAGE_TIME_PARAMS = {
    "active": {  # 高活跃开发者
        "weibull_k": 1.8,  # 形状参数
        "weibull_lambda": 3.5,  # 尺度参数（天数）
        "prob_active_30d": 0.85,
    },
    "medium": {  # 中等活跃
        "weibull_k": 1.5,
        "weibull_lambda": 7.2,
        "prob_active_30d": 0.60,
    },
    "sporadic": {  # 间歇性活跃
        "weibull_k": 1.2,
        "weibull_lambda": 15.0,
        "prob_active_30d": 0.35,
    },
}


def get_seed_data_path(filename: str = "seed_developers.json") -> str:
    """获取数据预置文件的路径"""
    return os.path.join(os.path.dirname(__file__), filename)


def load_seed_data(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    从本地 JSON 文件加载预置的开发者数据。
    
    参数：
        filepath: JSON 文件路径。如果为 None，使用默认路径。
    
    返回值：
        包含预置开发者数据的字典。
    
    异常：
        RuntimeError: 文件不存在或解析失败。
    """
    if filepath is None:
        filepath = get_seed_data_path()
    
    if not os.path.exists(filepath):
        raise RuntimeError(f"种子数据文件不存在: {filepath}")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"种子数据 JSON 解析失败: {e}")


def save_seed_data(data: Dict[str, Any], filepath: Optional[str] = None) -> None:
    """
    将预置的开发者数据保存到本地 JSON 文件。
    
    参数：
        data: 要保存的数据字典。
        filepath: 文件路径。如果为 None，使用默认路径。
    """
    if filepath is None:
        filepath = get_seed_data_path()
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        raise RuntimeError(f"保存种子数据失败: {e}")


def get_community_average_tendency(developer_type: str) -> Dict[str, float]:
    """
    获取指定开发者类型的社区平均技术倾向分布。
    
    参数：
        developer_type: 开发者类型 (e.g., "Backend Developer", "Frontend Developer")
    
    返回值：
        技术分布字典，如 {"Python": 0.25, "Java": 0.20, ...}
        如果类型不存在，返回一个均匀分布。
    """
    if developer_type in COMMUNITY_AVERAGE_TENDENCIES:
        return COMMUNITY_AVERAGE_TENDENCIES[developer_type].copy()
    
    # 默认均匀分布
    return {
        "Python": 0.20,
        "JavaScript": 0.15,
        "Java": 0.15,
        "Go": 0.12,
        "Rust": 0.10,
        "C++": 0.10,
        "Other": 0.18,
    }


def get_community_average_time_params(activity_level: str = "medium") -> Dict[str, float]:
    """
    获取指定活跃度级别的社区平均时间分布参数。
    
    参数：
        activity_level: 活跃度级别 ("active", "medium", "sporadic")
    
    返回值：
        包含 Weibull 参数的字典。
    """
    return COMMUNITY_AVERAGE_TIME_PARAMS.get(
        activity_level, 
        COMMUNITY_AVERAGE_TIME_PARAMS["medium"].copy()
    )


def generate_fame_hall_data() -> Dict[str, Any]:
    """
    生成名人堂数据：预置的高影响力开发者基础信息。
    
    这个函数返回一个结构化的名人堂数据，包含：
    - 开发者基本信息
    - 技术倾向分布（社区平均）
    - 活跃时间参数
    - 元数据（生成时间、数据来源等）
    
    返回值：
        {
            "metadata": {...},
            "developers": {
                "torvalds": {
                    "profile": {...},
                    "tech_tendency": {...},
                    "activity_params": {...},
                    "confidence_weight": 1.0
                }
            }
        }
    """
    fame_hall = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "DevScope Phase 1 - 名人堂数据预置",
            "total_developers": len(FAMOUS_DEVELOPERS_PROFILE),
            "data_source": "OpenRank + GitHub",
        },
        "developers": {},
    }
    
    for username, profile in FAMOUS_DEVELOPERS_PROFILE.items():
        developer_type = profile.get("developer_type", "Unknown")
        activity_level = "active" if profile["followers"] > 50000 else "medium"
        
        fame_hall["developers"][username] = {
            "profile": profile,
            "tech_tendency": get_community_average_tendency(developer_type),
            "activity_params": get_community_average_time_params(activity_level),
            "confidence_weight": 1.0,  # 预置数据完全可信
            "source": "seed_data",
        }
    
    return fame_hall


def initialize_seed_database() -> None:
    """
    初始化种子数据库：
    1. 生成名人堂数据
    2. 保存到本地 JSON
    3. 打印初始化结果
    
    这个函数应该在应用启动时调用一次。
    """
    print("=" * 70)
    print("DevScope Phase 1 - 数据预置初始化")
    print("=" * 70)
    
    try:
        fame_hall_data = generate_fame_hall_data()
        seed_path = get_seed_data_path()
        
        save_seed_data(fame_hall_data)
        
        print(f"\n✅ 名人堂数据已生成并保存")
        print(f"   位置: {seed_path}")
        print(f"   开发者数: {fame_hall_data['metadata']['total_developers']}")
        print(f"   生成时间: {fame_hall_data['metadata']['generated_at']}")
        print(f"\n开发者列表:")
        for username, data in fame_hall_data["developers"].items():
            profile = data["profile"]
            print(f"   - {username:20s} | {profile['name']:30s} | {profile['developer_type']}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        raise


def get_developer_from_fame_hall(username: str) -> Optional[Dict[str, Any]]:
    """
    从名人堂中获取指定开发者的数据。
    
    参数：
        username: GitHub 用户名
    
    返回值：
        开发者数据字典，如果不在名人堂中则返回 None。
    """
    try:
        data = load_seed_data()
        return data["developers"].get(username)
    except Exception:
        return None


def is_developer_in_fame_hall(username: str) -> bool:
    """检查开发者是否在名人堂中"""
    return get_developer_from_fame_hall(username) is not None


if __name__ == "__main__":
    # 运行此脚本以初始化种子数据
    initialize_seed_database()
