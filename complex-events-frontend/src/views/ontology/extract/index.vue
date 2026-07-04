<script setup lang="ts">
import FileSelectCard from '@/views/ontology/extract/FileSelectCard.vue'
import PromptConfigCard from '@/views/ontology/extract/PromptConfigCard.vue'
import ExtractResultPreview from '@/views/ontology/extract/ExtractResultPreviewCard.vue'
import { reactive, ref, Ref } from 'vue'
import { formattedExtractResult, OutputStream } from '@/views/ontology/extract/index.js'
import { io } from 'socket.io-client'
import OutputDrawer from '@/commomComponents/OutputDrawer.vue'
import { ElMessage } from 'element-plus'

/**
 * 事件抽取入口文件
 */
const selectedItems = ref([])
const handleSelectionChange = (newSelectedItems) => {
  selectedItems.value = newSelectedItems
}
const outputDialogVisible = ref(false)
const outputInfo = ref<OutputStream[]>([])

const extractResult = ref([])

// 目前正在大模型抽取处理的index
const currentProcessId = ref('')
// 提取完成计数
const finishedCount = ref(0)
const completedFlag = ref(false)
/**
 * 初始化连接开始的变量
 */
function initLinkStart(){

  outputDialogVisible.value = true
  finishedCount.value = 0
  completedFlag.value = false
}
const extract = async (prompt) => {
  // 初始化输出信息
  outputInfo.value = Array.from({ length: selectedItems.value.length }, (_, i) => ({
    id: selectedItems.value[i].id,
    content: '',
  }))

  initLinkStart()
  // 串行处理每个项目
  for (let index = 0; index < selectedItems.value.length; index++) {
    const item = selectedItems.value[index]
    const reportID = item.id

    // 创建Promise来等待当前任务完成
    await new Promise((resolve) => {
      // 为每个项目创建独立的socket连接
      const socket = io(import.meta.env.VITE_APP_BASE_API)
      // 连接成功
      socket.on('connect', function () {
        // 开始新连接
        currentProcessId.value = reportID
      })
      // 注册事件监听器
      socket.on('extract_progress', function (data) {
        outputInfo.value[index].content += data.content
      })

      socket.on('extract_complete', function (data) {
        console.log('完成:', data)
        extractResult.value.push(formattedExtractResult(data.data))
        finishedCount.value ++;
        resolve() // 完成当前任务
      })

      socket.on('extract_error', function (data) {
        console.error('错误:', data.error)
        ElMessage.error(data.error)

        resolve() // 即使出错也继续下一个任务
      })
      // 发送请求
      socket.emit('extract_data', {
        reportId: reportID,
        prompt: prompt,
      })
    })
  }
  completedFlag.value = true

  ElMessage.success('所有抽取任务完成')
}
</script>

<template>
  <el-row :gutter="50" class="display-row">
    <el-col :span="12" class="first-col">
      <FileSelectCard
        :selectedItems="selectedItems"
        @selectedItemsChanged="handleSelectionChange"
        class="file-select-card"
      />
      <PromptConfigCard
        class="prompt-config-card"
        :selectedItems="selectedItems.at(-1)"
        @startExtract="extract"
      />
    </el-col>
    <el-col :span="12" class="second-col">
      <ExtractResultPreview
        :selectedItems="selectedItems"
        class="result-card"
        :table-data="extractResult"
      />
    </el-col>
  </el-row>
  <OutputDrawer
    v-model="outputDialogVisible"
    v-model:output="outputInfo"
    :finished-count="finishedCount"
    :currentId="currentProcessId"
    :completed-flag="completedFlag"
  />
</template>

<style lang="scss" scoped>
.display-row {
  height: 90vh;
  width: 100%;
  padding-left: 1vw;

  .first-col {
    height: calc(100% - 20px);

    .file-select-card {
      height: 50%;
    }

    .prompt-config-card {
      margin-top: 20px;
      height: 50%;
    }
  }

  .second-col {
    height: 100%;

    .result-card {
      height: 100%;
    }
  }
}
</style>
