<template>
  <div class="worker-management-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header" @click="togglePanel('worker')">
        <div class="panel-title">
          <img src="/src/assets/工人管理.png" alt="工人管理" class="panel-icon mr6" />
          工人管理
        </div>
        <div class="panel-tools" @click.stop>
          <el-button size="small" circle @click="openAddWorker">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button link @click="togglePanel('worker')">
            <el-icon>
              <component :is="workerPanelOpen ? ArrowUpBold : ArrowDownBold" />
            </el-icon>
          </el-button>
        </div>
      </div>
      <el-collapse-transition>
        <div v-show="workerPanelOpen" class="panel-body">
          <!-- 工人池可视化区域 -->
          <div class="worker-pool-container">
            <div class="pool-header">
              <div class="pool-header-left">
                <span class="pool-title">工人池</span>
                <span class="pool-subtitle">Worker Pool</span>
              </div>
              <el-button type="primary" size="small" @click="openEditPoolDialog" class="pool-config-btn">
                <el-icon><Edit /></el-icon> 配置班组
              </el-button>
            </div>
            <div class="pool-cards-row">
              <div v-for="stat in poolStats" :key="stat.type" class="pool-card-v2" :class="'pool-card-' + stat.type">
                <div class="pool-card-accent"></div>
                <div class="pool-card-body">
                  <div class="pool-card-top">
                    <div class="pool-card-label-group">
                      <span class="pool-card-type-name">{{ stat.typeName }}</span>
                      <span class="pool-card-type-en">{{ stat.typeEn }}</span>
                    </div>
                    <div class="pool-card-ring" :class="'ring-' + stat.type">
                      <svg viewBox="0 0 36 36" class="ring-svg">
                        <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <path class="ring-fill" :style="{ strokeDasharray: stat.percentage + ' 100' }" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      </svg>
                      <span class="ring-text">{{ stat.percentage }}%</span>
                    </div>
                  </div>
                  <div class="pool-card-stats">
                    <div class="stat-block">
                      <span class="stat-num total-num">{{ stat.total }}</span>
                      <span class="stat-label">总人数</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-block">
                      <span class="stat-num assigned-num">{{ stat.assigned }}</span>
                      <span class="stat-label">已分配</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-block">
                      <span class="stat-num available-num">{{ stat.available }}</span>
                      <span class="stat-label">待分配</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="filter-toolbar">
            <el-input v-model="workerKeyword" placeholder="搜索姓名/工种/编号" clearable class="search-input" />
            <el-select v-model="workerCategoryFilter" placeholder="工种分类筛选" clearable class="category-select">
              <el-option label="全部" value="" />
              <el-option label="核心检修工种" value="核心检修工种" />
              <el-option label="检测与安全工种" value="检测与安全工种" />
              <el-option label="特种作业工种" value="特种作业工种" />
              <el-option label="新兴技术工种" value="新兴技术工种" />
              <el-option label="辅助工种" value="辅助工种" />
            </el-select>
          </div>
          
          <!-- 动态表格列 -->
          <el-table 
            ref="workerTableRef"
            :data="pagedWorkers" 
            height="500" 
            size="large" 
            class="worker-table"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column 
              v-for="column in tableColumns" 
              :key="column.prop"
              :prop="column.prop" 
              :label="column.label" 
              :min-width="column.minWidth"
              :show-overflow-tooltip="column.showOverflowTooltip"
            >
              <template #default="{ row }">
                <template v-if="column.prop === 'status'">
                <el-tag :type="getWorkerStatusType(row.status)">{{ row.status }}</el-tag>
              </template>
              <template v-else-if="column.prop === 'is_certified'">
                <span
                  v-if="formatCertifiedValue(row.is_certified) === '是'"
                  class="certified-yes"
                >
                  <el-icon><SuccessFilled /></el-icon> 是
                </span>
                <span
                  v-else-if="formatCertifiedValue(row.is_certified) === '否'"
                  class="certified-no"
                >
                  <el-icon><CircleCloseFilled /></el-icon> 否
                </span>
                <span v-else>{{ row.is_certified }}</span>
              </template>
              <template v-else-if="column.prop === 'compose'">
                <div v-if="parseCompose(row.compose).length" class="compose-tags">
                  <span
                    v-for="item in parseCompose(row.compose)"
                    :key="item.label"
                    class="compose-chip"
                    :class="'compose-' + item.cls"
                  >
                    {{ item.label }} <strong>{{ item.count }}</strong>
                  </span>
                </div>
                <span v-else class="compose-empty">未分配</span>
              </template>
              <template v-else>
                {{ row[column.prop] }}
              </template>
  </template>
            </el-table-column>
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
              :total="filteredWorkers.length"
            />
          </div>
          
          <!-- 显示选中项信息和操作按钮 -->
          <div class="selected-info-container" v-if="selectedWorkers.length > 0">
            <div class="selected-info">
              已选择 {{ selectedWorkers.length }} 项
            </div>
            <div class="selected-actions">
              <el-button type="primary" size="small" @click="saveToLocalStorage">
                导出选中项
              </el-button>
              <el-button type="danger" size="small" @click="deleteSelectedWorkers">
                删除选中项
              </el-button>
            </div>
          </div>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 添加工人对话框 -->
    <el-dialog v-model="addWorkerVisible" title="添加工人" width="600px" :close-on-click-modal="false">
      <el-form label-width="120px">
        <el-form-item label="姓名" required>
          <el-input v-model="workerForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="编号" required>
          <el-input v-model="workerForm.code" placeholder="例如 W001" />
        </el-form-item>
        <el-form-item label="工种" required>
          <el-select v-model="workerForm.type" placeholder="请选择工种" style="width: 100%">
            <el-option-group label="核心检修工种">
              <el-option label="焊工" value="焊工" />
              <el-option label="钳工" value="钳工" />
              <el-option label="仪表工" value="仪表工" />
              <el-option label="管工" value="管工" />
              <el-option label="电工" value="电工" />
              <el-option label="起重工" value="起重工" />
              <el-option label="防腐保温工" value="防腐保温工" />
              <el-option label="力工" value="力工" />
            </el-option-group>
            <el-option-group label="检测与安全工种">
              <el-option label="无损检测员(UT/RT)" value="无损检测员(UT/RT)" />
              <el-option label="安全员(HSE)" value="安全员(HSE)" />
              <el-option label="设备检验师" value="设备检验师" />
            </el-option-group>
            <el-option-group label="特种作业工种">
              <el-option label="带压堵漏工" value="带压堵漏工" />
              <el-option label="受限空间作业员" value="受限空间作业员" />
              <el-option label="高处作业工" value="高处作业工" />
              <el-option label="射线探伤工" value="射线探伤工" />
            </el-option-group>
            <el-option-group label="新兴技术工种">
              <el-option label="无人机操控员" value="无人机操控员" />
              <el-option label="3D扫描建模师" value="3D扫描建模师" />
              <el-option label="智能检测工程师" value="智能检测工程师" />
              <el-option label="机器人操作员" value="机器人操作员" />
            </el-option-group>
            <el-option-group label="辅助工种">
              <el-option label="脚手架工" value="脚手架工" />
              <el-option label="保温工" value="保温工" />
              <el-option label="油漆工" value="油漆工" />
              <el-option label="清洁工" value="清洁工" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="技能">
          <el-input v-model="workerForm.skills" type="textarea" :rows="2" placeholder="请输入技能，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="证书">
          <el-input v-model="workerForm.certification" type="textarea" :rows="2" placeholder="请输入相关证书，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="workerForm.status" placeholder="请选择">
            <el-option label="作业中" value="作业中" />
            <el-option label="待命" value="待命" />
            <el-option label="休假中" value="休假中" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addWorkerVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!workerForm.name || !workerForm.code || !workerForm.type" @click="submitAddWorker">确定</el-button>
      </template>
    </el-dialog>

    <!-- 配置班组对话框（工人池已分配人数） -->
    <el-dialog v-model="editPoolDialogVisible" title="配置班组构成" width="500px">
      <el-form :model="teamCompose" label-width="100px">
        <el-form-item label="普工数量">
          <el-input-number v-model="teamCompose.普工" :min="0" :max="poolStats.find(s => s.type === 'general')?.total || 100" />
        </el-form-item>
        <el-form-item label="技工数量">
          <el-input-number v-model="teamCompose.技工" :min="0" :max="poolStats.find(s => s.type === 'skilled')?.total || 100" />
        </el-form-item>
        <el-form-item label="高级技工数量">
          <el-input-number v-model="teamCompose.高级技工" :min="0" :max="poolStats.find(s => s.type === 'senior')?.total || 100" />
        </el-form-item>
        <div class="dialog-tip">注：已分配人数不能超过对应工种总人数</div>
      </el-form>
      <template #footer>
        <el-button @click="editPoolDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTeamCompose">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick} from 'vue'
import { ArrowUpBold, ArrowDownBold, Plus, SuccessFilled, CircleCloseFilled, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 工人表格引用
const workerTableRef = ref(null)

// 工人面板展开状态
const workerPanelOpen = ref(true)

// 工人搜索关键词
const workerKeyword = ref('')
const workerCategoryFilter = ref('')

// 选中的工人数据
const selectedWorkers = ref([])

// 用于存储所有页面选中项的ID集合
const selectedWorkerIds = ref(new Set())

// 工人数据 - 包含所有API返回的字段
const workers = ref([])

// 表格列配置 - 根据API返回的字段动态生成
const tableColumns = ref([])

// 分页相关数据
const currentPage = ref(1)
const pageSize = ref(10)

// 班组构成（已分配人数），模拟班组长班组数据，格式：{"普工": 3, "技工": 1, "高级技工": 1}
const teamCompose = ref({
  普工: 3,
  技工: 1,
  高级技工: 1
})

// 工人池配置对话框
const editPoolDialogVisible = ref(false)
// 临时存储对话框中的编辑值
const editPoolForm = reactive({
  普工: 0,
  技工: 0,
  高级技工: 0
})
const workerPoolData = ref([])
const fetchWorkerPool = async () => {
  try {
    console.log('fetchWorkerPool 开始执行');
    const response = await fetch('/api/worker-team')
    const result = await response.json()
    if (result.success) {
      workerPoolData.value = result.data
    } else {
      console.error('获取工人池数据失败:', result.message)
    }
  } catch (error) {
    console.error('获取工人池数据异常:', error)
  }
}
const openEditPoolDialog = () => {
  // 从当前 workerPoolData 中提取当前 assigned 值
  const general = workerPoolData.value.find(item => item.type === '普工')
  const skilled = workerPoolData.value.find(item => item.type === '技工')
  const senior = workerPoolData.value.find(item => item.type === '高级技工')
  editPoolForm.普工 = general ? general.assigned : 0
  editPoolForm.技工 = skilled ? skilled.assigned : 0
  editPoolForm.高级技工 = senior ? senior.assigned : 0
  editPoolDialogVisible.value = true
}
const saveTeamCompose = async () => {
  try {
    const response = await fetch('/api/worker-team', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        普工: editPoolForm.普工,
        技工: editPoolForm.技工,
        高级技工: editPoolForm.高级技工
      })
    })
    const result = await response.json()
    if (result.success) {
      ElMessage.success('班组配置已保存')
      editPoolDialogVisible.value = false
      // 刷新工人池数据
      await fetchWorkerPool()
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (error) {
    console.error('保存班组配置失败:', error)
    ElMessage.error('保存失败，请检查网络')
  }
}

// 计算工人池统计数据（用于展示）
const poolStats = computed(() => {
  return workerPoolData.value.map(item => ({
    type: item.type === '普工' ? 'general' : (item.type === '技工' ? 'skilled' : 'senior'),
    typeName: item.type,
    typeEn: item.type === '普工' ? 'General Worker' : (item.type === '技工' ? 'Skilled Worker' : 'Senior Technician'),
    tagType: item.type === '普工' ? 'info' : (item.type === '技工' ? 'success' : 'warning'),
    total: item.total,
    assigned: item.assigned,
    available: item.available,
    percentage: item.total > 0 ? Math.round((item.assigned / item.total) * 100) : 0,
    progressColor: item.type === '普工' ? '#409EFF' : (item.type === '技工' ? '#67C23A' : '#E6A23C')
  }))
})

const filteredWorkers = computed(() => {
  return workers.value.filter(worker => {
    const matchesKeyword = !workerKeyword.value || 
      (worker.name && worker.name.includes(workerKeyword.value)) || 
      (worker.code && worker.code.includes(workerKeyword.value)) || 
      (worker.type && worker.type.includes(workerKeyword.value)) ||
      (worker.worker_type && worker.worker_type.includes(workerKeyword.value))
    
    const matchesCategory = !workerCategoryFilter.value || worker.category === workerCategoryFilter.value
    
    return matchesKeyword && matchesCategory
  })
})

// 分页后的数据
const pagedWorkers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredWorkers.value.slice(start, end)
})

// 处理分页大小变更
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  nextTick(() => {
    selectAllWorkersGlobally()
  })
}

// 处理当前页变更
const handleCurrentChange = (val) => {
  currentPage.value = val
  nextTick(() => {
    selectAllWorkersGlobally()
  })
}

// 处理选中的行变化
const handleSelectionChange = (selection) => {
  selectedWorkers.value = selection
  
  const selectedIds = new Set(selection.map(item => item.id))
  const currentPageIds = new Set(pagedWorkers.value.map(item => item.id))
  
  currentPageIds.forEach(id => {
    if (!selectedIds.has(id)) {
      selectedWorkerIds.value.delete(id)
    }
  })
  
  selection.forEach(item => {
    if (item.id) {
      selectedWorkerIds.value.add(item.id)
    }
  })
  
  selectedWorkers.value = workers.value.filter(worker => selectedWorkerIds.value.has(worker.id))
}
// 全选所有工人
const selectAllWorkersGlobally = () => {
  if (workerTableRef.value && workers.value.length > 0) {
    workers.value.forEach(row => {
      selectedWorkerIds.value.add(row.id)
      if (pagedWorkers.value.some(pageRow => pageRow.id === row.id)) {
        workerTableRef.value.toggleRowSelection(row, true)
      }
    })
    selectedWorkers.value = workers.value.filter(worker => selectedWorkerIds.value.has(worker.id))
  }
}

// 添加工人对话框显示状态
const addWorkerVisible = ref(false)

// 工人表单数据
const workerForm = reactive({
  name: '',
  code: '',
  type: '',
  skills: '',
  certification: '',
  status: '待命'
})

// 获取工人数据并动态生成表格列
const fetchWorkers = async () => {
  try {
    const response = await fetch('/api/workers')
    const data = await response.json()
    console.log('获取工人数据成功:', data)
    
    if (data.success && data.workers && data.workers.length > 0) {
      workers.value = data.workers.map(worker => {
        return {
          ...worker,
          is_certified: formatCertifiedValue(worker.is_certified)
        }
      })
      generateTableColumns(data.workers[0])
      nextTick(() => {
        selectAllWorkersGlobally()
      })
    } else {
      loadDefaultWorkers()
    }
  } catch (error) {
    console.error('获取工人数据失败:', error)
    loadDefaultWorkers()
  }
}

// 加载默认工人数据
const loadDefaultWorkers = () => {
  workers.value = [
    {
      id: 1,
      name: '张三',
      code: 'W001',
      worker_type: '焊工',
      type: '焊工',
      status: '作业中',
      category: '核心检修工种',
      skills: '电弧焊,气焊',
      certification: '焊工证',
      is_certified: '是',
      experience: '5年',
      level: '高级'
    },
    {
      id: 2,
      name: '李四',
      code: 'W002',
      worker_type: '电工',
      type: '电工',
      status: '待命',
      category: '核心检修工种',
      skills: '高压电,低压电',
      certification: '电工证',
      is_certified: '是',
      experience: '3年',
      level: '中级'
    },
    {
      id: 3,
      name: '王五',
      code: 'W003',
      worker_type: '力工',
      type: '力工',
      status: '待命',
      category: '核心检修工种',
      skills: '搬运,清理',
      certification: '',
      is_certified: '否',
      experience: '2年',
      level: '初级'
    },
    {
      id: 4,
      name: '赵六',
      code: 'W004',
      worker_type: '带压堵漏工',
      type: '带压堵漏工',
      status: '作业中',
      category: '特种作业工种',
      skills: '带压堵漏',
      certification: '特种作业证',
      is_certified: '是',
      experience: '8年',
      level: '高级'
    }
  ].map(worker => {
    return {
      ...worker,
      is_certified: formatCertifiedValue(worker.is_certified)
    }
  })
  
  generateTableColumns(workers.value[0])
  
  nextTick(() => {
    selectAllWorkersGlobally()
  })
}

// 根据数据字段动态生成表格列（过滤掉创建时间、emp_id等）
const generateTableColumns = (sampleData) => {
  const columns = []
  
  // 定义字段到列名的映射
  const fieldLabelMap = {
    id:'工号',
    name: '姓名',
    code: '编号',
    worker_type: '工种',
    worker_type_id: '工种ID',
    type: '类型',
    status: '状态',
    category: '分类',
    skills: '技能',
    certification: '证书',
    is_certified: '是否持证',
    experience: '经验',
    level: '等级',
    phone: '电话',
    email: '邮箱',
    department: '部门',
    organization:'组织',
    compose:'班组'
  }
  
  // 需要跳过的字段（不显示在表格中）
  const skipFields = ['_id', 'created_time', 'updated_time', 'emp_id', 'employee_id', 'created_at', 'updated_at','创建时间']
  
  // 定义特殊字段的宽度和属性
  const specialFields = {
    skills: { minWidth: 180, showOverflowTooltip: true },
    certification: { minWidth: 180, showOverflowTooltip: true },
    name: { minWidth: 120 },
    worker_type: { minWidth: 120 },
    type: { minWidth: 120 },
    category: { minWidth: 150 },
    is_certified: { minWidth: 100 },
    id: { minWidth: 80 },
    compose: { minWidth: 200, showOverflowTooltip: false },
  }
  
  // 遍历数据的所有字段生成列配置
  Object.keys(sampleData).forEach(field => {
    // 跳过不需要显示的字段
    if (skipFields.includes(field)) return
    
    const columnConfig = {
      prop: field,
      label: fieldLabelMap[field] || field,
      minWidth: specialFields[field]?.minWidth || 120,
      showOverflowTooltip: specialFields[field]?.showOverflowTooltip || false,
      customRender: specialFields[field]?.customRender || false
    }
    
    columns.push(columnConfig)
  })
  const composeIndex = columns.findIndex(col => col.prop === 'compose')
  if (composeIndex !== -1) {
    const composeColumn = columns.splice(composeIndex, 1)[0]
    columns.push(composeColumn)
  }
  tableColumns.value = columns
}

// 页面加载时获取数据
onMounted(async () => {
  console.log('组件已挂载');
  try {
    await fetchWorkers();
    await fetchWorkerPool();
  } catch (error) {
    console.error('在 onMounted 中获取数据失败:', error);
    // 可以在这里设置一个错误状态，并在模板中显示给用户
  }
});

// 切换面板展开状态
const togglePanel = (panel) => {
  if (panel === 'worker') {
    workerPanelOpen.value = !workerPanelOpen.value
  }
}

// 打开添加工人对话框
const openAddWorker = () => {
  addWorkerVisible.value = true
}

// 提交添加工人
const submitAddWorker = async () => {
  try {
    const response = await fetch('/api/add-worker', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        worker_type: workerForm.type,
        worker_name: workerForm.name,
        is_certified: workerForm.certification ? 1 : 0,
        organization: '',
        compose: ''
      })
    })
    const result = await response.json()
    if (result.success) {
      ElMessage.success('工人添加成功')
      addWorkerVisible.value = false
      Object.keys(workerForm).forEach(key => { workerForm[key] = '' })
      workerForm.status = '待命'
      await fetchWorkers()
    } else {
      ElMessage.error(result.message || '添加失败')
    }
  } catch (e) {
    console.error('添加工人失败:', e)
    ElMessage.error('添加失败，请检查网络')
  }
}

// 导出选中的工人数据
const saveToLocalStorage = async () => {
  if (selectedWorkers.value.length === 0) {
    ElMessage.warning('请先选择要导出的工人')
    return
  }

  try {
    selectedWorkers.value = workers.value.filter(worker => selectedWorkerIds.value.has(worker.id))
    
    const selectedWorkerIdsArray = Array.from(selectedWorkerIds.value);
    console.log('Sending selected worker IDs to backend:', selectedWorkerIdsArray);
    
    const response = await fetch('/api/select-workers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        selected_worker_ids: selectedWorkerIdsArray
      })
    });

    const result = await response.json();
    
    if (result.success) {
      ElMessage.success(result.message || '已成功将选中的工人发送到后端');
    } else {
      ElMessage.error(result.message || '发送到后端失败');
    }
  } catch (e) {
    console.error('保存或发送到后端失败:', e)
    ElMessage.error('操作失败，请检查浏览器设置和网络连接')
  }
}

// 删除选中的工人数据
const deleteSelectedWorkers = async () => {
  if (selectedWorkers.value.length === 0) {
    ElMessage.warning('请先选择要删除的工人')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedWorkers.value.length} 个工人吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const selectedIds = selectedWorkers.value.map(worker => worker.id)
    for (const id of selectedIds) {
      const response = await fetch(`/api/workers/${id}`, { method: 'DELETE' })
      const result = await response.json()
      if (!result.success) {
        console.error(`删除工人 ${id} 失败:`, result.message)
      }
    }
    
    ElMessage.success(`成功删除 ${selectedIds.length} 个工人`)
    await fetchWorkers()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除工人失败:', e)
      ElMessage.error('删除失败，请检查网络')
    }
  }
}

// 根据工种类型获取分类
const getWorkerCategory = (type) => {
  const coreTypes = ['焊工', '钳工', '仪表工', '管工', '电工', '起重工', '防腐保温工', '力工']
  const safetyTypes = ['无损检测员(UT/RT)', '安全员(HSE)', '设备检验师']
  const specialTypes = ['带压堵漏工', '受限空间作业员', '高处作业工', '射线探伤工']
  const emergingTypes = ['无人机操控员', '3D扫描建模师', '智能检测工程师', '机器人操作员']
  const auxiliaryTypes = ['脚手架工', '保温工', '油漆工', '清洁工']
  
  if (coreTypes.includes(type)) return '核心检修工种'
  if (safetyTypes.includes(type)) return '检测与安全工种'
  if (specialTypes.includes(type)) return '特种作业工种'
  if (emergingTypes.includes(type)) return '新兴技术工种'
  if (auxiliaryTypes.includes(type)) return '辅助工种'
  return '其他'
}

// 解析班组 compose 字段，返回 [{label, count, cls}] 数组
const COMPOSE_STYLE_MAP = {
  '普工': 'general',
  '技工': 'skilled',
  '高级技工': 'senior',
}

const parseCompose = (value) => {
  if (!value) return []
  let obj = value
  if (typeof value === 'string') {
    try { obj = JSON.parse(value) } catch { return [] }
  }
  if (typeof obj !== 'object' || Array.isArray(obj)) return []
  return Object.entries(obj)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({
      label: k,
      count: v,
      cls: COMPOSE_STYLE_MAP[k] || 'default',
    }))
}

// 获取工人状态标签类型
const getWorkerStatusType = (status) => {
  switch (status) {
    case '作业中': return 'success'
    case '待命': return 'info'
    case '休假中': return 'danger'
    default: return 'info'
  }
}

// 格式化是否持证字段的值
const formatCertifiedValue = (value) => {
  if (value === 1 || value === '1') return '是'
  if (value === 0 || value === '0') return '否'
  return value
}
</script>

<style scoped>
.worker-management-container {
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

/* 工人池样式 */
.worker-pool-container {
  margin-bottom: 24px;
  padding: 28px 28px 24px;
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22px;
}

.pool-header-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.pool-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.3px;
}

.pool-subtitle {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.pool-config-btn {
  border-radius: 8px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* Card row layout */
.pool-cards-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

/* Modern pool card */
.pool-card-v2 {
  position: relative;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e8ecf1;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.pool-card-v2:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
}

/* Top accent bar */
.pool-card-accent {
  height: 4px;
}

.pool-card-general .pool-card-accent {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}
.pool-card-skilled .pool-card-accent {
  background: linear-gradient(90deg, #10b981, #34d399);
}
.pool-card-senior .pool-card-accent {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.pool-card-body {
  padding: 20px 22px 22px;
}

/* Card top: label + ring chart */
.pool-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.pool-card-label-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pool-card-type-name {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
}

.pool-card-type-en {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

/* Ring chart */
.pool-card-ring {
  position: relative;
  width: 52px;
  height: 52px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #f1f5f9;
  stroke-width: 3;
}

.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.pool-card-general .ring-fill {
  stroke: #3b82f6;
}
.pool-card-skilled .ring-fill {
  stroke: #10b981;
}
.pool-card-senior .ring-fill {
  stroke: #f59e0b;
}

.ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
}

/* Stats row */
.pool-card-stats {
  display: flex;
  align-items: center;
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px 0;
}

.stat-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}

.total-num {
  color: #3b82f6;
}
.assigned-num {
  color: #10b981;
}
.available-num {
  color: #f59e0b;
}

.stat-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: #e2e8f0;
  flex-shrink: 0;
}

/* Card subtle left border glow on hover */
.pool-card-general:hover {
  border-color: #93c5fd;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 60%);
}
.pool-card-skilled:hover {
  border-color: #6ee7b7;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 60%);
}
.pool-card-senior:hover {
  border-color: #fcd34d;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 60%);
}

.dialog-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
  text-align: center;
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
.category-select {
  width: 220px;
}

.search-input :deep(.el-input__wrapper),
.category-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

/* 分页容器样式 */
.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* 选中项信息容器样式 */
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

.config-complete-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.config-complete-container .el-button {
  border-radius: 8px;
  padding: 10px 24px;
  font-weight: 500;
}

/* 表格样式优化 */
:deep(.worker-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

:deep(.worker-table .el-table__inner-wrapper::before) {
  display: none;
}

:deep(.worker-table th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

:deep(.worker-table td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

:deep(.worker-table .el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

/* 是否持证标签样式 */
.certified-yes {
  color: #059669;
  background-color: #d1fae5;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  line-height: 12px;
  border: none;
}

.certified-no {
  color: #dc2626;
  background-color: #fee2e2;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  line-height: 12px;
  border: none;
}

/* 班组 compose 列标签 */
.compose-tags {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
}

.compose-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 26px;
  padding: 0 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  transition: all 0.15s ease;
}

.compose-chip strong {
  font-weight: 700;
  margin-left: 2px;
}

.compose-chip.compose-general {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}
.compose-chip.compose-general:hover {
  background: #dbeafe;
}

.compose-chip.compose-skilled {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.compose-chip.compose-skilled:hover {
  background: #dcfce7;
}

.compose-chip.compose-senior {
  background: #fffbeb;
  color: #b45309;
  border: 1px solid #fde68a;
}
.compose-chip.compose-senior:hover {
  background: #fef3c7;
}

.compose-chip.compose-default {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e2e8f0;
}

.compose-empty {
  color: #94a3b8;
  font-size: 13px;
  font-style: italic;
}
</style>