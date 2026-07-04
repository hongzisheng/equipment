<template>
<div>
    <el-botton @click="fetchData">
        {{ selectedRow.reportId }}
    </el-botton>
    <div ref="svgContainer" class="gmap-container"></div>
</div>
</template>
<script setup lang="ts">
import * as d3 from 'd3'
import { ForceNode, ForceEdge,formatEventLink} from '@/utils/gMapUtil'
import {computed, onMounted,reactive, ref,Ref} from 'vue'
import { OntologySystemData } from '@/views/ontology/ontologySystem'
import dataApi from '@/api/dataApi'
import { format } from 'echarts'

defineOptions({name:'GraphStructure'})

const props = defineProps({
    selectedItems: {
        type: Array<OntologySystemData>,
        default: () => [],
    },
})

let resizeObserver: ResizeObserver | null = null

const selectedRow = computed<OntologySystemData | ''>(() => {
    if (props.selectedItems && props.selectedItems.length > 0) {
        return props.selectedItems[0]
    }
    else {
        return ''
    }
})


const svgContainer = ref<HTMLElement | null>(null)
const state = reactive({
  width: 0,
  height: 0,
})
const data = ref<Ref<{ nodes: ForceNode[]; edges: ForceEdge[] }>>(null)

const drawForceGraph = (data: { nodes: ForceNode[]; edges: ForceEdge[] }) => {
  // 清空容器
  const container = svgContainer.value
  if (!container) return

  // 设置图形尺寸
  const width = container.clientWidth || 800
  const height = container.clientHeight || 600

  // 清空之前的图形
  container.innerHTML = ''

  // 创建SVG和缩放容器
  const svg = d3.select(container).append('svg').attr('width', width).attr('height', height)

  // 创建缩放行为
  const g = svg.append('g')

  const zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 10])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  // 应用缩放到SVG
  svg.call(zoom)

  // 创建力导向模拟器
  const simulation = d3
    .forceSimulation<ForceNode>(data.nodes)
    .force(
      'link',
      d3
        .forceLink<ForceNode, ForceEdge>(data.edges)
        .id((d) => d.nodeId)
        .distance(100),
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))

  // 创建连线
  const link = g // 注意：现在添加到g元素而不是svg
    .append('g')
    .selectAll('line')
    .data(data.edges)
    .enter()
    .append('line')
    .attr('stroke', getLinkColorByType)
    .attr('stroke-opacity', 0.3)
    .attr('stroke-width', 2)

  // 创建节点
  const node = g // 注意：现在添加到g元素而不是svg
    .append('g')
    .selectAll('circle')
    .data(data.nodes)
    .enter()
    .append('circle')
    .attr('r', 10)
    .attr('fill', getColorByType)

  // 添加节点标签
  const text = g // 注意：现在添加到g元素而不是svg
    .append('g')
    .selectAll('text')
    .data(data.nodes)
    .enter()
    .append('text')
    .text((d) => d.nodeName)
    .attr('font-size', 12)
    .attr('dx', 12)
    .attr('dy', 4)


  // 更新位置
  simulation.on('tick', () => {
      link
      .attr('x1', (d) => (d.source as any).x!)
      .attr('y1', (d) => (d.source as any).y!)
      .attr('x2', (d) => (d.target as any).x!)
      .attr('y2', (d) => (d.target as any).y!)

    node.attr('cx', (d) => d.x!).attr('cy', (d) => d.y!)
    text.attr('x', (d) => d.x!).attr('y', (d) => d.y!)
  });
  simulation.on('click',()=>{

  })
}

function getColorByType(d: ForceNode) {
    if (d.isShare){
        return '#61f4ff'
    }
  const colorMap: Record<string, string> = {
    mainEventName: '#ff0000',
    eventName: '#ff7f0e',
    person: '#808080',
    organization: '#808080',
    default: '#808080',
  }
  return colorMap[d.nodeType] || colorMap['default']
}

function getLinkColorByType(d: ForceEdge) {
  const colorMap: Record<string, string> = {
    eventLink: '#ff0000',
    otherLink: '#808080',
  }
  return d.highlight?colorMap['eventLink']:colorMap['otherLink']
}

async function fetchData(){
  const res = await dataApi.getEventLinkResult(selectedRow.value.reportId)
//   console.log("res.data",res.data)
  data.value=formatEventLink(res.data,selectedRow)
  console.log("data.value",data.value)
  const chartContainerDOM = svgContainer.value
  // 创建 ResizeObserver 监听容器尺寸变化
  resizeObserver = new ResizeObserver((entries) => {
    for (let entry of entries) {
      const { width, height } = entry.contentRect
      // 避免无限循环：只有当尺寸真正改变时才重绘
      if (Math.abs(width - state.width) > 1 || Math.abs(height - state.height) > 1) {
        state.width = width
        state.height = height
        drawForceGraph(data.value)
      }
    }
  })
  resizeObserver.observe(chartContainerDOM)
  drawForceGraph(data.value)
}

</script>
<style scoped>
.gmap-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
