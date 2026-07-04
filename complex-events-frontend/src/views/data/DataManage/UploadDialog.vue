<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue'
import SupportFileTags from '@/views/data/DataManage/SupportFileTags.vue'

import { computed, reactive, ref } from 'vue'
import { uploadFileApi } from '@/api/fileApi'
import { ElMessage, UploadRawFile } from 'element-plus'
import {
  normalizeNewlines,
  preprocess,
  removeAllSpaces,
  removeExtraSpaces,
  removeNewlines,
  spacesToNewlines,
  trimSpaces,
} from '@/utils/textPreprocess'
import { supportFileValues } from '@/views/data/DataManage/supportFileFormats'

interface FileInfo {
  fileName: string
  filePath: string
  fileText: string
  textEmbedding: number[]
  fileEmbedding: number[]
}

const dialogFormVisible = defineModel()

const { title = '上传文件' } = defineProps<{
  title: string
}>()

const fileForm = reactive<FileInfo>({
  fileName: '',
  filePath: '',
  fileText: '',
  textEmbedding: [],
  fileEmbedding:[]
})

function setForm(data: FileInfo) {
  fileForm.filePath = data.filePath
  fileForm.fileName = data.fileName
  fileForm.fileText = data.fileText
  fileForm.textEmbedding = data.textEmbedding
  fileForm.fileEmbedding = data.fileEmbedding
}

function clearForm() {
  fileForm.fileName = ''
  fileForm.filePath = ''
  fileForm.fileText = ''
  fileForm.textEmbedding = []
  fileForm.fileEmbedding = []
}

const fileUploadList = ref([])
// 存储解析成功之后的所有数据，按照文件名区分
const fileUploadSuccessDetailsMap = ref({})

function handleBeforeUpload(rawFile: UploadRawFile) {
  // 根据文件名判断文件格式
  const fileExtension = rawFile.name.substring(rawFile.name.lastIndexOf('.') + 1).toLowerCase()
  // 判断文件格式是否支持
  if (!supportFileValues.includes(rawFile.type) && !supportFileValues.includes(fileExtension)) {
    ElMessage.error('不支持的文件格式')
    return false
  }
  return true
}

// 上传文件，缺文件预览
function handleUploadSuccess(response, file, uploadList) {
  if (response.code === 20000) {
    setForm(response.data)
    fileUploadSuccessDetailsMap.value[file.name] = response.data
    fileUploadList.value = uploadList
  } else {
    ElMessage.error('上传失败')
  }
}

function handleFileRemove(file, fileList) {
  clearForm()
}

function handleFileChange(file, files) {
  // console.log('changeFile', file)
  // console.log('文件列表', files)
}

function handleFileClickInList(file) {
  ElMessage.success(file.name)
  setForm(fileUploadSuccessDetailsMap.value[file.name])
}

const formLabelWidth = '150px'

const emits = defineEmits(['confirm'])

function handleConfirm() {
  dialogFormVisible.value = false
  emits('confirm')
}

// 文本预处理方法
const preprocessMethods = [
  { label: '去除所有空格', method: removeAllSpaces },
  { label: '空格换回车', method: spacesToNewlines },
  { label: '去掉首尾空格', method: trimSpaces },
  { label: '去除多余空格', method: removeExtraSpaces },
  { label: '去除换行符', method: removeNewlines },
  { label: '合并换行符', method: normalizeNewlines },
  { label: '综合预处理', method: preprocess },
]

// 执行文本预处理
function executePreprocess(method: (text: string) => string) {
  fileForm.fileText = method(fileForm.fileText)
}

function handleDialogClose() {
  clearForm()
  fileUploadList.value = []
  fileUploadSuccessDetailsMap.value = {}
}

/**
 * 多模态数据的语义表征
 */
const embedding = computed(()=>{
  console.log(fileForm.textEmbedding)
  return fileForm.textEmbedding.slice(0,10).join(',')+"...."
})

const fileEmbedding = computed(()=>{
  return fileForm.fileEmbedding.slice(0,10).join(',')+"...."
})
</script>

<template>
  <el-dialog :title="title" v-model="dialogFormVisible" @close="handleDialogClose">
    <div class="upload-row">
      <!-- 上传文件 -->
      <el-upload
        class="upload-demo"
        drag
        :before-upload="handleBeforeUpload"
        :action="uploadFileApi"
        :on-success="handleUploadSuccess"
        :on-remove="handleFileRemove"
        :on-change="handleFileChange"
        :show-file-list="false"
      >
        <el-icon class="el-icon--upload">
          <upload-filled />
        </el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div style="padding-top: 5px">
            <SupportFileTags />
          </div>
        </template>
      </el-upload>
      <div class="upload-file-list">
        <span><b>文件上传解析成功列表</b></span>

        <el-empty v-if="fileUploadList.length == 0" :image-size="50" />
        <div v-else style="margin-top: 10px">
          <ul class="file-list">
            <li
              v-for="file in fileUploadList"
              class="el-upload-list__item"
              @click="handleFileClickInList(file)"
            >
              {{ file.name }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <el-form ref="fileFormRef" :model="fileForm" label-position="top">
      <!-- 展示文件名 -->
      <el-form-item label="文件名" prop="fileName" :label-width="formLabelWidth">
        <el-input v-model="fileForm.fileName" autocomplete="off" readonly />
      </el-form-item>
      <!-- 展示文件存放地址 -->
      <el-form-item label="文件存放地址" prop="filePath" :label-width="formLabelWidth">
        <el-input v-model="fileForm.filePath" autocomplete="off" readonly />
      </el-form-item>
      <el-form-item prop="fileText" :label-width="formLabelWidth">
        <template #label>
          <el-text>事件数据解析与统一表征</el-text>
        </template>
        <el-input
          v-model="fileForm.fileText"
          type="textarea"
          readonly
          autocomplete="off"
          :rows="10"
          style="white-space: pre-wrap"
        />
      </el-form-item>
      <el-form-item prop="embedding" :label-width="formLabelWidth">
        <template #label>
          <span>多模态学习的语义表征</span>
        </template>
        <el-input v-model="embedding" />
      </el-form-item>
      <el-form-item prop="fileEmbedding" :label-width="formLabelWidth">
        <template #label>
          <span>多模态数据结构化表征</span>
        </template>
        <el-input v-model="fileEmbedding" />
      </el-form-item>
      <el-form-item prop="preprocess" :label-width="formLabelWidth">
        <template #label>
          <el-text tag="b" :size="14"> 多模态数据预处理</el-text>
        </template>
        <el-row :gutter="20" style="width: 100%">
          <el-col :span="3" v-for="(item, index) in preprocessMethods" :key="index">
            <el-button @click="executePreprocess(item.method)" style="width: 100%">
              {{ item.label }}
            </el-button>
          </el-col>
        </el-row>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.upload-row {
  display: flex;
  flex-direction: row;
  width: 100%;

  .upload-demo {
    width: 80%;
    margin-bottom: 1vh;
  }

  .upload-file-list {
    width: 20%;
    padding-left: 20px;

    // 添加文件列表样式
    .file-list {
      list-style: none; // 去掉小圆点
      padding-left: 0; // 去掉默认左边距
      margin: 0; // 去掉默认外边距
    }
  }
}

.label-container {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  align-items: flex-end;
  gap: 0;
  height: 100%;
  justify-content: center; // 垂直居中内容
  // 添加以下样式确保文本紧密连接
  line-height: 1; // 减少行高
  span {
    margin: 0; // 确保没有外边距
    padding: 0; // 确保没有内边距
  }
}
</style>
