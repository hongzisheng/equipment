<script setup>
import fileApi from '@/api/fileApi.js'
import { ElMessage } from 'element-plus'
import { getTableHeaderStyle } from '@/views/ontology/index.js'
import OntologyConfigSelector from '@/commomComponents/OntologyConfigSelector.vue'
import { onMounted, reactive, ref, watch } from 'vue'

/**
 * 文件选择卡片，选择需要提取的数据
 */
defineOptions({
  name: 'FileSelectCard',
})
const tableData = ref([])
const total = ref(0)
const searchModel = reactive({
  pageNo: 1,
  pageSize: 20,
})
const tableLoading = ref(false)

onMounted(() => {
  getFileList()
})

function handleCurrentChange(pageNo) {
  searchModel.pageNo = pageNo
  getFileList()
}

function getFileList() {
  fileApi
    .getFileList(searchModel)
    .then((response) => {
      tableData.value = response.data.rows // 回调用户数据
      tableData.value = tableData.value.map((row) => {
        // 添加记录本体配置的数据列
        return {
          ...row,
          config: undefined,
        }
      })
      total.value = response.data.total // 回调统计值
    })
    .catch((error) => {
      console.error(error)
      ElMessage.error('获取失败')
    })
    .finally(() => {
      tableLoading.value = false
    })
}

const props = defineProps({
  selectedItems: {
    type: Array,
    default: () => [],
  },
})

const emits = defineEmits(['selectedItemsChanged'])
const handleSelectionChange = (newSelectedItems) => {
  emits('selectedItemsChanged', newSelectedItems)
}

// 批量选择
const batchConfigSelected = ref('')
watch(batchConfigSelected, () => {
  tableData.value.forEach((row) => {
    row.config = batchConfigSelected.value
  })
})
</script>

<template>
  <el-card>
    <template #header>
      <div class="title">
        <label>数据选择</label>
      </div>
    </template>
    <div class="table-container">
      <el-table
        :data="tableData"
        :header-cell-style="getTableHeaderStyle"
        :show-overflow-tooltip="true"
        border
        class="table"
        @selectionChange="handleSelectionChange"
      >
        <el-table-column
          width="5%"
          type="selection"
          :selectable="(row) => row.config !== undefined"
        />
        <el-table-column label="ID" prop="id" width="15%" />
        <el-table-column label="文件名" prop="title" width="45%" />
        <el-table-column label="上传/爬取时间" prop="date" width="15%" />
        <el-table-column label="操作" width="20%">
          <template #header>
            <div class="opt-hearer" style="display: flex; align-items: center">
              <span style="width: 30%">操作</span>
              <OntologyConfigSelector style="width: 70%" v-model="batchConfigSelected" />
            </div>
          </template>
          <template #default="scoped">
            <OntologyConfigSelector v-model="scoped.row.config" />
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        :total="total"
        background
        class="pagination"
        layout="slot,-> , pager,jumper "
        size="small"
        @current-change="handleCurrentChange"
      >
        <template #default>
          <span>已选中 {{ selectedItems.length }} / {{ searchModel.pageSize }} </span>
        </template>
      </el-pagination>
    </div>
  </el-card>
</template>

<style lang="scss" scoped>
.table-container {
  height: 30vh;
  width: 100%;

  .table {
    height: 90%;
    // 设置表头宽度
    :deep(.el-table__header-wrapper) {
      .el-table__header {
        width: 100% !important;
      }
    }

    // 设置表体宽度
    :deep(.el-table__body-wrapper) {
      .el-table__body {
        width: 100% !important;

        .el-table__row {
          .cell {
            width: 100% !important;
          }
        }
      }
    }
  }

  .pagination {
    padding-top: 5%;
    width: 100%;
    height: 10%;
  }
}
</style>
