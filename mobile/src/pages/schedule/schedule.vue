<template>
  <view class="container">
    <!-- 标题栏 -->
    <view class="header">
      <text class="title">我的排程</text>
    </view>

    <!-- 筛选标签 -->
    <view class="filter-tabs">
      <view class="tabs-grid">
        <view
          v-for="(tab, index) in visibleTabs"
          :key="`${tab.key}-${index}`"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @tap="handleTabTap(tab.key)"
        >
          {{ tab.text }}
        </view>
      </view>
      <view
        v-if="hasMoreTabs"
        class="tab-expand-btn"
        @tap="toggleTabExpand"
      >
        {{ isTabExpanded ? '收起筛选' : '展开筛选' }}
      </view>
    </view>

    <!-- 排程列表 -->
    <view class="schedule-list">
      <view
        v-for="(item, index) in filteredSchedule"
        :key="index"
        class="schedule-row-wrap"
      >
        <ScheduleRow :item="item"/>
      </view>

    </view>
  </view>
</template>

<script setup lang="ts">
import {computed, ComputedRef, ref} from 'vue'
import './schedule.scss'
import {getSchedule} from "@/request/schedule";
import Taro, {useDidShow, usePullDownRefresh} from "@tarojs/taro";
import type {WorkOrderProcess} from "@/utils";
import {getStatusLabel, STATUS_SEQUENCE} from "@/utils";
import ScheduleRow from "@/components/ScheduleRow.vue";
// 排程数据
const scheduleData = ref<WorkOrderProcess[]>([])

type TabItem = {
  key: string
  text: string
}

const ALL_TAB_KEY = 'all'
const ALL_TAB: TabItem = {key: ALL_TAB_KEY, text: '全部'}

// 根据返回数据动态生成状态标签
const statusTabs: ComputedRef<TabItem[]> = computed(() => {
  const statusSet = new Set<string>()
  scheduleData.value.forEach((item) => {
    if (item.task_status) statusSet.add(item.task_status)
  })

  const appearedStatuses = Array.from(statusSet)

  const sortedStatuses = appearedStatuses.sort((a, b) => {
    const aIndex = STATUS_SEQUENCE.indexOf(a)
    const bIndex = STATUS_SEQUENCE.indexOf(b)
    return aIndex - bIndex
  })

  return sortedStatuses.map((status) => ({
    key: status,
    text: getStatusLabel(status)
  }))
})

const tabs: ComputedRef<TabItem[]> = computed(() => [ALL_TAB, ...statusTabs.value])

const DEFAULT_VISIBLE_TAB_COUNT = 4
const isTabExpanded = ref(false)
const hasMoreTabs: ComputedRef<boolean> = computed(() => tabs.value.length > DEFAULT_VISIBLE_TAB_COUNT)
const visibleTabs: ComputedRef<TabItem[]> = computed(() => {
  if (isTabExpanded.value || !hasMoreTabs.value) return tabs.value
  return tabs.value.slice(0, DEFAULT_VISIBLE_TAB_COUNT)
})

// 当前激活的标签
const activeTab = ref(ALL_TAB_KEY)

// 筛选逻辑
const filteredSchedule: ComputedRef<WorkOrderProcess[]> = computed(() => {
  if (activeTab.value === ALL_TAB_KEY) return scheduleData.value
  return scheduleData.value.filter((item) => item.task_status === activeTab.value)
})

// 切换标签
const handleTabTap = (key: string) => {
  activeTab.value = key
}

const toggleTabExpand = () => {
  isTabExpanded.value = !isTabExpanded.value
}

const refresh = async () => {
  Taro.showLoading({title: "刷新中"})
  try {
    const currentUserId = Taro.getStorageSync("userInfo")?.emp_id
    scheduleData.value = await getSchedule(currentUserId)
    // 当状态变更导致当前 tab 消失时，回退到“全部”
    const hasActiveTab = tabs.value.some((tab) => tab.key === activeTab.value)
    if (!hasActiveTab) activeTab.value = ALL_TAB_KEY
  } catch (e) {
    // no-op
  } finally {
    Taro.hideLoading()
    Taro.stopPullDownRefresh()
  }

}

usePullDownRefresh(
  refresh
)

useDidShow(refresh)
</script>
