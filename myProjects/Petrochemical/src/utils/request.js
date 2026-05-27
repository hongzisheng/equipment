// 封装 axios 请求
import axios from 'axios'
import { ElMessage } from 'element-plus'
import config from '../config'

// 创建 axios 实例
const service = axios.create({
  baseURL: config.baseUrl,
  timeout: config.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    console.log('API请求:', {
      url: config.url,
      method: config.method,
      data: config.data,
      params: config.params
    })
    const token = localStorage.getItem('token') // 或从您的状态管理获取
    if (token) {
      config.headers.Authorization = `Bearer ${token}` // 常见的 JWT 格式
    }
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    console.log('API响应:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    })
    
    const res = response.data
    
    // 根据后端返回的数据结构进行判断
    // 如果后端返回的是 { message: "成功" } 这种格式
    if (response.status === 200) {
      return res
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  (error) => {
    console.error('API响应错误:', error)
    
    let message = '网络请求失败'
    if (error.response) {
      message = `请求错误: ${error.response.status}`
      if (error.response.data?.error) {
        message = error.response.data.error
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service

