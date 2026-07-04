<script setup lang="ts">
import * as d3 from 'd3'
import { computed, onMounted, reactive, ref, useTemplateRef, watch } from 'vue'
import { useListViewStore } from '@/stores/listViewStore'
//响应式 Props 解构,结构的props依然具有响应式，用于为基于类型的props声明定义默认值
const {
  svgClass = [],
  id = '',
  width = 0,
  text = '',
  linkIntensity = 0,
  count = 0,
  total = 0,
} = defineProps<{
  // class
  svgClass: string[]
  // 区分画布的id
  id: string
  // 获取画布的实际的客户端宽度
  width: number
  text: string
  // 连接强度
  linkIntensity?: number
  // 数量统计
  count?: number
  // 总的数量（包含重复）
  total?: number
}>()

const currentLinkIntensity = ref(0)
const currentCount = ref(0)

function initData() {
  currentCount.value = count ?? 0
  updateCount(count)
  currentLinkIntensity.value = linkIntensity ?? 0
  updateLinkIntensity(linkIntensity)
}

type SVGSelection = d3.Selection<SVGSVGElement, unknown, HTMLElement, any>
// 存储画布的一些属性
const svgState = reactive({
  // 画布
  svg: null as SVGSelection | null,
  height: 30,
  width: width,
})

watch(
  () => width,
  () => {
    svgState.width = width
  },
)

// 设置颜色比例尺，用于映射不同的连接强度
const colorScale = d3
  .scaleLinear()
  // 超过domain最大值时，d3会自动外推，除非手动设置clamp
  .domain([0, 5, 10, 20])
  .range(['white', 'lightyellow', 'yellow', 'orange'])

// 设置数量比例尺，映射不同的长度,
// 使用计算属性，映射不同的total
const countScale = computed(() => {
  return d3.scaleLinear().domain([0, total]).range([0, svgState.width])
})

const draw = () => {
  // 创建 SVG 容器
  svgState.svg = d3
    .select(`#${id}`)
    .append('svg')
    .attr('id', `svg-${id}`)
    // 展开数组 ['class1','class2',...]=>class:'class1 class2 ...'
    .attr('class', Array.isArray(svgClass) ? svgClass.join(' ') : svgClass)
    .attr('height', svgState.height)
    .attr('width', svgState.width)

  // 添加矩形元素
  svgState.svg
    .append('rect')
    .attr('class', 'element-rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', svgState.width)
    .attr('height', svgState.height)
    .attr('fill', colorScale(currentLinkIntensity.value))
    .attr('rx', 5)
    .attr('stroke', 'black')
    .attr('stroke-width', 1)

  // 添加文本元素（作为 SVG 的直接子元素）
  svgState.svg
    .append('text')
    .attr('x', 10)
    .attr('y', svgState.height / 2)
    .attr('dominant-baseline', 'middle')
    // 设置深色颜色的文字为白色，增强显示效果
    .attr('fill', currentLinkIntensity.value > 80 ? 'white' : 'black')
    .attr('font-family', 'Arial, sans-serif')
    .attr('font-size', '14px')
    .style('user-select', 'none') // 屏蔽文字的划词功能
    .text(text)

  svgState.svg
    .append('rect')
    .attr('class', 'count-rect')
    .attr('x', svgState.width - countScale.value(currentCount.value))
    .attr('y', svgState.height / 2 - 5)
    .attr('height', 10)
    .attr('width', countScale.value(currentCount.value))
    .attr('fill', 'black')
}

const addEvent = () => {
  // 添加鼠标事件
  svgState.svg
    .on('mouseover', function () {
      d3.select(this).style('cursor', 'pointer').select('.element-rect').attr('fill', 'lightblue')
    })
    .on('mouseout', function () {
      d3.select(this)
        .style('cursor', 'default')
        .select('.element-rect')
        .attr('fill', colorScale(currentLinkIntensity.value))
    })
    .on('click', clickEvent)
}

const listViewStore = useListViewStore()

function clickEvent() {
  if (listViewStore.addClickedNode(this)) {
    // 如果添加成功，即不是重复点击
    listViewStore.addLinePairAndDraw()
  }
}

const element = useTemplateRef('element')
onMounted(() => {
  if (element.value) {
    element.value.addEventListener('update-link-intensity', (event: any) =>
      handleUpdateLinkIntensity(event as CustomEvent<number>),
    )
    element.value.addEventListener('update-count', (event: any) =>
      handleUpdateCount(event as CustomEvent<number>),
    )
  }
  draw()
  addEvent()
  initData()
})

/**
 * 更新连接强度
 * @param newLinkIntensity 新的连接强度，可选，没传入的时候默认+1
 */
function updateLinkIntensity(newLinkIntensity?: number) {
  newLinkIntensity = newLinkIntensity ?? currentLinkIntensity.value + 1
  currentLinkIntensity.value = newLinkIntensity
  svgState.svg.select('.element-rect').attr('fill', colorScale(currentLinkIntensity.value))
}

/**
 * 更新数量
 * @param newCount 新的数量，可选，没传入的时候默认+1
 */
function updateCount(newCount?: number) {
  newCount = newCount ?? currentCount.value + 1
  currentCount.value = newCount
  svgState.svg
    .select('.count-rect')
    // 调整左边的开始点
    .attr('x', svgState.width - countScale.value(currentCount.value))
    // 调整宽度
    .attr('width', countScale.value(currentCount.value))
}

watch(
  () => count,
  (newVal) => {
    updateCount(newVal)
  },
)

watch(
  () => linkIntensity,
  (newVal) => {
    updateLinkIntensity(newVal)
  },
)

// 定义可以通过 DOM 事件触发的方法
function handleUpdateLinkIntensity(event: CustomEvent<number>) {
  updateLinkIntensity(event.detail)
}

function handleUpdateCount(event: CustomEvent<number>) {
  updateCount(event.detail)
}

const getCurrentCount = computed(() => currentCount.value)
const getCurrentLinkIntensity = computed(() => currentLinkIntensity.value)

defineExpose({
  updateLinkIntensity,
  updateCount,
  getCurrentCount,
  getCurrentLinkIntensity,
})
</script>

<template>
  <div ref="element" :id="id" />
</template>

<style scoped lang="scss"></style>
