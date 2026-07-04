<script>
import { getTableHeaderStyle } from '@/views/ontology/index.js'
import { getLabelByProp } from '@/views/ontology/ontologySystem.js'

export default {
  name: 'ToSelectList',
  methods: {
    getLabelByProp,
    getTableHeaderStyle,
    handleCurrentChange(val) {
      this.$emit('handleSelectionChange', val)
    },
  },
  props: {
    eventsListTableData: {
      type: Array,
      required: true,
      default: () => [],
    },
    selectedEventsList: {
      type: Array,
      default: () => [],
    },
  },
  // 从eventsList/index.vue 中得到注入
  inject: ['fieldSelectedList'],
}
</script>

<template>
  <el-card class="card">
    <el-table
      :data="eventsListTableData"
      :header-cell-style="getTableHeaderStyle"
      border
      class="table"
      highlight-current-row
      @current-change="handleCurrentChange"
    >
      <el-table-column
        v-for="prop in fieldSelectedList"
        :label="getLabelByProp(prop)"
        :prop="prop"
      />
    </el-table>
  </el-card>
</template>
<style lang="scss" scoped>
.card {
  height: 100%; // 继承父元素高度

  .table {
    height: 30vh;
  }
}
</style>
