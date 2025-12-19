# OpenDigger 使用指南

## 什么是 OpenDigger？

**OpenDigger** 是 X-Lab 开源实验室提供的开源生态数据分析平台，通过静态 JSON API 提供 GitHub 生态的长期指标数据。

核心特点：
- ✅ **免费且无需认证** - 无需 Token 即可访问
- ✅ **历史数据丰富** - 提供多年的趋势数据
- ✅ **OpenRank 指标** - 独特的开源影响力评估算法
- ✅ **多维度分析** - 活跃度、协作网络、技术影响力等

---

## OpenDigger 数据结构

### API 地址格式

```
https://oss.x-lab.info/open_digger/github/{owner}/{repo}/{metric}.json
https://oss.x-lab.info/open_digger/github/{owner}/openrank.json (用户级)
```

### 核心指标类型

| 指标名称 | 文件名 | 说明 | 示例数据 |
|---------|--------|------|---------|
| **OpenRank** | `openrank.json` | 开源影响力综合评分 | `{"2020": 33.99, "2021": 49.36}` |
| **Activity** | `activity.json` | 月度活跃度（Issue/PR/Commit 加权） | `{"2020-01": 125.5, "2020-02": 98.3}` |
| **Attention** | `attention.json` | 关注度（Star/Fork/Watch） | `{"2020-01": 450, "2020-02": 520}` |
| **Contributors** | `new_contributors.json` | 新增贡献者数 | `{"2020-01": 12, "2020-02": 8}` |
| **Technical Fork** | `technical_fork.json` | 技术分叉（非单纯复制） | `{"linux": 0.85, "busybox": 0.72}` |

---

## OpenRank 指标详解

**OpenRank** 是基于网络影响力传播模型的开源价值评估算法：

### 数学原理（简化版）

$$
\text{OpenRank}(v) = \alpha \sum_{u \in \text{in}(v)} \frac{\text{OpenRank}(u)}{\text{out}(u)} + (1-\alpha) \cdot \text{base}
$$

- **网络传播模型**：类似 Google PageRank，但针对开源协作网络
- **节点定义**：开发者、仓库、Issue、PR 均为节点
- **边权重**：Commit、Review、Issue 互动等行为的加权
- **阻尼因子** $\alpha$：防止循环累积，典型取值 0.85

### 实际意义

- **高 OpenRank（> 50）**：核心开源贡献者，影响力大
- **中等（10-50）**：活跃参与者
- **低（< 10）**：新手或边缘参与者

---

## 使用 OpenDigger 获取数据

### 方式 1：仓库级 OpenRank

```python
from opendigger_client import load_opendigger_json

# 获取 open-digger 仓库的 OpenRank 历史
url = "https://oss.x-lab.info/open_digger/github/X-lab2017/open-digger/openrank.json"
data = load_opendigger_json(url)

print("年度 OpenRank 值:")
for year, score in sorted(data.items()):
    print(f"  {year}: {score:.2f}")

# 输出示例:
#   2020: 33.99
#   2021: 49.36
#   2022: 89.06
#   2023: 120.45
```

### 方式 2：用户级 OpenRank

```python
# 获取 Linus Torvalds 的 OpenRank（需要用户在 OpenDigger 数据库中）
url = "https://oss.x-lab.info/open_digger/github/torvalds/openrank.json"
data = load_opendigger_json(url)

# 计算平均值
avg_rank = sum(data.values()) / len(data)
print(f"平均 OpenRank: {avg_rank:.2f}")
```

### 方式 3：批量指标聚合

```python
import requests

def get_repo_metrics(owner: str, repo: str):
    """获取仓库的多维度指标"""
    base_url = f"https://oss.x-lab.info/open_digger/github/{owner}/{repo}"
    
    metrics = {}
    for metric in ["openrank", "activity", "attention"]:
        try:
            resp = requests.get(f"{base_url}/{metric}.json", timeout=10)
            if resp.status_code == 200:
                metrics[metric] = resp.json()
        except Exception as e:
            print(f"获取 {metric} 失败: {e}")
    
    return metrics

# 使用示例
data = get_repo_metrics("microsoft", "vscode")
print(f"VS Code 最新 OpenRank: {list(data['openrank'].values())[-1]}")
```

---

## 常见问题

### Q1: 所有用户/仓库都有 OpenRank 数据吗？

**A**: 不是。OpenDigger 只覆盖活跃度较高的仓库和贡献者。小型或新创建的仓库可能没有数据。

**检测方法**：
```python
try:
    data = load_opendigger_json(url)
    print("数据存在")
except RuntimeError as e:
    if "404" in str(e):
        print("该用户/仓库未被 OpenDigger 收录")
```

### Q2: OpenRank 更新频率？

**A**: 通常**每月更新**。数据存在 1-2 个月的延迟。

### Q3: 如何解释 OpenRank 趋势？

| 趋势 | 含义 |
|------|------|
| 持续上升 | 影响力稳定增长，社区活跃 |
| 稳定高位 | 成熟项目，持续贡献 |
| 突然上升 | 项目爆发期（病毒式传播、重大更新） |
| 下降 | 活跃度降低，可能进入维护期 |

### Q4: OpenRank vs GitHub Stars？

| 维度 | OpenRank | Stars |
|------|----------|-------|
| 衡量对象 | 实际贡献与协作网络 | 关注度 |
| 防刷能力 | 强（基于网络拓扑） | 弱（可购买假 Star） |
| 时间维度 | 历史趋势 | 累积值 |
| 适用场景 | 评估开发者影响力 | 评估项目热度 |

---

## 整合到 DevScope

### Phase 1 应用场景

在当前阶段，OpenDigger 用于：

1. **补充 GitHub API 数据**
   - GitHub API：实时仓库/用户数据
   - OpenDigger：长期历史趋势

2. **验证用户影响力**
   ```python
   # 伪代码逻辑
   user_repos = github_client.get_repos(username)
   
   for repo in user_repos:
       openrank_data = load_opendigger_json(f".../{repo['name']}/openrank.json")
       if openrank_data:
           # 加权用户总 OpenRank
           user_influence += calculate_contribution_weight(repo, openrank_data)
   ```

3. **时间序列预测的输入特征**（Phase 2）
   - 使用 OpenRank 历史趋势拟合 Weibull 分布
   - 结合 GitHub 提交时间戳预测活跃窗口

---

## 实战案例

### 案例 1：对比两个开发者的影响力

```python
def compare_developers(user1: str, user2: str):
    users = [user1, user2]
    results = {}
    
    for user in users:
        # 获取用户仓库
        repos = github_client.get_repos(user, per_page=10, max_pages=1)
        total_rank = 0
        
        for repo in repos:
            url = f"https://oss.x-lab.info/open_digger/github/{user}/{repo['name']}/openrank.json"
            try:
                data = load_opendigger_json(url)
                # 取最新年份的 OpenRank
                total_rank += max(data.values())
            except:
                continue
        
        results[user] = total_rank
    
    print(f"{user1}: {results[user1]:.2f}")
    print(f"{user2}: {results[user2]:.2f}")
    print(f"影响力比: {results[user1]/results[user2]:.2f}")

# 使用
compare_developers("torvalds", "octocat")
```

### 案例 2：识别技术领域

```python
def detect_tech_domain(username: str):
    """基于仓库 OpenRank 识别主导技术领域"""
    repos = github_client.get_repos(username, per_page=20, max_pages=1)
    
    # 语言加权累计
    lang_scores = {}
    
    for repo in repos:
        lang = repo.get("language")
        if not lang:
            continue
        
        # 尝试获取 OpenRank
        url = f"https://oss.x-lab.info/open_digger/github/{username}/{repo['name']}/openrank.json"
        try:
            data = load_opendigger_json(url)
            weight = max(data.values())  # 使用峰值 OpenRank 作为权重
        except:
            weight = 1  # 默认权重
        
        lang_scores[lang] = lang_scores.get(lang, 0) + weight
    
    # 排序
    sorted_langs = sorted(lang_scores.items(), key=lambda x: x[1], reverse=True)
    print(f"{username} 的技术倾向 (基于 OpenRank 加权):")
    for lang, score in sorted_langs[:5]:
        print(f"  {lang}: {score:.2f}")

detect_tech_domain("torvalds")
```

---

## 参考资源

- 官方网站: https://open-digger.cn/
- GitHub 仓库: https://github.com/X-lab2017/open-digger
- 数据 API 根地址: https://oss.x-lab.info/open_digger/github/
- 论文: "OpenRank: Towards a Transparent and Interpretable Influence Measurement for Open Source Communities"

---

**更新日期**: 2024-12-17  
**适用版本**: DevScope Phase 1
