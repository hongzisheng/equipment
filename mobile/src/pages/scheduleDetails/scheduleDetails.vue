<template>
  <view class="container">
    <view class="info-card">
      <!-- 顶部强调线 -->
      <view class="top-line" :style="{ backgroundColor: statusStyle.lineBg }"></view>

      <!-- 工序名称和状态 -->
      <view class="info-header">
        <view class="title-section">
          <text class="process-name">{{ processData?.process_name }}</text>
          <text class="equipment-name">{{ processData?.equipment_name }}</text>
        </view>
        <text
          class="status-tag"
          :style="{
            backgroundColor: statusStyle.tagBg,
            color: statusStyle.tagText,
            borderColor: statusStyle.tagBorder
          }"
        >
          {{ getStatusLabel(processData?.task_status) }}
        </text>
      </view>

      <!-- 工序编号 -->
      <view class="info-row">
        <text class="label">工序编号</text>
        <text class="value">{{ processData?.task_code }}</text>
      </view>

      <!-- 工序ID -->
      <view class="info-row">
        <text class="label">工序ID</text>
        <text class="value">{{ processData?.process_id }}</text>
      </view>

      <!-- 工单编号 -->
      <view class="info-row">
        <text class="label">工单编号</text>
        <text class="value">{{ processData?.order_number }}</text>
      </view>

      <!-- 开始时间 -->
      <view class="info-row">
        <text class="label">开始时间</text>
        <text class="value">{{ processData?.scheduled_start_time }}</text>
      </view>

      <!-- 结束时间 -->
      <view class="info-row">
        <text class="label">结束时间</text>
        <text class="value">{{ processData?.scheduled_end_time }}</text>
      </view>

      <!-- 预计工时 -->
      <view class="info-row">
        <text class="label">预计工时</text>
        <text class="value">{{ processData?.estimated_hours }} 小时</text>
      </view>

      <!-- 任务描述 -->
      <view class="info-row">
        <text class="label">任务描述</text>
        <text class="value description">
          {{ processData?.description || '暂无描述' }}
        </text>
      </view>
    </view>

    <!-- 操作区 -->
    <view class="action-card">
      <button
        class="primary-btn"
        :disabled="materialsLoading"
        @tap="fetchMaterials"
      >
        {{ materialsLoading ? '加载中...' : '获取任务指导和材料' }}
      </button>
    </view>

    <!-- 任务指导书 -->
    <view class="materials-section">
      <view class="section-header">
        <text class="section-title">任务指导书</text>
        <text v-if="materialsLoading" class="loading-text">加载中...</text>
      </view>

      <view v-if="!materialsLoading && guideMarkdown" class="markdown-body">
        <rich-text :nodes="guideNode" />
      </view>

      <view v-else-if="!materialsLoading" class="empty-state">
        <text class="empty-text">暂无任务指导内容</text>
      </view>
    </view>

    <!-- 材料和辅料 -->
    <view class="materials-section">
      <view class="section-header">
        <text class="section-title">材料和辅料</text>
      </view>

      <view v-if="!materialsLoading && materialsMarkdown" class="markdown-body">
        <rich-text :nodes="materialsNode" />
      </view>

      <view v-else-if="!materialsLoading" class="empty-state">
        <text class="empty-text">暂无所需材料</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import {computed, ref} from 'vue'
import Taro, {useDidShow, useRouter} from '@tarojs/taro'
import './scheduleDetails.scss'
import type {StatusStyle} from '@/utils'
import {getStatusLabel, getStatusStyle} from '@/utils'
import {useProcessStore} from '@/stores/process'
import {getProcessMaterials} from '@/request/schedule'
import { renderMarkdown } from '@/utils/markdown'
// 从store获取工序数据
const processStore = useProcessStore()
const processData = computed(() => processStore.currentProcess)

type SuggestionOutput = {
  guide?: string
  materials?: string
}


const guideMarkdown = ref('')
const materialsMarkdown = ref('')
const materialsLoading = ref(false)

// 获取路由参数
const router = useRouter()

// 状态样式
const statusStyle = computed<StatusStyle>(() => {
  if (!processData.value) {
    return {
      lineBg: '#9ca3af',
      tagBg: '#f3f4f6',
      tagText: '#4b5563',
      tagBorder: '#d1d5db'
    }
  }
  return getStatusStyle(processData.value.task_status)
})

const guideNode = computed(() => {
  console.log("正在进行中",renderMarkdown(guideMarkdown.value))
  return renderMarkdown(guideMarkdown.value)
})
const materialsNode = computed(() => renderMarkdown(materialsMarkdown.value))
// 页面显示时的初始化
useDidShow(() => {
  // 如果没有数据，则从路由参数获取（备选方案）
  if (!processData.value && router.params.taskId) {
    // 这里可以调用接口根据taskId获取详情
    // 例如: const detail = await getProcessDetail(router.params.taskId)
    // processStore.setCurrentProcess(detail)
  }
})

// 返回上一页
const handleGoBack = () => {
  Taro.navigateBack({
    delta: 1
  })
}


// 获取材料清单接口
const fetchMaterials = async () => {
  if (!processData.value) {
    Taro.showToast({
      title: '缺少工序信息',
      icon: 'error'
    })
    return
  }

  materialsLoading.value = true
  try {
    Taro.showLoading({title:"加载中"})
    const response = await getProcessMaterials(processData.value.task_id)
    if (response && response.output) {
      const output = response.output as SuggestionOutput
      console.log(output)
      guideMarkdown.value = output.guide || ''
      materialsMarkdown.value = output.materials || ''
      console.log(guideMarkdown.value)
      Taro.hideLoading()
      Taro.showToast({
        title: '内容已加载',
        icon: 'success',
        duration: 2000
      })
    }
  } catch (error) {
    console.error('获取材料清单失败:', error)
    Taro.hideLoading()
    Taro.showToast({
      title: '加载失败，请重试',
      icon: 'error'
    })
  } finally {
    materialsLoading.value = false
  }
}
</script>
