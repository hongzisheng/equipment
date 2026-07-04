import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import * as d3 from 'd3'
import { useOntologyStore } from '@/stores/ontologyStore'

const ontologyStore = useOntologyStore()

export const useListViewStore = defineStore('listViewStore', () => {
  // listview的svg的画布，主要用于绘制连接线，是一个大的画布
  const listViewSVGRef = ref<SVGSVGElement>(null)

  // 设置svg,用于初始化
  function setListViewSVGRef(svg: SVGSVGElement) {
    listViewSVGRef.value = svg
  }

  // 清空svg
  function cleanSVG() {
    listViewSVGRef.value.innerHTML = ''
    const allElements = elementsLine.value.flatMap((line) => [line.startElement, line.endElement])
    // 清空所有元素的强度
    allElements.forEach((el) => {
      updateLinkIntensity(el, 0)
    })
  }

  // list view 的列的个数
  const listViewColumnCount = ref(3)

  // listview中选择了哪些本体展示
  const selectedOntologies = ref<string[]>([])

  function cleanSelectedOntologies() {
    for (let i = 0; i < selectedOntologies.value.length; i++) {
      selectedOntologies.value[i] = ''
    }
  }

  // 初始化本体选择数组
  watch(
    listViewColumnCount,
    () => {
      if (selectedOntologies.value.length >= listViewColumnCount.value) {
        // 还是等于原来的列数,超出的部分删掉
        selectedOntologies.value = selectedOntologies.value.slice(0, listViewColumnCount.value)
      } else {
        // 补齐不足的部分，初始化为‘’，空字符串
        selectedOntologies.value = selectedOntologies.value.concat(
          Array(listViewColumnCount.value - selectedOntologies.value.length).fill(''),
        )
      }
    },
    { immediate: true },
  )
  const selectedOntologyObjects = computed(() => {
    const result = []
    selectedOntologies.value.forEach((prop) => {
      if (prop && prop != '') {
        result.push(ontologyStore.getAllOntologyObject.find((item) => item.prop == prop))
      }
    })
    return result
  })

  function selected(order: number, ontology: string) {
    selectedOntologies.value[order - 1] = ontology
  }

  // 鼠标选中了哪些节点
  const clickedNodes = ref<SVGElement[]>([])

  // 根据是否添加成功返回bool类型
  function addClickedNode(node: SVGElement): boolean {
    if (clickedNodes.value.some((n) => n.getAttribute('id') == node.getAttribute('id'))) {
      // 存在的时候不添加
      console.log('已存在')
      return false
    } else {
      clickedNodes.value.push(node)
      return true
    }
  }

  // 存储两个元素连接线的一对数据
  const elementsLine = ref<{ startElement: SVGElement; endElement: SVGElement }[]>([])

  function cleanElements() {
    elementsLine.value = []
    clickedNodes.value = []
  }

  function addLinePairAndDraw() {
    // 遍历点击的节点
    clickedNodes.value.forEach((clickedNodeElement: SVGElement) => {
      // 一个svg (this)具有多个类名
      const reportIds = getNodeReportId(clickedNodeElement)
      // 找到整个页面上的相同的，包含有reportid的class的元素
      const sameIdElements = []
      reportIds.forEach((id) => {
        sameIdElements.push(...Array.from(document.querySelectorAll(`[class*="${id}"]`)))
      })
      sameIdElements.forEach((element) => {
        addLinePair(clickedNodeElement, <SVGElement>element)
      })
    })
    // 添加完成之后触发绘制
    drawLines()
  }

  function addLinePair(startElement: SVGElement, endElement: SVGElement) {
    // 获取元素的类名称
    const startProp = getNodeProp(startElement)[0]
    const endProp = getNodeProp(endElement)[0]
    if (startProp == endProp) {
      // 不能连接自己
      return
    }
    // 判断是不是相邻的list
    const indexNeighbor =
      selectedOntologies.value.indexOf(startProp) - selectedOntologies.value.indexOf(endProp)
    if (indexNeighbor == -1) {
      // 正常情况，开始在结束的左边
      elementsLine.value.push({
        startElement: startElement,
        endElement: endElement,
      })
    } else if (indexNeighbor == 1) {
      // 另一种清空，开始在结束的右边
      elementsLine.value.push({
        startElement: endElement,
        endElement: startElement,
      })
    }
  }

  /**
   * class生成规则见
   * @see src/views/analysis/association/listView/Column/elements/OneOntology.vue generateClassList
   */
  function getElementClass(element: Element): string[] {
    return element.getAttribute('class').split(' ')
  }

  function getNodeProp(element: Element): string[] {
    return getElementClass(element).map((name) => {
      return name.split('&')[0]
    })
  }

  function getNodeReportId(element: Element) {
    return getElementClass(element).map((name) => {
      return name.split('&')[1]
    })
  }

  function updateLinkIntensity(element: Element, newIntensity?: number) {
    element.parentElement.dispatchEvent(
      new CustomEvent('update-link-intensity', {
        detail: newIntensity,
      }),
    )
  }

  function updateCount(element: Element, newCount?: number) {
    element.parentElement.dispatchEvent(
      new CustomEvent('update-count', {
        detail: newCount,
      }),
    )
  }

  // 绘制连接线
  function drawLines() {
    // 画之前先清空画布，避免重复绘制
    cleanSVG()
    elementsLine.value.forEach((linePair) => {
      connectElementsWithLine(linePair.startElement, linePair.endElement)
      updateLinkIntensity(linePair.startElement)
      updateLinkIntensity(linePair.endElement)
    })
  }

  // 绘制一条线，连接两个元素
  function connectElementsWithLine(element1, element2) {
    // 1. 获取两个元素在页面中的位置（中心点）
    const rect1 = element1.getBoundingClientRect()
    const rect2 = element2.getBoundingClientRect()

    // 2. 获取 SVG 容器的位置
    const svgRect = listViewSVGRef.value.getBoundingClientRect()

    // 3. 将视口坐标转换为 SVG 容器内的相对坐标
    const x1 = rect1.right - svgRect.left
    const y1 = rect1.top + rect1.height / 2 - svgRect.top

    const x2 = rect2.left - svgRect.left
    const y2 = rect2.top + rect2.height / 2 - svgRect.top

    d3.select(listViewSVGRef.value)
      .append('line')
      .attr('x1', x1)
      .attr('y1', y1)
      .attr('x2', x2)
      .attr('y2', y2)
      .style('stroke', '#DAA520')
      .style('stroke-width', '1')
  }

  function $reset() {
    selectedOntologies.value = []
    clickedNodes.value = []
    elementsLine.value = []
  }

  return {
    listViewSVGRef,
    setListViewSVGRef,
    cleanSVG,
    cleanElements,
    $reset,
    listViewColumnCount,
    selectedOntologies,
    cleanSelectedOntologies,
    selected,
    clickedNodes,
    addClickedNode,
    drawLines,
    elementsLine,
    addLinePair,
    addLinePairAndDraw,
    getElementClass,
    getNodeProp,
    getNodeReportId,
    selectedOntologyObjects,
  }
})
