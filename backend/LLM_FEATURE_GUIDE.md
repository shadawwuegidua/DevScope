# LLM 增强功能实现指南：基于提交历史的智能预测

## 1. 变更说明
**注意**：本指南明确**废除**原项目中“禁止引入深度学习/黑箱模型”的约束。
本阶段目标是引入大语言模型（LLM）API，对用户的 Commit History 进行语义分析，以预测下一次提交的**具体内容**和**类型**。

## 2. 功能需求
通过分析用户最近的 Commit Messages（已由 `github_client.py` 获取），预测：
1.  **关注点 (Focus Area)**: 开发者当前关注的功能模块（如 "Auth", "UI/UX", "Database"）。
2.  **下一次提交类型 (Next Commit Type)**: 预测是 Bug Fix, Feature, Refactor 等。
3.  **预测描述 (Prediction)**: 一句简短的自然语言描述（如 "可能继续修复登录页面的样式问题"）。

## 3. 技术架构规范

### 3.1 依赖管理
- 引入 `openai` 库（或其他兼容 OpenAI 接口的 SDK）。
- 在 `requirements.txt` 中添加依赖。

### 3.2 环境变量 (.env)
必须支持以下配置以灵活切换模型提供商：
- `LLM_API_KEY`: API 密钥
- `LLM_API_BASE`: API 基础 URL (用于支持 Azure 或自定义代理)
- `LLM_MODEL`: 模型名称 (e.g., `gpt-3.5-turbo`, `gpt-4`)

### 3.3 模块设计
新建 `backend/llm_service.py`，包含以下核心逻辑：
- **异步调用**: 必须使用 `async/await` 以避免阻塞 FastAPI 主线程。
- **超时控制**: 设置严格的超时时间（建议 3-5秒），防止拖慢整体 API 响应。
- **降级策略 (Fallback)**: 如果 LLM 调用失败、超时或未配置 Key，**必须**返回默认的空值或基于规则的简单推测，**严禁**导致整个 `/analyze` 接口报错 500。

### 3.4 Prompt 设计 (参考)
```text
System: 你是一个代码行为分析专家。请根据给定的 git commit 历史，预测该开发者下一次提交可能涉及的内容。
Input: [Commit List]
Output Format (JSON):
{
  "focus_area": "string (short tag)",
  "commit_type": "string (feat/fix/docs/style/refactor)",
  "prediction": "string (max 20 words)"
}
```

## 4. 数据模型变更
在 `backend/main.py` 中扩展 `DeveloperAnalysis` 模型：

```python
class NextCommitPrediction(BaseModel):
    focus_area: str = Field(..., description="关注领域")
    commit_type: str = Field(..., description="预测的提交类型")
    prediction: str = Field(..., description="简短的预测描述")

class DeveloperAnalysis(BaseModel):
    # ... 原有字段 ...
    next_commit_prediction: Optional[NextCommitPrediction] = Field(
        None, 
        description="基于 LLM 的下一次提交预测"
    )
```

## 5. Copilot 行为准则
当要求 Copilot 实现此功能时，Copilot 必须：
1.  **优先检查环境**: 检查 `.env` 是否配置了 LLM 相关变量。
2.  **防御性编程**: 编写 LLM 调用代码时，始终包裹在 `try-except` 块中。
3.  **保持轻量**: 不要引入 LangChain 等重型框架，直接使用原生 HTTP 请求或轻量级 SDK。
4.  **用户提示**: 如果 LLM 未配置，在日志中输出警告，但不要抛出异常给前端。
