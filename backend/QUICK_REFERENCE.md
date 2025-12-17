# DevScope Phase 1 快速参考卡

## 🚀 快速开始

### 1️⃣ 环境设置（仅首次）
```powershell
# 激活虚拟环境
cd "c:\Users\Zhuang\Documents\My Stuff\DevScope"
.\DevScope\Scripts\Activate.ps1

# 安装依赖
pip install -r backend\requirements.txt
```

### 2️⃣ 配置 Token
确保 `backend\.env` 文件存在且内容正确：
```
GITHUB_TOKEN=your_github_token_here
```

### 3️⃣ 运行测试（验证环境）
```powershell
cd backend

# UTF-8 编码设置（避免乱码）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 完整单元测试
python test_all_units.py
```

---

## 📚 快速命令参考

### GitHub 数据抓取
```powershell
# 抓取指定用户数据
python test_data_fetch.py --username octocat

# 抓取并包含 OpenDigger 数据
python test_data_fetch.py --username torvalds --opendigger "https://example.com/data.json"
```

### OpenDigger 专项测试
```powershell
# 测试仓库 OpenRank
python test_opendigger.py --mode repo --owner microsoft --repo vscode

# 测试多维度指标
python test_opendigger.py --mode multi --owner vuejs --repo vue

# 分析开发者影响力
python test_opendigger.py --mode developer --username torvalds
```

### 完整验证
```powershell
# 运行所有单元测试
python test_all_units.py

# 输出示例：
# ✅ 所有单元测试通过！
# 🎉 Phase 1 数据抓取层验证完成！
```

---

## 🔧 代码使用示例

### GitHub 客户端
```python
from dotenv import load_dotenv
from github_client import GitHubClient

load_dotenv()  # 加载 .env 文件

client = GitHubClient()  # 自动使用环境变量中的 Token

# 获取用户信息
user = client.get_user("octocat")
print(user["login"], user["public_repos"])

# 获取仓库列表
repos = client.get_repos("octocat", per_page=10, max_pages=1)
for r in repos:
    print(f"{r['name']} - {r['stargazers_count']} stars")

# 获取提交历史
commits = client.get_commits("octocat", "Hello-World", per_page=20)
for c in commits:
    print(c["commit"]["author"]["date"])
```

### OpenDigger 客户端
```python
from opendigger_client import load_opendigger_json

# 远程加载
url = "https://oss.x-lab.info/open_digger/github/microsoft/vscode/openrank.json"
data = load_opendigger_json(url)

# 显示最新 OpenRank
sorted_data = sorted(data.items())
print(f"最新 OpenRank: {sorted_data[-1]}")

# 本地加载
data = load_opendigger_json("./local_data.json")
```

---

## ⚡ 常见问题速查

| 问题 | 解决方案 |
|------|---------|
| `UnicodeEncodeError` 乱码 | 运行前执行 UTF-8 编码设置命令 |
| `404 Not Found` | 检查用户名/仓库名拼写；部分数据未被 OpenDigger 收录 |
| `403 Forbidden` | Token 无效或过期，检查 `.env` 文件 |
| `Rate Limit` | 客户端会自动休眠，耐心等待或减少请求量 |
| 无 OpenDigger 数据 | 仅活跃项目被收录，尝试知名仓库（如 vscode、vue） |

---

## 📖 文档速查

| 文档 | 用途 | 适合人群 |
|------|------|---------|
| [README.md](README.md) | 完整使用指南 | 所有开发者 |
| [VERIFICATION.md](VERIFICATION.md) | 验证步骤 | 新加入成员 |
| [OPENDIGGER_GUIDE.md](OPENDIGGER_GUIDE.md) | OpenDigger 专项 | 需要理解 OpenRank 的开发者 |
| [PHASE1_REPORT.md](PHASE1_REPORT.md) | 验证报告 | 项目管理者 |
| 本文档 | 快速参考 | 日常开发使用 |

---

## 🎯 核心 API 速记

### GitHubClient
```python
client.get_user(username)                          # 用户信息
client.get_repos(username, per_page, max_pages)    # 仓库列表
client.get_commits(owner, repo, per_page)          # 提交历史
client.get_user_commit_activity(username, limit)   # 聚合时间序列
```

### OpenDigger
```python
load_opendigger_json(url_or_path)                  # 加载 JSON
get_developer_metrics(username, data)              # 查询开发者
```

### OpenDigger URL 模板
```
https://oss.x-lab.info/open_digger/github/{owner}/{repo}/{metric}.json

指标类型 (metric):
- openrank.json          # OpenRank 评分
- activity.json          # 活跃度
- attention.json         # 关注度
- new_contributors.json  # 新增贡献者
```

---

## 🏆 验证通过标准

运行 `python test_all_units.py`，看到以下输出即为成功：

```
✅ 所有单元测试通过！

测试摘要:
  ✅ GitHub 客户端: 所有方法正常工作
  ✅ OpenDigger 客户端: 远程/本地加载正常
  ✅ 错误处理: 异常捕获机制正确
  ✅ 性能: API 调用速度符合预期

🎉 Phase 1 数据抓取层验证完成！可进入 Phase 2 开发。
```

---

**最后更新**: 2024-12-17  
**维护**: DevScope 团队  
**适用**: Phase 1 数据抓取层
