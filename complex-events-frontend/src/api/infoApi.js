import request from '@/utils/request.js'

export function getWorkerStatus(data) {
  return request({
    url: '/info/workers',
    method: 'post',
    data: data
  })
}

export function getOrders() {
  return request({
    url: '/info/orders',
    method: 'get'
  })
}

export function getMaterialInventory(data) {
  return request({
    url: '/info/materials',
    method: 'post',
    data: data
  })
}

export function getMaintenanceTools(data) {
  return request({
    url: '/info/tools',
    method: 'post',
    data: data
  })
}