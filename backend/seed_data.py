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

# 预设的顶级开源社区代表开发者（Top 40）
# 数据来源：GitStar Ranking + OpenRank + GitHub Trending
# 这些是真实存在的高影响力开发者，用作社区基准数据和演示案例
FAMOUS_DEVELOPERS_PROFILE = {
    # === 顶级明星开发者 (1-10) ===
    "sindresorhus": {
        "name": "Sindre Sorhus",
        "bio": "Full-Time Open Source Maintainer",
        "company": "Open Source",
        "location": "Thailand",
        "public_repos": 1200,
        "followers": 65000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "TypeScript", "Node.js", "Swift"],
    },
    "kamranahmedse": {
        "name": "Kamran Ahmed",
        "bio": "Developer Roadmaps Creator",
        "company": "roadmap.sh",
        "location": "Dubai",
        "public_repos": 120,
        "followers": 82000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["JavaScript", "Go", "DevOps", "Architecture"],
    },
    "donnemartin": {
        "name": "Donne Martin",
        "bio": "System Design & Interview Prep",
        "company": "Open Source",
        "location": "USA",
        "public_repos": 80,
        "followers": 78000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "AWS", "System Design", "Interview"],
    },
    "jwasham": {
        "name": "John Washam",
        "bio": "Coding Interview University",
        "company": "Google",
        "location": "USA",
        "public_repos": 45,
        "followers": 91000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "C++", "Algorithms", "Interview"],
    },
    "karpathy": {
        "name": "Andrej Karpathy",
        "bio": "AI Researcher, ex-Tesla AI Director",
        "company": "OpenAI",
        "location": "San Francisco",
        "public_repos": 35,
        "followers": 125000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "PyTorch", "Deep Learning", "AI"],
    },
    "vinta": {
        "name": "Vinta Chen",
        "bio": "Awesome Python Creator",
        "company": "Open Source",
        "location": "Taiwan",
        "public_repos": 95,
        "followers": 48000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "Django", "Go", "Backend"],
    },
    "trekhleb": {
        "name": "Oleksii Trekhleb",
        "bio": "JavaScript Algorithms Author",
        "company": "Open Source",
        "location": "Europe",
        "public_repos": 80,
        "followers": 62000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "Algorithms", "React", "TypeScript"],
    },
    "trimstray": {
        "name": "Trimstray",
        "bio": "Security & DevOps Expert",
        "company": "Open Source",
        "location": "Poland",
        "public_repos": 65,
        "followers": 38000,
        "developer_type": "DevOps/Infrastructure",
        "tech_keywords": ["Bash", "Security", "Linux", "DevOps"],
    },
    "torvalds": {
        "name": "Linus Torvalds",
        "bio": "Linux Kernel Creator",
        "company": "Linux Foundation",
        "location": "Portland, USA",
        "public_repos": 100,
        "followers": 180000,
        "developer_type": "DevOps/Infrastructure",
        "tech_keywords": ["C", "Linux", "Kernel", "Git"],
    },
    "yyx990803": {
        "name": "Evan You",
        "bio": "Vue.js Creator",
        "company": "Vue.js",
        "location": "Singapore",
        "public_repos": 150,
        "followers": 95000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "TypeScript", "Vue", "Vite"],
    },
    
    # === 语言设计者 & 核心贡献者 (11-20) ===
    "gvanrossum": {
        "name": "Guido van Rossum",
        "bio": "Python Creator",
        "company": "Microsoft",
        "location": "USA",
        "public_repos": 50,
        "followers": 45000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "Language Design", "PEP"],
    },
    "matz": {
        "name": "Yukihiro Matsumoto",
        "bio": "Ruby Creator",
        "company": "Ruby Association",
        "location": "Japan",
        "public_repos": 60,
        "followers": 28000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Ruby", "Language Design", "C"],
    },
    "antirez": {
        "name": "Salvatore Sanfilippo",
        "bio": "Redis Creator",
        "company": "Open Source",
        "location": "Italy",
        "public_repos": 90,
        "followers": 32000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["C", "Redis", "Databases", "Systems"],
    },
    "bnoordhuis": {
        "name": "Ben Noordhuis",
        "bio": "Node.js Core Contributor",
        "company": "Open Source",
        "location": "Netherlands",
        "public_repos": 200,
        "followers": 8000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Node.js", "JavaScript", "C++"],
    },
    "tj": {
        "name": "TJ Holowaychuk",
        "bio": "Go, Node.js Pioneer",
        "company": "Open Source",
        "location": "Canada",
        "public_repos": 400,
        "followers": 42000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Go", "Node.js", "JavaScript", "CLI"],
    },
    "defunkt": {
        "name": "Chris Wanstrath",
        "bio": "GitHub Co-Founder",
        "company": "GitHub",
        "location": "San Francisco",
        "public_repos": 180,
        "followers": 58000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Ruby", "Git", "JavaScript", "GitHub"],
    },
    "fabpot": {
        "name": "Fabien Potencier",
        "bio": "Symfony Creator",
        "company": "Symfony",
        "location": "France",
        "public_repos": 120,
        "followers": 21000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["PHP", "Symfony", "Backend", "Framework"],
    },
    "chriscoyier": {
        "name": "Chris Coyier",
        "bio": "CSS-Tricks Founder",
        "company": "CodePen",
        "location": "USA",
        "public_repos": 95,
        "followers": 28000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["CSS", "HTML", "JavaScript", "Design"],
    },
    "addyosmani": {
        "name": "Addy Osmani",
        "bio": "Google Chrome Team",
        "company": "Google",
        "location": "USA",
        "public_repos": 250,
        "followers": 45000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "Performance", "Chrome", "Web"],
    },
    "paulirish": {
        "name": "Paul Irish",
        "bio": "Google Chrome DevTools",
        "company": "Google",
        "location": "USA",
        "public_repos": 180,
        "followers": 52000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "Chrome", "DevTools", "Performance"],
    },
    
    # === AI/ML 领域 (21-25) ===
    "goodfeli": {
        "name": "Ian Goodfellow",
        "bio": "GAN Inventor",
        "company": "DeepMind",
        "location": "USA",
        "public_repos": 25,
        "followers": 38000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "TensorFlow", "GANs", "Deep Learning"],
    },
    "fchollet": {
        "name": "François Chollet",
        "bio": "Keras Creator",
        "company": "Google",
        "location": "USA",
        "public_repos": 40,
        "followers": 68000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "Keras", "TensorFlow", "Deep Learning"],
    },
    "lexfridman": {
        "name": "Lex Fridman",
        "bio": "AI Researcher & Podcaster",
        "company": "MIT",
        "location": "USA",
        "public_repos": 35,
        "followers": 42000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "Deep Learning", "Research", "AI"],
    },
    "fastai": {
        "name": "Jeremy Howard",
        "bio": "Fast.ai Founder",
        "company": "fast.ai",
        "location": "Australia",
        "public_repos": 80,
        "followers": 28000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "PyTorch", "Deep Learning", "Education"],
    },
    "soumith": {
        "name": "Soumith Chintala",
        "bio": "PyTorch Co-Creator",
        "company": "Meta",
        "location": "USA",
        "public_repos": 95,
        "followers": 25000,
        "developer_type": "AI/ML Developer",
        "tech_keywords": ["Python", "PyTorch", "C++", "Deep Learning"],
    },
    
    # === 系统/性能专家 (26-30) ===
    "brendangregg": {
        "name": "Brendan Gregg",
        "bio": "Performance Engineering Expert",
        "company": "Intel",
        "location": "USA",
        "public_repos": 65,
        "followers": 28000,
        "developer_type": "DevOps/Infrastructure",
        "tech_keywords": ["C", "Performance", "Linux", "Systems"],
    },
    "kelseyhightower": {
        "name": "Kelsey Hightower",
        "bio": "Kubernetes Advocate",
        "company": "Google",
        "location": "USA",
        "public_repos": 120,
        "followers": 82000,
        "developer_type": "DevOps/Infrastructure",
        "tech_keywords": ["Go", "Kubernetes", "Cloud", "DevOps"],
    },
    "jessfraz": {
        "name": "Jessie Frazelle",
        "bio": "Containers & Security Expert",
        "company": "Open Source",
        "location": "USA",
        "public_repos": 180,
        "followers": 35000,
        "developer_type": "DevOps/Infrastructure",
        "tech_keywords": ["Go", "Docker", "Security", "Linux"],
    },
    "mjackson": {
        "name": "Michael Jackson",
        "bio": "React Router Creator",
        "company": "Remix",
        "location": "USA",
        "public_repos": 140,
        "followers": 38000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "React", "TypeScript", "Web"],
    },
    "zpao": {
        "name": "Paul O'Shannessy",
        "bio": "React Core Team",
        "company": "Meta",
        "location": "USA",
        "public_repos": 85,
        "followers": 12000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "React", "Flow", "Web"],
    },
    
    # === 数据工程 & 开源工具 (31-40) ===
    "kennethreitz": {
        "name": "Kenneth Reitz",
        "bio": "Requests Library Author",
        "company": "Open Source",
        "location": "USA",
        "public_repos": 280,
        "followers": 28000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "Requests", "CLI", "API"],
    },
    "jaredpalmer": {
        "name": "Jared Palmer",
        "bio": "Formik & Turborepo Creator",
        "company": "Vercel",
        "location": "USA",
        "public_repos": 95,
        "followers": 22000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["TypeScript", "React", "Monorepo", "Tools"],
    },
    "getify": {
        "name": "Kyle Simpson",
        "bio": "You Don't Know JS Author",
        "company": "Open Source",
        "location": "USA",
        "public_repos": 120,
        "followers": 35000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "Education", "Async", "Functional"],
    },
    "jakevdp": {
        "name": "Jake VanderPlas",
        "bio": "Python Data Science Author",
        "company": "Google",
        "location": "USA",
        "public_repos": 110,
        "followers": 18000,
        "developer_type": "Data Engineer",
        "tech_keywords": ["Python", "NumPy", "Pandas", "Visualization"],
    },
    "miguelgrinberg": {
        "name": "Miguel Grinberg",
        "bio": "Flask Mega-Tutorial Author",
        "company": "Open Source",
        "location": "Ireland",
        "public_repos": 95,
        "followers": 15000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Python", "Flask", "WebSockets", "Tutorial"],
    },
    "wycats": {
        "name": "Yehuda Katz",
        "bio": "Ember.js & Rust Core",
        "company": "Tilde",
        "location": "USA",
        "public_repos": 200,
        "followers": 28000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "Rust", "Ember", "Ruby"],
    },
    "dhh": {
        "name": "David Heinemeier Hansson",
        "bio": "Ruby on Rails Creator",
        "company": "Basecamp",
        "location": "Denmark",
        "public_repos": 85,
        "followers": 92000,
        "developer_type": "Backend Developer",
        "tech_keywords": ["Ruby", "Rails", "Web", "Startup"],
    },
    "rauchg": {
        "name": "Guillermo Rauch",
        "bio": "Vercel CEO, Next.js Creator",
        "company": "Vercel",
        "location": "USA",
        "public_repos": 120,
        "followers": 88000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "React", "Next.js", "Serverless"],
    },
    "sebmarkbage": {
        "name": "Sebastian Markbåge",
        "bio": "React Core Team Lead",
        "company": "Meta",
        "location": "USA",
        "public_repos": 45,
        "followers": 18000,
        "developer_type": "Frontend Developer",
        "tech_keywords": ["JavaScript", "React", "Architecture", "Concurrency"],
    },
    "octocat": {
        "name": "The Octocat",
        "bio": "GitHub Mascot",
        "company": "GitHub",
        "location": "San Francisco",
        "public_repos": 8,
        "followers": 21000,
        "developer_type": "Frontend Developer",
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
