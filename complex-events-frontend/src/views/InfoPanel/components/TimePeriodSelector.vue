<template>
  <div class="time-period-selector">
    <el-form :inline="true" :model="searchForm" class="time-period-form">
      <el-form-item label="从第">
        <el-input-number v-model="searchForm.startDay" :min="1" :max="projectTotalDays" size="small" />
      </el-form-item>
      <el-form-item label="天的">
        <el-time-select
          v-model="searchForm.startTime"
          :picker-options="timeOptions"
          placeholder="选择时间"
          size="small"
        />
      </el-form-item>
      <el-form-item label="到第">
        <el-input-number v-model="searchForm.endDay" :min="1" :max="projectTotalDays" size="small" />
      </el-form-item>
      <el-form-item label="天的">
        <el-time-select
          v-model="searchForm.endTime"
          :picker-options="timeOptions"
          placeholder="选择时间"
          size="small"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  projectTotalDays: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['update:modelValue', 'time-change'])

const searchForm = reactive({
  startDay: 1,
  startTime: '08:00',
  endDay: props.projectTotalDays,
  endTime: '20:00'
})

const timeOptions = {
  start: '08:00',
  step: '00:30',
  end: '20:00'
}

watch(() => props.modelValue, (val) => {
  if (val) {
    Object.assign(searchForm, val)
  }
}, { immediate: true, deep: true })

watch(searchForm, (val) => {
  emit('update:modelValue', { ...val })
  emit('time-change', val)
}, { deep: true })
</script>

<style scoped>
.time-period-selector {
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  margin-left: auto;
  margin-right: auto;
  max-width: 800px;
  width: 100%;
}

.time-period-form {
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 15px;
}

.time-period-form .el-form-item {
  margin-bottom: 0;
  margin-right: 0;
}

.time-period-form .el-form-item__label {
  color: #4a5568;
  font-weight: 500;
}
</style>