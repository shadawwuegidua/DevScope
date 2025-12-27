"""
OpenDigger 功能验证脚本
测试 OpenRank 及其他指标的获取
"""

import argparse
import os
from typing import Dict, Any, List

from dotenv import load_dotenv
from opendigger_client import load_opendigger_json

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def test_repo_openrank(owner: str, repo: str) -> None:
    """测试仓库级 OpenRank 获取"""
    print(f"\n{'='*60}")
    print(f"测试仓库: {owner}/{repo}")
    print('='*60)
    
    url = f"https://oss.x-lab.info/open_digger/github/{owner}/{repo}/openrank.json"
    
    try:
        data = load_opendigger_json(url)
        
        if not data:
            print("❌ 数据为空")
            return
        
        # 按年份/月份排序
        sorted_data = sorted(data.items(), key=lambda x: x[0])
        
        print(f"\n✅ OpenRank 历史数据 (共 {len(sorted_data)} 个时间点):")
        print("-" * 60)
        
        # 显示前 5 个和最后 5 个
        display_count = min(5, len(sorted_data))
        for period, score in sorted_data[:display_count]:
            print(f"  {period:15s} | OpenRank: {score:>8.2f}")
        
        if len(sorted_data) > 10:
            print("  " + "." * 55)
        
        if len(sorted_data) > display_count:
            for period, score in sorted_data[-display_count:]:
                print(f"  {period:15s} | OpenRank: {score:>8.2f}")
        
        # 统计分析
        scores = [v for v in data.values() if isinstance(v, (int, float))]
        if scores:
            print("\n📊 统计摘要:")
            print(f"  最高值: {max(scores):.2f}")
            print(f"  最低值: {min(scores):.2f}")
            print(f"  平均值: {sum(scores)/len(scores):.2f}")
            print(f"  最新值: {sorted_data[-1][1]:.2f}")
            
            # 趋势分析
            if len(sorted_data) >= 2:
                trend = sorted_data[-1][1] - sorted_data[-2][1]
                trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                print(f"  近期趋势: {trend_emoji} {trend:+.2f}")
        
    except RuntimeError as e:
        if "404" in str(e):
            print(f"❌ 该仓库未被 OpenDigger 收录")
            print(f"   提示: OpenDigger 只覆盖活跃度较高的项目")
        else:
            print(f"❌ 获取失败: {e}")


def test_multiple_metrics(owner: str, repo: str, metrics: List[str]) -> None:
    """测试多个指标的获取"""
    print(f"\n{'='*60}")
    print(f"多维度指标测试: {owner}/{repo}")
    print('='*60)
    
    base_url = f"https://oss.x-lab.info/open_digger/github/{owner}/{repo}"
    
    results = {}
    for metric in metrics:
        url = f"{base_url}/{metric}.json"
        try:
            data = load_opendigger_json(url)
            if data:
                # 获取最新值
                sorted_items = sorted(data.items(), key=lambda x: x[0])
                latest_period, latest_value = sorted_items[-1]
                results[metric] = {
                    "latest_period": latest_period,
                    "latest_value": latest_value,
                    "data_points": len(data)
                }
                print(f"✅ {metric:20s} | 最新: {latest_value:>10.2f} ({latest_period}) | 共 {len(data)} 个数据点")
            else:
                print(f"⚠️  {metric:20s} | 数据为空")
        except RuntimeError as e:
            if "404" in str(e):
                print(f"❌ {metric:20s} | 未收录")
            else:
                print(f"❌ {metric:20s} | 错误: {e}")


def analyze_developer_influence(username: str) -> None:
    """分析开发者影响力（基于其仓库的 OpenRank）"""
    print(f"\n{'='*60}")
    print(f"开发者影响力分析: {username}")
    print('='*60)
    
    # 测试一些知名开发者的仓库
    test_repos = {
        "torvalds": ["linux", "subsurface-for-dirk", "test-tlb"],
        "octocat": ["Hello-World", "Spoon-Knife", "linguist"],
        "yyx990803": ["vue", "vite", "vue-next"],
        "tj": ["commander.js", "co", "express"],
    }
    
    repos_to_test = test_repos.get(username, [])
    
    if not repos_to_test:
        print(f"⚠️  未为 '{username}' 配置测试仓库")
        print(f"   提示: 手动指定仓库或添加到预设列表")
        return
    
    total_rank = 0
    success_count = 0
    
    print(f"\n正在分析 {len(repos_to_test)} 个仓库...")
    
    for repo in repos_to_test:
        url = f"https://oss.x-lab.info/open_digger/github/{username}/{repo}/openrank.json"
        try:
            data = load_opendigger_json(url)
            if data:
                sorted_items = sorted(data.items(), key=lambda x: x[0])
                latest_value = sorted_items[-1][1]
                total_rank += latest_value
                success_count += 1
                print(f"  ✅ {repo:30s} | OpenRank: {latest_value:>8.2f}")
            else:
                print(f"  ⚠️  {repo:30s} | 数据为空")
        except RuntimeError:
            print(f"  ❌ {repo:30s} | 未收录")
    
    if success_count > 0:
        avg_rank = total_rank / success_count
        print(f"\n📊 影响力摘要:")
        print(f"  成功分析仓库数: {success_count}/{len(repos_to_test)}")
        print(f"  总 OpenRank: {total_rank:.2f}")
        print(f"  平均 OpenRank: {avg_rank:.2f}")
        
        # 影响力等级评估
        if avg_rank > 100:
            level = "🌟 顶级开源贡献者"
        elif avg_rank > 50:
            level = "⭐ 核心开源贡献者"
        elif avg_rank > 20:
            level = "✨ 活跃开源贡献者"
        elif avg_rank > 5:
            level = "💫 新兴开源贡献者"
        else:
            level = "🔰 初级贡献者"
        
        print(f"  影响力等级: {level}")
    else:
        print("\n❌ 未能获取任何有效数据")


def main():
    parser = argparse.ArgumentParser(description="OpenDigger 数据验证工具")
    parser.add_argument(
        "--mode",
        choices=["repo", "multi", "developer"],
        default="repo",
        help="测试模式: repo=单仓库OpenRank, multi=多指标, developer=开发者影响力"
    )
    parser.add_argument("--owner", type=str, default="X-lab2017", help="仓库所有者")
    parser.add_argument("--repo", type=str, default="open-digger", help="仓库名称")
    parser.add_argument("--username", type=str, default="torvalds", help="开发者用户名 (developer 模式)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OpenDigger 数据验证工具")
    print("=" * 60)
    
    if args.mode == "repo":
        test_repo_openrank(args.owner, args.repo)
    
    elif args.mode == "multi":
        metrics = ["openrank", "activity", "attention", "new_contributors"]
        test_multiple_metrics(args.owner, args.repo, metrics)
    
    elif args.mode == "developer":
        analyze_developer_influence(args.username)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
