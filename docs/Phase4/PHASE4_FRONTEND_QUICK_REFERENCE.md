# Phase 4 前端快速参考 (Quick Reference)

本文件面向基础较为薄弱的开发者，帮助你快速上手并理解 DevScope 前端（Vue 3 + Vite + ECharts）在 Phase 4 的实现与使用方式。

## 目标与结构
- 技术栈：Vue 3、Vite、TypeScript、ECharts
- 页面结构：单页应用（SPA），包含搜索、加载、结果展示三部分
- 关键组件：
  - `src/App.vue`：主界面与数据请求逻辑
  - `src/components/GravityGraph.vue`：技术关系引力图（力导向）

目录位置：
- 前端根目录：`frontend/`
- 入口文件：`frontend/src/main.ts`
- 主页面：`frontend/src/App.vue`
- 引力图组件：`frontend/src/components/GravityGraph.vue`
- Vite 配置：`frontend/vite.config.ts`

## 数据来源与接口
- 后端服务：FastAPI 在 `http://localhost:8000`
- 前端代理：Vite dev server 在 `http://localhost:5173`，通过代理将 `/api/*` 请求转发到后端
- 核心接口：`GET /api/analyze/{username}`
  - 返回字段（简化）：
    - `persona.avatar_url`：开发者头像 URL
    - `tech_tendency[]`：技术倾向数组（每项含 `category`, `probability`）
    - `time_prediction`：活跃时间拟合结果（可选）

## 使用步骤
1. 启动后端（新终端）：
   ```bash
   cd backend
   python main.py
   ```
2. 启动前端（另一个终端）：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. 打开浏览器访问 `http://localhost:5173`，在搜索框输入 GitHub 用户名（如 `torvalds`），点击“分析”。

## 主页面 `App.vue` 做了什么
- 提供输入框与按钮，收集 `username`
- 使用 `axios` 调用 `GET /api/analyze/{username}` 获取分析数据
- 展示：
  - 个人信息卡片（头像、简介、仓库数等）
  - 技术倾向柱状图（ECharts）
  - 技术关系引力图（`GravityGraph`）
  - 活跃时间预测（若后端返回）
- 错误处理：将接口错误友好提示到界面上

## 引力图组件 `GravityGraph.vue`
- 类型：ECharts `graph` 系列，`layout: 'force'`
- 节点：
  - 中心节点：开发者，显示头像（`symbol: image://...`）
  - 技术节点：围绕中心节点分布
- 连线距离：严格按公式计算：
  - $L = (1 - P) \times 500$（概率越高距离越近）
  - 通过 `links[].value = L` + `force.edgeLength: [10, 500]` 映射到实际边长
- 交互：
  - 点击技术节点触发事件 `node-click`（携带 `category` 与 `probability`）
- 属性 (Props)：
  - `username: string`
  - `avatarUrl?: string`
  - `techTendency: { category: string; probability: number }[]`
  - `width?: number`、`height?: number`

示例使用（在 `App.vue`）：
```vue
<GravityGraph
  :username="analysisData.username"
  :avatar-url="analysisData.persona.avatar_url"
  :tech-tendency="analysisData.tech_tendency"
  :width="800"
  :height="500"
  @node-click="handleNodeClick"
/>
```

## 配置文件说明
- `frontend/vite.config.ts`
  - `server.proxy['/api']` 指向 `http://localhost:8000`
  - 使得前端调用相对路径 `/api/...` 自动代理到后端，无需处理 CORS
- `frontend/package.json`
  - `scripts.dev`：启动 Vite 开发服务
  - 依赖：`vue`、`echarts`、`axios`

## 常见问题排查
- 页面无响应：请打开浏览器开发者工具（F12），查看 Network 是否有对 `/api/analyze/{username}` 的请求；若没有，请确认你已输入用户名并点击“分析”。
- 代理是否生效：在浏览器访问 `http://localhost:5173/api/analyze/octocat` 应该由 Vite 代理到后端；若返回 404，请确认后端接口路径是否正确且服务运行中。
- 后端是否启动：访问 `http://localhost:8000/health` 应返回 `{status: 'ok'}`。
- CORS 问题：开发环境使用代理，通常无需额外 CORS 设置；若绕过代理直接访问后端，请确保后端允许来源 `http://localhost:5173`。

## 最小改动原则
- 组件仅实现要求的力导向图、距离公式、头像与点击交互
- 无多余动画与复杂样式，便于后续迭代与维护
