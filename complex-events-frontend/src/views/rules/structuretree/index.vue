<template>
  <div class="knowledge-tree-page">
    <el-card class="page-card" shadow="hover">
      <div class="page-header">
        <div class="title-block">
          <div class="page-title">知识结构树</div>
          <div class="page-subtitle">基于设备分类的知识体系结构，默认展示根节点与一级分类，点击分类展开下级设备</div>
        </div>
        <div class="header-tools">
          <el-button-group class="view-switch">
            <el-button :type="viewMode === 'tree' ? 'primary' : 'default'" @click="viewMode = 'tree'">
              <el-icon><Share /></el-icon>
              结构视图
            </el-button>
            <el-button :type="viewMode === 'list' ? 'primary' : 'default'" @click="viewMode = 'list'">
              <el-icon><Tickets /></el-icon>
              列表视图
            </el-button>
          </el-button-group>
          <el-button @click="updateData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            更新数据
          </el-button>
          <el-button @click="exportStructure">
            <el-icon><Download /></el-icon>
            导出结构
          </el-button>
          <el-button @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
            {{ isFullscreen ? '退出全屏' : '全屏展示' }}
          </el-button>
        </div>
      </div>

      <div class="legend-row">
        <div class="legend-items">
          <span class="legend-item"><i class="dot dot-blue"></i>设备</span>
          <span class="legend-item"><i class="dot dot-green"></i>设备分类</span>
          <span class="legend-item"><i class="dot dot-orange"></i>设备名称</span>
        </div>
        <div class="legend-actions">
          <!-- 缩放工具栏：仅在树形视图下显示 -->
          <div class="zoom-tools" v-if="viewMode === 'tree'">
            <el-button circle :disabled="zoomPercent <= zoomMin" @click="zoomOut">
              <el-icon><Minus /></el-icon>
            </el-button>
            <span class="zoom-percent">{{ zoomPercent }}%</span>
            <el-button circle :disabled="zoomPercent >= zoomMax" @click="zoomIn">
              <el-icon><Plus /></el-icon>
            </el-button>
            <el-button circle @click="resetZoom" title="重置缩放">
              <el-icon><RefreshRight /></el-icon>
            </el-button>
            <el-button circle @click="fitToView" title="适配画布">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </div>

          <!-- 定位根节点按钮：仅树形视图有效 -->
          <el-button circle @click="centerOnRootNode" title="定位根节点">
            <el-icon><Aim /></el-icon>
          </el-button>

          <el-button link type="primary" @click="expandAll">
            <el-icon><Plus /></el-icon> 展开全部
          </el-button>
          <el-button link type="primary" @click="collapseAll">
            <el-icon><Minus /></el-icon> 收起全部
          </el-button>
        </div>
      </div>

      <div class="tree-stage">
        <div
          class="tree-stage-inner"
          :class="{ 'list-mode': viewMode === 'list' }"
          ref="treeStageRef"
          v-loading="loading"
          @mousedown="handleDragStart"
          @mousemove="handleDragMove"
          @mouseup="handleDragEnd"
          @mouseleave="handleDragEnd"
          @wheel.prevent="handleWheel"
        >
          <div v-if="!loading && categoryNodes.length === 0" class="empty-state">
            <el-empty v-if="!backendConnected" description="后端服务未连接">
              <template #image>
                <el-icon :size="60" color="#909399"><Connection /></el-icon>
              </template>
              <el-button type="primary" @click="updateData">
                <el-icon><Refresh /></el-icon> 重新连接
              </el-button>
            </el-empty>
            <el-empty v-else description="暂无设备分类数据" />
          </div>

          <!-- 树形 SVG 视图 -->
          <div v-else-if="viewMode === 'tree'" class="tree-canvas" ref="treeCanvasRef">
            <svg
              :width="svgWidth"
              :height="svgHeight"
              :viewBox="`${-viewX} ${-viewY} ${svgWidth / zoomScaleValue} ${svgHeight / zoomScaleValue}`"
            >
              <g>
                <path
                  v-for="link in computedLinks"
                  :key="link.key"
                  :d="link.path"
                  fill="none"
                  stroke="#93a3c0"
                  stroke-width="2.5"
                  :class="{ 'no-transition': disableTransitions }"
                />
                <g
                  v-for="node in layoutNodes"
                  :key="node.id"
                  :transform="`translate(${node.y},${node.x})`"
                  :class="['node-group', { 'no-transition': disableTransitions }]"
                  @click.stop="handleNodeClick(node)"
                >
                  <title>{{ node.label }}</title>
                  <rect
                    :x="-nodeWidth / 2"
                    :y="-nodeHeight / 2"
                    :width="nodeWidth"
                    :height="nodeHeight"
                    :rx="8"
                    :ry="8"
                    :fill="nodeBgColor(node)"
                    :stroke="nodeStrokeColor(node)"
                    stroke-width="2"
                    style="cursor:pointer"
                  />
                  <text
                    dy="0.35em"
                    text-anchor="middle"
                    font-size="12"
                    fill="#1f2937"
                    style="pointer-events:none"
                  >
                    {{ truncateLabel(node.label, 7) }}
                  </text>
                  <template v-if="hasVisibleChildren(node)">
                    <circle
                      :cx="nodeWidth / 2 - 6"
                      :cy="-nodeHeight / 2 + 6"
                      r="8"
                      fill="white"
                      stroke="#cbd5e1"
                      stroke-width="1.5"
                    />
                    <text
                      :x="nodeWidth / 2 - 6"
                      :y="-nodeHeight / 2 + 6"
                      dy="0.35em"
                      text-anchor="middle"
                      font-size="10"
                      fill="#1f2937"
                      style="pointer-events:none"
                    >
                      {{ getVisibleChildrenCount(node) }}
                    </text>
                  </template>
                </g>
              </g>
            </svg>
          </div>

          <!-- 列表视图 -->
          <div v-else class="list-view-container" ref="listContainerRef">
            <el-tree
              ref="treeRef"
              :data="listData"
              :props="{ label: 'label', children: 'children' }"
              node-key="id"
              :default-expanded-keys="['root']"
              highlight-current
              expand-on-click-node
            >
              <template #default="{ node, data }">
                <span class="list-node">
                  <span class="list-node-label">{{ data.label }}</span>
                  <span class="list-node-count" v-if="data.children && data.children.length">
                    （{{ data.children.length }} 个子节点）
                  </span>
                  <span class="list-node-depth">层级 {{ data.depth }}</span>
                </span>
              </template>
            </el-tree>
          </div>
        </div>
      </div>

      <div class="page-footer">
        <div class="footer-summary">
          共 {{ summary.categories }} 个分类，{{ summary.types }} 台设备，{{ summary.chapters }} 个设备名称，{{ summary.processes }} 个检修工序
        </div>
        <div class="footer-update-info" v-if="lastUpdateTime">
          上次更新：{{ lastUpdateTime }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, nextTick, shallowRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download, FullScreen, Minus, Plus, RefreshRight, Share, Tickets, Refresh, Aim, Connection
} from '@element-plus/icons-vue'
import * as d3 from 'd3'
import request from '@/utils/request'

const CACHE_KEY = 'knowledge_tree_cache'
const CACHE_EXPIRE_HOURS = 24

const viewMode = ref('tree')
const loading = ref(false)
const categoryNodes = ref([])
const collapsedNodeIds = ref(new Set())
const lastUpdateTime = ref('')
const isFullscreen = ref(false)
const backendConnected = ref(true)

const nodeWidth = 140
const nodeHeight = 36
const nodeVerticalSpacing = 24
const nodeHorizontalSpacing = 300

const treeLayout = ref(null)
const initTreeLayout = () => {
  treeLayout.value = d3.tree()
    .nodeSize([nodeHeight + nodeVerticalSpacing, nodeHorizontalSpacing])
    .separation((a, b) => a.parent === b.parent ? 1.2 : 1.5)
}

const layoutNodes = shallowRef([])
const computedLinks = shallowRef([])
const disableTransitions = ref(false)

// 列表视图数据（带虚拟根节点）
const listData = computed(() => {
  if (!categoryNodes.value.length) return []
  return [{
    id: 'root',
    label: '设备',
    depth: 0,
    children: categoryNodes.value
  }]
})

const treeRef = ref(null)
const listContainerRef = ref(null)

// ---------- 工具函数 ----------
function truncateLabel(label, maxLen = 7) {
  if (!label) return ''
  return label.length > maxLen ? label.slice(0, maxLen) + '...' : label
}

// ---------- 数据构建函数 ----------
const buildRelationMaps = (relations) => {
  const equipmentToChapters = new Map()
  const chapterToProcesses = new Map()
  const chapterToSections = new Map()
  const sectionToProcesses = new Map()
  const entityNames = new Map()
  if (!relations?.length) return { equipmentToChapters, chapterToProcesses, chapterToSections, sectionToProcesses, entityNames }

  const normalizeEntityName = (entityId) => {
    if (!entityId) return ''
    const matched = entityId.match(/^[^_]+_(.+)$/)
    return matched ? matched[1] : entityId
  }

  relations.forEach(rel => {
    if (!rel) return
    if (rel.source_name) entityNames.set(rel.source_id, rel.source_name)
    if (rel.target_name) entityNames.set(rel.target_id, rel.target_name)

    const sourceName = rel.source_name || normalizeEntityName(rel.source_id)
    const targetName = rel.target_name || normalizeEntityName(rel.target_id)

    if (rel.source_type === '册名' && rel.target_type === '章节' && rel.relation_type === '包含章节') {
      if (!equipmentToChapters.has(sourceName)) equipmentToChapters.set(sourceName, [])
      equipmentToChapters.get(sourceName).push({ id: rel.target_id, name: targetName || `设备名称${rel.target_id}` })
    }
    if (rel.source_type === '章节' && rel.target_type === '工序' && rel.relation_type === '包含工序') {
      if (!chapterToProcesses.has(rel.source_id)) chapterToProcesses.set(rel.source_id, [])
      chapterToProcesses.get(rel.source_id).push({ id: rel.target_id, name: targetName || `工序${rel.target_id}` })
    }
    if (rel.source_type === '章节' && rel.target_type === '节' && rel.relation_type === '包含节') {
      if (!chapterToSections.has(rel.source_id)) chapterToSections.set(rel.source_id, [])
      chapterToSections.get(rel.source_id).push({ id: rel.target_id, name: targetName || `节${rel.target_id}` })
    }
    if (rel.source_type === '节' && rel.target_type === '工序' && rel.relation_type === '包含工序') {
      if (!sectionToProcesses.has(rel.source_id)) sectionToProcesses.set(rel.source_id, [])
      sectionToProcesses.get(rel.source_id).push({ id: rel.target_id, name: targetName || `工序${rel.target_id}` })
    }
  })

  return { equipmentToChapters, chapterToProcesses, chapterToSections, sectionToProcesses, entityNames }
}

const buildTree = (categories, types, relations) => {
  const {
    equipmentToChapters,
    chapterToProcesses,
    chapterToSections,
    sectionToProcesses,
    entityNames
  } = buildRelationMaps(relations)

  const removedCategoryNames = ['静设备', '知识结构', '静置设备']
  const categoryList = (categories || [])
    .filter(cat => !removedCategoryNames.includes(cat.name))
    .map(cat => ({
      id: cat.id,
      label: cat.name,
      depth: 1,
      children: []
    }))

  const categoryIndex = new Map(categoryList.map(item => [item.label, item]))
  const typesByCategory = new Map()
  ;(types || []).forEach(type => {
    if (!type) return
    const catName = type.category || '未分类'
    if (!removedCategoryNames.includes(catName)) {
      if (!typesByCategory.has(catName)) typesByCategory.set(catName, [])
      typesByCategory.get(catName).push(type)
    }
  })

  typesByCategory.forEach((value, catName) => {
    if (!categoryIndex.has(catName)) {
      const extra = { id: `extra-${catName}`, label: catName, depth: 1, children: [] }
      categoryIndex.set(catName, extra)
      categoryList.push(extra)
    }
  })

  const buildChapterNodes = (chapterEntries, baseDepth) => {
    return chapterEntries.map(chapter => {
      const processMap = new Map()
      const directProcesses = chapterToProcesses.get(chapter.id) || []
      directProcesses.forEach(proc => processMap.set(proc.id, proc))

      const sectionEntries = chapterToSections.get(chapter.id) || []
      sectionEntries.forEach(section => {
        const sectionProcesses = sectionToProcesses.get(section.id) || []
        sectionProcesses.forEach(proc => processMap.set(proc.id, proc))
      })

      const processNodes = Array.from(processMap.values()).map(proc => ({
        id: String(proc.id),
        label: proc.name,
        depth: baseDepth + 1,
        children: []
      }))

      return {
        id: chapter.id,
        label: chapter.name || entityNames.get(chapter.id) || `设备名称${chapter.id}`,
        depth: baseDepth,
        children: processNodes
      }
    })
  }

  categoryList.forEach(cat => {
    const typeList = typesByCategory.get(cat.label) || []
    cat.children = typeList.map((type, idx) => {
      if (!type) return null
      const eqName = type.name || type.id || String(idx)
      const chapterEntries = equipmentToChapters.get(eqName) || []
      const chapterNodes = buildChapterNodes(chapterEntries, 3)
      return {
        id: String(type.id || idx),
        label: type.name,
        depth: 2,
        children: chapterNodes
      }
    }).filter(Boolean)
  })

  let staticSettledNode = null
  if (Array.isArray(types)) {
    const targetType = types.find(t =>
      t && t.category === '静置设备' && t.name === '静置设备'
    )
    if (targetType) {
      const chapterEntries = equipmentToChapters.get(targetType.name) || []
      const chapterNodes = buildChapterNodes(chapterEntries, 2)
      staticSettledNode = {
        id: String(targetType.id),
        label: targetType.name,
        depth: 1,
        children: chapterNodes
      }
    }
  }

  if (!staticSettledNode && equipmentToChapters.has('静置设备')) {
    const chapterEntries = equipmentToChapters.get('静置设备') || []
    const chapterNodes = buildChapterNodes(chapterEntries, 2)
    staticSettledNode = {
      id: 'relation-static-settled-equipment',
      label: '静置设备',
      depth: 1,
      children: chapterNodes
    }
  }

  if (staticSettledNode) {
    categoryList.push(staticSettledNode)
  }

  const allEquipmentNames = new Set(
    categoryList.flatMap(cat => {
      if (cat.label === '静置设备') {
        return ['静置设备']
      }
      return (cat.children || []).map(n => n.label)
    })
  )

  const extraNodes = []
  equipmentToChapters.forEach((chapterEntries, sourceName) => {
    if (!allEquipmentNames.has(sourceName) &&
      sourceName !== '静置设备' &&
      !['轴流式通风机', '特种过滤器', '管壳式换热器', '结晶器'].includes(sourceName)) {
      const node = {
        id: `relation-${sourceName}`,
        label: sourceName,
        depth: 2,
        children: buildChapterNodes(chapterEntries, 3)
      }
      extraNodes.push(node)
    }
  })

  if (extraNodes.length) {
    const otherCategory = {
      id: 'other-equipment',
      label: '其他设备',
      depth: 1,
      children: extraNodes
    }
    categoryList.push(otherCategory)
  }

  categoryNodes.value = categoryList.filter(cat => cat.children?.length || cat.label === '静置设备')

  // 默认折叠：折叠一级分类及以下，仅显示根节点（树形视图）
  const defaultCollapsed = new Set()
  const collectNodesByDepth = (nodes, minDepth) => {
    nodes.forEach(n => {
      if (n.depth >= minDepth) defaultCollapsed.add(n.id)
      if (n.children) collectNodesByDepth(n.children, minDepth)
    })
  }
  categoryNodes.value.forEach(cat => {
    defaultCollapsed.add(cat.id)
    collectNodesByDepth(cat.children || [], 2)
  })
  collapsedNodeIds.value = defaultCollapsed
}

// ---------- D3 布局 ----------
const buildD3Hierarchy = () => {
  if (!categoryNodes.value.length) return null
  const rawData = {
    id: 'root',
    label: '设备',
    children: categoryNodes.value
  }
  const root = d3.hierarchy(rawData)
  root.descendants().forEach(d => {
    d.id = d.data.id
    d.label = d.data.label
    d._children = d.children
    if (collapsedNodeIds.value.has(d.id)) {
      d.children = null
    }
  })
  return root
}

let layoutRAF = null
const updateLayout = (onComplete) => {
  if (layoutRAF) cancelAnimationFrame(layoutRAF)
  layoutRAF = requestAnimationFrame(() => {
    const root = buildD3Hierarchy()
    if (!root) {
      layoutNodes.value = []
      computedLinks.value = []
      if (onComplete) onComplete()
      return
    }
    treeLayout.value(root)
    const nodes = root.descendants().map(d => ({
      id: d.id,
      label: d.label,
      depth: d.depth,
      x: d.x,
      y: d.y,
      children: d.children,
      _children: d._children
    }))
    const links = root.links().map(link => ({
      key: `${link.source.id}-${link.target.id}`,
      path: `M${link.source.y + nodeWidth / 2},${link.source.x} C${link.source.y + nodeWidth / 2 + (link.target.y - link.source.y - nodeWidth) * 0.3},${link.source.x} ${link.target.y - nodeWidth / 2 - (link.target.y - link.source.y - nodeWidth) * 0.3},${link.target.x} ${link.target.y - nodeWidth / 2},${link.target.x}`
    }))
    layoutNodes.value = nodes
    computedLinks.value = links
    disableTransitions.value = nodes.length > 200

    if (nodes.length) {
      const minX = d3.min(nodes, d => d.x)
      const maxX = d3.max(nodes, d => d.x)
      svgHeight.value = Math.max(800, maxX - minX + nodeHeight + 100)
    }

    if (onComplete) {
      nextTick(() => {
        onComplete()
      })
    }
  })
}

watch(collapsedNodeIds, () => updateLayout(), { deep: false })
watch(categoryNodes, () => updateLayout(), { deep: false })

// ---------- 节点样式 ----------
function nodeBgColor(node) {
  if (!node) return '#ffffff'
  if (node.depth === 0) return '#eef2ff'
  if (node.depth === 1) return '#e9f9ef'
  if (node.depth === 2) return '#f3e8ff'
  if (node.depth === 3) return '#fff7ed'
  if (node.depth >= 4) return '#ffedd5'
  return '#ffedd5'
}
function nodeStrokeColor(node) {
  if (!node) return '#cbd5e1'
  if (node.depth === 0) return '#3b82f6'
  if (node.depth === 1) return '#22c55e'
  if (node.depth === 2) return '#a855f7'
  if (node.depth === 3) return '#f59e0b'
  if (node.depth >= 4) return '#ea580c'
  return '#ea580c'
}

function hasVisibleChildren(node) {
  return (node.children?.length || node._children?.length) > 0
}
function getVisibleChildrenCount(node) {
  return node.children ? node.children.length : (node._children ? node._children.length : 0)
}

function handleNodeClick(node) {
  if (!node) return
  const hasChildren = (node.children?.length || node._children?.length) > 0
  if (!hasChildren) return
  const newSet = new Set(collapsedNodeIds.value)
  if (newSet.has(node.id)) {
    newSet.delete(node.id)
  } else {
    newSet.add(node.id)
  }
  collapsedNodeIds.value = newSet
}

// ---------- 展开/收起 ----------
function expandAll() {
  if (viewMode.value === 'list') {
    const tree = treeRef.value
    if (tree) {
      const rootNode = tree.store.root
      const expandNode = (node) => {
        if (node.childNodes && node.childNodes.length) {
          node.expanded = true
          node.childNodes.forEach(child => expandNode(child))
        }
      }
      rootNode.expanded = true
      rootNode.childNodes.forEach(child => expandNode(child))
    }
    return
  }
  collapsedNodeIds.value = new Set()
}

function collapseAll() {
  if (viewMode.value === 'list') {
    const tree = treeRef.value
    if (tree) {
      const rootNode = tree.store.root
      const collapseNode = (node) => {
        if (node.childNodes && node.childNodes.length) {
          node.childNodes.forEach(child => collapseNode(child))
          if (node !== rootNode) {
            node.expanded = false
          }
        }
      }
      rootNode.childNodes.forEach(child => collapseNode(child))
    }
    return
  }
  const ids = new Set()
  function collect(n) {
    if (n.children?.length || n._children?.length) {
      ids.add(n.id)
      n.children?.forEach(collect)
      n._children?.forEach(collect)
    }
  }
  const root = buildD3Hierarchy()
  if (root) collect(root)
  collapsedNodeIds.value = ids
}

// ---------- 统计 ----------
const summary = computed(() => {
  try {
    const categories = categoryNodes.value.length
    const types = categoryNodes.value.reduce((s, c) => s + (c.children?.length || 0), 0)
    const chapters = categoryNodes.value.reduce(
      (s, c) => s + (c.children?.reduce((s2, e) => s2 + (e.children?.length || 0), 0) || 0), 0
    )
    const processes = categoryNodes.value.reduce(
      (s, c) => s + (c.children?.reduce(
        (s2, e) => s2 + (e.children?.reduce((s3, ch) => s3 + (ch.children?.length || 0), 0) || 0), 0
      ) || 0), 0
    )
    return { categories, types, chapters, processes }
  } catch (e) {
    return { categories: 0, types: 0, chapters: 0, processes: 0 }
  }
})

// ---------- 拖拽/缩放 ----------
const treeStageRef = ref(null)
const svgWidth = ref(800)
const svgHeight = ref(800)
const viewX = ref(0)
const viewY = ref(0)
const isDragging = ref(false)
const dragStart = { x: 0, y: 0, viewX: 0, viewY: 0 }
const zoomPercent = ref(100)
const zoomMin = 20
const zoomMax = 200
const zoomScaleValue = computed(() => zoomPercent.value / 100)
const zoomStep = 5

let resizeObserver = null
let fullscreenChangeListener = null

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
  nextTick(() => {
    if (treeStageRef.value) {
      svgWidth.value = treeStageRef.value.clientWidth
      svgHeight.value = treeStageRef.value.clientHeight
      fitToView()
    }
  })
}

const toggleFullscreen = async () => {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
    } else {
      await document.exitFullscreen()
    }
  } catch (error) {
    ElMessage.error('全屏操作失败：' + error.message)
  }
}

onMounted(() => {
  initTreeLayout()
  if (treeStageRef.value) {
    resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        svgWidth.value = entry.contentRect.width
        svgHeight.value = entry.contentRect.height
      }
    })
    resizeObserver.observe(treeStageRef.value)
  }
  fullscreenChangeListener = handleFullscreenChange
  document.addEventListener('fullscreenchange', fullscreenChangeListener)
  loadTree(false)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (fullscreenChangeListener) document.removeEventListener('fullscreenchange', fullscreenChangeListener)
  if (layoutRAF) cancelAnimationFrame(layoutRAF)
})

// 拖拽与滚轮（列表视图禁用）
const handleDragStart = (e) => {
  if (viewMode.value === 'list') return
  if (e.target.closest('.node-group, .zoom-tools, .legend-row, .page-header')) return
  isDragging.value = true
  dragStart.x = e.clientX
  dragStart.y = e.clientY
  dragStart.viewX = viewX.value
  dragStart.viewY = viewY.value
  e.preventDefault()
}

let dragTimer = null
const handleDragMove = (e) => {
  if (viewMode.value === 'list') return
  if (!isDragging.value) return
  if (dragTimer) cancelAnimationFrame(dragTimer)
  dragTimer = requestAnimationFrame(() => {
    const dx = e.clientX - dragStart.x
    const dy = e.clientY - dragStart.y
    viewX.value = dragStart.viewX + dx / zoomScaleValue.value
    viewY.value = dragStart.viewY + dy / zoomScaleValue.value
  })
}

const handleDragEnd = () => {
  if (viewMode.value === 'list') return
  isDragging.value = false
  if (dragTimer) cancelAnimationFrame(dragTimer)
}

let wheelTimer = null
const handleWheel = (e) => {
  if (viewMode.value === 'list') return // 列表视图允许滚动
  e.preventDefault()
  if (wheelTimer) cancelAnimationFrame(wheelTimer)
  wheelTimer = requestAnimationFrame(() => {
    const delta = e.deltaY > 0 ? -zoomStep : zoomStep
    const newZoom = Math.max(zoomMin, Math.min(zoomMax, zoomPercent.value + delta))
    if (newZoom === zoomPercent.value) return
    const rect = treeStageRef.value.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const svgX = mouseX / zoomScaleValue.value + viewX.value
    const svgY = mouseY / zoomScaleValue.value + viewY.value
    zoomPercent.value = newZoom
    viewX.value = svgX - mouseX / zoomScaleValue.value
    viewY.value = svgY - mouseY / zoomScaleValue.value
  })
}

function zoomIn() {
  if (viewMode.value === 'list') return
  if (zoomPercent.value < zoomMax) {
    const centerX = svgWidth.value / 2 / zoomScaleValue.value + viewX.value
    const centerY = svgHeight.value / 2 / zoomScaleValue.value + viewY.value
    zoomPercent.value = Math.min(zoomMax, zoomPercent.value + zoomStep)
    viewX.value = centerX - svgWidth.value / 2 / zoomScaleValue.value
    viewY.value = centerY - svgHeight.value / 2 / zoomScaleValue.value
  }
}

function zoomOut() {
  if (viewMode.value === 'list') return
  if (zoomPercent.value > zoomMin) {
    const centerX = svgWidth.value / 2 / zoomScaleValue.value + viewX.value
    const centerY = svgHeight.value / 2 / zoomScaleValue.value + viewY.value
    zoomPercent.value = Math.max(zoomMin, zoomPercent.value - zoomStep)
    viewX.value = centerX - svgWidth.value / 2 / zoomScaleValue.value
    viewY.value = centerY - svgHeight.value / 2 / zoomScaleValue.value
  }
}

function resetZoom() {
  if (viewMode.value === 'list') return
  zoomPercent.value = 100
  centerOnRootNode()
}

function fitToView() {
  if (viewMode.value === 'list') return

  const nodes = layoutNodes.value
  if (!nodes.length) return

  // 计算所有节点的边界（含内边距）
  const padding = 30
  const minX = d3.min(nodes, d => d.x) - nodeHeight / 2 - padding
  const maxX = d3.max(nodes, d => d.x) + nodeHeight / 2 + padding
  const minY = d3.min(nodes, d => d.y) - nodeWidth / 2 - padding
  const maxY = d3.max(nodes, d => d.y) + nodeWidth / 2 + padding

  const contentWidth = maxY - minY
  const contentHeight = maxX - minX

  // 计算合适的缩放比例（使内容完整可见）
  const scaleX = svgWidth.value / contentWidth
  const scaleY = svgHeight.value / contentHeight
  let scale = Math.min(scaleX, scaleY, 1) // 最大 100%

  // 限制缩放范围（min 20%, max 200%）
  const minScale = zoomMin / 100
  const maxScale = zoomMax / 100
  scale = Math.max(minScale, Math.min(maxScale, scale))

  // 更新缩放百分比
  zoomPercent.value = Math.round(scale * 100)

  // 获取根节点（深度为0）
  const rootNode = nodes.find(n => n.depth === 0) || nodes[0]
  if (!rootNode) return

  // 使根节点精确居中（与定位按钮一致）
  viewX.value = rootNode.y - (svgWidth.value / 2) / scale
  viewY.value = rootNode.x - (svgHeight.value / 2) / scale
}

// ---------- 定位根节点（无偏移，精确居中） ----------
function centerOnRootNode() {
  if (viewMode.value === 'list') return

  const rootNode = layoutNodes.value.find(n => n.depth === 0) || layoutNodes.value[0]
  if (!rootNode || !treeStageRef.value) return

  // 确保尺寸最新
  svgWidth.value = treeStageRef.value.clientWidth
  svgHeight.value = treeStageRef.value.clientHeight

  const scale = zoomScaleValue.value || 1
  viewX.value = (svgWidth.value / 2) / scale - rootNode.y
  viewY.value = (svgHeight.value / 2) / scale - rootNode.x
}

// ---------- 导出 ----------
function exportStructure() {
  try {
    const data = { summary: summary.value, data: categoryNodes.value, exportTime: new Date().toISOString() }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `知识结构树_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('结构导出成功')
  } catch (error) {
    ElMessage.error('导出结构失败')
  }
}

// ---------- 缓存与加载 ----------
const loadFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (!cached) return null
    const data = JSON.parse(cached)
    if (Date.now() - data.timestamp > CACHE_EXPIRE_HOURS * 60 * 60 * 1000) {
      localStorage.removeItem(CACHE_KEY)
      return null
    }
    return data
  } catch (e) {
    return null
  }
}

const saveToCache = (categories, types, relations) => {
  try {
    const data = { categories, types, relations, timestamp: Date.now(), updateTime: new Date().toLocaleString() }
    localStorage.setItem(CACHE_KEY, JSON.stringify(data))
    lastUpdateTime.value = data.updateTime
  } catch (e) { /* ignore */ }
}

// ========== 关键修改：统一使用 updateLayout 回调执行居中 ==========
const loadTree = async (forceUpdate = false) => {
  loading.value = true
  try {
    if (!forceUpdate) {
      const cached = loadFromCache()
      if (cached) {
        buildTree(cached.categories, cached.types, cached.relations)
        lastUpdateTime.value = cached.updateTime
        // ✅ 传递回调，在布局完成后居中
        updateLayout(() => {
          nextTick(() => {
            centerOnRootNode()
          })
        })
        ElMessage.success('从缓存加载成功')
        loading.value = false
        return
      }
    }
    const [catRes, typeRes, relationsRes] = await Promise.all([
      request({ url: '/api/equipment-categories', method: 'GET' }),
      request({ url: '/api/equipment-types-with-category', method: 'GET' }),
      request({ url: '/api/graph-relations-archive', method: 'GET' })
    ])
    if (!catRes?.success || !typeRes?.success || !relationsRes?.success) {
      throw new Error('数据获取失败')
    }
    buildTree(catRes.data, typeRes.data, relationsRes.data)
    saveToCache(catRes.data, typeRes.data, relationsRes.data)
    // ✅ 传递回调，在布局完成后居中
    updateLayout(() => {
      nextTick(() => {
        centerOnRootNode()
      })
    })
    ElMessage.success(forceUpdate ? '更新成功' : '加载成功')
    backendConnected.value = true
  } catch (err) {
    const msg = err?.message || ''
    if (msg.includes('Network Error') || msg.includes('ECONNREFUSED') || msg.includes('Failed to fetch') || msg.includes('timeout')) {
      backendConnected.value = false
      ElMessage.warning('后端服务未连接，无法加载数据')
    } else {
      ElMessage.error(msg || '加载失败')
    }
    categoryNodes.value = []
  } finally {
    loading.value = false
  }
}

const updateData = () => loadTree(true)
</script>

<style scoped>
.knowledge-tree-page { padding: 16px; height: 100%; box-sizing: border-box; background: linear-gradient(180deg, #f5f7fb 0%, #eef3fb 100%); overflow: hidden; }
.page-card { height: 100%; display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; background: #fff; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 18px 22px 14px; border-bottom: 1px solid #eef2f7; flex-shrink: 0; }
.title-block { min-width: 0; }
.page-title { font-size: 20px; font-weight: 800; color: #1f2937; }
.page-subtitle { margin-top: 6px; color: #7a869a; font-size: 13px; }
.header-tools { display: flex; align-items: center; gap: 12px; flex-shrink: 0; flex-wrap: wrap; }
.view-switch :deep(.el-button) { min-width: 110px; }
.legend-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px 8px; flex-shrink: 0; flex-wrap: wrap; }
.legend-items { display: flex; align-items: center; flex-wrap: wrap; gap: 18px; }
.legend-item { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #46556c; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.dot-blue { background: #3b82f6; }
.dot-green { background: #22c55e; }
.dot-orange { background: #f59e0b; }
.legend-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.zoom-tools { display: flex; align-items: center; gap: 10px; }
.zoom-percent { min-width: 52px; text-align: center; color: #475569; font-weight: 600; }
.tree-stage { box-sizing: border-box; padding: 8px 18px 18px; min-height: 850px; height: 850px; }
.tree-stage-inner { height: 100%; border-radius: 16px; border: 1px solid #e7edf5; background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); overflow: hidden; cursor: grab; position: relative; }
.tree-stage-inner:active { cursor: grabbing; }
.tree-stage-inner.list-mode { cursor: default; }
.tree-canvas { width: 100%; height: 100%; }
.empty-state { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.page-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px 18px; flex-shrink: 0; border-top: 1px solid #eef2f7; flex-wrap: wrap; }
.footer-summary { color: #64748b; font-size: 13px; }
.footer-update-info { color: #94a3b8; font-size: 12px; }
.node-group { transition: transform 0.3s ease-in-out; }
path { transition: d 0.3s ease-in-out; }
.no-transition { transition: none !important; }

.list-view-container {
  width: 100%;
  height: 100%;
  padding: 16px 20px;
  overflow: auto;
  background: #fafcff;
}
.list-view-container .el-tree {
  background: transparent;
}
.list-view-container .el-tree-node__content {
  height: 40px;
  border-bottom: 1px solid #f0f4f9;
  transition: background 0.15s;
}
.list-view-container .el-tree-node__content:hover {
  background: #eef6ff;
}
.list-node {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #1f2937;
  width: 100%;
}
.list-node-label {
  font-weight: 500;
}
.list-node-count {
  color: #7a869a;
  font-size: 12px;
}
.list-node-depth {
  margin-left: auto;
  color: #b0bccd;
  font-size: 12px;
}

@media (max-width: 1200px) {
  .page-header, .legend-row, .page-footer { flex-direction: column; align-items: flex-start; }
  .header-tools { width: 100%; }
}
</style>