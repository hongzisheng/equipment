<template>
  <el-card class="material-board-card" shadow="never">
    <template #header>
      <div class="material-header">
        <span>物料库存使用看板</span>
        <div class="material-header-right">
          <el-select
            v-model="selectedTask"
            placeholder="全部任务"
            clearable
            size="small"
            style="width: 140px; margin-right: 10px;"
          >
            <el-option label="全部任务" value="" />
            <el-option label="空冷器1检修" value="空冷器1检修" />
            <el-option label="轴流式通风机1检修" value="轴流式通风机1检修" />
            <el-option label="离心泵1检修" value="离心泵1检修" />
          </el-select>
          <el-tag
            :type="stockStatus === 'warning' ? 'danger' : 'success'"
            size="small"
          >
            {{ stockStatus === 'warning' ? '库存预警' : '库存正常' }}
          </el-tag>
        </div>
      </div>
    </template>

    <div class="material-content">
      <div class="chart-group-wrapper">
        <div class="chart-group">
          <div class="chart-item" style="width: 100%;">
            <div class="chart-container">
              <div v-for="(material, index) in allMaterials" :key="index" class="single-chart">
                <div class="material-label">{{ material.name }}</div>
                <div class="chart-wrapper">
                  <el-progress
                    type="circle"
                    :percentage="Math.round((material.used / material.stock) * 100)"
                    :color="getPieChartColor(material)"
                    :width="80"
                    :stroke-width="8"
                  >
                    <template #default="{ percentage }">
                      <span class="percentage-text">{{ percentage }}%</span>
                    </template>
                  </el-progress>
                </div>
                <div class="stock-info">
                  <span>库存: {{ material.stock }}{{ material.unit || '' }}</span>
                  <span>已用: {{ formatNumber(material.used) }}{{ material.unit || '' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getPieChartColor, formatNumber, getMaterialCategory } from '../utils'

const props = defineProps({
  materials: {
    type: Array,
    required: true
  }
})

const selectedTask = ref('')

const formattedMaterials = computed(() => {
  const groupedMaterials = {
    pipeline: [],
    connector: [],
    equipment: []
  }

  props.materials.forEach(material => {
    const category = getMaterialCategory(material.material_name)
    groupedMaterials[category].push({
      name: material.material_name,
      stock: material.initial_stock,
      used: material.initial_stock - material.current_stock,
      unit: material.unit
    })
  })

  return groupedMaterials
})

const allMaterials = computed(() => {
  const materials = []
  const stockData = formattedMaterials.value

  if (Object.keys(stockData).length === 0) {
    return []
  }

  for (const typeKey in stockData) {
    materials.push(...stockData[typeKey])
  }

  return materials
})

const stockStatus = computed(() => {
  const stockData = formattedMaterials.value
  for (const typeKey in stockData) {
    for (const material of stockData[typeKey]) {
      if (material.used / material.stock >= 0.8) {
        return 'warning'
      }
    }
  }
  return 'normal'
})
</script>

<style scoped>
.material-board-card {
  flex: 1;
  background: white;
  min-height: 300px;
  min-width: 0;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: none;
  display: flex;
  flex-direction: column;
}

.material-board-card :deep(.el-card__header) {
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 20px;
  border-radius: 10px 10px 0 0;
}

.material-board-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.material-header > span {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.chart-group-wrapper {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.material-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chart-group {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  justify-content: center;
}

.chart-item {
  flex: 1;
  min-width: 250px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chart-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  flex: 1;
  align-items: center;
}

.single-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 120px;
  background: white;
  padding: 15px 10px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.material-label {
  margin-bottom: 12px;
  text-align: center;
  font-size: 14px;
  color: #4a5568;
  font-weight: 500;
}

.chart-wrapper {
  margin: 8px 0;
}

.percentage-text {
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
}

.stock-info {
  margin-top: 12px;
  font-size: 12px;
  color: #718096;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: center;
}

.stock-info span {
  padding: 2px 0;
}

:deep(.el-progress-circle) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-tag) {
  border-radius: 12px;
  padding: 0 12px;
  font-weight: 500;
}
</style>