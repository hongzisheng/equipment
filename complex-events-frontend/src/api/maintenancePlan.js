import request from '@/utils/request'

const BASE = '/api/maintenance-plans'

/**
 * 获取检修计划列表
 * @param {Object} params - { page, page_size, plan_name, plan_scale, status }
 */
export function getMaintenancePlans(params = {}) {
  return request({
    url: BASE,
    method: 'get',
    params,
  })
}

/**
 * 获取检修计划详情
 * @param {number} id - 计划ID
 */
export function getMaintenancePlan(id) {
  return request({
    url: `${BASE}/${id}`,
    method: 'get',
  })
}

/**
 * 新建检修计划
 * @param {Object} data - 计划信息 + work_order_ids 数组
 */
export function createMaintenancePlan(data) {
  return request({
    url: BASE,
    method: 'post',
    data,
  })
}

/**
 * 更新检修计划
 * @param {number} id - 计划ID
 * @param {Object} data - 更新字段
 */
export function updateMaintenancePlan(id, data) {
  return request({
    url: `${BASE}/${id}`,
    method: 'put',
    data,
  })
}

/**
 * 删除检修计划
 * @param {number} id - 计划ID
 */
export function deleteMaintenancePlan(id) {
  return request({
    url: `${BASE}/${id}`,
    method: 'delete',
  })
}

/**
 * 获取未纳入任何计划的工单列表
 * @param {Object} params - { plan_id } 编辑模式下传入 plan_id 获取已关联+未计划工单
 */
export function getUnplannedWorkOrders(params = {}) {
  return request({
    url: '/api/work-orders/unplanned',
    method: 'get',
    params,
  })
}

/**
 * 获取计划下的所有工单详情
 * @param {number} id - 计划ID
 */
export function getPlanWorkOrders(id) {
  return request({
    url: `${BASE}/${id}/work-orders`,
    method: 'get',
  })
}

/**
 * 查看计划关联的调度方案
 * @param {number} id - 计划ID
 */
export function getPlanSchedulePlan(id) {
  return request({
    url: `${BASE}/${id}/schedule-plan`,
    method: 'get',
  })
}
