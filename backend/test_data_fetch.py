import argparse
import os
from typing import Optional

from dotenv import load_dotenv

from github_client import GitHubClient
from opendigger_client import load_opendigger_json, get_developer_metrics

# 加载 .env 文件中的环境变量
load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="DevScope Phase 1 数据抓取测试")
    parser.add_argument("--username", type=str, default="torvalds", help="GitHub 用户名")
    parser.add_argument(
        "--opendigger", type=str, default=None, help="OpenDigger JSON 的 URL 或本地路径"
    )
    args = parser.parse_args()

    token: Optional[str] = os.environ.get("GITHUB_TOKEN")
    gh = GitHubClient(token=token)

    print("== GitHub 用户信息 ==")
    user = gh.get_user(args.username)
    print({k: user.get(k) for k in ("login", "name", "public_repos", "followers", "following")})

    print("\n== 仓库列表示例 (最多 5 个) ==")
    repos = gh.get_repos(args.username, per_page=5, max_pages=1)
    for r in repos:
        print(f"- {r.get('name')} | stars={r.get('stargazers_count')} | forks={r.get('forks_count')}")

    if repos:
        first = repos[0]
        owner = first.get("owner", {}).get("login", args.username)
        name = first.get("name")
        print(f"\n== 仓库 '{owner}/{name}' 的提交样例 (最多 10 条) ==")
        commits = gh.get_commits(owner, name, per_page=10, max_pages=1)
        for c in commits:
            sha = c.get("sha")
            msg = c.get("commit", {}).get("message", "").split("\n")[0]
            date = c.get("commit", {}).get("author", {}).get("date")
            print(f"- {date} {sha} {msg}")

    print("\n== 用户级提交时间序列 (聚合，最多 5 仓库) ==")
    activity_data = gh.get_user_commit_activity(args.username, limit_repos=5, per_repo_commits=50)
    timestamps = activity_data["commit_times"]
    print(f"总计 {len(timestamps)} 条时间戳样本，示例前 10 条：")
    print(f"观测窗口: {activity_data['window_start']} 至 {activity_data['window_end']}")
    for ts in timestamps[:10]:
        print(f"- {ts}")

    if args.opendigger:
        print("\n== OpenDigger 指标样例 ==")
        data = load_opendigger_json(args.opendigger)
        metrics = get_developer_metrics(args.username, data)
        if metrics:
            keys = list(metrics.keys())[:10]
            preview = {k: metrics.get(k) for k in keys}
            print(f"找到开发者 {args.username} 指标，前 10 个字段预览：")
            print(preview)
        else:
            print(f"未在数据中找到开发者 {args.username} 的记录。")


if __name__ == "__main__":
    main()
