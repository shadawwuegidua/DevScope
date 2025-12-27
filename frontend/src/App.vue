<template>
  <div class="container">
    <h1 class="title">DevScope</h1>
    <p class="subtitle">开发者画像与行为倾向分析</p>
    
    <!-- 搜索框 -->
    <div class="search-box">
      <input
        v-model="username"
        type="text"
        placeholder="输入 GitHub 用户名..."
        class="search-input"
        @keyup.enter="fetchAnalysis"
        :disabled="loading || isRequesting"
      />
      <button @click="fetchAnalysis" :disabled="loading || isRequesting" class="search-btn">
        {{ loading ? '分析中...' : '分析' }}
      </button>
      <button @click="showDocs = true" class="doc-btn">
        文档
      </button>
    </div>

    <DocModal :is-open="showDocs" @close="showDocs = false" />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在抓取数据并拟合概率模型...</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="error && !loading" class="error">
      <p>{{ error }}</p>
      <button @click="reset" class="reset-btn">重新搜索</button>
    </div>

    <!-- 分析结果 -->
    <div v-if="analysisData && !loading" class="dashboard">
      <button @click="reset" class="back-btn">← 返回搜索</button>
      
      <!-- 个人信息卡片 -->
      <div class="profile-card">
        <img
          v-if="analysisData.persona.avatar_url"
          :src="analysisData.persona.avatar_url"
          :alt="analysisData.username"
          class="avatar"
        />
        <div class="profile-info">
          <h2>{{ analysisData.persona.name || analysisData.username }}</h2>
          <p v-if="analysisData.persona.bio" class="bio">{{ analysisData.persona.bio }}</p>
          <div class="stats">
            <span>仓库: {{ analysisData.persona.public_repos }}</span>
            <span>关注者: {{ analysisData.persona.followers }}</span>
            <span>主要语言: {{ analysisData.primary_language || 'N/A' }}</span>
          </div>
          <p v-if="analysisData.is_cold_start" class="cold-start-note">
            ⚠️ {{ analysisData.cold_start_note }}
          </p>
        </div>
      </div>

      <!-- 活跃时间预测 (Moved to top) -->
      <div v-if="analysisData.time_prediction" class="chart-section">
        <h3>活跃时间预测</h3>
        <div class="time-prediction">
          <p>预期活跃间隔: <strong>{{ analysisData.time_prediction.expected_interval_days.toFixed(1) }}</strong> 天</p>
          <p>未来30天活跃概率: <strong>{{ (analysisData.time_prediction.next_active_prob_30d * 100).toFixed(1) }}%</strong></p>
          <p>分布类型: {{ analysisData.time_prediction.distribution_type }}</p>
        </div>
      </div>

      <!-- Contribution Graph -->
      <div class="chart-section">
        <h3>贡献活跃度</h3>
        <ContributionGraph :timestamps="analysisData.contribution_calendar" />
      </div>

      <!-- 技术倾向柱状图 -->
      <div class="chart-section">
        <h3>技术倾向预测</h3>
        <div ref="tendencyChartRef" class="chart"></div>
      </div>

      <!-- 技术关系引力图 -->
      <div class="chart-section">
        <h3>技术关系引力图</h3>
        <GravityGraph
          :username="analysisData.username"
          :avatar-url="analysisData.persona.avatar_url"
          :tech-tendency="analysisData.tech_tendency"
          :width="1000"
          :height="600"
          @node-click="handleNodeClick"
        />
        <p v-if="selectedTech" class="tech-info">
          点击技术: <strong>{{ selectedTech.category }}</strong> 
          (概率: {{ (selectedTech.probability * 100).toFixed(1) }}%)
        </p>
      </div>

      <!-- Next Commit Prediction -->
      <div class="chart-section" v-if="analysisData.next_commit_prediction">
        <h3>下一次提交预测 (AI)</h3>
        <div class="prediction-card">
          <div class="prediction-header">
            <span class="tag focus-area">{{ analysisData.next_commit_prediction.focus_area }}</span>
            <span class="tag commit-type">{{ analysisData.next_commit_prediction.commit_type }}</span>
          </div>
          <p class="prediction-text">{{ analysisData.next_commit_prediction.prediction }}</p>
        </div>
      </div>

      <!-- Recent Commits -->
      <div class="chart-section" v-if="analysisData.recent_commits && analysisData.recent_commits.length > 0">
        <h3>最近提交动态</h3>
        <div class="commits-list">
          <div v-for="(commit, index) in analysisData.recent_commits" :key="index" class="commit-item">
            <div class="commit-header">
              <span class="repo-name">{{ commit.repo_name }}</span>
              <span class="commit-date">{{ new Date(commit.date).toLocaleDateString() }}</span>
            </div>
            <div class="commit-message">
              <a :href="commit.url" target="_blank">{{ commit.message }}</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { api } from './api'
import * as echarts from 'echarts'
import GravityGraph from './components/GravityGraph.vue'
import ContributionGraph from './components/ContributionGraph.vue'
import DocModal from './components/DocModal.vue'

type TechItem = {
  category: string
  probability: number
  explanation: string
}

type CommitInfo = {
  message: string
  repo_name: string
  date: string
  url: string
}

type NextCommitPrediction = {
  focus_area: string
  commit_type: string
  prediction: string
}

type AnalysisData = {
  username: string
  is_cold_start: boolean
  confidence_weight: number
  persona: {
    username: string
    name?: string
    bio?: string
    avatar_url?: string
    company?: string
    location?: string
    public_repos: number
    followers: number
    following: number
    created_at?: string
  }
  tech_tendency: TechItem[]
  next_commit_prediction?: NextCommitPrediction
  time_prediction?: {
    expected_interval_days: number
    next_active_prob_30d: number
    distribution_type: string
  }
  primary_language?: string
  cold_start_note?: string
  recent_commits: CommitInfo[]
  contribution_calendar: string[]
}

const username = ref('')
const loading = ref(false)
const error = ref('')
const showDocs = ref(false)
const analysisData = ref<AnalysisData | null>(null)
const tendencyChartRef = ref<HTMLDivElement>()
const selectedTech = ref<TechItem | null>(null)

let tendencyChart: echarts.ECharts | null = null

// 防止重复请求
let isRequesting = false

async function fetchAnalysis() {
  // 防止重复请求
  if (isRequesting || loading.value) {
    return
  }

  const searchUsername = username.value.trim()
  if (!searchUsername) {
    error.value = '请输入GitHub用户名'
    return
  }

  // 验证用户名格式（GitHub用户名规则：1-39个字符，只能包含字母数字和连字符）
  if (!/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/.test(searchUsername)) {
    error.value = '请输入有效的GitHub用户名（1-39个字符，只能包含字母、数字和连字符）'
    return
  }

  isRequesting = true
  loading.value = true
  error.value = ''
  analysisData.value = null

  try {
    console.log('开始分析用户:', searchUsername)
    
    // 修复：baseURL已经是/api，所以这里只需要/analyze/{username}
    // 添加时间戳防止缓存
    const res = await api.get(`/analyze/${encodeURIComponent(searchUsername)}?t=${Date.now()}`)
    
    if (!res.data) {
      throw new Error('后端返回数据为空')
    }
    
    console.log('分析成功，收到数据:', res.data)
    console.log('技术倾向数据:', res.data.tech_tendency)
    analysisData.value = res.data
    
    // 等待DOM更新后渲染图表
    await nextTick()
    // 再次等待确保DOM完全渲染
    await new Promise(resolve => setTimeout(resolve, 100))
    renderTendencyChart()
  } catch (err: any) {
    console.error('分析失败:', err)
    
    // 处理各种错误情况
    if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
      error.value = '请求超时，请稍后重试或设置 GitHub Token 提升速率'
    } else if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error') || err?.message?.includes('Failed to fetch')) {
      error.value = '无法连接后端服务，请确认 http://localhost:8000 正在运行'
    } else if (err?.response?.status === 404) {
      const detail = err?.response?.data?.detail || err?.response?.data?.error
      error.value = detail || `GitHub 用户 "${searchUsername}" 不存在或没有公开仓库`
    } else if (err?.response?.status === 503) {
      error.value = err?.response?.data?.detail || err?.response?.data?.error || 'GitHub API 请求次数已达限制，请 1 小时后重试'
    } else if (err?.response?.status === 400) {
      error.value = err?.response?.data?.detail || err?.response?.data?.error || '请求参数错误'
    } else if (err?.response?.status === 500) {
      error.value = err?.response?.data?.detail || err?.response?.data?.error || '服务器内部错误，请稍后重试'
    } else if (err?.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err?.response?.data?.error) {
      error.value = err.response.data.error
    } else {
      error.value = err?.message || '分析失败，请稍后重试'
    }
  } finally {
    loading.value = false
    isRequesting = false
  }
}

function reset() {
  username.value = ''
  analysisData.value = null
  error.value = ''
  selectedTech.value = null
  loading.value = false
  isRequesting = false
  
  // 清理图表
  if (tendencyChart) {
    const resizeHandler = (tendencyChart as any)?._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    tendencyChart.dispose()
    tendencyChart = null
  }
}

function renderTendencyChart() {
  console.log('开始渲染技术倾向图表')
  console.log('tendencyChartRef.value:', tendencyChartRef.value)
  console.log('analysisData.value:', analysisData.value)
  
  if (!tendencyChartRef.value || !analysisData.value) {
    console.warn('图表容器或数据不存在，无法渲染')
    return
  }

  // 如果图表已存在，先销毁
  if (tendencyChart) {
    tendencyChart.dispose()
    tendencyChart = null
  }

  tendencyChart = echarts.init(tendencyChartRef.value)
  console.log('ECharts实例已创建')
  
  // 确保数据存在
  if (!analysisData.value.tech_tendency || analysisData.value.tech_tendency.length === 0) {
    console.warn('技术倾向数据为空')
    tendencyChart.setOption({
      title: {
        text: '暂无技术倾向数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#999' }
      }
    })
    return
  }

  console.log('技术倾向数据:', analysisData.value.tech_tendency)
  const data = analysisData.value.tech_tendency.map(t => ({
    name: t.category,
    value: t.probability * 100
  }))
  console.log('处理后的图表数据:', data)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        // 保留两位小数
        if (Array.isArray(params)) {
          const p = params[0]
          return `${p.name}: ${Number(p.value).toFixed(2)}%`
        }
        return `${params.name}: ${Number(params.value).toFixed(2)}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: { rotate: 45, interval: 0 }
    },
    yAxis: {
      type: 'value',
      name: '概率 (%)',
      axisLabel: {
        formatter: (val: number) => Number(val).toFixed(2)
      }
    },
    series: [{
      type: 'bar',
      data: data.map(d => Number(d.value.toFixed(2))),
      label: {
        show: true,
        position: 'top',
        formatter: ({ value }: any) => Number(value).toFixed(2) + '%'
      },
      itemStyle: {
        color: '#667eea'
      }
    }]
  }

  tendencyChart.setOption(option)
  console.log('图表配置已应用')
  
  // 监听窗口大小变化
  const resizeHandler = () => {
    tendencyChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
  
  // 在组件卸载时移除监听器
  if (tendencyChart) {
    // 存储resize handler以便后续清理
    ;(tendencyChart as any)._resizeHandler = resizeHandler
  }
}

function handleNodeClick(payload: { category: string; probability: number }) {
  selectedTech.value = {
    category: payload.category,
    probability: payload.probability,
    explanation: ''
  }
}

watch(analysisData, (newVal) => {
  if (newVal) {
    console.log('analysisData变化，准备渲染图表')
    nextTick(() => {
      // 确保DOM完全渲染后再渲染图表
      setTimeout(() => {
        renderTendencyChart()
      }, 200)
    })
  }
}, { deep: true })
</script>

<style scoped>
.container {
  max-width: 1200px;
  width: 100%;
}

.title {
  font-size: 3rem;
  color: white;
  text-align: center;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.subtitle {
  font-size: 1.2rem;
  color: rgba(255,255,255,0.9);
  text-align: center;
  margin-bottom: 2rem;
}

.search-box {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.search-input {
  width: 400px;
  padding: 1rem;
  font-size: 1.1rem;
  border: none;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.search-btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: bold;
  color: white;
  background: #3c229b;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: background 0.3s;
}

.search-btn:hover:not(:disabled) {
  background: #38a169;
}

.search-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.doc-btn {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
  background: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: background 0.3s;
}

.doc-btn:hover {
  background: #f0f0f0;
}

.loading {
  text-align: center;
  color: white;
  padding: 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  text-align: center;
  color: white;
  background: rgba(255,0,0,0.2);
  padding: 1rem;
  border-radius: 8px;
}

.reset-btn, .back-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.dashboard {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.back-btn {
  margin-bottom: 1rem;
}

.profile-card {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f7fafc;
  border-radius: 8px;
}

.avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
}

.profile-info h2 {
  margin-bottom: 0.5rem;
  color: #2d3748;
}

.bio {
  color: #4a5568;
  margin-bottom: 1rem;
}

.stats {
  display: flex;
  gap: 1.5rem;
  color: #718096;
  font-size: 0.9rem;
}

.cold-start-note {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fef5e7;
  border-left: 4px solid #f39c12;
  font-size: 0.9rem;
  color: #856404;
}

.chart-section {
  margin-bottom: 2rem;
}

.chart-section h3 {
  margin-bottom: 1rem;
  color: #2d3748;
}

.chart {
  width: 100%;
  height: 400px;
  min-height: 400px;
}

.time-prediction {
  padding: 1.5rem;
  background: #f7fafc;
  border-radius: 8px;
}

.time-prediction p {
  margin-bottom: 0.5rem;
  color: #4a5568;
}

.tech-info {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #e6fffa;
  border-left: 4px solid #38b2ac;
  color: #234e52;
}

.commits-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.commit-item {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
}

.commit-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #718096;
}

.repo-name {
  font-weight: bold;
  color: #4a5568;
}

.commit-message a {
  color: #2b6cb0;
  text-decoration: none;
  font-weight: 500;
}

.commit-message a:hover {
  text-decoration: underline;
}

.prediction-card {
  padding: 1.5rem;
  background: linear-gradient(to right, #f0f9ff, #e6fffa);
  border-radius: 8px;
  border: 1px solid #bbeeeb;
}

.prediction-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.tag {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.focus-area {
  background-color: #ebf8ff;
  color: #2b6cb0;
  border: 1px solid #bee3f8;
}

.commit-type {
  background-color: #f0fff4;
  color: #2f855a;
  border: 1px solid #c6f6d5;
}

.prediction-text {
  color: #2d3748;
  font-size: 1.1rem;
  line-height: 1.6;
}
</style>
