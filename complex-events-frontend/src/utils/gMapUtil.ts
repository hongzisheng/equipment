import { useMapStore } from '@/stores/mapStore'
import { computed } from 'vue'
import { ExtractResult, Person } from '@/views/ontology/extract/index'

const mapStore = useMapStore()
const eventList = computed(() => mapStore.eventsListTableData)
// 处理节点数据
let nodesDict = {}
// 处理关系数据
let edgesDict = {}
// 节点计数器
let nodeCount = 0
// 关系计数器
let edgeCount = 0

function getNodeKey(nodeName: string, nodeType: string) {
  return nodeName + nodeType
}

function getEdgeKey(sourceID: number, targetID: number) {
  return sourceID + '_' + targetID
}

/**
 * 创建新节点或获取已存在的节点
 * @param nodeName 节点名称
 * @param nodeType 节点类型
 * @returns 返回节点在字典中的标识符（数字）
 */
function createOrGetNodeId(nodeName: string, nodeType: string,isEnevt=true) {
  // 生成节点的唯一键值
  const nodeKey = getNodeKey(nodeName, nodeType)

  // 检查节点是否已存在，如果存在则直接返回，否则创建新节点
  if (nodesDict[nodeKey]) {
    // nodesDict[nodeKey].linkNum+=1
    if(!isEnevt){
      nodesDict[nodeKey].isShare=true
    }
    return nodesDict[nodeKey].nodeId
  } else {
    nodesDict[nodeKey] = { nodeName: nodeName, nodeType: nodeType, nodeId: nodeCount++,isShare:false,linkNum:1 }
    return nodesDict[nodeKey].nodeId
  }
}

/**
 * 创建或获取边的唯一标识符
 * @param sourceID 源节点的ID
 * @param targetID 目标节点的ID
 * @returns 返回边的唯一标识符
 */
function createOrGetEdgeId(sourceID: number, targetID: number, highlight = false) {
  // 获取边的键值
  const edgeKey = getEdgeKey(sourceID, targetID)

  // 如果该边已存在，则返回已有的边ID；否则创建新的边ID
  if (edgesDict[edgeKey]) {
    return edgesDict[edgeKey].edgeId
  } else {
    edgesDict[edgeKey] = { source: sourceID, target: targetID, edgeId: edgeCount++, highlight }
    return edgesDict[edgeKey]
  }
}

export interface ForceNode {
  nodeName: string
  nodeType: string
  nodeId: number
  isShare?: boolean
}

export interface ForceEdge {
  edgeId: number
  source: ForceNode['nodeId']
  target: ForceNode['nodeId']
  highlight?: boolean
}

export const gMapData = async (): Promise<{ nodes: ForceNode[]; edges: ForceEdge[] }> => {
  // 代表不分页，不限制
  mapStore.setUnlimitedFlag(true)
  await mapStore.filter()
  eventList.value.forEach((row: any) => {
    try {
      const eventName = row.eventName
      const eventNameNodeId = createOrGetNodeId(eventName, 'eventName')
      const reportDate = row.time
      const reportDateNodeId = createOrGetNodeId(reportDate, 'reportDate')
      createOrGetEdgeId(reportDateNodeId, eventNameNodeId)
      const persons = row.person.split(',')
      persons.forEach((person: Person) => {
        createOrGetEdgeId(eventNameNodeId, createOrGetNodeId(person.personName, 'person'))
      })
      const organization = row.organizations.split(',')
      organization.forEach((organizationName: string) => {
        createOrGetEdgeId(eventNameNodeId, createOrGetNodeId(organizationName, 'organization'))
      })
      const places = row.place.split(',')
      places.forEach((place: string) => {
        createOrGetEdgeId(eventNameNodeId, createOrGetNodeId(place, 'place'))
      })
    } catch (e) {
      console.log(row, e)
    }
  })
  return {
    nodes: Object.values(nodesDict),
    edges: Object.values(edgesDict),
  }
}

export const formatEventLink = (dataArray: any[], mainEvent): { nodes: ForceNode[]; edges: ForceEdge[] } => {
  const mainEventName = mainEvent.eventName
  const mainEventNameId = createOrGetNodeId(mainEventName, 'mainEventName')
  dataArray.forEach((item: any) => {
    try {
      const row = item.relevantEventDetails
      const eventName = row.eventName
      const eventNameNodeId = createOrGetNodeId(eventName, 'eventName')
      createOrGetEdgeId(mainEventNameId, eventNameNodeId, true)
      if (Array.isArray(row.person)) {
        row.person.forEach((person: Person) => {
          const personNodeId = createOrGetNodeId(person.personName, 'person',false)
          createOrGetEdgeId(eventNameNodeId, personNodeId)
        })
      }
      const organization = (row.organizations || '').split(/[,，]\s*/)
      organization.forEach((organizationName: string) => {
        const organizationId = createOrGetNodeId(organizationName, 'organization',false)
        createOrGetEdgeId(eventNameNodeId, organizationId)
      })

      const places = (row.place || '').split(/[,，]\s*/)
      places.forEach((place: string) => {
        const placeId = createOrGetNodeId(place, 'place',false)
        createOrGetEdgeId(eventNameNodeId, placeId)
      })
    } catch (e) {
      console.error("error:", item, e)
    }
  })
  return {
    nodes: Object.values(nodesDict),
    edges: Object.values(edgesDict),
  }
}

function getEdgeCountByNodeName(name: string) {
  const edges=Object.values(edgesDict)
  edges.f
}

