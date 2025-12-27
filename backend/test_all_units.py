"""
完整的模块单元测试脚本
验证 github_client.py 和 opendigger_client.py 的所有功能
"""

import os
import sys
import json
import tempfile
from dotenv import load_dotenv

# 设置 UTF-8 输出（解决 Windows 控制台编码问题）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

print("=" * 70)
print("DevScope Phase 1 - 完整单元测试")
print("=" * 70)

# ========== 测试 1: GitHub 客户端 ==========
print("\n[测试 1/6] GitHub 客户端初始化")
print("-" * 70)

from github_client import GitHubClient

token = os.getenv("GITHUB_TOKEN")
if token:
    print(f"✅ Token 已加载: {token[:7]}{'*' * 30}")
else:
    print("⚠️  未找到 GITHUB_TOKEN，将使用匿名访问（速率限制较低）")

client = GitHubClient(token=token)
print("✅ GitHubClient 初始化成功")

# ========== 测试 2: get_user ==========
print("\n[测试 2/6] 测试 get_user() 方法")
print("-" * 70)

user = client.get_user("octocat")
assert "login" in user, "用户数据缺少 login 字段"
assert user["login"] == "octocat", "用户名不匹配"
assert "public_repos" in user, "用户数据缺少 public_repos 字段"
print(f"✅ 获取用户信息成功")
print(f"   用户: {user['login']} ({user.get('name', 'N/A')})")
print(f"   公开仓库: {user['public_repos']}")
print(f"   粉丝: {user.get('followers', 0)}")

# ========== 测试 3: get_repos ==========
print("\n[测试 3/6] 测试 get_repos() 方法")
print("-" * 70)

repos = client.get_repos("octocat", per_page=5, max_pages=1)
assert len(repos) > 0, "仓库列表为空"
assert all("name" in r for r in repos), "仓库数据缺少 name 字段"
assert all("stargazers_count" in r for r in repos), "仓库数据缺少 stars 字段"
print(f"✅ 获取仓库列表成功 ({len(repos)} 个仓库)")
for r in repos[:3]:
    print(f"   - {r['name']:30s} | ⭐ {r['stargazers_count']:>5d} | 🍴 {r['forks_count']:>5d}")

# ========== 测试 4: get_commits ==========
print("\n[测试 4/6] 测试 get_commits() 方法")
print("-" * 70)

if repos:
    repo = repos[0]
    owner = repo["owner"]["login"]
    name = repo["name"]
    commits = client.get_commits(owner, name, per_page=10, max_pages=1)
    assert len(commits) > 0, "提交记录为空"
    assert all("commit" in c for c in commits), "提交数据缺少 commit 字段"
    assert all("author" in c["commit"] for c in commits), "提交数据缺少 author 字段"
    print(f"✅ 获取提交历史成功 ({len(commits)} 条提交)")
    for c in commits[:3]:
        msg = c["commit"]["message"].split("\n")[0][:50]
        date = c["commit"]["author"]["date"]
        print(f"   - {date} | {msg}")

# ========== 测试 5: get_user_commit_activity ==========
print("\n[测试 5/6] 测试 get_user_commit_activity() 方法")
print("-" * 70)

# 使用 torvalds 以确保最近一年有活跃数据 (octocat 可能很久没更新)
test_user = "torvalds"
print(f"   正在获取用户 {test_user} 的数据...")
activity_data = client.get_user_commit_activity(test_user, limit_repos=5, per_repo_commits=20)
timestamps = activity_data["commit_times"]

if len(timestamps) == 0:
    print("⚠️  警告: 该用户最近一年无提交记录，无法验证时间戳格式")
else:
    assert all(isinstance(ts, str) for ts in timestamps), "时间戳格式错误"
    print(f"✅ 聚合提交时间序列成功 ({len(timestamps)} 条时间戳)")
    print(f"   示例: {timestamps[:3]}")

assert "window_start" in activity_data
assert "window_end" in activity_data
print(f"   窗口: {activity_data['window_start']} -> {activity_data['window_end']}")

# ========== 测试 6: OpenDigger 客户端 ==========
print("\n[测试 6/6] 测试 OpenDigger 客户端")
print("-" * 70)

from opendigger_client import load_opendigger_json, get_developer_metrics

# 测试远程加载
print("  [6.1] 测试远程 JSON 加载")
url = "https://oss.x-lab.info/open_digger/github/X-lab2017/open-digger/openrank.json"
data = load_opendigger_json(url)
assert data is not None, "远程数据加载失败"
assert len(data) > 0, "远程数据为空"
print(f"  ✅ 远程 JSON 加载成功 ({len(data)} 个数据点)")

# 测试本地加载
print("  [6.2] 测试本地 JSON 加载")
sample_data = {
    "octocat": {"activity": 0.85, "stars": 1000},
    "torvalds": {"activity": 0.95, "stars": 50000}
}

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
    json.dump(sample_data, f)
    temp_path = f.name

try:
    loaded = load_opendigger_json(temp_path)
    assert loaded == sample_data, "本地数据加载不一致"
    print(f"  ✅ 本地 JSON 加载成功")
finally:
    os.remove(temp_path)

# 测试 dict 型数据查询
print("  [6.3] 测试 get_developer_metrics (dict 型)")
metrics = get_developer_metrics("octocat", sample_data)
assert metrics is not None, "查询失败"
assert metrics["activity"] == 0.85, "数据不匹配"
print(f"  ✅ dict 型数据查询成功: {metrics}")

# 测试 list 型数据查询
print("  [6.4] 测试 get_developer_metrics (list 型)")
list_data = [
    {"username": "octocat", "activity": 0.85},
    {"login": "torvalds", "activity": 0.95}
]
metrics_list = get_developer_metrics("torvalds", list_data)
assert metrics_list is not None, "列表查询失败"
assert metrics_list["activity"] == 0.95, "列表数据不匹配"
print(f"  ✅ list 型数据查询成功: {metrics_list}")

# ========== 测试 7: 错误处理 ==========
print("\n[测试 7/8] 错误处理验证")
print("-" * 70)

# 测试用户不存在
print("  [7.1] 测试用户不存在场景")
try:
    client.get_user("this_user_definitely_does_not_exist_xyz_12345")
    assert False, "应抛出异常"
except RuntimeError as e:
    assert "404" in str(e) or "fail" in str(e).lower(), "异常信息不正确"
    print(f"  ✅ 正确捕获用户不存在错误")

# 测试仓库不存在
print("  [7.2] 测试仓库不存在场景")
try:
    client.get_commits("octocat", "nonexistent_repo_xyz_999", per_page=5, max_pages=1)
    assert False, "应抛出异常"
except RuntimeError as e:
    assert "404" in str(e) or "fail" in str(e).lower(), "异常信息不正确"
    print(f"  ✅ 正确捕获仓库不存在错误")

# 测试 OpenDigger 文件不存在
print("  [7.3] 测试 OpenDigger 文件不存在")
try:
    load_opendigger_json("/nonexistent/path/data.json")
    assert False, "应抛出异常"
except RuntimeError as e:
    error_msg = str(e).lower()
    assert "fail" in error_msg or "no such file" in error_msg, f"异常信息不正确: {e}"
    print(f"  ✅ 正确捕获文件读取错误")

# ========== 测试 8: 性能检查 ==========
print("\n[测试 8/8] 性能基准测试")
print("-" * 70)

import time

# 测试单次 API 调用耗时
start = time.time()
user = client.get_user("octocat")
elapsed = time.time() - start
print(f"  get_user() 耗时: {elapsed:.3f}s")
assert elapsed < 5.0, "API 调用超时"

# 测试批量操作耗时
start = time.time()
repos = client.get_repos("octocat", per_page=5, max_pages=1)
elapsed = time.time() - start
print(f"  get_repos(5) 耗时: {elapsed:.3f}s")
assert elapsed < 10.0, "批量操作超时"

print("\n" + "=" * 70)
print("✅ 所有单元测试通过！")
print("=" * 70)
print("\n测试摘要:")
print("  ✅ GitHub 客户端: 所有方法正常工作")
print("  ✅ OpenDigger 客户端: 远程/本地加载正常")
print("  ✅ 错误处理: 异常捕获机制正确")
print("  ✅ 性能: API 调用速度符合预期")
print("\n🎉 Phase 1 数据抓取层验证完成！可进入 Phase 2 开发。")
