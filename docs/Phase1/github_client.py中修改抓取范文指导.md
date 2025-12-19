你是本项目的工程协作者，请严格按照以下要求修改代码与文档。
本次修改只解决一个问题：统一将开发者行为建模的数据采样策略
从“按数量限制”改为“按最近一年的时间窗口限制”。

====================================
一、修改目标（唯一目标）
====================================

当前问题：
- github_client.py 中通过 limit_repos / per_repo_commits
  对数据进行数量级截断
- modeling 阶段默认将其视为完整历史行为
- 这在统计上会导致时间分布参数的系统性偏差

本次目标：
- 明确并统一采用“最近一年（rolling 12 months）”作为观测窗口
- 所有建模、seed 数据、文档说明均基于该时间窗口
- 不追求全量历史，只保证时间窗口内数据的统计自洽性

====================================
二、github_client.py 的修改要求
====================================

1. 移除或弱化以下“数量型限制”作为核心逻辑：
   - limit_repos
   - per_repo_commits

   它们可以作为兜底上限存在，但不再是主要采样方式。

2. 在获取 commit 数据时：
   - 使用 GitHub API 的 `since` 参数
   - since = 当前时间往前推 1 年

   示例逻辑（伪代码）：
since_date = now() - timedelta(days=365)
get_repo_commits(..., since=since_date)

css
复制代码

3. 对外暴露的数据结构中，必须显式包含：
- observation_window_start
- observation_window_end

例如：
```python
{
  "commit_times": [...],
  "window_start": since_date,
  "window_end": now()
}
不需要保证抓取“所有 repo 的所有 commit”，
只需保证：时间窗口定义清晰且一致。

====================================
三、opendigger_client.py（不改逻辑，只改语义定位）
不修改其数据抓取逻辑

但在注释和文档中明确说明：
OpenDigger 数据作为“年度尺度的宏观指标”，
与 GitHub API 的一年时间窗口在时间尺度上是兼容的

====================================
四、seed_data / seed_developers.json 的修改要求
不需要重新设计 seed 机制

需要确保：

seed 数据是基于“最近一年时间窗口”生成的

而不是隐含为“完整历史”

在 seed 相关代码或注释中明确说明：

seed 数据用于 demo / fallback

遵循与实时查询相同的时间窗口假设

不作为 ground truth 或训练数据

====================================
五、文档（MD 文件）的强制修改点
请在 Prompt_context.md / QUICK_REFERENCE.md / README（如存在）中，
至少新增或修改以下表述（可等价转述，但含义必须一致）：

数据观测假设：
sql
This system models developer behavior
within a rolling one-year observation window,
rather than the entire GitHub career.

建模边界说明：
sql
All probabilistic estimates are conditional
on observed activity within the last 12 months.

seed 数据说明：
sql
Seed data follows the same one-year observation window
and is used only for demonstration and cold-start fallback.
====================================
六、禁止事项（非常重要）
不要尝试抓取完整 GitHub 历史

不要引入新的机器学习模型

不要扩大本次修改范围

不要修改 modeling 的数学形式，只修正其“数据前提”

====================================
七、完成标准
修改完成后，应满足：

所有时间相关建模都能明确回答：
“这是基于最近一年数据得出的”

不再存在“数量截断但假装是完整历史”的情况

文档、seed、代码三者对时间窗口的假设完全一致
