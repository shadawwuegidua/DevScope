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
    
    prompt = f"""
System: 你是一个代码行为分析专家。请根据给定的 git commit 历史，预测该开发者下一次提交可能涉及的内容。使用中文输出，给出做出该预测的理由。
Input: {json.dumps(recent_commits)}
Output Format (JSON):
{{
  "focus_area": "string (short tag)",
  "commit_type": "string (feat/fix/docs/style/refactor)",
  "prediction": "string (max 40 words)"
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
            timeout=5.0 # 5 seconds timeout as per guide
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned empty content.")
            return None
            
        data = json.loads(content)
        
        return NextCommitPrediction(
            focus_area=data.get("focus_area", "Unknown"),
            commit_type=data.get("commit_type", "Unknown"),
            prediction=data.get("prediction", "No prediction available")
        )

    except asyncio.TimeoutError:
        logger.error("LLM call timed out.")
        return None
    except ImportError:
        logger.error("openai library not installed.")
        return None
    except Exception as e:
        logger.error(f"Error during LLM prediction: {e}")
        return None
