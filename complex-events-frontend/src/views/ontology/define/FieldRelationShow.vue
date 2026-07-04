<script setup lang="ts">
import { Plus, Edit, Check, Delete } from '@element-plus/icons-vue'
import { computed, ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Relation, useOntologyStore } from '@/stores/ontologyStore'
import { ElMessage, ElDialog, ElSelect, ElOption, ElInput, ElButton } from 'element-plus'

const props = defineProps({
  fieldName: {
    type: String,
    default: '字段名',
  },
  config: {
    type: Object,
    default: () => ({ sources: [], targets: [] }),
    required: true,
  },
  searchText: {
    type: String,
    default: '',
  },
})

defineOptions({ name: 'RelationShow' })

const oneRowDisplayNum = 3
const relationData = ref<Relation[]>([])
const originRelationData = ref<Relation[]>([])
const allRelations = ref<Relation[]>([])
const isLoading = ref(false)
const dialogVisible = ref(false)
const currentRelation = ref<Relation | null>(null)
const editSource = ref('')
const editTarget = ref('')
const editType = ref('')
// 新增：跟踪当前正在编辑的关系项
const editingRelation = ref<Relation | null>(null)
// 新增：编辑状态下的临时值
const tempSource = ref('')
const tempTarget = ref('')
const tempType = ref('')

const ontologyStore = useOntologyStore()

const filterRelations = () => {
  if (!props.searchText) {
    relationData.value = [...originRelationData.value]
  } else {
    const searchLower = props.searchText.toLowerCase()
    relationData.value = originRelationData.value.filter((relation) =>
      relation.type.toLowerCase().includes(searchLower),
    )
  }
}

onMounted(async () => {
  try {
    // await ontologyStore.initData()
    await fetchRelationData(props.fieldName)
  } catch (error) {
    console.error('数据加载失败:', error)
  }
})

const rowDisplayNum = computed(() => {
  return Math.ceil(relationData.value.length / oneRowDisplayNum)
})
const colSpan = computed(() => {
  return Math.floor(24 / oneRowDisplayNum)
})

const fetchRelationData = async (currentFieldName: string) => {
  isLoading.value = true
  try {
    allRelations.value = [...ontologyStore.relations]

    const filteredRelations = allRelations.value.filter(
      (item) => item.source === currentFieldName || item.target === currentFieldName,
    )
    originRelationData.value = filteredRelations
    filterRelations()

    return filteredRelations
  } catch (error) {
    ElMessage.error('获取关系数据失败')
    console.error('获取关系数据异常:', error)
    originRelationData.value = []
    relationData.value = []
    throw error
  } finally {
    isLoading.value = false
  }
}

watch(
  () => props.fieldName,
  (newFieldName) => {
    fetchRelationData(newFieldName)
  },
  { immediate: false },
)

watch(
  () => props.searchText,
  () => {
    filterRelations()
  },
)

// 新增关系
const addRelation = () => {
  const newRelation: Relation = {
    source: props.fieldName,
    target: '',
    type: '',
  }

  originRelationData.value.push(newRelation)
  filterRelations()

  modify(newRelation)
}

// 打开编辑弹窗
const modify = (relation: Relation) => {
  currentRelation.value = { ...relation }
  editSource.value = relation.source
  editTarget.value = relation.target
  editType.value = relation.type
  dialogVisible.value = true
}

// 确认弹窗编辑
const confirmEdit = () => {
  if (!currentRelation.value) return

  if (!editSource.value || !editTarget.value || !editType.value) {
    ElMessage.warning('请填写完整信息')
    return
  }

  const isNew = !originRelationData.value.some(
    (item) =>
      item.source === currentRelation.value!.source &&
      item.target === currentRelation.value!.target &&
      item.type === currentRelation.value!.type,
  )

  if (!isNew) {
    const index = originRelationData.value.findIndex(
      (item) =>
        item.source === currentRelation.value!.source &&
        item.target === currentRelation.value!.target &&
        item.type === currentRelation.value!.type,
    )
    if (index !== -1) {
      originRelationData.value[index] = {
        source: editSource.value,
        target: editTarget.value,
        type: editType.value,
      }
    }

    allRelations.value = allRelations.value.filter(
      (item) =>
        !(
          item.source === currentRelation.value!.source &&
          item.target === currentRelation.value!.target &&
          item.type === currentRelation.value!.type
        ),
    )
  } else {
    originRelationData.value.push({
      source: editSource.value,
      target: editTarget.value,
      type: editType.value,
    })
  }

  allRelations.value.push({
    source: editSource.value,
    target: editTarget.value,
    type: editType.value,
  })

  ontologyStore.updateRelations(allRelations.value)

  filterRelations()

  dialogVisible.value = false
  ElMessage.success(isNew ? '关系已添加' : '关系已更新')
}

const startQuickEdit = (relation: Relation, event: MouseEvent) => {
  event.stopPropagation()

  editingRelation.value = { ...relation }

  tempSource.value = relation.source
  tempTarget.value = relation.target
  tempType.value = relation.type
}

const startQuickDelete = (relation: Relation, event: MouseEvent) => {
  event.stopPropagation()
  editingRelation.value = { ...relation }

  tempSource.value = relation.source
  tempTarget.value = relation.target
  tempType.value = relation.type

  if (!editingRelation.value) return

  const index = originRelationData.value.findIndex(
    (item) =>
      item.source === editingRelation.value!.source &&
      item.target === editingRelation.value!.target &&
      item.type === editingRelation.value!.type,
  )

  if (index !== -1) {
    allRelations.value = allRelations.value.filter(
      (item) =>
        !(
          item.source === editingRelation.value!.source &&
          item.target === editingRelation.value!.target &&
          item.type === editingRelation.value!.type
        ),
    )

    originRelationData.value.splice(index, 1)

    // 同步更新到本体存储
    ontologyStore.updateRelations(allRelations.value)

    filterRelations()
    ElMessage.success('已删除关系')
  }

  editingRelation.value = null
}

const confirmQuickEdit = (event: MouseEvent) => {
  event.stopPropagation()

  if (!editingRelation.value) return

  if (!tempSource.value || !tempTarget.value || !tempType.value) {
    ElMessage.warning('请填写完整信息')
    return
  }

  const index = originRelationData.value.findIndex(
    (item) =>
      item.source === editingRelation.value!.source &&
      item.target === editingRelation.value!.target &&
      item.type === editingRelation.value!.type,
  )

  if (index !== -1) {
    allRelations.value = allRelations.value.filter(
      (item) =>
        !(
          item.source === editingRelation.value!.source &&
          item.target === editingRelation.value!.target &&
          item.type === editingRelation.value!.type
        ),
    )

    originRelationData.value[index] = {
      source: tempSource.value,
      target: tempTarget.value,
      type: tempType.value,
    }

    // 添加新关系到allRelations
    allRelations.value.push({
      source: tempSource.value,
      target: tempTarget.value,
      type: tempType.value,
    })

    // 同步更新到本体存储
    ontologyStore.updateRelations(allRelations.value)

    filterRelations()
    ElMessage.success('关系已更新')
  }

  editingRelation.value = null
}

const isEditing = (relation: Relation) => {
  if (!editingRelation.value) return false
  return (
    relation.source === editingRelation.value.source &&
    relation.target === editingRelation.value.target &&
    relation.type === editingRelation.value.type
  )
}
</script>

<template>
  <div class="title">
    <label>{{ fieldName }}</label>
    <el-button round type="primary" @click="addRelation">
      <el-icon>
        <Plus />
      </el-icon>
      新增关系
    </el-button>
  </div>

  <el-skeleton v-if="isLoading" :rows="3" class="mb-4" />

  <div class="relations-container" v-else>
    <el-row v-for="(row, rowIndex) in rowDisplayNum" :key="rowIndex" :gutter="30" class="relation-display">
      <template v-for="(item, colIndex) in relationData.slice(
        rowIndex * oneRowDisplayNum,
        rowIndex * oneRowDisplayNum + oneRowDisplayNum,
      )" :key="`${item.source}-${item.target}-${item.type}`">
        <el-col :span="colSpan">
          <div class="relation-item">
            <template v-if="isEditing(item)">
              <el-select v-model="tempSource" placeholder="请选择来源" class="relation-field-select">
                <el-option v-for="option in props.config" :key="option" :label="option" :value="option" />
              </el-select>
              <div class="connector-line"></div>
              <el-input v-model="tempType" placeholder="关系类型" class="relation-type-input" />
              <div class="connector-line-end"></div>
              <el-select v-model="tempTarget" placeholder="请选择目标" class="relation-field-select">
                <el-option v-for="option in props.config" :key="option" :label="option" :value="option" />
              </el-select>
              <div class="edit-icon" @click="confirmQuickEdit($event)">
                <el-icon size="16">
                  <Check />
                </el-icon>
              </div>
            </template>

            <!-- 非编辑状态显示文本 -->
            <template v-else>
              <div class="relation-field">{{ item.source }}</div>
              <div class="connector-line"></div>
              <div class="relation-name">{{ item.type }}</div>
              <div class="connector-line-end"></div>
              <div class="relation-field">{{ item.target }}</div>
              <el-tooltip content="事件本体关联关系编辑" placement="top">
                <div class="edit-icon" style="right: 30px;" @click="startQuickEdit(item, $event)">
                  <el-icon size="16">
                    <Edit />
                  </el-icon>
                </div>
              </el-tooltip>
              <el-tooltip content="事件本体关联关系删除" placement="top">
                <div class="edit-icon" @click="startQuickDelete(item, $event)">
                  <el-icon size="16">
                    <Delete />
                  </el-icon>
                </div>
              </el-tooltip>
            </template>
          </div>
        </el-col>
      </template>
    </el-row>

    <el-empty v-if="relationData.length === 0" description="暂无相关关系数据" />
  </div>
</template>

<style lang="scss" scoped>
.title {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 20px;
}

.relations-container {
  width: 100%;
}

.relation-display {
  width: 100%;
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.relation-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  padding: 15px 10px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  position: relative;
  cursor: pointer;

  &:hover {
    border-color: #409eff;
    box-shadow: 0 4px 8px rgba(64, 158, 255, 0.1);
  }
}

.edit-icon {
  position: absolute;
  right: 10px;
  top: 3px;
  color: #409eff;
  opacity: 0.7;
  cursor: pointer;
  transition: opacity 0.3s;

  &:hover {
    opacity: 1;
  }
}

.relation-field {
  padding: 5px 10px;
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  font-size: 14px;
  color: #606266;
  min-width: 80px;
  text-align: center;
}

.relation-field-select {
  min-width: 80px;
  width: auto;
  margin: 0 5px;
}

.relation-type-input {
  min-width: 100px;
  width: auto;
  margin: 0 5px;
  text-align: center;
}

.relation-name {
  padding: 6px 12px;
  background-color: #ecf5ff;
  border-radius: 10px;
  border: 1px solid #b3d8ff;
  color: #409eff;
  font-weight: 500;
  font-size: 15px;
  min-width: 100px;
  text-align: center;
}

.connector-col {
  display: flex;
  align-items: center;
  justify-content: center;
}

.connector-line {
  width: 30px;
  height: 2px;
  background-color: #c0c4cc;
  position: relative;
}

.connector-line-end {
  width: 30px;
  height: 2px;
  background-color: #c0c4cc;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 6px solid #c0c4cc;
  }
}

.dialog-form {
  padding: 10px 0;
}

.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;

  &:last-child {
    margin-bottom: 0;
  }
}

.form-label {
  width: 80px;
  text-align: right;
  margin-right: 15px;
  font-weight: 500;
}

.form-value {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.form-control {
  width: 100%;
  max-width: 300px;
}
</style>
