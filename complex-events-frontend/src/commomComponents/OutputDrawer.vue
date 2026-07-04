<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import { OutputStream } from '@/views/ontology/extract/index'
import { ref, watch } from 'vue'
import { Loading, SuccessFilled, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  finishedCount: number
  currentId: number|string
  completedFlag: boolean
}>()

const currentTabName = ref<string|number>(0)
watch(
  () => props.currentId,
  (newVal) => {
    currentTabName.value = newVal
  },
)

const visible = defineModel()
const output = defineModel<OutputStream[]>('output')
const emits = defineEmits(['closed'])
const handleClose = () => {
  ElMessageBox.confirm('确定要关闭吗？', 'Warning', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      visible.value = false
      output.value = []
      emits('closed')
    })
    .catch(() => {
      visible.value = true
    })
}
</script>

<template>
  <el-drawer v-model="visible" :before-close="handleClose">
    <template #header>
      <div class="header">
        <span>实时输出结果</span>
        <div class="icons">
          <el-icon class="is-loading" v-if="!completedFlag">
            <Loading />
          </el-icon>
          <el-icon
            style="color: orange"
            v-else-if="completedFlag && finishedCount !== output.length"
          >
            <WarningFilled />
          </el-icon>

          <el-icon style="color: green" v-else>
            <SuccessFilled />
          </el-icon>
          <span>{{ finishedCount }}/{{ output.length }}</span>
        </div>
      </div>
    </template>
    <el-tabs tab-position="left" style="height: 100%" v-model="currentTabName">
      <el-tab-pane v-for="(item, index) in output" :key="index" :label="item.id" :name="item.id">
        <div class="output">
          <pre>{{ item.content }}</pre>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-drawer>
</template>

<style scoped lang="scss">
:deep(.el-tabs__content) {
  overflow: auto !important;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .icons {
    display: flex;
    align-items: center;
    gap: 8px; // 图标和文本之间的间距
  }
}
</style>
