<template>
  <div class="container">
    <h1>D3.js 时间轴与框选功能 (Vue 3 Composition API Demo)</h1>
    <div ref="timelineContainer" id="timeline-container"></div>

    <div id="selection-info">
      <p>框选时间范围:</p>
      <p v-if="selectionStart && selectionEnd">
        从 <strong>{{ formatDate(selectionStart) }}</strong> 到
        <strong>{{ formatDate(selectionEnd) }}</strong>
      </p>
      <p v-else>请在时间轴上拖拽以选择时间范围</p>
      <button id="clear-btn" @click="clearSelection">清除选择</button>
    </div>

    <div class="instructions">
      <p>操作说明：在时间轴上按下鼠标左键并拖拽以框选时间范围</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount, reactive } from 'vue'
import * as d3 from 'd3'

// 响应式数据
const timelineContainer = ref(null)
const selectionStart = ref(null)
const selectionEnd = ref(null)
const selectionWidth = ref(null)

interface TimelineState {
  svg:  d3.Selection<SVGSVGElement, unknown, HTMLElement, any>;
  xScale: d3.ScaleTime<number, number>;
  xAxis: d3.Axis<d3.NumberValue>;
  brushRect: d3.Selection<SVGRectElement, unknown, SVGElement, any>;
  width: number;
  ticksCount: number;
  height: number;
  margin: { top: number; right: number; bottom: number; left: number };
}

// D3相关引用
const state: TimelineState = reactive({
  svg: null,
  xScale: null,
  xAxis: null,
  brushRect: null,
  width: 0,
  ticksCount: 10,
  height: 300,
  margin: { top: 20, right: 30, bottom: 20, left: 40 },
})

// 初始化时间轴
const initTimeline = () => {
  const container = timelineContainer.value
  if (!container) return

  // 清空容器
  container.innerHTML = ''

  // 计算尺寸
  state.width = container.clientWidth - state.margin.left - state.margin.right

  // 创建SVG时设置固定高度但允许宽度变化
  state.svg = d3
    .select(container)
    .append('svg')
    .attr('width', state.width + state.margin.left + state.margin.right)
    .attr('height', state.height + state.margin.top + state.margin.bottom)
    .style('min-width', '100%') // 确保SVG至少占满容器宽度
    .append('g')
    .attr('transform', `translate(${state.margin.left},${state.margin.top - 100})`)

  // 定义时间范围 (示例：过去24小时)
  const now = new Date()
  const startTime = new Date(now.getTime() - 100 * 24 * 60 * 60 * 1000)

  // 创建X轴比例尺
  state.xScale = d3.scaleTime().domain([startTime, now]).range([0, state.width])

  // 创建X轴时添加倾斜效果
  state.xAxis = d3
    .axisBottom(state.xScale)
    .tickFormat(d3.timeFormat('%Y-%m-%d'))
    .scale(state.xScale)
    .ticks(Math.max(5, Math.min(100, state.width / 50)))
    .tickSize(6)
    .tickPadding(8)

  // 在调用axis后添加倾斜样式
  const xAxisGroup = state.svg
    .append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${state.height})`)
    .call(state.xAxis)

  // 添加倾斜效果
  xAxisGroup
    .selectAll('text')
    .style('text-anchor', 'end')
    .attr('dx', '-.8em')
    .attr('dy', '.15em')
    .attr('transform', 'rotate(-45)')

  // 添加brush覆盖层
  state.brushRect = state.svg
    .append('rect')
    .attr('class', 'brush-overlay')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', 0)
    .attr('height', state.height)
    .style('fill', 'lightblue')
    .style('opacity', 0.8)
    .style('display', 'none')



  // 添加事件监听
  addEventListeners()
}

// 添加事件监听器
const addEventListeners = () => {
  let isBrushing = false
  let startX = 0

  const container = timelineContainer.value

  container.addEventListener('mousedown', (e) => {
    isBrushing = true
    startX = e.offsetX - state.margin.left
    selectionStart.value = state.xScale.invert(startX)
    state.brushRect.attr('x', startX).attr('width', 0).style('display', 'block')
  })

  container.addEventListener('mousemove', (e) => {
    if (!isBrushing) return

    const currentX = e.offsetX - state.margin.left
    const minX = Math.min(startX, currentX)
    const width = Math.abs(currentX - startX)

    state.brushRect.attr('x', minX).attr('width', width)
  })

  container.addEventListener('mouseup', (e) => {
    if (!isBrushing) return
    isBrushing = false

    const endX = e.offsetX - state.margin.left
    selectionEnd.value = state.xScale.invert(endX)

    // 确保start < end
    if (selectionStart.value > selectionEnd.value) {
      ;[selectionStart.value, selectionEnd.value] = [selectionEnd.value, selectionStart.value]
    }
    selectionWidth.value = selectionEnd.value - selectionStart.value
  })

  container.addEventListener('mouseleave', () => {
    isBrushing = false
  })

  container.addEventListener('mousewheel', (e) => {
    e.preventDefault()

    const clampedDeltaY = Math.max(-100, Math.min(100, e.deltaY))
    const scale = 1 - clampedDeltaY * 0.005

    if (state.width * scale <= 25000 && state.width * scale >= 250) {
      state.width = state.width * scale
      state.xScale.range([0, state.width])

      // 更新SVG的宽度以适应缩放
      d3.select(container)
        .select('svg')
        .attr('width', state.width + state.margin.left + state.margin.right)

      // 更新选区矩形
      if (selectionStart.value && selectionEnd.value) {
        const newStartX = state.xScale(selectionStart.value)
        const newEndX = state.xScale(selectionEnd.value)
        const newWidth = Math.abs(newEndX - newStartX)

        state.brushRect
          .transition()
          .duration(750)
          .attr('x', Math.min(newStartX, newEndX))
          .attr('width', newWidth)
          .style('display', 'block')

      }

      // 更新坐标轴
      // 更新坐标轴配置
      state.xAxis
        .scale(state.xScale)
        .ticks(Math.max(5, Math.min(100, state.width / 50)))
        .tickSize(6)
        .tickPadding(8)

      // 更新坐标轴显示
      const xAxisGroup = state.svg.select('.axis').transition().duration(750).call(state.xAxis)

      // 重新应用倾斜效果
      xAxisGroup
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)')
    }
  })
}

// 清除选择
const clearSelection = () => {
  selectionStart.value = null
  selectionEnd.value = null
  state.brushRect.attr('width', 0).style('display', 'none')
}

// 格式化日期
const formatDate = (date) => {
  return d3.timeFormat('%Y-%m-%d %H:%M:%S')(date)
}

// 处理窗口大小调整
const handleResize = () => {
  initTimeline()
}

// 生命周期钩子
onMounted(() => {
  initTimeline()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.container {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
}

#timeline-container {
  width: 100%;
  height: 400px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 20px;
  position: relative;
  overflow-x: auto;
  background-color: #fafafa;
}

:deep(.axis) {
  font-size: 12px;
  // 设置坐标轴的文字不会被划词选中
  -webkit-user-select: none; /* Safari */
  -moz-user-select: none; /* Firefox */
  -ms-user-select: none; /* IE10+/Edge */
  user-select: none; /* 标准语法 */
  .path,
  .line {
    fill: none;
    stroke: #999;
    shape-rendering: crispEdges;
  }
}

.brush-overlay {
  fill: steelblue;
  opacity: 0.3;
}

#selection-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #eef;
  border-radius: 4px;
  text-align: center;
}

#selection-info p {
  margin: 5px 0;
  font-size: 16px;
}

#clear-btn {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

#clear-btn:hover {
  background-color: #ff5252;
}

.instructions {
  margin-top: 15px;
  font-size: 14px;
  color: #666;
  text-align: center;
}
</style>
