<script setup>
import CorrelationTab from '@/views/ontology/eventsList/correlationTab/index.vue'
import ListTab from '@/views/ontology/eventsList/listTab/index.vue'
import { provide, ref } from 'vue'

const activeName = ref('list')
const fieldSelectedList = ref([])
provide('fieldSelectedList', fieldSelectedList)
const selectedItems = ref([])
</script>

<template>
  <el-tabs v-model="activeName" class="tabs">
    <el-tab-pane label="事件列表" name="list">
      <ListTab
        v-model:field-selected-list="fieldSelectedList"
        v-model:activeName="activeName"
        v-model:selected-items="selectedItems"
      />
    </el-tab-pane>
    <el-tab-pane label="事件关联" name="correlation">
      <CorrelationTab :selected-items="selectedItems" />
    </el-tab-pane>
  </el-tabs>
</template>

<style lang="scss" scoped>
.tabs {
  padding-left: 1vw;
  padding-right: 1vw;
  height: 100%;

  :deep(.el-tab-pane) {
    height: 100%;
  }
}
</style>
