<template>
  <el-card class="repair-tools-card" shadow="never">
    <template #header>
      <div class="tools-header">
        <span>维修器具使用状态看板</span>
        <el-select
          v-model="typeFilter"
          placeholder="按类型筛选"
          clearable
          size="small"
          style="width: 140px;"
        >
          <el-option label="全部类型" value="" />
          <el-option label="起重设备" value="起重设备" />
          <el-option label="运输设备" value="运输设备" />
          <el-option label="焊接设备" value="焊接设备" />
          <el-option label="通风设备" value="通风设备" />
          <el-option label="加热设备" value="加热设备" />
        </el-select>
      </div>
    </template>

    <div class="tools-content-wrapper">
      <div class="tools-content">
        <el-table :data="filteredTools" style="width: 100%">
          <el-table-column prop="name" label="器具名称" width="200" />
          <el-table-column prop="type" label="器具类型" width="150" />
          <el-table-column label="使用状态" width="150">
            <template #default="{ row }">
              <el-tag :type="row.isAvailable ? 'success' : 'danger'" size="small">
                {{ row.isAvailable ? '可用' : '占用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="usedBy" label="使用任务" min-width="200">
            <template #default="{ row }">
              {{ row.isAvailable ? '无' : row.usedBy }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  tools: {
    type: Array,
    required: true
  }
})

const typeFilter = ref('')

const filteredTools = computed(() => {
  let toolsArray = props.tools

  if (typeFilter.value) {
    toolsArray = toolsArray.filter(tool => tool.tool_type === typeFilter.value)
  }

  return toolsArray.map(tool => ({
    id: tool.tool_id,
    name: tool.tool_name,
    type: tool.tool_type,
    isAvailable: tool.usage_status === '空闲',
    usedBy: tool.usage_tasks && tool.usage_tasks.length > 0
      ? tool.usage_tasks.map(task => task.task_name).join(', ')
      : '无'
  }))
})
</script>

<style scoped>
.repair-tools-card {
  background: white;
  min-height: 200px;
  min-width: 0;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: none;
  display: flex;
  flex-direction: column;
}

.repair-tools-card :deep(.el-card__header) {
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 20px;
  border-radius: 10px 10px 0 0;
}

.repair-tools-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tools-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tools-header > span {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.tools-content-wrapper {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.tools-content {
  padding: 10px 0;
  min-height: 0;
}

.tools-content :deep(.el-table) {
  background: transparent;
}

.tools-content :deep(.el-table th) {
  background-color: #f8fafc !important;
  color: #4a5568;
  font-weight: 500;
}

:deep(.el-tag) {
  border-radius: 12px;
  padding: 0 12px;
  font-weight: 500;
}
</style>