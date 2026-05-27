// 设备相关的 API 接口
import request from '../utils/request'

/**
 * 添加设备记录
 * @param {string} type - 设备类型ID
 * @param {string} name - 设备名称
 * @returns {Promise}
 */
export function addEquipment(type, name) {
  // 注意：后端使用的是 form data 格式，需要使用 FormData
  const formData = new FormData()
  formData.append('type', type)
  formData.append('name', name)
  
  return request({
    url: 'http://localhost:5000/add',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 导入数据（上传 Excel）
 * @param {File} file - 文件对象
 * @param {string} type - 模板类型
 * @returns {Promise}
 */
export function importData(file, type) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  
  return request({
    url: 'http://localhost:5000/import',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 下载模板
 * @param {string} type - 模板类型
 * @returns {string} 下载链接
 */
export function getTemplateUrl(type) {
  return `${request.defaults.baseURL}/template?type=${encodeURIComponent(type)}`
}

/**
 * 执行调度算法
 * @param {string} algorithm - 算法类型
 * @returns {Promise}
 */
export function runScheduler(algorithm = 'topological') {
  return request({
    url: 'http://localhost:5000/api/run-scheduler',
    method: 'POST',
    data: {
      algorithm: algorithm,
      selected_worker_ids:selected_worker_ids
    },
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

/**
 * 获取调度器状态
 * @returns {Promise}
 */
export function getSchedulerStatus() {
  return request({
    url: 'http://localhost:5000/api/scheduler-status',
    method: 'GET'
  })
}

