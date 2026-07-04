<script setup lang="ts">
import { h, onMounted, reactive, Ref, ref } from 'vue'
import * as d3 from 'd3'
import { ForceNode, ForceEdge, gMapData } from '@/utils/gMapUtil'
import dataApi from '@/api/dataApi'

let resizeObserver: ResizeObserver | null = null

const svgContainer = ref<HTMLElement | null>(null)
const state = reactive({
  width: 0,
  height: 0,
})
const data = ref<Ref<{ nodes: ForceNode[]; edges: ForceEdge[] }>>(null)
onMounted(async () => {
  data.value = await gMapData()
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
})

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
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
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
    if (simulation.alpha() < 0.05) {
      simulation.stop();

      const finalNodes = simulation.nodes().map((d) => ({
        nodeId: d.nodeId,
        nodeName: d.nodeName,
        nodeType: d.nodeType,
        x: d.x,
        y: d.y,
        vx: d.vx,
        vy: d.vy,
        index: d.index
      }));
      dataApi.getClusterParams(finalNodes).then(cas => {
        console.log("cas", cas)
        drawBackgroundLayer(cas.data, g, 1113, 940)
      })


      console.log('布局稳定，节点最终坐标：', finalNodes);
    }
  });
}

function getColorByType(d: ForceNode) {
  const colorMap: Record<string, string> = {
    eventName: '#ff7f0e',
    person: '#2ca02c',
    organization: '#d62728',
    reportDate: '#9467bd',
    default: '#1f77b4',
  }
  return colorMap[d.nodeType] || colorMap['default']
}

function drawBackgroundLayer(
  cas: any[],
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  widthParam: number,
  heightParam: number
) {
  // defensive width/height
  const width = Number.isFinite(widthParam) && widthParam > 0 ? widthParam : 800
  const height = Number.isFinite(heightParam) && heightParam > 0 ? heightParam : 600

  console.log('drawBackgroundLayer called. nodes:', cas?.length, 'width,height:', width, height)

  // remove old
  g.selectAll('.background-layer').remove()
  const backgroundLayer = g.append('g').attr('class', 'background-layer').lower()

  if (!cas || cas.length === 0) {
    console.warn('no clustering data')
    return
  }

  // Ensure numeric coordinates (use simulation coords directly—NO extra scaling)
  cas.forEach(d => {
    if (!Number.isFinite(d.x)) d.x = width / 2
    if (!Number.isFinite(d.y)) d.y = height / 2
  })

  let delaunay: d3.Delaunay<any>
  let voronoi: d3.Voronoi<any>
  let minX = Infinity, maxX = -Infinity
  let minY = Infinity, maxY = -Infinity

  cas.forEach(d => {
    if (typeof d.x === 'number' && typeof d.y === 'number') {
      if (d.x < minX) minX = d.x
      if (d.x > maxX) maxX = d.x
      if (d.y < minY) minY = d.y
      if (d.y > maxY) maxY = d.y
    }
  })
  try {
    delaunay = d3.Delaunay.from(cas, (d: any) => d.x, (d: any) => d.y)
    console.log("widht", width, "hight", height)
    voronoi = delaunay.voronoi([minX-100, minY-100, maxX+100, maxY+100])
  } catch (err) {
    console.error('Delaunay/Voronoi error:', err)
    return
  }

  // prepare cluster -> polygons list
  const clusterPolygons: Record<string, number[][][]> = {}
  cas.forEach((d, i) => {
    const poly = voronoi.cellPolygon(i)
    if (poly && poly.length) {
      const cid = String(d.cluster ?? '0')
      if (!clusterPolygons[cid]) clusterPolygons[cid] = []
      clusterPolygons[cid].push(poly)
    }
  })

  const clusters = Object.keys(clusterPolygons)
  if (clusters.length === 0) {
    console.warn('no polygons generated')
    return
  }

  // color ordinal using actual cluster ids as domain to ensure distinct colors
  const clusterColors = d3.scaleOrdinal<string>()
    .domain(clusters as any)
    .range(d3.schemeCategory10)

  // defs + a blur filter with enlarged region to avoid clipping
  let defs = g.select('defs')
  if (defs.empty()) defs = g.append('defs')

  let filter = defs.select('#bg-blur-filter')
  if (filter.empty()) {
    filter = defs.append('filter')
      .attr('id', 'bg-blur-filter')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%')
    filter.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', Math.min(width, height) * 0.06)
  }

  // helper convert polygons->path string
  const polyToPath = (polys: number[][][]) => polys.map(poly => 'M' + poly.map(p => p.join(',')).join('L') + 'Z').join(' ')

  // two layers: blurred underlay + crisp overlay w/ stroke for boundaries
  const blurredLayer = backgroundLayer.append('g').attr('class', 'bg-blur-layer')
  const crispLayer = backgroundLayer.append('g').attr('class', 'bg-crisp-layer')

  const entries = Object.entries(clusterPolygons) // [ [clusterId, [poly,...]], ... ]

  blurredLayer.selectAll('path')
    .data(entries)
    .enter()
    .append('path')
    .attr('d', ([cid, polys]: any) => polyToPath(polys))
    .attr('fill', ([cid]: any) => clusterColors(cid))
    .attr('opacity', 0.35)
    .attr('filter', 'url(#bg-blur-filter)')
    .attr('stroke', 'none')

  crispLayer.selectAll('path')
    .data(entries)
    .enter()
    .append('path')
    .attr('d', ([cid, polys]: any) => polyToPath(polys))
    .attr('fill', ([cid]: any) => clusterColors(cid))
    .attr('opacity', 0.65)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)
    .attr('stroke-opacity', 0.35)

  // overall fade-in
  backgroundLayer.attr('opacity', 0)
    .transition()
    .duration(1000)
    .ease(d3.easeCubicInOut)
    .attr('opacity', 0.5)

  console.log('background drawn. clusters:', clusters.length)
}

</script>

<template>
  <div ref="svgContainer" class="gmap-container"></div>
</template>

<style scoped lang="scss">
.gmap-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.background-layer {
  width: 100%;
  height: 100%;
}
</style>
