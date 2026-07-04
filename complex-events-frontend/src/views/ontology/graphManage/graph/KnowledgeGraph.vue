<template>
  <div id="viz" />
  <!-- 右键菜单 -->
  <ContextMenu
    v-show="contextMenuVisible"
    class="context-menu"
    :style="{ top: contextMenuPosition.y + 'px', left: contextMenuPosition.x + 'px' }"
    @cancel="cancelContextMenu"
  />
  <div v-show="false">vis.js提供技术支持</div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, provide, watch } from 'vue'
import { Network, FocusOptions } from 'vis-network'
import { getGraphOptions } from '@/views/ontology/graphManage/graph/index'
import ContextMenu from '@/views/ontology/graphManage/graph/contextMenu/ContextMenu.vue'
import { useGraphStore } from '@/stores/graphStore'
import { storeToRefs } from 'pinia'

defineOptions({ name: 'KnowledgeGraph' })

let viz: Network

const graphStore = useGraphStore()
/**
 * 点击的节点的id列表 ref
 */
const {
  nodesDataSet,
  edgesDataSet,
  clickedNodeIds,
  clickedEdgeIds,
  rightClickedNode,
  contextMenuVisible,
  contextMenuPosition,
  isDirty,
} = storeToRefs(graphStore)
const { vizClickedCallback, vizRightClickedCallback } = graphStore
/**
 * 画布初始化函数
 */
const draw = () => {
  const container = document.getElementById('viz')
  // 初始化画布
  viz = new Network(
    container,
    {},
    getGraphOptions(),
  )
  viz.on('click', vizClickedCallback)
  // 添加右键点击事件
  viz.on('oncontext', vizRightClickedCallback)
}

// 点击其他地方隐藏菜单
document.addEventListener('click', () => {
  contextMenuVisible.value = false
})
const focusOptions: FocusOptions = {
  scale: 1.5,
  animation: {
    duration: 2000,
    easingFunction: 'easeInOutQuad',
  },
}
// 聚焦节点
const focusNode = () => {
  if (rightClickedNode.value) {
    // 聚焦到右键节点的逻辑
    viz.focus(rightClickedNode.value, focusOptions)
    contextMenuVisible.value = false
  }
}
provide('focusNodeProvider', focusNode)

const cancelContextMenu = () => {
  contextMenuVisible.value = false
}
onMounted(() => draw())

/**
 * 使用nodes,edges的数据集进行图的绘制
 * 数据集由父组件统计管理，构造好之后传过来
 * 这个组件只负责展示
 * 修改只负责展示上的修改，如固定位置
 */
// 监听数据集的变化
watch([nodesDataSet, edgesDataSet], () => {
  refreshData()
})

const refresh = ()=>{
  // 手动重新获取更新之后的结果，更新数据集中的数据
  graphStore.getNodesDataSet()
  graphStore.getEdgesDataSet()
  refreshData();
}

const refreshData = () => {

  if (rightClickedNode.value) {
    // 选择展开节点，只固定右键节点的位置
    const nodeId = rightClickedNode.value
    const nodePosition = viz.getPosition(nodeId)
    nodesDataSet.value.update({
      id: nodeId,
      x: nodePosition.x,
      y: nodePosition.y,
      fixed: true, // 固定位置，防止物理引擎移动
    })
  }
  // 更新数据
  viz.setData({
    nodes: nodesDataSet.value,
    edges: edgesDataSet.value,
  })
  // dom更新完成之后执行视觉引导
  nextTick(() => {
    // 更新之后聚焦到右键的位置
    if (rightClickedNode.value) focusNode()
    // 更新之后保持节点的选中状态
    if (clickedNodeIds.value.length > 0) viz.selectNodes([...clickedNodeIds.value], true)
  })
}



const { locked } = storeToRefs(graphStore)

watch(locked, (newValue) => {
  if (!newValue) unlock()
  else lock()
})

/**
 * 锁定画布布局
 */
const lock = () => {
  // 1. 保存当前所有节点的位置
  const positions = viz.getPositions() // 获取当前所有节点的 x, y
  const nodes = nodesDataSet.value

  // 3. 恢复原来节点的位置，并固定它们
  Object.keys(positions).forEach((nodeId) => {
    const node = nodes.get(nodeId)
    if (node) {
      // 更新节点数据，固定其位置
      nodes.update({
        id: nodeId,
        x: positions[nodeId].x,
        y: positions[nodeId].y,
        fixed: true, // 固定位置，防止物理引擎移动
      })
    }
  })
}

/**
 * 解锁画布布局
 */
const unlock = () => {
  const nodes = nodesDataSet.value
  // 更新完成之后取消fix
  const newPositions = viz.getPositions()
  Object.keys(newPositions).forEach((nodeId) => {
    const node = nodes.get(nodeId)
    if (node) {
      // 更新节点数据，固定其位置
      nodes.update({
        id: nodeId,
        fixed: false,
        // 取消fix
      })
    }
  })
}

/**
 * 图谱编辑模式
 */
const selectNodes = (nodeIds: string[]) => {
  viz.selectNodes(nodeIds)
}

const addNodeMode = () => {
  viz.addNodeMode()
}

const addEdgeMode = () => {
  viz.addEdgeMode()
}

const editEdgeMode = () => {
  viz.editEdgeMode()
}

const disableEditMode = () => {
  viz.disableEditMode()
}

const focus = (nodeId: string | number, options?: any) => {
  viz.focus(nodeId, options ? options : focusOptions)
}

const getPositions = (nodeIds?: string[] | number[]) => {
  return viz.getPositions(nodeIds)
}

const setData = (data: any) => {
  viz.setData(data)
}

defineExpose({
  refresh,
  selectNodes,
  addNodeMode,
  addEdgeMode,
  editEdgeMode,
  disableEditMode,
  focus,
  getPositions,
  setData,
  unlock,
})
</script>

<style scoped lang="scss">
#viz {
  width: 100%;
  height: 100%;
  border: 1px solid lightgray;
  font: 22pt arial;

  &:hover {
    box-shadow: 0 0 5px var(--my-system-primary-color); // 发光效果
  }
}

.context-menu {
  position: absolute;
  z-index: 1000;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}
</style>

<style lang="scss">
//自定义 manipulation 工具栏样式,跳出scoped使其生效
@use '@/views/ontology/graphManage/graph/style/visNetwork.scss' as *;
</style>
