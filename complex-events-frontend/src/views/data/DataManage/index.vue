<template>
  <div class="data-upload-page">
    <div class="toolbar">
      <div class="upload-actions">
        <el-button type="primary" @click="dialogFormVisible = true">
          <el-icon>
            <Upload />
          </el-icon>
          上传文件
        </el-button>
        <SupportFileTags />
      </div>
      <div class="search-actions">
        <el-input v-model="searchKeyword" clearable placeholder="输入关键词检索上传文件">
          <template #append>
            <el-button type="primary" :icon="Search" @click="searchFiles">检索</el-button>
          </template>
        </el-input>
      </div>
    </div>

    <div class="report-card">
      <ReportFilesCard
        :file-list="fileList"
        :loading="loading"
        :total="pageModel.total"
        :distance="avgDistance"
        @page-model-changed="handlePageChange"
        @after-deleted="getFileList"
      />
    </div>

    <UploadDialog v-model="dialogFormVisible" title="上传文件" @confirm="getFileList" />
  </div>
</template>

<script setup>
import { Search, Upload } from '@element-plus/icons-vue'
import SupportFileTags from '@/views/data/DataManage/SupportFileTags.vue'
import UploadDialog from '@/views/data/DataManage/UploadDialog.vue'
import fileApi from '@/api/fileApi.js'
import ReportFilesCard from '@/views/data/DataManage/ReportFilesCard.vue'
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

const loading = ref(false)
const pageModel = reactive({
  pageNo: 1,
  pageSize: 10,
  total: 1,
})
const fileList = ref([])
const searchKeyword = ref('')
const avgDistance = ref(0)
const dialogFormVisible = ref(false)

function getFileList() {
  loading.value = true
  fileApi
    .getFileList(pageModel)
    .then((response) => {
      fileList.value = response.data.rows
      pageModel.total = response.data.total
      avgDistance.value = 0
    })
    .catch((error) => {
      console.error(error)
      ElMessage.error('获取失败')
    })
    .finally(() => {
      loading.value = false
    })
}

const handlePageChange = (newPgMd) => {
  pageModel.pageNo = newPgMd.pageNo
  pageModel.pageSize = newPgMd.pageSize
  getFileList()
}

function searchFiles() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    getFileList()
    return
  }

  loading.value = true
  fileApi
    .search(keyword)
    .then((res) => {
      fileList.value = res.data
      avgDistance.value = 0
      pageModel.total = res.data.length
    })
    .catch((e) => {
      console.error(e)
      ElMessage.error('检索失败')
    })
    .finally(() => {
      loading.value = false
    })
}

onMounted(() => {
  getFileList()
})
</script>

<style scoped lang="scss">
.data-upload-page {
  padding: 0 1vw;
}

.toolbar {
  width: 100%;
  min-height: 5vh;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-actions {
  width: min(420px, 45vw);
}

.report-card {
  margin-top: 2vh;
  height: 80vh;
}
</style>
