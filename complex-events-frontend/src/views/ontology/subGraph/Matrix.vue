<template>
  <div>
    <ResizeObserveChartContainer @sizeChanged="onSizeChanged" ref="resizeContainerRef">
      <svg ref="matrixSvgRef" width="500" height="500"></svg>
    </ResizeObserveChartContainer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, useTemplateRef, watch } from 'vue'
import * as d3 from 'd3'
import { Node } from '@/views/ontology/graphManage/graph'
import ResizeObserveChartContainer from '@/commomComponents/ResizeObserveChartContainer.vue'

const { adjacencyMatrix, nodesData } = defineProps<{
  adjacencyMatrix: {
    col: number[]
    data: number[]
    row: number[]
    shape: number[]
  }
  nodesData: Node[]
}>()

// 使用ref获取DOM元素
const matrixSvg = useTemplateRef('matrixSvgRef')
const resizeContainer = useTemplateRef('resizeContainerRef')
const onSizeChanged = (hv) => {
  update()
}
const update = () => {
  if (adjacencyMatrix && adjacencyMatrix.shape && nodesData?.length > 0) {
    // 清空画布
    d3.select(matrixSvg.value).selectAll('*').remove()
    drawMatrix()
  } else {
    console.log('no data while draw matrix')
  }
}

function generateDrawData() {
  const result = adjacencyMatrix.data.map((value, index) => ({
    value,
    row: adjacencyMatrix.row[index],
    col: adjacencyMatrix.col[index],
  }))

  return result
}

const drawMatrix = () => {
  // 方阵，长宽一样
  const size = Math.min(resizeContainer.value.width, resizeContainer.value.height)
  console.log('size', size)
  const svg = d3
    .select(matrixSvg.value)
    .attr('width', size)
    .attr('height', size)
    // 垂直方向上稍微下移使其重心下移
    .attr('transform', `translate(0, ${(resizeContainer.value.height - size) / 4})`)

  // 计算行列数
  const [rows, cols] = adjacencyMatrix.shape
  const cellSize = size / Math.max(rows, cols)

  // 构建完整矩阵数据
  const matrixData = []
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      matrixData.push({ row: i, col: j, value: 0 }) // 默认值为0
    }
  }

  // 填充实际数据
  adjacencyMatrix.data.forEach((value, index) => {
    const row = adjacencyMatrix.row[index]
    const col = adjacencyMatrix.col[index]
    const idx = row * cols + col
    matrixData[idx].value = value
  })
  // 添加网格线
  svg
    .append('g')
    .attr('class','horizon-lines')
    .selectAll('.grid-line')
    .data(d3.range(rows + 1))
    .enter()
    .append('line')
    .attr('class', 'grid-line')
    .attr('x1', 0)
    .attr('y1', (d) => d * cellSize)
    .attr('x2', size)
    .attr('y2', (d) => d * cellSize)
    .style('stroke', '#ccc')
    .style('stroke-width', 0.5)

  // 修改垂直网格线的选择器类名
  svg
    .append('g')
    .attr('class','vertical-lines')
    .selectAll('.grid-line-vertical')
    .data(d3.range(cols + 1))
    .enter()
    .append('line')
    .attr('class', 'grid-line-vertical') // 改为不同的类名
    .attr('x1', (d) => d * cellSize)
    .attr('y1', 0)
    .attr('x2', (d) => d * cellSize)
    .attr('y2', size)
    .style('stroke', '#ccc')
    .style('stroke-width', 0.5)

  // 更新颜色映射以包含0值
  const color = d3
    .scaleLinear()
    .domain([0, d3.max(adjacencyMatrix.data)]) // 从0开始
    .range(['white', 'steelblue'])

  // 绘制对角线填充
  svg
    .append('g')
    .attr('class', 'diagonal-cells-group')
    .selectAll('.diagonal-cell')
    .data(
      () => {
        const result = []
        for (let i = 0; i < adjacencyMatrix.shape[0]; i++) {
          result.push({
            value: 1,
            row: i,
            col: i,
          })
        }
        return result
      } // 填充对角线元素
    )
    .enter()
    .append('rect')
    .attr('class', 'diagonal-cell fill')
    .attr('x', (d) => d.col * cellSize)
    .attr('y', (d) => d.row * cellSize)
    .attr('width', cellSize)
    .attr('height', cellSize)
    .style('fill', (d) => color(d.value))
    .style('padding', '10 10 10 10')
    .append('title')
    .text((d, i) =>
        d.value != 0 ? `${formatNode(nodesData[d.row])}->${formatNode(nodesData[d.col])}` : '',)


  // 绘制其他位置（非对角线）
  svg
    .append('g')
    .attr('class','cells-group')
    .selectAll('.cell')
    .data(generateDrawData())
    .enter()
    .append('rect')
    .attr('class', 'cell fill')
    .attr('x', (d) => d.col * cellSize)
    .attr('y', (d) => d.row * cellSize)
    .attr('width', cellSize)
    .attr('height', cellSize)
    .style('fill', (d) => color(d.value))
    .style('padding', '10 10 10 10')
    .append('title')
    .text((d, i) =>
      d.value != 0 ? `${formatNode(nodesData[d.row])}->${formatNode(nodesData[d.col])}` : '',
    )
}

function formatNode(node: Node) {
  return `${node.name}：${node.group}`
}

watch(
  () => [adjacencyMatrix, nodesData],
  (newVal) => {
    update()
  },
  { deep: true },
)
</script>

<style scoped>
.cell {
  stroke: #666;
  stroke-width: 1px;
}

.fill {
  fill: steelblue;
}
</style>
