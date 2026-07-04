<template>
  <div class="card-container">
    <el-card id="info-card-events-list">
      <label style="height: 5%">事件列表</label>
      <el-table
        class="table"
        :data="eventsListTableData"
        :header-cell-style="getTableHeaderStyle"
        :height="paginationHidden ? '95%' : '90%'"
        :row-class-name="tableRowClassName"
        @row-click="handleRowClick"
      >
        <el-table-column fixed width="50">
          <template #default="scoped">
            <div :style="getCellStyle(scoped.$index)">
              {{ scoped.$index + 1 }}
            </div>
          </template>
        </el-table-column>
        <el-table-column
          v-for="col in colOpts"
          :prop="col.prop"
          :label="col.label"
          :fixed="col?.fixed"
          show-overflow-tooltip
        >
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="!paginationHidden"
        background
        class="pagination"
        layout="total, prev, pager, next"
        :total="total"
        :pager-count="3"
        small
        @current-change="
          (currentPage: number) => {
            mapStore.setCurrentPage(currentPage)
          }
        "
      />

      <!-- Tooltip 弹窗 -->
      <el-popover
        ref="rowTooltip"
        placement="left"
        :visible="tooltipVisible"
        virtual-triggering
        :virtual-ref="tooltipTriggerRef"
        :width="autoWidth"
        popper-class="auto-size-popover"
      >
        <template #default>
          <div class="tooltip-content" v-html="currentReportDetails.details" ref="contentRef"></div>
        </template>
      </el-popover>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { getTableHeaderStyle } from '@/views/ontology'
import { getOntologySystemOptions } from '@/views/ontology/ontologySystem'
import { useMapStore } from '@/stores/mapStore'
import { storeToRefs } from 'pinia'
import fileApi from '@/api/fileApi'

defineProps<{
  paginationHidden?: boolean
}>()

const mapStore = useMapStore()
const eventsListTableData = computed(() => mapStore.eventsListTableData)
const total = computed(() => mapStore.total)
const colOpts = getOntologySystemOptions()

// Tooltip 相关变量
const tooltipVisible = ref(false)
const tooltipTriggerRef = ref()
const currentRowData = ref<any>(null)
const contentRef = ref<HTMLDivElement | null>(null)
const autoWidth = ref<string | number>('auto')
let currentReportDetails = reactive<{ details: string }>({ details: '' })

// 表格行的类名处理
const tableRowClassName = ({ row }: { row: any }) => {
  return 'event-row'
}

const getCellStyle = (index: number) => {
  const bgColor = mapStore.getColor(index)
  return {
    background: bgColor,
    color: mapStore.getContrastColor(bgColor),
    display: 'flex',
    'justify-content': 'center',
  }
}
// 鼠标进入行事件
const handleRowClick = (row, col, e: MouseEvent) => {
  if (tooltipVisible.value) {
    // 再次点击关闭，在打开的状态下单击
    tooltipVisible.value = false
  } else {
    const target = e.target as HTMLElement
    const rowElement = target.closest('.event-row') as HTMLElement

    if (rowElement) {
      currentRowData.value = row
      tooltipTriggerRef.value = rowElement

      const reportId = row['reportId']
      fileApi.searchById(reportId).then((res) => {
        currentReportDetails.details = res.data.details
        tooltipVisible.value = true

        // 在内容更新后重新计算尺寸
        nextTick(() => {
          if (contentRef.value) {
            const contentWidth = contentRef.value.scrollWidth
            const contentHeight = contentRef.value.scrollHeight

            // 可以根据需要设置最大宽高限制
            autoWidth.value = Math.min(contentWidth + 20, 600) // 添加一些padding
            // 高度可以通过CSS max-height 控制
          }
        })
      })
    }
  }
}
</script>

<style scoped lang="scss">
.card-container {
  width: 100%;
  height: 100%;

  #info-card-events-list {
    width: 100%;
    height: 100%;

    .table {
      padding-top: 10px;
      height: 95%;
    }

    .pagination {
      height: 5%;

      :deep(.el-pagination) {
        width: auto;
      }

      :deep(.el-pager) {
        width: auto;
      }
    }
  }
}

.tooltip-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;
}

// 自定义 popover 样式以支持自适应大小
:deep(.auto-size-popover) {
  max-width: 600px;
  max-height: 500px;
  overflow: visible;

  .el-popover__reference-wrapper {
    display: block;
  }
}
</style>
