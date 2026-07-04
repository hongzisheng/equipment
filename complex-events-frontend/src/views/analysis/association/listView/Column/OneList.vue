<script setup lang="ts">
import OntologySelector from '@/commomComponents/OntologySelector.vue'
import { computed, nextTick, ref, useTemplateRef, watch } from 'vue'
import { useMapStore } from '@/stores/mapStore'
import OneOntology from '@/views/analysis/association/listView/Column/elements/OneOntology.vue'
import { Plus } from '@element-plus/icons-vue'
import { useListViewStore } from '@/stores/listViewStore'
import { SortIcon } from '@/views/analysis/association/listView/Column/elements/Sort'
import { ElScrollbar } from 'element-plus'

const keyReportDict = ref({})
// 这个list算上重复项有多少个，用于频次统计的时候的domain
const totalCount = ref(0)
const selectedProp = ref()
const detailsList = ref()
const mapStore = useMapStore()
const eventsTableData = computed(() => mapStore.eventsListTableData)
watch(selectedProp, () => {
  keyReportDict.value = {}
  // 先清除元素强度
  listViewStore.cleanSVG()
  // 再清除元素
  listViewStore.cleanElements()

  // 提取每一行的数据
  eventsTableData.value.forEach((item) => {
    const values = item[selectedProp.value].split(',')
    values.forEach((value) => {
      const valueKey = value.trim()
      if (Object.keys(keyReportDict.value).some((key) => key === valueKey)) {
        keyReportDict.value[valueKey].push(item.reportId)
      } else {
        keyReportDict.value[valueKey] = [item.reportId]
      }
    })
  })
  detailsList.value = Object.keys(keyReportDict.value)
  // 值是数组，提取所有values是[[values1],[values2]]，经过一次拍扁再计算长度
  totalCount.value = Object.values(keyReportDict.value).flat().length
  sortedDetailsList.value = detailsList.value
})

const scrollbarRef = useTemplateRef<InstanceType<typeof ElScrollbar>>('scrollbarRef')
const listContainerRef = useTemplateRef('listContainerRef')
const width = computed(() => {
  return listContainerRef.value.clientWidth - 15
})

const listViewStore = useListViewStore()

const props = defineProps<{
  // 顺序的序号，从1开始
  order: number
}>()
// 监听本体选择
watch(selectedProp, (newValue) => {
  listViewStore.selected(props.order, newValue)
})

// 存储组件实例的引用
const ontologyRefs = ref({})
// 生成唯一key
const getItemKey = (item) => {
  return `${selectedProp.value}-${item}`
}
// 设置组件引用
const setOntologyRef = (el, item) => {
  const key = getItemKey(item)
  if (el) {
    ontologyRefs.value[key] = el
  }
}
const sortType = ref<number>(0)
const sortedDetailsList = ref([])

function sortByLinkIntensity() {
  // 滚动到顶部
  scrollbarRef.value.setScrollTop(0)
  // 切换成下一种排序方式,总共3种，下标0，1，2
  sortType.value = sortType.value < 2 ? sortType.value + 1 : 0
  if (!detailsList.value || detailsList.value.length === 0) {
    return
  }
  if (sortType.value == 0) {
    // default sort
    sortedDetailsList.value = detailsList.value
  } else {
    // type 1 : descending
    // type 2 : ascending
    sortedDetailsList.value = [...detailsList.value].sort((a, b) => {
      const keyA = getItemKey(a)
      const keyB = getItemKey(b)

      const intensityA = ontologyRefs.value[keyA]?.getCurrentLinkIntensity || 0
      const intensityB = ontologyRefs.value[keyB]?.getCurrentLinkIntensity || 0
      console.log(keyA)

      return sortType.value == 1 ? intensityB - intensityA : intensityA - intensityB
    })
  }

  nextTick(() => {
    listViewStore.drawLines()
  })
}

function generateClassList(key: string) {
  const reportIds = keyReportDict.value[key]
  return reportIds.map((id: string) => {
    return selectedProp.value + '&' + id
  })
}
</script>

<template>
  <div class="header">
    <OntologySelector
      class="selector"
      v-model="selectedProp"
      selected-prop
      :disabled-items="listViewStore.selectedOntologyObjects"
    />
    <el-input class="input" />
  </div>
  <div class="header-options">
    <el-button type="text">
      <el-icon>
        <Plus />
      </el-icon>
    </el-button>
    <el-button type="text" @click="sortByLinkIntensity">
      <component :is="SortIcon(sortType)" />
    </el-button>
  </div>
  <el-scrollbar ref="scrollbarRef" class="list-scrollbar" @scroll="listViewStore.drawLines()">
    <ul class="list-container" ref="listContainerRef">
      <li v-for="(item, index) in sortedDetailsList" :key="item" class="list-item">
        <OneOntology
          :ref="(el) => setOntologyRef(el, item)"
          :svg-class="generateClassList(item)"
          :id="selectedProp + index"
          :text="item"
          :width="width"
          :count="keyReportDict[item].length"
          :total="totalCount"
        />
      </li>
    </ul>
  </el-scrollbar>
</template>

<style scoped lang="scss">
.header {
  height: 5%;
  width: 100%;
  display: flex;
  gap: 20px; /* 添加元素间距 */
  align-items: center; /* 垂直居中对齐 */
}

.header-options {
  display: flex;
  // 靠右对齐
  justify-content: flex-end;
  width: 100%;
  height: 2%;
}

.selector {
  width: 40%;
}

.input {
  width: 50%;
}

.list-scrollbar {
  margin: 10px 0 0 0;
  height: 93%;
  width: 100%;

  .list-container {
    padding: 0;
    margin: 0;
  }
}

.list-item {
  padding: 5px 0;
  list-style: none;
  border-bottom: 1px solid #eee;
}

.list-item:last-child {
  border-bottom: none;
}
</style>
