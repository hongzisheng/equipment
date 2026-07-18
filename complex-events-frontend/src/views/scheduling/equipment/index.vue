<template>
  <div class="device-management-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header" @click="togglePanel('device')">
        <div class="panel-title">
          <img src="/src/assets/iconfont/设备管理.png" alt="设备管理" class="panel-icon mr6" />
          设备管理
        </div>
        <div class="panel-tools" @click.stop>
          <el-button size="small" circle @click="openAddDevice">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button link @click="togglePanel('device')">
            <el-icon>
              <component :is="devicePanelOpen ? ArrowUpBold : ArrowDownBold" />
            </el-icon>
          </el-button>
        </div>
      </div>
      <el-collapse-transition>
        <div v-show="devicePanelOpen" class="panel-body">
          <div class="filter-toolbar">
            <el-input v-model="deviceKeyword" placeholder="搜索设备名称" clearable class="search-input" @input="handleKeywordInput" />
          </div>
          
          <!-- 设备表格 -->
          <el-table 
            ref="deviceTableRef"
            :data="pagedDevices" 
            height="500" 
            size="large" 
            class="device-table"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="设备名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="equipment_type_name" label="设备类型" min-width="130" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" min-width="130" show-overflow-tooltip />
            
          </el-table>
          
          <!-- 分页组件 -->
          <div class="pagination-container">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="currentPage"
              :page-sizes="[10, 20, 30]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="filteredDevices.length"
            />
          </div>
          
          <!-- 显示选中项信息和操作按钮 -->
          <div class="selected-info-container" v-if="selectedDevices.length > 0">
            <div class="selected-info">
              已选择 {{ selectedDevices.length }} 项
            </div>
            <div class="selected-actions">
              <el-button type="primary" size="small" @click="saveToBackend">
                导出选中项
              </el-button>
              <el-button type="danger" size="small" @click="deleteSelectedDevices">
                删除选中项
              </el-button>
            </div>
          </div>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 添加设备对话框 -->
    <el-dialog v-model="addDeviceVisible" title="添加设备/机具" width="600px" :close-on-click-modal="false">
      <el-form label-width="120px">
        <el-form-item label="设备名称">
          <el-autocomplete
            v-model="deviceForm.name"
            :fetch-suggestions="querySearchEquipment"
            placeholder="请输入设备名称（可联想选择）"
            @select="onSelectEquipmentName"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="设备编号">
          <el-input v-model="deviceForm.code" placeholder="例如 EQ-1001 或 TOOL-001" />
        </el-form-item>
        <el-form-item label="设备分类">
          <el-select v-model="deviceForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option-group label="机具类">
              <el-option label="检测与监测类" value="检测与监测类" />
              <el-option label="拆装与维修类" value="拆装与维修类" />
              <el-option label="清洁与处理类" value="清洁与处理类" />
              <el-option label="吊装与运输类" value="吊装与运输类" />
              <el-option label="焊接与热处理类" value="焊接与热处理类" />
              <el-option label="安全与防护类" value="安全与防护类" />
              <el-option label="新兴智能机具" value="新兴智能机具" />
              <el-option label="其他专用机具" value="其他专用机具" />
            </el-option-group>
            <el-option-group label="设备类">
              <el-option label="静设备" value="静设备" />
              <el-option label="动设备" value="动设备" />
              <el-option label="电气" value="电气" />
              <el-option label="仪表" value="仪表" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="deviceForm.type" placeholder="请选择设备类型" filterable style="width: 100%">
            <el-option
              v-for="opt in equipmentTypeOptions"
              :key="opt.id"
              :label="`${opt.name}（${opt.id}）`"
              :value="opt.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备规格">
          <el-select v-model="deviceForm.size" placeholder="请选择规格" style="width: 100%">
            <el-option label="大型" value="大型" />
            <el-option label="中型" value="中型" />
            <el-option label="小型" value="小型" />
          </el-select>
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="deviceForm.location" placeholder="请输入存放位置" />
        </el-form-item>
        <el-form-item label="设备描述">
          <el-input v-model="deviceForm.description" type="textarea" :rows="2" placeholder="请输入设备描述" />
        </el-form-item>
        <el-form-item label="应用场景">
          <el-input v-model="deviceForm.applications" type="textarea" :rows="2" placeholder="请输入典型应用场景" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="deviceForm.status" placeholder="请选择">
            <el-option label="正常" value="正常" />
            <el-option label="维修中" value="维修中" />
            <el-option label="待检" value="待检" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDeviceVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!deviceForm.name || !deviceForm.code" @click="submitAddDevice">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { ArrowUpBold, ArrowDownBold, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const BASE = import.meta.env.VITE_APP_BASE_API || ''
const API = `${BASE}/api`

// 设备表格引用
const deviceTableRef = ref(null)

// 设备面板展开状态
const devicePanelOpen = ref(true)

// 设备搜索关键词
const deviceKeyword = ref('')
const deviceCategoryFilter = ref('')
const deviceTypeFilter = ref('')

// 选中的设备数据
const selectedDevices = ref([])

// 用于存储所有页面选中项的ID集合
const selectedDeviceIds = ref(new Set())

// 设备数据
const devices = ref([])

// 分页相关数据
const currentPage = ref(1)
const pageSize = ref(10)

// 设备数据过滤
const filteredDevices = computed(() => {
  return devices.value.filter(device => {
    const matchesKeyword = !deviceKeyword.value || 
      device.name.includes(deviceKeyword.value)
    
    return matchesKeyword
  })
})

// 分页后的数据
const pagedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDevices.value.slice(start, end)
})

// 处理分页大小变更
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1 // 重置为第一页
  nextTick(() => {
    restoreSelectionOnCurrentPage()
  })
}

// 处理当前页变更
const handleCurrentChange = (val) => {
  currentPage.value = val
  nextTick(() => {
    restoreSelectionOnCurrentPage()
  })
}

// 处理选中的行变化
const handleSelectionChange = (selection) => {
  // 更新当前选中项的状态
  selectedDevices.value = selection
  
  // 更新选中项ID集合：从当前选中项中移除不在selection中的项，添加新的选中项
  const selectedIds = new Set(selection.map(item => item.id))
  const currentPageIds = new Set(pagedDevices.value.map(item => item.id))
  
  // 移除当前页面中未被选中的项
  currentPageIds.forEach(id => {
    if (!selectedIds.has(id)) {
      selectedDeviceIds.value.delete(id)
    }
  })
  
  // 添加当前页面中被选中的项
  selection.forEach(item => {
    if (item.id) {
      selectedDeviceIds.value.add(item.id)
    }
  })
  
  // 更新selectedDevices为所有页面选中的项
  selectedDevices.value = devices.value.filter(device => selectedDeviceIds.value.has(device.id))
}

// 全选当前页设备
const selectAllDevices = () => {
  if (deviceTableRef.value && pagedDevices.value.length > 0) {
    pagedDevices.value.forEach(row => {
      deviceTableRef.value.toggleRowSelection(row, true)
    })
  }
}

// 恢复当前页中已选行的勾选状态（不全选，只恢复 selectedDeviceIds 中已存在的）
const restoreSelectionOnCurrentPage = () => {
  if (!deviceTableRef.value) return
  pagedDevices.value.forEach(row => {
    if (selectedDeviceIds.value.has(row.id)) {
      deviceTableRef.value.toggleRowSelection(row, true)
    }
  })
}

// 全选所有设备（包括未在当前页面显示的）
const selectAllDevicesGlobally = () => {
  if (deviceTableRef.value && devices.value.length > 0) {
    devices.value.forEach(row => {
      selectedDeviceIds.value.add(row.id)
      // 只对当前页的数据执行界面勾选操作
      if (pagedDevices.value.some(pageRow => pageRow.id === row.id)) {
        deviceTableRef.value.toggleRowSelection(row, true)
      }
    })
    // 更新selectedDevices为所有页面选中的项
    selectedDevices.value = devices.value.filter(device => selectedDeviceIds.value.has(device.id))
  }
}

// 添加设备对话框显示状态
const addDeviceVisible = ref(false)

// 设备表单数据
const deviceForm = reactive({
  name: '',
  code: '',
  category: '',
  type: '',
  size: '',
  location: '',
  description: '',
  applications: '',
  status: '正常'
})

// 设备类型选项（示例数据）
const equipmentTypeOptions = ref([
  { id: 'EQ-001', name: '离心泵' },
  { id: 'EQ-002', name: '压缩机' },
  { id: 'EQ-003', name: '换热器' },
  { id: 'TOOL-001', name: '电焊机' },
  { id: 'TOOL-002', name: '切割机' }
])

// 切换面板展开状态
const togglePanel = (panel) => {
  if (panel === 'device') {
    devicePanelOpen.value = !devicePanelOpen.value
  }
}

// 打开添加设备对话框
const openAddDevice = () => {
  addDeviceVisible.value = true
}

// 查询设备名称建议
const querySearchEquipment = (queryString, cb) => {
  // 这里应该调用API获取设备名称建议
  const results = equipmentTypeOptions.value.filter(item => 
    item.name.toLowerCase().includes(queryString.toLowerCase())
  ).map(item => ({ value: item.name }))
  cb(results)
}

// 选择设备名称
const onSelectEquipmentName = (item) => {
  // 根据选择的设备名称自动填充其他字段
  const equipment = equipmentTypeOptions.value.find(e => e.name === item.value)
  if (equipment) {
    deviceForm.type = equipment.name
  }
}

// 提交添加设备
const submitAddDevice = async () => {
  try {
    const response = await fetch('/api/add-equipment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        equipment_type_id: deviceForm.code,
        equipment_name: deviceForm.name,
        equipment_category: deviceForm.category
      })
    })
    const result = await response.json()
    if (result.success) {
      ElMessage.success('设备添加成功')
      addDeviceVisible.value = false
      Object.keys(deviceForm).forEach(key => { deviceForm[key] = '' })
      deviceForm.status = '正常'
      await fetchDevices()
    } else {
      ElMessage.error(result.message || '添加失败')
    }
  } catch (e) {
    console.error('添加设备失败:', e)
    ElMessage.error('添加失败，请检查网络')
  }
}

// 从后端获取设备数据
const fetchDevices = async () => {
  try {
    const res = await axios.get(`${API}/equipment-instances`)
    const resData = res.data
    const deviceList = resData.data || resData.equipment_instances
    console.log('Fetched device data from backend:', deviceList)
    if (resData.success && deviceList && deviceList.length > 0) {
      devices.value = deviceList.map(item => ({
        id: item.id,
        name: item.name,
        equipment_type_id: item.equipment_type_id,
        equipment_type_name: item.equipment_type_name,
        category: item.category,
        status: '正常'
      }))
    } else {
      // 加载默认数据
      loadDefaultDevices()
    }
  } catch (error) {
    console.error('获取设备数据失败:', error)
    loadDefaultDevices()
  }
}

// 加载默认设备数据
const loadDefaultDevices = () => {
  devices.value = [
    { id: 1, name: '加热炉 F6001', equipment_type_id: 'EQ-1001', equipment_type_name: '加热炉', status: '正常', category: '静设备' },
    { id: 2, name: '精馏塔 T6001', equipment_type_id: 'EQ-1002', equipment_type_name: '精馏塔', status: '正常', category: '静设备' },
    { id: 3, name: '反应器 R6001', equipment_type_id: 'EQ-1003', equipment_type_name: '反应器', status: '维修中', category: '静设备' },
    { id: 4, name: '换热器 E6001', equipment_type_id: 'EQ-1004', equipment_type_name: '换热器', status: '维修中', category: '静设备' },
    { id: 5, name: '离心泵 P6001', equipment_type_id: 'EQ-2001', equipment_type_name: '离心泵', status: '正常', category: '动设备' },
    { id: 6, name: '压缩机 K6001', equipment_type_id: 'EQ-2002', equipment_type_name: '压缩机', status: '正常', category: '动设备' },
    { id: 7, name: '变压器 T6002', equipment_type_id: 'EQ-3001', equipment_type_name: '变压器', status: '正常', category: '电气' },
    { id: 8, name: 'DCS系统 D6001', equipment_type_id: 'EQ-4001', equipment_type_name: 'DCS系统', status: '正常', category: '仪表' }
  ]
}

// 保存选中设备到后端
const saveToBackend = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请先选择要保存的设备')
    return
  }

  try {
    // 同时将选中的设备发送到后端
    const selectedDeviceIdsArray = Array.from(selectedDeviceIds.value)
    console.log('Sending selected device IDs to backend:', selectedDeviceIdsArray)
    
    const response = await axios.post(`${API}/select-equipments`, {
      selected_equipment_ids: selectedDeviceIdsArray
    })

    const result = response.data
    console.log('Backend response:', result)
    if (result.success) {
      ElMessage.success(result.message || '已成功将选中的设备发送到后端')
    } else {
      ElMessage.error(result.message || '发送到后端失败')
    }
  } catch (e) {
    console.error('发送到后端失败:', e)
    ElMessage.error('操作失败，请检查网络连接')
  }
}

// 删除选中的设备
const deleteSelectedDevices = async () => {
  if (selectedDevices.value.length === 0) {
    ElMessage.warning('请先选择要删除的设备')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDevices.value.length} 个设备吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const selectedIds = selectedDevices.value.map(d => d.id)
    for (const id of selectedIds) {
      const response = await fetch(`/api/equipment-instances/${id}`, { method: 'DELETE' })
      const result = await response.json()
      if (!result.success) {
        console.error(`删除设备 ${id} 失败:`, result.message)
      }
    }

    ElMessage.success(`成功删除 ${selectedIds.length} 个设备`)
    await fetchDevices()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除设备失败:', e)
      ElMessage.error('删除失败，请检查网络')
    }
  }
}

// 处理关键字输入事件
const handleKeywordInput = () => {
  // 关键字变化时保持勾选状态
  nextTick(() => {
    restoreSelection()
  })
}

// 恢复选中状态
const restoreSelection = () => {
  if (deviceTableRef.value && pagedDevices.value.length > 0) {
    pagedDevices.value.forEach(row => {
      if (selectedDeviceIds.value.has(row.id)) {
        deviceTableRef.value.toggleRowSelection(row, true)
      }
    })
  }
}

// 页面加载时获取设备数据
onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-management-container {
  padding: 24px;
  min-height: 100%;
  box-sizing: border-box;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background-color: #ffffff;
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
}

.panel-header:hover {
  background-color: #fafafa;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  color: #1a1a1a;
}

.panel-icon {
  width: 24px;
  height: 24px;
  margin-right: 12px;
}

.panel-tools {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-tools .el-button {
  color: #64748b;
}

.panel-tools .el-button:hover {
  color: #3b82f6;
  background-color: #f0f7ff;
}

.panel-body {
  padding: 24px;
  background: #ffffff;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 24px 0 rgba(0, 0, 0, 0.04);
}

.filter-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  padding: 24px;
  background: #f8fafc;
  border-radius: 12px;
}

.search-input,
.category-select,
.type-select {
  width: 220px;
}

.search-input :deep(.el-input__wrapper),
.category-select :deep(.el-input__wrapper),
.type-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

/* 增大表格行高与表格样式优化 */
:deep(.device-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

:deep(.device-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.device-table th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

:deep(.device-table td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

:deep(.device-table .el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

.pagination-container {
  margin: 24px 0;
  display: flex;
  justify-content: flex-end;
}

.selected-info-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding: 16px 24px;
  background-color: #f0fdf4;
  border: none;
  border-radius: 12px;
}

.selected-info {
  font-weight: 600;
  color: #166534;
  font-size: 14px;
}

.selected-actions {
  display: flex;
  gap: 12px;
}

.selected-actions .el-button {
  border-radius: 8px;
  font-weight: 500;
}
</style>
