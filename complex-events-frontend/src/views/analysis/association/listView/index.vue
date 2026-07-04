<script setup lang="ts">
import OneList from '@/views/analysis/association/listView/Column/OneList.vue'
import { computed, onMounted, onUnmounted, useTemplateRef } from 'vue'
import { useListViewStore } from '@/stores/listViewStore'

defineOptions({ name: 'ListViewCard' })

const listViewStore = useListViewStore()
const svgContainer = useTemplateRef('svgRef')

onMounted(() => {
  listViewStore.setListViewSVGRef(svgContainer.value)
})

const columns = computed(() => {
  return listViewStore.listViewColumnCount
})
const columnsSpan = computed(() => {
  // el-rpw只有24个col单位
  return 24 / columns.value
})

onUnmounted(() => {
  listViewStore.cleanSVG()
  listViewStore.cleanSelectedOntologies()
})
</script>

<template>
  <el-card class="card">
    <el-row class="row" :gutter="50">
      <el-col v-for="i in columns" :span="columnsSpan" class="col-list">
        <OneList :order="i" />
      </el-col>
      <!-- 叠加的 SVG 层（用于画线） -->
      <svg class="connection-overlay" ref="svgRef" pointer-events="none"></svg>
    </el-row>
  </el-card>
</template>

<style scoped lang="scss">
.card {
  height: 100%;
  width: 100%;
  position: relative;

  .row {
    height: 100%;
    width: 100%;

    .col-list {
      height: 100%;
      width: 100%;
    }

    .connection-overlay {
      position: absolute;
      //padding-top: 5px;
      top: calc(7% + 5px);
      left: 0;
      width: 100%;
      // onelist 里面的 header 5% + header-options 2% 的高度
      height: 93%;
      pointer-events: none; /* 确保不影响底层点击 */
      z-index: 1;
      overflow: hidden;
    }
  }
}

.selector {
  width: 40%;
}

.input {
  width: 50%;
}
</style>
