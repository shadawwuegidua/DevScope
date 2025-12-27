<template>
  <div
    ref="chartRef"
    :style="{ width: (width || 640) + 'px', height: (height || 400) + 'px' }"
  />
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, computed } from 'vue'
import * as echarts from 'echarts'

/**
 * GravityGraph.vue
 * 使用 ECharts 的 force 布局渲染开发者-技术关系引力图。
 * 要求：
 * - 使用力导向布局（series: 'graph', layout: 'force'）
 * - 节点距离根据 tech_tendency 概率反比例计算：L = (1 - P) * 500
 * - 中心节点显示开发者头像
 * - 周围节点可点击交互（向外触发 node-click 事件）
 */

type TechItem = {
  category: string
  probability: number // 0 ~ 1
  explanation?: string
}

const props = defineProps<{
  username: string
  avatarUrl?: string | null
  techTendency: TechItem[]
  width?: number
  height?: number
}>()

const emit = defineEmits<{
  (e: 'node-click', payload: { category: string; probability: number }): void
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const safeWidth = computed(() => props.width ?? 640)
const safeHeight = computed(() => props.height ?? 400)

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  renderOption()
  chart.on('click', params => {
    // 只响应技术节点点击（排除中心节点）
    const data = params?.data as any
    if (data && data.type === 'tech' && typeof data.category === 'string') {
      emit('node-click', {
        category: data.category,
        probability: Number(data.probability ?? 0)
      })
    }
  })
}

function disposeChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

function clampP(p: number): number {
  if (Number.isNaN(p)) return 0
  return Math.max(0, Math.min(1, p))
}

// 辅助函数：简单的颜色变亮
function lightenColor(color: string, percent: number): string {
  // 这里简单处理，实际可以使用更复杂的颜色库
  // 如果是 hex
  if (color.startsWith('#')) {
    // 简单返回原色，或者引入 tinycolor2 等库
    return color
  }
  return color
}

function computeEdgeLength(p: number): number {
  // 规范要求：L = (1 - P) * 500
  const P = clampP(p)
  return (1 - P) * 500
}

function renderOption() {
  if (!chart) {
    console.warn('GravityGraph: chart实例不存在')
    return
  }

  console.log('GravityGraph: 开始渲染，techTendency:', props.techTendency)

  // 构建中心节点（开发者头像）
  const centerNode = {
    id: 'center',
    name: props.username,
    type: 'center',
    symbol: props.avatarUrl ? `image://${props.avatarUrl}` : 'circle',
    symbolSize: 100,
    fixed: true,
    x: safeWidth.value / 2,
    y: safeHeight.value / 2,
    label: {
      show: true,
      position: 'bottom',
      fontSize: 16,
      fontWeight: 'bold',
      color: '#333'
    },
    itemStyle: {
      shadowBlur: 20,
      shadowColor: 'rgba(0, 0, 0, 0.3)',
      borderColor: '#fff',
      borderWidth: 4
    }
  }

  // 构建技术节点与边
  const techNodes: any[] = []
  const links: any[] = []
  
  // 漂亮的配色方案
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', 
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
  ]

  if (!props.techTendency || props.techTendency.length === 0) {
    console.warn('GravityGraph: techTendency为空')
    chart.setOption({
      title: {
        text: '暂无技术倾向数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#999' }
      }
    })
    return
  }

  props.techTendency.forEach((item, index) => {
    const p = clampP(item.probability)
    // 调整距离计算，让概率高的更近
    const length = (1 - p) * 300 + 50 

    const nodeId = `tech:${item.category}`
    const color = colors[index % colors.length]
    
    techNodes.push({
      id: nodeId,
      name: item.category,
      type: 'tech',
      category: item.category,
      probability: p,
      symbol: 'circle',
      // 根据概率调整大小: 40 ~ 90
      symbolSize: 40 + p * 50,
      itemStyle: {
        color: {
          type: 'radial',
          x: 0.5,
          y: 0.5,
          r: 0.5,
          colorStops: [
            { offset: 0, color: lightenColor(color, 20) },
            { offset: 1, color: color }
          ]
        },
        shadowBlur: 10,
        shadowColor: color
      },
      label: {
        show: true,
        formatter: '{b}',
        fontSize: 12 + p * 4,
        color: '#fff',
        textBorderColor: color,
        textBorderWidth: 2
      }
    })

    links.push({
      source: 'center',
      target: nodeId,
      value: length,
      lineStyle: {
        width: 1 + p * 4,
        curveness: 0.1,
        opacity: 0.6,
        color: color
      }
    })
  })

  const option: echarts.EChartsOption = {
    backgroundColor: '#f8f9fa', // 淡灰色背景
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    tooltip: {
      show: true,
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: (params: any) => {
        if (params?.data?.type === 'tech') {
          const c = params.data.category
          const p = Number(params.data.probability) || 0
          return `<div style="font-weight:bold">${c}</div><div>相关度: ${(p * 100).toFixed(1)}%</div>`
        }
        return `<div style="font-weight:bold">${props.username}</div>`
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        focusNodeAdjacency: true,
        data: [centerNode, ...techNodes],
        links,
        force: {
          edgeLength: [50, 400],
          repulsion: 1500,
          gravity: 0.05,
          layoutAnimation: true
        }
      }
    ]
  }

  console.log('GravityGraph: 节点数量:', techNodes.length, '边数量:', links.length)
  chart.setOption(option, true)
  console.log('GravityGraph: 图表配置已应用')
}

onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  disposeChart()
})

watch(
  () => [props.username, props.avatarUrl, props.techTendency, safeWidth.value, safeHeight.value],
  () => {
    if (chart) {
      chart.resize()
      renderOption()
    }
  },
  { deep: true }
)
</script>

<style scoped>
/* 容器由行内样式控制尺寸，此处无需额外样式 */
</style>
