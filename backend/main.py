"""
DevScope Phase 3 - 后端 API 服务 (FastAPI)

此模块实现最小可用后端 API，用于：
- 前端页面展示
- PPT 截图
- 比赛交付演示

核心逻辑：
1. 集成 github_client.py 获取用户数据
2. 集成 modeling.py 进行统计分析
3. 通过 Pydantic 模型序列化结果
4. 返回严格符合数据结构的 JSON

**严格约束**：
- 禁止修改 modeling.py 中的任何算法逻辑
- 禁止引入深度学习/黑箱模型
- 禁止设计数据库/缓存/用户系统
- 禁止过度抽象、重构项目结构
- 所有输出必须直接来源于 Phase 2 的函数返回值
"""

from typing import Dict, List, Optional, Any
import math
from datetime import datetime, timedelta
import json
import logging
import os

from dotenv import load_dotenv

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from fastapi import FastAPI, HTTPException, Query, Path, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from github_client import GitHubClient
import modeling
from llm_service import predict_next_commit, NextCommitPrediction
from opendigger_client import (
    load_opendigger_json,
    get_developer_metrics,
    get_user_openrank,
    get_repo_openrank,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 确保输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# 确保github_client的日志也显示
logging.getLogger('github_client').setLevel(logging.INFO)


# =============================================================================
# Pydantic 数据模型（严格遵循 Prompt_context.md 4.1 规范）
# =============================================================================

class PredictionResult(BaseModel):
    """单个技术倾向预测结果"""
    category: str = Field(..., description="技术领域，如 'Python'")
    probability: float = Field(..., ge=0.0, le=1.0, description="概率值 0.0 - 1.0")
    explanation: str = Field(..., description="自动生成的解释文本")


class TimePrediction(BaseModel):
    """活跃时间预测结果"""
    expected_interval_days: float = Field(..., ge=0, description="预期活跃间隔（天）")
    next_active_prob_30d: float = Field(..., ge=0.0, le=1.0, description="未来30天活跃概率")
    distribution_type: str = Field(..., description="'Weibull' 或 'Exponential'")


class PersonaInfo(BaseModel):
    """开发者画像信息"""
    username: str = Field(..., description="GitHub 用户名")
    name: Optional[str] = Field(None, description="真名")
    bio: Optional[str] = Field(None, description="个人简介")
    avatar_url: Optional[str] = Field(None, description="头像 URL")
    company: Optional[str] = Field(None, description="公司")
    location: Optional[str] = Field(None, description="位置")
    public_repos: int = Field(default=0, description="公开仓库数")
    followers: int = Field(default=0, description="关注者数")
    following: int = Field(default=0, description="正在关注数")
    created_at: Optional[str] = Field(None, description="账户创建时间")
    openrank: Optional[float] = Field(None, description="OpenRank 值")


class CommitInfo(BaseModel):
    """提交信息"""
    message: str = Field(..., description="提交信息")
    repo_name: str = Field(..., description="仓库名称")
    date: str = Field(..., description="提交日期")
    url: str = Field(..., description="提交链接")


class RecentTopicContribution(BaseModel):
    """近期贡献的 Topic 与仓库映射"""
    topic: str = Field(..., description="推断的 Topic 或标签")
    language: Optional[str] = Field(None, description="仓库主要语言")
    repo: str = Field(..., description="仓库全名 owner/repo")
    repo_url: str = Field(..., description="仓库链接")
    repo_openrank: Optional[float] = Field(None, description="仓库 OpenRank")


class DeveloperAnalysis(BaseModel):
    """完整的开发者分析结果（主要数据结构）"""
    username: str = Field(..., description="GitHub 用户名")
    is_cold_start: bool = Field(..., description="是否启用冷启动补救逻辑")
    confidence_weight: float = Field(..., ge=0.0, le=1.0, description="置信度权重 w")
    persona: PersonaInfo = Field(..., description="开发者基本信息")
    next_commit_prediction: Optional[NextCommitPrediction] = Field(
        None, 
        description="基于 LLM 的下一次提交预测"
    )
    tech_tendency: List[PredictionResult] = Field(
        default_factory=list,
        description="技术倾向预测列表（按概率降序）"
    )
    topic_tendency: List[PredictionResult] = Field(
        default_factory=list,
        description="Topic 倾向预测列表（按概率降序，优先用于展示）"
    )
    language_tendency: List[PredictionResult] = Field(
        default_factory=list,
        description="编程语言倾向预测列表（按概率降序，作为辅助信息）"
    )
    time_prediction: Optional[TimePrediction] = Field(
        None,
        description="活跃时间预测（项目数<5 时为 None）"
    )
    recent_commits: List[CommitInfo] = Field(
        default_factory=list,
        description="最近提交记录"
    )
    contribution_calendar: List[str] = Field(
        default_factory=list,
        description="过去一年的提交日期列表"
    )
    recent_topic_contributions: List[RecentTopicContribution] = Field(
        default_factory=list,
        description="近期贡献的 Topic/语言/仓库及仓库 OpenRank"
    )
    match_scores: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="技术栈匹配分值（可选）"
    )
    primary_language: Optional[str] = Field(None, description="主要编程语言")
    cold_start_note: Optional[str] = Field(
        None,
        description="冷启动时的说明文案"
    )


class MatchRequest(BaseModel):
    """匹配度接口请求"""
    username: str = Field(..., description="GitHub 用户名")
    target_techs: List[str] = Field(
        ...,
        description="目标技术栈列表，如 ['Python', 'React']"
    )


# =============================================================================
# FastAPI 应用初始化
# =============================================================================

app = FastAPI(
    title="DevScope Backend API",
    description="基于开源生态数据的开发者画像与行为倾向分析 API",
    version="1.0.0"
)

# 配置 CORS（允许前端 Vite 默认端口 5173 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 GitHub 客户端（使用环境变量中的 Token）
github_client = GitHubClient()
logger.info("GitHub 客户端初始化完成")

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"收到请求: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    try:
        response = await call_next(request)
        logger.info(f"响应: {request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"请求处理异常: {request.method} {request.url.path} - {str(e)}")
        raise


# =============================================================================
# 数据处理辅助函数
# =============================================================================

def _extract_primary_language(repos: List[Dict]) -> Optional[str]:
    """
    从仓库列表中提取主要编程语言。
    
    策略：计算频次，返回最常见的语言。
    """
    languages = [r.get("language") for r in repos if r.get("language")]
    if not languages:
        return None
    from collections import Counter
    return Counter(languages).most_common(1)[0][0]


def _extract_languages(repos: List[Dict]) -> List[str]:
    """返回仓库语言列表（过滤 None）。"""
    return [r.get("language") for r in repos if r.get("language")]


def _extract_repo_topics(repos: List[Dict]) -> List[str]:
    """
    从仓库列表中提取所有话题（Topic）。不做语言兜底，保持 Topic 的纯粹性。
    """
    topics = []
    for repo in repos:
        repo_topics = repo.get("topics") or []
        if repo_topics:
            topics.extend(repo_topics)
    return topics


def _extract_repo_topics_weighted(repos: List[Dict], commit_counts_by_repo: Optional[Dict[str, int]] = None) -> List[str]:
    """根据仓库星标数对 topics 加权，降低均匀概率的出现。

    权重方案：
    - 星标权重：ws = int(log1p(stargazers_count))
    - 提交权重：wc = int(log1p(user_commits_in_repo))（若提供）
    - 总权重：weight = max(1, ws + wc)
    例如：stars=100→ws=4；commits=50→wc=3；则 weight=7。
    """
    weighted: List[str] = []
    for repo in repos:
        repo_topics = repo.get("topics") or []
        if not repo_topics:
            continue
        stars = 0
        try:
            stars = int(repo.get("stargazers_count") or 0)
        except Exception:
            stars = 0
        ws = int(math.log1p(stars))
        wc = 0
        # 提交权重按 full_name 命中
        if commit_counts_by_repo:
            key = repo.get("full_name") or (
                f"{repo.get('owner', {}).get('login', '')}/{repo.get('name', '')}"
            )
            try:
                commits_in_repo = int(commit_counts_by_repo.get(key, 0))
                wc = int(math.log1p(commits_in_repo))
            except Exception:
                wc = 0
        weight = max(1, ws + wc)
        for t in repo_topics:
            # 重复追加以实现加权计数
            weighted.extend([t] * weight)
    return weighted


def _sort_predictions_by_probability(
    predictions: Dict[str, Dict[str, Any]]
) -> List[PredictionResult]:
    """
    将预测结果按概率降序排列，转换为 Pydantic 模型列表。
    """
    sorted_preds = sorted(
        predictions.items(),
        key=lambda x: x[1].get("probability", 0),
        reverse=True
    )
    return [
        PredictionResult(
            category=category,
            probability=data["probability"],
            explanation=data["explanation"]
        )
        for category, data in sorted_preds
    ]


# =============================================================================
# 核心 API 接口
# =============================================================================

@app.get("/health", tags=["Health Check"])
async def health_check(request: Request):
    """健康检查端点"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


async def _analysis_generator(username: str, client_host: str = "unknown"):
    """
    Core analysis logic as an async generator.
    Yields:
        {"type": "progress", "value": int, "message": str}
        {"type": "result", "data": DeveloperAnalysis}
    """
    logger.info(f"收到分析请求 (Stream): username={username}, client={client_host}")
    
    try:
        # Step 1: 获取用户基本信息
        yield {"type": "progress", "value": 10, "message": f"正在获取用户 {username} 的基本信息..."}
        logger.info(f"开始获取用户信息: {username}")
        user_info = github_client.get_user(username)
        logger.info(f"用户信息获取成功: {user_info.get('login', 'unknown')}")
        
        # Step 2: 获取用户仓库列表
        yield {"type": "progress", "value": 20, "message": "用户信息获取成功，正在获取仓库列表..."}
        logger.info(f"开始获取仓库列表: {username}")
        # 合并拥有与参与贡献的仓库
        repos = github_client.get_user_repos_union(username)
        logger.info(f"仓库列表获取成功: {len(repos)} 个仓库")
        
        if not repos:
            logger.warning(f"用户 {username} 没有公开仓库")
            raise HTTPException(
                status_code=404,
                detail=f"用户 {username} 没有公开仓库"
            )
        
        # Step 3: 提取关键数据
        yield {"type": "progress", "value": 30, "message": f"找到 {len(repos)} 个仓库，正在提取关键数据..."}
        project_count = len(repos)
        primary_language = _extract_primary_language(repos)
        repo_languages = _extract_languages(repos)
        logger.info(
            f"提取数据: 项目数={project_count}, 主要语言={primary_language}, languages={len(repo_languages)}"
        )
        
        # Step 4: 获取提交历史
        yield {"type": "progress", "value": 40, "message": "正在分析最近提交历史与活跃度..."}
        logger.info(f"开始获取提交历史: {username}")
        commit_activity = github_client.get_user_commit_activity(
            username, 
            limit_repos=min(20, project_count),
            repos=repos  # 显式传入已排序的 repo 列表，确保分析真正活跃的仓库
        )
        commit_times = commit_activity.get("commit_times", [])
        recent_commits_data = commit_activity.get("recent_commits", [])
        commit_counts_by_repo = commit_activity.get("commit_counts_by_repo", {})
        logger.info(f"提交历史获取成功: {len(commit_times)} 条提交记录")

        # 基于星标与提交次数加权计算 Topic 列表
        repo_topics = _extract_repo_topics_weighted(repos, commit_counts_by_repo)
        logger.info(f"加权 Topic 计算完成: topics={len(repo_topics)}")

        # Step 3.1: 组装“近期贡献的 Topic/语言/仓库/OpenRank”列表
        yield {"type": "progress", "value": 50, "message": "正在构建近期贡献图谱..."}
        recent_topic_contributions: List[RecentTopicContribution] = []
        try:
            sorted_repos_by_commit = sorted(
                commit_counts_by_repo.items(), key=lambda x: x[1], reverse=True
            )
            for repo_full, _ in sorted_repos_by_commit[:5]:  # 取前 5 个最近活跃仓库
                owner, name = repo_full.split("/", 1)
                repo_meta = next(
                    (
                        r
                        for r in repos
                        if (r.get("full_name") == repo_full)
                        or (
                            r.get("name") == name
                            and r.get("owner", {}).get("login") == owner
                        )
                    ),
                    {},
                )
                topics = repo_meta.get("topics") or []
                topic = topics[0] if topics else (repo_meta.get("language") or "Unspecified")
                language = repo_meta.get("language")
                repo_url = repo_meta.get("html_url") or f"https://github.com/{repo_full}"

                repo_openrank = None
                try:
                    repo_openrank = get_repo_openrank(owner, name, timeout=8)
                except Exception as e:
                    logger.warning(f"仓库 OpenRank 获取失败 {repo_full}: {e}")

                recent_topic_contributions.append(
                    RecentTopicContribution(
                        topic=topic or "Unspecified",
                        language=language,
                        repo=repo_full,
                        repo_url=repo_url,
                        repo_openrank=repo_openrank,
                    )
                )
        except Exception as e:
            logger.warning(f"构建近期贡献列表失败: {e}")
        
        # Step 4.1: LLM 预测
        yield {"type": "progress", "value": 60, "message": "正在使用 LLM 预测下一次提交..."}
        commit_messages = [c.get("message", "") for c in recent_commits_data]
        next_commit_pred = None
        try:
            next_commit_pred = await predict_next_commit(commit_messages)
        except Exception as e:
            logger.warning(f"LLM 预测失败，继续处理: {e}")
            next_commit_pred = None
        
        # Step 5: 冷启动检测和数据融合
        yield {"type": "progress", "value": 70, "message": "正在计算统计模型与社区数据融合..."}
        is_cold = modeling.is_cold_start(project_count)
        confidence_weight = modeling.calculate_confidence_weight(project_count)
        
        # Step 6: 获取社区基准数据
        if is_cold:
            developer_type = modeling.get_developer_type_guess(primary_language)
            community_tendency = modeling.get_community_average_tendency(
                developer_type
            )
            community_time_params = modeling.get_community_average_time_params(
                "active" if project_count > 3 else "sporadic"
            )
        else:
            community_tendency = None
            community_time_params = None
        
        # Step 7: 计算技术倾向概率
        topic_probs = modeling.calculate_topic_probability(
            topics=repo_topics if repo_topics else [],
            alpha=1.0,
            community_average=community_tendency,
            confidence_weight=confidence_weight
        )

        language_probs = modeling.calculate_topic_probability(
            topics=repo_languages if repo_languages else ([primary_language] if primary_language else []),
            alpha=1.0,
            community_average=community_tendency,
            confidence_weight=confidence_weight
        )
        
        # Step 8: 计算活跃时间分布
        if project_count >= 5 and commit_times:
            time_pred = modeling.fit_time_distribution(commit_times)
            time_prediction = TimePrediction(
                expected_interval_days=time_pred["expected_interval_days"],
                next_active_prob_30d=time_pred["next_active_prob_30d"],
                distribution_type=time_pred["distribution_type"]
            )
        else:
            time_prediction = None
        
        # Step 9: 构建响应对象
        yield {"type": "progress", "value": 90, "message": "正在获取 OpenRank 评分..."}
        # 获取 OpenRank
        openrank_value = None
        try:
            openrank_value = get_user_openrank(username, timeout=10)
            if openrank_value is not None:
                logger.info(f"OpenRank 获取成功: {username} = {openrank_value}")
            else:
                logger.info(f"OpenRank 数据不存在: {username} (用户可能未被 OpenDigger 收录)")
        except Exception as e:
            logger.warning(f"OpenRank 获取失败: {e}")
            
        persona = PersonaInfo(
            username=username,
            name=user_info.get("name"),
            bio=user_info.get("bio"),
            avatar_url=user_info.get("avatar_url"),
            company=user_info.get("company"),
            location=user_info.get("location"),
            public_repos=user_info.get("public_repos", 0),
            followers=user_info.get("followers", 0),
            following=user_info.get("following", 0),
            created_at=user_info.get("created_at"),
            openrank=openrank_value,
        )
        
        # 转换技术倾向为预测结果列表
        topic_predictions = _sort_predictions_by_probability(topic_probs)
        language_predictions = _sort_predictions_by_probability(language_probs)
        tech_predictions = topic_predictions if topic_predictions else language_predictions

        logger.info(
            f"技术倾向: topics={len(topic_predictions)}, languages={len(language_predictions)}"
        )
        if topic_predictions:
            logger.info(
                f"前3项Topic: {[(p.category, p.probability) for p in topic_predictions[:3]]}"
            )
        else:
            logger.warning(f"Topic 倾向为空！原始数据: {topic_probs}")
        
        # 生成冷启动说明
        cold_start_note = None
        if is_cold:
            cold_start_note = (
                f"该开发者项目数({project_count})不足，已融合社区同类型开发者"
                f"({modeling.get_developer_type_guess(primary_language)})的平均数据，"
                f"置信度权重为 {confidence_weight:.1%}。预测结果仅供参考。"
            )
        
        logger.info(f"分析完成: {username}, 技术倾向数量={len(tech_predictions)}")
        
        result = DeveloperAnalysis(
            next_commit_prediction=next_commit_pred,
            username=username,
            is_cold_start=is_cold,
            confidence_weight=confidence_weight,
            persona=persona,
            tech_tendency=tech_predictions,
            topic_tendency=topic_predictions,
            language_tendency=language_predictions,
            time_prediction=time_prediction,
            match_scores=None,
            primary_language=primary_language,
            cold_start_note=cold_start_note,
            recent_commits=[CommitInfo(**c) for c in recent_commits_data],
            contribution_calendar=commit_times,
            recent_topic_contributions=recent_topic_contributions,
        )
        
        yield {"type": "progress", "value": 100, "message": "分析完成！"}
        yield {"type": "result", "data": result}
        
    except HTTPException as e:
        yield {"type": "rx_error", "data": e.detail}
        raise e
    except RuntimeError as e:
        logger.error(f"RuntimeError for {username}: {str(e)}")
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"GitHub 用户 {username} 不存在"
            )
        elif "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="GitHub API 请求次数已达限制，请 1 小时后重试"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"数据获取失败: {str(e)}"
            )
    except Exception as e:
        logger.exception(f"未处理的异常 for {username}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


@app.get("/api/analyze/{username}/stream", tags=["Analysis"])
async def analyze_developer_stream(
    request: Request,
    username: str = Path(..., min_length=1, max_length=39)
):
    """
    Streaming version of the analysis endpoint.
    Yields Server-Sent Events (SSE).
    """
    async def sse_wrapper():
        try:
            async for item in _analysis_generator(username, request.client.host if request.client else 'unknown'):
                if item["type"] == "result":
                    data = item["data"].dict()
                    yield f"data: {json.dumps({'type': 'result', 'data': data}, ensure_ascii=False)}\n\n"
                elif item["type"] == "rx_error":
                    pass
                else:
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        except HTTPException as e:
             yield f"data: {json.dumps({'type': 'error', 'message': str(e.detail)}, ensure_ascii=False)}\n\n"
        except Exception as e:
             yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_wrapper(), media_type="text/event-stream")


@app.get(
    "/api/analyze/{username}",
    response_model=DeveloperAnalysis,
    tags=["Analysis"],
    summary="分析开发者",
    description="根据 GitHub 用户名分析开发者的技术倾向和活跃预测"
)
async def analyze_developer(
    request: Request,
    username: str = Path(..., min_length=1, max_length=39, description="GitHub 用户名"),
    skip_cache: bool = Query(False, description="是否跳过缓存（仅演示用）")
) -> DeveloperAnalysis:
    """
    **核心接口：GET /api/analyze/{username}**
    (Now wraps the streaming generator)
    """
    generator = _analysis_generator(username, request.client.host if request.client else 'unknown')
    last_result = None
    async for item in generator:
        if item["type"] == "result":
            last_result = item["data"]
    
    if last_result:
        return last_result
    # If we get here, generator finished without result (error handled inside generator usually re-raises)
    raise HTTPException(status_code=500, detail="未收到分析结果")



@app.post(
    "/api/match",
    tags=["Analysis"],
    summary="计算技术栈匹配度",
    description="基于开发者的技术倾向和活跃度预测，计算与指定技术栈的匹配分值"
)
async def match_technology_stack(request: MatchRequest):
    """
    **匹配度接口：POST /api/match**
    
    输入：
    - username: GitHub 用户名
    - target_techs: 目标技术栈列表
    
    输出：
    - 基于 3.5 节公式的匹配分值及解释
    
    公式：Score = (P_tendency * 0.7) + (P_active * 0.3)
    """
    try:
        # 获取开发者分析结果
        user_info = github_client.get_user(request.username)
        repos = github_client.get_user_repos_union(request.username)
        
        if not repos:
            raise HTTPException(
                status_code=404,
                detail=f"用户 {request.username} 没有公开仓库"
            )
        
        # 提取数据
        project_count = len(repos)
        primary_language = _extract_primary_language(repos)
        repo_languages = _extract_languages(repos)
        # 显式传入 sorted repos，保证分析的一致性
        commit_activity = github_client.get_user_commit_activity(
            request.username,
            repos=repos 
        )
        commit_times = commit_activity.get("commit_times", [])
        commit_counts_by_repo = commit_activity.get("commit_counts_by_repo", {})
        # 基于星标与提交次数加权计算 Topic 列表
        repo_topics = _extract_repo_topics_weighted(repos, commit_counts_by_repo)
        
        # 计算技术倾向
        confidence_weight = modeling.calculate_confidence_weight(project_count)
        is_cold = modeling.is_cold_start(project_count)
        
        if is_cold:
            developer_type = modeling.get_developer_type_guess(primary_language)
            community_tendency = modeling.get_community_average_tendency(
                developer_type
            )
        else:
            community_tendency = None
        
        topic_probs = modeling.calculate_topic_probability(
            topics=repo_topics if repo_topics else [],
            alpha=1.0,
            community_average=community_tendency,
            confidence_weight=confidence_weight
        )

        language_probs = modeling.calculate_topic_probability(
            topics=repo_languages if repo_languages else ([primary_language] if primary_language else []),
            alpha=1.0,
            community_average=community_tendency,
            confidence_weight=confidence_weight
        )

        # Topic 优先的融合（相同 key 时 Topic 覆盖语言）
        tech_tendency = {**language_probs, **topic_probs}
        
        # 计算活跃概率（基于并集仓库的提交活动）
        if project_count >= 5 and commit_times:
            time_pred = modeling.fit_time_distribution(commit_times)
            active_prob_30d = time_pred["next_active_prob_30d"]
        else:
            active_prob_30d = 0.5  # 默认值
        
        # 计算每个目标技术的匹配度
        match_results = {}
        for target_tech in request.target_techs:
            score_info = modeling.calculate_match_score(
                tech_tendency=tech_tendency,
                target_tech=target_tech,
                active_prob_30d=active_prob_30d,
                tech_weight=0.7,
                active_weight=0.3
            )
            match_results[target_tech] = score_info
        
        return {
            "username": request.username,
            "target_techs": request.target_techs,
            "match_scores": match_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"匹配度计算失败: {str(e)}"
        )


# =============================================================================
# 错误处理
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """统一 HTTP 异常处理"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# 启动脚本
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # 使用 uvicorn 运行 FastAPI 应用
    # Host: 0.0.0.0 (所有网卡)
    # Port: 8000
    # reload: 开启热重载（开发模式）
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
