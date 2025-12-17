# Phase 1 - 数据抓取层验证指南

## 快速验证清单

### ✅ 验证 1：环境配置

```powershell
# 确认虚拟环境激活
python --version  # 应显示 Python 3.9+

# 确认依赖已安装
pip list | Select-String "requests"  # 应显示 requests 包
```

### ✅ 验证 2：GitHub Token 配置

在 PowerShell 中设置环境变量（每次会话）：
```powershell
$env:GITHUB_TOKEN = "your_github_token_here"
echo $env:GITHUB_TOKEN  # 验证设置成功
```

或创建 `.env` 文件（推荐团队使用）：
```powershell
# 在 backend 目录创建 .env 文件
"GITHUB_TOKEN=your_github_token_here" | Out-File -Encoding utf8 ".env"
```

### ✅ 验证 3：运行测试脚本

**测试 1：基础功能测试（octocat 账户）**

```powershell
cd "c:\Users\Zhuang\Documents\My Stuff\DevScope\backend"
$env:GITHUB_TOKEN = "your_github_token_here"
python test_data_fetch.py --username octocat
```

**预期输出**：
```
== GitHub 用户信息 ==
{'login': 'octocat', 'name': 'The Octocat', 'public_repos': 8, ...}

== 仓库列表示例 (最多 5 个) ==
- boysenberry-repo-1 | stars=408 | forks=25
- git-consortium | stars=525 | forks=148
...

== 仓库 'octocat/XXX' 的提交样例 (最多 10 条) ==
- 2016-12-12T23:11:00Z d09e445076... Commit message

== 用户级提交时间序列 (聚合，最多 5 仓库) ==
总计 64 条时间戳样本，示例前 10 条：
- 2016-12-12T23:11:00Z
- 2016-12-12T23:06:48Z
...
```

✅ **通过标准**：
- 无崩溃异常
- 获取到用户信息（name、public_repos 非空）
- 获取到至少 2 个仓库
- 获取到至少 10 条提交
- 聚合出时间戳列表（非空）

---

**测试 2：高活跃度用户测试（torvalds 账户）**

```powershell
python test_data_fetch.py --username torvalds
```

✅ **通过标准**：
- 成功获取 Linus Torvalds 信息
- 获取到大量 Linux 内核仓库数据

---

**测试 3：速率限制验证**

连续运行多次以测试 rate limit 处理：

```powershell
for ($i = 1; $i -le 3; $i++) {
    Write-Host "=== 第 $i 次运行 ==="
    python test_data_fetch.py --username octocat
    Start-Sleep -Seconds 2
}
```

✅ **通过标准**：
- 所有运行都成功完成
- 若触发 rate limit，脚本自动休眠后重试

---

### ✅ 验证 4：模块单元测试

在 Python REPL 中逐个验证（打开 PowerShell 进入 Python）：

```powershell
python
```

然后在 Python 交互式环境中：

```python
import os
os.environ["GITHUB_TOKEN"] = "your_github_token_here"

# ========== 测试 GitHub 客户端 ==========
from github_client import GitHubClient

client = GitHubClient()

# 测试 get_user
user = client.get_user("octocat")
assert "login" in user and user["login"] == "octocat"
print("✓ get_user 工作正常")

# 测试 get_repos
repos = client.get_repos("octocat", per_page=5, max_pages=1)
assert len(repos) > 0
assert all("name" in r and "stargazers_count" in r for r in repos)
print(f"✓ get_repos 工作正常 (获取 {len(repos)} 个仓库)")

# 测试 get_commits
repo = repos[0]
commits = client.get_commits(
    repo["owner"]["login"], 
    repo["name"], 
    per_page=10, 
    max_pages=1
)
assert len(commits) > 0
assert all("commit" in c and "author" in c["commit"] for c in commits)
print(f"✓ get_commits 工作正常 (获取 {len(commits)} 条提交)")

# 测试 get_user_commit_activity
timestamps = client.get_user_commit_activity("octocat", limit_repos=3, per_repo_commits=20)
assert len(timestamps) > 0
assert all(isinstance(ts, str) for ts in timestamps)
print(f"✓ get_user_commit_activity 工作正常 (获取 {len(timestamps)} 条时间戳)")

# ========== 测试 OpenDigger 客户端 ==========
from opendigger_client import load_opendigger_json, get_developer_metrics
import json

# 创建样例数据
sample_data = {
    "octocat": {"activity": 0.85, "stars": 1000},
    "torvalds": {"activity": 0.95, "stars": 50000}
}

# 测试 get_developer_metrics
metrics = get_developer_metrics("octocat", sample_data)
assert metrics is not None and metrics["activity"] == 0.85
print("✓ get_developer_metrics 工作正常 (dict 型数据)")

# 测试列表型数据
list_data = [
    {"username": "octocat", "activity": 0.85},
    {"username": "torvalds", "activity": 0.95}
]
metrics_list = get_developer_metrics("torvalds", list_data)
assert metrics_list is not None and metrics_list["activity"] == 0.95
print("✓ get_developer_metrics 工作正常 (list 型数据)")

# 测试本地 JSON 加载
json_path = "test_data.json"
with open(json_path, "w") as f:
    json.dump(sample_data, f)
loaded = load_opendigger_json(json_path)
assert loaded == sample_data
print("✓ load_opendigger_json 工作正常 (本地文件)")

# 清理
import os as os_module
os_module.remove(json_path)

print("\n✅ 所有单元测试通过！")
exit()
```

---

### ✅ 验证 5：错误处理测试

在 Python 中测试异常处理：

```python
from github_client import GitHubClient
import os

os.environ["GITHUB_TOKEN"] = "your_github_token_here"
client = GitHubClient()

# 测试 1：用户不存在
try:
    client.get_user("this_user_definitely_does_not_exist_12345")
except RuntimeError as e:
    print(f"✓ 捕获用户不存在错误: {e}")

# 测试 2：仓库不存在
try:
    client.get_commits("octocat", "nonexistent_repo_xyz", per_page=10, max_pages=1)
except RuntimeError as e:
    print(f"✓ 捕获仓库不存在错误: {e}")

# 测试 3：无效的 OpenDigger 路径
from opendigger_client import load_opendigger_json
try:
    load_opendigger_json("/nonexistent/path/data.json")
except RuntimeError as e:
    print(f"✓ 捕获文件读取错误: {e}")

print("\n✅ 错误处理验证通过！")
```

---

## 性能基准

在标准网络条件下，Phase 1 各模块的典型运行时间：

| 操作 | 时间 | 备注 |
|------|------|------|
| `get_user()` | 0.2-0.5s | 单个请求 |
| `get_repos(per_page=5, max_pages=1)` | 0.5-1.5s | 5 个仓库 |
| `get_commits(per_page=10, max_pages=1)` | 0.5-1.5s | 10 条提交/仓库 |
| `get_user_commit_activity()` | 2-5s | 5 个仓库，50 条提交/仓库 |
| **完整测试脚本** | **5-10s** | 取决于网络 |

---

## 调试技巧

### 启用详细日志

在客户端初始化后添加日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from github_client import GitHubClient
client = GitHubClient()
# 现在会打印详细的请求/响应信息
```

### 查看 HTTP 请求详情

```python
import requests
requests.packages.urllib3.disable_warnings()

import httplib2
httplib2.debuglevel = 1

# 然后运行客户端调用
```

### 检查速率限制状态

```python
from github_client import GitHubClient
import os

os.environ["GITHUB_TOKEN"] = "your_github_token_here"
client = GitHubClient()

# 发起一个请求
user = client.get_user("octocat")

# 从会话的最后一个响应头检查速率限制
resp = client.session.head("https://api.github.com/user")
print(f"Rate Limit Remaining: {resp.headers.get('X-RateLimit-Remaining')}")
print(f"Rate Limit Reset: {resp.headers.get('X-RateLimit-Reset')}")
```

---

## 下一步（Phase 2 预告）

- [ ] 数学建模模块 (`modeling.py`)
- [ ] 拉普拉斯平滑概率计算
- [ ] Weibull/指数分布拟合
- [ ] 时间序列分析
- [ ] 缓存层集成（SQLite/Redis）

---

**验证完成标准**：✅ 所有 5 个验证流程通过 → Phase 1 完成 → 可进入 Phase 2

---

**文档版本**：v1.0  
**最后更新**：2024-12-17
