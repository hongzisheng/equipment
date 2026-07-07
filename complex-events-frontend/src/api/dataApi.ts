import request from '@/utils/request.js'
import { typeGroupReduce } from '@/views/ontology/eventsList/correlationTab/index.js'

function normalizeExtractResult(data) {
  return data
}

export default {
  getDataList: (start, limit) => {
    return request({
      url: '/data/list',
      method: 'get',
      params: {
        start,
        limit,
      },
    }).then((res) => {
      const list = res.data.list || []
      return {
        ...res.data,
        list: list.filter((item) => item.del !== true),
      }
    })
  },
  postDeleteId: (id) => {
    return request({
      url: '/data/delete',
      method: 'post',
      params: { id },
    })
  },
  postEditItem: (editItem) => {
    return request({
      url: '/data/edit',
      method: 'post',
      data: { editItem },
    })
  },
  postAddAction: (report_id, actionPosition, action) => {
    return request({
      url: '/data/addAction',
      method: 'post',
      data: {
        report_id,
        actionPosition,
        actions: action,
      },
    })
  },
  getDataById: (id) => {
    return request({
      url: '/data/find',
      method: 'get',
      params: { id },
    }).then((res) => {
      res.data = normalizeExtractResult(res.data)
      return res
    })
  },
  getEventLink: (id, needformatter = true) => {
    return request({
      url: '/data/eventLink',
      method: 'get',
      params: {
        report_id: id,
      },
    }).then((res) => {
      if (needformatter) {
        res.data = typeGroupReduce(res.data)
      }
      return res
    })
  },
  getEventLinkResult: (id) => {
    return request({
      url: '/data/eventLinkResult',
      method: 'get',
      params: {
        report_id: id,
      },
    })
  },
  postCorrentionSearch: (sourceData) => {
    return request({
      url: '/data/event_correlation_search',
      method: 'post',
      data: { sourceData },
    })
  },
  // ---------- compatibility helpers for ontology store ----------
  // 返回本体字段与提示词（前端本地默认实现）
  getFieldsPrompt: () => {
    // 返回结构：{ data: { prompt: [...] } }
    const prompt = [
      { value: '事件', label: '事件', promptList: [] },
      { value: '人物', label: '人物', promptList: [] },
      { value: '角色', label: '角色', promptList: [] },
      { value: '行动', label: '行动', promptList: [] },
      { value: '时间', label: '时间', promptList: [] },
      { value: '地点', label: '地点', promptList: [] },
      { value: '组织', label: '组织', promptList: [] },
    ]
    return Promise.resolve({ data: { prompt } })
  },

  // 返回本体配置列表（前端本地默认实现）
  getOntologyConfiguration: () => {
    const configurations = [
      {
        label: '默认配置',
        extract_fields_list: [
          { field: 'eventName', SelectedStrategy: 0 },
          { field: 'person', SelectedStrategy: 0 },
        ],
      },
    ]
    return Promise.resolve({ data: { configurations } })
  },

  // 返回关系配置，优先尝试读取前端根目录的 test.json（开发环境常见），否则返回空数组
  getEventsLinkConfiguration: () => {
    if (typeof fetch === 'function') {
      return fetch('/test.json')
        .then((r) => r.json())
        .then((arr) => ({ data: { eventsLink: Array.isArray(arr) ? arr : [] } }))
        .catch(() => ({ data: { eventsLink: [] } }))
    }
    return Promise.resolve({ data: { eventsLink: [] } })
  },
}
