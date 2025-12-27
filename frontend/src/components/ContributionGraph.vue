<template>
  <div ref="chartRef" class="contribution-chart"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  timestamps: string[]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  renderChart()
  
  window.addEventListener('resize', () => chart?.resize())
}

function renderChart() {
  if (!chart) return

  // Process timestamps to get daily counts
  const dailyCounts: Record<string, number> = {}
  const now = new Date()
  const oneYearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
  
  // Initialize all days in the last year with 0
  for (let d = new Date(oneYearAgo); d <= now; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0]
    dailyCounts[dateStr] = 0
  }

  props.timestamps.forEach(ts => {
    const dateStr = ts.split('T')[0]
    if (dailyCounts[dateStr] !== undefined) {
      dailyCounts[dateStr]++
    }
  })

  const data = Object.entries(dailyCounts).map(([date, count]) => [date, count])
  const maxCount = Math.max(...Object.values(dailyCounts), 5) // At least 5 for visual scale

  const option = {
    tooltip: {
      position: 'top',
      formatter: function (p: any) {
        const format = echarts.format.formatTime('yyyy-MM-dd', p.data[0]);
        return `${format}: ${p.data[1]} contributions`;
      }
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
      }
    },
    calendar: {
      top: 30,
      left: 30,
      right: 30,
      cellSize: ['auto', 13],
      range: [oneYearAgo.toISOString().split('T')[0], now.toISOString().split('T')[0]],
      itemStyle: {
        borderWidth: 0.5
      },
      yearLabel: { show: false },
      dayLabel: { firstDay: 1, nameMap: 'en' },
      monthLabel: { nameMap: 'en' }
    },
    series: {
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: data
    }
  }

  chart.setOption(option)
}

watch(() => props.timestamps, () => {
  if (chart) {
    renderChart()
  } else {
    initChart()
  }
})

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})
</script>

<style scoped>
.contribution-chart {
  width: 100%;
  height: 200px;
}
</style>
