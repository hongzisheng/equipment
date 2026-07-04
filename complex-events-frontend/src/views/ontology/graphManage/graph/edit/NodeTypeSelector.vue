<script setup lang="ts">
import { nodeLegend } from '@/views/ontology/graphManage/graph'
import nodeTypeTag from '@/views/ontology/graphManage/nodeTypeTag'

const selectedType = defineModel<string>()
</script>

<template>
  <div>
    <el-select v-model="selectedType">
      <el-option v-for="opt in nodeLegend" :value="opt.id">
        <template #default >
          <span class="option-span"  >
            <component :is="nodeTypeTag(opt.id)" />
          </span>
        </template>
      </el-option>
    </el-select>
  </div>
</template>

<style scoped lang="scss">
.option-span{
  display: block;
  width: 100%;
}
// 设置el-select 选中的时候的背景颜色
.is-selected{
  background-color: var(--my-system-primary-color-opacity);
}


:deep(.el-tag--info) {
  --el-tag-border-color: transparent;
}
</style>
