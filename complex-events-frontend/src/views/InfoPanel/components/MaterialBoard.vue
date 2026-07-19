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
                  <svg class="stock-circle" viewBox="0 0 100 100">
                    <circle
                      class="circle-bg"
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="#E2E8F0"
                      stroke-width="8"
                    />
                    <circle
                      v-if="material.greenPercentage > 0"
                      class="circle-green"
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="#10B981"
                      stroke-width="8"
                      :stroke-dasharray="material.greenDasharray"
                      :stroke-dashoffset="material.greenDashoffset"
                      stroke-linecap="round"
                      transform="rotate(-90 50 50)"
                    />
                    <circle
                      v-if="material.yellowPercentage > 0"
                      class="circle-yellow"
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="#EAB308"
                      stroke-width="8"
                      :stroke-dasharray="material.yellowDasharray"
                      :stroke-dashoffset="material.yellowDashoffset"
                      stroke-linecap="round"
                      transform="rotate(-90 50 50)"
                    />
                    <circle
                      v-if="material.redPercentage > 0"
                      class="circle-red"
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="#EF4444"
                      stroke-width="8"
                      :stroke-dasharray="material.redDasharray"
                      :stroke-dashoffset="material.redDashoffset"
                      stroke-linecap="round"
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div class="stock-center">
                    <span class="stock-number">{{ material.stock }}</span>
                    <span class="stock-unit">{{ material.unit }}</span>
                  </div>
                </div>
                <div class="stock-info">
                  <span class="plan-usage">计划使用: {{ material.planUsage }}{{ material.unit || '' }}</span>
                  <span class="actual-usage">已使用: {{ material.actualUsage }}{{ material.unit || '' }}</span>
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
import { getMaterialCategory } from '../utils'

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
    const stock = material.initial_stock || 0
    const planUsage = material.plan_usage || 0
    const actualUsage = material.actual_usage || 0

    const CIRCUMFERENCE = 2 * Math.PI * 42
    
    let redPercentage = 0
    let yellowPercentage = 0
    let greenPercentage = 0
    
    if (stock > 0) {
      redPercentage = Math.min(Math.round((actualUsage / stock) * 100), 100)
      const planPercentage = Math.min(Math.round((planUsage / stock) * 100), 100)
      yellowPercentage = Math.max(0, planPercentage - redPercentage)
      greenPercentage = Math.max(0, 100 - planPercentage)
    }
    
    const redLength = (redPercentage / 100) * CIRCUMFERENCE
    const yellowLength = (yellowPercentage / 100) * CIRCUMFERENCE
    const greenLength = (greenPercentage / 100) * CIRCUMFERENCE
    
    groupedMaterials[category].push({
      name: material.material_name,
      stock: stock,
      planUsage: planUsage,
      actualUsage: actualUsage,
      redPercentage: redPercentage,
      yellowPercentage: yellowPercentage,
      greenPercentage: greenPercentage,
      redDasharray: `${redLength} ${CIRCUMFERENCE}`,
      redDashoffset: 0,
      yellowDasharray: `${yellowLength} ${CIRCUMFERENCE}`,
      yellowDashoffset: -redLength,
      greenDasharray: `${greenLength} ${CIRCUMFERENCE}`,
      greenDashoffset: -(redLength + yellowLength),
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
      if (material.actualUsage / material.stock >= 0.8) {
        return 'warning'
      }
    }
  }
  return 'normal'
})
</script>

<style scoped>
.material-board-card {
  flex: 1.2;
  background: white;
  min-height: 400px;
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
  width: 150px;
  background: white;
  padding: 20px 15px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.material-label {
  margin-bottom: 15px;
  text-align: center;
  font-size: 13px;
  color: #4a5568;
  font-weight: 500;
  line-height: 1.3;
}

.chart-wrapper {
  margin: 8px 0;
  position: relative;
  width: 100px;
  height: 100px;
}

.stock-circle {
  width: 100%;
  height: 100%;
}

.stock-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
}

.stock-number {
  font-size: 22px;
  font-weight: 700;
  color: #2d3748;
  line-height: 1;
}

.stock-unit {
  font-size: 11px;
  color: #718096;
  margin-top: 3px;
}

.stock-info {
  margin-top: 15px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  text-align: center;
}

.plan-usage {
  color: #EAB308;
  font-weight: 500;
}

.actual-usage {
  color: #10B981;
  font-weight: 500;
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