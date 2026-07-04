<script setup lang="ts">
import { defineModel, onMounted, ref } from 'vue'
import { getTableHeaderStyle } from '@/views/ontology/index.js'
import {
  getLabelByProp,
  getOntologySystemOptions,
  getIdByLable,
  OntologySystemData,
} from '@/views/ontology/ontologySystem.ts'
import { Connection, Delete, Document, Edit, Plus, View } from '@element-plus/icons-vue'
import dataApi from '@/api/dataApi.js'
import { formattedExtractResult } from '@/views/ontology/extract/index'
import OntologySelector from '@/commomComponents/OntologySelector.vue'
import EventDetail from '@/views/ontology/eventsList/listTab/EventDetail.vue'
import SvgIcon from '@/components/SvgIcon/index.vue'
import graphApi from '@/api/graphApi.js'
import { ElMessage } from 'element-plus'
import fileApi from '@/api/fileApi'
import { Response } from '@/api'

const drawer = ref(false)
const current_event_item = ref({})
const searchText = ref('')
const EditDialogVisible = ref(false)
const editItem = ref()

// 定义双向绑定 v-model 值
// 字段选择
const fieldSelectedList = defineModel<string[]>('fieldSelectedList', { required: true })
// 标签页页面，用于跳转到另一个标签页
const activeName = defineModel('activeName', { default: 'list' })
// 勾选哪些行
const selectedItems = defineModel<OntologySystemData[]>('selectedItems', { default: [] })

// 点击关联数据的时候前往关联
const headCorrelation = () => {
  console.log('headCorrelation')
  activeName.value = 'correlation'
}
// 选中的行改变的时候触发
const handleSelectionChange = (selectedArray) => {
  selectedItems.value = selectedArray
}
// 数据展示数组
const eventsListTableData = ref([])
const filteredFullList = ref([])
const filterEventsListTableData = ref([])
// 总共多少条
const total = ref(0)

onMounted(() => {
  fetchData(0)
})

const fetchData = (startNum) => {
  dataApi.getDataList().then((res) => {
    eventsListTableData.value = res.list
    filteredFullList.value = eventsListTableData.value.map((item) => {
      return formattedExtractResult(item)
    })
    total.value = res.total
    filterEventsListTableData.value = filteredFullList.value.slice(
      startNum * 10,
      startNum * 10 + pageSize,
    )
  })
  if (fieldSelectedList.value && fieldSelectedList.value.length == 0) {
    fieldSelectedList.value.push(getOntologySystemOptions()[0].prop)
  }
}

const selected = ref('')
const selectedField = ref([])

const pageSize = 10

const handleCurrentChange = (currentPage) => {
  const startIndex = pageSize * (currentPage - 1)
  const endIndex = startIndex + pageSize
  filterEventsListTableData.value = filteredFullList.value.slice(startIndex, endIndex)
}
const handleView = (data) => {
  current_event_item.value = data
  drawer.value = true
}
const handleEdit = (data) => {
  const dataId = data.reportId
  const matched = eventsListTableData.value.find((item) => {
    return item.id === dataId
  })
  if (matched) {
    editItem.value = matched
    console.log(editItem.value)
  } else {
    editItem.value = null
    console.warn('没有在 eventsListTableData 中找到 id =', dataId)
  }
  EditDialogVisible.value = true
}

const handleDelete = (data) => {
  const dataId = data.reportId
  dataApi
    .postDeleteId(dataId)
    .then((res) => {
      fetchData(0)
    })
    .catch((err) => {
      console.error('删除失败：', err)
    })
}

const handleConfirmEdit = () => {
  console.log(editItem.value)
  dataApi
    .postEditItem(editItem.value)
    .then((res) => {
      fetchData(0)
    })
    .catch((err) => {
      console.error('修改失败：', err)
    })
  EditDialogVisible.value = false
}

const handleRetrieval = () => {
  const selectedProp = getIdByLable(selected.value)
  const key = selectedProp
  const keyword = searchText.value.trim().toLowerCase()
  const casEventList = eventsListTableData.value.map((item) => {
    return formattedExtractResult(item)
  })
  if (!key || keyword === '') {
    filteredFullList.value = casEventList.slice()
  } else {
    filteredFullList.value = casEventList.filter((item) => {
      const v = item[key]
      if (v == null) return false
      return String(v).toLowerCase().includes(keyword)
    })
  }
  total.value = filteredFullList.value.length
  filterEventsListTableData.value = filteredFullList.value.slice(0, pageSize)
}
const rebuildLoading = ref(false)

function rebuildGraph() {
  rebuildLoading.value = true
  graphApi
    .rebuild()
    .then((res) => {
      if (res.code === 20000) {
        ElMessage.success('重建成功')
      }
    })
    .catch((err) => {
      ElMessage.error('重建失败' + err.toString())
    })
    .finally(() => {
      rebuildLoading.value = false
    })
}

const building = ref(false)

function buildGuild() {
  building.value = true
  const ids = selectedItems.value.map((item) => item.reportId)
  graphApi
    .build(ids)
    .then((res) => {
      if (res.code === 20000) {
        ElMessage.success('构建成功')
      }
    })
    .catch((err) => {
      ElMessage.error('构建失败' + err.toString())
    })
    .finally(() => {
      building.value = false
    })
}
// 时间关联空间关联特别处理
function timeAndSpaceRelatedProp(prop: string) {
  const label = getLabelByProp(prop)
  if (label == '时间') {
    return '数据与时间关联'
  } else if (label == '地点') {
    return '数据与空间关联'
  } else {
    return label
  }
}

const reportDialogVisibility = ref(false)
const reportDetails = ref('')
function viewReportDetail(row) {
  reportDialogVisibility.value = true
  const reportId = row.reportId
  fileApi.searchById(reportId).then((res: Response) => {
    reportDetails.value = res.data.details
  })
}
</script>

<template>
  <el-drawer
    v-model="drawer"
    title="查看事件详情"
    :with-header="true"
    :size="'40%'"
    :before-close="
      () => {
        drawer = false
      }
    "
  >
    <EventDetail :eventData="current_event_item" />
  </el-drawer>
  <el-dialog v-model="reportDialogVisibility" title="事件与数据语义关联">
    <div v-html="reportDetails" class="tooltip-content" />
  </el-dialog>

  <div class="config-row">
    <div class="search-col">
      <span class="title">事件数据语义检索与推荐</span>
      <OntologySelector v-model="selected" class="selector" />
      <el-input class="input" v-model="searchText" placeholder="请输入内容"></el-input>
      <el-button @click="handleRetrieval()" type="primary" class="search-button">检索</el-button>
    </div>
    <div class="field-col">
      <div class="field-selector">
        <label class="field-label">展示的字段：</label>
        <OntologySelector
          v-model="fieldSelectedList"
          class="field-select"
          clearable
          multiple
          selected-prop
        />
      </div>
    </div>
  </div>
  <div class="table">
    <el-table
      :data="filterEventsListTableData"
      :header-cell-style="getTableHeaderStyle"
      border
      height="100%"
      @selectionChange="handleSelectionChange"
    >
      <el-table-column type="selection" />
      <el-table-column
        v-for="prop in fieldSelectedList"
        :label="timeAndSpaceRelatedProp(prop)"
        :prop="prop"
      ></el-table-column>
      <el-table-column label="操作">
        <template #default="{ row, $index }">
          <el-tooltip content="查看" placement="top">
            <el-button @click="handleView(row)" text type="default">
              <el-icon>
                <View />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="事件与数据语义关联" placement="top" v-if="false">
            <el-button text type="default" @click="viewReportDetail(row)">
              <el-icon>
                <Document />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="编辑" placement="top">
            <el-button @click="handleEdit(row)" text type="default">
              <el-icon>
                <Edit />
              </el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <el-button @click="handleDelete(row)" text type="default">
              <el-icon>
                <Delete />
              </el-icon>
            </el-button>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <div class="pagination">
    <el-pagination
      :total="total"
      @current-change="handleCurrentChange"
      background
      layout="slot,total, prev, pager, next"
    >
      <template #default>选中{{ selectedItems.length }}项</template>
    </el-pagination>
    <div class="buttons">
      <el-button type="primary" @click="headCorrelation" :plain="selectedItems.length === 0">
        <el-icon>
          <Connection />
        </el-icon>
        关联数据
      </el-button>
      <el-button :disabled="selectedItems.length === 0" type="danger">
        <el-icon>
          <Delete />
        </el-icon>
        批量删除
      </el-button>
      <el-button type="success" @click="buildGuild" v-loading="building">
        <SvgIcon icon-class="hammer" />
        目标引导的事件图谱构建
      </el-button>
      <el-button type="warning" @click="rebuildGraph" v-loading="rebuildLoading">
        <SvgIcon icon-class="hammer" />
        重构
      </el-button>
    </div>
  </div>
  <el-dialog v-model="EditDialogVisible" title="事件数据交互编辑" width="800" align-center>
    <div v-if="editItem">
      <el-form label-width="100px">
        <el-form-item label="ID">
          <el-input v-model="editItem.id" disabled />
        </el-form-item>

        <el-form-item label="事件名称">
          <el-input v-model="editItem.eventName" />
        </el-form-item>

        <el-form-item label="时间">
          <el-input v-model="editItem.time" />
        </el-form-item>

        <el-form-item label="地点">
          <el-input v-model="editItem.places" />
        </el-form-item>

        <el-form-item label="组织">
          <el-input v-model="editItem.organizations" />
        </el-form-item>

        <!-- actions 数组 -->
        <div v-if="editItem.actions && editItem.actions.length">
          <h3>动作 (actions)</h3>
          <div v-for="(act, idx) in editItem.actions" :key="idx" class="dialog-section">
            <el-form-item label="动作名称">
              <el-input v-model="act.actionName" />
            </el-form-item>
            <el-form-item label="相关组织">
              <el-input v-model="act.relatedOrganization" />
            </el-form-item>
            <el-form-item label="相关人物">
              <el-input v-model="act.relatedPerson" />
            </el-form-item>
            <el-form-item label="相关地点">
              <el-input v-model="act.relatedPlace" />
            </el-form-item>
          </div>
        </div>

        <!-- person 数组 -->
        <div v-if="editItem.person && editItem.person.length">
          <h3>人物 (person)</h3>
          <div v-for="(p, idx) in editItem.person" :key="idx" class="dialog-section">
            <el-form-item label="组织">
              <el-input v-model="p.organization" />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="p.personName" />
            </el-form-item>
            <el-form-item label="角色">
              <el-input v-model="p.role" />
            </el-form-item>
          </div>
        </div>
      </el-form>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="EditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmEdit()">确认</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style lang="scss" scoped>
.config-row {
  width: 100%;
  display: flex;
  justify-items: center;
  justify-content: space-between;
  align-items: center;

  .search-col {
    width: 40%;
    display: flex;
    gap: 10px; // 添加间隙
    justify-items: center;
    justify-content: space-between;
    align-items: center;
    background: #f0f2f5;
    padding: 5px;
    border-radius: 4px;
    .title {
      width: 12rem;
      flex-shrink: 0; // 防止收缩
      font-size: 1em;
      font-weight: bold;
      color: #3f3f40;
    }

    .selector {
      flex: 1; // 自适应剩余空间
    }

    .input {
      flex: 2; // 自适应剩余空间，权重为2
    }

    .search-button {
      flex: 0.5; // 不放大不缩小，内容自适应
    }
  }
  .field-col {
    width: 40%;
    display: flex;

    .field-selector {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 10px;
      // 右对齐
      justify-content: flex-end;
      .field-select {
        width: 50%;
      }
    }
  }
}

.table {
  padding-top: 1vh;
  height: 70vh;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1vh;
}

.dialog-section {
  margin-bottom: 1em;
  padding-left: 0.5em;
  border-bottom: 1px solid #eee;
}

:deep(.el-button) {
  padding-left: 5px;
  padding-right: 5px;
  margin: 0;
}
.tooltip-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;
}
</style>
