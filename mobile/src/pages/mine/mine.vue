<template>
  <view class="container">
    <!-- 头部区域 -->
    <view class="header">
      <image :src="avatarIcon" mode="aspectFill" class="avatar"/>
      <view class="user-info">
        <text class="name">{{userInfo.username}}({{userInfo.real_name}})</text>
        <text class="workId">工号: {{userInfo.emp_id}}</text>
        <text class="position">维修技师 · 第一检修组</text>
      </view>
      <view>
        解除绑定
      </view>
    </view>

    <!-- 统计卡片 -->
    <view class="stats-card">
      <view class="stat-item">
        <text class="stat-number">156</text>
        <text class="stat-label">累计任务</text>
      </view>
      <view class="stat-item">
        <text class="stat-number">142</text>
        <text class="stat-label">已完成</text>
      </view>
      <view class="stat-item">
        <text class="stat-number" style="color: #FF6B00;">3</text>
        <text class="stat-label">进行中</text>
      </view>
    </view>

    <!-- 功能列表 -->
    <view class="menu-list">
      <navigator url="/pages/profile/profile" class="menu-item">
        <image :src="settingIcon" mode="aspectFill" class="menu-icon"/>
        <text class="menu-text">个人信息</text>
        <image :src="arrowRightIcon" mode="aspectFill" class="arrow-icon"/>
      </navigator>

      <navigator url="/pages/notifications/notifications" class="menu-item">
        <image :src="noticeIcon" mode="aspectFill" class="menu-icon"/>
        <text class="menu-text">消息通知</text>
<!--        <view class="badge">2</view>-->
        <image :src="arrowRightIcon" mode="aspectFill" class="arrow-icon"/>
      </navigator>

      <navigator url="/pages/settings/settings" class="menu-item">
        <image :src="settingIcon" mode="aspectFill" class="menu-icon"/>
        <text class="menu-text">系统设置</text>
        <image :src="arrowRightIcon" mode="aspectFill" class="arrow-icon"/>
      </navigator>

      <navigator url="/pages/help/help" class="menu-item">
        <image :src="helpIcon" mode="aspectFill" class="menu-icon"/>
        <text class="menu-text">帮助中心</text>
        <image :src="arrowRightIcon" mode="aspectFill" class="arrow-icon"/>
      </navigator>

      <navigator url="/pages/about/about" class="menu-item">
        <image :src="infoIcon" mode="aspectFill" class="menu-icon"/>
        <text class="menu-text">关于我们</text>
        <image :src="arrowRightIcon" mode="aspectFill" class="arrow-icon"/>
      </navigator>
    </view>

    <!-- 退出登录 -->
    <view class="logout-btn" @tap="handleLogout">
      <button class="logout-text">退出登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import Taro, {useDidShow} from '@tarojs/taro'
import {avatarIcon, settingIcon, noticeIcon, helpIcon, infoIcon, arrowRightIcon} from '@/assets/assetsImport'
import './mine.scss'
import {onMounted, reactive, ref} from "vue";

// 退出登录逻辑
const handleLogout = () => {
  Taro.showModal({
    title: '确认退出',
    content: '是否确定退出当前账号？',
    success: (res) => {
      if (res.confirm) {
        // 清除登录状态
        Taro.clearStorageSync()
        Taro.reLaunch({url: '/pages/login/login'})
      }
    }
  })
}

interface UserInfo {
  id: number
  company_id: number | null
  email: string
  phone: string
  real_name: string
  username?: string
  role?: string
  // 工号
  emp_id: number
}

// 登录的信息
const userInfo = reactive<UserInfo>({});

useDidShow(() => {
  const cached = Taro.getStorageSync('userInfo') || {}
  Object.assign(userInfo, cached)
  console.log("mine组件的用户信息", userInfo)
})
</script>
