import request from '@/utils/request.js'

export function getProcessList(params) {
  return request({
    url: '/process/list',
    method: 'get',
    params: params
  })
}

export function getProcessDetail(id) {
  return request({
    url: '/process/find',
    method: 'get',
    params: { id }
  })
}

export function updateProcess(data) {
  return request({
    url: '/process/update',
    method: 'post',
    data: data
  })
}

export function getEquipmentInfo() {
  return request({
    url: '/process/equipment/info',
    method: 'get'
  })
}