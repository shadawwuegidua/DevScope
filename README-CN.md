# DevScope

[![Node Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](https://nodejs.org/)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![English](https://img.shields.io/badge/English-README.md-blue)](README.md)

<!-- 建议：在此处放置项目 Banner 或 Logo -->
<!-- ![DevScope Banner](path/to/banner.png) -->

## 目录
<div align="center">
  <img src="assets/1658984090518c59925f2668b3b0ff3b.png" alt="DevScope 概览" width="100%">
</div>

- [背景](#背景)
- [项目介绍](#项目介绍)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [核心算法](#核心算法)
- [安装指南](#安装指南)
- [使用指南](#使用指南)
- [文档体系](#文档体系)
- [开发计划](#开发计划)

## 背景
开源生态日益繁荣，但深入理解开发者行为依然充满挑战。简单的提交计数往往无法真实反映贡献者的技术深度与未来活跃度。DevScope 致力于解决这一问题，提供一个基于统计学原理、具备可解释性的开发者画像构建与行为预测平台。

## 项目介绍
DevScope 是一个基于 GitHub 开源生态数据的开发者分析与可视化平台。与“黑箱”AI 模型不同，DevScope 采用透明的统计建模（如多项分布、韦伯分布），并结合大语言模型（LLM），提供：
- 精准的技术倾向画像。
- 未来活跃时间预测。
- 开发焦点的语义分析。

## 核心功能

<!-- 建议：在此处放置完整的仪表盘截图 -->
<!-- ![Dashboard Screenshot](path/to/dashboard.png) -->

1. **多维度画像**
   - **技术倾向**：利用多项分布模型识别开发者的技术专长。
   - **活跃预测**：基于提交间隔的韦伯分布分析，预测下一个活跃日期。

2. **冷启动优化**
   - 利用贝叶斯融合技术，将个人数据与社区先验（基于顶级开发者构建）结合，为新用户或低活跃用户提供准确分析。

3. **LLM 辅助预测**
   - 集成大语言模型分析通过 Commit Message，预测下一次贡献的具体关注领域和类型。

4. **交互式可视化**
   - **引力图**：可视化开发者与技术栈之间的连接强度。
   - **仪表盘**：全方位展示 OpenRank、活跃趋势及预测结果。

<!-- 建议：在此处放置引力图的特写截图 -->
<!-- ![Gravity Graph](path/to/gravity_graph.png) -->

## 技术架构

### 前端技术栈
- **Vue 3**: 渐进式 JavaScript 框架。
- **Vite**: 下一代前端构建工具。
- **ECharts**: 强大的交互式图表库。
- **TypeScript**: 静态类型检查。

### 后端技术栈
- **FastAPI**: 现代化、高性能的 Python Web 框架。
- **GitHub API**: 开发者活动的主要数据源。
- **OpenDigger**: 宏观开源指标（OpenRank）数据源。
- **LLM Integrations**: 支持 ECNU API 和其他 LLM 服务提供商。

<!-- 建议：在此处放置展示 数据源 -> 后端(建模) -> 前端 的架构图 -->
<!-- ![Architecture Diagram](path/to/architecture.png) -->

## 核心算法

系统基于可解释的统计学原理构建：

1.  **技术倾向（多项分布 + 拉普拉斯平滑）**：对技术使用概率进行建模，并对未观测事件进行平滑处理。
2.  **时间预测（韦伯分布）**：对提交间隔时间进行概率密度拟合，预测未来活跃度。
3.  **贝叶斯融合**：融合用户似然度与社区先验，实现鲁棒估计。

## 安装指南

### 前置条件
- Node.js 18+
- Python 3.9+
- Git

### 1. 配置 Token
生成一个 GitHub Personal Access Token (Classic)，勾选 `repo` 和 `user` 权限，以提高 API 速率限制。

### 2. 项目设置
```bash
git clone <repository-url>
cd DevScope
```

### 3. 后端设置
```bash
cd backend
# 创建配置文件 .env
# 添加内容:
# GITHUB_TOKEN=your_token
# LLM_API_KEY=your_key (可选，用于 LLM 功能)

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 4. 前端设置
```bash
cd frontend
# 安装依赖
npm install

# 启动客户端
npm run dev
# 或 同时运行前后端（推荐）
npm run dev:all
```

## 使用指南

1.  **启动系统**：确保后端（8000端口）和前端（5173端口）均已运行，然后在浏览器中访问 `http://localhost:5173`。
2.  **分析开发者**：在搜索栏输入 GitHub 用户名（例如 `torvalds`）。
3.  **探索洞察**：
    *   查看**引力图**了解技术栈亲和度。
    *   检查**活跃预测**，获取未来活跃日期预测。
    *   使用**AI 预测**功能，猜测下一次提交的具体内容。

## 文档体系
详细文档位于 `docs/` 目录：

- [项目概览](docs/PROJECT_OVERVIEW.md)
- [数据算法理论](docs/DATA_ALGORITHM_THEORY.md)
- [LLM 功能指南](backend/LLM_FEATURE_GUIDE.md)

## 开发计划
- [x] **Phase 1**: 核心数据获取与清洗 (GitHub/OpenDigger)
- [x] **Phase 2**: 统计建模 (韦伯分布/多项分布)
- [x] **Phase 3**: API 开发与 LLM 集成
- [x] **Phase 4**: 前端可视化与交互式仪表盘
- [ ] **未来计划**: 多用户对比与团队画像

## 团队介绍
**队伍名称**：爱如潮水

- **队长**：**庄子由**
  - **职责**：前后端开发、文档、PPT撰写
- **队员**：**曹玉霖**
  - **职责**：Debug、文档、PPT撰写、演示视频录制
