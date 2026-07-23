<template>
  <div class="home-container">
    <!-- 主体三栏布局 -->
    <div class="layout">
      <!-- 右侧：算法与明细 -->
      <div class="right">
        <el-card class="panel-card" shadow="hover">
          <div style="display: flex;">
            <div class="section-title">
    <img src="/src/assets/iconfont/算法选择.png" alt="工单选择" class="panel-icon mr6" /> 
    检修计划选择
  </div>
          <div class="section-title"><img src="/src/assets/iconfont/算法选择.png" alt="算法选择" class="panel-icon mr6" />目标选择 </div>
          <div class="section-title" ><img src="/src/assets/iconfont/算法选择.png" alt="算法选择" class="panel-icon mr6" />模型选择 </div>
          </div>
         

          <div class="algorithm-target-selection">
            <!-- 按工单模式：选择工单 -->
            <el-select
    v-model="selectedPlanId"
    placeholder="请选择检修计划"
    class="selection-item"
    :loading="loadingPlans"
    clearable
    @change="onPlanChange"
    style="width: 100%;"
  >
    <el-option
      v-for="plan in maintenancePlans"
      :key="plan.id"
      :label="`${plan.plan_name} (工单数: ${plan.work_order_count || 0}个) - ${plan.plan_scale || '规模未知'} - ${plan.status}`"
      :value="plan.id"
    />
  </el-select>
            <el-select v-model="selectedTarget" placeholder="请选择目标" class="selection-item">
              <el-option label="最小化工期" value="minimize_duration" />
              <el-option label="最小化成本" value="minimize_cost" />
              <el-option label="最大化资源利用率" value="maximize_resource_utilization" />
            </el-select>
            <el-select v-model="selectedAlgorithm" placeholder="请选择算法" class="selection-item">
              <el-option v-for="opt in algorithmOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </div>
          <div class="button-group mt8">
            <el-button type="primary" class="schedule-btn" :loading="loadingSchedule"
              @click="runScheduleByPlan">生成调度</el-button>

            <el-button type="success" @click="savePlan" :loading="saving" class="save-btn">保存方案</el-button>
            <!-- 方案历史按钮：已选计划时显示 -->
            <el-button
              v-if="selectedPlanId"
              type="info"
              @click="openPlanHistory"
              :loading="loadingPlanHistory"
              class="plan-history-btn"
            >方案历史</el-button>
           <el-button
    v-if="showGanttView"
    type="warning"
    @click="generateWorkOrders"
    :loading="generatingWorkOrders"
    class="generate-workorder-btn"
  >
    发布工单
  </el-button>
          </div>
        </el-card>

        <el-card class="panel-card mt12" shadow="hover">
          <div class="section-title">任务分配明细</div>


          <div class="filter-worker">
            <el-input 
              v-model="workerNameFilter" 
              placeholder="输入工人姓名查看" 
              style="width: 200px; margin-right: 10px;"
              clearable
              @keyup.enter="showWorkerSchedule"
            />
            <el-button type="primary" @click="showWorkerSchedule">查看任务表</el-button>
            
          </div>
          <div class="filter-bar" style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
  <span style="color: #606266; font-weight: 500;">筛选设备：</span>
  <el-select 
    v-model="selectedDeviceFilter" 
    placeholder="请选择设备" 
    clearable 
    style="width: 300px;" 
    @change="handleDeviceFilterChange"
  >
    <!-- 这里的选项是从当前任务数据中提取的 -->
    <el-option 
    v-for="device in [...new Set(assignmentRows?.map(row => row.device) || [])].sort()" 
      :key="device" 
      :label="device" 
      :value="device" 
    />
  </el-select>
  <!-- 提示当前筛选状态 -->
  <span v-if="selectedDeviceFilter" style="color: #409EFF; font-size: 14px;">
    正在查看 "{{ selectedDeviceFilter }}" 的任务
  </span>
</div>
          <el-table 
  :data="paginatedAssignmentRows" 
  style="width: 100%; margin-top: 16px" 
  border 
  stripe
  :row-style="getRowStyle"
>
            <el-table-column prop="task" label="工序" min-width="150"></el-table-column>
            <el-table-column prop="device" label="设备" min-width="120"></el-table-column>
            <el-table-column prop="workersText" label="工人" min-width="200"></el-table-column>
            <el-table-column prop="startTimeFormatted" label="开始时间" min-width="140"></el-table-column>
            <el-table-column prop="endTimeFormatted" label="结束时间" min-width="140"></el-table-column>
            <el-table-column label="操作" min-width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openEditWorkers(row)">更换工人</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-container" style="margin-top: 20px; display: flex; justify-content: flex-end;">
  <el-pagination
    @current-change="handleCurrentChange"
    :current-page="currentPage"
    :page-size="pageSize"
    :total="filteredAssignmentData.length"
    layout="total, prev, pager, next, jumper"
    background
  />
</div>
          <div class="gantt-container">
            <GanttView v-if="showGanttView" class="gantt-view" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 工人课表弹窗 -->
    <el-dialog
      v-model="showScheduleTable"
      :title="`${workerNameFilter} 的任务课表`"
      width="90%"
      height="80%"
      :fullscreen="false"
    >
      <div class="schedule-table-container">
        <!-- 添加分页控件 -->
        <div class="pagination-controls" style="margin-bottom: 16px; display: flex; justify-content: center; align-items: center;">
          <el-button @click="prevWeek" :disabled="currentWeek <= 1">上一周</el-button>
          <span style="margin: 0 16px;">第 {{ currentWeek }} 周 / 共 {{ totalWeeks }} 周</span>
          <el-button @click="nextWeek" :disabled="currentWeek >= totalWeeks">下一周</el-button>
          <div style="margin-left: 20px;">
            <el-select 
              v-model="selectedScheduleEquipment" 
              placeholder="选择设备" 
              clearable 
              style="width: 200px; margin-right: 10px;"
              @change="currentWeek = 1"
            >
              <el-option
                v-for="option in scheduleEquipmentOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-button 
              v-for="week in totalWeeks" 
              :key="week"
              @click="goToWeek(week)"
              :type="week === currentWeek ? 'primary' : 'default'"
              style="margin: 0 4px;"
              size="small"
            >
              第{{ week }}周
            </el-button>
          </div>
        </div>
        
        <div class="schedule-table-wrapper">
          <!-- 表头：天数 -->
          <div class="time-column-header">时间</div>
          <div 
            v-for="day in 7" 
            :key="day" 
            class="day-column-header"
          >
            第{{ day }}天
          </div>
          
          <!-- 左侧时间列 -->
          <div class="time-column">
            <div 
              v-for="(time, index) in timeSlots" 
              :key="index" 
              class="time-slot"
            >
              {{ time }}
            </div>
          </div>
          
          <!-- 每天的任务内容 -->
          <div 
            v-for="day in 7" 
            :key="day" 
            class="day-column"
          >
            <!-- 时间槽背景 -->
            <div 
              v-for="(time, index) in timeSlots" 
              :key="index" 
              class="time-slot-bg"
            ></div>
            
            <!-- 任务项 -->
            <div 
              v-for="task in weeklyScheduleTableData[day]" 
              :key="task.processId"
              class="task-item"
              :style="[getTaskPositionStyle(task), { margin: 0, padding: 0 }]"
              :title="`${task.task} (${task.startTimeFormatted} - ${getDisplayEndTime(task.endTimeFormatted)})`"
            >
              <div class="task-content">
                <div class="task-name">{{ task.task }}</div>
                <div class="task-device">{{ task.device }}</div>
                <div class="task-time">{{ task.startTimeFormatted.split(' ')[1] }}-{{ getDisplayEndTime(task.endTimeFormatted).split(' ')[1] }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeScheduleTable">关闭</el-button>
        </span>
      </template>
    </el-dialog>
    <!-- 方案历史对话框（仅按检修计划模式使用） -->
    <el-dialog
      v-model="planHistoryDialogVisible"
      title="方案历史"
      width="80%"
      :close-on-click-modal="false"
    >
      <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
        <el-button
          type="primary"
          :disabled="selectedComparePlans.length !== 2"
          @click="openCompareDialog"
        >
          对比选中方案{{ selectedComparePlans.length === 2 ? `（已选 ${selectedComparePlans.length} 个）` : `（需选 2 个，当前 ${selectedComparePlans.length}）` }}
        </el-button>
        <span style="color: #909399; font-size: 13px;">提示：在下方勾选两个方案后点击对比</span>
      </div>
      <el-table
        ref="planHistoryTableRef"
        :data="planHistoryList"
        v-loading="loadingPlanHistory"
        border
        stripe
        style="width: 100%"
        :row-class-name="planHistoryRowClassName"
        @selection-change="onPlanHistorySelectionChange"
      >
        <el-table-column type="selection" width="50" :selectable="canSelectPlan" />
        <el-table-column prop="schedule_name" label="方案名" min-width="180">
          <template #default="{ row }">
            <span>{{ row.schedule_name }}</span>
            <el-tag
              v-if="currentActiveSchedulePlanId && row.id === currentActiveSchedulePlanId"
              type="success"
              size="small"
              style="margin-left: 8px;"
            >当前生效</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="algorithm" label="算法" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="planStatusTagType(row.status)">
              {{ row.status || '—' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_tasks" label="任务数" min-width="80" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewPlanSchedule(row)">查看</el-button>
            <el-button
              v-if="row.status !== '生效中'"
              type="success"
              link
              @click="activatePlan(row)"
            >设为生效</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="planHistoryDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <!-- 方案对比对话框 -->
    <el-dialog
      v-model="compareDialogVisible"
      title="调度方案对比"
      width="95%"
      top="3vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-loading="loadingCompare">
        <!-- 顶部：两个方案元信息并排卡片 -->
        <el-row :gutter="24" v-if="compareData" class="comparison-container">
          <!-- ================= 方案 A ================= -->
          <el-col :span="12">
            <el-card class="compare-card plan-a-card" shadow="never">
              <template #header>
                <div class="compare-card-header">
                  <h3 class="compare-card-title">方案 A：{{ compareData.plan1.schedule_name }}</h3>
                  <el-button
                    v-if="compareData.plan1.status !== '生效中'"
                    type="primary"
                    size="small"
                    @click="activatePlanFromCompare(compareData.plan1)"
                  >
                    设为生效
                  </el-button>
                  <el-tag v-else type="success" size="small" effect="dark">当前生效</el-tag>
                </div>
              </template>

              <!-- 核心指标区 -->
              <div class="core-metrics">
                <!-- 预估成本 (实时计算) -->
                <div class="metric-item">
                  <div class="metric-label">💰 预估成本</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(costPlan1, costPlan2, true)]">
                        ¥ {{ formatNumber(costPlan1) }}
                      </span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(costPlan1, costPlan2, true)]">
                      {{ getCostDiffText(costPlan1, costPlan2) }}
                    </span>
                  </div>
                </div>

                <!-- 工人数 -->
                <div class="metric-item">
                  <div class="metric-label">👷 工人数</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(compareData.overview1.worker_count, compareData.overview2.worker_count, true)]">
                        {{ compareData.overview1.worker_count }}
                      </span>
                      <span class="metric-unit">人</span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(compareData.overview1.worker_count, compareData.overview2.worker_count, true)]">
                      {{ getWorkerDiffText(compareData.overview1.worker_count, compareData.overview2.worker_count) }}
                    </span>
                  </div>
                </div>

                <!-- 总工期 -->
                <div class="metric-item">
                  <div class="metric-label">📅 总工期</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(compareData.overview1.total_duration_days, compareData.overview2.total_duration_days, true)]">
                        {{ compareData.overview1.total_duration_days }}
                      </span>
                      <span class="metric-unit">天</span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(compareData.overview1.total_duration_days, compareData.overview2.total_duration_days, true)]">
                      {{ getDurationDiffText(compareData.overview1.total_duration_days, compareData.overview2.total_duration_days) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 次要信息区 -->
              <div class="secondary-info">
                <div class="info-row">
                  <span class="info-label">起止时间</span>
                  <span>{{ compareData.overview1.start_time_formatted || '—' }} ~ {{ compareData.overview1.end_time_formatted || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">创建时间</span>
                  <span>{{ compareData.plan1.created_at || '—' }}</span>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- ================= 方案 B ================= -->
          <el-col :span="12">
            <el-card class="compare-card plan-b-card" shadow="never">
              <template #header>
                <div class="compare-card-header">
                  <h3 class="compare-card-title">方案 B：{{ compareData.plan2.schedule_name }}</h3>
                  <el-button
                    v-if="compareData.plan2.status !== '生效中'"
                    type="primary"
                    size="small"
                    @click="activatePlanFromCompare(compareData.plan2)"
                  >
                    设为生效
                  </el-button>
                  <el-tag v-else type="success" size="small" effect="dark">当前生效</el-tag>
                </div>
              </template>

              <!-- 核心指标区 -->
              <div class="core-metrics">
                <!-- 预估成本 (实时计算) -->
                <div class="metric-item">
                  <div class="metric-label">💰 预估成本</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(costPlan2, costPlan1, true)]">
                        ¥ {{ formatNumber(costPlan2) }}
                      </span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(costPlan2, costPlan1, true)]">
                      {{ getCostDiffText(costPlan2, costPlan1) }}
                    </span>
                  </div>
                </div>

                <!-- 工人数 -->
                <div class="metric-item">
                  <div class="metric-label">👷 工人数</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(compareData.overview2.worker_count, compareData.overview1.worker_count, true)]">
                        {{ compareData.overview2.worker_count }}
                      </span>
                      <span class="metric-unit">人</span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(compareData.overview2.worker_count, compareData.overview1.worker_count, true)]">
                      {{ getWorkerDiffText(compareData.overview2.worker_count, compareData.overview1.worker_count) }}
                    </span>
                  </div>
                </div>

                <!-- 总工期 -->
                <div class="metric-item">
                  <div class="metric-label">📅 总工期</div>
                  <div class="metric-value-wrapper">
                    <div class="metric-main">
                      <span :class="['metric-value', getMetricColor(compareData.overview2.total_duration_days, compareData.overview1.total_duration_days, true)]">
                        {{ compareData.overview2.total_duration_days }}
                      </span>
                      <span class="metric-unit">天</span>
                    </div>
                    <span :class="['diff-tag', getDiffTagClass(compareData.overview2.total_duration_days, compareData.overview1.total_duration_days, true)]">
                      {{ getDurationDiffText(compareData.overview2.total_duration_days, compareData.overview1.total_duration_days) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 次要信息区 -->
              <div class="secondary-info">
                <div class="info-row">
                  <span class="info-label">起止时间</span>
                  <span>{{ compareData.overview2.start_time_formatted || '—' }} ~ {{ compareData.overview2.end_time_formatted || '—' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">创建时间</span>
                  <span>{{ compareData.plan2.created_at || '—' }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <!-- 合并差异筛选与任务明细对比 -->
        <el-card v-if="compareData" class="mt12 diff-panel" shadow="never">
          <!-- 头部：将筛选器移入表格卡片的 Header -->
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div class="section-title" style="margin-bottom: 0;">任务明细对比</div>
              
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="color: #606266; font-size: 14px;">差异筛选：</span>
                <el-radio-group v-model="diffFilter" size="small">
                  <el-radio-button value="all">全部 ({{ compareData.task_diff.summary.total }})</el-radio-button>
                  <el-radio-button value="changed">差异 ({{ compareData.task_diff.summary.added + compareData.task_diff.summary.removed + compareData.task_diff.summary.changed }})</el-radio-button>
                  <el-radio-button value="added">新增 ({{ compareData.task_diff.summary.added }})</el-radio-button>
                  <el-radio-button value="removed">删除 ({{ compareData.task_diff.summary.removed }})</el-radio-button>
                  <el-radio-button value="unchanged">相同 ({{ compareData.task_diff.summary.unchanged }})</el-radio-button>
                </el-radio-group>
                
                <el-button type="warning" size="small" @click="exportCompareReport">导出对比报告</el-button>
              </div>
            </div>
          </template>

          <!-- 主体：原有表格保持不变 -->
          <!-- 主体：原有表格保持不变 -->
          <el-table
            :data="filteredDiffItems"
            border
            stripe
            style="width: 100%"
            :row-class-name="diffRowClassName"
            :max-height="500"
          >
            <el-table-column label="设备 / 工序" min-width="180" fixed>
              <template #default="{ row }">
                <div class="diff-eq-name">{{ row.task1?.equipment_name || row.task2?.equipment_name || '—' }}</div>
                <div class="diff-proc-name">{{ row.task1?.process_name || row.task2?.process_name || '—' }}</div>
              </template>
            </el-table-column>
            
            <el-table-column label="方案 A" align="center">
              <el-table-column label="开始时间" min-width="140">
                <template #default="{ row }">
                  <span>{{ row.task1?.start_time_formatted || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="结束时间" min-width="140">
                <template #default="{ row }">
                  <span>{{ row.task1?.end_time_formatted || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="工人" min-width="160">
                <template #default="{ row }">
                  <span>{{ formatWorkersText(row.task1?.workers) }}</span>
                </template>
              </el-table-column>
            </el-table-column>

            <el-table-column label="方案 B" align="center">
              <el-table-column label="开始时间" min-width="140">
                <template #default="{ row }">
                  <span>{{ row.task2?.start_time_formatted || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="结束时间" min-width="140">
                <template #default="{ row }">
                  <span>{{ row.task2?.end_time_formatted || '—' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="工人" min-width="160">
                <template #default="{ row }">
                  <span>{{ formatWorkersText(row.task2?.workers) }}</span>
                </template>
              </el-table-column>
            </el-table-column>

            <el-table-column label="差异类型" min-width="140" fixed="right">
              <template #default="{ row }">
                <el-tag :type="diffTagType(row.status)" size="small">
                  {{ diffStatusLabel(row.status) }}
                </el-tag>
                <div v-if="row.changes && row.changes.length" class="diff-changes-text">
                  {{ row.changes.join('、') }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 简化甘特图对比 -->
        <el-card v-if="compareData" class="mt12" shadow="never">
          <div class="section-title">时间轴对比（甘特图简化视图）</div>
          <GanttCompareView
            :plan1="compareData.plan1"
            :plan2="compareData.plan2"
            :overview1="compareData.overview1"
            :overview2="compareData.overview2"
          />
        </el-card>
      </div>
      <template #footer>
        <el-button @click="compareDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <el-dialog
      v-model="editWorkerDialogVisible"
      title="更换工人"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="currentEditingTask">
        <el-form label-width="100px">
          <el-form-item
            v-for="(workerList, trade) in editingWorkers"
            :key="trade"
            :label="trade"
          >
            <el-select
              v-model="editingWorkers[trade]"
              filterable
              :placeholder="getCurrentWorkerNamesForTrade(trade) || '请选择工人'"
              style="width: 100%"
            >
              <el-option
                v-for="worker in getAvailableWorkersByTrade(trade)"
                :key="worker.id"
                :label="`${worker.name} (技能等级: ${worker.skill_level})`"
                :value="worker.id"
                :disabled="isWorkerCurrentlySelected(worker.id, trade)"
                :class="{ 
                  'conflict-option': isWorkerConflicted(worker.id),
                  'current-worker-option': isWorkerCurrentlySelected(worker.id, trade)
                  }"
                :title="isWorkerConflicted(worker.id, trade) 
                  ? '该工人存在时间冲突' 
                  :  (isWorkerConflicted(worker.id) ?'该工人存在时间冲突':'')"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="worker-edit-footer">
          <span v-if="!hasWorkerChanges" class="no-change-tip">
             <el-icon><Warning /></el-icon> 工人未变更
          </span>
          <div class="footer-buttons">
            <el-button @click="editWorkerDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveWorkersEdit" :disabled="!hasWorkerChanges">保存</el-button>
          </div>
        </div>
        
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { computed, reactive, ref, onBeforeUnmount, watch, nextTick,onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import axios from 'axios'
import request from '@/utils/request'
import { getPlansForSchedule } from '@/api/scheduleApi' 
import GanttView from './GanttView.vue'
import GanttCompareView from './GanttCompareView.vue'
const selectedDeviceFilter = ref('')
const currentPage = ref(1)          // 当前页码
const pageSize = ref(10) 
const projectStartDatetime = ref(null)
// 新增：
const loadingPlans = ref(false) // 计划加载状态
const workerBusyMap = ref(new Map())
const workerPool = ref([]) // 工人池数据
const editWorkerDialogVisible = ref(false)
const currentEditingTask = ref(null)        // 当前正在编辑的任务行
const editingWorkers = ref({})


const saving = ref(false)

// ====== 按检修计划模式相关状态 ======
const scheduleMode = ref('plan')          // 调度模式：仅按检修计划
const maintenancePlans = ref([])                // 检修计划列表
const selectedPlanId = ref(null)                // 选中的检修计划ID
const currentSchedulePlanId = ref(null)         // 当前生成的调度方案ID
const currentScheduleName = ref('')             // 当前生成的调度方案名
const planHistoryDialogVisible = ref(false)     // 方案历史对话框
const planHistoryList = ref([])                 // 方案历史列表
const loadingPlanHistory = ref(false)           // 方案历史加载状态
const currentActiveSchedulePlanId = ref(null)   // 当前生效方案ID（用于历史列表标记）

// ====== 方案对比相关状态 ======
const planHistoryTableRef = ref(null)            // 方案历史表格引用
const selectedComparePlans = ref([])             // 选中的对比方案（最多2个）
const compareDialogVisible = ref(false)          // 对比对话框
const loadingCompare = ref(false)                // 对比数据加载状态
const compareData = ref(null)                    // 对比数据

// ====== 预估成本（使用后端计算的 estimated_cost） ======

// 计算方案 A 的总成本
const costPlan1 = computed(() => {
  if (!compareData.value?.overview1) return 0;
  return compareData.value.overview1.estimated_cost || 0;
});

// 计算方案 B 的总成本
const costPlan2 = computed(() => {
  if (!compareData.value?.overview2) return 0;
  return compareData.value.overview2.estimated_cost || 0;
});

// 数字千分位格式化
const formatNumber = (num) => {
  return Number(num).toLocaleString('en-US'); 
}

// 获取指标颜色类名
const getMetricColor = (currentValue, targetValue, isLowerBetter = true) => {
  if (currentValue == null || targetValue == null) return 'status-neutral';
  const cur = Number(currentValue);
  const tar = Number(targetValue);
  if (cur === tar) return 'status-neutral';
  
  const isLower = cur < tar;
  return isLowerBetter 
    ? (isLower ? 'status-good' : 'status-bad') 
    : (isLower ? 'status-bad' : 'status-good');
}

// 获取差异标签的背景类名
const getDiffTagClass = (currentValue, targetValue, isLowerBetter = true) => {
  if (currentValue == null || targetValue == null) return 'neutral';
  const cur = Number(currentValue);
  const tar = Number(targetValue);
  if (cur === tar) return 'neutral';
  
  const isLower = cur < tar;
  return isLowerBetter 
    ? (isLower ? 'good' : 'bad') 
    : (isLower ? 'bad' : 'good');
}

// 成本差异文案
const getCostDiffText = (current, target) => {
  if (current == null || target == null || current === target) return '- 平局';
  const diff = Math.abs(current - target);
  return current < target ? `↓ 省 ¥ ${formatNumber(diff)}` : `↑ 贵 ¥ ${formatNumber(diff)}`;
}

// 工人数差异文案
const getWorkerDiffText = (current, target) => {
  if (current == null || target == null || current === target) return '- 平局';
  const diff = Math.abs(current - target);
  return current < target ? `↓ 少 ${diff} 人` : `↑ 多 ${diff} 人`;
}

// 工期差异文案
const getDurationDiffText = (current, target) => {
  if (current == null || target == null || current === target) return '- 平局';
  const diff = Math.abs(current - target);
  return current < target ? `↓ 快 ${diff} 天` : `↑ 慢 ${diff} 天`;
}

const diffFilter = ref('changed')                // 差异筛选：all/changed/added/removed/unchanged

async function savePlan() {
  // 按检修计划模式：方案在生成调度时已自动保存为新方案，无需再保存
  ElMessage.info('方案已随生成调度时自动保存')
}
async function fetchPlans() {
  loadingPlans.value = true
  try {
    const result = await getPlansForSchedule()
    if (result.success && Array.isArray(result.data)) {
      // 过滤出可以调度的计划（如待调度的计划）
      maintenancePlans.value = result.data.filter(plan => 
        plan.work_order_count && plan.work_order_count > 0
      )
      ElMessage.success(`加载了 ${maintenancePlans.value.length} 个待调度的检修计划`)
    } else {
      maintenancePlans.value = []
    }
  } catch (error) {
    console.error('获取检修计划列表失败:', error)
    maintenancePlans.value = []
  } finally {
    loadingPlans.value = false
  }
}

// ====== 按检修计划模式相关方法 ======

// 获取检修计划列表
async function fetchMaintenancePlans() {
  loadingPlans.value = true
  try {
    const result = await request({
      url: '/api/maintenance-plans',
      method: 'get',
      params: { page: 1, page_size: 100 }
    })
    if (result.success && Array.isArray(result.data)) {
      maintenancePlans.value = result.data
    } else {
      maintenancePlans.value = []
      ElMessage.warning(result.message || '获取检修计划列表失败')
    }
  } catch (error) {
    console.error('获取检修计划列表失败:', error)
    ElMessage.error('获取检修计划列表失败，请检查网络连接')
    maintenancePlans.value = []
  } finally {
    loadingPlans.value = false
  }
}

// 检修计划选择变化处理
function onPlanChange(planId) {
  if (planId) {
    const plan = maintenancePlans.value.find(p => p.id === planId)
    if (plan) {
      ElMessage.success(`已选择检修计划: ${plan.plan_name}`)
    }
  }
  // 切换计划时清空当前方案信息
  currentSchedulePlanId.value = null
  currentScheduleName.value = ''
}

// 打开方案历史对话框
async function openPlanHistory() {
  if (!selectedPlanId.value) {
    ElMessage.warning('请先选择检修计划')
    return
  }
  planHistoryDialogVisible.value = true
  loadingPlanHistory.value = true
  try {
    const result = await request({
      url: `/api/maintenance-plans/${selectedPlanId.value}/schedule-plans`,
      method: 'get'
    })
    if (result.success && Array.isArray(result.data)) {
      planHistoryList.value = result.data
      currentActiveSchedulePlanId.value = result.current_schedule_plan_id || null
    } else {
      planHistoryList.value = []
      currentActiveSchedulePlanId.value = null
      ElMessage.warning(result.message || '获取方案历史失败')
    }
  } catch (error) {
    console.error('获取方案历史失败:', error)
    ElMessage.error('获取方案历史失败，请检查后端服务')
    planHistoryList.value = []
    currentActiveSchedulePlanId.value = null
  } finally {
    loadingPlanHistory.value = false
  }
}

// 方案历史行样式：高亮当前生效方案
function planHistoryRowClassName({ row }) {
  if (currentActiveSchedulePlanId.value && row.id === currentActiveSchedulePlanId.value) {
    return 'current-plan-row'
  }
  return ''
}

// 方案状态标签类型映射
function planStatusTagType(status) {
  if (status === '生效中') return 'success'
  if (status === '已归档') return 'info'
  if (status === '生成中') return 'warning'
  if (status === '失败') return 'danger'
  return 'info'
}

// 多选：限制最多选2个，且只有成功生成的方案可选
function canSelectPlan(row) {
  return row.status && row.status !== '失败' && row.status !== '生成中'
}

// 方案历史多选变化处理
function onPlanHistorySelectionChange(selection) {
  // 限制最多2个：若超过2个，保留最后选的2个
  if (selection.length > 2) {
    const trimmed = selection.slice(-2)
    // 清空再重新设置（nextTick 避免 el-table 内部状态不一致）
    nextTick(() => {
      planHistoryTableRef.value?.clearSelection()
      trimmed.forEach(row => planHistoryTableRef.value?.toggleRowSelection(row, true))
    })
    selectedComparePlans.value = trimmed
  } else {
    selectedComparePlans.value = selection
  }
}

// 打开方案对比对话框
async function openCompareDialog() {
  if (selectedComparePlans.value.length !== 2) {
    ElMessage.warning('请选择两个方案进行对比')
    return
  }
  const [p1, p2] = selectedComparePlans.value
  compareDialogVisible.value = true
  loadingCompare.value = true
  compareData.value = null
  diffFilter.value = 'changed'
  try {
    const result = await request({
      url: '/api/schedule-plans/compare',
      method: 'get',
      params: { id1: p1.id, id2: p2.id }
    })
    if (result.success && result.data) {
      compareData.value = result.data
    } else {
      ElMessage.error(result.message || '获取对比数据失败')
    }
  } catch (error) {
    console.error('获取对比数据失败:', error)
    ElMessage.error('获取对比数据失败，请检查后端服务')
  } finally {
    loadingCompare.value = false
  }
}

// 切换生效方案
async function activatePlan(row) {
  if (!row || !row.id) return
  try {
    await ElMessageBox.confirm(
      `确认将方案「${row.schedule_name}」设为生效方案？同检修计划下其他方案将被归档。`,
      '切换生效方案',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }
  try {
    const result = await request({
      url: `/api/schedule-plans/${row.id}/activate`,
      method: 'put'
    })
    if (result.success) {
      ElMessage.success(result.message || '方案已设为生效')
      // 刷新方案历史列表
      await openPlanHistory()
      // 若当前对比对话框打开，也刷新对比数据中的状态
      if (compareDialogVisible.value && compareData.value) {
        if (compareData.value.plan1.id === row.id) compareData.value.plan1.status = '生效中'
        if (compareData.value.plan2.id === row.id) compareData.value.plan2.status = '生效中'
        // 另一个方案若同计划则改为已归档
        const otherPlan = compareData.value.plan1.id === row.id ? compareData.value.plan2 : compareData.value.plan1
        if (otherPlan.plan_id === row.plan_id) otherPlan.status = '已归档'
      }
    } else {
      ElMessage.error(result.message || '切换生效失败')
    }
  } catch (error) {
    console.error('切换生效失败:', error)
    ElMessage.error('切换生效失败，请检查后端服务')
  }
}

// 从对比对话框中触发切换生效
function activatePlanFromCompare(plan) {
  activatePlan({ id: plan.id, schedule_name: plan.schedule_name, plan_id: plan.plan_id })
}

// 差异筛选：根据 diffFilter 过滤对比项
const filteredDiffItems = computed(() => {
  if (!compareData.value) return []
  const items = compareData.value.task_diff.items || []
  if (diffFilter.value === 'all') return items
  if (diffFilter.value === 'changed') {
    return items.filter(i => i.status === 'added' || i.status === 'removed' || i.status === 'changed')
  }
  return items.filter(i => i.status === diffFilter.value)
})

// 差异行样式
function diffRowClassName({ row }) {
  if (row.status === 'added') return 'diff-row-added'
  if (row.status === 'removed') return 'diff-row-removed'
  if (row.status === 'changed') return 'diff-row-changed'
  return 'diff-row-unchanged'
}

// 差异标签类型
function diffTagType(status) {
  if (status === 'added') return 'success'
  if (status === 'removed') return 'danger'
  if (status === 'changed') return 'warning'
  return 'info'
}

// 差异状态中文标签
function diffStatusLabel(status) {
  const map = { added: '方案B新增', removed: '方案B删除', changed: '有差异', unchanged: '相同' }
  return map[status] || status
}

// 格式化工人显示文本
function formatWorkersText(workers) {
  if (!workers || typeof workers !== 'object') return '—'
  const parts = Object.entries(workers).map(([type, names]) => {
    const list = Array.isArray(names) ? names : []
    return `${type}: ${list.length > 0 ? list.join('、') : '待分配'}`
  })
  return parts.length > 0 ? parts.join('；') : '未分配'
}

// 导出对比报告为 Excel
function exportCompareReport() {
  if (!compareData.value) {
    ElMessage.warning('暂无对比数据')
    return
  }
  try {
    const { plan1, plan2, overview1, overview2, task_diff } = compareData.value
    const wb = XLSX.utils.book_new()

    // Sheet1: 概览对比
    const overviewData = [
      ['指标', '方案 A', '方案 B', '差异'],
      ['方案名', plan1.schedule_name || '', plan2.schedule_name || '', ''],
      ['算法', plan1.algorithm || '', plan2.algorithm || '', ''],
      ['状态', plan1.status || '', plan2.status || '', ''],
      ['创建时间', plan1.created_at || '', plan2.created_at || '', ''],
      ['任务数', overview1.total_tasks, overview2.total_tasks, overview2.total_tasks - overview1.total_tasks],
      ['总工期(天)', overview1.total_duration_days, overview2.total_duration_days, (overview2.total_duration_days - overview1.total_duration_days).toFixed(2)],
      ['开始时间', overview1.start_time_formatted || '', overview2.start_time_formatted || '', ''],
      ['结束时间', overview1.end_time_formatted || '', overview2.end_time_formatted || '', ''],
      ['工人数', overview1.worker_count, overview2.worker_count, overview2.worker_count - overview1.worker_count],
      ['', '', '', ''],
      ['差异统计', '数量', '', ''],
      ['方案B新增任务', task_diff.summary.added, '', ''],
      ['方案B删除任务', task_diff.summary.removed, '', ''],
      ['有差异的任务', task_diff.summary.changed, '', ''],
      ['完全相同', task_diff.summary.unchanged, '', ''],
    ]
    const ws1 = XLSX.utils.aoa_to_sheet(overviewData)
    ws1['!cols'] = [{ wch: 20 }, { wch: 30 }, { wch: 30 }, { wch: 15 }]
    XLSX.utils.book_append_sheet(wb, ws1, '概览对比')

    // Sheet2: 任务级差异明细
    const taskData = [['设备', '工序', '方案A开始', '方案A结束', '方案A工人', '方案B开始', '方案B结束', '方案B工人', '差异类型', '差异说明']]
    task_diff.items.forEach(item => {
      taskData.push([
        item.task1?.equipment_name || item.task2?.equipment_name || '',
        item.task1?.process_name || item.task2?.process_name || '',
        item.task1?.start_time_formatted || '',
        item.task1?.end_time_formatted || '',
        formatWorkersText(item.task1?.workers),
        item.task2?.start_time_formatted || '',
        item.task2?.end_time_formatted || '',
        formatWorkersText(item.task2?.workers),
        diffStatusLabel(item.status),
        (item.changes || []).join('、')
      ])
    })
    const ws2 = XLSX.utils.aoa_to_sheet(taskData)
    ws2['!cols'] = [{ wch: 18 }, { wch: 18 }, { wch: 20 }, { wch: 20 }, { wch: 25 }, { wch: 20 }, { wch: 20 }, { wch: 25 }, { wch: 12 }, { wch: 20 }]
    XLSX.utils.book_append_sheet(wb, ws2, '任务级差异')

    const fileName = `方案对比_${plan1.schedule_name}_vs_${plan2.schedule_name}_${new Date().toISOString().slice(0, 10)}.xlsx`
    XLSX.writeFile(wb, fileName)
    ElMessage.success('对比报告已导出')
  } catch (error) {
    console.error('导出对比报告失败:', error)
    ElMessage.error('导出对比报告失败')
  }
}

// 查看指定调度方案详情（支持历史方案），加载到主表格
async function viewPlanSchedule(row) {
  if (!row || !row.id) {
    ElMessage.warning('方案信息缺失')
    return
  }
  try {
    const result = await request({
      url: `/api/schedule-plans/${row.id}`,
      method: 'get'
    })
    if (result.success && result.data) {
      const data = result.data
      const tasks = data.schedule_tasks || []
      // 填充主表格
      assignmentRows.value = mapSchedulePlanToRows(tasks)
      // 记录当前方案信息
      currentSchedulePlanId.value = data.id || null
      if (row && row.schedule_name) {
        currentScheduleName.value = row.schedule_name
      }
      // 保存到 localStorage
      localStorage.setItem('schedule_plan', JSON.stringify(tasks))
      // 设置项目开始时间（用于甘特图渲染）
      if (data.project_start_datetime) {
        projectStartDatetime.value = data.project_start_datetime
      }
      // 重建甘特图
      buildScheduleRows(tasks, projectStartDatetime.value)
      useRealSchedule.value = true
      showGanttView.value = false
      await nextTick()
      showGanttView.value = true
      buildWorkerBusyMap(tasks)
      // 重新获取工人池数据
      await fetchWorkerPool()
      ElMessage.success(`已加载方案：${row?.schedule_name || data.schedule_plan_id || ''}`)
      await fetchWorkerPool()
      // 关闭对话框
      planHistoryDialogVisible.value = false
    } else {
      ElMessage.warning(result.message || '该检修计划暂无生效方案')
    }
  } catch (error) {
    console.error('加载方案详情失败:', error)
    ElMessage.error('加载方案详情失败，请检查后端服务')
  }
}

// 公共辅助：将后端 schedule_plan 数组映射为前端 assignmentRows 结构
function mapSchedulePlanToRows(schedulePlan) {
  return (schedulePlan || []).map(task => {
    const safeWorkers = task.workers && typeof task.workers === 'object' ? task.workers : {}
    const workersArray = Object.entries(safeWorkers).map(([type, workers]) => {
      const workersList = Array.isArray(workers) ? workers : []
      const names = workersList.length > 0 ? workersList.join('、') : '待分配'
      return `${type}: ${names}`
    })
    return {
      task: task.process_name,
      device: `${task.equipment_name}`,
      processId: task.process_id,
      equipmentId: task.equipment_id,
      workers: safeWorkers,
      workersText: Array.isArray(workersArray) && workersArray.length > 0 ? workersArray.join('；') : '未分配',
      startTimeFormatted: task.start_time_formatted,
      endTimeFormatted: task.end_time_formatted,
      durationHours: task.duration_hours,
      startDay: task.start_time,
      endDay: task.end_time
    }
  })
}

// 按检修计划模式生成调度（生成即保存为新方案，一步完成）
async function runScheduleByPlan() {
  if (!selectedPlanId.value) {
    ElMessage.warning('请先选择检修计划')
    return
  }
  const result = await request({
    url: `/api/maintenance-plans/${selectedPlanId.value}/run-scheduler`,
    method: 'post',
    data: {
      algorithm: selectedAlgorithm.value
    }
  })
  if (result.success) {
    // 记录当前生成的方案信息
    currentSchedulePlanId.value = result.schedule_plan_id || null
    currentScheduleName.value = result.schedule_name || ''
    // 填充调度结果到主表格
    assignmentRows.value = mapSchedulePlanToRows(result.schedule_plan)
    // 处理工人池
    const workerPoolData = result.worker_pool || {}
    const flatWorkers = []
    for (const [trade, workers] of Object.entries(workerPoolData)) {
      workers.forEach(worker => {
        flatWorkers.push({ ...worker, type: trade })
      })
    }
    workerPool.value = flatWorkers
    // 保存到 localStorage
    localStorage.setItem('schedule_plan', JSON.stringify(result.schedule_plan || []))
    // 构建甘特图数据
    buildScheduleRows(result.schedule_plan || [], projectStartDatetime.value)
    useRealSchedule.value = true
    showGanttView.value = false
    await nextTick()
    showGanttView.value = true
    buildWorkerBusyMap(result.schedule_plan || [])
    // 处理统计信息
    if (result.statistics) {
      statisticsData.value = result.statistics
    }
    ElMessage.success(`调度方案已生成并保存：${result.schedule_name || ''}`)
  } else {
    // 失败处理：区分工人不足与其他错误
    if (result.error_type === 'insufficient_workers') {
      ElMessage.error('工人不足，无法生成调度方案')
    } else {
      ElMessage.error(result.message || '调度执行失败')
    }
  }
}

const filteredAssignmentData = computed(() => {
  let data = assignmentRows.value || []

  // 第一步：根据工人姓名过滤（原有的逻辑）
  if (workerNameFilter.value) {
    const workerName = workerNameFilter.value.trim()
    data = data.filter(row => {
      const workerGroups = row.workersText?.split('；') || []
      return workerGroups.some(group => {
        const parts = group.split(': ')
        if (parts.length > 1) {
          const workersStr = parts[1]
          return workersStr.includes(workerName)
        }
        return false
      })
    })
  }
  if (selectedDeviceFilter.value) {
    data = data.filter(row => row.device === selectedDeviceFilter.value)
  }

  // 排序逻辑保持不变
  return data.sort((a, b) => {
    const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)?.[1] || 0)
    const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)?.[1] || 0)
    if (dayA !== dayB) return dayA - dayB
    return a.startTimeFormatted.localeCompare(b.startTimeFormatted)
  })
})

// 2. 计算当前页显示的数据 (用于表格绑定)
const paginatedAssignmentRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAssignmentData.value.slice(start, end)
})

// 3. 计算总页数
const totalPageCount = computed(() => {
  return Math.ceil(filteredAssignmentData.value.length / pageSize.value) || 1
})
function handleCurrentChange(page) {
  currentPage.value = page
}

// 设备筛选改变时，重置为第一页
function handleDeviceFilterChange() {
  currentPage.value = 1 // 筛选后回到第一页
}
function getAvailableWorkersByTrade(trade) {
  if (!workerPool.value) return [];
  return workerPool.value
    .filter(w => w.type === trade)
    .sort((a, b) => {
      // 将 skill_level 转为数字进行比较，数字越大等级越高，降序排列
      const levelA = Number(a.skill_level) || 0;
      const levelB = Number(b.skill_level) || 0;
      return levelB - levelA;
    });
}
function getRowStyle({ row }) {
  // 兼容多种可能的"待分配"文本格式
  const workersText = row.workersText || '';
  if (workersText.includes('待分配') || workersText.includes('未分配')) {
    return {
      backgroundColor: '#fef0f0',
      color: '#f56c6c'
    };
  }
  return {};
}
function openEditWorkers(row) {
  currentEditingTask.value = row;
  
  const workersObj = row.workers || {};
  const initialEdit = {};
  
  for (const [trade, names] of Object.entries(workersObj)) {
    const ids = [];
    // 防御性处理：确保 names 是数组
    const nameArray = Array.isArray(names) ? names : [names];
    
    for (const name of nameArray) {
      const worker = workerPool.value.find(w => w.type === trade && w.name === name);
      if (worker) {
        ids.push(worker.id);
      } else {
        console.warn(`工人 ${name} (${trade}) 不在工人池中`);
      }
    }
    // 关键：始终将工种对应的值设置为数组
    initialEdit[trade] = ids;
  }
  editingWorkers.value = initialEdit;
  editWorkerDialogVisible.value = true;
}

function getCurrentWorkerNamesForTrade(trade) {
  if (!currentEditingTask.value) return '';
  const workers = currentEditingTask.value.workers || {};
  const names = workers[trade];
  if (!names) return '';
  const nameArray = Array.isArray(names) ? names : [names];
  return nameArray.join('、');
}

// 检测当前编辑的工人是否与原任务有变化
const hasWorkerChanges = computed(() => {
  if (!currentEditingTask.value) return false;
  
  // 获取原始工人 ID 集合
  const originalIds = new Set();
  for (const [trade, names] of Object.entries(currentEditingTask.value.workers || {})) {
    const nameArray = Array.isArray(names) ? names : [names];
    for (const name of nameArray) {
      const worker = workerPool.value.find(w => w.type === trade && w.name === name);
      if (worker) originalIds.add(worker.id);
    }
  }
  
  // 获取当前选择的工人 ID 集合
  const currentIds = new Set();
  for (const ids of Object.values(editingWorkers.value)) {
    const idArray = Array.isArray(ids) ? ids : (ids != null ? [ids] : []);
    idArray.forEach(id => currentIds.add(id));
  }
  
  // 对比
  if (originalIds.size !== currentIds.size) return true;
  for (const id of originalIds) {
    if (!currentIds.has(id)) return true;
  }
  return false;
});

// 获取每个工种的当前已选工人 ID（用于禁用下拉选项）
const currentSelectedWorkerIdsByTrade = computed(() => {
  const result = {};
  for (const [trade, ids] of Object.entries(editingWorkers.value)) {
    const idArray = Array.isArray(ids) ? ids : (ids != null ? [ids] : []);
    result[trade] = new Set(idArray.filter(id => id != null));
  }
  return result;
});

async function saveWorkersEdit() {
  if (!currentEditingTask.value) return;
  const task = currentEditingTask.value;
  const taskStart = task.startDay;
  const taskEnd = task.endDay;
  const processId = task.processId;

  // 收集新分配的工人信息
  const newWorkerIds = [];
  const newWorkersObj = {};
  const newWorkersTextParts = [];

  for (const [trade, ids] of Object.entries(editingWorkers.value)) {
    const idArray = Array.isArray(ids) ? ids : (ids != null ? [ids] : []);
    const names = [];
    for (const id of idArray) {
      const worker = workerPool.value.find(w => w.id === id);
      if (worker) {
        names.push(worker.name);
        newWorkerIds.push(id);
      }
    }
    if (names.length > 0) {
      newWorkersObj[trade] = names;
      newWorkersTextParts.push(`${trade}: ${names.join('、')}`);
    }
  }
  const allConflicts = []; // 结构: [{ worker, conflicts }]
  for (const workerId of newWorkerIds) {
    const conflicts = findConflictingTasks(workerId, taskStart, taskEnd, processId);
    if (conflicts.length) {
      const worker = workerPool.value.find(w => w.id === workerId);
      allConflicts.push({ worker, conflicts });
    }
  }
  // 如果有冲突，弹出确认框
  if (allConflicts.length > 0) {
    const conflictMessages = allConflicts.map(item => {
      const workerName = item.worker.name;
      const taskNames = item.conflicts.map(c => `「${c.task}」(${c.device})`).join('、');
      return `• ${workerName} 与 ${taskNames} 时间冲突`;
    }).join('\n');

    try {
      await ElMessageBox.confirm(
        `检测到以下时间冲突：\n${conflictMessages}\n\n是否强制分配？确认后将自动从冲突任务中移除该工人，后续请为冲突任务重新分配人员。`,
        '强制分配确认',
        {
          type: 'warning',
          confirmButtonText: '强制分配',
          cancelButtonText: '取消',
          dangerouslyUseHTMLString: false,
        }
      );
    } catch {
      return; // 用户取消，终止操作
    }
  }

  // ========== 执行强制分配 ==========
  // 1. 从冲突任务中移除相关工人
  const affectedTaskNames = new Set(); // 记录受影响的冲突任务名称，用于提示

  for (const item of allConflicts) {
    const workerId = item.worker.id;
    const workerName = item.worker.name;

    for (const conflictTask of item.conflicts) {
      const conflictRow = assignmentRows.value.find(r => r.processId === conflictTask.processId);
      if (!conflictRow) continue;

      // 从 workers 对象中移除该工人
      const newWorkers = { ...conflictRow.workers };
      for (const [trade, names] of Object.entries(newWorkers)) {
        if (Array.isArray(names)) {
          const filtered = names.filter(name => name !== workerName);     
          newWorkers[trade] = filtered;
        }
      }
      conflictRow.workers = newWorkers;

      // 更新 workersText
      const textParts = [];
      for (const [trade, names] of Object.entries(newWorkers)) {
      const nameStr = Array.isArray(names) && names.length > 0 
        ? names.join('、') 
        : '待分配'; // ✅ 无工人时显示“待分配”
      textParts.push(`${trade}: ${nameStr}`);
    }
    conflictRow.workersText = textParts.join('；');

      // 记录受影响的冲突任务名称
      affectedTaskNames.add(`${conflictTask.task} (${conflictTask.device})`);
    }
  }

  // 2. 更新当前编辑任务
  const rowIndex = assignmentRows.value.findIndex(r => r.processId === processId);
  if (rowIndex !== -1) {
    assignmentRows.value[rowIndex].workers = newWorkersObj;
    assignmentRows.value[rowIndex].workersText = newWorkersTextParts.join('；');
  }

  // 3. 同步到 localStorage
  syncSchedulePlanToStorage();

  // 4. 刷新甘特图
  showGanttView.value = false;
  await nextTick();
  showGanttView.value = true;

  // 5. 关闭弹窗并给出最终提示
  editWorkerDialogVisible.value = false;

  if (allConflicts.length > 0) {
    const taskListStr = Array.from(affectedTaskNames).join('、');
    ElMessage.success(`已强制分配。请记得为以下冲突任务重新分配人员：${taskListStr}`);
  } else {
    ElMessage.success('工人更换成功');
  }
}

// 在现有响应式变量定义区域添加
const generatingWorkOrders = ref(false)
// 新增方法
async function generateWorkOrders() {
  generatingWorkOrders.value = true
  try {
    const result = await request({
      url: '/api/assign-workers-from-schedule',
      method: 'post',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
      // 不需要传递 body，后端自动处理
    })
    if (result.success) {
      ElMessage.success(`工人分配成功！共处理 ${result.assigned_count} 个任务`)
    } else {
      ElMessage.error(result.message || '工人分配失败')
    }
  } catch (error) {
    console.error('工人分配失败:', error)
    ElMessage.error('工人分配失败，请检查后端服务')
  } finally {
    generatingWorkOrders.value = false
  }
}


const devices = ref()
devices.value = JSON.parse(localStorage.getItem('devices'))

const deviceForm = reactive({
  id: 0,
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

const workers = ref()
workers.value = JSON.parse(localStorage.getItem('workers'))

// 添加工人池获取函数
const fetchWorkerPool = async () => {
  try {
    const res = await axios.get('/api/workers')
    if (res.data.success && res.data.data && res.data.data.workers) {
      // 将 worker_type_id 转换为 type 字段
      workerPool.value = res.data.data.workers.map(w => ({
        ...w,
        type: w.worker_type_id || w.type  // 新增：兼容已有 type 字段的数据
      }))
      console.log('工人池数据已加载:', workerPool.value)
    }
  } catch (error) {
    console.error('获取工人池数据失败:', error)
    // 失败时降级使用 localStorage
    workerPool.value = (workers.value || []).map(w => ({
      ...w,
      type: w.worker_type_id || w.type
    }))
  }
}
console.log('workers:', workers.value)


const algorithmOptions = [
  { label: 'deepseek', value: 'topological' },
  { label: 'chatGPT—4.5', value: 'greedy' },
  { label: 'Claude', value: 'genetic' },
  { label: 'CodeX', value: 'spt' },
  { label:'通义千问', value:'lowest_cost'}
]
const selectedAlgorithm = ref('topological')
const selectedTarget = ref('minimize_duration') // 添加默认目标选择
const loadingSchedule = ref(false)
const assignmentRows = ref([])
const workerNameFilter = ref('')
const showGanttView = ref(false) // 新增状态控制GanttView显示
const showScheduleTable = ref(false) // 控制课表弹窗显示
const selectedScheduleEquipment = ref('') // 添加设备筛选状态

// 添加计算属性，用于筛选按工人姓名的任务
// 修改filteredAssignmentRows计算属性中的排序逻辑
const filteredAssignmentRows = computed(() => {
  if (!workerNameFilter.value) {
    return assignmentRows.value
  }
  
  const workerName = workerNameFilter.value.trim();
  if (!workerName) {
    return assignmentRows.value
  }
  
  // 筛选逻辑保持不变
  const filtered = assignmentRows.value.filter(row => {
    const workerGroups = row.workersText.split('；');
    for (const group of workerGroups) {
      const parts = group.split(': ');
      if (parts.length > 1) {
        const workersPart = parts[1];
        const workers = workersPart.split('、');
        if (workers.some(worker => worker.includes(workerName))) {
          return true;
        }
      }
    }
    return false;
  })
  
  // 按开始时间中的天数升序排列（提取"第X天"中的数字进行比较）
  return filtered.sort((a, b) => {
    // 从开始时间字符串中提取天数（假设格式如"第1天 08:00"）
    const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    
    // 先按天数排序
    if (dayA !== dayB) {
      return dayA - dayB;
    }
    
    // 天数相同则按时间排序
    const timeA = a.startTimeFormatted.split(' ')[1];
    const timeB = b.startTimeFormatted.split(' ')[1];
    return timeA.localeCompare(timeB);
  })
})

// 添加课表数据计算属性
const scheduleTableData = computed(() => {
  if (!workerNameFilter.value) return {}
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return {}
  
  // 筛选包含该工人的任务
  const workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 按天数分组任务
  const tasksByDay = {}
  workerTasks.forEach(task => {
    const dayMatch = task.startTimeFormatted.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      if (!tasksByDay[day]) {
        tasksByDay[day] = []
      }
      tasksByDay[day].push(task)
    }
  })
  
  return tasksByDay
})

// 获取最大天数


// 获取设备列表用于筛选
const scheduleEquipmentOptions = computed(() => {
  if (!workerNameFilter.value) return []
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return []
  
  // 获取该工人的所有任务涉及的设备
  const workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 提取唯一的设备名称
  const equipmentSet = new Set()
  workerTasks.forEach(task => {
    if (task.device) {
      equipmentSet.add(task.device)
    }
  })
  
  // 转换为选项数组
  return Array.from(equipmentSet).map(equipment => ({
    label: equipment,
    value: equipment
  }))
})

// 添加当前周数状态
const currentWeek = ref(1)

// 修改时间槽计算，只显示当前周的时间
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 19; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    slots.push(`${hour.toString().padStart(2, '0')}:30`)
  }
  // 添加最后一小时的结束时间20:00
  slots.push(`20:00`)
  return slots
})

// 修改课表数据计算属性，只返回当前周的数据
const weeklyScheduleTableData = computed(() => {
  if (!workerNameFilter.value) return {}
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return {}
  
  // 筛选包含该工人的任务
  let workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 如果选择了特定设备，则进一步筛选
  if (selectedScheduleEquipment.value) {
    workerTasks = workerTasks.filter(task => task.device === selectedScheduleEquipment.value)
  }
  
  // 按天数分组任务，并只返回当前周的数据
  const tasksByDay = {}
  const startDay = (currentWeek.value - 1) * 7 + 1
  const endDay = currentWeek.value * 7
  
  workerTasks.forEach(task => {
    const dayMatch = task.startTimeFormatted.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      // 只处理当前周的天数
      if (day >= startDay && day <= endDay) {
        const weekDay = day - startDay + 1
        if (!tasksByDay[weekDay]) {
          tasksByDay[weekDay] = []
        }
        // 更新任务中的天数信息以适应当前周显示
        const updatedTask = {...task}
        tasksByDay[weekDay].push(updatedTask)
      }
    }
  })
  
  return tasksByDay
})

// 计算总周数
const totalWeeks = computed(() => {
  const days = Object.keys(scheduleTableData.value).map(day => parseInt(day))
  const maxDay = days.length > 0 ? Math.max(...days) : 0
  return Math.ceil(maxDay / 7) || 1
})

// 上一周
function prevWeek() {
  if (currentWeek.value > 1) {
    currentWeek.value--
  }
}

// 下一周
function nextWeek() {
  if (currentWeek.value < totalWeeks.value) {
    currentWeek.value++
  }
}

// 跳转到指定周
function goToWeek(week) {
  if (week >= 1 && week <= totalWeeks.value) {
    currentWeek.value = week
  }
}

// 获取显示用的结束时间
function getDisplayEndTime(endTimeFormatted) {
  // 检查结束时间是否为8:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      // 将第n天8:00改为第(n-1)天20:00
      return `第${day - 1}天 20:00`
    }
  }
  return endTimeFormatted
}

// 根据任务时间获取在课表中的位置
function getTaskPosition(task) {
  // 处理特殊情况：如果结束时间是第n天的8:00，应该显示为第(n-1)天的20:00
  let startTimeFormatted = task.startTimeFormatted
  let endTimeFormatted = task.endTimeFormatted
  
  // 检查结束时间是否为8:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      // 将第n天8:00改为第(n-1)天20:00
      endTimeFormatted = `第${day - 1}天 20:00`
    }
  }
  
  const startTimeMatch = startTimeFormatted.match(/(\d+):(\d+)$/)
  const endTimeMatch = endTimeFormatted.match(/(\d+):(\d+)$/)
  
  if (!startTimeMatch || !endTimeMatch) return null
  
  const startHour = parseInt(startTimeMatch[1])
  const startMinute = parseInt(startTimeMatch[2])
  const endHour = parseInt(endTimeMatch[1])
  const endMinute = parseInt(endTimeMatch[2])
  
  // 计算开始和结束的时间槽索引（从8:00开始，每半小时一个槽）
  const startIndex = (startHour - 8) * 2 + (startMinute >= 30 ? 1 : 0)
  const endIndex = (endHour - 8) * 2 + (endMinute >= 30 ? 1 : 0)
  
  return {
    startIndex,
    endIndex,
    span: endIndex - startIndex
  }
}

// 获取任务的样式
function getTaskPositionStyle(task) {
  const position = getTaskPosition(task)
  if (!position) return {}
  
  // 每个时间槽高度为40px，与CSS中的.grid-template-rows保持一致
  // 为了精确对齐，top应该等于startIndex * 40px
  const top = position.startIndex * 40
  // 高度应该等于span * 40px，减去2px以留出适当的间隔
  const height = position.span * 40 - 1
  
  // 根据设备ID获取颜色，确保每个设备实例有不同的颜色
  const taskWithEquipmentId = assignmentRows.value.find(row => row.processId === task.processId)
  let backgroundColor = '#ccc' // 默认颜色
  
  if (taskWithEquipmentId && taskWithEquipmentId.equipmentId) {
    // 使用已有的设备颜色映射或创建新的颜色
    if (!equipmentColors.has(taskWithEquipmentId.equipmentId)) {
      equipmentColors.set(taskWithEquipmentId.equipmentId, colorPalette[equipmentColors.size % colorPalette.length])
    }
    backgroundColor = equipmentColors.get(taskWithEquipmentId.equipmentId)
  }
  
  return {
    top: `${top}px`,
    height: `${height}px`,
    backgroundColor: backgroundColor
  }
}

// 显示工人课表
function showWorkerSchedule() {
  if (!workerNameFilter.value.trim()) {
    ElMessage.warning('请输入工人姓名')
    return
  }
  currentWeek.value = 1 // 重置到第一周
  selectedScheduleEquipment.value = '' // 重置设备筛选
  showScheduleTable.value = true
}

// 关闭课表弹窗
function closeScheduleTable() {
  showScheduleTable.value = false
  selectedScheduleEquipment.value = '' // 清除设备筛选
}

function buildWorkerBusyMap(schedulePlan) {
  const map = new Map();
  schedulePlan.forEach(task => {
    const startDay = task.start_time;
    const endDay = task.end_time;
    if (task.workers) {
      for (const [trade, names] of Object.entries(task.workers)) {
        names.forEach(name => {
          const worker = workerPool.value.find(w => w.type === trade && w.name === name);
          if (worker) {
            const slots = map.get(worker.id) || [];
            slots.push({ start: startDay, end: endDay });
            map.set(worker.id, slots);
          }
        });
      }
    }
  });
  workerBusyMap.value = map;
}
// 统计信息相关数据
const equipmentUtilizationData = ref([]) // 设备利用率数据
const workerTypeUtilizationData = ref([]) // 工种利用率数据
const statisticsData = ref({
  total_project_duration_days: 0,
  total_project_duration_hours: 0,
  total_workers: 0,
  total_equipments: 0,
  total_processes: 0
})
function isWorkerConflicted(workerId) {
  if (!currentEditingTask.value) return false;
  const task = currentEditingTask.value;
  const conflicts = findConflictingTasks(
    workerId,
    task.startDay,
    task.endDay,
    task.processId
  );
  return conflicts.length > 0;
}
// 判断工人是否是当前任务的已选工人（同一工种内）
function isWorkerCurrentlySelected(workerId, trade) {
  const selectedIds = currentSelectedWorkerIdsByTrade.value[trade];
  return selectedIds?.has(workerId) ?? false;
}
// 返回冲突任务列表（每个冲突任务包含完整行数据）
function findConflictingTasks(workerId, taskStart, taskEnd, excludeProcessId = null) {
  const conflicts = [];
  for (const row of assignmentRows.value) {
    if (excludeProcessId && row.processId === excludeProcessId) continue;

    // 提取当前任务中所有工人的 ID
    const workerIdsInTask = [];
    if (row.workers) {
      for (const [trade, names] of Object.entries(row.workers)) {
        const nameArray = Array.isArray(names) ? names : [names];
        for (const name of nameArray) {
          const worker = workerPool.value.find(w => w.type === trade && w.name === name);
          if (worker) workerIdsInTask.push(worker.id);
        }
      }
    }

    if (!workerIdsInTask.includes(workerId)) continue;

    // 时间段重叠判断
    if (taskStart < row.endDay && taskEnd > row.startDay) {
      conflicts.push({ ...row }); // 返回副本避免意外修改
    }
  }
  return conflicts;
}
function syncSchedulePlanToStorage() {
  const schedulePlan = JSON.parse(localStorage.getItem('schedule_plan') || '[]');
  assignmentRows.value.forEach(row => {
    const planIndex = schedulePlan.findIndex(p => p.process_id === row.processId);
    if (planIndex !== -1) {
      schedulePlan[planIndex].workers = row.workers;
    }
  });
  localStorage.setItem('schedule_plan', JSON.stringify(schedulePlan));
}

// 导出任务分配明细为Excel文件
function exportAssignmentToExcel() {
  if (!assignmentRows.value || assignmentRows.value.length === 0) {
    ElMessage.warning('没有数据可以导出')
    return
  }

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  
  // 准备第一个工作表的数据 - 按开始时间排序
  const sortedByStartTime = [...assignmentRows.value].sort((a, b) => {
    // startTimeFormatted 格式为 "YYYY-MM-DD HH:MM:SS"，字符串字典序即时间顺序
    return a.startTimeFormatted.localeCompare(b.startTimeFormatted)
  });
  
  const data1 = sortedByStartTime.map(row => ({
    '任务': row.task,
    '设备': row.device,
    '工序ID': row.processId,
    '设备ID': row.equipmentId,
    '工人': row.workersText,
    '开始时间': row.startTimeFormatted,
    '结束时间': row.endTimeFormatted,
    '工时(h)': row.durationHours
  }));

  // 创建第一个工作表（按开始时间排序）
  const ws1 = XLSX.utils.json_to_sheet(data1)
  ws1['!cols'] = [
    { wch: 20 }, // 任务
    { wch: 20 }, // 设备
    { wch: 15 }, // 工序ID
    { wch: 15 }, // 设备ID
    { wch: 30 }, // 工人
    { wch: 20 }, // 开始时间
    { wch: 20 }, // 结束时间
    { wch: 10 }  // 工时(h)
  ]
  XLSX.utils.book_append_sheet(wb, ws1, '按开始时间排序')

  // 准备第二个工作表的数据 - 按设备分类排序
  const groupedByDevice = {};
  assignmentRows.value.forEach(row => {
    if (!groupedByDevice[row.device]) {
      groupedByDevice[row.device] = [];
    }
    groupedByDevice[row.device].push(row);
  });

  // 对每个设备内的工序按开始时间排序
  Object.keys(groupedByDevice).forEach(device => {
    groupedByDevice[device].sort((a, b) => {
      // startTimeFormatted 格式为 "YYYY-MM-DD HH:MM:SS"，字符串字典序即时间顺序
      return a.startTimeFormatted.localeCompare(b.startTimeFormatted)
    });
  });

  // 按设备名称排序
  const sortedDevices = Object.keys(groupedByDevice).sort();

  // 创建按设备分类的数据数组，设备之间插入空行
  const data2 = [];
  sortedDevices.forEach((device, index) => {
    // 添加设备内排序好的工序
    groupedByDevice[device].forEach(row => {
      data2.push({
        '任务': row.task,
        '设备': row.device,
        '工序ID': row.processId,
        '设备ID': row.equipmentId,
        '工人': row.workersText,
        '开始时间': row.startTimeFormatted,
        '结束时间': row.endTimeFormatted,
        '工时(h)': row.durationHours
      });
    });
    
    // 如果不是最后一个设备，添加一个空行
    if (index < sortedDevices.length - 1) {
      data2.push({
        '任务': '',
        '设备': '',
        '工序ID': '',
        '设备ID': '',
        '工人': '',
        '开始时间': '',
        '结束时间': '',
        '工时(h)': ''
      });
    }
  });

  // 创建第二个工作表（按设备分类排序）
  const ws2 = XLSX.utils.json_to_sheet(data2)
  ws2['!cols'] = [
    { wch: 20 }, // 任务
    { wch: 20 }, // 设备
    { wch: 15 }, // 工序ID
    { wch: 15 }, // 设备ID
    { wch: 30 }, // 工人
    { wch: 20 }, // 开始时间
    { wch: 20 }, // 结束时间
    { wch: 10 }  // 工时(h)
  ]
  XLSX.utils.book_append_sheet(wb, ws2, '按设备排序')

  // 导出文件
  const filename = '任务分配明细.xlsx'
  XLSX.writeFile(wb, filename)
  
  ElMessage.success('导出成功')
}


const ganttVisible = ref(false)




// 任务数据
const tasks = ref()
tasks.value = JSON.parse(localStorage.getItem('tasks'))
console.log('任务数据:', tasks.value)




// =================== 甘特图 三层交互逻辑（ECharts） ===================
// 层级：overview -> device -> worker
const currentLevel = ref('overview')
const currentDeviceId = ref(null)
const currentDeviceName = ref('')
const currentWorkerInfo = ref(null)
const currentProcessInfo = ref(null)
const currentCategory = ref('')

// 甘特图数据：总览层（设备分类的检修任务段）
// 时间单位以时间戳毫秒为准


// 是否使用真实调度结果驱动甘特图
const useRealSchedule = ref(false)
// 由后端调度结果转换得到的甘特图行
const scheduleGanttRows = ref([])
const equipmentColors = reactive(new Map())
const colorPalette = ['#5470C6', '#91CC75', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']



// 根据设备名称推断设备类型
function inferDeviceType(equipmentName) {
  if (!equipmentName) return '未分类'

  const name = equipmentName.toLowerCase()

  // 静设备关键词
  if (name.includes('塔') || name.includes('罐') || name.includes('炉') ||
    name.includes('换热器') || name.includes('容器') || name.includes('反应器')) {
    return '静设备'
  }

  // 动设备关键词
  if (name.includes('泵') || name.includes('压缩机') || name.includes('风机') ||
    name.includes('电机') || name.includes('汽轮机')) {
    return '动设备'
  }

  // 特种设备关键词
  if (name.includes('变压器') || name.includes('开关') || name.includes('仪表') ||
    name.includes('阀门') || name.includes('管道')) {
    return '特种设备'
  }

  return '未分类'
}



function buildScheduleRows(plan, startDateTimeStr) {
  if (!plan || plan.length === 0) return
  equipmentColors.clear()
  const rows = []
  plan.forEach(t => {
    const startDay = t.start_time        // 相对天数（如 0.0, 0.33）
    const endDay = t.end_time
    const color = equipmentColors.get(t.equipment_id) || colorPalette[equipmentColors.size % colorPalette.length]
    if (!equipmentColors.has(t.equipment_id)) {
      equipmentColors.set(t.equipment_id, color)
    }
    rows.push({
      y: t.equipment_name,
      start: startDay,
      end: endDay,
      name: t.process_name,
      color,
      deviceName: t.equipment_name,
      processName: t.process_name,
      workers: t.workers,
      startFormatted: t.start_time_formatted,
      endFormatted: t.end_time_formatted,
      meta: {
        level: 'overview',
        deviceType: inferDeviceType(t.equipment_name),
        deviceName: t.equipment_name,
        processId: t.process_id,
        workers: t.workers,
        startFormatted: t.start_time_formatted,
        endFormatted: t.end_time_formatted
      }
    })
  })
  scheduleGanttRows.value = rows
  saveScheduleGanttRowsToLocalStorage()
}

// 保存scheduleGanttRows到localStorage
function saveScheduleGanttRowsToLocalStorage() {
  try {
    // 创建数据副本并转换Date对象为时间戳
    const rowsToSave = scheduleGanttRows.value.map(row => {
      return {
        ...row,
        start: row.start instanceof Date ? row.start.getTime() : row.start,
        end: row.end instanceof Date ? row.end.getTime() : row.end,
        // meta对象保持不变
        meta: row.meta
      }
    })
    
    localStorage.setItem('scheduleGanttRows', JSON.stringify(rowsToSave))
    console.log('甘特图数据已保存')
  } catch (e) {
    console.error('保存甘特图数据到localStorage失败:', e)
  }
}

function getOverviewOption() {
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无调度数据，请先执行调度', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按设备类型分组（同原逻辑）
  const typeMap = new Map()
  scheduleGanttRows.value.forEach(row => {
    const type = row.meta.deviceType || '未分类'
    if (!typeMap.has(type)) {
      typeMap.set(type, { start: row.start, end: row.end, tasks: [] })
    }
    const group = typeMap.get(type)
    group.start = Math.min(group.start, row.start)
    group.end = Math.max(group.end, row.end)
    group.tasks.push(row)
  })

  const dataRows = []
  const yCategories = []
  for (const [type, group] of typeMap.entries()) {
    yCategories.push(type)
    const color = group.tasks[0]?.color || '#409EFF'
    dataRows.push({
      y: type,
      start: group.start,
      end: group.end,
      name: `${type}检修`,
      color: color,
      meta: { level: 'overview', category: type, deviceType: type }
    })
  }

  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: { text: '三层交互式检修进度甘特图（按设备类型）', left: 10, top: 10, textStyle: { fontSize: 16, fontWeight: 'bold' } },
    backgroundColor: '#fafafa',
    legend: { type: 'plain', orient: 'vertical', right: 20, top: 60, data: legendData, textStyle: { fontSize: 12 } },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;   // 开始天数
    const endDay = Math.floor(v[2]) + 1;     // 结束天数
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天`;
      },
      backgroundColor: 'rgba(0,0,0,0.8)'
    },
    grid: { left: 100, right: 160, top: 100, bottom: 60, containLabel: true },
    xAxis: {
      type: 'value',
      name: '调度天数',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1
          return `第${day}天`
        }
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } }
    },
    yAxis: { type: 'category', data: yCategories, axisLabel: { fontSize: 13 } },
    series: buildCustomSeries(dataRows, yCategories)
  }
}

const ganttEl = ref(null)
let chart = null
let ro = null // ResizeObserver

function buildCustomSeries(dataRows, yCategories) {
  const seriesData = dataRows.map((r, index) => {
    const yIndex = yCategories.indexOf(r.y)
    if (yIndex < 0) return null
    return [yIndex, r.start, r.end, r.name, r.meta, r.color]
  }).filter(item => item !== null)

  return [{
    type: 'custom',
    name: '设备进度',
    silent: false,
    triggerEvent: true,
    renderItem(params, api) {
      const yIndex = api.value(0)
      const startDay = api.value(1)
      const endDay = api.value(2)
      const color = api.value(5)

      const startCoord = api.coord([startDay, yIndex])
      const endCoord = api.coord([endDay, yIndex])
      const height = api.size([0, 1])[1] * 0.4
      const y = startCoord[1] - height / 2
      const x = startCoord[0]
      const width = Math.max(3, endCoord[0] - startCoord[0])

      return {
        type: 'rect',
        shape: { x, y, width, height },
        style: { fill: color },
        emphasis: { style: { fill: color, opacity: 0.8 } }
      }
    },
    encode: { x: [1, 2], y: 0 },
    data: seriesData
  }]
}

function renderChart() {
  console.log('开始渲染甘特图，ganttEl.value:', ganttEl.value)
  if (!ganttEl.value) {
    console.error('甘特图容器元素不存在')
    return
  }
  if (!chart) {
    chart = echarts.init(ganttEl.value)
    console.log('ECharts 实例已初始化，准备注册点击事件。') // 调试信息
  }

  // 确保事件绑定在每次渲染时都重新绑定
  if (chart) {
    // 先移除旧的事件监听器
    chart.off('click')

    // 甘特图点击事件处理
    chart.on('click', (params) => {
      console.log('=== 甘特图点击事件触发 ===')
      console.log('点击事件参数:', params)

      // 简单的点击测试
      ElMessage.success('甘特图被点击了！')

      // 检查数据结构
      if (params.value && params.value.length >= 5) {
        const meta = params.value[4]
        console.log('点击元数据:', meta)

        if (meta && meta.level === 'overview') {
          // 真实数据：点击类别 -> 第二层
          if (useRealSchedule.value) {
            currentLevel.value = 'device'
            currentCategory.value = meta.category || meta.deviceName || ''
            updateChart()
            return
          }
          console.log('点击总览层，设备ID:', meta.deviceId)
          if (meta.deviceId === 1) { // 静设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else if (meta.deviceId === 2) { // 动设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else if (meta.deviceId === 3) { // 特种设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else {
            // 其他设备类型暂时显示总览
            ElMessage.info('该设备类型暂未开放详细视图')
          }
        } else if (meta && meta.level === 'device') {
          // 真实数据：点击某台设备 -> 第三层（展示工序详情）
          if (useRealSchedule.value) {
            currentLevel.value = 'worker'
            currentDeviceName.value = meta.deviceName
            currentWorkerInfo.value = { requiredTrade: '工序详情', processName: meta.deviceName }
            updateChart()
            ElMessage.info(`查看设备: ${meta.deviceName} 的工序详情`)
            return
          }
          console.log('点击设备层工序')
          // 设置当前工序信息
          currentProcessInfo.value = {
            deviceName: meta.deviceName,
            processName: params.value[3],
            requiredTrade: meta.requiredTrade
          }
          // 切换到第三层工人详情
          currentLevel.value = 'worker'
          currentWorkerInfo.value = {
            requiredTrade: meta.requiredTrade,
            processName: params.value[3]
          }
          console.log('切换到工人层:', currentWorkerInfo.value)
          updateChart()
        } else if (meta && meta.level === 'worker') {
          console.log('点击工人层')
          // 显示工人详情
          ElMessage.info(`工人详情: ${meta.worker.name} - ${meta.worker.level}`)
        } else {
          console.log('未识别的点击类型或缺少元数据')
        }
      } else {
        console.log('点击数据格式不正确:', params.value)
      }
    })
  }

  updateChart()
}


function updateChart() {
  console.log('更新甘特图，当前层级:', currentLevel.value)
  if (!chart) {
    console.error('图表实例不存在')
    return
  }

  let option = null
  if (currentLevel.value === 'overview') {
    option = getOverviewOption()
    console.log('使用总览层配置:', option)
  } else if (currentLevel.value === 'device') {
    option = getStaticDeviceOption()
    console.log('使用设备层配置:', option)
  } else if (currentLevel.value === 'worker') {
    option = getWorkerOption(currentWorkerInfo.value?.requiredTrade || '工序详情')
    console.log('使用工人层配置:', option)
  }

  if (option) {
    chart.setOption(option, true)
    console.log('甘特图配置已应用')
  }

  nextTick(() => {
    if (chart) {
      chart.resize()
      console.log('甘特图已调整大小')
    }
  })
}



function setupResize() {
  if (!ganttEl.value) return
  ro = new ResizeObserver(() => {
    chart && chart.resize()
  })
  ro.observe(ganttEl.value)
  window.addEventListener('resize', onWindowResize)
}
function teardownResize() {
  window.removeEventListener('resize', onWindowResize)
  if (ro) { ro.disconnect(); ro = null }
}
function onWindowResize() { chart && chart.resize() }

watch(ganttVisible, async (val) => {
  if (val) {
    await nextTick()
    currentLevel.value = 'overview'
    renderChart()
    setupResize()
  } else {
    teardownResize()
    if (chart) { chart.dispose(); chart = null }
  }
})

onBeforeUnmount(() => {
  teardownResize()
  if (chart) { chart.dispose(); chart = null }
})

function getStaticDeviceOption() {
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无设备数据', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 筛选当前类别的任务
  const categoryRows = scheduleGanttRows.value.filter(
    row => row.meta.deviceType === currentCategory.value
  )
  if (categoryRows.length === 0) {
    return {
      title: { text: `${currentCategory.value} 类别下无设备数据`, left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按设备名称分组
  const deviceMap = new Map()
  categoryRows.forEach(row => {
    const deviceName = row.deviceName
    if (!deviceMap.has(deviceName)) {
      deviceMap.set(deviceName, { start: row.start, end: row.end, tasks: [] })
    }
    const group = deviceMap.get(deviceName)
    group.start = Math.min(group.start, row.start)
    group.end = Math.max(group.end, row.end)
    group.tasks.push(row)
  })

  const dataRows = []
  const yCategories = []
  for (const [deviceName, group] of deviceMap.entries()) {
    yCategories.push(deviceName)
    const color = group.tasks[0]?.color || '#1890ff'
    dataRows.push({
      y: deviceName,
      start: group.start,
      end: group.end,
      name: deviceName,
      color: color,
      meta: { level: 'device', deviceName: deviceName, category: currentCategory.value }
    })
  }

  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: {
      text: `${currentCategory.value} - 设备列表`,
      left: 10,
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold', color: '#000' }
    },
    backgroundColor: '#fafafa',
    legend: {
      type: 'plain',
      orient: 'vertical',
      right: 20,
      top: 60,
      selectedMode: false,
      data: legendData,
      textStyle: { fontSize: 12, color: '#333' },
      itemWidth: 20,
      itemHeight: 14,
      itemGap: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;
    const endDay = Math.floor(v[2]) + 1;
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天`;
      },
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#333',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: 100,
      right: 160,
      top: 100,
      bottom: 60,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1; // 将相对天数转为“第X天”，假设项目从第1天开始
    return `第${day}天`;
        },
        fontSize: 11,
        color: '#666'
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: { fontSize: 13, fontWeight: '500', color: '#333' },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    series: buildCustomSeries(dataRows, yCategories)
  }
}

function getWorkerOption(requiredTrade) {
  // 注意：requiredTrade 参数在真实调度中可能不再使用，这里改为显示当前选中设备的工序
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无工序数据', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 获取当前选中设备的所有工序
  const deviceRows = scheduleGanttRows.value.filter(
    row => row.deviceName === currentDeviceName.value
  )
  if (deviceRows.length === 0) {
    return {
      title: { text: `${currentDeviceName.value} 无工序数据`, left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按工序名称分组（通常每个工序独立显示）
  const dataRows = deviceRows.map(row => ({
    y: row.processName,
    start: row.start,
    end: row.end,
    name: row.processName,
    color: row.color,
    meta: {
      level: 'worker',
      deviceName: row.deviceName,
      processName: row.processName,
      workers: row.workers
    }
  }))

  const yCategories = dataRows.map(r => r.y)
  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: {
      text: `${currentDeviceName.value} - 工序详情`,
      left: 10,
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold', color: '#000' }
    },
    backgroundColor: '#fafafa',
    legend: {
      type: 'plain',
      orient: 'vertical',
      right: 20,
      top: 60,
      selectedMode: false,
      data: legendData,
      textStyle: { fontSize: 12, color: '#333' },
      itemWidth: 20,
      itemHeight: 14,
      itemGap: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;
    const endDay = Math.floor(v[2]) + 1;
    const meta = v[4];
    let workersInfo = '';
    if (meta && meta.workers) {
      const workerList = [];
      Object.entries(meta.workers).forEach(([trade, names]) => {
        if (Array.isArray(names) && names.length) {
          workerList.push(`${trade}: ${names.join('、')}`);
        }
      });
      workersInfo = workerList.length ? `<br/>工人:<br/>${workerList.join('<br/>')}` : '';
    }
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天${workersInfo}`;
  },
  backgroundColor: 'rgba(0,0,0,0.8)',
  borderColor: '#333',
  textStyle: { color: '#fff' }
    },
    grid: {
      left: 100,
      right: 160,
      top: 100,
      bottom: 60,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1; // 将相对天数转为“第X天”，假设项目从第1天开始
    return `第${day}天`;
        },
        fontSize: 11,
        color: '#666'
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: { fontSize: 13, fontWeight: '500', color: '#333' },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    series: buildCustomSeries(dataRows, yCategories)
  }
}
onMounted(async() => {
  await fetchPlans()
  await fetchWorkerPool() 
})
</script>

<style scoped>
/* 全局CSS变量定义 */

.worker-edit-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.no-change-tip {
  color: #909399;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer-buttons {
  display: flex;
  gap: 12px;
}

:root {
  --primary-color: #409EFF;
  --success-color: #67C23A;
  --warning-color: #E6A23C;
  --error-color: #F56C6C;
  --bg-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e4e7ed;
  --text-primary: #303133;
  --text-secondary: #606266;
  --text-muted: #909399;
}

.current-worker-option {
  background-color: #f4f4f5 !important;
  color: #909399 !important;
  cursor: not-allowed;
}

.current-worker-option::after {
  content: ' (当前)';
  color: #c0c4cc;
  font-size: 12px;
}

/* 全局平滑过渡 */
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
}

.home-container {
  min-height: 100vh;
  padding: 20px 24px;
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.top-bar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  margin-bottom: 20px;
  background: #ffffff !important;
  color: #303133;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
}

.brand .title {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.button-group {
  display: flex;
  gap: 12px;
}

.button-group .schedule-btn,
.button-group .gantt-btn,
.button-group .save-btn {
  align-items: center;
  justify-content: center;
  width: 5vw;
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 20px;
  height: calc(100vh - 140px);
}

.left,
.center {

  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 83vh;
  width: 20vw;
  margin-left: 50vw;
  overflow: auto;
}

.right {
  width: 60vw;

}

.panel-card {
  background: #ffffff !important;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 1px 4px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: auto;
  width: 85vw;
}

.panel-card:hover {
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.panel-header {
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-radius: 16px 16px 0 0;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 0;
}

.panel-header:hover {
  background: linear-gradient(90deg, #f8f9fa 0%, #f5f6f8 100%);
}

.panel-title {
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  font-size: 16px;
}

.panel-title .el-icon {
  color: var(--primary-color);
  font-size: 18px;
  margin-right: 8px;
}

.panel-tools {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-body {
  padding: 20px;
}

/* 间距工具类 */
.mr6 {
  margin-right: 6px;
}

.mx8 {
  margin: 0 8px;
}

.mr4 {
  margin-right: 4px;
}

.ml4 {
  margin-left: 4px;
}

.mt8 {
  margin-top: 8px;
}

.mt12 {
  margin-top: 12px;
}

.mb8 {
  margin-bottom: 8px;
}

.w100 {
  width: 100%;
}

.map-card {
  height: 100%;
  border-radius: 16px;
  overflow: auto;
}

.map-placeholder {
  height: 100%;
  border-radius: 8px;
  background: repeating-linear-gradient(45deg, #f7f9fc, #f7f9fc 10px, #f2f5fb 10px, #f2f5fb 20px);
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  font-weight: 500;
  font-size: 16px;
  transition: all 0.3s ease;
}

.map-placeholder::before {
  content: "🗺️";
  font-size: 24px;
  margin-right: 8px;
}

.map-placeholder:hover {
  border-color: var(--primary-color);
  color: var(--text-secondary);
  background-color: rgba(22, 119, 255, 0.05);
}

.gantt-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
}

.gantt-chart {
  height: 500px;
}

/* 工人筛选区域 */
.filter-worker {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 10px;
}

/* 课表样式 */
.schedule-table-container {
  width: 100%;
  overflow: auto;
  max-height: 70vh;
}

.schedule-table-wrapper {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  grid-template-rows: 40px repeat(24, 40px);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  min-width: calc(80px + 7 * 150px);
}

.schedule-header {
  display: contents;
}

.schedule-content {
  display: contents;
}

.time-column-header,
.day-column-header {
  background-color: #f5f7fa;
  padding: 10px;
  text-align: center;
  font-weight: bold;
  border-right: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-column {
  grid-column: 1;
  grid-row: 2 / -1;
  border-right: 1px solid var(--border-color);
}

.day-column {
  grid-row: 2 / -1;
  border-right: 1px solid var(--border-color);
  position: relative;
}

.time-slot-bg {
  height: 40px;
  border-bottom: 1px solid var(--border-color);
}

.time-slot {
  padding: 5px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  box-sizing: border-box;
  transform: translateY(2px); /* 向下移动2px */
}

.task-item {
  position: absolute;
  left: 2px;
  right: 2px;
  background-color: #409EFF;
  color: white;
  border-radius: 4px;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transform: translateY(20px); /* 向下移动20px */
}

.task-content {
  font-size: 12px;
  text-align: center;
  width: 100%;
  padding: 2px;
  box-sizing: border-box;
}

.task-name {
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-device,
.task-time {
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination-controls {
  padding: 10px 0;
  text-align: center;
}

.dialog-footer {
  text-align: right;
}

.gantt-chart {
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.process-brief {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
}

.worker-brief {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  display: flex;
  gap: 16px;
  border: 1px solid var(--border-color);
}

/* 任务管理模块样式 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;


  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.section-actions {
  display: flex;
  gap: 8px;
}

.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.filter-toolbar .el-input,
.filter-toolbar .el-select {
  width: 100%;
}
/* 待分配任务行标红 */
:deep(.warning-row) {
  background-color: #fef0f0 !important;
}

:deep(.warning-row:hover > td) {
  background-color: #fde2e2 !important;
}
.mr8 {
  margin-right: 8px;
}

.text-danger {
  color: var(--error-color);
}

.task-detail {
  padding: 16px 0;
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 100px;
  font-size: 14px;
}

.detail-row .value {
  color: var(--text-primary);
  flex: 1;
  font-size: 14px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  font-size: 16px;
  color: var(--text-primary);
  flex: 1;
  text-align: center;
  margin: 0 8px;
}

.section-title .el-icon {
  font-size: 16px;
  color: var(--primary-color);
  margin-right: 8px;
}

/* 增强的表格和卡片样式 */
:deep(.el-card) {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

:deep(.el-card:hover) {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: auto;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:deep(.el-table th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 2px solid #e2e8f0;
  font-size: 14px;
}

:deep(.el-table tr:hover) {
  background-color: #f8fafc;
}

:deep(.el-table--small .el-table__cell) {
  padding: 8px 12px;
  font-size: 13px;
}

:deep(.el-table__body td) {
  border-bottom: 1px solid var(--border-color);
}

/* 按钮样式现代化 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

:deep(.el-button--primary:hover) {
  background: #66b1ff;
  border-color: #66b1ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

:deep(.el-button--success) {
  background: var(--success-color);
  border: 1px solid var(--success-color);
  color: white;
  box-shadow: 0 2px 4px rgba(103, 194, 58, 0.2);
}

:deep(.el-button--success:hover) {
  background: #85ce61;
  border-color: #85ce61;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

:deep(.el-button.is-text) {
  color: var(--primary-color);
  padding: 4px 8px;
}

:deep(.el-button.is-text:hover) {
  background-color: rgba(64, 158, 255, 0.1);
}

:deep(.el-button--primary.is-plain) {
  background: white;
  border: 1px solid var(--primary-color);
  color: var(--primary-color);
}

:deep(.el-button--primary.is-plain:hover) {
  background: var(--primary-color);
  color: white;
}

/* 数据导入按钮样式 - 蓝色边框按钮 */
.import-btn {
  background: white !important;
  border: 1px solid #409EFF !important;
  color: #409EFF !important;
  font-weight: 500;
}

.import-btn:hover {
  background: #409EFF !important;
  color: white !important;
  border-color: #409EFF !important;
}

/* 保存方案按钮样式 - 绿色按钮 */
.save-btn {
  background: #67C23A !important;
  border: 1px solid #67C23A !important;
  color: white !important;
  font-weight: 500;
}

.save-btn:hover {
  background: #85ce61 !important;
  border-color: #85ce61 !important;
  color: white !important;
}

/* 发布工单按钮样式 - 橙色按钮 */
.publish-btn {
  background: #E6A23C !important;
  border: 1px solid #E6A23C !important;
  color: white !important;
  font-weight: 500;
}

.publish-btn:hover {
  background: #ebb563 !important;
  border-color: #ebb563 !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

.publish-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(230, 162, 60, 0.2);
}

/* 标签状态颜色优化 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  border: none;
  font-size: 12px;
}

:deep(.el-tag--success) {
  background: linear-gradient(135deg, var(--success-color) 0%, #73d13d 100%);
  color: white;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, var(--warning-color) 0%, #ffc53d 100%);
  color: white;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, var(--error-color) 0%, #ff7875 100%);
  color: white;
}

:deep(.el-tag--info) {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: white;
}

/* 输入框和选择器样式 */
:deep(.el-input),
:deep(.el-select) {
  border-radius: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

:deep(.el-select .el-select__wrapper) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

:deep(.el-select .el-select__wrapper:hover) {
  border-color: var(--primary-color);
}

/* 加载状态美化 */
:deep(.el-loading-mask) {
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner .circular) {
  background: linear-gradient(135deg, var(--primary-color) 0%, #4096ff 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 卡片展开收起动画 */
:deep(.el-collapse-transition) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 响应式布局优化 */
@media (max-width: 1400px) {
  .home-container {
    padding: 16px 20px;
  }

  .layout {
    grid-template-columns: 280px 1fr 320px;
    gap: 16px;
  }
}

@media (max-width: 1200px) {
  .home-container {
    padding: 16px;
  }

  .layout {
    grid-template-columns: 1fr;
    gap: 16px;
    height: auto;
  }

  .left,
  .center {
    height: auto;
    min-height: 400px;

  }

  .map-placeholder {
    height: 300px;
  }

  .top-bar {
    height: 56px;
    padding: 0 16px;
  }

  .brand .title {
    font-size: 18px;
  }

  .actions {
    gap: 8px;
  }

  .panel-card {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .home-container {
    padding: 12px;
  }

  .top-bar {
    flex-direction: column;
    height: auto;
    padding: 16px;
    gap: 12px;
    border-radius: 12px;
  }

  .actions {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }

  .brand .title {
    font-size: 16px;
  }

  .layout {
    gap: 12px;
  }

  .panel-header {
    padding: 12px 16px;
  }

  .panel-body {
    padding: 16px;
  }

  .filter-toolbar {
    padding: 12px;
  }

  .map-placeholder {
    height: 250px;
    font-size: 14px;
  }

  /* 移动端优化表格 */
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table__header-wrapper th) {
    padding: 8px 4px;
    font-size: 12px;
  }

  :deep(.el-table__body td) {
    padding: 8px 4px;
    font-size: 12px;
  }

  /* 移动端对话框优化 */
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-row .label {
    min-width: auto;
  }

  .worker-brief {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 8px;
  }

  .top-bar {
    padding: 12px;
  }

  .brand .title {
    font-size: 14px;
  }

  .panel-header {
    padding: 8px 12px;
  }

  .panel-body {
    padding: 12px;
  }

  .filter-toolbar {
    padding: 8px;
  }

  .map-placeholder {
    height: 200px;
    font-size: 12px;
  }

  /* 超小屏幕表格 */
  :deep(.el-table__header-wrapper th) {
    padding: 6px 2px;
    font-size: 11px;
  }

  :deep(.el-table__body td) {
    padding: 6px 2px;
    font-size: 11px;
  }
}

/* 高分辨率屏幕优化 */
@media (min-width: 1600px) {
  .home-container {
    padding: 24px 32px;
  }

  .layout {
    grid-template-columns: 360px 1fr 420px;
    gap: 24px;
  }
}

/* 深色模式支持（可选） */
@media (prefers-color-scheme: white) {
  :root {
    --primary-color: #4096ff;
    --success-color: #73d13d;
    --warning-color: #ffc53d;
    --error-color: #ff7875;
    --bg-color: #141414;
    --card-bg: #1f1f1f;
    --border-color: #303030;
    --text-primary: #ffffff;
    --text-secondary: #d9d9d9;
    --text-muted: #8c8c8c;
  }

  .home-container {
    background: linear-gradient(135deg, #141414 0%, #1f1f1f 100%);
  }
}

/* 打印样式 */
@media print {
  .home-container {
    background: white;
    padding: 0;
  }

  .top-bar,
  .gantt-toolbar,
  .actions {
    display: none;
  }

  .panel-card,
  .map-card,
  .gantt-chart {
    box-shadow: none;
    border: 1px solid #ccc;

  }
}

/* 甘特图按钮样式 - 浅蓝色背景配蓝色文字 */
.gantt-btn {
  background-color: #e6f7ff !important;
  border: 1px solid #91d5ff !important;
  color: #1890ff !important;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.gantt-btn:hover {
  background-color: #bae7ff !important;
  border-color: #69c0ff !important;
  color: #0050b3 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.gantt-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

/* 任务管理布局优化 */
.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.search-input {
  width: 100%;
}

.status-select {
  width: 100%;
}

/* 查看按钮样式 - 蓝色 */
.view-btn {
  color: #1890ff !important;
  font-weight: 500;
  margin-right: 8px;
  transition: all 0.3s ease;
}

.view-btn:hover {
  color: #40a9ff !important;
  background-color: #e6f7ff !important;
  border-radius: 4px;
}

/* 编辑按钮样式 - 绿色实心按钮 */
.edit-btn {
  background-color: #52c41a !important;
  border-color: #52c41a !important;
  color: white !important;
  font-weight: 600;
  transition: all 0.3s ease;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(82, 196, 26, 0.2);
}

.edit-btn:hover {
  background-color: #73d13d !important;
  border-color: #73d13d !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.edit-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(82, 196, 26, 0.2);
}

/* 任务表格优化 */
:deep(.el-table .el-table__row) {
  transition: all 0.3s ease;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f8f9fa;
}

:deep(.el-table .el-table__header-wrapper th) {
  background: #fafbfc;
  color: #606266;
  font-weight: 600;
  border-bottom: 2px solid #e4e7ed;
}

:deep(.el-table .el-table__body-wrapper) {
  border-radius: 0 0 8px 8px;
}

/* 确定按钮样式优化 */
:deep(.el-button--primary) {
  background-color: #409EFF !important;
  border-color: #409EFF !important;
  color: white !important;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

:deep(.el-button--primary:active) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.2);
}

/* 状态标签优化 */
:deep(.el-tag--small) {
  min-width: 60px;
  text-align: center;
  white-space: nowrap;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 1.2;
}

/* 确保状态列有足够空间 */
:deep(.el-table .el-table__cell) {
  padding: 8px 12px;
}

/* 状态列特殊处理 */
:deep(.el-table .el-table__cell:nth-child(3)) {
  min-width: 100px;
  text-align: center;
}

/* 生成调度按钮样式 */
.schedule-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.schedule-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.schedule-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.schedule-btn:hover::before {
  left: 100%;
}

.schedule-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.schedule-btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.stat-section {
  margin-bottom: 20px;
}

.stat-section h4 {
  margin: 0 0 12px 0;
  font-weight: 600;
  color: #303133;
}

.total-hours-info {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
}

.mt16 {
  margin-top: 16px;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 8px 0;
}

.custom-progress {
  flex: 1;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.custom-progress:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.custom-progress :deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #f0f2f5;
  overflow: hidden;
  position: relative;
}

.custom-progress :deep(.el-progress-bar__inner) {
  border-radius: 10px;
  position: relative;
  overflow: hidden;
  animation: progressAnimation 1s ease-out !important;
  /* 从0.5s改为0.3s，进一步加快加载速度 */
  background: var(--progress-bg, linear-gradient(90deg, #67c23a, #b3e19d)) !important;
}

.custom-progress :deep(.el-progress-bar__inner)::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
      transparent,
      rgba(255, 255, 255, 0.3),
      transparent);

}

.custom-progress :deep(.el-progress__text) {
  font-weight: 600;
  font-size: 12px !important;
  color: #555;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
  min-width: 40px;
  text-align: right;
}

@keyframes progressAnimation {
  0% {
    width: 0;
  }

  100% {
    width: var(--progress-width, 0%);
  }
}

@keyframes shimmer {
  0% {
    left: -100%;
    opacity: 0.5;
  }

  50% {
    opacity: 1;
  }

  100% {
    left: 100%;
    opacity: 0.5;
  }
}

.stat-table :deep(.el-table__cell) {
  padding: 8px 0;
}

.stat-icon {
  margin-right: 8px;
  font-size: 18px;
  vertical-align: middle;
}

/* 添加导出按钮样式 */
.table-export-button {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 加载状态样式 */
.schedule-btn.is-loading {
  background: linear-gradient(135deg, #a8a8a8 0%, #888888 100%) !important;
  cursor: not-allowed;
}

.schedule-btn.is-loading:hover {
  transform: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* Icon Font 美化样式 */
/* 注意：需要在HTML头部引入icon font，例如：
<link rel="stylesheet" href="//at.alicdn.com/t/font_xxxxx_xxxxx.css">
或者使用其他icon font库如Font Awesome等
*/

.algorithm-target-selection {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.selection-item {
  flex: 1; /* 三个下拉框等宽 */
  min-width: 0;
}

/* 调度模式切换栏 */
.schedule-mode-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.schedule-mode-bar .mode-label {
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
}

/* 方案历史按钮样式 */
.plan-history-btn {
  background: #909399 !important;
  border: 1px solid #909399 !important;
  color: white !important;
  font-weight: 500;
  border-radius: 8px;
}

.plan-history-btn:hover {
  background: #a6a9ad !important;
  border-color: #a6a9ad !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.3);
}

/* 方案历史中当前生效方案行高亮 */
:deep(.el-table .current-plan-row) {
  background-color: #f0f9eb !important;
}

:deep(.el-table .current-plan-row:hover > td) {
  background-color: #e1f3d8 !important;
}

.iconfont {
  font-size: 18px;
  color: #409EFF;
  transition: all 0.3s ease;
  display: inline-block;
}

/* 面板图标统一样式 */
.panel-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  transition: all 0.3s ease;
  filter: brightness(1) saturate(1);
}

.panel-icon:hover {
  transform: scale(1.1);
  filter: brightness(1.1) saturate(1.2) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}

/* 面板标题悬停效果 */
.panel-title:hover .panel-icon {
  transform: scale(1.1);
  filter: brightness(1.1) saturate(1.2) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}

/* 算法选择图标特殊样式 */
.section-title .panel-icon {
  width: 22px;
  height: 22px;
  margin-right: 8px;
}

.iconfont:active {
  animation: iconPulse 0.3s ease;
}

.gantt-container {
  transform: scale(0.9);
  transform-origin: top left;
  width: 111.11%; /* 100% / 0.9 to maintain the same visual width */
  height:90vh;
}

/* 图标动画效果 */
@keyframes iconPulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }

  100% {
    transform: scale(1);
  }
}

.iconfont:active {
  animation: iconPulse 0.3s ease;
}
.conflict-option {
  color: #f56c6c !important;
}

/* ====== 方案对比对话框样式 ====== */

.comparison-container {
  margin-bottom: 24px;
}

.compare-card {
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  height: 100%;
}

.plan-a-card { border-top: 4px solid #1890ff; }
.plan-b-card { border-top: 4px solid #52c41a; }

.compare-card :deep(.el-card__header) {
  padding: 16px 24px;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.compare-card :deep(.el-card__body) {
  padding: 0;
}

.compare-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compare-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f1f1f;
  margin: 0;
}

/* 核心指标区 */
.core-metrics {
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  border-bottom: 1px dashed #e8e8e8;
}

.metric-label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.metric-value-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.metric-main {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
}

.metric-unit {
  font-size: 14px;
  color: #8c8c8c;
}

/* 色彩对比状态 */
.status-good { color: #52c41a; }
.status-bad { color: #f5222d; }
.status-neutral { color: #1f1f1f; } 

.diff-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  line-height: 1.5;
}
.diff-tag.good { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.diff-tag.bad { background: #fff2f0; color: #f5222d; border: 1px solid #ffa39e; }
.diff-tag.neutral { background: #f5f5f5; color: #8c8c8c; border: 1px solid #d9d9d9; }

/* 次要信息区 */
.secondary-info {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  font-size: 14px;
  color: #595959;
  display: flex;
  align-items: center;
}

.info-label {
  color: #8c8c8c;
  width: 70px;
  flex-shrink: 0;
}


.diff-summary-row {
  margin-top: 8px;
}
.diff-summary-item {
  text-align: center;
  padding: 16px 12px;
  border-radius: 6px;
  color: #fff;
}
.diff-summary-item .diff-num {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.diff-summary-item .diff-label {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.9;
}
.diff-added { background: #67C23A; }
.diff-removed { background: #F56C6C; }
.diff-changed { background: #E6A23C; }
.diff-unchanged { background: #909399; }

.diff-filter-bar {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.diff-eq-name {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}
.diff-proc-name {
  color: #606266;
  font-size: 12px;
  margin-top: 2px;
}
.diff-changes-text {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

:deep(.diff-row-added) {
  background-color: #f0f9eb !important;
}
:deep(.diff-row-removed) {
  background-color: #fef0f0 !important;
}
:deep(.diff-row-changed) {
  background-color: #fdf6ec !important;
}
:deep(.diff-row-unchanged) {
  background-color: #f4f4f5 !important;
}

.current-plan-row {
  background-color: #f0f9eb !important;
}
</style>
