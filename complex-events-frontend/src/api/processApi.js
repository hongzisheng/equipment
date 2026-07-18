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

/**
 * 确认/驳回操作
 * @param {Object} data - { id, action: 'confirm'|'reject', approval_comments }
 */
export function updateProcess(data) {
  return request({
    url: '/process/update',
    method: 'post',
    data: data
  })
}

/**
 * 管理员取消流程（任意状态 → cancelled）
 * @param {Object} data - { id, approval_comments? }
 */
export function cancelProcess(data) {
  return request({
    url: '/process/cancel',
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
