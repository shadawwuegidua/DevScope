DevScope 项目实现规范文档
文件名: project_context.md
用途: GitHub Copilot / Cursor 核心参考文档
项目名称: DevScope (基于开源生态数据的开发者画像与行为倾向分析平台)
比赛: OpenRank (作品类 W 赛道)
1. 项目概述 (Overview)DevScope 是一个基于 GitHub 开源生态数据的开发者分析与可视化平台。核心目标：不仅仅展示开发者的历史数据，而是通过统计建模（Statistical Modeling）与概率分布（Probabilistic Distribution），对开发者的技术倾向和未来活跃行为进行可解释的预测。核心逻辑流
    输入: GitHub 用户名。
    获取: 实时调用 GitHub API + 读取 OpenDigger 静态数据。
    计算: 进行数据清洗、画像构建、概率分布拟合（Python/SciPy）。
    缓存: 结果存入数据库，实现“准实时”响应。
    输出: 前端通过 BI 仪表盘（Dashboard）展示画像及预测概率。
2. 技术栈 (Tech Stack)
    Backend: Python 3.9+, FastAPI (用于构建 REST API)。
    Data Processing: Pandas, NumPy, SciPy (用于统计分布拟合)。
    Frontend: Vue 3, Vite, ECharts (用于核心可视化)。
    Data Source:
        GitHub REST API (实时获取 User Profile, Repos, Commits)。
        penDigger (获取长期活跃度指标)。
    Storage/Cache: SQLite (轻量级) 或 Redis。
3. 核心数学模型与统计原理 (Mathematical Logic)注意： 本项目严禁使用黑箱机器学习/深度学习模型。所有预测必须基于以下统计学原理，强调可解释性。
    3.1 开发者画像向量 (Developer Persona)将开发者 $U$ 建模为多维向量：$$U = (A, P, L, T)$$$A$ (Activity): 活跃度指标集合（Commit/PR/Issue计数）。$P$ (Projects): 参与项目集合。$L$ (Languages): 语言偏好分布。$T$ (Time): 时间序列特征。
    3.2 技术/主题倾向性预测 (Tendency Prediction)目标：预测开发者未来参与某一技术主题 $T_i$ 的概率。模型：基于多项分布（Multinomial Distribution）的贝叶斯平滑估计。定义技术主题集合 $\mathcal{T} = \{T_1, T_2, \dots, T_K\}$。统计历史中属于 $T_i$ 的项目数量 $n_i$。核心公式（应用拉普拉斯平滑 Laplace Smoothing，防止零概率）：$$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$$$N$: 参与的总项目数。$K$: 技术类别的总数。$\alpha$: 平滑参数，通常取 $1$。实现要求：代码需计算出各技术领域的概率值，并返回解释文本（如：“基于历史数据，该开发者参与 AI 项目的概率为 42%”）。
    3.3 活跃时间窗口预测 (Activity Time Prediction)目标：预测开发者“下一次开启/参与新项目”的时间间隔。模型：基于时间间隔序列的连续概率分布拟合。
        构建时间序列 $t_1, t_2, \dots, t_n$，计算相邻间隔 $\Delta t_i = t_{i+1} - t_i$。拟合分布 (使用 scipy.stats)：方案 A (Weibull 分布 - 推荐)：描述活跃率随时间变化的情况。$$f(t) = \frac{k}{\lambda} \left(\frac{t}{\lambda}\right)^{k-1} e^{-(t/\lambda)^k}$$方案 B (指数分布 - 备选)：假设活跃是无记忆的随机过程。$$f(t) = \lambda e^{-\lambda t}$$输出：计算未来特定时间窗口（如 30 天）内的累积概率 $P(T \le 30)$。
4. 后端接口规范 (Backend Specification)使用 FastAPI 实现，遵循 RESTful 风格。
    4.1 数据结构 (Data Structures)在代码中定义 Pydantic Model:
        class PredictionResult(BaseModel):
            category: str  # 技术领域，如 "Machine Learning"
            probability: float  # 0.0 - 1.0
            explanation: str  # 自动生成的解释文本

        class TimePrediction(BaseModel):
            expected_interval_days: float
            next_active_prob_30d: float # 未来30天活跃概率
            distribution_type: str # "Weibull" or "Exponential"

        class DeveloperAnalysis(BaseModel):
            username: str
            persona: dict  # 基础画像数据
            tech_tendency: List[PredictionResult] # 3.2 的结果
            time_prediction: TimePrediction # 3.3 的结果
    4.2 核心 APIGET /api/analyze/{username}逻辑：检查 Cache 是否有该用户 24 小时内的数据。Miss: 触发 GitHub API 爬虫 -> 数据清洗 -> 统计建模 -> 存入 Cache -> 返回。Hit: 直接返回 JSON。边界条件：若用户项目数 $< 5$，不进行预测，返回 prediction_available: false。
5. 前端仪表盘规范 (Frontend Dashboard)使用 Vue 3 + ECharts 实现 BI 风格界面。
    搜索页：大号搜索框，输入 GitHub ID。
    加载页：展示“正在抓取数据...”、“正在拟合概率模型...”的进度条（增强用户体验）。
    结果页 (Dashboard)：
        左侧: 个人信息卡片 + 雷达图 (六维能力图)。
        中部:
            倾向性预测柱状图：展示 $P(T_i)$，高亮概率最高的领域。
            活跃时间分布曲线：绘制拟合后的 PDF (概率密度函数) 曲线。
            技术关系引力图 (Tech Relation Graph)：
                核心逻辑：使用 ECharts 的 graph 类型（力导向布局）。
                节点 (Nodes)：中心节点为开发者，四周为技术标签（如 Python, React, PyTorch）。
                连线 (Edges)：连线长度反比于概率 $P(T_i)$。概率越高，节点距离中心越近，引力越强。
                交互：点击技术节点，展示该开发者在该领域最具代表性的 Repository。
        底部: 历史项目时间轴。
6. 开发步骤 (Implementation Steps)请 Copilot 按照以下顺序辅助编码：
    Phase 1: Data Fetching实现 github_client.py，封装 API 调用，处理 Rate Limit。实现 opendigger_client.py，获取 JSON 数据。
        github_client.py:实现一个 GitHubClient 类，使用 GitHub REST API 获取用户数据，包括用户资料、仓库列表和提交历史。处理 Rate Limit（检查 X-RateLimit-Remaining header，如果低则 sleep）。使用环境变量存储 Token。
        Opendigger_client.py:基于 OpenDigger 的静态 JSON 数据源，实现一个客户端函数，从指定 URL 或本地文件读取开发者活跃度指标。处理数据解析和错误。
        测试:写一个小脚本调用这些客户端，输出样例数据
    Phase 2: Mathematical Modeling (Core)实现 modeling.py。编写函数 calculate_topic_probability(history_list) 实现拉普拉斯平滑。编写函数 fit_time_distribution(intervals) 使用 scipy.stats.weibull_min.fit。
    Phase 3: Backend API整合 FastAPI，设置 Pydantic 模型，联调数据层。
    Phase 4: Frontend Visualization搭建 Vue 框架，集成 ECharts，对接 API。
7. 提示词/代码风格要求 (Prompting Rules)
    代码注释：所有涉及数学公式的函数，必须在 Docstring 中写明对应的数学公式（LaTeX 格式）。
    错误处理：对于网络请求失败、数据不足（<5 个项目）的情况，必须有显式的 try-except 和用户提示。
    不确定的预测：在 UI 文案中，必须使用“倾向于”、“概率为”等词汇，严禁使用“一定会”等确定性词汇。
    禁止行为：
    - 引入 sklearn 的分类 / 回归模型
    - 引入神经网络、embedding、transformer
    - 任何形式的“训练集/测试集”划分