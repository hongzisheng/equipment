import Taro from '@tarojs/taro'

export const baseURL = 'http://127.0.0.1:5000/api'

// 用于防止多次 401 导致多次 reLaunch
let isNavigatingToLogin = false

const request = (options: Taro.request.Option) => {
  const token = Taro.getStorageSync('token') // 从本地取 token

  return Taro.request({
    ...options,
    url: baseURL + options.url,
    header: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
      ...options.header
    }
  }).then(res => {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return res.data
    } else if (res.statusCode == 401) {
      // 防止多次调用 reLaunch
      if (!isNavigatingToLogin) {
        isNavigatingToLogin = true
        // 清除 token 和用户信息
        Taro.removeStorageSync('token')
        Taro.removeStorageSync('userInfo')

        Taro.showToast({title: '未授权，请重新登录', icon: 'none'})

        // 使用 setTimeout 确保 Toast 显示后再导航
        setTimeout(() => {
          Taro.reLaunch({url: '/pages/login/login'}).then(_ => {
            isNavigatingToLogin = false
          })

        }, 300)
      }
      return Promise.reject({message: '未授权，请重新登录'})
    } else {
      Taro.showToast({title: '请求失败', icon: 'none'})
      return Promise.reject(res)
    }
  }).catch(err => {
    console.log(err)
    Taro.showToast({title: '网络错误', icon: 'none'})
    return Promise.reject(err)
  })
}

export default request
