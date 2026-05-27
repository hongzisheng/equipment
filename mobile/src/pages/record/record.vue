<template>
  <view class="container">
    <!-- 标题栏 -->
    <view class="header">
      <text class="title">维修记录</text>
    </view>

    <!-- 标签切换 -->
    <view class="tab-switch">
      <view
        v-for="(tab, index) in tabs"
        :key="index"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="handleTabClick(tab.key)"
      >
        {{ tab.text }}
      </view>
    </view>

    <!-- 维修记录列表 -->
    <view class="record-list">
      <view
        v-for="(item, index) in filteredRecords"
        :key="index"
        class="record-item"
      >
        <!-- 任务标题和状态 -->
        <view class="item-header">
          <text class="task-title">{{ item.title }}</text>
          <text class="status-tag" :class="item.statusClass">{{ item.status }}</text>
        </view>

        <!-- 日期 -->
        <view class="date">
          <text class="date-icon">📅</text>
          <text class="date-text">{{ item.date }}</text>
        </view>

        <!-- 完成进度 -->
        <view class="progress-section">
          <text class="progress-label">完成进度</text>
          <view class="progress-container">
            <text class="progress-value">{{ item.progress }}%</text>
            <view class="progress-bar">
              <view
                class="progress-fill"
                :style="{ width: `${item.progress}%`, backgroundColor: item.progressColor }"
              ></view>
            </view>
          </view>
        </view>

        <!-- 图片数量和详情 -->
        <view class="photos-section">
          <text class="photo-count">
            <image :src="photoIconSrc" mode="aspectFill" class="photo-icon"/>
            {{ item.photos }} 张照片
          </text>
          <navigator url="/pages/record-detail/record-detail?id=1" class="detail-btn">
            查看详情 >
          </navigator>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import {ref, computed} from 'vue'
import {photoIcon} from '@/assets/assetsImport'

const photoIconSrc = photoIcon
// 维修记录数据（模拟接口返回）
const recordsData = [
  {
    id: 1,
    title: '空冷器1检修-拆解',
    date: '2024-01-15',
    progress: 100,
    status: '已完成',
    statusClass: 'completed',
    photos: 5,
    progressColor: '#3EBD97'
  },
  {
    id: 2,
    title: '高心泵1检修-现场验证',
    date: '2024-01-16',
    progress: 75,
    status: '进行中',
    statusClass: 'processing',
    photos: 3,
    progressColor: '#FF6B00'
  },
  {
    id: 3,
    title: '输送泵1检修-井井检验',
    date: '2024-01-17',
    progress: 100,
    status: '已完成',
    statusClass: 'completed',
    photos: 8,
    progressColor: '#3EBD97'
  }
]

// 标签切换
const tabs = [
  {key: 'record', text: '维修记录'},
  {key: 'fault', text: '故障上报'}
]

// 当前激活的标签
const activeTab = ref('record')

// 筛选逻辑
const filteredRecords = computed(() => {
  if (activeTab.value === 'record') return recordsData
  if (activeTab.value === 'fault') return []
  return recordsData
})

// 切换标签
const handleTabClick = (key) => {
  activeTab.value = key
}
</script>

<style lang="scss">
.container {
  background-color: #f5f7fa;
  padding: 20rpx;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  position: relative;
}

.back-btn {
  width: 40rpx;
  height: 40rpx;
  margin-right: 20rpx;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.tab-switch {
  display: flex;
  background: white;
  border-radius: 50rpx;
  overflow: hidden;
  margin-bottom: 30rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.tab-item {
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  color: #666;
  text-align: center;
  border-radius: 50rpx;
  transition: all 0.3s;
}

.tab-item.active {
  background: #3EBD97;
  color: white;
}

.record-list {
  background: white;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.record-item {
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
  position: relative;
}

.record-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15rpx;
}

.task-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.status-tag {
  padding: 6rpx 15rpx;
  border-radius: 15rpx;
  font-size: 24rpx;
  min-width: 80rpx;
  text-align: center;
}

.status-tag.completed {
  background: #E6F7E6;
  color: #3EBD97;
}

.status-tag.processing {
  background: #FFE8E8;
  color: #FF6B00;
}

.date {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  color: #666;
}

.date-icon {
  margin-right: 10rpx;
}

.date-text {
  font-size: 28rpx;
}

.progress-section {
  margin-bottom: 20rpx;
}

.progress-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.progress-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 24rpx;
  color: #666;
}

.progress-value {
  font-weight: bold;
  color: #333;
}

.progress-bar {
  flex: 1;
  height: 10rpx;
  background: #eee;
  border-radius: 5rpx;
  margin: 0 10rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 5rpx;
  transition: width 0.3s ease;
}

.photos-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 24rpx;
  color: #666;
}

.photo-count {
  display: flex;
  align-items: center;
}

.photo-icon {
  width: 20rpx;
  height: 20rpx;
  margin-right: 5rpx;
}

.detail-btn {
  color: #3EBD97;
  text-decoration: none;
}
</style>
