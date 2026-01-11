<template>
  <DocPage v-if="currentView === 'docs'" @back="currentView = 'home'" />
  <div v-else class="container">
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
      <button @click="currentView = 'docs'" class="doc-btn">
        文档
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="progress-bar-container">
        <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="progress-text">{{ progressMessage || '初始化中...' }} <span v-if="progress > 0" class="progress-pct">({{ progress }}%)</span></p>
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
          <p
            v-if="analysisData.persona && (analysisData.persona as any).openrank !== undefined && (analysisData.persona as any).openrank !== null"
            class="openrank-line"
          >
            <strong>OpenRank: {{ Number((analysisData.persona as any).openrank).toFixed(2) }}</strong>
          </p>
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
        <div v-if="analysisData?.topic_tendency && analysisData.topic_tendency.length > 0">
          <div ref="topicChartRef" class="chart"></div>
        </div>
        <p v-else class="chart-subtitle">暂无Topic倾向数据</p>
        <div ref="languageChartRef" class="chart"></div>

        <!-- 近期贡献的 Topic / 语言 / 仓库 / OpenRank -->
        <div class="recent-topic-list">
          <h4>近期贡献映射</h4>
          <div v-if="analysisData.recent_topic_contributions && analysisData.recent_topic_contributions.length > 0">
            <div class="recent-topic-row recent-topic-header">
              <span>Topic</span>
              <span>语言</span>
              <span>仓库</span>
              <span>OpenRank</span>
            </div>
            <div
              v-for="(item, idx) in analysisData.recent_topic_contributions"
              :key="idx"
              class="recent-topic-row"
            >
              <span class="topic-label">{{ item.topic || 'Unspecified' }}</span>
              <span>{{ item.language || 'N/A' }}</span>
              <a :href="item.repo_url" target="_blank" rel="noreferrer" class="repo-link">{{ item.repo }}</a>
              <span><strong>{{ item.repo_openrank !== null && item.repo_openrank !== undefined ? item.repo_openrank.toFixed(2) : 'N/A' }}</strong></span>
            </div>
          </div>
          <p v-else class="chart-subtitle">暂无近期贡献映射数据</p>
        </div>
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

      <!-- 综合匹配度打分 -->
      <div class="chart-section">
        <h3>综合匹配度打分</h3>
        <div class="match-inputs">
          <input
            v-model="matchLocatorInput"
            type="text"
            placeholder="定位技术（输入名称，自动滚动到对应项）"
            class="search-input"
            :disabled="loading || isRequesting"
            @keyup.enter="locateMatchItem"
          />
          <button @click="locateMatchItem" :disabled="loading || isRequesting || !analysisData" class="search-btn">
            定位
          </button>
        </div>
        <p class="chart-subtitle">匹配度基于技术倾向与未来30天活跃概率综合计算</p>

        <div v-if="Object.keys(matchResults).length > 0">
          <div ref="matchChartRef" class="chart"></div>
          <div class="match-controls" v-if="Object.keys(matchResults).length > matchLimit">
            <button class="expand-btn" @click="matchExpanded = !matchExpanded">
              {{ matchExpanded ? '收起' : `展开全部 (共 ${Object.keys(matchResults).length} 项)` }}
            </button>
          </div>
          <div class="match-list">
            <div v-for="([tech, item], idx) in displayedMatches" :key="tech" :class="['match-item', { highlight: isTechHighlighted(tech) }]" :id="sanitizeTechId(tech)">
              <div class="match-header">
                <span class="tech-name">{{ tech }}</span>
                <span class="match-score">综合分: {{ (item.score * 100).toFixed(1) }}%</span>
              </div>
              <div class="match-detail">
                <span>技术倾向: {{ (item.tech_prob * 100).toFixed(1) }}%</span>
                <span>活跃概率(30d): {{ (item.active_prob * 100).toFixed(1) }}%</span>
              </div>
              <p class="match-explanation" v-if="item.explanation">{{ item.explanation }}</p>
            </div>
          </div>
        </div>
        <p v-else class="chart-subtitle">暂无匹配度数据。</p>
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
import { ref, watch, nextTick, computed } from 'vue'
import { api } from './api'
import * as echarts from 'echarts'
import GravityGraph from './components/GravityGraph.vue'
import ContributionGraph from './components/ContributionGraph.vue'
import DocPage from './components/DocPage.vue'

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
    openrank?: number | null
  }
  tech_tendency: TechItem[]
  topic_tendency: TechItem[]
  language_tendency: TechItem[]
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
  recent_topic_contributions: {
    topic: string
    language?: string | null
    repo: string
    repo_url: string
    repo_openrank?: number | null
  }[]
}

const username = ref('')
const loading = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const error = ref('')
const currentView = ref<'home' | 'docs'>('home')
const analysisData = ref<AnalysisData | null>(null)
const topicChartRef = ref<HTMLDivElement>()
const languageChartRef = ref<HTMLDivElement>()
const matchChartRef = ref<HTMLDivElement>()
const selectedTech = ref<TechItem | null>(null)

let topicChart: echarts.ECharts | null = null
let languageChart: echarts.ECharts | null = null
let matchChart: echarts.ECharts | null = null

// 综合匹配度：定位输入与结果（自动计算）
const matchLocatorInput = ref('')
const matchResults = ref<Record<string, { score: number; explanation?: string; tech_prob: number; active_prob: number }>>({})
const matchExpanded = ref(false)
const matchLimit = 10
const matchKeywords = computed(() => (
  (matchLocatorInput.value || '')
    .split(/[\s,]+/)
    .map(s => s.trim().toLowerCase())
    .filter(s => s.length > 0)
))
const isTechHighlighted = (tech: string) => {
  const t = (tech || '').toLowerCase()
  return matchKeywords.value.some(k => t.includes(k))
}
const displayedMatches = computed(() => {
  const entries = Object.entries(matchResults.value)
  return matchExpanded.value ? entries : entries.slice(0, matchLimit)
})

// 防止重复请求
let isRequesting = false

async function fetchAnalysis() {
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
  progress.value = 0
  progressMessage.value = '准备开始...'
  error.value = ''
  analysisData.value = null

  console.log('开始分析用户(SSE):', searchUsername)
  
  // 使用 SSE 流式获取进度和结果
  const streamUrl = `/api/analyze/${encodeURIComponent(searchUsername)}/stream?t=${Date.now()}`
  
  let eventSource: EventSource | null = null;
  try {
    eventSource = new EventSource(streamUrl)
  
    eventSource.onopen = () => {
      console.log('SSE 连接已建立')
    }

    eventSource.onmessage = async (event) => {
      try {
        if (!event.data) return
        const msg = JSON.parse(event.data)
        
        if (msg.type === 'progress') {
          progress.value = msg.value
          progressMessage.value = msg.message
        } else if (msg.type === 'result') {
          console.log('收到分析结果:', msg.data)
          analysisData.value = msg.data
          eventSource?.close()
          loading.value = false
          isRequesting = false
          
          await nextTick()
          await new Promise(resolve => setTimeout(resolve, 100))
          renderCharts()
        } else if (msg.type === 'error' || msg.type === 'rx_error') {
          throw new Error(msg.message || msg.data)
        }
      } catch (e: any) {
        console.error('SSE Message Error:', e)
        error.value = e.message || '解析响应失败'
        eventSource?.close()
        loading.value = false
        isRequesting = false
      }
    }

    eventSource.onerror = (e) => {
      // 只有在没有收到数据且报错时才认为是连接错误
      if (eventSource?.readyState === EventSource.CLOSED) {
          if (!analysisData.value && !error.value) {
             console.error('SSE Closed prematurely', e)
             error.value = '连接中断或分析出错，请检查网络或重试'
             loading.value = false
             isRequesting = false
          }
      } else {
          console.error('SSE Error:', e)
          // 尝试关闭
          eventSource?.close()
          if (!error.value) {
             error.value = '连接服务器失败，请确认后端服务运行正常'
          }
          loading.value = false
          isRequesting = false
      }
    }
  } catch(err: any) {
      console.error('SSE Setup Error:', err)
      error.value = err.message
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
  if (topicChart) {
    const resizeHandler = (topicChart as any)?._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    topicChart.dispose()
    topicChart = null
  }
  if (languageChart) {
    const resizeHandler = (languageChart as any)?._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    languageChart.dispose()
    languageChart = null
  }
  if (matchChart) {
    const resizeHandler = (matchChart as any)?._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    matchChart.dispose()
    matchChart = null
  }
  matchResults.value = {}
}

function renderBarChart(
  chartRef: HTMLDivElement | undefined,
  dataSource: TechItem[] | undefined,
  titleWhenEmpty: string,
  currentChart: echarts.ECharts | null,
  axisBold: boolean = false
): echarts.ECharts | null {
  if (!chartRef) {
    console.warn('图表容器不存在')
    return null
  }

  if (currentChart) {
    const resizeHandler = (currentChart as any)?._resizeHandler
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
    }
    currentChart.dispose()
    currentChart = null
  }

  const chart = echarts.init(chartRef)

  if (!dataSource || dataSource.length === 0) {
    chart.setOption({
      title: {
        text: titleWhenEmpty,
        left: 'center',
        top: 'center',
        textStyle: { color: '#999' }
      }
    })
    return chart
  }

  const data = dataSource.map(t => ({
    name: t.category,
    value: t.probability * 100
  }))

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
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
      axisLabel: { rotate: 45, interval: 0, fontWeight: axisBold ? 'bold' : 'normal' }
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

  chart.setOption(option)

  const resizeHandler = () => {
    chart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
  ;(chart as any)._resizeHandler = resizeHandler
  return chart
}

function renderCharts() {
  if (!analysisData.value) return
  topicChart = renderBarChart(
    topicChartRef.value,
    (analysisData.value.topic_tendency && analysisData.value.topic_tendency.length > 0)
      ? analysisData.value.topic_tendency
      : (analysisData.value.tech_tendency || analysisData.value.language_tendency),
    '暂无 Topic 倾向数据',
    topicChart,
    true
  )
  languageChart = renderBarChart(
    languageChartRef.value,
    analysisData.value.language_tendency,
    '暂无语言倾向数据',
    languageChart,
    false
  )
  // 若已有匹配结果，刷新匹配度图
  computeMatchResults()
  renderMatchChart()
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
        renderCharts()
      }, 200)
    })
    // 切换用户时清空此前匹配结果，避免误展示
    matchResults.value = {}
  }
}, { deep: true })

function computeMatchResults() {
  if (!analysisData.value) return
  const techs = analysisData.value.tech_tendency || []
  const activeProb = analysisData.value.time_prediction?.next_active_prob_30d ?? 0.5
  const results: Record<string, { score: number; explanation?: string; tech_prob: number; active_prob: number }> = {}
  for (const t of techs) {
    const score = t.probability * 0.7 + activeProb * 0.3
    results[t.category] = {
      score,
      tech_prob: t.probability,
      active_prob: activeProb,
      explanation: '综合分 = 技术倾向(70%) + 活跃概率(30%)'
    }
  }
  // 排序：分数高到低
  const sorted = Object.entries(results).sort((a, b) => b[1].score - a[1].score)
  matchResults.value = Object.fromEntries(sorted)
}

function renderMatchChart() {
  const items: TechItem[] = Object.entries(matchResults.value).map(([tech, info]) => ({
    category: tech,
    probability: info.score,
    explanation: ''
  }))
  matchChart = renderBarChart(
    matchChartRef.value,
    items,
    '暂无匹配度数据',
    matchChart
  )
}

function sanitizeTechId(tech: string) {
  return 'match-' + tech.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-_]/g, '').toLowerCase()
}

function locateMatchItem() {
  const q = (matchLocatorInput.value || '').toLowerCase().trim()
  if (!q) return
  const keys = Object.keys(matchResults.value)
  const found = keys.find(k => k.toLowerCase().includes(q))
  if (!found) return
  
  // 检查找到的tech是否在当前显示的列表中
  const displayedKeys = displayedMatches.value.map(([tech]) => tech)
  const isCurrentlyVisible = displayedKeys.includes(found)
  
  // 如果不在当前显示的列表中，先展开列表
  if (!isCurrentlyVisible && !matchExpanded.value) {
    matchExpanded.value = true
    // 等待DOM更新后再滚动
    nextTick(() => {
      setTimeout(() => {
        scrollToMatchItem(found)
      }, 100)
    })
  } else {
    scrollToMatchItem(found)
  }
}

function scrollToMatchItem(tech: string) {
  const id = sanitizeTechId(tech)
  // 等待一下确保DOM已更新
  setTimeout(() => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 高亮效果通过 isTechHighlighted 函数自动应用（基于 matchLocatorInput）
    }
  }, 50)
}
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

.openrank-line {
  margin: 0.25rem 0 0.75rem;
  color: #2d3748;
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

.chart-subtitle {
  margin: 0.25rem 0 0.75rem;
  color: #4a5568;
  font-size: 0.95rem;
}

.recent-topic-list {
  margin-top: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}
.recent-topic-list h4 {
  margin: 0 0 0.75rem;
  color: #2d3748;
}
.recent-topic-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1.6fr 0.7fr;
  gap: 0.75rem;
  padding: 0.5rem 0;
  align-items: center;
  border-top: 1px solid #e2e8f0;
}
.recent-topic-header {
  font-weight: 700;
  color: #4a5568;
  border-top: none;
}
.topic-label {
  font-weight: 600;
  color: #2d3748;
}
.repo-link {
  color: #2b6cb0;
  text-decoration: none;
  font-weight: 600;
}
.repo-link:hover {
  text-decoration: underline;
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

/* 匹配度列表样式优化 */
.match-inputs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  align-items: center;
}
.match-inputs .search-input {
  flex: 1;
  max-width: 400px;
}
.match-inputs .search-btn {
  padding: 1rem 1.5rem;
  white-space: nowrap;
}
.match-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}
.match-item {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  transition: background 0.2s ease, border-color 0.2s ease;
}
.match-item.highlight {
  background: #ebf8ff;
  border-color: #3182ce;
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
}
.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.tech-name {
  font-weight: 700;
  font-size: 1.1rem;
  color: #2d3748;
}
.match-score {
  font-weight: 600;
  color: #667eea;
  font-size: 1rem;
}
.match-detail {
  display: flex;
  gap: 1.5rem;
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 0.5rem;
}
.match-explanation {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #4a5568;
  font-style: italic;
}
.match-controls {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.expand-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #2b6cb0;
  background: #ebf8ff;
  border: 1px solid #bee3f8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.expand-btn:hover {
  background: #dbeafe;
  border-color: #90cdf4;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

/* 进度条样式 */
.progress-bar-container {
  width: 300px;
  height: 10px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  margin: 0 auto 1.5rem;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 5px;
  transition: width 0.3s ease-out;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.7);
}

.progress-text {
  font-size: 1.1rem;
  font-weight: 500;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.progress-pct {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-left: 5px;
}
</style>
