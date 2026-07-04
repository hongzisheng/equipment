<template>
  <div class="graph-legend" v-if="showLegend">
    <div class="legend-header">
      <h3>图例</h3>
      <button @click="toggleLegend" class="close-btn">×</button>
    </div>
    <div class="legend-content">
      <div
        v-for="item in nodeGroupsLegendDisplay"
        :key="item.id"
        class="legend-item"
        :class="{ 'legend-item-highlight': clickedNodeGroup && clickedNodeGroup.indexOf(item.id) != -1 }"
      >
<!--        <div-->
<!--          class="legend-color"-->
<!--          :style="{-->
<!--            backgroundColor: item.color.background,-->
<!--            border: `2px solid ${item.color.border}`,-->
<!--          }"-->
<!--        />-->
        <!-- 使用 img 标签显示 SVG -->
        <img
          v-if="item.image && typeof item.image === 'object'"
          :src="item.image.unselected"
          :alt="item.id"
          class="legend-svg"
        />
        <span class="legend-label">{{ item.id }}</span>
      </div>
    </div>
  </div>
  <div v-else class="graph-legend">
    <el-button @click="toggleLegend" class="legend-toggle">显示图例</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useGraphStore } from '@/stores/graphStore'
import { storeToRefs } from 'pinia'

const showLegend = ref(true)

const toggleLegend = () => {
  showLegend.value = !showLegend.value
}

const graphStore = useGraphStore()
const {nodeGroupsLegendDisplay,clickedNodeGroup} = storeToRefs(graphStore)
</script>

<style scoped lang="scss">
.graph-legend {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 180px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-family: Arial, sans-serif;
}

.legend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
}

.legend-header h3 {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.legend-content {
  padding: 8px 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  padding: 3px 6px;
  border-radius: 3px;
  transition: all 0.2s ease;

  &:last-child {
    margin-bottom: 0;
  }

  &:hover {
    background-color: #f5f5f5;
  }
}

.legend-item-highlight {
  background-color: #e3f2fd;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);

  .legend-label {
    font-weight: bold;
    color: #1976d2;
  }
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}

.legend-label {
  font-size: 12px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.legend-svg {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  flex-shrink: 0;
}
</style>
