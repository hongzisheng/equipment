<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, useTemplateRef, watch } from 'vue'
import * as d3 from 'd3'
import { REPORT_DATE_COUNT_JSON_API } from '@/api/statisticApi'
import { useMapStore } from '@/stores/mapStore'
import { storeToRefs } from 'pinia'

const chartContainer = useTemplateRef('chartContainer')
let resizeObserver: ResizeObserver | null = null
let currentWidth = 0
let currentHeight = 0
// 过渡动画的时间during
const timeout = 750

// D3相关引用
const state = reactive({
  // 画布,svg-g
  svg: d3.Selection<SVGElement, unknown, SVGElement, any>,
  // x 轴比例尺
  xScale: null,
  // y 轴比例尺
  yScale: null,
  // x 轴
  xAxis: null,
  // y 轴
  yAxis: null,
  // 画布宽度
  width: 0,
  // 画布高度
  height: 0,
})
let minWidth = null
// 响应式画布边界
const margin = computed(() => {
  return {
    top: state.height * 0.1,
    right: state.width * 0.05,
    bottom: state.height * 0.1,
    left: state.width * 0.05,
  }
})
// x轴的高度
const XAxisHeight = computed(() => {
  return state.height * 0.2
})
// 响应式内容宽度
const containerWidth = computed(() => {
  return state.width - margin.value.left - margin.value.right
})

// 响应式内容高度
const containerHeight = computed(() => {
  return state.height - margin.value.top - margin.value.bottom - XAxisHeight.value
})
const props = defineProps<{
  data?: {
    // 绘制的日期，x 轴
    _id: string
    // 日期的数量，y 轴
    count: number
  }[]
  // 是否隐藏x轴
  hiddenXAxis?: boolean
  // 是否隐藏y轴
  hiddenYAxis?: boolean
}>()
onMounted(async () => {
  const chartContainerDOM = chartContainer.value
  if (chartContainerDOM) {
    // 创建 ResizeObserver 监听容器尺寸变化
    resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect
        // 避免无限循环：只有当尺寸真正改变时才重绘
        if (Math.abs(width - currentWidth) > 1 || Math.abs(height - currentHeight) > 1) {
          state.width = width
          state.height = height
          drawBarChart()
        }
      }
    })

    resizeObserver.observe(chartContainerDOM)
    // 等待数据加载完成，一会还要根据数据长度判断是否需要添加滚动事件
    await loadData()

    if (data.length > 5) {
      // 数据条多于5条才添加滚动监听时间，否则没有滚动
      // 在 mousewheel 事件中调用
      chartContainerDOM.addEventListener('mousewheel', (e: WheelEvent) => {
        e.preventDefault()
        // 屏蔽柱状图事件
        removeBarEvent()

        if (minWidth == null) {
          // 记录第一次的宽度为最小宽度
          minWidth = state.width
        }

        const clampedDeltaY = Math.max(-100, Math.min(100, e.deltaY))
        const scale = 1 - clampedDeltaY * 0.005

        if (state.width * scale <= minWidth * 10) {
          if (state.width * scale < minWidth) {
            state.width = minWidth
          } else {
            state.width = state.width * scale
          }

          // 更新SVG的宽度以适应缩放
          d3.select(chartContainerDOM).select('svg').attr('width', state.width)

          // 移除之前的高亮区域
          removeHighlightDateRange()
          // 更新图表元素
          updateChartOnZoom()

          // 在过渡动画结束后恢复事件
          setTimeout(() => {
            /**
             * 更新高亮的区域，相当于重新绘制
             * 另一种解决方案是可以使用更新绘制的话需要重新计算坐标，但是更新绘制的话可以有动画跟踪
             */
            highlightDateRange(dateRange.value?.[0] || null, dateRange.value?.[1] || null)
            addBarEvent()
            // 等动画结束了再更新ticks的位置
            // updateXAxis()
          }, timeout) // 与过渡动画时间保持一致
        } else {
          // 如果不满足缩放条件，立即恢复事件
          addBarEvent()
        }
      })
    }
  }
})

onBeforeUnmount(() => {
  if (resizeObserver && chartContainer.value) {
    resizeObserver.unobserve(chartContainer.value)
  }
})
// 更新缩放
const updateChartOnZoom = () => {
  // 更新X轴比例尺范围
  state.xScale.range([0, containerWidth.value])

  // 更新坐标轴
  state.xAxis
    .transition()
    .duration(timeout)
    .call(
      d3.axisBottom(state.xScale).tickValues(
        data.map((d) => d._id).filter((d, i) => i % 6 === 0), // 每隔6个显示一个
      ),
    )
  updateXAxis()
  // 更新柱状图
  state.svg
    .selectAll('.bar')
    .transition()
    .duration(timeout)
    .attr('x', (d: any) => state.xScale(d._id)!)
    .attr('width', state.xScale.bandwidth())
}
// 随机数据
let data = []
const loadData = async () => {
  try {
    data = props.data ?? (await d3.json(REPORT_DATE_COUNT_JSON_API))
    // 数据加载完成后重新绘制图表
    if (chartContainer.value) {
      const { width, height } = chartContainer.value.getBoundingClientRect()
      state.width = width
      state.height = height
      drawBarChart()
    }
  } catch (error) {
    console.error('Failed to load data:', error)
  }
}
const drawBarChart = () => {
  // 如果尺寸无效，不绘制图表
  if (containerWidth.value <= 0 || containerHeight.value <= 0) return

  // 清除之前的内容
  d3.select(chartContainer.value).select('svg').remove()

  // 创建 SVG 容器 - 使用固定尺寸而不是百分比
  const svg = d3
    .select(chartContainer.value)
    .append('svg')
    .attr('width', state.width)
    .attr('height', state.height)
    .style('display', 'block') // 避免 inline-block 导致的额外空间

  // 创建图表组
  state.svg = svg
    .append('g')
    .attr('transform', `translate(${margin.value.left},${margin.value.top})`)

  // X 轴比例尺
  state.xScale = d3
    .scaleBand()
    .domain(data.map((d) => d._id))
    .range([0, containerWidth.value])
    .padding(0.1)
  // Y 轴比例尺
  state.yScale = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => d.count)!])
    .range([containerHeight.value, 0])
  if (!props.hiddenXAxis) {
    // 不隐藏x轴
    // 创建 X 轴
    state.xAxis = state.svg
      .append('g')
      .attr('transform', `translate(0,${containerHeight.value})`)
      .attr('height', XAxisHeight.value)
      .call(
        d3
          .axisBottom(state.xScale)
          .tickValues(data.map((d) => d._id).filter((d, i) => i % 6 === 0)),
      )
    updateXAxis()
  }
  if (!props.hiddenYAxis) {
    // 不隐藏 y 轴
    // 创建 Y 轴
    state.yAxis = state.svg
      .append('g')
      .call(d3.axisLeft(state.yScale).ticks(5))
      .selectAll('text')
      .style('font-size', '12px')
  }

  // 绘制柱状图
  state.svg
    .selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d) => state.xScale(d._id)!)
    .attr('y', (d) => state.yScale(d.count))
    .attr('width', state.xScale.bandwidth())
    .attr('height', (d) => Math.max(0, containerHeight.value - state.yScale(d.count))) // 确保高度不为负
    .attr('fill', 'lightskyblue')
  addBarEvent()

  // 添加数值标签（可选）
  // g.selectAll('.label')
  //   .data(data)
  //   .enter()
  //   .append('text')
  //   .attr('class', 'label')
  //   .attr('x', (d) => x(d._id)! + x.bandwidth() / 2)
  //   .attr('y', (d) => y(d.count) - 5)
  //   .attr('text-anchor', 'middle')
  //   .text((d) => d.count)
  //   .style('font-size', '12px')
  //   .style('fill', 'black')
}

// 更新x轴的一些细节
function updateXAxis() {
  // 单独设置x轴的指示竖线，默认是x轴高度的一半，最大是6
  state.xAxis
    .transition()
    .duration(timeout)
    .selectAll('line')
    .attr('y2', XAxisHeight.value / 2 > 6 ? 6 : XAxisHeight.value / 2)

  // 单独设置文本样式
  state.xAxis
    .transition()
    .duration(timeout)
    .selectAll('text')
    .attr('y', XAxisHeight.value / 2 > 6 + 1 ? 6 + 1 : XAxisHeight.value / 2 + 1) // 控制ticks文本距离轴线的距离,最大是竖线最大高度6+1
    .style('font-size', 'clamp(5px, 1vw, 14px);')
}

/**
 * 移除柱状图事件
 */
const removeBarEvent = () => {
  state.svg.selectAll('.bar').on('mouseover', null).on('mouseout', null).on('click', null)
}

/**
 * 添加柱状图交互事件
 */
const addBarEvent = () => {
  // 添加鼠标交互事件
  state.svg
    .selectAll('.bar')
    .on('mouseover', function (event, d) {
      d3.select(this).transition().duration(200).attr('fill', 'orange')

      // 可选：添加数值提示
      const tooltip = state.svg
        .append('text')
        .attr('class', 'tooltip')
        .attr('x', state.xScale(d._id)! + state.xScale.bandwidth() / 2)
        .attr('y', state.yScale(d.count) - 1)
        .attr('text-anchor', 'middle')
        .text(d.count)
        .style('font-size', '10px')
        .style('fill', 'black')
    })
    .on('mouseout', function () {
      d3.select(this).transition().duration(200).attr('fill', 'lightskyblue')

      // 移除提示
      state.svg.select('.tooltip').remove()
    })
    .on('click', function (event, d) {
      // 2023-12
      // 解析月份字符串 (格式: YYYY-MM)
      const [year, month] = d._id.split('-').map(Number)

      // 生成月初日期 (1号)
      const startDate = `${d._id}-01`

      // 生成月末日期
      // 创建下个月的第一天，然后减去一天得到本月最后一天
      const lastDay = new Date(year, month, 0) // month是0索引，所以直接传入即可
      const endDate = `${d._id}-${String(lastDay.getDate()).padStart(2, '0')}`

      const mapStore = useMapStore()
      const { dateRangePicker } = storeToRefs(mapStore)
      dateRangePicker.value = [startDate, endDate]
    })
}
/**
 * 高亮指定日期范围，可以高亮一部分柱状图，也可以在柱状图上交互
 * @param startDateStr 开始日期
 * @param endDateStr 结束日期
 */
const highlightDateRange = (startDateStr: string | null, endDateStr: string | null) => {
  if (!chartContainer.value) return

  const g = state.svg

  // 如果没有日期范围，直接返回
  if (!startDateStr || !endDateStr) {
    return
  }

  // 解析日期
  const startDate = new Date(startDateStr)
  const endDate = new Date(endDateStr)

  // 获取涉及的月份
  const startMonth = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}`
  const endMonth = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}`

  // 高亮涉及的柱子并添加精确覆盖层
  data.forEach((d: any) => {
    const barMonth = d._id
    const barDate = new Date(barMonth + '-01')
    const startBarDate = new Date(startMonth + '-01')
    const endBarDate = new Date(endMonth + '-01')

    // 检查柱子是否在日期范围内
    if (barDate >= startBarDate && barDate <= endBarDate) {
      // 改变柱子颜色
      g.selectAll('.bar').filter((item: any) => item._id === barMonth)
      // .attr('fill', 'orange')

      // 计算该月的天数
      const year = barDate.getFullYear()
      const month = barDate.getMonth()
      const totalDays = new Date(year, month + 1, 0).getDate()

      let startDayRatio = 0
      let endDayRatio = 1

      // 如果是起始月
      if (barMonth === startMonth) {
        startDayRatio = (startDate.getDate() - 1) / totalDays
      }

      // 如果是结束月
      if (barMonth === endMonth) {
        endDayRatio = endDate.getDate() / totalDays
      }

      // 计算高亮区域
      const xPosition = state.xScale(barMonth)!
      const bandwidth = state.xScale.bandwidth()
      const highlightStart = xPosition + bandwidth * startDayRatio
      const highlightWidth = bandwidth * (endDayRatio - startDayRatio)

      // 添加高亮覆盖层
      g.append('rect')
        .attr('class', 'highlight-overlay')
        .attr('x', highlightStart)
        .attr('y', state.yScale(d.count)) // 从顶部开始
        .attr('width', highlightWidth)
        .attr('height', Math.max(0, containerHeight.value - state.yScale(d.count))) // 到底部
        .attr('fill', 'orange')
        .attr('pointer-events', 'none')
    }
  })
}
/**
 * 移除高亮区域
 */
const removeHighlightDateRange = () => {
  const g = state.svg
  // 移除之前的高亮
  g.selectAll('.highlight-overlay').remove()
  g.selectAll('.bar').attr('fill', 'lightskyblue') // 重置所有柱子颜色
}

// 监听日期范围变化
const mapStore = useMapStore()
const dateRange = computed(() => mapStore.dateRangePicker)
watch(dateRange, () => {
  if (chartContainer.value) {
    // 移除之前的高亮区域
    removeHighlightDateRange()
    highlightDateRange(dateRange.value?.[0] || null, dateRange.value?.[1] || null)
  }
})
</script>

<template>
  <div ref="chartContainer" style="width: 100%; height: 100%"></div>
</template>

<style scoped lang="scss">
.bar {
  transition: fill 0.3s;
}

.bar:hover {
  fill: orange;
}
</style>
