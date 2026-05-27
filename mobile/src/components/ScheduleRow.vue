<template>
  <view class="schedule-row" @tap="handleNavigateToDetail">
    <!-- 顶部强调线 -->
    <view class="top-line-green" :style="{
      backgroundColor: statusStyle.lineBg,
      color: statusStyle.lineBg,
      height:'4rpx',
      display: 'block',
      width: '100%',
      'min-height': '4rpx',
      'flex-shrink': '0',
      position: 'relative',
      top: '0',
      background: '#3ebd97' }"></view>

    <view class="item-header">
      <text class="task-title">{{ item.process_name }}</text>
      <text
        class="status-tag"
        :style="{
          backgroundColor: statusStyle.tagBg,
          color: statusStyle.tagText,
          borderColor: statusStyle.tagBorder
        }"
      >
        {{ getStatusLabel(item.task_status) }}
      </text>
    </view>

    <view class="item-body">
      <text class="location">📍 {{ item.task_code }} - {{ item.work_order_title }}</text>
    </view>

    <view class="item-footer">
      <view class="time-group">
        <view class="time">开始 {{ item.scheduled_start_time }}</view>
        <view class="day">结束 {{ item.scheduled_end_time }}</view>
      </view>
      <view class="detail-btn">
        查看详情
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import type {StatusStyle, WorkOrderProcess} from '@/utils'
import {getStatusLabel, getStatusStyle} from '@/utils'
import {computed} from 'vue'
import Taro from '@tarojs/taro'
import {useProcessStore} from '@/stores/process'

const props = defineProps<{ item: WorkOrderProcess }>()
const item = computed(() => props.item)
const statusStyle = computed<StatusStyle>(() => getStatusStyle(item.value.task_status))
const processStore = useProcessStore()

const handleNavigateToDetail = () => {
  // 将当前工序数据存储到全局store
  processStore.setCurrentProcess(item.value)
  // 导航到详情页面
  Taro.navigateTo({
    url: '/pages/scheduleDetails/scheduleDetails'
  })
}
</script>

<style lang="scss">
.schedule-row {
  position: relative;
  padding: 24rpx;
  border-radius: 18rpx;
  background: #fff;
  box-shadow: 0 6rpx 20rpx rgba(15, 23, 42, 0.06);
  overflow: hidden;


  .item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6rpx;
  }

  .task-title {
    flex: 1;
    color: #1f2937;
    font-size: 30rpx;
    font-weight: 600;
    line-height: 1.4;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-tag {
    flex-shrink: 0;
    max-width: 220rpx;
    margin-left: 16rpx;
    padding: 8rpx 16rpx;
    border-radius: 999rpx;
    border: 1rpx solid transparent;
    font-size: 22rpx;
    line-height: 1.4;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .item-body {
    margin-top: 16rpx;
  }

  .location {
    color: #6b7280;
    font-size: 25rpx;
    line-height: 1.5;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .item-footer {
    margin-top: 18rpx;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
  }

  .time-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .time,
  .day {
    color: #6b7280;
    font-size: 23rpx;
    line-height: 1.5;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .day {
    margin-top: 8rpx;
  }

  .detail-btn {
    flex-shrink: 0;
    margin-left: 16rpx;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 56rpx;
    padding: 0 20rpx;
    border-radius: 14rpx;
    background: #3ebd97;
    color: #fff;
    font-size: 24rpx;
    line-height: 1;
  }
}
</style>
