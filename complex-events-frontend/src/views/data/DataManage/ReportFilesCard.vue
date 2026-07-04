<script setup lang="ts">
import { Delete, Download, View } from '@element-plus/icons-vue'
import { NOT_IMPL_WARN } from '@/views/ontology'
import fileApi from '@/api/fileApi'
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import { Report } from '@/views/ontology/eventsList/correlationTab'

const props = defineProps<{
  fileList: []
  loading: boolean
  total: number
  paginationHidden?:boolean
  distance:number
}>()

watch(
  () => props.loading,
  (newVal) => {
    tableLoading.value = newVal
  },
)

const pageModel = reactive({
  pageNo: 1,
  pageSize: 10,
})

// 添加判断是否为base64编码的方法
function isBase64(str) {
  if (typeof str !== 'string') return false
  const base64Regex = /^data:image\/[a-zA-Z+]+;base64,/
  return (
    base64Regex.test(str) ||
    /^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$/.test(str)
  )
}
function isVideo(url: string): boolean {
  const videoExtensions = /\.(mp4|webm|ogg|mkv)$/i
  return videoExtensions.test(url)
}
const tableLoading = ref(false)
const emits = defineEmits(['pageModelChanged', 'afterDeleted'])
function handleSizeChange(pageSize: number) {
  pageModel.pageSize = pageSize
  emits('pageModelChanged', pageModel)
}

function handleCurrentChange(pageNo: number) {
  pageModel.pageNo = pageNo // 更新当前页码
  emits('pageModelChanged', pageModel)
}

const selectedItems = ref<Report[]>([])
function handleSelectionChange(newSelection: Report[]) {
  selectedItems.value = newSelection
}

function confirmFileDeleted() {
  const reportIds = selectedItems.value.map((item) => item.id)
  console.log('准备要删除的items', reportIds)
  fileApi
    .deleteFilesById(reportIds)
    .finally(() => {
      emits('afterDeleted')
    })
}
</script>

<template>
  <el-card class="report-card">
    <el-table
      :data="fileList"
      stripe
      style="width: 100%; z-index: 1"
      height="95%"
      v-loading="tableLoading"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" />
      <el-table-column prop="id" label="ID" width="200" />
      <el-table-column prop="topic" label="主题" width="100" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="date" sortable label="日期" width="100" />
      <el-table-column prop="link_url" label="来源">
        <template #default="scoped">
          <a :href="scoped.row.link_url">{{ scoped.row.link_url }}</a>
        </template>
      </el-table-column>
      <el-table-column prop="resources" label="相关资料">
        <template #default="{ row }">
          <div class="img-row">
            <div v-for="url in row.resources" :key="url">
              <!-- 判断是否为base64编码 -->
              <el-image v-if="isBase64(url)" :src="url" fit="fill" />
              <video v-else-if="isVideo(url)" controls >
                <source :src="url" type="video/mp4">
                您的浏览器不支持视频播放。
              </video>
              <!-- 如果不是base64编码，则展示为文本 -->
              <span v-else><a :href="url">{{ url }}</a></span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="文件操作" v-if="false">
        <template #default="scope">
          <el-tooltip content="下载">
            <el-button
              :icon="Download"
              circle
              size="small"
              type="primary"
              @click="NOT_IMPL_WARN(scope.row)"
            />
          </el-tooltip>
          <el-tooltip content="预览">
            <el-button
              :icon="View"
              circle
              size="small"
              type="info"
              @click="NOT_IMPL_WARN(scope.row)"
            />
          </el-tooltip>
          <el-tooltip content="删除">
            <el-button
              :icon="Delete"
              circle
              size="small"
              type="danger"
              @click="NOT_IMPL_WARN(scope.row)"
            />
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
    <!-- 分页组件 -->
    <div class="end-row">
      <el-pagination
        v-show="!paginationHidden"
        class="table-pagination"
        :current-page="pageModel.pageNo"
        :page-sizes="[10, 20, 50]"
        :page-size="pageModel.pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
      <div>
        <el-text v-show="distance">语义相似度{{distance.toFixed(2)}}</el-text>
        <el-button type="success" @click="confirmFileDeleted" v-if="selectedItems?.length > 0">
          基于语义的多模态数据过滤
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.img-row {
  display: flex;
  video{
    width: 150px;
    height: calc(150px * (9/16));
    object-fit: cover;
  }
}
.end-row {
  height: 5%;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;

  .table-pagination {
    height: 100%;
  }
}
</style>
