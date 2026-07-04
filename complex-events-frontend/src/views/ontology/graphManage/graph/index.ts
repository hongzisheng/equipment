import { EdgeOptions, NodeOptions } from 'vis-network/declarations/network/Network.js'
import { useGraphStore } from '@/stores/graphStore'
import graphApi from '@/api/graphApi'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import { getOntologySystemOptions, getRelation } from '@/views/ontology/ontologySystem'

export interface Node extends NodeOptions {
  // neo4j 中的 <elementID>
  id?: string
  // 节点原始名称，label可能带有省略号
  name?: string
  // neo4j 中的 <id>
  index?: string
  properties?: {}
}

export interface Edge extends EdgeOptions {
  id?: string
  // 节点原始名称，label可能带有省略号
  name?: string
  index?: string
  properties?: {}
  from?: Node['id']
  to?: Node['id']
}

interface NodeLegend {
  id: string
  color: {
    background: string
    border: string
  }
  // 节点形状
  shape: string
  // 节点大小
  size: number
  // 节点图像
  image?:
    | string
    | {
        selected: string
        unselected: string
      }
}

/**
 * 存储图例的颜色和对应的节点类别
 * 还可以用于节点的配置
 */
export const nodeLegend: NodeLegend[] = [
  {
    id: 'Action',
    color: {
      background: '#FF6B6B',
      border: '#FF5252',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/action/selected.svg',
      unselected: '/graphIcons/action/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Event',
    color: {
      background: '#A8B3A0', // 莫兰迪绿灰
      border: '#8F9987', // 深一度的绿灰
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/event/selected.svg',
      unselected: '/graphIcons/event/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Organization',
    color: {
      background: '#45B7D1',
      border: '#1E88E5',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/organization/selected.svg',
      unselected: '/graphIcons/organization/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Person',
    color: {
      background: '#B3A0B3', // 莫兰迪紫灰
      border: '#998799', // 深一度的紫灰
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/person/selected.svg',
      unselected: '/graphIcons/person/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Report',
    color: {
      background: '#FFEAA7',
      border: '#FFD600',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/report/selected.svg',
      unselected: '/graphIcons/report/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Role',
    color: {
      background: '#DDA0DD',
      border: '#BA55D3',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/role/selected.svg',
      unselected: '/graphIcons/role/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Place',
    color: {
      background: '#FFB347',
      border: '#FF8C00',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/place/selected.svg',
      unselected: '/graphIcons/place/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Time',
    color: {
      background: '#98D8C8',
      border: '#00BDA9',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/time/selected.svg',
      unselected: '/graphIcons/time/unselected.svg',
    },
    size: 15,
  },
  {
    id: 'Resource',
    color: {
      background: '#FFDAB9',
      border: '#FFA500',
    },
    shape: 'image',
    image: {
      selected: '/graphIcons/resource/selected.svg',
      unselected: '/graphIcons/resource/unselected.svg',
    },
    size: 15,
  },
]

export const nodeLegendMap = nodeLegend.reduce((map, legend) => {
  map[legend.id] = legend
  return map
}, {})
const graphStore = useGraphStore()
/**
 * 网络图的相关配置
 */
export const getGraphOptions = () => {
  return {
    groups: nodeLegendMap,
    locale: 'cn',
    interaction: {
      multiselect: true,
      tooltipDelay: 200,
    },
    physics: {
      stabilization: {
        enabled: true,
        iterations: 1000,
        fit: false,
      },
    },
    edges: {
      arrows: {
        to: {
          enabled: true,
          type: 'arrow',
          scaleFactor: 0.5,
        },
      },
      color: {
        inherit: 'both',
      },
    },
    manipulation: {
      enabled: true,
      initiallyActive: true,
      addNode: handleAddNode,
      editEdge: handleEditEdge,
      addEdge: handleAddEdge,
      controlNodeStyle: {
        shape: 'dot',
        size: 15,
        color: {
          background: '#FFECB3',
          border: '#FFD54F',
        },
        opacity: 0.8,
      },
    },
  }
}
const { loading } = storeToRefs(graphStore)

function handleAddNode(nodeData: Node, callback: Function) {
  console.log('Node added:', nodeData)
  loading.value = true
  nodeData.group = 'Action'
  nodeData.name = 'newData' + Date.now().toString()
  graphApi
    .addNode(nodeData.name, nodeData.group)
    .then((res) => {
      if (res.code == 20000) {
        // 使用图谱中返回的id
        nodeData.id = res.data
        ElMessage.success('节点添加成功')
        graphStore.addNode(nodeData)
      } else {
        ElMessage.error('节点添加失败')
      }
    })
    .finally(() => {
      loading.value = false
      callback(nodeData)
      if (nodeData.id) {
        // 图谱选中新增的节点
        graphStore.selectNodes([nodeData.id])
        graphStore.handleNodeClick([nodeData.id])
        // 聚焦
        graphStore.focus(nodeData.id)
      }
    })
}

async function getEdgeRelationName(edgeData) {
  // 判断连接的前后两个点的类别判断关系的名称
  const startTypeProp = graphStore.findNode(edgeData.from).group
  const endTypeProp = graphStore.findNode(edgeData.to).group
  const startLabel = getOntologySystemOptions().find((i) => i.type === startTypeProp).label
  const endLabel = getOntologySystemOptions().find((i) => i.type === endTypeProp).label
  const relation = await getRelation(startLabel, endLabel)
  return relation?.type ?? '未知关系'
}

export async function handleEditEdge(
  edgeData: Edge,
  callback: Function,
  updateRelationFlag = false,
) {
  console.log('Edge edited:', edgeData)
  loading.value = true
  // 是用来手动更新边的，不需要自动获取关系名称
  const relationName = updateRelationFlag ? edgeData.name : await getEdgeRelationName(edgeData)
  graphApi
    .updateEdge(edgeData.id, edgeData.from, edgeData.to, relationName)
    .then((res) => {
      if (res.code == 20000) {
        ElMessage.success('关系修改成功')
        // 删除旧边，创建新边，会返回一个新的id
        edgeData.id = res.data
        graphStore.updateEdge(edgeData)
      } else {
        ElMessage.error('关系修改失败')
      }
    })
    .finally(() => {
      callback(edgeData)
      loading.value = false
    })
}

async function handleAddEdge(edgeData: Edge, callback: Function) {
  console.log('Edge added:', edgeData)
  loading.value = true
  try {
    const relation = await getEdgeRelationName(edgeData)
    graphApi
      .addEdge(edgeData.from, edgeData.to, relation)
      .then((res) => {
        if (res.code === 20000) {
          edgeData.id = res.data
          graphStore.updateEdge(edgeData)
          ElMessage.success('关系添加成功')
        } else {
          ElMessage.error('关系添加失败')
        }
      })
      .finally(() => {
        loading.value = false
        callback(edgeData)
      })
  } catch (e) {
    ElMessage.error('关系添加失败')
    console.error(e)
  }
}
