<template>
  <div class="import-container">
    <el-card class="import-card" shadow="hover">
      <h2 class="title">导入数据</h2>

      <div class="two-col">
        <!-- 左列：下载模板 -->
        <div class="col left">
          <div class="step-title">1、下载excel数据模版，填写信息</div>
          <div class="excel-icon">X</div>
          <el-dropdown trigger="click" @command="handleDownloadCommand">
            <el-button :disabled="downloading">下载模板</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="opt in typeOptions"
                  :key="'tpl-' + opt.value"
                  :command="opt.value"
                >{{ opt.label }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <div class="tip-mini" v-if="selectedType">已选择模板类型：{{ selectedType }}</div>
        </div>

        <!-- 中间分割线 -->
        <div class="divider"></div>

        <!-- 右列：上传并导入 -->
        <div class="col right">
          <div class="step-title">2、上传填写好的excel文件</div>
          <div class="excel-icon">X</div>

          <el-upload
            ref="uploadRef"
            class="upload-custom"
            :action="uploadUrl"
            :data="{ type: selectedType }"
            :auto-upload="false"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :on-change="handleFileChange"
            :on-success="handleSuccess"
            :on-error="handleError"
            :on-progress="handleProgress"
            accept=".xlsx,.xls,.csv"
          >
            <template #trigger>
              <el-button class="choose-btn" plain>选择文件</el-button>
            </template>
            <div class="fileline" @click="$refs.uploadRef?.$el.querySelector('input')?.click()">
              <span class="paperclip">📎</span>
              <span>{{ selectedFileName || '未选择文件' }}</span>
            </div>
          </el-upload>

          <el-button type="primary" class="import-btn" :disabled="!selectedFile || uploading" :loading="uploading" @click="submitUpload">
            导入数据
          </el-button>
        </div>
      </div>

      <!-- 进度条显示上传进度与状态 -->
      <div v-if="progressVisible" class="progress-wrap">
        <el-progress :percentage="progressPercent" :status="progressStatus" :stroke-width="14" />
        <div class="progress-text">{{ progressText }}</div>
      </div>

      <el-alert
        v-if="tipVisible"
        :title="tipMessage"
        :type="tipType"
        show-icon
        class="result-tip"
        @close="tipVisible = false"
      />
    </el-card>
    
    <!-- Excel编辑器弹窗 -->
    <ExcelEditor 
      v-model="editorVisible"
      :title="editorTitle"
      :data="editorData"
      :columns="editorColumns"
      @confirm="handleConfirmImport"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import ExcelEditor from './ExcelEditor.vue'
import axios from 'axios'

// 模板类型（用于下载与上传类型映射）
const typeOptions = [
  { label: '检修计划工单样例模板', value: '检修计划工单样例模板' },
  { label: '检修人员表', value: '检修人员表' },
  { label: '检修机具', value: '检修机具' },
  { label: '工种', value: '工种' },
  { label: '人员资质', value: '人员资质' },
  { label: '设备检修人员配置表', value: '设备检修人员配置表' },
]

const selectedType = ref('') // 由"下载模板"选择后同步到这里
const uploading = ref(false)
const uploadRef = ref()
const selectedFile = ref(null)
const selectedFileName = ref('')

// 保留的后端接口地址
const uploadUrl = '/api/import'

const tipVisible = ref(false)
const tipMessage = ref('')
const tipType = ref('success') // success | error | warning | info

// 进度状态
const progressPercent = ref(0)
const progressVisible = ref(false)
const progressStatus = ref(undefined) // success | exception | warning | undefined
const progressText = computed(() => {
  if (progressStatus.value === 'success') return '导入完成'
  if (progressStatus.value === 'exception') return '导入失败'
  if (uploading.value) return `正在导入… ${progressPercent.value}%`
  return ''
})

const downloading = ref(false)

// Excel编辑器相关
const editorVisible = ref(false)
const editorTitle = ref('')
const editorData = ref([])
const editorColumns = ref([])

// 模拟解析Excel文件的方法
function parseExcelFile(file) {
  // 在实际实现中，这里会真正解析Excel文件
  // 目前我们只是模拟一些数据
  
  // 根据不同的模板类型返回不同的列定义
  let columns = []
  let data = []
  
  switch(selectedType.value) {
    case '检修计划工单样例模板':
      columns = [
        { prop: 'orderId', label: '工单编号' },
        { prop: 'deviceName', label: '设备名称' },
        { prop: 'maintenanceType', label: '维修类型' },
        { prop: 'plannedDate', label: '计划日期' }
      ]
      data = [
        { orderId: 'WO001', deviceName: '反应釜', maintenanceType: '定期保养', plannedDate: '2023-06-15' },
        { orderId: 'WO002', deviceName: '离心泵', maintenanceType: '故障维修', plannedDate: '2023-06-16' }
      ]
      break
      
    case '检修人员表':
      columns = [
        { prop: 'workerId', label: '员工编号' },
        { prop: 'name', label: '姓名' },
        { prop: 'department', label: '部门' },
        { prop: 'position', label: '职位' }
      ]
      data = [
        { workerId: 'EMP001', name: '张三', department: '维修部', position: '技师' },
        { workerId: 'EMP002', name: '李四', department: '维修部', position: '助理' }
      ]
      break
      
    default:
      columns = [
        { prop: 'field1', label: '字段1' },
        { prop: 'field2', label: '字段2' },
        { prop: 'field3', label: '字段3' }
      ]
      data = [
        { field1: '值1', field2: '值2', field3: '值3' },
        { field1: '값4', field2: '값5', field3: '값6' }
      ]
  }
  
  return { columns, data }
}

function handleDownloadCommand(typeValue) {
  // 点击某个模板项：先记录所选类型，再发起下载
  selectedType.value = typeValue
  downloadTemplate(typeValue)
}

async function downloadTemplate(typeValue) {
  try {
    downloading.value = true
    if (!typeValue) {
      ElMessage.warning('请选择要下载的模板类型')
      return
    }
    const url = `/api/template?type=${encodeURIComponent(typeValue)}`
    window.open(url, '_blank')
  } catch {
    ElMessage.error('模板下载失败')
  } finally {
    downloading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file?.raw || null
  selectedFileName.value = file?.name || ''
}

function submitUpload() {
  if (!selectedType.value) {
    ElMessage.warning('请先在左侧"下载模板"中选择一个模板类型')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  
  // 解析文件并打开编辑器而不是直接上传
  const { columns, data } = parseExcelFile(selectedFile.value)
  editorColumns.value = columns
  editorData.value = data
  editorTitle.value = `编辑${selectedType.value}数据`
  editorVisible.value = true
}

function handleBeforeUpload(file) {
  if (!selectedType.value) {
    ElMessage.warning('请先选择模板类型')
    return false
  }

  const isAllowedType =
    file.type === 'text/csv' ||
    file.type === 'application/vnd.ms-excel' ||
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowedType) {
    ElMessage.error('仅支持 CSV 或 Excel 文件')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }

  return true
}

// 修改这部分，不再使用原来的上传逻辑
function handleSuccess() {
  // 这个方法不会再被调用，因为我们不再自动上传文件
}

function handleError() {
  // 这个方法也不会再被调用
}

function handleProgress(event) {
  // 这个方法也不会再被调用
}

// 新增：确认导入处理函数
async function handleConfirmImport(editedData) {
  try {
    uploading.value = true
    tipVisible.value = false
    progressVisible.value = true
    progressStatus.value = undefined
    progressPercent.value = 0
    
    // 模拟进度条更新
    const interval = setInterval(() => {
      if (progressPercent.value < 90) {
        progressPercent.value += 10
      }
    }, 200)
    
    // 将编辑后的数据发送到后端
    const requestData = {
      type: selectedType.value,
      items: editedData.map(item => ({ data: item }))
    }
    
    // 发送POST请求到后端
    const response = await axios.post('/api/import', requestData)
    
    clearInterval(interval)
    progressPercent.value = 100
    progressStatus.value = 'success'
    
    setTimeout(() => {
      uploading.value = false
      tipType.value = 'success'
      tipMessage.value = response.data.message || '数据导入成功'
      tipVisible.value = true
      ElMessage.success('数据导入成功')
    }, 500)
  } catch (error) {
    uploading.value = false
    progressStatus.value = 'exception'
    tipType.value = 'error'
    tipMessage.value = '导入失败：' + (error.response?.data?.detail || error.message)
    tipVisible.value = true
    ElMessage.error('数据导入失败')
    console.error('导入失败:', error)
  }
}
</script>

<style scoped>
.import-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  padding: 24px;
}

.import-card {
  width: 880px;
  max-width: 96vw;
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  padding-bottom: 16px;
}

.title {
  margin: 8px 0 16px 0;
  font-weight: 600;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  align-items: start;
  gap: 0;
}

.col {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 12px;
}

.left {}
.right {}

.divider {
  width: 1px;
  background: #e5e7eb;
  height: 260px;
  margin: auto 0;
}

.step-title {
  color: #606266;
  margin-bottom: 10px;
}

.excel-icon {
  width: 100px;
  height: 100px;
  background: #1f9d55;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 60px;
  line-height: 1;
  user-select: none;
  margin-bottom: 12px;
}

.choose-btn {
  margin-bottom: 8px;
}

.fileline {
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 12px;
}

.paperclip {
  margin-right: 6px;
}

.import-btn {
  width: 120px;
}

.progress-wrap {
  margin-top: 16px;
  display: grid;
  gap: 6px;
}

.result-tip {
  margin-top: 16px;
}

.progress-text {
  text-align: center;
  font-size: 12px;
  color: #606266;
}

.tip-mini {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 920px) {
  .import-card { width: 100%; }
  .two-col { grid-template-columns: 1fr; }
  .divider { display: none; }
}