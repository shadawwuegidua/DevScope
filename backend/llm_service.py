import os
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

class NextCommitPrediction(BaseModel):
    focus_area: str = Field(..., description="关注领域")
    commit_type: str = Field(..., description="预测的提交类型")
    prediction: str = Field(..., description="简短的预测描述")

async def predict_next_commit(commit_messages: List[str]) -> Optional[NextCommitPrediction]:
    """
    Uses LLM to predict the next commit based on recent commit messages.
    
    Args:
        commit_messages: A list of recent commit messages.
        
    Returns:
        NextCommitPrediction object or None if prediction fails or LLM is not configured.
    """
    
    api_key = os.environ.get("LLM_API_KEY")
    # Default to ECNU API base URL if not provided
    base_url = os.environ.get("LLM_API_BASE", "https://chat.ecnu.edu.cn/open/api/v1")
    # Default to ecnu-plus model if not provided
    model = os.environ.get("LLM_MODEL", "ecnu-plus")

    if not api_key:
        logger.warning("LLM_API_KEY not found. Skipping LLM prediction.")
        return None

    if not commit_messages:
        logger.info("No commit messages provided for prediction.")
        return None

    # Limit to last 10 commits to avoid token limits and focus on recent activity
    recent_commits = commit_messages[:10]
    
    # 构建包含实际 commit messages 的 prompt
    commits_text = "\n".join([f"- {msg}" for msg in recent_commits if msg.strip()])
    if not commits_text:
        logger.info("No valid commit messages for prediction.")
        return None
    
    prompt = f"""
System: 你是一个代码行为分析专家。请根据给定的 git commit 历史，预测该开发者下一次提交可能涉及的内容。使用中文输出，必须指出可能是与什么topic，repository相关的内容。

Recent Commit Messages:
{commits_text}

Output Format (JSON):
{{
  "focus_area": "string (short tag)",
  "commit_type": "string (feat/fix/docs/style/refactor)",
  "prediction": "string (最多四十字)"
}}
"""

    try:
        from openai import AsyncOpenAI
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = AsyncOpenAI(**client_kwargs)

        logger.info(f"Calling LLM ({model}) for next commit prediction...")
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            ),
            timeout=10.0  # 增加到 10 秒超时
        )

        if not response or not response.choices:
            logger.warning("LLM returned empty response.")
            return None
            
        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned empty content.")
            return None
        
        # 尝试解析 JSON，如果失败则记录详细错误
        try:
            data = json.loads(content)
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM JSON response: {json_err}. Content: {content[:200]}")
            return None
        
        # 验证必需字段
        if not isinstance(data, dict):
            logger.error(f"LLM returned non-dict data: {type(data)}")
            return None
        
        return NextCommitPrediction(
            focus_area=data.get("focus_area", "Unknown"),
            commit_type=data.get("commit_type", "Unknown"),
            prediction=data.get("prediction", "No prediction available")
        )

    except asyncio.TimeoutError:
        logger.error("LLM call timed out after 10 seconds.")
        return None
    except ImportError:
        logger.error("openai library not installed.")
        return None
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error in LLM response: {json_err}")
        return None
    except Exception as e:
        logger.error(f"Error during LLM prediction: {e}", exc_info=True)
        return None
