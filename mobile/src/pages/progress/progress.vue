<template>
  <view class="progress-submit-page">
    <!-- 顶部标题 -->
    <view class="header">
      <text class="title">进度提交</text>
    </view>

    <!-- 表单内容 -->
    <view class="form-container">
      <!-- 选择任务 -->
      <view class="form-item">
        <text class="label">选择工单</text>
        <picker :range="workOrderOptions" :value="selectedTaskIndex" range-key="option"
                @change="onTaskChange">
          <view class="picker-input">
            {{ selectedTask?.option ?? '请选择工单' }}
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <view v-if="selectedTask" class="form-item">
        <text class="label">选择工序</text>
        <picker :range="processesOptions" :value="selectedProcessIndex" range-key="option"
                @change="onProcessChange">
          <view class="picker-input">
            {{ selectedProcess?.option ?? '请选择工序' }}
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <!-- 任务状态 -->
      <view class="form-item">
        <text class="label">任务状态</text>
        <view v-if="selectedProcess" class="status-buttons">
          <text>工序号：{{ selectedProcess.process_id }}</text>
          <text>工序状态:{{ getStatusLabel(selectedProcess.task_status) }}</text>
          <text>下一个状态：{{ getNextStatusLabel(selectedProcess.task_status) }}</text>
        </view>
        <view v-else>
          <text>请先选择工序</text>
        </view>
      </view>

      <!-- 工作说明 -->
      <view class="form-item">
        <text class="label">工作说明</text>
        <textarea
          :value="workDescription"
          class="description-input"
          maxlength="500"
          placeholder="请描述本次工作内容、遇到的问题或需要说明的情况"
          @input="onWorkDescriptionInput"
        />
        <view class="char-count">{{ workDescription.length }}/500</view>
      </view>

      <!-- 工况照片 -->
      <view class="form-item">
        <text class="label">工况照片 (最多1张)</text>
        <view class="image-upload-area">
          <view
            v-if="images.length === 0"
            class="upload-placeholder"
            @tap="chooseImage"
          >
            <text class="iconfont">📷</text>
            <text class="upload-text">上传照片</text>
          </view>
          <view class="image-grid">
            <view
              v-for="(img, idx) in images"
              :key="idx"
              class="image-item"
            >
              <image :src="img" class="image-preview" mode="aspectFill"/>
              <text class="delete-btn" @tap="deleteImage(idx)">×</text>
            </view>
            <view
              v-if="images.length < 1"
              class="add-image"
              @tap="chooseImage"
            >
              <text class="iconfont">+</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="submit-btn-wrapper">
        <button
          class="submit-btn"
          @tap="submitReport"
        >
          提交进度
        </button>
      </view>
    </view>
  </view>
</template>

<script lang="ts" setup>
import {computed, ref} from 'vue'
import Taro, {navigateBack, showToast, useDidShow} from '@tarojs/taro'
import './progress.scss'
import {getSchedule, updateProgress} from "@/request/schedule";
import {getNextStatusLabel, getStatusLabel, WorkOrder, WorkOrderProcess} from "@/utils";


// 状态变量
const selectedTaskIndex = ref(null)
const selectedProcessIndex = ref(null)
const workDescription = ref('')
const images = ref([])

// 工单改变监听
const onTaskChange = (e) => {
  selectedTaskIndex.value = e.detail.value
}

// 选中的工单任务
const selectedTask = computed(() => {
  return selectedTaskIndex.value != null ? workOrderOptions.value[selectedTaskIndex.value] : null
})

// 格式化工单选项显示内容
const formatTaskOption = (task: WorkOrder) => `${task.work_order_title} (${task.order_number})`

// 监听工序改变
const onProcessChange = (e) => {
  selectedProcessIndex.value = e.detail.value
}
// 选中的工序
const selectedProcess = computed(() => {
  return selectedProcessIndex.value != null ? processesOptions.value[selectedProcessIndex.value] : null
})

// 格式化下拉选项展示的内容
const formatProcessOption = (task: WorkOrderProcess) => `${task.process_name} (${task.equipment_name}) - ${task.task_code}`

// 选择/拍摄图片
const chooseImage = async () => {
  if (images.value.length >= 1) {
    showToast({title: '最多上传1张图片'})
    return
  }

  const res = await Taro.chooseImage({
    count: 1 - images.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera']
  })

  if (res.errMsg === 'chooseImage:ok') {
    images.value.push(...res.tempFilePaths)
  }
}

const deleteImage = (index) => {
  images.value.splice(index, 1)
}


const workOrderOptions = ref<WorkOrder[]>([])
const processesOptions = computed<WorkOrderProcess[]>(() => {
  if (selectedTaskIndex.value != null && workOrderOptions?.value?.length > 0) {
    const selectedWorkOrder = workOrderOptions.value[selectedTaskIndex.value]
    return selectedWorkOrder.processes
  } else {
    return []
  }

})
// 获取工单和工序数据
const fetchWorkOrders = async () => {
  try {
    const currentUserId = Taro.getStorageSync("userInfo")?.emp_id
    const responseData = await getSchedule(currentUserId)

    // 按工单ID分组并去重
    const workOrderMap = new Map()

    responseData.forEach(item => {
      // 创建工单对象（如果不存在）
      if (!workOrderMap.has(item.work_order_id)) {
        workOrderMap.set(item.work_order_id, {
          work_order_id: item.work_order_id,
          work_order_title: item.work_order_title,
          order_number: item.order_number,
          work_order_status: item.work_order_status,
          priority: item.priority,
          work_order_created_at: item.work_order_created_at,
          worker_name: item.worker_name,
          worker_type: item.worker_type,
          processes: [],
          option: formatTaskOption(item)
        })
      }

      // 构建完整的工序对象，包含所有必要信息
      const processItem = {
        // 工序基本信息
        process_id: item.process_id,
        process_name: item.process_name,
        equipment_id: item.equipment_id,
        equipment_name: item.equipment_name,
        description: item.description,
        estimated_hours: item.estimated_hours,

        // 任务相关信息
        task_id: item.task_id,
        task_code: item.task_code,
        task_status: item.task_status,
        is_milestone: item.is_milestone,
        assignment_status: item.assignment_status,

        // 时间信息
        scheduled_start_time: item.scheduled_start_time,
        scheduled_end_time: item.scheduled_end_time,
        actual_start_time: item.actual_start_time,
        actual_end_time: item.actual_end_time,

        // 工单信息
        work_order_id: item.work_order_id,
        order_number: item.order_number,
        work_order_title: item.work_order_title,
        work_order_status: item.work_order_status,
        priority: item.priority,

        // 工人信息
        worker_name: item.worker_name,
        worker_type: item.worker_type,

        // 选项
        option: formatProcessOption(item)
      }

      // 将工序添加到对应的工单中
      workOrderMap.get(item.work_order_id).processes.push(processItem)
    })

    // 转换为数组并按工单ID排序
    workOrderOptions.value = Array.from(workOrderMap.values()).sort((a, b) =>
      a.work_order_id - b.work_order_id
    )

    // 对每个工单下的工序按计划开始时间排序
    workOrderOptions.value.forEach(workOrder => {
      workOrder.processes.sort((a, b) => {
        const startDiff =
          new Date(a.scheduled_start_time.replace(' ', 'T')).getTime() -
          new Date(b.scheduled_start_time.replace(' ', 'T')).getTime()

        if (startDiff !== 0) return startDiff

        return (
          new Date(a.scheduled_end_time.replace(' ', 'T')).getTime() -
          new Date(b.scheduled_end_time.replace(' ', 'T')).getTime()
        )
      })
    })

    console.log('获取到工单数据:', workOrderOptions.value)

  } catch (error) {
    console.error('获取工单数据失败:', error)
  } finally {
  }
}

useDidShow(fetchWorkOrders)
const onWorkDescriptionInput = (e: any) => {
  workDescription.value = e.detail.value
}

// 验证表单
const validateForm = () => {
  if (selectedTask.value == null || selectedProcess.value == null || selectedProcess.value.task_id == null) {
    return false
  }
  if (workDescription.value == null || workDescription.value.length == 0) {
    return false
  }
  return true
}

const submitReport = async () => {
  if (!validateForm()) return

  try {
    let response = await updateProgress({
      taskId: selectedProcess.value!.task_id,
      description: workDescription.value,
      imagePath: images.value[0] // 没有图片就传 undefined
    })

    // 获取选中的工序信息
    if (response.errMsg == 'uploadFile:ok' || response?.success) {
      Taro.setStorageSync('progress_submit_toast', '工况提交成功')
      navigateBack()
    } else {
      await showToast({
        title: `提交失败: ${response.message || '未知错误'}`, duration: 2000
      })
    }
  } catch (error) {
    console.error('提交工况失败:', error)
    await showToast({title: '提交失败，请稍后重试', duration: 2000})
  }
}
</script>
