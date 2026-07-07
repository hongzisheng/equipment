<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="90%"
    top="60px"
    :before-close="handleClose"
    class="excel-editor-dialog"
  >
    <div class="table-container">
      <el-table :data="tableData" height="calc(90vh - 200px)" border style="width: 100%">
        <el-table-column
          v-for="column in columns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width || 150"
        >
          <template #default="scope">
            <el-input 
              v-model="scope.row[column.prop]" 
              :placeholder="column.label"
              @input="handleDataChange"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteRow(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div style="margin-top: 20px;">
      <el-button type="primary" @click="addRow">新增行</el-button>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="confirmImport">确认导入</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '数据预览'
  },
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'save'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

const tableData = ref([])

watch(() => props.data, (newData) => {
  tableData.value = JSON.parse(JSON.stringify(newData))
}, { immediate: true, deep: true })

function handleClose() {
  visible.value = false
}

function addRow() {
  const newRow = {}
  props.columns.forEach(column => {
    newRow[column.prop] = ''
  })
  tableData.value.push(newRow)
}

function deleteRow(index) {
  tableData.value.splice(index, 1)
}

function handleDataChange() {
  // 数据变化时的处理
}

function confirmImport() {
  // 检查数据是否完整 - 过滤掉完全为空的行
  const validData = tableData.value.filter(row => {
    return Object.values(row).some(val => val !== null && val !== undefined && val !== '')
  })

  if (validData.length === 0) {
    ElMessage.warning('请至少保留一条有效数据')
    return
  }

  emit('confirm', validData)
  ElMessage.success(`已成功导入 ${validData.length} 条数据`)
  visible.value = false
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.excel-editor-dialog {
  height: 90%;
}

.table-container {
  height: calc(90vh - 200px);
  overflow: auto;
}
</style>