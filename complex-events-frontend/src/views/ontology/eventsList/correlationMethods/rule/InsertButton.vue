<script setup lang="ts">
import { ref, computed, useTemplateRef, nextTick, watch, onMounted } from 'vue'
import { getOntologySystemOptions } from '@/views/ontology/ontologySystem'



// 状态：是否显示下拉
const isSelecting = ref(false)

// 按钮点击：展开下拉
const openSelect = () => {
  isSelecting.value = true
}
// 计算下拉宽度（与按钮一致）
const selectWidth = ref(0)
const onButtonMounted = (el: HTMLElement) => {
  selectWidth.value = el.offsetWidth
}
const emits =  defineEmits<{
  selectedChanged:[value:string]
}>()
function handleSelectChanged(value:string){
  emits('selectedChanged',value)
  isSelecting.value = false
}

const options = ref([])
onMounted(()=>{
  options.value = getOntologySystemOptions()
})

</script>

<template>
  <div class="toggle-select-wrapper" >
    <!-- 按钮状态 -->
    <Transition name="fade" mode="out-in">
      <el-button
        v-if="!isSelecting"
        ref="buttonRef"
        class="toggle-btn"
        @click="openSelect"
      >
        插入实体
      </el-button>

      <!-- 下拉选择状态 -->
      <el-select
        v-else
        ref="selectRef"
        class="select-native"
        @change="handleSelectChanged"
        @blur="isSelecting = false"
      >
        <el-option value="" label="请选择..." disabled />
        <el-option v-for="opt in options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </el-option>
      </el-select>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.toggle-select-wrapper {
  display: inline-block;
  position: relative;
}

.toggle-btn,
.toggle-select {
  width: 100%;
  height: 36px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  border-color: #409eff;
}

.select-native {
  width: 100%;
  height: 36px;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #606266;
  padding: 0 10px;
  appearance: none; /* 隐藏默认箭头（可选） */
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
