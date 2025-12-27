# DevScope - 开发者画像与行为倾向分析平台

DevScope 是一个基于 GitHub 开源生态数据的开发者分析与可视化平台。通过统计建模与可解释概率分布，为开发者的技术倾向和未来活跃行为提供可视化预测。

## 项目结构
```
backend/      # FastAPI 后端（Phase 1-3）
docs/         # 文档（各 Phase）
frontend/     # Vue 3 + Vite 前端（Phase 4）
```

## 前置条件
- Python 3.9+
- Node.js 18+
- （可选）GitHub Token（提高 API 速率，配置在环境变量中）
- （可选）LLM API Key（用于下一次提交预测功能，支持 ECNU API）

## 环境变量配置 (.env)
在 `backend` 目录下创建 `.env` 文件，添加以下配置：
```env
# GitHub Token (可选，用于提高 GitHub API 速率限制)
GITHUB_TOKEN=your_github_token_here

# LLM API 配置 (可选，用于启用 AI 预测功能)
# 默认使用 ECNU 开放 API
LLM_API_KEY=your_ecnu_api_key_here
# LLM_API_BASE=https://chat.ecnu.edu.cn/open/api/v1  # 默认值，可不填
# LLM_MODEL=ecnu-plus                                # 默认值，可不填
```

## 后端启动（FastAPI）
1. 安装依赖：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. 启动服务：
   ```bash
   python main.py
   ```
3. 健康检查：
   - 访问 `http://localhost:8000/health` 应返回 `{status: 'ok'}`

## 前端启动（Vue 3 + Vite）
1. 安装依赖（必须）：
   ```bash
   cd frontend
   npm install
   ```
   - 说明：此步骤会安装包含 `concurrently` 在内的前端依赖；若跳过，`npm run dev:all` 可能报错“concurrently 不是内部或外部命令”。

2. 一键启动（推荐，前后端同时运行）：
   ```bash
   # 在 frontend 目录内
   npm run dev:all
   ```
   - 后端：FastAPI（端口 8000）
   - 前端：Vite（端口 5173）

3. 分别启动（备选方案）：
   - 终端A（后端）：
     ```bash
     cd backend
     python main.py
     ```
   - 终端B（前端）：
     ```bash
     cd frontend
     npm run dev
     ```

4. 打开浏览器访问 `http://localhost:5173`

## 使用指南
1. 在页面输入 GitHub 用户名（如 `octocat`），点击“分析”
2. 查看分析结果：
   - 个人信息卡片（头像、简介、仓库数等）
   - 技术倾向柱状图（各技术的概率）
   - 技术关系引力图（概率越高越靠近中心）
   - 活跃时间预测（拟合的分布与下月活跃概率）
3. 点击引力图中的技术节点，可查看该技术的概率数值

## 关键实现原则
- 统计建模可解释，禁止引入黑箱模型（深度学习等）
- 遵循文档中的拉普拉斯平滑、时间分布拟合、冷启动融合等规则
- 前端满足最小必要实现：不做额外内容，专注核心图表与交互

## 常见问题与排查
- 前端页面无响应：
  - 确认后端已运行并 `http://localhost:8000/health` 正常
   - 打开浏览器开发者工具查看 Network 是否有 `/api/analyze/{username}` 请求
   - 确认 Vite 代理已生效，`vite.config.ts` 中 `/api` 指向 `http://localhost:8000`
   - 推荐使用 `npm run dev:all`，避免因未启动后端导致请求失败
- 速率限制：
  - GitHub API 受限时后端会提示，请稍后重试或配置令牌提升速率

### 端口占用（Windows）
- 检查端口：
   ```powershell
   netstat -ano | Select-String ":8000"
   netstat -ano | Select-String ":5173"
   ```
- 结束占用进程：
   ```powershell
   # 将 <PID> 替换为上一步查到的进程号
   Stop-Process -Id <PID> -Force
   ```
- 健康检查（PowerShell）：
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | Select-Object -ExpandProperty Content
   ```

### `npm run dev:all` 报错 "concurrently 不是内部或外部命令"
- 解决：在 frontend 目录重新安装依赖
   ```bash
   cd frontend
   npm install
   npm run dev:all
   ```

### GitHub Token（提升速率）
- PowerShell 设置环境变量（临时）：
   ```powershell
   $env:GITHUB_TOKEN = "your_github_token_here"
   ```
   重新启动后端后生效。

## 相关文档
- Phase 4 前端快速参考：`docs/Phase4/PHASE4_FRONTEND_QUICK_REFERENCE.md`
- 项目安全规范：`SECURITY.md`
