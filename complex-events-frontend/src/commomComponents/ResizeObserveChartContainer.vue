<template>
  <div ref="container" class="chart-container">
    <!-- 你的 SVG 或 canvas 放在这里 -->
    <slot :width="width" :height="height" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, useTemplateRef } from 'vue'

const container = useTemplateRef('container')
let resizeObserver = null
const width = ref(0)
const height = ref(0)
const emits = defineEmits<{
  sizeChanged: [{ height: number; width: number }]
}>()

// 获取当前容器尺寸并执行绘制逻辑
const redraw = () => {
  if (!container.value) return

  const newWidth = container.value.clientWidth
  const newHeight = container.value.clientHeight

  // 只有当尺寸发生实质性变化时才触发更新
  if (Math.abs(newWidth - width.value) > 1 || Math.abs(newHeight - height.value) > 1) {
    width.value = newWidth
    height.value = newHeight

    if (width.value > 0 && height.value > 0) {
      emits('sizeChanged', { height: height.value, width: width.value })
      console.log('sizeChanged', { height: height.value, width: width.value })
    }
  }
}
defineExpose({
  width: width,
  height: height,
})
onMounted(() => {
  // 初始绘制
  redraw()

  // 创建 ResizeObserver 监听容器尺寸变化
  resizeObserver = new ResizeObserver(() => {
    redraw()
  })
  resizeObserver.observe(container.value)
})

onUnmounted(() => {
  // 清理监听器，防止内存泄漏
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  position: relative;
  max-height: 100vh;
  max-width: 100vw;
}
</style>
