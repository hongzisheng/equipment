<script setup>
import { getLabelByProp } from '@/views/ontology/ontologySystem.js'
// Props
const props = defineProps({
  row: {
    type: Object,
    default: () => {},
  },
})

</script>

<template>
  <el-card class="card">
    <div v-if="row && Object.keys(row).length > 0">
      <div v-for="(value, key) in row" :key="key" class="detail-item">
        <span class="key">{{ getLabelByProp(key) }}:</span>
        <span class="value">{{ value }}</span>
      </div>
    </div>
    <div v-else>
      <p>暂无数据</p>
    </div>
  </el-card>
</template>

<style lang="scss" scoped>
.card {
  height: 100%;
  width: 100%;
}

.title {
  width: 100%;
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}
</style>
