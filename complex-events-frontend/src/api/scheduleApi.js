import request from '@/utils/request'

/**
 * 获取检修计划列表（用于选择）
 * @param {Object} params - { page, page_size, status }
 */
export function getPlansForSchedule(params = {}) {
  return request({
    url: '/api/maintenance-plans',
    method: 'get',
    params: {
      page: 1,
      page_size: 100,
      ...params
    }
  })
}

/**
 * 基于检修计划执行调度
 * @param {Object} data - { plan_id, algorithm, target }
 */
export function runScheduleFromPlan(data) {
  return request({
    url: '/api/schedule-from-plan',
    method: 'post',
    data
  })
}

/**
 * 获取检修计划的调度方案
 * @param {number} planId - 计划ID
 */
export function getPlanSchedule(planId) {
  return request({
    url: `/api/maintenance-plans/${planId}/schedule-plan`,
    method: 'get'
  })
}

/**
 * 保存/发布调度方案
 */
export function saveSchedule(planId, scheduleData) {
  return request({
    url: `/api/maintenance-plans/${planId}`,
    method: 'put',
    data: {
      status: '调度完成',
      schedule_plan_id: scheduleData.schedule_plan_id
    }
  })
}
