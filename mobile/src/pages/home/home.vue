<template>
  <view class="container">
    <!-- 头部 -->
    <view class="header">
      <image class="logo" :src="logoIcon" mode="aspectFill"></image>
      <text class="title">石化设备大检修系统</text>
      <text class="subtitle">员工端</text>

    </view>

    <!-- 功能快捷入口 -->
    <view class="quick-actions">
      <navigator url="/pages/report/report" open-type="navigate">
        <view class="action-item orange">
          <image class="action-icon" :src="alertIcon" mode="aspectFill"></image>
          <text class="action-title">故障上报</text>
          <text class="action-subtitle">即时上报</text>
        </view>
      </navigator>
      <navigator url="/pages/progress/progress" open-type="navigate">
        <view class="action-item green">
          <image class="action-icon" :src="progressIcon" mode="aspectFill"></image>
          <text class="action-title">进度提交</text>
          <text class="action-subtitle">更新状态</text>
        </view>
      </navigator>
      <navigator url="/pages/upload/upload" open-type="navigate">
        <view class="action-item purple">
          <image class="action-icon" :src="uploadIcon" mode="aspectFill"></image>
          <text class="action-title">成果上传</text>
          <text class="action-subtitle">提交资料</text>
        </view>
      </navigator>
    </view>

    <!-- 最新通知 -->
    <view class="notice-card" @tap="goToNotifications">
      <view class="notice-header">
        <view class="notification-badge">
          <image class="icon" :src="noticeIcon" mode="aspectFill"></image>
          <text class="badge">1</text>
        </view>
        <text class="notice-title">最新通知</text>
        <navigator url="/pages/notifications/notifications" class="see-all">查看全部</navigator>
      </view>
      <view class="notice-content">
        <text class="notice-text">明日排程提醒</text>
        <text class="notice-detail">空冷器1检修-拆解，08:00-12:00</text>
      </view>
    </view>

    <!-- 我的排程 -->
    <view class="schedule-section">
      <view class="section-header">
        <text class="section-title">我的排程</text>
        <text
          @tap="()=>{
            Taro.switchTab({url:'/pages/schedule/schedule'})
          }"
          class="see-all">
          查看全部
        </text>
      </view>
      <view class="schedule-list">
        <ScheduleRow :item="schedule" v-for="schedule in scheduleSimplifyList" :key="schedule.process_id"/>
      </view>
    </view>

    <!-- 本周统计 -->
    <view class="stats-card">
      <text class="stats-title">本周统计</text>
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-number">12</text>
          <text class="stat-label">已完成</text>
        </view>
        <view class="stat-item">
          <text class="stat-number" style="color: #FF6B00;">3</text>
          <text class="stat-label">进行中</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">8</text>
          <text class="stat-label">待开始</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import Taro, {useDidShow, usePullDownRefresh} from '@tarojs/taro'
import {alertIcon, logoIcon, noticeIcon, progressIcon, uploadIcon} from '@/assets/assetsImport'
import './home.scss'
import {getSchedule} from "@/request/schedule";
import {ref} from "vue";
import ScheduleRow from "@/components/ScheduleRow.vue";
import {WorkOrderProcess} from "@/utils";

// 跳转到通知页面
const goToNotifications = () => {
  Taro.requestSubscribeMessage({
    tmplIds: ['WmPw__tRb61Mfz1ujftQJEsODS64BbCZ-i5r6NCfdpk'],
    entityIds: []
  })
  Taro.navigateTo({
    url: '/pages/notifications/notifications'
  })

}

// 只是用于首页展示的排程的列表
const scheduleSimplifyList = ref<WorkOrderProcess[]>([]);

const refresh = async () => {
  Taro.showLoading({title: '刷新中'})
  try {
    const currentUserId = Taro.getStorageSync("userInfo")?.emp_id
    const allSchedule = await getSchedule(currentUserId)
    // 首页最多只展示3个排程
    scheduleSimplifyList.value = allSchedule.slice(0, 3)
    Taro.hideLoading()
  } catch (e) {
    Taro.hideLoading()
    Taro.showToast({title: '刷新失败', icon: 'none'})
  } finally {
    Taro.stopPullDownRefresh()
  }
}
// 配置下拉刷新
usePullDownRefresh(refresh)

useDidShow(() => {

  const msg = Taro.getStorageSync('progress_submit_toast')
  if (msg) {
    Taro.removeStorageSync('progress_submit_toast')
    Taro.showToast({title: msg, icon: 'success', duration: 1500})
  } else {
    refresh()
  }

  // 根据token是否存在判断是否登录
  const tokenExist = Taro.getStorageSync('token')
  if (!tokenExist) {
    // 不存在的时候重定向到登录界面
    Taro.reLaunch({url: '/pages/login/login'})
  }

})
</script>

