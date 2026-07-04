<script setup lang="ts">
import { ref, onMounted, watch, useTemplateRef } from 'vue'
import * as d3 from 'd3'
import ResizeObserveChartContainer from '@/commomComponents/ResizeObserveChartContainer.vue'
import { SubGraphEmbedding } from '@/views/ontology/subGraph/index'
import { Node } from '@/views/ontology/graphManage/graph'

// 定义数据类型
interface EmbeddingPoint {
  x: number
  y: number
  label: string
}

// 响应式数据
const svgRef = useTemplateRef('svgRef')
const containerWidth = ref(0)
const containerHeight = ref(0)

const points = ref<EmbeddingPoint[]>([])

const { embeddings, nodesData, activeName } = defineProps<{
  embeddings: SubGraphEmbedding[]
  nodesData: Node[]
  activeName: string
}>()

// 获取数据
const data = (): EmbeddingPoint[] => {
  return embeddings.map((eb, index) => {
    return {
      x: eb.reduced_embedding[0],
      y: eb.reduced_embedding[1],
      label: eb.name,
    }
  })
}
// 添加hash函数，根据字符串生成固定数值
const hashString = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // 转换为32位整数
  }
  return Math.abs(hash)
}

// 根据label生成固定颜色
const getColorByLabel = (label: string): string => {
  const hash = hashString(label)
  return d3.interpolateRainbow((hash % 1000) / 1000)
}
// 绘制散点图
const drawEmbedding = () => {
  if (!svgRef.value) {
    console.log('kong', svgRef)
    return
  }

  // 清空之前的svg内容
  d3.select(svgRef.value).selectAll('*').remove()

  // 使用容器提供的尺寸而不是固定尺寸
  const width = containerWidth.value
  const height = containerHeight.value
  const margin = { top: 40, right: 40, bottom: 60, left: 60 }

  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom

  const svg = d3.select(svgRef.value).attr('width', width).attr('height', height)
  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  // 数据范围计算
  const xExtent = d3.extent(points.value, (d) => d.x) as [number, number]
  const yExtent = d3.extent(points.value, (d) => d.y) as [number, number]

  // 添加一些边距
  const xRange: [number, number] = [xExtent[0] - 0.1, xExtent[1] + 0.1]
  const yRange: [number, number] = [yExtent[0] - 0.1, yExtent[1] + 0.1]

  // 比例尺
  const xScale = d3.scaleLinear().domain(xRange).range([0, innerWidth])

  const yScale = d3.scaleLinear().domain(yRange).range([innerHeight, 0])

  // 添加坐标轴
  const xAxis = d3.axisBottom(xScale)
  const yAxis = d3.axisLeft(yScale)

  g.append('g').attr('class', 'x-axis').attr('transform', `translate(0,${innerHeight})`).call(xAxis)

  g.append('g').attr('class', 'y-axis').call(yAxis)

  // 绘制点
  const dots = g
    .selectAll('.dot')
    .data(points.value)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('cx', (d) => xScale(d.x))
    .attr('cy', (d) => yScale(d.y))
    .attr('r', 8)
    .style('fill', (d) => getColorByLabel(d.label))
    .style('stroke', '#fff')
    .style('stroke-width', 1.5)

  // 添加聚光灯效果
  dots
    .filter((d) => d.label === activeName)
    .raise() // 将高亮的点移到最前面
    .attr('r', 12) // 增大点半径
    .style('stroke', (d) => getColorByLabel(d.label))
    .style('stroke-width', 3) // 更粗的边框
    .style('filter', 'url(#glow)') // 添加发光效果

  // 为非高亮点降低透明度
  dots.filter((d) => d.label !== activeName).style('opacity', 0.5)


  // 添加滤镜定义用于发光效果
  const defs = svg.append('defs')
  const filter = defs
    .append('filter')
    .attr('id', 'glow')
    .attr('x', '-50%')
    .attr('y', '-50%')
    .attr('width', '200%')
    .attr('height', '200%')

  filter.append('feGaussianBlur').attr('stdDeviation', 3).attr('result', 'coloredBlur')

  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')
}

// 初始化数据
const initializeData = () => {
  // 在实际应用中，这里应该通过props或API获取数据
  points.value = data()
  drawEmbedding()
}

// 监听数据变化
watch(
  () => [embeddings, nodesData, activeName],
  () => {
    initializeData()
  },
  { deep: true },
)

// 组件挂载时初始化
onMounted(() => {
  initializeData()
})
// 处理尺寸变化
const onSizeChanged = (hv: { height: number; width: number }) => {
  containerWidth.value = hv.width
  containerHeight.value = hv.height
  // 使用容器提供的尺寸进行绘制
  initializeData()
}
</script>

<template>
  <div>
    <ResizeObserveChartContainer @sizeChanged="onSizeChanged">
      <template #default>
        <div class="embedding-container">
          <svg ref="svgRef"></svg>
        </div>
      </template>
    </ResizeObserveChartContainer>
  </div>
</template>

<style scoped lang="scss">
.embedding-container {
  padding: 20px;

  h2 {
    text-align: center;
    margin-bottom: 20px;
    color: #333;
  }

  .loading {
    text-align: center;
    padding: 50px;
    font-size: 18px;
    color: #666;
  }

  .chart-container {
    display: flex;
    justify-content: center;
    align-items: center;

    svg {
      border: 1px solid #ddd;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
  }
}

// D3样式
.x-axis,
.y-axis {
  .domain,
  .tick line {
    stroke: #999;
  }

  .tick text {
    fill: #666;
    font-size: 12px;
  }
}

.x-axis-label,
.y-axis-label {
  fill: #333;
  font-size: 14px;
  font-weight: bold;
}

.legend {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 10px;

  text {
    font-family: sans-serif;
  }
}
</style>
