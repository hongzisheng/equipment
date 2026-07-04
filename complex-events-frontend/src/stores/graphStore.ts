import { defineStore } from 'pinia'
import { computed, Ref, ref } from 'vue'
import { Edge, Node, nodeLegend } from '@/views/ontology/graphManage/graph'
import { DataSet } from 'vis-data'
import graphApi from '@/api/graphApi'
import KnowledgeGraph from '@/views/ontology/graphManage/graph/KnowledgeGraph.vue'
import { ElMessage } from 'element-plus'

type KnowledgeGraphType = InstanceType<typeof KnowledgeGraph>
export const useGraphStore = defineStore('graph', () => {
  // 图谱的组件引用
  const visRef = ref<Ref<KnowledgeGraphType>>(null)

  function selectNodes(nodeIds: string[]) {
    visRef.value.selectNodes(nodeIds)
  }

  function unlock() {
    visRef.value.unlock()
  }

  function focus(nodeId: string, options?) {
    visRef.value.focus(nodeId, options)
  }

  // 图谱展示的所有节点
  const nodes = ref<Node[]>()
  const addNode = (node: Node) => {
    nodes.value.push(node)
    // 更新数据集
    getNodesDataSet()
    visRef.value.refresh()
  }
  // 根据id不变更新这个node
  const updateNode = (node: Node) => {
    updatedNodes.value = [node]
    getNodesDataSet()
    // 刷新图谱数据
    visRef.value.refresh()
  }
  const deleteNode = (node: Node) => {
    nodesDataSet.value.remove(node.id)
    nodes.value = nodesDataSet.value.get()
    visRef.value.refresh()
  }
  // 图谱展示的所有边的集合
  const edges = ref<Edge[]>()

  const updateEdge = (edge: Edge) => {
    updatedEdges.value = [edge]
    getEdgesDataSet()
    visRef.value.refresh()
  }

  const deleteEdge = (edge: Edge) => {
    edgesDataSet.value.remove(edge.id)
    edges.value = edgesDataSet.value.get()
    visRef.value.refresh()
  }
  // 图谱的编辑模式相关函数和数据
  const toggleAddNodeMode = () => {
    visRef.value.addNodeMode()
  }

  const toggleAddEdgeMode = () => {
    visRef.value.addEdgeMode()
  }

  const toggleEditEdgeMode = () => {
    visRef.value.editEdgeMode()
  }

  // 退出所有编辑模式
  const toggleDisableEditMode = () => {
    // 退出所有编辑模式
    visRef.value.disableEditMode()
  }
  /**
   * 右键的节点
   */
  const rightClickedNode = ref(null)
  // 点击（选中）的节点和边
  const clickedNodes = ref<Node[]>([])
  const clickedEdges = ref<Edge[]>([])

  /**
   * 点击的节点的id列表 ref
   */
  const clickedNodeIds = ref<string[]>([])
  /**
   * 点击的边
   */
  const clickedEdgeIds = ref<string[]>([])
  // 处理节点点击：根据节点id找到Node对象
  const handleNodeClick = (nodeIds: string[]) => {
    if (nodeIds.length > 0) {
      clickedNodes.value = nodeIds.map((nodeId) => {
        return nodes.value.find((node) => node.id === nodeId)
      })
    } else {
      clickedNodes.value = []
    }
  }
  // 点击的节点的类型
  const clickedNodeGroup = computed(() => {
    if (clickedNodes.value) {
      return clickedNodes.value.map((node) => node.group)
    }
    return []
  })
  // 处理边点击：根据边的id找到Edge对象
  const handleEdgeClick = (edgeIds: string[]) => {
    clickedEdges.value = edgeIds.map((edgeId) => {
      return edges.value.find((edge) => edge.id === edgeId)
    })
  }
  // 点击的对象数组，包括节点和边
  const clickedObjects = computed(() => {
    let objects = []
    if (clickedNodes.value) {
      clickedNodes.value.map((node, index) => {
        node['number'] = '节点' + (index + 1)
        objects.push(node)
      })
    }
    if (clickedEdges.value) {
      clickedEdges.value.map((edge, index) => {
        // 用大写字母编号
        edge['number'] = '边' + String.fromCharCode(65 + index)
        objects.push(edge)
      })
    }
    return objects
  })

  /**
   * 用于图例展示，筛选节点中有哪些类型（group），没有的类型不展示
   */
  const nodeGroups = computed(() => {
    if (nodes.value) {
      const groups = nodes.value.map((node) => node.group)
      return Array.from(new Set(groups))
    }
    return []
  })
  /**
   * 不展示所有的图例，动态展示图例
   * 当前画布上有哪些类型的节点，就显示哪些图例
   */
  const nodeGroupsLegendDisplay = computed(() => {
    return nodeGroups.value
      .map((group) => {
        return nodeLegend.find((item) => item.id === group)
      })
      .filter((item) => item !== undefined) // 过滤掉未找到的项
  })

  // 用于网络图的增量更新
  const updatedNodes = ref<Node[]>([])
  const updatedEdges = ref<Edge[]>([])
  /**
   * 用于网络图展示的数据源
   */
  const nodesDataSet = ref<DataSet<Node>>()
  const edgesDataSet = ref<DataSet<Edge>>()

  const getNodesDataSet = () => {
    const nodesWithLabel: Node[] = nodes.value.map((node) => ({
      ...node,
      // 标签太长了加省略号，虽然label和name来源相同，但是修改的时候展示的和改掉的是不带省略号的name
      label: node.name?.length > 10 ? node.name.substring(0, 10) + '...' : node.name,
    }))

    const updatedNodesWithLabel: Node[] = updatedNodes.value.map((node) => ({
      ...node,
      label: node.name?.length > 10 ? node.name.substring(0, 10) + '...' : node.name,
    }))
    // 合并
    nodesDataSet.value = new DataSet(nodesWithLabel)
    nodesDataSet.value.update(updatedNodesWithLabel)
    nodes.value = nodesDataSet.value.get()
    // console.log('merge之后', nodes.value)

    // 方便下次更新
    updatedNodes.value = []
  }

  const getEdgesDataSet = () => {
    // 合并
    edgesDataSet.value = new DataSet(edges.value)
    edgesDataSet.value.update(updatedEdges.value)
    // 更新
    edges.value = edgesDataSet.value.get()
    // 方便下次更新
    updatedEdges.value = []
  }

  // 右键菜单相关状态
  const contextMenuVisible = ref(false)
  const contextMenuPosition = ref({ x: 0, y: 0 })

  /**
   * 点击事件回调函数
   *
   * @param params - 点击事件参数对象
   * @param params.nodes - 被选中的节点ID数组
   * @param params.edges - 被选中的边ID数组
   * @param params.event - 原始点击事件对象
   * @param params.pointer - 指针位置信息
   * @param params.pointer.DOM - DOM坐标 {x: number, y: number}
   * @param params.pointer.canvas - 画布坐标 {x: number, y: number}
   * @param params.items - 点击的项目数组
   *
   */
  const vizClickedCallback = (params: any) => {
    if (params.nodes.length > 0) {
      clickedNodeIds.value = params.nodes
    } else {
      clickedNodeIds.value = []
    }
    handleNodeClick(clickedNodeIds.value)

    if (params.edges.length > 0) {
      clickedEdgeIds.value = params.edges
    } else {
      clickedEdgeIds.value = []
    }
    handleEdgeClick(clickedEdgeIds.value)
  }
  /**
   * 右键事件回调函数
   *
   * @param params - 点击事件参数对象
   * @param params.nodes - 被选中的节点ID数组
   * @param params.edges - 被选中的边ID数组
   * @param params.event - 原始点击事件对象
   * @param params.pointer - 指针位置信息
   * @param params.pointer.DOM - DOM坐标 {x: number, y: number}
   * @param params.pointer.canvas - 画布坐标 {x: number, y: number}
   *
   */
  const vizRightClickedCallback = (params: any) => {
    // 阻止默认右键菜单
    params.event.preventDefault()

    if (params.nodes.length > 0) {
      // 默认只选第一个节点
      rightClickedNode.value = params.nodes[0]

      // 获取鼠标点击位置
      const pointer = params.pointer.DOM

      // 设置菜单位置
      contextMenuPosition.value = {
        x: pointer.x,
        y: pointer.y,
      }

      // 显示自定义菜单
      contextMenuVisible.value = true

      // 触发右键点击事件（可选）
      // emits('nodeRightClick', nodeId)
    } else {
      // 点击空白处隐藏菜单
      contextMenuVisible.value = false
    }
  }

  /**
   * 是否锁定画布
   */
  const locked = ref<boolean>(false)
  /**
   * 加载的时候是否显示加载动画
   */
  const loading = ref<boolean>(false)

  function enableLoading() {
    loading.value = true
  }

  function disableLoading() {
    loading.value = false
  }

  /**
   * 展开节点
   * @param nodeId 需要展开的节点id
   */
  const handleExpandNode = (nodeId: string) => {
    loading.value = true
    graphApi
      .expandNode(nodeId)
      .then((res) => {
        updatedNodes.value = res.data.nodes
        updatedEdges.value = res.data.edges.map((edge) => {
          return {
            ...edge,
            label: '',
          }
        })
        // 进行更新
        getNodesDataSet()
        getEdgesDataSet()
        loading.value = false
      })
      .catch(() => {
        loading.value = false
      })
  }

  function handleExpandCommonNodes(commonType: string, centerNodeId: string) {
    loading.value = true
    graphApi
      .expandCommonNodes(centerNodeId, commonType)
      .then((res) => {
        updatedNodes.value = res.data.nodes
        updatedEdges.value = res.data.edges.map((edge) => {
          return {
            ...edge,
            label: '',
          }
        })
        // 进行更新
        getNodesDataSet()
        getEdgesDataSet()
      })
      .catch((e) => {
        ElMessage.error('更新失败')
      })
      .finally(() => {
        loading.value = false
      })
  }

  /**
   * 根据id查找节点对象
   */
  const findNode = (nodeId: string): Node => {
    return nodes.value.find((n) => n.id == nodeId)
  }

  /**
   * 记录数据是否被修改，被修改的话需要更新数据
   * 用于监听是否需要刷新图谱数据
   */
  const isDirty = ref<boolean>(false)

  return {
    visRef,
    selectNodes,
    unlock,
    focus,
    nodes,
    addNode,
    updateNode,
    deleteNode,
    edges,
    deleteEdge,
    toggleAddNodeMode,
    toggleAddEdgeMode,
    toggleEditEdgeMode,
    toggleDisableEditMode,
    clickedNodes,
    clickedEdges,
    clickedNodeIds,
    clickedEdgeIds,
    clickedNodeGroup,
    nodeGroupsLegendDisplay,
    rightClickedNode,
    handleNodeClick,
    handleEdgeClick,
    clickedObjects,
    nodeGroups,
    updatedNodes,
    updatedEdges,
    nodesDataSet,
    edgesDataSet,
    getNodesDataSet,
    getEdgesDataSet,
    contextMenuVisible,
    contextMenuPosition,
    vizClickedCallback,
    vizRightClickedCallback,
    locked,
    handleExpandNode,
    handleExpandCommonNodes,
    loading,
    enableLoading,
    disableLoading,
    findNode,
    updateEdge,
    isDirty,
  }
})
