<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'
import ResizeObserveChartContainer from '@/commomComponents/ResizeObserveChartContainer.vue'

interface Props {
  maxValue: number
  value: number
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  color: '#409eff'
})

const barContainer = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

const drawBar = (newWidth = 200,newHeight = 20) => {
  if (!barContainer.value) return

  // 清除之前的内容
  barContainer.value.innerHTML = ''

  // 获取容器宽度
  const containerWidth = newWidth
  const containerHeight = newHeight

  // 创建 SVG
  const svg = d3.select(barContainer.value)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)

  // 计算比例
  const scale = d3.scaleLinear()
    .domain([0, props.maxValue])
    .range([0, containerWidth])

  // 绘制背景条
  svg.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', containerWidth)
    .attr('height', containerHeight)
    .attr('fill', '#ebeef5')
    .attr('rx', 3)
    .attr('ry', 3)

  // 绘制数值条
  svg.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', scale(props.value))
    .attr('height', containerHeight)
    .attr('fill', props.color)
    .attr('rx', 3)
    .attr('ry', 3)
}

// 监听属性变化
watch([() => props.maxValue, () => props.value], drawBar)

// 组件挂载后绘制
onMounted(drawBar)

function onSizeChanged(hv){
  drawBar(hv.width)
}
</script>

<template>
  <ResizeObserveChartContainer @sizeChanged="onSizeChanged">
    <div ref="barContainer" class="bar-container" />
  </ResizeObserveChartContainer>

</template>

<style scoped lang="scss">
.bar-container {
  width: 100%;
  height: 100%;
}
</style>
