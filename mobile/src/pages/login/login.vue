<template>
  <view class="login-page">
    <view class="login-container">
      <text class="login-title">欢迎登录</text>
      <input type="text" placeholder="请输入用户名" class="login-input" v-model="username"/>
      <input type="password" placeholder="请输入密码" :password="true" class="login-input" v-model="password"/>
      <button class="login-button" @tap="loginBind" :disabled="submitting">
        {{
          !submitting ? "登录" : "登录中..."
        }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import './login.scss'
import {ref} from 'vue'
import Taro, {useDidShow} from '@tarojs/taro'
import {webLogin, wxBind, wxLogin} from '@/request/login'

const username = ref('')
const password = ref('')
const submitting = ref(false)
const autoLoginAttempted = ref(false) // 防止重复自动登录

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// 登录绑定微信
const loginBind = async () => {
  if (submitting.value) return

  const usernameValue = username.value.trim()
  const passwordValue = password.value.trim()

  if (!usernameValue || !passwordValue) {
    await Taro.showToast({title: '请输入用户名和密码', icon: 'none'})
    return
  }

  submitting.value = true
  try {
    const loginRes = await webLogin(usernameValue, passwordValue)
    if (!loginRes?.success || !loginRes?.token) {
      await Taro.showToast({title: loginRes?.message || '登录失败', icon: 'none'})
      return
    }

    // 登录成功后先保存 token，供后续需要鉴权的接口使用。
    Taro.setStorageSync('token', loginRes.token)
    if (loginRes?.user) {
      Taro.setStorageSync('userInfo', loginRes.user)
    }

    const userId = loginRes?.user?.id
    const isWeapp = Taro.getEnv() === Taro.ENV_TYPE.WEAPP

    if (isWeapp && userId) {
      try {
        const wxLoginRes = await Taro.login()
        if (wxLoginRes?.code) {
          const bindRes = await wxBind(wxLoginRes.code, String(userId))
          if (!bindRes?.success) {
            await Taro.showToast({title: bindRes?.message || '微信绑定未完成', icon: 'none', duration: 1800})
            await sleep(1800)
          }
        }
      } catch (_) {
        await Taro.showToast({title: '微信绑定失败', icon: 'none', duration: 1800})
        await sleep(1800)
      }
    }

    await Taro.showToast({title: '登录成功', icon: 'success', duration: 1200})
    await sleep(1200)
    await Taro.reLaunch({url: '/pages/home/home'})
  } catch (error) {
    await Taro.showToast({title: error?.message || '登录异常', icon: 'none'})
  } finally {
    submitting.value = false
  }
}

// 打开登录界面的时候首先尝试自动登录
useDidShow(() => {
  console.log('[Login] useDidShow triggered')

  // 检查是否已有有效的 token，如果有则直接跳转
  const existingToken = Taro.getStorageSync('token')
  if (existingToken) {
    console.log('[Login] Found existing token, navigating to home')
    Taro.reLaunch({url: '/pages/home/home'})
    return
  }

  // 防止重复的自动登录尝试
  if (autoLoginAttempted.value) {
    console.log('[Login] Auto login already attempted, skipping')
    return
  }

  autoLoginAttempted.value = true

  Taro.login({
    success: function (res) {
      if (res.code) {
        console.log('[Login] WeChat login code obtained:', res.code)
        //发起网络请求
        wxLogin(res.code).then(loginRes => {
          if (loginRes?.success) {
            console.log('[Login] Auto login successful')
            // 登录成功的话保存token到本地
            Taro.setStorageSync("token", loginRes.token)
            if (loginRes?.user) {
              Taro.setStorageSync('userInfo', loginRes.user)
            }

            Taro.showToast({title: "自动登录成功", icon: "success", duration: 1000})
            setTimeout(() => {
              Taro.reLaunch({url: '/pages/home/home'})
            }, 1000)
          } else {
            console.log("[Login] Auto login failed:", loginRes)
            // 自动登录失败，允许用户手动登录
            autoLoginAttempted.value = false
            Taro.showToast({title: "自动登录失败，请手动登录", icon: "none", duration: 1500})
          }
        }).catch(err => {
          console.log('[Login] Auto login error:', err)
          autoLoginAttempted.value = false
        })
      } else {
        console.log('[Login] WeChat login failed:', res.errMsg)
        autoLoginAttempted.value = false
      }
    },
    fail: function (err) {
      console.log('[Login] WeChat login error:', err)
      autoLoginAttempted.value = false
    }
  })
})
</script>

