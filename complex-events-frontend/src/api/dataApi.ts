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
}
