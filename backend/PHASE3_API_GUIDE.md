# DevScope Phase 3 - Backend API

## 概述

这是 DevScope Phase 3 的后端 API 实现，提供最小可用的 RESTful 接口用于：
- 前端页面展示
- PPT 截图
- 比赛交付演示

## 项目结构

```
backend/
├── main.py              # Phase 3 - FastAPI 应用入口
├── github_client.py     # Phase 1 - GitHub API 客户端
├── modeling.py          # Phase 2 - 统计建模核心逻辑
├── seed_data.py         # Phase 1 - 数据预置（名人堂）
├── requirements.txt     # Python 依赖
└── README.md           # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

在 `backend/` 目录创建 `.env` 文件：

```bash
GITHUB_TOKEN=your_github_token_here
```

> 注意：不设置 Token 也可以使用，但 API 调用次数限制会更严格（60次/小时）。
> 设置 Token 可提升到 5000次/小时。

### 3. 启动服务

```bash
python main.py
```

或使用 uvicorn 直接运行：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 4. 访问 API 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 接口规范

### 健康检查

```http
GET /health
```

**响应示例：**
```json
{
  "status": "ok",
  "timestamp": "2025-12-27T10:30:45.123456"
}
```

---

### 分析开发者（核心接口）

```http
GET /api/analyze/{username}?skip_cache=false
```

**参数：**
- `username` (path, required): GitHub 用户名，长度 1-39 字符
- `skip_cache` (query, optional): 是否跳过缓存，默认 false

**响应模型：DeveloperAnalysis**

```json
{
  "username": "torvalds",
  "is_cold_start": false,
  "confidence_weight": 1.0,
  "persona": {
    "username": "torvalds",
    "name": "Linus Torvalds",
    "bio": "...",
    "avatar_url": "https://...",
    "company": "The Linux Foundation",
    "location": "Portland, OR",
    "public_repos": 145,
    "followers": 250000,
    "following": 0,
    "created_at": "2011-09-03T15:06:01Z"
  },
  "tech_tendency": [
    {
      "category": "C",
      "probability": 0.85,
      "explanation": "基于历史数据(125次)，参与概率为 85.0%"
    },
    {
      "category": "Shell",
      "probability": 0.12,
      "explanation": "基于历史数据(18次)，参与概率为 12.0%"
    }
  ],
  "time_prediction": {
    "expected_interval_days": 45.3,
    "next_active_prob_30d": 0.62,
    "distribution_type": "Weibull"
  },
  "match_scores": null,
  "primary_language": "C",
  "cold_start_note": null
}
```

**错误响应：**

| 状态码 | 说明 | 示例 |
|-------|------|------|
| 404 | 用户不存在 | `{"error": "GitHub 用户 nonexistent 不存在"}` |
| 503 | API 限流 | `{"error": "GitHub API 请求次数已达限制，请 1 小时后重试"}` |
| 400 | 数据获取失败 | `{"error": "数据获取失败: ..."}` |
| 500 | 服务器错误 | `{"error": "服务器内部错误: ..."}` |

---

### 计算技术栈匹配度

```http
POST /api/match
Content-Type: application/json

{
  "username": "torvalds",
  "target_techs": ["C", "Python", "Rust"]
}
```

**请求体：MatchRequest**
- `username` (string, required): GitHub 用户名
- `target_techs` (array of strings, required): 目标技术栈列表

**响应示例：**

```json
{
  "username": "torvalds",
  "target_techs": ["C", "Python", "Rust"],
  "match_scores": {
    "C": {
      "score": 0.815,
      "level": "极高匹配",
      "tech_contribution": 0.595,
      "active_contribution": 0.22,
      "explanation": "综合评分 0.81 (极高匹配)。技术契合度贡献: 0.60, 活跃度贡献: 0.22。"
    },
    "Python": {
      "score": 0.125,
      "level": "低度契合",
      "tech_contribution": 0.025,
      "active_contribution": 0.1,
      "explanation": "综合评分 0.13 (低度契合)。技术契合度贡献: 0.02, 活跃度贡献: 0.10。注意：未在历史记录中找到 Python 相关项目。"
    }
  },
  "timestamp": "2025-12-27T10:35:22.456789"
}
```

---

## 数据结构说明

### DeveloperAnalysis（完整开发者分析）

| 字段 | 类型 | 说明 |
|------|------|------|
| `username` | string | GitHub 用户名 |
| `is_cold_start` | boolean | 是否启用冷启动补救逻辑 |
| `confidence_weight` | float | 置信度权重，范围 [0.0, 1.0]，值越大数据越可信 |
| `persona` | PersonaInfo | 开发者基本信息 |
| `tech_tendency` | List[PredictionResult] | 技术倾向预测列表，已按概率降序排列 |
| `time_prediction` | TimePrediction | 活跃时间预测（项目数<5 时为 null） |
| `match_scores` | Dict or null | 技术栈匹配分值（可通过 /api/match 获取） |
| `primary_language` | string | 主要编程语言 |
| `cold_start_note` | string or null | 冷启动说明文案 |

### PersonaInfo（开发者信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| `username` | string | GitHub 用户名 |
| `name` | string or null | 真名 |
| `bio` | string or null | 个人简介 |
| `avatar_url` | string or null | 头像 URL |
| `company` | string or null | 公司 |
| `location` | string or null | 位置 |
| `public_repos` | int | 公开仓库数 |
| `followers` | int | 关注者数 |
| `following` | int | 正在关注数 |
| `created_at` | string or null | 账户创建时间 (ISO 8601) |

### PredictionResult（单个技术预测）

| 字段 | 类型 | 说明 |
|------|------|------|
| `category` | string | 技术领域名称，如 "Python"、"React" |
| `probability` | float | 概率值，范围 [0.0, 1.0] |
| `explanation` | string | 自动生成的解释文本 |

### TimePrediction（活跃时间预测）

| 字段 | 类型 | 说明 |
|------|------|------|
| `expected_interval_days` | float | 预期活跃间隔（天） |
| `next_active_prob_30d` | float | 未来 30 天活跃概率，范围 [0.0, 1.0] |
| `distribution_type` | string | 拟合分布类型："Weibull" 或 "Exponential" |

---

## 核心逻辑说明

### 1. 数据获取流程

```
GitHub 用户名
    ↓
获取用户基本信息 (github_client.get_user)
    ↓
获取仓库列表 (github_client.get_repos)
    ↓
提取编程语言和话题
    ↓
获取提交历史 (github_client.get_user_commit_activity)
    ↓
使用 modeling.py 进行统计分析
    ↓
返回 DeveloperAnalysis
```

### 2. 冷启动逻辑

当用户项目数 < 5 时：

1. **冷启动检测**：`is_cold_start(project_count)`
2. **置信度计算**：`confidence_weight = min(1.0, project_count / 10)`
3. **社区融合**：融合社区同类型开发者的平均数据
   - 根据主要编程语言猜测开发者类型（前端、后端、AI等）
   - 获取该类型的社区平均倾向分布
   - 使用加权融合公式：`P_final = w * P_user + (1-w) * P_community`
4. **返回标记**：`is_cold_start=true`，附加冷启动说明文案

### 3. 技术倾向计算

基于 **拉普拉斯平滑** (Laplace Smoothing) 的多项分布：

$$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$$

其中：
- $n_i$：技术领域 $T_i$ 的项目数
- $N$：总项目数
- $K$：技术类别总数
- $\alpha$：平滑参数（默认 1.0）

### 4. 活跃时间分布拟合

使用两种统计分布：

**Weibull 分布**（推荐）：
- 形状参数 $k$ 描述活跃率随时间的变化趋势
- 尺度参数 $\lambda$ 描述平均活跃间隔
- 计算 CDF 得到未来 30 天活跃概率

**Exponential 分布**（备选）：
- 用于拟合失败的 Fallback
- 假设活跃是无记忆随机过程

### 5. 匹配度计算

公式：
$$Score = (P_{tendency} \times 0.7) + (P_{active} \times 0.3)$$

分级：
- **> 0.8**：极高匹配
- **0.6-0.8**：高度匹配
- **0.4-0.6**：中等匹配
- **0.2-0.4**：低度契合
- **< 0.2**：不匹配

---

## 开发模式

### 热重载开发

```bash
python main.py
```

修改代码后自动重启服务。

### 生产模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

使用多个 worker 进程提升并发能力。

---

## CORS 配置

API 已配置 CORS，允许以下来源：
- `http://localhost:5173` (Vite 默认端口)
- `http://localhost:3000` (Next.js 默认端口)

如需添加其他来源，编辑 `main.py` 中的 CORSMiddleware 配置。

---

## 常见问题

### Q: API 返回 404，但用户确实存在？
**A:** 可能是 GitHub API 限流。设置 `GITHUB_TOKEN` 环境变量，限额会从 60/小时 提升到 5000/小时。

### Q: 冷启动逻辑何时触发？
**A:** 当用户公开仓库数 < 5 时自动触发。此时会融合社区同类型开发者的数据以提升预测准确性。

### Q: 时间预测为什么有时是 null？
**A:** 当项目数 < 5 或提交历史为空时，时间预测被禁用，以确保结果可靠性。

### Q: 如何修改匹配度的权重？
**A:** 编辑 `/api/analyze` 或 `/api/match` 中的 `modeling.calculate_match_score` 调用，修改 `tech_weight` 和 `active_weight` 参数。

---

## 约束说明

本实现严格遵循以下约束：

✅ **已严格遵循**：
- 禁止修改 modeling.py 中的任何算法逻辑 → 仅调用 modeling 的公共函数
- 禁止引入深度学习/黑箱模型 → 仅使用 SciPy 统计分布
- 禁止设计数据库/缓存 → 无持久化存储，每次都实时计算
- 所有输出直接来源 Phase 2 函数 → 无额外处理或修改

❌ **未实现的功能**（不属于 Phase 3 范围）：
- 持久化缓存 → 可由前端实现缓存策略
- 用户认证/授权 → 本服务为开放式 API
- 数据库 → 演示时无需存储

---

## 测试示例

### 使用 curl 测试

**查询已知开发者：**
```bash
curl "http://localhost:8000/api/analyze/torvalds"
```

**查询新手开发者（冷启动）：**
```bash
curl "http://localhost:8000/api/analyze/newly-joined-user"
```

**计算匹配度：**
```bash
curl -X POST "http://localhost:8000/api/match" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "torvalds",
    "target_techs": ["C", "Python"]
  }'
```

### 使用 Python requests 测试

```python
import requests

# 分析开发者
response = requests.get("http://localhost:8000/api/analyze/torvalds")
print(response.json())

# 计算匹配度
response = requests.post(
    "http://localhost:8000/api/match",
    json={
        "username": "torvalds",
        "target_techs": ["C", "Rust"]
    }
)
print(response.json())
```

---

## 许可证

本项目属于 OpenRank 竞赛 W 赛道作品。

---

## 贡献指南

本项目在 Phase 3 阶段，后续开发按照 `Prompt_context.md` 的规范进行。

**禁止事项**：
- 修改 modeling.py 的算法逻辑
- 引入 sklearn、TensorFlow、PyTorch 等黑箱 ML 模型
- 设计持久化数据库或缓存系统
