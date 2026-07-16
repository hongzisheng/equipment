<template>
  <div class="task-management-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header" @click="togglePanel('task')">
        <div class="panel-title">
          <el-icon class="panel-icon mr6"><List /></el-icon>
          工单管理
        </div>
        <div class="panel-tools" @click.stop>
          <el-button size="small" circle @click="refreshWorkOrders">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button link @click="togglePanel('task')">
            <el-icon>
              <component :is="taskPanelOpen ? ArrowUpBold : ArrowDownBold" />
            </el-icon>
          </el-button>
        </div>
      </div>
      <el-collapse-transition>
        <div v-show="taskPanelOpen" class="panel-body" style="height: 80vh;">
          <!-- 筛选工具栏 -->
          <div class="filter-toolbar">
            <el-input
              v-model="taskKeyword"
              placeholder="搜索工单编号/标题/设备"
              clearable
              size="small"
              class="search-input"
              :prefix-icon="Search"
            />
            <el-select
              v-model="taskStatusFilter"
              placeholder="状态"
              clearable
              size="small"
              class="status-select"
            >
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已暂停" value="paused" />
            </el-select>
            <el-select
              v-model="taskPriorityFilter"
              placeholder="优先级"
              clearable
              size="small"
              class="priority-select"
            >
              <el-option label="全部" value="" />
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
            <el-button type="primary" size="small" @click="refreshWorkOrders">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>

          <!-- 工单表格 -->
          <el-table 
            :data="filteredWorkOrders" 
            height="calc(80vh - 120px)" 
            size="large" 
            class="task-table"
            v-loading="loading"
            border
            stripe
          >
            <el-table-column type="index" label="序号" width="50" fixed="left" align="center" />
            
            <el-table-column prop="order_number" label="工单编号" min-width="120" show-overflow-tooltip fixed="left">
              <template #default="{ row }">
                <span class="order-number">{{ row.order_number }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="title" label="工单标题" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="title-text">{{ row.title }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="equipment_name" label="设备名称" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="equipment-info">
                  <el-icon><Monitor /></el-icon>
                  <span>{{ row.equipment_name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" min-width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small" effect="light" class="status-tag">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="priority" label="优先级" min-width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small" effect="light" class="priority-tag">
                  {{ getPriorityText(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="scheduled_start_time" label="计划开始时间" min-width="100" align="center">
              <template #default="{ row }">
                {{ formatScheduleTime(row.scheduled_start_time) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="scheduled_end_time" label="计划结束时间" min-width="100" align="center">
              <template #default="{ row }">
                {{ formatScheduleTime(row.scheduled_end_time) }}
              </template>
            </el-table-column>
            
            <!-- 新增：工单任务详情列 -->
            <el-table-column label="工单任务" min-width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="info" plain @click="showTaskDetails(row)">
                  <el-icon><List /></el-icon> 任务详情
                </el-button>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" min-width="140" fixed="right" align="center">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button size="small" type="primary" plain @click="viewWorkOrder(row)">
                    <el-icon><View /></el-icon> 查看
                  </el-button>
                  <el-button size="small" type="success" plain @click="editWorkOrder(row)">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 统计信息 -->
          <div class="table-footer">
            <div class="create-btn-wrapper">
          <el-button type="primary" @click="openCreateWorkOrderDialog">
      <el-icon><Plus /></el-icon> 新建工单
    </el-button></div>
            <div class="stats-info">        
              <el-tag type="info" size="small">总工单数: {{ filteredWorkOrders.length }}</el-tag>
              <el-tag type="primary" size="small">待处理: {{ getStatusCount('pending') }}</el-tag>
              <el-tag type="success" size="small">已完成: {{ getStatusCount('completed') }}</el-tag>
              <el-tag type="warning" size="small">进行中: {{ getStatusCount('in_progress') }}</el-tag>
            </div>
          </div>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 查看工单对话框 -->
    <el-dialog v-model="viewDialogVisible" title="查看工单详情" width="600px" :close-on-click-modal="false" destroy-on-close>
      <el-form label-width="120px" :model="currentWorkOrder" :disabled="true" class="detail-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工单编号">
              <el-input v-model="currentWorkOrder.order_number" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工单标题">
              <el-input v-model="currentWorkOrder.title" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备名称">
              <el-input v-model="currentWorkOrder.equipment_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备ID">
              <el-input v-model="currentWorkOrder.equipment_id" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-tag :type="getStatusType(currentWorkOrder.status)" size="small">
                {{ getStatusText(currentWorkOrder.status) }}
              </el-tag>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-tag :type="getPriorityType(currentWorkOrder.priority)" size="small">
                {{ getPriorityText(currentWorkOrder.priority) }}
              </el-tag>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划开始时间">
              <el-input :value="formatScheduleTime(currentWorkOrder.scheduled_start_time)" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划结束时间">
              <el-input :value="formatScheduleTime(currentWorkOrder.scheduled_end_time)" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="创建时间">
              <el-input :value="formatDateTime(currentWorkOrder.created_at)" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="创建人">
              <el-input v-model="currentWorkOrder.created_by" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="createWorkOrderDialogVisible" title="新建工单" width="750px" destroy-on-close>
  <el-form :model="newWorkOrderForm" label-width="120px">
    <el-form-item label="设备类型" required>
      <el-select v-model="newWorkOrderForm.equipmentTypeId" placeholder="请选择设备类型" @change="onEquipmentTypeChange">
        <el-option v-for="type in equipmentTypes" :key="type.id" :label="type.name" :value="type.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="设备实例" required>
      <el-select v-model="newWorkOrderForm.equipmentId" placeholder="请选择设备" @change="onEquipmentChange">
        <el-option v-for="eq in equipmentInstances" :key="eq.id" :label="eq.name" :value="eq.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="工序模板" required>
      <el-tree-select
        v-model="newWorkOrderForm.processTemplateIds"
        :data="processTreeData"
        multiple
        show-checkbox
        node-key="id"
        placeholder="请选择工序（勾选大工序可自动选中所有子工序）"
        @change="onProcessChange"
        :props="{ label: 'description', children: 'children' }"
        style="width: 100%"
      />
    </el-form-item>
    <el-form-item label="已选工序" v-if="selectedProcesses.length > 0">
  <div style="max-height: 150px; overflow-y: auto; border: 1px solid #e4e7ed; border-radius: 4px; padding: 8px; background-color: #f8f9fa;">
    <div v-for="proc in selectedProcesses" :key="proc.id" style="padding: 6px 0; border-bottom: 1px solid #e8e8e8; line-height: 1.4;">
      <div style="font-weight: 500; color: #303133; font-size: 13px;">{{ proc.description }}</div>
      <div style="font-size: 12px; color: #666; margin-top: 2px;">
        <span>工时分解: </span>
        <span v-if="proc.worker_price" style="color: #409eff; font-family: monospace;">
          {{ proc.worker_price }}
        </span>
      </div>
    </div>
  </div>
</el-form-item>

<!-- 修改工时合计部分，使用更紧凑的布局 -->
<el-form-item label="工时统计" v-if="selectedProcesses.length > 0">
  <div class="hours-summary-container">
    <div class="hours-row">
      <div class="hours-label">普工工时合计</div>
      <div class="hours-value">{{ totalCommonHours }} 天</div>
    </div>
    <div class="hours-row">
      <div class="hours-label">技工工时合计</div>
      <div class="hours-value">{{ totalSkilledHours }} 天</div>
    </div>
    <div class="hours-row">
      <div class="hours-label">高级技工工时合计</div>
      <div class="hours-value">{{ totalSeniorHours }} 天</div>
    </div>
  </div>
</el-form-item>

<!-- 修改价格合计部分 -->
<el-form-item label="价格合计" v-if="selectedProcesses.length > 0">
  <div class="price-summary-container">
    <div class="price-row">
      <div class="price-label">人工时价格合计</div>
      <div class="price-value">¥{{ totalWorkerPrice }}</div>
    </div>
    <div class="price-detail" style="font-size: 12px; color: #999; margin-top: 4px;">
      计算公式: 普工{{totalCommonHours}}天 × 126 + 技工{{totalSkilledHours}}天 × 173 + 高级{{totalSeniorHours}}天 × 236
    </div>
  </div>
</el-form-item>
    <el-form-item label="所需工人汇总" v-if="aggregatedWorkers && Object.keys(aggregatedWorkers).length">
      <div v-for="(count, type) in aggregatedWorkers" :key="type">
        {{ type }}: {{ count }} 人
      </div>
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="createWorkOrderDialogVisible = false">取消</el-button>
    <el-button type="primary" @click="submitNewWorkOrder" :loading="creatingWorkOrder">确定</el-button>
  </template>
</el-dialog>
    <!-- 编辑工单对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑工单" width="600px" :close-on-click-modal="false" destroy-on-close>
      <el-form label-width="120px" :model="currentWorkOrder" class="detail-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工单编号">
              <el-input v-model="currentWorkOrder.order_number" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工单标题">
              <el-input v-model="currentWorkOrder.title" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备名称">
              <el-input v-model="currentWorkOrder.equipment_name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备ID">
              <el-input v-model="currentWorkOrder.equipment_id" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="currentWorkOrder.status" style="width: 100%">
                <el-option label="待处理" value="pending" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="completed" />
                <el-option label="已暂停" value="paused" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="currentWorkOrder.priority" style="width: 100%">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划开始时间">
              <el-input v-model="currentWorkOrder.scheduled_start_time" placeholder="例如：第1天 08:00" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划结束时间">
              <el-input v-model="currentWorkOrder.scheduled_end_time" placeholder="例如：第6天 17:00" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="创建时间">
              <el-input :value="formatDateTime(currentWorkOrder.created_at)" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="创建人">
              <el-input v-model="currentWorkOrder.created_by" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditWorkOrder" :loading="editLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新增：工单任务详情弹窗 -->
    <el-dialog v-model="taskDetailDialogVisible" :title="`工单任务详情 - ${currentWorkOrderTitle}`" width="90vw" height="80vh" :close-on-click-modal="false" destroy-on-close>
      <div v-loading="taskLoading">
        <div class="task-dialog-header">
          <el-button type="primary" @click="openCreateTaskDialog" style="margin-bottom: 16px;">
            <el-icon><Plus /></el-icon> 新建工单任务
          </el-button>
        </div>
        <div v-if="filteredTasksByWorkOrder.length === 0" class="no-data-tip">
          <el-empty description="该工单暂无任务数据" />
        </div>
        <el-table v-else :data="sortedTasks" border stripe style="width: 100%" max-height="60vh">
          <el-table-column prop="task_code" label="任务编码" min-width="100" fixed="left" />
          <el-table-column prop="process_id" label="工序ID" min-width="90" />
          <el-table-column prop="process_name" label="工序名称" min-width="120" />
          <el-table-column prop="equipment_name" label="设备名称" min-width="120" />
          <el-table-column prop="description" label="描述" min-width="100" show-overflow-tooltip />
          <el-table-column prop="estimated_hours" label="预估工时(h)" width="100" align="center" />
          <el-table-column prop="scheduled_start_time" label="计划开始" width="120" align="center" />
          <el-table-column prop="scheduled_end_time" label="计划结束" width="120" align="center" />
          <el-table-column prop="actual_start_time" label="实际开始" width="120" align="center">
            <template #default="{ row }">{{ row.actual_start_time || '--' }}</template>
          </el-table-column>
          <el-table-column prop="actual_end_time" label="实际结束" width="120" align="center">
            <template #default="{ row }">{{ row.actual_end_time || '--' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getTaskStatusType(row.status)" size="small">
                {{ getTaskStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="predecessor_task_ids" label="前置任务" width="100" align="center">
            <template #default="{ row }">{{ row.predecessor_task_ids?.length ? row.predecessor_task_ids.join(',') : '无' }}</template>
          </el-table-column>
         
          <el-table-column prop="material_requirements" label="物料需求" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ formatJson(row.material_requirements) }}</template>
          </el-table-column>
          <el-table-column prop="tools_requirements" label="工具需求" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ formatJson(row.tools_requirements) }}</template>
          </el-table-column>
          <el-table-column prop="workers" label="人员" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ formatWorkers(row.workers) }}</template>
          </el-table-column>
          <el-table-column prop="approver_id" label="审批人ID" width="150" align="center">
            <template #default="{ row }">{{ row.approver_id || '--' }}</template>
          </el-table-column>
          <el-table-column prop="approval_comments" label="审批意见" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.approval_comments || '--' }}</template>
          </el-table-column>
          <el-table-column prop="approved_at" label="审批时间" width="150" align="center">
            <template #default="{ row }">{{ row.approved_at || '--' }}</template>
          </el-table-column>
         
        </el-table>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <span class="task-count">共 {{ filteredTasksByWorkOrder.length }} 条任务</span>
          <el-button @click="taskDetailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新增：创建工单任务对话框 -->
    <el-dialog v-model="createTaskDialogVisible" title="新建工单任务" width="800px" :close-on-click-modal="false" destroy-on-close>
      <el-form 
        :model="newTaskForm" 
        :rules="taskFormRules" 
        ref="taskFormRef"
        label-width="120px"
        class="task-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工序ID" prop="process_id">
              <el-input v-model="newTaskForm.process_id" placeholder="请输入工序ID" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工序名称" prop="process_name">
              <el-input v-model="newTaskForm.process_name" placeholder="请输入工序名称" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备ID" prop="equipment_id">
              <el-input v-model.number="newTaskForm.equipment_id" placeholder="请输入设备ID" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备名称" prop="equipment_name">
              <el-input v-model="newTaskForm.equipment_name" placeholder="请输入设备名称" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务编号" prop="task_code">
              <el-input v-model="newTaskForm.task_code" placeholder="请输入任务编号（可选）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计工时" prop="estimated_hours">
              <el-input-number 
                v-model="newTaskForm.estimated_hours" 
                :min="0.5" 
                :step="0.5" 
                placeholder="请输入预计工时"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计划开始时间" prop="scheduled_start_time">
              <el-input v-model="newTaskForm.scheduled_start_time" placeholder="例如：第1天 08:00" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划结束时间" prop="scheduled_end_time">
              <el-input v-model="newTaskForm.scheduled_end_time" placeholder="例如：第1天 12:00" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="是否里程碑">
              <el-switch v-model="newTaskForm.is_milestone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="前置任务">
              <el-select 
                v-model="newTaskForm.predecessor_task_ids" 
                multiple 
                placeholder="请选择前置任务（可选）"
                style="width: 100%"
              >
                <el-option
                  v-for="task in filteredTasksByWorkOrder"
                  :key="task.id"
                  :label="`${task.task_code} - ${task.process_name}`"
                  :value="task.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="任务描述">
          <el-input 
            v-model="newTaskForm.description" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入任务描述（可选）" 
          />
        </el-form-item>
        
        <el-divider>资源配置</el-divider>
        
        <el-form-item label="物料需求">
          <el-input 
            v-model="materialInput" 
            placeholder="格式：物料名:数量:单位，多个用逗号分隔，如：清洗剂:10:升,润滑油:5:公斤"
            @blur="parseMaterialRequirements"
          />
          <div v-if="Object.keys(newTaskForm.material_requirements).length > 0" class="requirements-preview">
            <el-tag 
              v-for="(req, material) in newTaskForm.material_requirements" 
              :key="material"
              size="small"
              closable
              @close="removeMaterial(material)"
            >
              {{ material }}: {{ req.quantity }}{{ req.unit }}
            </el-tag>
          </div>
        </el-form-item>
        
        <el-form-item label="工具需求">
          <el-input 
            v-model="toolsInput" 
            placeholder="格式：工具名:数量:单位，多个用逗号分隔，如：扳手:2:把,螺丝刀:1:把"
            @blur="parseToolsRequirements"
          />
          <div v-if="Object.keys(newTaskForm.tools_requirements).length > 0" class="requirements-preview">
            <el-tag 
              v-for="(req, tool) in newTaskForm.tools_requirements" 
              :key="tool"
              size="small"
              closable
              @close="removeTool(tool)"
            >
              {{ tool }}: {{ req.quantity }}{{ req.unit }}
            </el-tag>
          </div>
        </el-form-item>
        
        <el-form-item label="人员分配">
          <el-input 
            v-model="workersInput" 
            placeholder="格式：工种:姓名1,姓名2，多个工种用分号分隔，如：钳工:张三,李四；电工:王五"
            @blur="parseWorkers"
          />
          <div v-if="Object.keys(newTaskForm.workers).length > 0" class="requirements-preview">
            <el-tag 
              v-for="(names, role) in newTaskForm.workers" 
              :key="role"
              size="small"
              closable
              @close="removeWorkerRole(role)"
            >
              {{ role }}: {{ names.join(',') }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createTaskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitNewTask" :loading="createTaskLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted,reactive} from 'vue'
import { ArrowUpBold, ArrowDownBold, Search, Refresh, View, Edit, Monitor, List, Plus} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const BASE = import.meta.env.VITE_APP_BASE_API || ''
const API = `${BASE}/api`        // WorkOrderManagement 蓝图（/api 前缀）
const SAPI = `${BASE}/api` // SchedulingdataManagement 蓝图（/scheduling 前缀）

// 工单面板展开状态
const taskPanelOpen = ref(true)

// 搜索关键词和筛选条件
const taskKeyword = ref('')
const taskStatusFilter = ref('')
const taskPriorityFilter = ref('')

// 加载状态
const loading = ref(false)
const editLoading = ref(false)
const createTaskLoading = ref(false)

// 工单数据
const workOrders = ref([])
// 新建工单相关
const createWorkOrderDialogVisible = ref(false)
const creatingWorkOrder = ref(false)
const equipmentTypes = ref([])
const equipmentInstances = ref([])
const processTemplates = ref([])
const processTreeData = computed(() => {
  if (!processTemplates.value || processTemplates.value.length === 0) return []
  
  const mainProcess = processTemplates.value[0]
  const subProcesses = processTemplates.value.slice(1)
  
  return [
    {
      ...mainProcess,
      children: subProcesses.length > 0 ? subProcesses : undefined
    }
  ]
})
const newWorkOrderForm = reactive({
  equipmentTypeId: null,
  equipmentId: null,
  processTemplateIds: [],
})
// 获取设备类型列表
const fetchEquipmentTypes = async () => {
  try {
    const res = await axios.get(`${SAPI}/equipment-types`)
    equipmentTypes.value = res.data?.data || res.data
  } catch (error) {
    console.error('获取设备类型失败', error)
  }
}
// 根据设备类型获取设备实例
const fetchEquipmentByType = async (typeId) => {
  try {
    const res = await axios.get(`${SAPI}/equipment-instances/by-type/${encodeURIComponent(typeId)}`)
    equipmentInstances.value = res.data?.data?.equipment_instances || []|| res.data
  } catch (error) {
    console.error('获取设备实例失败', error)
  }
}
// 根据设备类型获取工序模板
const fetchProcessTemplatesByType = async (typeId) => {
  try {
    const res = await axios.get(`${API}/process-templates/equipment-type/${encodeURIComponent(typeId)}`)
    processTemplates.value = res.data?.data || res.data
  } catch (error) {
    console.error('获取工序模板失败', error)
  }
}
// 设备类型变化
const onEquipmentTypeChange = (typeId) => {
  newWorkOrderForm.equipmentId = null
  newWorkOrderForm.processTemplateIds = [];
  newWorkOrderForm.processTemplateId = null
  if (typeId) {
    fetchEquipmentByType(typeId)
    fetchProcessTemplatesByType(typeId)
  } else {
    equipmentInstances.value = []
    processTemplates.value = []
  }
}
// 工序变化，加载价格和工人需求
const onProcessChange = () => {

  }
const selectedProcesses = computed(() => {
  if (!newWorkOrderForm.processTemplateIds.length) return [];
  // processTemplates 的第一项是大工序，其余是子工序
  const allProcs = processTemplates.value;
  return allProcs.filter(p => 
    newWorkOrderForm.processTemplateIds.includes(p.id)
  );
});

const totalCommonHours = computed(() => {
  const processes = selectedProcesses.value;
  if (processes.length === 0) return 0;
  
  let total = 0;
  processes.forEach(process => {
    if (process.worker_price) {
      const prices = process.worker_price.split(',').map(Number);
      if (prices.length >= 1) {
        total += prices[0] || 0;
      }
    }
  });
  return parseFloat(total.toFixed(3));
});

// 计算技工工时合计
const totalSkilledHours = computed(() => {
  const processes = selectedProcesses.value;
  if (processes.length === 0) return 0;
  
  let total = 0;
  processes.forEach(process => {
    if (process.worker_price) {
      const prices = process.worker_price.split(',').map(Number);
      if (prices.length >= 2) {
        total += prices[1] || 0;
      }
    }
  });
  return parseFloat(total.toFixed(3));
});

// 计算高级技工工时合计
const totalSeniorHours = computed(() => {
  const processes = selectedProcesses.value;
  if (processes.length === 0) return 0;
  
  let total = 0;
  processes.forEach(process => {
    if (process.worker_price) {
      const prices = process.worker_price.split(',').map(Number);
      if (prices.length >= 3) {
        total += prices[2] || 0;
      }
    }
  });
  return parseFloat(total.toFixed(3));
});

// 计算总价格
const totalWorkerPrice = computed(() => {
  const commonPrice = totalCommonHours.value * 126;
  const skilledPrice = totalSkilledHours.value * 173;
  const seniorPrice = totalSeniorHours.value * 236;
  const total = commonPrice + skilledPrice + seniorPrice;
  return parseFloat(total.toFixed(2));
});

// 打开新建工单对话框
const openCreateWorkOrderDialog = () => {
  fetchEquipmentTypes()
  createWorkOrderDialogVisible.value = true
}

// 提交新建工单
const submitNewWorkOrder = async () => {
  console.log('提交数据:', {
  equipmentId: newWorkOrderForm.equipmentId,
  processTemplateIds: newWorkOrderForm.processTemplateIds
})
  if (!newWorkOrderForm.equipmentId || !newWorkOrderForm.processTemplateIds.length) {
    ElMessage.warning('请完整选择设备类型、设备和工序')
    return
  }
  
  
  // 把所有勾选的节点（包括大工序和子工序）全部传给后端。
  const processIdsToSend = newWorkOrderForm.processTemplateIds;
  
  if (processIdsToSend.length === 0) {
    ElMessage.warning('请至少选择一个工序')
    return
  }

  creatingWorkOrder.value = true
  try {
    const res = await axios.post(`${API}/manual-create-work-order`, {
      equipment_id: newWorkOrderForm.equipmentId,
      process_template_ids: processIdsToSend
    });
    const result = res.data
    if (result.success) {
      ElMessage.success('工单创建成功')
      createWorkOrderDialogVisible.value = false
      refreshWorkOrders()  // 刷新工单列表
      // 可选：刷新任务数据
      refreshAllWorkOrderTasks()
    } else {
      ElMessage.error(result.message || '创建失败')
      console.error('后端返回错误详情:', result)
    }
  } catch (error) {
    console.error('创建工单请求失败:', error)
    if (error.response && error.response.data && error.response.data.message) {
      ElMessage.error(`创建失败: ${error.response.data.message}`)
    } else {
      ElMessage.error('创建工单失败，请检查网络或后端日志')
    }
  } finally {
    creatingWorkOrder.value = false
  }
}
// 工单数据过滤
const filteredWorkOrders = computed(() => {
  return workOrders.value.filter(order => {
    const matchesKeyword = !taskKeyword.value || 
      (order.title && order.title.includes(taskKeyword.value)) || 
      (order.order_number && order.order_number.includes(taskKeyword.value)) ||
      (order.equipment_name && order.equipment_name.includes(taskKeyword.value))
    
    const matchesStatus = !taskStatusFilter.value || order.status === taskStatusFilter.value
    const matchesPriority = !taskPriorityFilter.value || order.priority === taskPriorityFilter.value
    
    return matchesKeyword && matchesStatus && matchesPriority
  })
})

// 获取指定状态的数量
const getStatusCount = (status) => {
  return workOrders.value.filter(order => order.status === status).length
}

// 查看对话框显示状态
const viewDialogVisible = ref(false)

// 编辑对话框显示状态
const editDialogVisible = ref(false)

// 当前工单数据
const currentWorkOrder = ref({
  id: null,
  order_number: '',
  title: '',
  equipment_id: '',
  equipment_name: '',
  status: 'pending',
  created_by: '',
  created_at: '',
  scheduled_start_time: '',
  scheduled_end_time: '',
  priority: 'medium'
})

// 新增：任务详情弹窗相关
const taskDetailDialogVisible = ref(false)
const taskLoading = ref(false)
const currentWorkOrderId = ref(null)
const currentWorkOrderTitle = ref('')
const allWorkOrderTasks = ref([]) // 存储所有工单的任务列表

// 新增：创建工单任务对话框相关
const createTaskDialogVisible = ref(false)
const taskFormRef = ref(null)

// 新增：新建任务表单数据
const newTaskForm = ref({
  work_order_id: null, // 将在打开对话框时设置
  task_code: '',
  process_id: '',
  process_name: '',
  equipment_id: null,
  equipment_name: '',
  description: '',
  estimated_hours: null,
  scheduled_start_time: '',
  scheduled_end_time: '',
  predecessor_task_ids: [],
  is_milestone: false,
  material_requirements: {},
  tools_requirements: {},
  workers: {}
})

// 新增：表单验证规则
const taskFormRules = {
  process_id: [
    { required: true, message: '请输入工序ID', trigger: 'blur' }
  ],
  process_name: [
    { required: true, message: '请输入工序名称', trigger: 'blur' }
  ],
  equipment_id: [
    { required: true, message: '请输入设备ID', trigger: 'blur' },
    { type: 'number', message: '设备ID必须为数字', trigger: 'blur' }
  ],
  equipment_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  estimated_hours: [
    { required: true, message: '请输入预计工时', trigger: 'blur' }
  ],
  scheduled_start_time: [
    { required: true, message: '请输入计划开始时间', trigger: 'blur' }
  ],
  scheduled_end_time: [
    { required: true, message: '请输入计划结束时间', trigger: 'blur' }
  ]
}

// 新增：输入框绑定数据
const materialInput = ref('')
const toolsInput = ref('')
const workersInput = ref('')

// 格式化计划时间（处理"第X天 HH:MM"格式）
const formatScheduleTime = (timeStr) => {
  if (!timeStr) return '--'
  return timeStr
}

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '--'
  return dateTimeStr
}

// 获取状态类型（标签颜色）
const getStatusType = (status) => {
  const statusMap = {
    pending: 'info',
    in_progress: 'primary',
    completed: 'success',
    paused: 'warning'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    paused: '已暂停'
  }
  return statusMap[status] || status
}

// 获取优先级类型（标签颜色）
const getPriorityType = (priority) => {
  const priorityMap = {
    high: 'danger',
    medium: 'warning',
    low: 'success'
  }
  return priorityMap[priority] || 'info'
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const priorityMap = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return priorityMap[priority] || priority
}

// 新增：任务状态映射
const getTaskStatusType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'primary',
    completed: 'success',
    paused: 'warning'
  }
  return map[status] || 'info'
}
const getTaskStatusText = (status) => {
  const map = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    paused: '已暂停'
  }
  return map[status] || status
}

// 辅助函数：格式化JSON对象显示
const formatJson = (obj) => {
  if (!obj) return '--'
  try {
    return JSON.stringify(obj)
  } catch {
    return '--'
  }
}

// 格式化工人显示
const formatWorkers = (workers) => {
  if (!workers) return '--'
  const parts = []
  for (const [role, names] of Object.entries(workers)) {
    if (Array.isArray(names) && names.length) {
      parts.push(`${role}: ${names.join(', ')}`)
    }
  }
  return parts.join('；') || '--'
}

// 切换面板展开状态
const togglePanel = (panel) => {
  if (panel === 'task') {
    taskPanelOpen.value = !taskPanelOpen.value
  }
}

// 刷新工单数据
const refreshWorkOrders = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API}/work-orders`)
    const data = res.data?.data || res.data
    if (Array.isArray(data)) {
      workOrders.value = data
      ElMessage.success(`成功加载 ${data.length} 条工单数据`)
    } else {
      ElMessage.warning('获取工单数据失败或数据格式不正确')
    }
  } catch (error) {
    console.error('获取工单数据失败:', error)
    ElMessage.error('获取工单数据失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 刷新所有工单任务数据
const refreshAllWorkOrderTasks = async () => {
  try {
    const res = await axios.get(`${API}/work-order-tasks`)
    const data = res.data?.data || res.data
    if (Array.isArray(data)) {
      allWorkOrderTasks.value = data
    } else {
      allWorkOrderTasks.value = []
    }
  } catch (error) {
    console.error('获取工单任务数据失败:', error)
    allWorkOrderTasks.value = []
  }
}

// 查看工单详情
const viewWorkOrder = (order) => {
  // 深拷贝工单数据到currentWorkOrder
  currentWorkOrder.value = { ...order }
  viewDialogVisible.value = true
}

// 编辑工单
const editWorkOrder = (order) => {
  // 深拷贝工单数据到currentWorkOrder
  currentWorkOrder.value = { ...order }
  editDialogVisible.value = true
}

// 提交编辑工单
const submitEditWorkOrder = async () => {
  editLoading.value = true
  try {
    // 在工单列表中找到当前编辑的工单并更新它
    const index = workOrders.value.findIndex(order => order.id === currentWorkOrder.value.id)
    if (index !== -1) {
      // 创建更新后的工单对象
      const updatedOrder = { ...currentWorkOrder.value }
      
      // 更新工单列表中的工单
      workOrders.value.splice(index, 1, updatedOrder)
      
      // 关闭对话框
      editDialogVisible.value = false
      
      ElMessage.success('工单更新成功')
    } else {
      ElMessage.error('未找到要更新的工单')
    }
  } catch (error) {
    console.error('更新工单失败:', error)
    ElMessage.error('更新工单失败，请重试')
  } finally {
    editLoading.value = false
  }
}

// 计算属性：根据当前工单ID过滤任务数据
const filteredTasksByWorkOrder = computed(() => {
  if (!currentWorkOrderId.value) return []
  return allWorkOrderTasks.value.filter(task => task.work_order_id === currentWorkOrderId.value)
})

// 新增：显示工单任务详情
const showTaskDetails = async (order) => {
  if (!order || !order.id) {
    ElMessage.warning('工单信息不完整')
    return
  }
  
  // 设置当前工单信息
  currentWorkOrderId.value = order.id
  currentWorkOrderTitle.value = `${order.order_number} - ${order.title}`
  
  // 打开弹窗
  taskDetailDialogVisible.value = true
  taskLoading.value = true
  
  try {
    // 如果还没有加载过任务数据，或者想刷新数据，则重新请求
    if (allWorkOrderTasks.value.length === 0) {
      await refreshAllWorkOrderTasks()
    }
    
    // 检查是否有该工单的任务
    const tasksForThisOrder = allWorkOrderTasks.value.filter(task => task.work_order_id === order.id)
    if (tasksForThisOrder.length === 0) {
      ElMessage.info('该工单暂无任务数据')
    }
  } catch (error) {
    console.error('获取工单任务失败:', error)
    ElMessage.error('获取工单任务失败')
  } finally {
    taskLoading.value = false
  }
}

// 新增：打开创建任务对话框
const openCreateTaskDialog = () => {
  // 重置表单
  resetTaskForm()
  // 设置工单ID
  newTaskForm.value.work_order_id = currentWorkOrderId.value
  // 打开对话框
  createTaskDialogVisible.value = true
}

// 新增：重置任务表单
const resetTaskForm = () => {
  newTaskForm.value = {
    work_order_id: null,
    task_code: '',
    process_id: '',
    process_name: '',
    equipment_id: null,
    equipment_name: '',
    description: '',
    estimated_hours: null,
    scheduled_start_time: '',
    scheduled_end_time: '',
    predecessor_task_ids: [],
    is_milestone: false,
    material_requirements: {},
    tools_requirements: {},
    workers: {}
  }
  materialInput.value = ''
  toolsInput.value = ''
  workersInput.value = ''
  if (taskFormRef.value) {
    taskFormRef.value.resetFields()
  }
}

// 新增：解析物料需求输入
const parseMaterialRequirements = () => {
  const input = materialInput.value.trim()
  if (!input) {
    newTaskForm.value.material_requirements = {}
    return
  }
  
  const materials = {}
  const items = input.split(/[,，]/)
  
  items.forEach(item => {
    const parts = item.trim().split(/[:：]/)
    if (parts.length >= 3) {
      const [name, quantity, unit] = parts
      materials[name.trim()] = {
        quantity: parseFloat(quantity.trim()) || 0,
        unit: unit.trim()
      }
    }
  })
  
  newTaskForm.value.material_requirements = materials
}

// 新增：解析工具需求输入
const parseToolsRequirements = () => {
  const input = toolsInput.value.trim()
  if (!input) {
    newTaskForm.value.tools_requirements = {}
    return
  }
  
  const tools = {}
  const items = input.split(/[,，]/)
  
  items.forEach(item => {
    const parts = item.trim().split(/[:：]/)
    if (parts.length >= 3) {
      const [name, quantity, unit] = parts
      tools[name.trim()] = {
        quantity: parseFloat(quantity.trim()) || 0,
        unit: unit.trim()
      }
    }
  })
  
  newTaskForm.value.tools_requirements = tools
}

// 新增：解析人员分配输入
const parseWorkers = () => {
  const input = workersInput.value.trim()
  if (!input) {
    newTaskForm.value.workers = {}
    return
  }
  
  const workers = {}
  const roles = input.split(/[;；]/)
  
  roles.forEach(roleItem => {
    const parts = roleItem.trim().split(/[:：]/)
    if (parts.length >= 2) {
      const [role, namesStr] = parts
      const names = namesStr.split(/[,，]/).map(name => name.trim()).filter(name => name)
      if (names.length > 0) {
        workers[role.trim()] = names
      }
    }
  })
  
  newTaskForm.value.workers = workers
}

// 新增：移除物料
const removeMaterial = (material) => {
  delete newTaskForm.value.material_requirements[material]
  // 重新构建输入框内容
  const materials = Object.entries(newTaskForm.value.material_requirements)
    .map(([name, req]) => `${name}:${req.quantity}:${req.unit}`)
    .join(',')
  materialInput.value = materials
}

// 新增：移除工具
const removeTool = (tool) => {
  delete newTaskForm.value.tools_requirements[tool]
  // 重新构建输入框内容
  const tools = Object.entries(newTaskForm.value.tools_requirements)
    .map(([name, req]) => `${name}:${req.quantity}:${req.unit}`)
    .join(',')
  toolsInput.value = tools
}

// 新增：移除工种
const removeWorkerRole = (role) => {
  delete newTaskForm.value.workers[role]
  // 重新构建输入框内容
  const roles = Object.entries(newTaskForm.value.workers)
    .map(([role, names]) => `${role}:${names.join(',')}`)
    .join('；')
  workersInput.value = roles
}

// 新增：提交新建任务
const submitNewTask = async () => {
  if (!taskFormRef.value) return
  
  try {
    // 验证表单
    await taskFormRef.value.validate()
    
    createTaskLoading.value = true
    
    // 发送POST请求
    const response = await axios.post(`${API}/work-order-tasks`, newTaskForm.value)

    if (response.data) {
      ElMessage.success('工单任务创建成功')
      createTaskDialogVisible.value = false
      
      // 刷新任务列表
      await refreshAllWorkOrderTasks()
      
      // 重置表单
      resetTaskForm()
    } else {
      ElMessage.error('创建工单任务失败')
    }
  } catch (error) {
    console.error('创建工单任务失败:', error)
    if (error.response?.data?.message) {
      ElMessage.error(`创建失败: ${error.response.data.message}`)
    } else {
      ElMessage.error('创建工单任务失败，请重试')
    }
  } finally {
    createTaskLoading.value = false
  }
}

// 新增：按计划开始时间排序（升序）
const sortedTasks = computed(() => {
  return [...filteredTasksByWorkOrder.value].sort((a, b) => {
    // 简单的字符串排序，假设时间格式一致 "第X天 HH:MM"
    const timeA = a.scheduled_start_time || ''
    const timeB = b.scheduled_start_time || ''
    return timeA.localeCompare(timeB)
  })
})

// 组件挂载时获取工单数据
onMounted(() => {
  refreshWorkOrders()
  // 预加载任务数据
  refreshAllWorkOrderTasks()
})
</script>

<style scoped>
.task-management-container {
  padding: 24px;
  min-height: 100%;
  box-sizing: border-box;
}

.panel-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 24px 0 rgba(0, 0, 0, 0.04);
  background: #ffffff;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background-color: #ffffff;
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
}

.filter-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  width: 280px;
}
.search-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.status-select,
.priority-select {
  width: 140px;
}
.status-select :deep(.el-input__wrapper),
.priority-select :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.filter-toolbar .el-button {
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 500;
}

/* 表格样式优化 */
.task-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f0f2f5;
}

/* 移除 Element Plus 默认的内外边框，使用底层线 */
.task-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}
.task-table :deep(.el-table__border-left-patch) {
  display: none;
}
.task-table :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

.task-table :deep(td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

.task-table :deep(.el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

.order-number {
  font-weight: 600;
  color: #3b82f6;
  font-size: 14px;
  font-family: monospace;
}

.title-text {
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
}

.equipment-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #475569;
}

.equipment-info .el-icon {
  color: #64748b;
  font-size: 14px;
}

/* 状态和优先级标签优化 */
.status-tag,
.priority-tag {
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
}

.status-tag {
  min-width: 60px;
}

/* 操作按钮优化 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-buttons .el-button {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
  border: none;
  background-color: transparent;
}

.action-buttons .el-button--primary {
  color: #3b82f6;
}
.action-buttons .el-button--primary:hover {
  background-color: #eff6ff;
}

.action-buttons .el-button--success {
  color: #10b981;
}
.action-buttons .el-button--success:hover {
  background-color: #ecfdf5;
}

.action-buttons .el-button--info {
  color: #64748b;
}
.action-buttons .el-button--info:hover {
  background-color: #f8fafc;
}

.action-buttons .el-button .el-icon {
  margin-right: 4px;
  font-size: 14px;
}

/* 表格底部 */
.table-footer {
  margin-top: 24px;
  display: flex;
  justify-content: space-between; /* 改为两端对齐，按钮在左，统计在右 */
  align-items: center;
  gap: 16px;
  flex-wrap: wrap; /* 移动端自适应换行 */
  padding-top: 16px;
  border-top: 1px solid #f0f2f5;
}

.create-btn-wrapper {
  flex-shrink: 0; /* 防止按钮被压缩 */
}

.stats-info {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}


.stats-info .el-tag {
  font-size: 13px;
  padding: 6px 16px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
}

/* 对话框样式优化 */
:deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

:deep(.el-dialog__header) {
  padding: 20px 24px;
  margin-right: 0;
  border-bottom: 1px solid #f0f2f5;
  background-color: #fafafa;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  font-size: 16px;
  color: #1e293b;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #f0f2f5;
  background-color: #fafafa;
}

.detail-form {
  padding: 0;
}

.detail-form .el-form-item {
  margin-bottom: 20px;
}

.detail-form .el-form-item__label {
  font-weight: 500;
  color: #475569;
}

/* 新增样式 */
.no-data-tip {
  padding: 60px 0;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-count {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

/* 工单任务详情弹窗样式 */
.task-dialog-header {
  margin-bottom: 20px;
}

.task-dialog-header .el-button {
  border-radius: 8px;
  font-weight: 500;
}

/* 新建工单任务表单样式 */
.task-form {
  padding: 0;
}

.task-form .el-form-item {
  margin-bottom: 24px;
}

.task-form .el-form-item__label {
  font-weight: 500;
  color: #606266;
}

.requirements-preview {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.requirements-preview .el-tag {
  margin-bottom: 4px;
}

.el-divider {
  margin: 24px 0 16px 0;
  font-weight: 500;
  color: #606266;
}
.hours-summary-container {
  background-color: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.hours-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.hours-row:last-child {
  border-bottom: none;
}

.hours-label {
  font-size: 13px;
  color: #606266;
  min-width: 120px; /* 固定标签最小宽度，防止换行 */
  flex-shrink: 0; /* 防止标签被压缩 */
  padding-right: 12px;
}

.hours-value {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  text-align: right;
  flex-grow: 1;
  font-family: 'Courier New', monospace; /* 等宽字体更好看 */
}

/* 价格统计容器 */
.price-summary-container {
  background-color: #f0f9ff;
  border: 1px solid #b3e0ff;
  border-radius: 4px;
  padding: 12px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.price-label {
  font-size: 13px;
  color: #606266;
  min-width: 120px;
  flex-shrink: 0;
  padding-right: 12px;
}

.price-value {
  font-size: 16px;
  font-weight: 600;
  color: #f56c6c;
  text-align: right;
  flex-grow: 1;
}

/* 调整表单整体布局 */
.task-management-container .el-form-item {
  margin-bottom: 18px;
}

.task-management-container .el-form-item__label {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
  padding-right: 12px;
  white-space: nowrap; /* 防止标签换行 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .filter-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input,
  .status-select,
  .priority-select {
    width: 100%;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .task-form .el-col {
    margin-bottom: 12px;
  }

/* 新增样式：让新建工单按钮靠左 */
.table-footer .el-button {
  margin-right: auto;
}
}
</style>
