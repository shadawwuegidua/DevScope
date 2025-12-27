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
        OpenDigger (获取长期活跃度指标)。
    Storage/Cache: SQLite (轻量级) 或 Redis。
3. 核心数学模型与统计原理 (Mathematical Logic)注意： 本项目严禁使用黑箱机器学习/深度学习模型。所有预测必须基于以下统计学原理，强调可解释性。
    3.1 开发者画像向量 (Developer Persona)将开发者 $U$ 建模为多维向量：$$U = (A, P, L, T)$$$A$ (Activity): 活跃度指标集合（Commit/PR/Issue计数）。$P$ (Projects): 参与项目集合。$L$ (Languages): 语言偏好分布。$T$ (Time): 时间序列特征。
    3.2 技术/主题倾向性预测 (Tendency Prediction)目标：预测开发者未来参与某一技术主题 $T_i$ 的概率。模型：基于多项分布（Multinomial Distribution）的贝叶斯平滑估计。定义技术主题集合 $\mathcal{T} = \{T_1, T_2, \dots, T_K\}$。统计历史中属于 $T_i$ 的项目数量 $n_i$。核心公式（应用拉普拉斯平滑 Laplace Smoothing，防止零概率）：$$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$$$N$: 参与的总项目数。$K$: 技术类别的总数。$\alpha$: 平滑参数，通常取 $1$。实现要求：代码需计算出各技术领域的概率值，并返回解释文本（如：“基于历史数据，该开发者参与 AI 项目的概率为 42%”）。
    3.3 活跃时间窗口预测 (Activity Time Prediction)目标：预测开发者“下一次开启/参与新项目”的时间间隔。模型：基于时间间隔序列的连续概率分布拟合。
        构建时间序列 $t_1, t_2, \dots, t_n$，计算相邻间隔 $\Delta t_i = t_{i+1} - t_i$。拟合分布 (使用 scipy.stats)：方案 A (Weibull 分布 - 推荐)：描述活跃率随时间变化的情况。$$f(t) = \frac{k}{\lambda} \left(\frac{t}{\lambda}\right)^{k-1} e^{-(t/\lambda)^k}$$方案 B (指数分布 - 备选)：假设活跃是无记忆的随机过程。$$f(t) = \lambda e^{-\lambda t}$$输出：计算未来特定时间窗口（如 30 天）内的累积概率 $P(T \le 30)$。
    #### 3.4 相似性对齐与冷启动处理 (Cold Start Handling)
    - **逻辑**：当用户项目数 $N < 5$ 时，通过相似度加权融合社区均值。
    - **权重计算**：定义置信度权重 $w = \min(1.0, N / 10)$。
    - **融合公式**：$P_{final} = w \cdot P_{user} + (1-w) \cdot P_{community}$。
    - **社区均值**：预置一套代表性开发者（如“典型后端”、“典型前端”）的概率分布作为 $P_{community}$。

    #### 3.5 匹配度打分模型 (Match Score)
    - **目标**：计算开发者与特定技术栈/仓库的契合度。
    - **核心公式**：$Score = (P_{tendency} \times 0.7) + (P_{active} \times 0.3)$。
    - **维度说明**：$P_{tendency}$ 是技术倾向概率，$P_{active}$ 是未来30天活跃概率。
    - **解释生成**：根据 Score 分值自动匹配评价语（如 >0.8 为“极高匹配”，<0.3 为“低契合度”）。
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
            is_cold_start: bool  # 标记是否启用了冷启动补救逻辑
            confidence_weight: float  # 即上述公式中的 w
            persona: dict
            tech_tendency: List[PredictionResult]
            time_prediction: TimePrediction
            match_scores: Optional[Dict[str, float]] # 技术栈匹配得分，Key为技术名
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
                连线 (Edges)：连线长度由 $1 - P(T_i)$ 决定（概率越大，距离越近）。
                交互：点击技术节点，展示该开发者在该领域最具代表性的 Repository。
        底部: 历史项目时间轴。
6. 开发步骤 (Implementation Steps)请 Copilot 按照以下顺序辅助编码：
    Phase 1: Data Fetching实现 github_client.py，封装 API 调用，处理 Rate Limit。实现 opendigger_client.py，获取 JSON 数据。
        github_client.py:实现一个 GitHubClient 类，使用 GitHub REST API 获取用户数据，包括用户资料、仓库列表和提交历史。处理 Rate Limit（检查 X-RateLimit-Remaining header，如果低则 sleep）。使用环境变量存储 Token。
        Opendigger_client.py:基于 OpenDigger 的静态 JSON 数据源，实现一个客户端函数，从指定 URL 或本地文件读取开发者活跃度指标。处理数据解析和错误。
        测试:写一个小脚本调用这些客户端，输出样例数据
        数据预置 (Seeding)：在本地数据库预存 OpenRank/GitHub 前 100 名高活跃开发者的分析结果，作为演示时的“名人堂”（Hall of Fame），确保在 API 受限或答辩演示时有完美的展示案例。
    Phase 2: Mathematical Modeling (Core)
        实现 `modeling.py`，必须包含 `calculate_weighted_probability` 函数（处理冷启动）。
        实现 `calculate_match_score` 函数，支持输入特定技术栈进行打分。
        所有 Scipy 拟合逻辑必须包含异常回退（Fallback）：若 Weibull 拟合失败，自动降级为指数分布或社区均值。
        编写函数 calculate_topic_probability(history_list) 实现拉普拉斯平滑。编写函数 fit_time_distribution(intervals) 使用 scipy.stats.weibull_min.fit。
        **目标**：基于 Phase 1 获取的基础数据，实现开发者行为预测和技术画像的数学模型。

        **1. 技术倾向性预测 (`calculate_topic_probability`)**
        - **输入**: `List[str]` (用户参与的项目话题/语言列表)。
        - **逻辑**: 
            - 统计各维度频次。
            - 实现 **拉普拉斯平滑 (Laplace Smoothing)**：$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$。
            - 预留一个 `community_averages` 参数，用于实现之前文档中提到的 **冷启动补救逻辑**。
        - **要求**: 返回一个字典，包含各领域的概率及其计算解释。

        **2. 活跃时间分布拟合 (`fit_time_distribution`)**
        - **输入**: `List[str]` (由 `github_client.py` 产出的 ISO 时间戳列表)。
        - **逻辑**: 
            - 将时间戳转换为相邻时间间隔（Days/Hours）。
            - 使用 `scipy.stats.weibull_min.fit` 进行参数估计（形状参数 k 和尺度参数 λ）。
            - 同时实现指数分布 (`expon`) 拟合作为对比。
            - 计算 **未来 30 天内活跃的累积概率** $P(T \le 30)$。
        - **异常处理**: 若间隔数据少于 3 个，返回默认的平均分布（冷启动逻辑）。

        **3. 相似性权重融合 (`blend_user_and_community`)**
        - **逻辑**: 实现置信度权重 $w$。
            - $w = \min(1.0, \text{count\_items} / 10)$。
            - 返回结果：$Result = w \cdot User\_Prob + (1-w) \cdot Community\_Prob$。

        **4. 代码要求**:
        - 必须使用 `scipy`, `numpy`, `pandas`。
        - 函数 Docstring 必须包含 LaTeX 格式的数学公式。
        - 建模逻辑必须是纯函数（Pure Functions），便于测试。
    Phase 3: Backend API (FastAPI Integration)
        目标：将 Phase 1 的数据获取与 Phase 2 的数学模型封装为高性能 REST API。

        项目入口 (main.py):

        实现 FastAPI 应用，配置 CORS 跨域支持（允许前端 Vite 默认端口 5173 访问）。

        集成 GitHubClient 和 modeling.py 中的逻辑。

        核心接口逻辑 (GET /api/analyze/{username}):

        数据流：接收用户名 -> 调用 github_client 获取原始数据 -> 传入 modeling.py 进行分析 -> 返回 DeveloperAnalysis 响应。

        缓存机制：实现一个简单的本地缓存（如使用 dict 或 diskcache），缓存分析结果 24 小时，避免重复请求 GitHub API 导致限流。

        错误处理：

        若用户不存在，返回 404 及友好提示。

        若 API 限流，返回 503 及重试时间提示。

        匹配度接口 (POST /api/match):

        输入：username 和 target_stack (技术栈列表)。

        输出：基于 3.5 节公式的匹配分值。
    Phase 4: Frontend Visualization (Vue 3 + ECharts)
        目标：构建一个极简、科技感的 BI 仪表盘，核心展示“预测性”数据。
            组件结构:
                SearchBar.vue: 带有加载状态（Loading）的大搜索框。
                ProfileCard.vue: 展示用户基础信息及 置信度权重 (w)。
                AnalysisDashboard.vue: 核心布局容器。
            核心图表实现 (ECharts):
                技术倾向柱状图 (Tendency Chart):展示 $P(T_i)$ 概率，对“推荐技术栈”使用金黄色高亮，并附带解释文案。
                活跃时间分布图 (Activity Curve):绘制 Weibull 拟合曲线（PDF），横轴为间隔天数，纵轴为概率密度。标注 $P(T \le 30)$ 的覆盖区域，显示“下月活跃概率”。
                重点：技术关系引力图 (Tech Relation Gravity Graph):类型: series: 'graph', layout: 'force'。节点定义: 中心节点为用户头像；四周节点为技术标签（Vue, AI, Rust 等）。引力逻辑: 连线长度 $L = (1 - P(T_i)) \times 500$。概率越高，距离中心越近。视觉引导: 使用不同深浅的颜色表示概率区间，高概率节点带有呼吸灯动画效果。
7. 提示词/代码风格要求 (Prompting Rules)
    代码注释：所有涉及数学公式的函数，必须在 Docstring 中写明对应的数学公式（LaTeX 格式）。
    错误处理：对于网络请求失败、数据不足（<5 个项目）的情况，必须有显式的 try-except 和用户提示。
    不确定的预测：在 UI 文案中，必须使用“倾向于”、“概率为”等词汇，严禁使用“一定会”等确定性词汇。
    禁止行为：
    - 引入 sklearn 的分类 / 回归模型
    - 引入神经网络、embedding、transformer
    - 任何形式的“训练集/测试集”划分

8. 文档管理规范 (Documentation Standards)
    - **目录结构**: 所有文档需存放在 `docs/` 文件夹中，并按阶段 (e.g., `docs/Phase1/`, `docs/Phase2/`) 进行分类管理，避免根目录混乱。