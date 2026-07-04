import request from '@/utils/request'
import { Response } from '@/api/index'
import { Node } from '@/views/ontology/graphManage/graph'

export interface NodeOption {
  // 节点的元素id，删除和修改
  id?: string
  // 节点的名称，新增和修改
  name?: string
  // 节点的类型，新增和修改
  type?: string
}

export interface EdgeOption {
  // 边（关系）的元素id
  id: string
  startNodeId: NodeOption['id']
  endNodeId: NodeOption['id']
  type: string
}

export default {
  build(ids: string[]) {
    return request({
      url: '/graph/build',
      method: 'post',
      data: {
        ids: ids,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  rebuild() {
    return request({
      url: '/graph/rebuild',
      method: 'get',
    })
  },
  /**
   * 获取最新一批节点的数据
   */
  latestGraphData(nodeLimit: string) {
    return request({
      url: '/graph/latest',
      method: 'get',
      params: {
        node_limit: nodeLimit,
      },
    })
  },
  searchGraphData(keyword: string, nodeLimit: string) {
    return request({
      url: '/graph/search',
      method: 'post',
      params: {
        keyword: keyword,
        node_limit: nodeLimit,
      },
    })
  },
  expandNode(nodeId) {
    return request({
      url: '/graph/expandNode/' + nodeId,
      method: 'get',
    })
  },
  expandCommonNodes(centerNodeId: string, commonNodeType: string) {
    return request({
      url: '/graph/expandCommonNodes',
      method: 'post',
      data: {
        centerNodeId: centerNodeId,
        commonNodeType: commonNodeType,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  addNode(nodeName: NodeOption['name'], nodeType: NodeOption['type']) {
    return request({
      url: '/graph/addNode',
      method: 'post',
      data: {
        name: nodeName,
        type: nodeType,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  updateNode(nodeId: NodeOption['id'], nodeName: NodeOption['name'], nodeType: NodeOption['type']) {
    return request({
      url: '/graph/updateNode',
      method: 'post',
      data: {
        id: nodeId,
        name: nodeName,
        type: nodeType,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  deleteNode(nodeId: NodeOption['id']): Promise<Response> {
    return request({
      url: '/graph/deleteNode',
      method: 'delete',
      data: {
        id: nodeId,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  addEdge(
    startNodeId: EdgeOption['startNodeId'],
    endNodeId: EdgeOption['endNodeId'],
    edgeType: EdgeOption['type'],
  ): Promise<Response> {
    return request({
      url: '/graph/addEdge',
      method: 'post',
      data: {
        startNodeId: startNodeId,
        endNodeId: endNodeId,
        type: edgeType,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  updateEdge(
    edgeId: EdgeOption['id'],
    startNodeId: EdgeOption['startNodeId'],
    endNodeId: EdgeOption['endNodeId'],
    edgeType: EdgeOption['type'],
  ): Promise<Response> {
    return request({
      url: '/graph/updateEdge',
      method: 'post',
      data: {
        id: edgeId,
        startNodeId: startNodeId,
        endNodeId: endNodeId,
        type: edgeType,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  deleteEdge(edgeId: EdgeOption['id']): Promise<Response> {
    return request({
      url: '/graph/deleteEdge',
      method: 'delete',
      data: {
        id: edgeId,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  // 存储子图
  saveSubGraph(
    name: string,
    nodes: Node[],
    edges: {
      from: string
      to: string
    }[],
  ) {
    return request({
      url: '/graph/save',
      method: 'post',
      data: {
        name: name,
        nodes: nodes,
        edges: edges,
      },
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  // 获取所有子图
  listSubGraphs() {
    return request({
      url: '/graph/list',
      method: 'get',
    })
  },
  // 获取指定子图数据
  loadSubGraphByName(name) {
    return request({
      url: '/graph/load',
      method: 'get',
      params: {
        name: name,
      },
    })
  },
}
