# DevScope 后端模块 - Phase 1 数据抓取层

**版本**: Phase 1 v3.0  
**更新日期**: 2024-12-18  
**新功能**: 40位顶级开发者预置数据 + 冷启动处理

---

## 项目结构

```
backend/
├── github_client.py          # GitHub API 客户端封装
├── opendigger_client.py      # OpenDigger 数据加载客户端
├── seed_data.py              # 🆕 数据预置模块（40位开发者名人堂）
├── modeling.py               # 🆕 冷启动处理与数据融合
├── seed_developers.json      # 🆕 预置开发者数据（自动生成）
├── test_data_fetch.py        # 数据抓取功能测试脚本
├── test_modeling.py          # 🆕 预置数据与冷启动测试
├── verify_phase1_complete.py # 🆕 Phase 1 综合验证脚本
├── requirements.txt          # Python 依赖列表
├── README.md                 # 本文档
├── PHASE1_SEEDING_GUIDE.md   # 🆕 数据预置详细指南
├── VERIFICATION.md           # 验证步骤清单
└── ...（其他文档）
```

---

## 🎯 Phase 1 核心功能

### ✅ 数据抓取
- GitHub REST API 客户端（速率限制管理）
- OpenDigger JSON 数据加载

### 🆕 数据预置（Seeding）
- **40位顶级开发者离线数据**
- 分类覆盖：Frontend(14) | Backend(14) | AI/ML(6) | DevOps(5) | Data(1)
- 包含：Linus Torvalds, Guido van Rossum, Evan You, Andrej Karpathy等

### 🆕 冷启动处理
- 项目数 < 5 时自动触发社区数据融合
- 数学公式：$P_{final} = w \cdot P_{user} + (1-w) \cdot P_{community}$
- 置信度权重：$w = \min(1.0, N/10)$

---

## 40位预置开发者概览

### 🎨 前端开发 (14位)
```
sindresorhus, yyx990803(Evan You), trekhleb, chriscoyier,
addyosmani, paulirish, mjackson, zpao, jaredpalmer,
getify, wycats, rauchg, sebmarkbage, octocat
```

### ⚙️ 后端开发 (14位)
```
kamranahmedse, donnemartin, jwasham, vinta,
gvanrossum(Python创始人), matz(Ruby创始人), antirez(Redis),
bnoordhuis, tj, defunkt, fabpot, kennethreitz,
miguelgrinberg, dhh(Rails创始人)
```

### 🤖 AI/ML (6位)
```
karpathy(前Tesla AI总监), goodfeli(GAN发明者),
fchollet(Keras), lexfridman, fastai, soumith(PyTorch)
```

### 🔧 DevOps/基础设施 (5位)
```
trimstray, torvalds(Linux), brendangregg,
kelseyhightower, jessfraz
```

### 📊 数据工程 (1位)
```
jakevdp(NumPy/Pandas专家)
```

**详细说明**: 参见 [PHASE1_SEEDING_GUIDE.md](PHASE1_SEEDING_GUIDE.md)

---

## 安装与环境配置

### 1. 虚拟环境与依赖安装

已完成（你已执行 `python -m venv DevScope` 和 `pip install -r .\backend\requirements.txt`）。

### 2. GitHub Token 配置

**关键：必须设置 GitHub Token 以提升 API 速率限制。**

在 PowerShell 中执行以下命令来设置环境变量：

```powershell
$env:GITHUB_TOKEN = "your_github_token_here"
```

**或者** 创建 `.env` 文件（推荐用于团队共享，避免频繁输入）：

在 `backend/` 目录下创建 `.env` 文件：
```
GITHUB_TOKEN=your_github_token_here
```

然后在 Python 脚本顶部安装 `python-dotenv`：
```
pip install python-dotenv
```

在脚本中加载：
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 核心模块原理

### github_client.py - GitHub API 客户端

**目的**：封装 GitHub REST API 调用，处理身份验证和速率限制。

**核心特性**：

1. **速率限制管理**
   - GitHub 匿名请求限制：60 次/小时
   - 使用 Token 后限制：5000 次/小时
   - 客户端监听响应头 `X-RateLimit-Remaining` 和 `X-RateLimit-Reset`
   - 当剩余配额过低（默认 ≤2）时，自动休眠至重置时间

2. **数据获取接口**
   - `get_user(username)` - 获取用户基本信息（公开资料、粉丝数等）
   - `get_repos(username, per_page, max_pages)` - 获取用户仓库列表（支持分页）
   - `get_commits(owner, repo, since, until, per_page, max_pages)` - 获取仓库提交历史
   - `get_user_commit_activity(username, limit_repos, per_repo_commits)` - 聚合用户跨仓库的提交时间戳

3. **错误处理**
   - 网络异常捕获（超时、连接失败）
   - HTTP 错误码检测（4xx/5xx）
   - 详细错误提示

**示例**：
```python
from github_client import GitHubClient

client = GitHubClient(token="YOUR_GITHUB_TOKEN")

# 获取用户信息
user = client.get_user("torvalds")
print(user["login"], user["public_repos"])  # Linus Torvalds 的公开仓库数

# 获取提交历史
commits = client.get_commits("torvalds", "linux", per_page=50, max_pages=1)
for c in commits:
    print(c["commit"]["author"]["date"], c["commit"]["message"])
```

---

### opendigger_client.py - OpenDigger 数据加载

**目的**：加载并解析 OpenDigger 静态 JSON 数据源，用于补充 GitHub 官方 API 的历史活跃度指标。

**核心函数**：

1. **load_opendigger_json(path_or_url, timeout)**
   - 支持从远程 URL 或本地文件加载
   - 自动 JSON 解析与错误处理
   - 默认超时 30 秒

2. **get_developer_metrics(username, data)**
   - 从加载的数据中查找特定开发者的指标
   - 兼容 dict 型（用户名作键）和 list 型（逐项搜索）数据结构

**示例**：
```python
from opendigger_client import load_opendigger_json, get_developer_metrics

# 从 URL 加载
data = load_opendigger_json("https://api.openrank.com/developer/metrics.json")

# 或从本地文件加载
data = load_opendigger_json("./opendigger_data.json")

# 查询开发者指标
metrics = get_developer_metrics("torvalds", data)
if metrics:
    print("活跃度指标:", metrics)
else:
    print("未找到该开发者")
```

---

## 使用指南：test_data_fetch.py

这是一个综合性测试脚本，验证数据抓取层的完整功能链路。

### 基础用法

在虚拟环境中，进入 `backend/` 目录，执行：

```powershell
# 使用默认用户 (Linus Torvalds)
python test_data_fetch.py

# 或指定其他 GitHub 用户
python test_data_fetch.py --username octocat

# 指定 OpenDigger 数据源 (可选)
python test_data_fetch.py --username torvalds --opendigger https://api.example.com/data.json
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `--username` | `torvalds` | 要测试的 GitHub 用户名 |
| `--opendigger` | `None` | OpenDigger JSON 数据的 URL 或本地路径 |

### 输出说明

脚本按顺序输出以下几部分：

1. **GitHub 用户信息**
   ```
   == GitHub 用户信息 ==
   {'login': 'torvalds', 'name': 'Linus Torvalds', 'public_repos': 123, ...}
   ```
   验证点：用户名、公开仓库数是否符合预期

2. **仓库列表示例**
   ```
   == 仓库列表示例 (最多 5 个) ==
   - linux | stars=15000 | forks=5000
   - subsurface-for-dirk | stars=500 | forks=200
   ...
   ```
   验证点：仓库数据是否完整、Stars/Forks 数值是否合理

3. **单仓库提交历史**
   ```
   == 仓库 'torvalds/linux' 的提交样例 (最多 10 条) ==
   - 2024-12-17T10:30:00Z abc123def Fix bug in scheduler
   - 2024-12-16T15:45:00Z xyz789uvw Update documentation
   ...
   ```
   验证点：提交时间戳格式是否正确、提交信息是否有效

4. **用户级提交时间序列**
   ```
   == 用户级提交时间序列 (聚合，最多 5 仓库) ==
   总计 42 条时间戳样本，示例前 10 条：
   - 2024-12-17T10:30:00Z
   - 2024-12-16T15:45:00Z
   ...
   ```
   验证点：时间戳数量、时间顺序是否合理

5. **OpenDigger 指标（可选）**
   ```
   == OpenDigger 指标样例 ==
   找到开发者 torvalds 指标，前 10 个字段预览：
   {'metric1': 0.8, 'metric2': 1234, ...}
   ```

---

## 验证步骤

### 步骤 1：验证 GitHub 客户端

在 PowerShell 中，设置环境变量后执行测试脚本：

```powershell
cd c:\Users\Zhuang\Documents\My Stuff\DevScope\backend
$env:GITHUB_TOKEN = "your_github_token_here"
python test_data_fetch.py --username octocat
```

**预期结果**：
- ✅ 无异常崩溃
- ✅ 获取到有效的用户信息（login、name、public_repos 字段非空）
- ✅ 获取到至少 1 个仓库
- ✅ 仓库中获取到至少 5 条提交记录
- ✅ 聚合出有效的时间戳列表

**常见问题排查**：
| 症状 | 原因 | 解决 |
|------|------|------|
| `404 Not Found` | 用户名不存在 | 检查用户名拼写，用 octocat 或 torvalds 测试 |
| `403 Forbidden` | Token 无效或过期 | 重新获取 Token，确保环境变量正确设置 |
| `requests.Timeout` | 网络连接超时 | 检查网络连接，增加 timeout 参数 |
| `RateLimitError` | 请求过于频繁 | 脚本会自动休眠，或减少 max_pages 参数 |

### 步骤 2：验证 OpenDigger 客户端（可选）

若有 OpenDigger 数据源 URL，可测试：

```powershell
python test_data_fetch.py --username octocat --opendigger "https://api.example.com/developers.json"
```

或使用本地 JSON 文件：
```powershell
python test_data_fetch.py --username octocat --opendigger "./sample_opendigger.json"
```

### 步骤 3：单元验证（高级）

在 Python REPL 中逐个验证模块：

```python
from github_client import GitHubClient
import os

os.environ["GITHUB_TOKEN"] = "your_github_token_here"

# 初始化客户端
client = GitHubClient()

# 测试 get_user
user = client.get_user("octocat")
assert "login" in user
print("✓ get_user 工作正常")

# 测试 get_repos
repos = client.get_repos("octocat", per_page=5, max_pages=1)
assert len(repos) > 0
print(f"✓ get_repos 工作正常 (找到 {len(repos)} 个仓库)")

# 测试 get_commits
if repos:
    r = repos[0]
    commits = client.get_commits(r["owner"]["login"], r["name"], per_page=10, max_pages=1)
    assert len(commits) > 0
    print(f"✓ get_commits 工作正常 (找到 {len(commits)} 条提交)")
```

---

## 速率限制详解

GitHub API 速率限制是关键问题，特别是在大规模数据采集时。

**无 Token 请求**：
- 限制：60 请求/小时
- 用途：快速测试、公开数据

**有 Token 请求**：
- 限制：5000 请求/小时 ≈ 83 请求/分钟
- 用途：生产环境、授权用户数据

**客户端处理逻辑**：

1. 每个响应都包含三个关键头：
   - `X-RateLimit-Limit` - 总配额
   - `X-RateLimit-Remaining` - 剩余次数
   - `X-RateLimit-Reset` - 重置时间戳（Unix 秒）

2. 当 `Remaining ≤ min_remaining`（默认 2）时：
   ```python
   sleep_seconds = reset_time - current_time
   time.sleep(sleep_seconds)  # 自动等待至重置
   ```

3. 建议优化：
   - 减少 `per_page` 和 `max_pages` 参数以降低请求数
   - 缓存结果以避免重复请求
   - 异步并发请求（Phase 2 优化项）

---

## 错误处理指南

所有模块都遵循**显式异常处理**原则，抛出 `RuntimeError` 附带详细错误消息：

```python
try:
    user = client.get_user("invalid_user_12345")
except RuntimeError as e:
    print(f"错误: {e}")  # "获取用户信息失败: 404 Not Found"
```

---

## Phase 1 完成度检查表

- [x] `GitHubClient` 类实现（用户/仓库/提交数据获取）
- [x] 速率限制自动处理
- [x] `opendigger_client` 模块（本地/远程数据加载）
- [x] 综合测试脚本 `test_data_fetch.py`
- [x] 依赖声明 `requirements.txt`
- [x] 本文档（使用指南 + 原理说明）

**下一步**（Phase 2）：
- 数学建模模块 `modeling.py`
- 概率分布拟合（多项分布、Weibull 分布）
- 时间序列分析

---

## 常见问题 (FAQ)

**Q：为什么要用 Token？**  
A：无 Token 限制太低（60/小时），Token 提升至 5000/小时。在生产环境中，建议使用 GitHub App 或 OAuth App 实现用户级认证。

**Q：test_data_fetch.py 需要改动参数吗？**  
A：不需要。默认参数 `--username torvalds` 已为大量数据优化。若网络不稳定，可减少 `limit_repos` 和 `per_repo_commits`。

**Q：如何在团队中安全地共享 Token？**  
A：
1. **不要**提交 Token 到 Git（添加 `.env` 到 `.gitignore`）
2. 使用 GitHub Secrets（CI/CD 环境）
3. 使用团队 GitHub App（推荐）

**Q：如何扩展功能（如获取 Issue 数据）？**  
A：在 `GitHubClient` 中添加新方法：
```python
def get_issues(self, owner: str, repo: str, per_page: int = 100) -> List[Dict[str, Any]]:
    # 类似 get_commits 的实现
    pass
```

---

## 贡献者指南

修改本模块时，请确保：
1. 所有函数包含 docstring（参数、返回值、异常说明）
2. 涉及数学的函数标注 LaTeX 公式
3. 新增的 HTTP 调用都集成速率限制处理
4. 修改后运行 `test_data_fetch.py` 验证

---

**文档版本**：v1.0 (Phase 1)  
**最后更新**：2025-12-17  
**维护者**：DevScope 开发团队
