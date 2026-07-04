<script setup lang="ts">
import { getOntologySystemOptions } from '@/views/ontology/ontologySystem'
import { reactive, ref, computed } from 'vue'

const checkedItems = defineModel()
const options = computed(() => {
  return getOntologySystemOptions()
})
const props = withDefaults(
  defineProps<{
    oneRowDisplayNum?: number
  }>(),
  {
    oneRowDisplayNum: 3,
  },
)
const selectedCell = reactive({ row: undefined, col: undefined })

const emits = defineEmits(['clickedItem'])

function handleCheckboxClicked(rowIndex, colIndex, item) {
  selectedCell.row = rowIndex
  selectedCell.col = colIndex
  emits('clickedItem', item)
}
</script>

<template>
  <el-checkbox-group v-model="checkedItems">
    <el-row v-for="(row, index) in Math.ceil(options.length / oneRowDisplayNum)" :gutter="40">
      <el-col v-for="(item, colIndex) in options.slice(
        index * oneRowDisplayNum,
        index * oneRowDisplayNum + oneRowDisplayNum,
      )" :key="item.value" :span="24 / oneRowDisplayNum" :class="{
          'selected-row': selectedCell.row === index && selectedCell.col === colIndex,
        }" @click="handleCheckboxClicked(index, colIndex, item)">
        <el-checkbox :label="item.value" class="checkbox-item" size="large">
          {{ item.label }}
        </el-checkbox>
      </el-col>
    </el-row>
  </el-checkbox-group>
</template>

<style scoped lang="scss">
:deep(.el-row) {
  padding-top: 10px;
  //height: 5vh;

  .el-col {
    height: 100%;
  }

  .selected-row {
    background-color: #e6f7ff;
    height: 100%;
  }
}
</style>
