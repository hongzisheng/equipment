<script setup lang="ts">
import { computed, nextTick, onMounted, ref, shallowRef, useTemplateRef, watch } from 'vue'
import { methodsList } from '@/views/ontology/eventsList'
import * as d3 from 'd3'

defineOptions({ name: 'CorrelationMethods' })

// 当前选中的方法
const currentMethod = shallowRef(methodsList[0])

// 定义每个方法对应的流动曲线配置
const flowPaths = [
  {
    id: 'method1',
    color: ['#60a5fa', '#3b82f6'],
    path: 'M0,0 C70,25 70,75 0,100',
  },
  {
    id: 'method2',
    color: ['#f97316', '#fb923c'],
    path: 'M0,0 C80,20 80,80 0,100',
  },
  {
    id: 'method3',
    color: ['#10b981', '#34d399'],
    path: 'M0,0 C60,15 60,85 0,100',
  },
  {
    id: 'method4',
    color: ['#8b5cf6', '#a78bfa'],
    path: 'M0,0 C50,30 50,70 0,100',
  },
]
const hoverColors = [
  'rgba(37, 99, 235, 0.55)', // 对应 index 0 的hover颜色
  'rgba(249, 115, 22, 0.55)', // 对应 index 1 的hover颜色
  'rgba(16, 185, 129, 0.55)', // 对应 index 2 的hover颜色
  'rgba(139, 92, 246, 0.55)', // 对应 index 3 的hover颜色
]
const activeColors = [
  'linear-gradient(135deg, #2563eb, #3b82f6)', // 对应 index 0 的active颜色
  'linear-gradient(135deg, #ea580c, #f97316)', // 对应 index 1 的active颜色
  'linear-gradient(135deg, #059669, #10b981)', // 对应 index 2 的active颜色
  'linear-gradient(135deg, #7c3aed, #8b5cf6)', // 对应 index 3 的active颜色
]

watch(currentMethod, (newMethod) => {
  drawFlowConnector()
})

const currentMethodIndex = computed<number>(() => {
  return methodsList.findIndex((m) => m.name === currentMethod.value.name)
})
const mainContentRef = useTemplateRef('mainContentRef')
const methodsRefList = ref([])
const flowConnectorRef = useTemplateRef('flowConnectorRef')

// 绘制流动连接区域
function drawFlowConnector() {
  // 确保 DOM 元素已加载
  if (!methodsRefList.value[currentMethodIndex.value] || !mainContentRef.value) {
    console.log('DOM 元素未加载，请稍后再试。')
    return
  }

  const currentMethodDOM = methodsRefList.value[currentMethodIndex.value]
  const mainDOM = mainContentRef.value

  // 获取元素相对于视窗的位置
  const leftRect = currentMethodDOM.getBoundingClientRect()
  const rightRect = mainDOM.getBoundingClientRect()
  const connectorRect = flowConnectorRef.value.getBoundingClientRect()
  // 添加尺寸检查
  if (connectorRect.width === 0 || connectorRect.height === 0) {
    console.log('连接区域尺寸为0，稍后重试')
    // 延迟重试
    setTimeout(drawFlowConnector, 50)
    return
  }
  // 计算相对坐标 - 左侧元素的顶部和底部 - 圆角radius
  const yLeftTop = leftRect.top - connectorRect.top + 16
  const yLeftBottom = leftRect.bottom - connectorRect.top - 16

  // 计算相对坐标 - 右侧元素的顶部和底部
  const yRightTop = rightRect.top - connectorRect.top
  const yRightBottom = rightRect.bottom - connectorRect.top

  // 清除之前的绘制内容
  d3.select(flowConnectorRef.value).select('svg').remove()

  // 创建 SVG 容器
  const svg = d3
    .select(flowConnectorRef.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${connectorRect.width} ${connectorRect.height}`)
    .attr('preserveAspectRatio', 'none')

  // 定义渐变色
  const gradientId = `gradient-${currentMethodIndex.value}`
  const gradient = svg
    .append('defs')
    .append('linearGradient')
    .attr('id', gradientId)
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '100%')
    .attr('y2', '0%')

  gradient
    .append('stop')
    .attr('offset', '0%')
    .attr('stop-color', flowPaths[currentMethodIndex.value].color[0])
    .attr('stop-opacity', '0.4')

  gradient
    .append('stop')
    .attr('offset', '100%')
    .attr('stop-color', flowPaths[currentMethodIndex.value].color[1])
    .attr('stop-opacity', '0.1')

  // 定义第一条曲线路径：连接左侧顶部到右侧顶部
  const path1 = d3.path()
  path1.moveTo(0, yLeftTop)
  path1.bezierCurveTo(
    connectorRect.width * 0.7,
    yLeftTop,
    connectorRect.width * 0.3,
    yRightTop,
    connectorRect.width,
    yRightTop,
  )

  // 定义第二条曲线路径：连接左侧底部到右侧底部
  const path2 = d3.path()
  path2.moveTo(0, yLeftBottom)
  path2.bezierCurveTo(
    connectorRect.width * 0.7,
    yLeftBottom,
    connectorRect.width * 0.3,
    yRightBottom,
    connectorRect.width,
    yRightBottom,
  )

  // 创建封闭区域路径（连接两条曲线）
  const areaPath = d3.path()
  areaPath.moveTo(0, yLeftTop)
  areaPath.bezierCurveTo(
    connectorRect.width * 0.7,
    yLeftTop,
    connectorRect.width * 0.3,
    yRightTop,
    connectorRect.width,
    yRightTop,
  )
  areaPath.lineTo(connectorRect.width, yRightBottom)
  areaPath.bezierCurveTo(
    connectorRect.width * 0.3,
    yRightBottom,
    connectorRect.width * 0.7,
    yLeftBottom,
    0,
    yLeftBottom,
  )
  areaPath.closePath()

  // 绘制填充区域
  svg
    .append('path')
    .attr('d', areaPath.toString())
    .attr('fill', `url(#${gradientId})`)
    .attr('stroke', 'none')

  // 绘制第一条曲线（顶部连接）
  svg
    .append('path')
    .attr('d', path1.toString())
    .attr('stroke', flowPaths[currentMethodIndex.value].color[0])
    .attr('stroke-width', 2)
    .attr('fill', 'none')
    .attr('opacity', 0.7)

  // 绘制第二条曲线（底部连接）
  svg
    .append('path')
    .attr('d', path2.toString())
    .attr('stroke', flowPaths[currentMethodIndex.value].color[1])
    .attr('stroke-width', 1.5)
    .attr('fill', 'none')
    .attr('opacity', 0.5)
}

onMounted(() => {
  currentMethod.value = methodsList[0]
  // 延迟绘制直到DOM更新完成
  nextTick(() => {
    drawFlowConnector()
  })
})

const props = defineProps<{
  selectedItems: []
}>()
</script>

<template>
  <div class="correlation-layout">
    <!-- 左侧控制栏 -->
    <div class="control-bar">
      <div
        v-for="(method, index) in methodsList"
        :key="method.name"
        class="control-card"
        :class="{ active: currentMethod.name === method.name }"
        @click="currentMethod = method"
        :style="{
          '--hover-bg-color': hoverColors[index],
          '--active-bg-color': activeColors[index],
        }"
        :ref="
          (el) => {
            if (el) methodsRefList[index] = el
          }
        "
      >
        <h3>{{ method.name }}</h3>
        <p class="desc">配置 {{ method.name }} 参数</p>
      </div>
    </div>

    <!-- 中间流动连接区域 -->
    <div class="flow-connector" ref="flowConnectorRef" />

    <!-- 右侧主界面 -->
    <div class="main-content" ref="mainContentRef">
      <transition name="scale-fade" mode="out-in">
        <component
          :is="currentMethod.component"
          :key="currentMethod.name"
          :selected-items="selectedItems"
        />
      </transition>
    </div>
  </div>
</template>

<style scoped lang="scss">
.correlation-layout {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
  position: relative;
}
/* 左侧控制栏 */
.control-bar {
  width: 20%;
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
  z-index: 2;
}

.control-card {
  flex: 1; /* 平均分配剩余空间 */
  display: flex;
  flex-direction: column;
  justify-content: center; /* 垂直居中内容 */
  width: 85%;
  background: #757575;
  border-radius: 1rem;
  margin: 0.5rem auto; /* 水平居中 */
  padding: 1rem;
  color: #e2e8f0;
  cursor: pointer;
  text-align: center;
  transition: all 0.3s ease;

  &:hover {
    background: var(--hover-bg-color, rgba(37, 99, 235, 0.55)); // 默认颜色作为后备
    transform: translateX(4px);
  }

  &.active {
    background: var(
      --active-bg-color,
      linear-gradient(135deg, #2563eb, #3b82f6)
    ); // 默认颜色作为后备
    color: white;
    transform: scale(1.05);
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
  }

  h3 {
    font-size: 1rem;
    margin-bottom: 0.4rem;
  }

  .desc {
    font-size: 0.8rem;
    opacity: 0.8;
  }
}

/* 中间流动区 */
.flow-connector {
  width: 5%;
  height: 100%;
  position: relative;
  z-index: 1;
  overflow: hidden;
  margin-left: -1.5vw;

  svg {
    width: 100%;
    height: 100%;
  }
}

/* 主界面 */
.main-content {
  width: 75%;
  height: 100%;
  background: #f8fafc;
  padding: 1.5rem;
  overflow: hidden;
  border-radius: 16px;
}

/* 动画 */
.scale-fade-enter-active,
.scale-fade-leave-active,
.path-fade-enter-active,
.path-fade-leave-active {
  transition: all 0.6s ease;
}

.scale-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.scale-fade-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

.path-fade-enter-from,
.path-fade-leave-to {
  opacity: 0;
  transform: translateX(-10%);
}
</style>
