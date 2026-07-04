<script setup lang="ts">
import {
  useOntologyStore,
  OntologyPromptOption,
  OntologyConfigurationItem,
  Relation,
} from '@/stores/ontologyStore'
import { ref, reactive, watch, onMounted } from 'vue'
import OntologyConfigSelector from '@/commomComponents/OntologyConfigSelector.vue'
import OntologyCheckboxRows from '@/commomComponents/OntologyCheckboxRows.vue'
import { ElMessage } from 'element-plus'
import ontologyItemDisplay from './ontologyItemDisplay.vue'
import { disableEdit } from 'mind-elixir/dist/types/interact'

// props & emits
const props = defineProps({
  selectedConfig: {
    type: String,
    default: '',
    required: false,
  },
})
const emit = defineEmits(['selectOntologyItem'])

// refs & reactive
const checkedItems = ref<string[]>([])
const options = ref<OntologyPromptOption[]>([])
const dialogVisible = ref(false)
const selectedOntologyItem = ref('')
const newOntologyField = ref('')
const newOntologyFieldEng = ref('')
const selectedCell = ref({ row: -1, col: -1 })

const ontologyStoreConfig = ref<OntologyConfigurationItem[]>([])
const ontologyStorePrompt = ref<OntologyPromptOption[]>([])
const ontologyStoreRelation = ref<Relation[]>([])

// store
const ontologyStore = useOntologyStore()

// 更新选中复选框状态
const updateCheckedItems = () => {
  if (props.selectedConfig?.trim() && Array.isArray(ontologyStore.ontologyConfigurations)) {
    const matchedItem = ontologyStore.ontologyConfigurations.find(
      (item) => item.label === props.selectedConfig.trim(),
    )
    if (matchedItem && Array.isArray(matchedItem.extract_fields_list)) {
      checkedItems.value = matchedItem.extract_fields_list
        .filter((fieldItem) => fieldItem.field)
        .map((fieldItem) => fieldItem.field)
    } else {
      checkedItems.value = []
      console.warn(`未找到 label 为 ${props.selectedConfig} 的项，或该项无有效 extract_fields_list`)
    }
  } else {
    checkedItems.value = []
    console.warn('更新选中状态失败：selectedConfig 不是有效字符串或 extract_list 格式错误')
  }
}

// 选择本体项
function handleSelectedOntologyItem(item: OntologyPromptOption) {
  selectedOntologyItem.value = item.label
  emit('selectOntologyItem', item.label)
}

// 初始化数据
onMounted(async () => {
  try {
    console.log('数据加载中...')
    await ontologyStore.initData() // 如果需要异步初始化
    options.value = ontologyStore.ontologyPrompt
    console.log('数据初始化完成')
    updateCheckedItems()
  } catch (error) {
    console.error('数据加载失败:', error)
  }
})

// 监听复选框变化，同步到 store
watch(
  checkedItems,
  (newChecked) => {
    const newExtractFields = newChecked.map((label) => ({
      field: label,
      SelectedStrategy: '1',
    }))
    const updatedSelectedConfig = {
      label: props.selectedConfig.trim(),
      extract_fields_list: newExtractFields,
    }
    ontologyStore.updateOntologyConfiguration(updatedSelectedConfig)
    console.log('复选框状态变化 → 同步给上层的 extract_fields_list：', updatedSelectedConfig)
  },
  { deep: true },
)

// 监听 props.selectedConfig 变化
watch(
  () => props.selectedConfig,
  () => {
    updateCheckedItems()
  },
  { deep: true },
)

// 打开新增本体对话框
function handleAddOntology() {
  ontologyStorePrompt.value = JSON.parse(JSON.stringify(ontologyStore.ontologyPrompt))
  ontologyStoreConfig.value = JSON.parse(JSON.stringify(ontologyStore.ontologyConfigurations))
  ontologyStoreRelation.value = JSON.parse(JSON.stringify(ontologyStore.relations))
  dialogVisible.value = true
}

function handleConfirm() {
  ontologyStore.updateOntologyConfiguration(ontologyStoreConfig.value)
  ontologyStore.updateOntologyPromptOptions(ontologyStorePrompt.value)
  ontologyStore.updateRelations(ontologyStoreRelation.value)
  dialogVisible.value=false
}

function handleUpdateLabel({
  index,
  newLabel,
  newProp,
}: {
  index: number
  newLabel: string
  newProp?: string
}) {
  const item = ontologyStorePrompt.value[index]
  if (!item) return

  const oldLabel = item.label
  item.label = newLabel
  if (newProp !== undefined) item.prop = newProp

  ontologyStoreConfig.value.forEach((configItem) => {
    if (Array.isArray(configItem.extract_fields_list)) {
      configItem.extract_fields_list.forEach((fieldItem) => {
        if (fieldItem.field === oldLabel) {
          fieldItem.field = newLabel
        }
      })
    }
  })

  ontologyStoreRelation.value.forEach((relItem) => {
    if (relItem.source === oldLabel) relItem.source = newLabel
    if (relItem.target === oldLabel) relItem.target = newLabel
  })
}

function handleDelete(index: number) {
  if (index < 0 || index >= ontologyStorePrompt.value.length) return

  const deletedItem = ontologyStorePrompt.value[index]
  const deletedLabel = deletedItem.label

  ontologyStorePrompt.value.splice(index, 1)

  ontologyStoreConfig.value.forEach((configItem) => {
    if (Array.isArray(configItem.extract_fields_list)) {
      configItem.extract_fields_list = configItem.extract_fields_list.filter(
        (fieldItem) => fieldItem.field !== deletedLabel,
      )
    }
  })

  ontologyStoreRelation.value = ontologyStoreRelation.value.filter(
    (relItem) => relItem.source !== deletedLabel && relItem.target !== deletedLabel,
  )
}

function handleAdd() {
  ontologyStorePrompt.value.push({
    label: '',
    value: '',
    prop: '',
    promptList: [],
  })
}
</script>

<template>
  <div class="title">
    <span>本体体系</span>
    <el-button @click="handleAddOntology">事件本体编辑</el-button>
  </div>
  <teleport to="body">
    <el-dialog
      v-model="dialogVisible"
      title="事件本体与属性编辑"
      width="30%"
    >
      <div v-for="(item, index) in ontologyStorePrompt" :key="index">
        <ontologyItemDisplay
          :newOntologyLabelItem="item.label"
          :index="index"
          @update-label="handleUpdateLabel"
          @delete-item="handleDelete"
        />
      </div>
      <el-button @click="handleAdd">+</el-button>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确认</el-button>
      </template>
    </el-dialog>
  </teleport>

  <el-card class="system-card">
    <OntologyCheckboxRows v-model="checkedItems" @clicked-item="handleSelectedOntologyItem" />
  </el-card>
</template>

<style lang="scss" scoped>
.title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-bottom: 1vh;
}

.checkbox-container {
  width: 90%;
  height: 90%;
}

.selected-row {
  background-color: #e6f7ff;
}

.system-selector {
  width: 10vw;
}

.system-card {
  width: 100%;
  height: 80%;
  overflow-y: auto;
}
</style>
