<template>
  <div class="filter-section">
    <div class="filter-title">
      <el-icon><Filter /></el-icon>
      <span>设备筛选</span>
      <el-button
        v-if="selectedCategory || selectedType || selectedInstance"
        type="primary"
        link
        size="small"
        @click="clearFilters"
        class="clear-filter-btn"
      >
        清除筛选
      </el-button>
    </div>
    <el-row :gutter="16" class="filter-row">
      <el-col :xs="24" :sm="8" :md="6">
        <div class="filter-item">
          <div class="filter-label">
            <el-icon><Folder /></el-icon>
            <span>设备种类</span>
          </div>
          <el-select
            v-model="selectedCategory"
            placeholder="全部种类"
            clearable
            size="default"
            @change="handleCategoryChange"
            class="filter-select"
            :popper-append-to-body="false"
          >
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="`${item.label} (${item.count})`"
              :value="item.value"
            />
          </el-select>
        </div>
      </el-col>

      <el-col :xs="24" :sm="8" :md="6">
        <div class="filter-item">
          <div class="filter-label">
            <el-icon><Files /></el-icon>
            <span>设备类型</span>
          </div>
          <el-select
            v-model="selectedType"
            placeholder="全部类型"
            :disabled="!selectedCategory"
            clearable
            size="default"
            @change="handleTypeChange"
            class="filter-select"
            :popper-append-to-body="false"
          >
            <el-option
              v-for="item in typeOptions"
              :key="item.value"
              :label="`${item.label} (${item.count})`"
              :value="item.value"
            />
          </el-select>
        </div>
      </el-col>

      <el-col :xs="24" :sm="8" :md="6">
        <div class="filter-item">
          <div class="filter-label">
            <el-icon><Monitor /></el-icon>
            <span>设备实例</span>
          </div>
          <el-select
            v-model="selectedInstance"
            placeholder="全部实例"
            :disabled="!selectedType"
            clearable
            size="default"
            @change="handleInstanceChange"
            class="filter-select"
            :popper-append-to-body="false"
            filterable
          >
            <el-option
              v-for="item in instanceOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
      </el-col>

      <el-col :xs="24" :sm="8" :md="6">
        <div class="filter-stats">
          <el-tag type="info" effect="plain" size="large">
            总计: {{ totalCount }} 条工序
          </el-tag>
          <el-tag v-if="selectedInstance" type="success" effect="plain" size="large">
            设备: {{ getSelectedInstanceName }}
          </el-tag>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="filter-row" style="margin-top: 16px;">
      <el-col :xs="24" :sm="12" :md="8">
        <div class="filter-item">
          <div class="filter-label">
            <el-icon><DataLine /></el-icon>
            <span>工单状态</span>
          </div>
          <el-select
            v-model="selectedStatus"
            placeholder="全部状态"
            clearable
            size="default"
            class="filter-select"
            :popper-append-to-body="false"
            @change="emitFilterChange"
          >
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="`${item.label} (${item.count})`"
              :value="item.value"
            />
          </el-select>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="16" class="filter-stats-wrapper">
        <div class="filter-stats">
          <el-tag type="info" effect="plain" size="large">
            总计: {{ totalCount }} 条工序
          </el-tag>
          <el-tag v-if="selectedInstance" type="success" effect="plain" size="large">
            设备: {{ getSelectedInstanceName }}
          </el-tag>
          <el-button
            v-if="selectedCategory || selectedType || selectedInstance || selectedStatus"
            type="primary"
            link
            size="small"
            @click="clearFilters"
            class="clear-all-btn"
          >
            清除所有筛选
          </el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Filter, Folder, Files, Monitor, DataLine } from '@element-plus/icons-vue'
import { getStatusText } from '../utils'

const props = defineProps({
  processes: {
    type: Array,
    default: () => []
  },
  equipmentInfo: {
    type: Object,
    default: () => ({ categories: [], types: {}, instances: {} })
  }
})

const emit = defineEmits(['filter-change'])

const selectedCategory = ref('')
const selectedType = ref('')
const selectedInstance = ref('')
const selectedStatus = ref('')

const typeOptions = ref([])
const instanceOptions = ref([])

const categoryOptions = computed(() => {
  return props.equipmentInfo.categories || []
})

const totalCount = computed(() => props.processes.length)

const getSelectedInstanceName = computed(() => {
  if (!selectedInstance.value) return ''
  const typeKey = `${selectedCategory.value}|${selectedType.value}`
  const instances = props.equipmentInfo.instances[typeKey] || []
  const instance = instances.find(i => i.id === selectedInstance.value)
  return instance ? instance.name : ''
})

const statusOptions = computed(() => {
  const statusSet = new Set(props.processes.map(p => p.status))
  return Array.from(statusSet)
    .map(status => ({
      value: status,
      label: getStatusText(status),
      count: props.processes.filter(p => p.status === status).length
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

function handleCategoryChange() {
  selectedType.value = ''
  selectedInstance.value = ''

  if (selectedCategory.value) {
    const types = props.equipmentInfo.types[selectedCategory.value] || []
    typeOptions.value = types.map(type => ({
      value: type,
      label: type,
      count: props.processes.filter(p =>
        p.equipment_category === selectedCategory.value &&
        p.equipment_type_name === type
      ).length
    })).sort((a, b) => a.label.localeCompare(b.label))
  } else {
    typeOptions.value = []
  }

  emitFilterChange()
}

function handleTypeChange() {
  selectedInstance.value = ''

  if (selectedType.value && selectedCategory.value) {
    const typeKey = `${selectedCategory.value}|${selectedType.value}`
    const instances = props.equipmentInfo.instances[typeKey] || []
    instanceOptions.value = instances.map(instance => ({
      value: instance.id,
      label: instance.name
    })).sort((a, b) => a.label.localeCompare(b.label))
  } else {
    instanceOptions.value = []
  }

  emitFilterChange()
}

function handleInstanceChange() {
  emitFilterChange()
}

function clearFilters() {
  selectedCategory.value = ''
  selectedType.value = ''
  selectedInstance.value = ''
  selectedStatus.value = ''
  typeOptions.value = []
  instanceOptions.value = []
  emitFilterChange()
}

function emitFilterChange() {
  emit('filter-change', {
    category: selectedCategory.value,
    type: selectedType.value,
    instance: selectedInstance.value,
    status: selectedStatus.value
  })
}
</script>

<style scoped>
.filter-section {
  padding: 16px 20px;
  border-bottom: 1px solid #eef2f6;
  background: #fafcfd;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1f4e6a;
}

.filter-title .el-icon {
  font-size: 16px;
  color: #409eff;
}

.clear-filter-btn {
  margin-left: auto;
}

.filter-row {
  display: flex;
  align-items: flex-end;
}

.filter-item {
  background: white;
  border-radius: 8px;
  padding: 8px 12px;
  border: 1px solid #e4edf2;
  transition: all 0.3s;
}

.filter-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #5a7e94;
}

.filter-label .el-icon {
  font-size: 14px;
  color: #409eff;
}

.filter-select {
  width: 100%;
}

.filter-select :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none !important;
  padding-left: 0;
}

.filter-stats {
  display: flex;
  gap: 8px;
  align-items: center;
  height: 100%;
  padding: 8px 0;
}

.filter-stats .el-tag {
  font-size: 13px;
}
</style>