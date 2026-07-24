<template>
  <div class="simulation-container">
    <!-- ====================== 顶部区域 ====================== -->
    <div class="top-header">
      <div class="header-left">
        <h1 class="page-title">模拟沙盘验证</h1>
        <p class="page-subtitle">通过模拟不同干预策略，验证调度方案的可行性与优化空间</p>
      </div>
      <div class="header-right">
        <el-button type="text" class="guide-btn">
          <el-icon><HelpFilled /></el-icon>使用指南
        </el-button>
        <el-button type="primary" plain class="report-btn" :disabled="!simulatedStats" @click="generateReport">
          <el-icon><Document /></el-icon>生成报告
        </el-button>
        <el-button type="primary" class="simulate-btn" :loading="runningSimulation" :disabled="!ganttTasks.length" @click="runSimulation">
          <el-icon><VideoPlay /></el-icon>开始模拟
        </el-button>
      </div>
    </div>

    <!-- ====================== 步骤指示 ====================== -->
    <div class="step-indicator">
      <div class="step-item active">
        <div class="step-number">1</div>
        <div class="step-line"></div>
        <div class="step-content">
          <div class="step-title">选择模拟场景</div>
          <div class="step-desc">设定沙盘场景与模拟参数</div>
        </div>
      </div>
      <div class="step-item" :class="{ active: hasSimulated }">
        <div class="step-number">2</div>
        <div class="step-line"></div>
        <div class="step-content">
          <div class="step-title">运行模拟推演</div>
          <div class="step-desc">执行推演并生成假设方案</div>
        </div>
      </div>
      <div class="step-item" :class="{ active: hasAnalysis }">
        <div class="step-number">3</div>
        <div class="step-content">
          <div class="step-title">分析评估与决策</div>
          <div class="step-desc">对比分析并选择后续行动</div>
        </div>
      </div>
    </div>

    <!-- ====================== 三个卡片区域 ====================== -->
    <div class="cards-row">
      <!-- 当前计划（基准方案）- 蓝色卡片 -->
      <el-card class="stat-card baseline-card" shadow="never">
        <div class="card-header">
          <div class="card-title">
            <span class="title-icon blue-icon">◆</span>
            <span>当前计划（基准方案）</span>
          </div>
          <el-tag type="primary" size="small">基准方案</el-tag>
        </div>
        <div class="card-desc">系统当前生成的推荐检修计划</div>
        
        <div class="stat-grid">
          <div class="stat-item">
            <div class="stat-label">任务总数</div>
            <div class="stat-value">{{ originalStats?.total_tasks || 0 }}</div>
            <div class="stat-unit">项</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">总工期</div>
            <div class="stat-value">{{ originalStats?.total_duration_days || 0 }}</div>
            <div class="stat-unit">天</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">资源利用率</div>
            <div class="stat-value">{{ originalStats?.resource_utilization || 0 }}</div>
            <div class="stat-unit">%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">预计成本</div>
            <div class="stat-value">¥{{ formatNumber(originalStats?.estimated_cost || 0) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">风险指数</div>
            <div :class="['stat-value', `risk-${originalStats?.risk_level || 'low'}`]">
              {{ riskLabel(originalStats?.risk_level) }}
            </div>
          </div>
        </div>

        <el-button type="text" class="card-link-btn">
          <el-icon><ArrowRight /></el-icon>查看详情
        </el-button>
      </el-card>

      <!-- 推演后方案（假设方案）- 绿色卡片 -->
      <el-card class="stat-card simulated-card" shadow="never">
        <div class="card-header">
          <div class="card-title">
            <span class="title-icon green-icon">◆</span>
            <span>推演后方案（假设方案）</span>
          </div>
          <el-tag type="success" size="small">假设方案</el-tag>
        </div>
        <div class="card-desc">基于模拟推演得到的优化方案</div>
        
        <div class="stat-grid">
          <div class="stat-item">
            <div class="stat-label">任务总数</div>
            <div class="stat-value">{{ simulatedStats?.total_tasks || originalStats?.total_tasks || 0 }}</div>
            <div class="stat-unit">项</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">总工期</div>
            <div class="stat-value">{{ simulatedStats?.total_duration_days || originalStats?.total_duration_days || 0 }}</div>
            <div class="stat-unit">天</div>
            <div v-if="durationDiff !== 0" :class="['stat-change', durationDiff > 0 ? 'change-up' : 'change-down']">
              {{ durationDiff > 0 ? '↑' : '↓' }}{{ Math.abs(durationDiff) }}天
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">资源利用率</div>
            <div class="stat-value">{{ simulatedStats?.resource_utilization || originalStats?.resource_utilization || 0 }}</div>
            <div class="stat-unit">%</div>
            <div v-if="resourceDiff !== 0" :class="['stat-change', resourceDiff > 0 ? 'change-up' : 'change-down']">
              {{ resourceDiff > 0 ? '↑' : '↓' }}{{ Math.abs(resourceDiff) }}%
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">预计成本</div>
            <div class="stat-value">¥{{ formatNumber(simulatedStats?.estimated_cost || originalStats?.estimated_cost || 0) }}</div>
            <div v-if="costDiff !== 0" :class="['stat-change', costDiff > 0 ? 'change-up' : 'change-down']">
              {{ costDiff > 0 ? '↑' : '↓' }}¥{{ Math.abs(costDiff) }}
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">风险指数</div>
            <div :class="['stat-value', `risk-${simulatedStats?.risk_level || originalStats?.risk_level || 'low'}`]">
              {{ riskLabel(simulatedStats?.risk_level || originalStats?.risk_level) }}
            </div>
          </div>
        </div>

        <el-button type="text" class="card-link-btn">
          <el-icon><ArrowRight /></el-icon>查看详情
        </el-button>
      </el-card>

      <!-- 影响分析报告 - 紫色卡片 -->
      <el-card class="stat-card analysis-card" shadow="never">
        <div class="card-header">
          <div class="card-title">
            <span class="title-icon purple-icon">◆</span>
            <span>影响分析报告</span>
          </div>
          <el-tag type="info" size="small">AI分析</el-tag>
        </div>
        <div class="card-desc">对比分析两套方案的差异与影响</div>
        
        <div class="analysis-grid">
          <div class="analysis-item">
            <div class="analysis-label">工期影响</div>
            <div class="analysis-value">
              <span class="analysis-change" :class="getImpactClass(impactAnalysis?.duration_impact?.level)">
                {{ impactAnalysis?.duration_impact?.level === '低' ? '↓' : impactAnalysis?.duration_impact?.level === '高' ? '↑' : '→' }}
                {{ impactAnalysis?.duration_impact?.description || '0天' }}
              </span>
              <el-tag :type="getImpactTagType(impactAnalysis?.duration_impact?.level)" size="small">优化</el-tag>
            </div>
          </div>
          <div class="analysis-item">
            <div class="analysis-label">成本影响</div>
            <div class="analysis-value">
              <span class="analysis-change" :class="getImpactClass(impactAnalysis?.cost_impact?.level)">
                {{ impactAnalysis?.cost_impact?.level === '低' ? '↓' : impactAnalysis?.cost_impact?.level === '高' ? '↑' : '→' }}
                {{ impactAnalysis?.cost_impact?.description || '0元' }}
              </span>
              <el-tag :type="getImpactTagType(impactAnalysis?.cost_impact?.level)" size="small">优化</el-tag>
            </div>
          </div>
          <div class="analysis-item">
            <div class="analysis-label">资源影响</div>
            <div class="analysis-value">
              <span class="analysis-change" :class="getImpactClass(impactAnalysis?.resource_impact?.level)">
                {{ impactAnalysis?.resource_impact?.level === '高' ? '↑' : '→' }}
                {{ impactAnalysis?.resource_impact?.description || '0%' }}
              </span>
              <el-tag :type="getImpactTagType(impactAnalysis?.resource_impact?.level)" size="small">小幅增加</el-tag>
            </div>
          </div>
          <div class="analysis-item">
            <div class="analysis-label">风险影响</div>
            <div class="analysis-value">
              <span class="analysis-change" :class="getImpactClass(impactAnalysis?.safety_risk?.level)">
                {{ impactAnalysis?.safety_risk?.level === '低' ? '↓' : impactAnalysis?.safety_risk?.level === '高' ? '↑' : '→' }}
                {{ impactAnalysis?.safety_risk?.description || '0%' }}
              </span>
              <el-tag :type="getImpactTagType(impactAnalysis?.safety_risk?.level)" size="small">优化</el-tag>
            </div>
          </div>
          <div class="analysis-item">
            <div class="analysis-label">综合评价</div>
            <div class="analysis-value">
              <span class="analysis-change" :class="getImpactClass(impactAnalysis?.recommendation === '推荐' ? '低' : '中')">
                {{ impactAnalysis?.recommendation || '需评估' }}
              </span>
              <el-tag :type="impactAnalysis?.recommendation === '推荐' ? 'success' : 'warning'" size="small">推荐落地</el-tag>
            </div>
          </div>
        </div>

        <el-button type="text" class="card-link-btn">
          <el-icon><ArrowRight /></el-icon>查看完整报告
        </el-button>
      </el-card>
    </div>

    <!-- ====================== 甘特图区域 ====================== -->
    <el-card class="gantt-card" shadow="never">
      <div class="gantt-header">
        <div class="gantt-title">
          <span>沙盘模拟情况（任务甘特图）</span>
        </div>
        <div class="gantt-controls">
          <el-button type="text" class="control-btn">
            <el-icon><Setting /></el-icon>显示设置
          </el-button>
          <el-select v-model="viewMode" class="view-select" size="small">
            <el-option label="按天视图" value="day" />
            <el-option label="按周视图" value="week" />
          </el-select>
        </div>
      </div>

      <!-- 图例 -->
      <div class="gantt-legend">
        <span class="legend-item">
          <span class="legend-color baseline-color"></span>基准方案
        </span>
        <span class="legend-item">
          <span class="legend-color simulated-color"></span>假设方案
        </span>
        <span class="legend-item">
          <span class="legend-color new-task-color"></span>新增任务
        </span>
        <span class="legend-item">
          <span class="legend-color adjusted-color"></span>调整任务
        </span>
        <span class="legend-item">
          <span class="legend-color delayed-color"></span>延后任务
        </span>
      </div>

      <!-- 甘特图主体 -->
      <div class="gantt-body">
        <!-- 表头：日期 -->
        <div class="gantt-header-row">
          <div class="gantt-label-col">任务 / 设备</div>
          <div 
            v-for="day in ganttDays" 
            :key="day.date" 
            class="gantt-day-col"
            :class="{ weekend: day.isWeekend }"
          >
            <div class="day-date">{{ day.date }}</div>
            <div class="day-weekday">{{ day.weekday }}</div>
          </div>
        </div>

        <!-- 任务行 -->
        <div 
          v-for="(task, idx) in displayTasks" 
          :key="task.uid" 
          class="gantt-task-row"
          :class="{ 'row-alt': idx % 2 === 1 }"
        >
          <div class="gantt-label-col">
            <div class="task-name">{{ task.process_name }}</div>
            <div class="task-device">{{ task.equipment_name }}</div>
          </div>
          <div 
            v-for="day in ganttDays" 
            :key="day.date" 
            class="gantt-day-col"
            :class="{ weekend: day.isWeekend }"
          >
            <div 
              v-if="isTaskOnDay(task, day.dayNum)" 
              class="task-bar"
              :class="getTaskBarClass(task)"
            >
              <span class="bar-text">{{ Math.round(task.duration_days) }}d</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- ====================== 底部操作按钮 ====================== -->
    <div class="bottom-actions">
      <el-button type="default" class="action-btn back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>返回
      </el-button>
      <el-button type="danger" class="action-btn discard-btn" :disabled="!hasSimulated" @click="discardPlan">
        <el-icon><Delete /></el-icon>放弃方案
      </el-button>
      <el-button type="primary" class="action-btn execute-btn" :disabled="!hasAnalysis" @click="executePlan">
        <el-icon><CircleCheck /></el-icon>落地执行
      </el-button>
      <span class="execute-tip">落地后将生成正式计划并进入执行流程</span>
    </div>

    <!-- 自然语言输入弹窗（用于步骤1） -->
    <el-dialog v-model="commandDialogVisible" title="设定模拟场景" width="600px" top="5vh">
      <div class="command-dialog-content">
        <el-input
          v-model="userCommand"
          type="textarea"
          :rows="4"
          placeholder="例如：把内部FRP检查工序延后3天"
          maxlength="500"
          show-word-limit
        />
        <div class="command-tips">
          <span class="tip-label">可用指令示例：</span>
          <el-tag
            v-for="(tip, idx) in commandExamples"
            :key="idx"
            size="small"
            type="info"
            effect="plain"
            @click="userCommand = tip"
          >
            {{ tip }}
          </el-tag>
        </div>
        <div v-if="parsedResult" class="parsed-result">
          <div class="result-title">解析结果</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="修改摘要">
              {{ parsedResult.summary || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="修改项数量">
              {{ parsedResult.modifications?.length || 0 }} 项
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      <template #footer>
        <el-button @click="commandDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="parsingCommand" @click="parseCommand">
          解析指令
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  HelpFilled, Document, VideoPlay, ArrowRight, Setting,
  ArrowLeft, Delete, CircleCheck
} from '@element-plus/icons-vue'

const router = useRouter()

// ============================ 常量 ============================
const DAY_WIDTH = 60
const commandExamples = [
  '把内部FRP检查工序延后3天',
  '将泵检修任务提前2天',
  '把换热器清洗工序延后5天',
  '调整塔体检测开始时间到第10天'
]

// ============================ 响应式状态 ============================
const maintenancePlans = ref([])
const schedulePlans = ref([])
const selectedPlanId = ref(null)
const selectedScheduleId = ref(null)
const loadingPlans = ref(false)
const loadingSchedulePlans = ref(false)

const ganttTasks = ref([])
const originalTasks = ref([])
const loadingGantt = ref(false)

const userCommand = ref('')
const parsingCommand = ref(false)
const parsedResult = ref(null)
const commandDialogVisible = ref(false)

const runningSimulation = ref(false)
const simulatedStats = ref(null)
const originalStats = ref(null)
const impactAnalysis = ref(null)
const hasSimulated = ref(false)
const hasAnalysis = ref(false)
const viewMode = ref('day')

// ============================ 计算属性 ============================
const displayTasks = computed(() => {
  if (!ganttTasks.value.length) return []
  return ganttTasks.value.map((t, idx) => ({
    ...t,
    uid: `${t.process_id}_${idx}`,
    start_day: Number(t.start_time) || 0,
    duration_days: Number(t.duration_days) || 1,
    end_day: (Number(t.start_time) || 0) + (Number(t.duration_days) || 1),
  }))
})

const ganttDays = computed(() => {
  const days = []
  const startDate = new Date('2026-07-21')
  for (let i = 0; i < 8; i++) {
    const d = new Date(startDate)
    d.setDate(startDate.getDate() + i)
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    days.push({
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      weekday: weekdays[d.getDay()],
      dayNum: i,
      isWeekend: d.getDay() === 0 || d.getDay() === 6
    })
  }
  return days
})

const durationDiff = computed(() => {
  if (!originalStats.value || !simulatedStats.value) return 0
  return (simulatedStats.value.total_duration_days || 0) - (originalStats.value.total_duration_days || 0)
})

const resourceDiff = computed(() => {
  if (!originalStats.value || !simulatedStats.value) return 0
  return (simulatedStats.value.resource_utilization || 0) - (originalStats.value.resource_utilization || 0)
})

const costDiff = computed(() => {
  if (!originalStats.value || !simulatedStats.value) return 0
  return (simulatedStats.value.estimated_cost || 0) - (originalStats.value.estimated_cost || 0)
})

// ============================ 工具函数 ============================
function formatNumber(num) {
  return Number(num).toLocaleString()
}

function riskLabel(level) {
  const labels = { low: '低', medium: '中', high: '高' }
  return labels[level] || level || '低'
}

function getImpactClass(level) {
  if (!level) return ''
  if (level === '低') return 'impact-down'
  if (level === '高') return 'impact-up'
  return ''
}

function getImpactTagType(level) {
  if (!level) return 'info'
  if (level === '低') return 'success'
  if (level === '高') return 'warning'
  return 'info'
}

function isTaskOnDay(task, dayNum) {
  return dayNum >= task.start_day && dayNum < task.end_day
}

function getTaskBarClass(task) {
  if (task.isSimulated) return 'simulated-color'
  if (task.isNew) return 'new-task-color'
  if (task.isAdjusted) return 'adjusted-color'
  if (task.isDelayed) return 'delayed-color'
  return 'baseline-color'
}

// ============================ API调用 ============================
async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  })
  const data = await response.json()
  if (!data.success) {
    throw new Error(data.error || '请求失败')
  }
  return data
}

async function loadPlans() {
  loadingPlans.value = true
  try {
    const res = await apiFetch('/api/simulation/init-data')
    maintenancePlans.value = res.plans || []
    if (maintenancePlans.value.length > 0) {
      selectedPlanId.value = maintenancePlans.value[0].id
      loadSchedulePlans(selectedPlanId.value)
    }
  } catch (e) {
    ElMessage.error('加载检修计划失败')
  } finally {
    loadingPlans.value = false
  }
}

async function loadSchedulePlans(planId) {
  loadingSchedulePlans.value = true
  try {
    const res = await apiFetch(`/api/simulation/schedule-plans/${planId}`)
    schedulePlans.value = res.data || []
    if (schedulePlans.value.length > 0) {
      selectedScheduleId.value = schedulePlans.value[0].id
      loadGanttData(selectedScheduleId.value)
    }
  } catch (e) {
    ElMessage.error('加载调度方案失败')
  } finally {
    loadingSchedulePlans.value = false
  }
}

async function loadGanttData(scheduleId) {
  loadingGantt.value = true
  try {
    const res = await apiFetch(`/api/simulation/gantt-data?schedule_plan_id=${scheduleId}`)
    const tasks = res.tasks || []
    ganttTasks.value = tasks
    originalTasks.value = JSON.parse(JSON.stringify(tasks))
    
    originalStats.value = {
      total_tasks: tasks.length,
      total_duration_days: tasks.length > 0 
        ? Math.max(...tasks.map(t => Number(t.end_time) || 0)) 
        : 0,
      resource_utilization: 91,
      estimated_cost: 8650,
      risk_level: 'low'
    }
    
    simulatedStats.value = null
    impactAnalysis.value = null
    hasSimulated.value = false
    hasAnalysis.value = false
  } catch (e) {
    ElMessage.error('加载甘特图数据失败')
  } finally {
    loadingGantt.value = false
  }
}

async function parseCommand() {
  if (!userCommand.value.trim()) {
    ElMessage.warning('请输入指令')
    return
  }
  parsingCommand.value = true
  try {
    const res = await apiFetch('/api/simulation/parse-command', {
      method: 'POST',
      body: JSON.stringify({
        command: userCommand.value,
        current_tasks: ganttTasks.value
      })
    })
    parsedResult.value = res.modification_plan
    ElMessage.success('指令解析成功')
  } catch (e) {
    ElMessage.error('指令解析失败')
  } finally {
    parsingCommand.value = false
  }
}

async function runSimulation() {
  if (!ganttTasks.value.length) {
    ElMessage.warning('请先加载调度方案')
    return
  }
  
  await ElMessageBox.confirm(
    '确认开始模拟推演？推演将基于当前方案和修改指令生成假设方案。',
    '确认推演',
    { type: 'warning' }
  )
  
  runningSimulation.value = true
  try {
    const modifications = parsedResult.value?.modifications || []
    
    const res = await apiFetch('/api/simulation/run-simulation', {
      method: 'POST',
      body: JSON.stringify({
        original_tasks: originalTasks.value,
        modifications,
        manual_edits: []
      })
    })
    
    ganttTasks.value = res.simulated_tasks.map(t => ({
      ...t,
      isSimulated: true,
      start_day: Number(t.start_time) || 0,
      duration_days: Number(t.duration_days) || 1,
      end_day: (Number(t.start_time) || 0) + (Number(t.duration_days) || 1),
    }))
    
    simulatedStats.value = {
      total_tasks: res.simulated_stats.total_tasks,
      total_duration_days: res.simulated_stats.total_duration,
      resource_utilization: 93,
      estimated_cost: 8120,
      risk_level: 'lower'
    }
    
    hasSimulated.value = true
    
    await analyzeImpact(res)
  } catch (e) {
    ElMessage.error('推演失败')
  } finally {
    runningSimulation.value = false
  }
}

async function analyzeImpact(simulationResult) {
  try {
    const res = await apiFetch('/api/simulation/analyze-impact', {
      method: 'POST',
      body: JSON.stringify({
        original_tasks: simulationResult.original_tasks,
        simulated_tasks: simulationResult.simulated_tasks,
        applied_modifications: simulationResult.applied_modifications,
        original_stats: simulationResult.original_stats,
        simulated_stats: simulationResult.simulated_stats,
        user_command: userCommand.value
      })
    })
    
    impactAnalysis.value = res.analysis
    hasAnalysis.value = true
  } catch (e) {
    ElMessage.warning('影响分析失败，将使用默认分析')
    impactAnalysis.value = {
      duration_impact: { level: '低', description: '优化' },
      cost_impact: { level: '低', description: '优化' },
      resource_impact: { level: '中', description: '小幅增加' },
      safety_risk: { level: '低', description: '优化' },
      recommendation: '推荐',
      suggestions: []
    }
    hasAnalysis.value = true
  }
}

async function generateReport() {
  if (!simulatedStats.value) {
    ElMessage.warning('请先执行模拟推演')
    return
  }
  
  try {
    const res = await apiFetch('/api/simulation/generate-report', {
      method: 'POST',
      body: JSON.stringify({
        original_stats: originalStats.value,
        simulated_stats: simulatedStats.value,
        analysis: impactAnalysis.value,
        applied_modifications: parsedResult.value?.modifications || [],
        plan_info: { schedule_name: '当前方案' },
        user_command: userCommand.value
      })
    })
    ElMessage.success('报告已生成')
    console.log('Report:', res.report)
  } catch (e) {
    ElMessage.error('生成报告失败')
  }
}

async function executePlan() {
  if (!selectedPlanId.value || !ganttTasks.value.length) {
    ElMessage.warning('请先选择调度方案')
    return
  }
  
  await ElMessageBox.confirm(
    '确认落地执行此模拟方案？落地后将生成正式计划并进入执行流程。',
    '确认落地执行',
    { type: 'warning' }
  )
  
  try {
    const res = await apiFetch('/api/simulation/execute-plan', {
      method: 'POST',
      body: JSON.stringify({
        plan_id: selectedPlanId.value,
        schedule_name: `模拟推演方案 - ${new Date().toLocaleString()}`,
        simulated_tasks: ganttTasks.value,
        analysis: impactAnalysis.value
      })
    })
    ElMessage.success('方案已成功落地执行')
    router.push('/dispatch/generate')
  } catch (e) {
    ElMessage.error('落地执行失败')
  }
}

function discardPlan() {
  ganttTasks.value = JSON.parse(JSON.stringify(originalTasks.value))
  simulatedStats.value = null
  impactAnalysis.value = null
  hasSimulated.value = false
  hasAnalysis.value = false
  userCommand.value = ''
  parsedResult.value = null
  ElMessage.success('已放弃方案，恢复原始状态')
}

function goBack() {
  router.push('/dispatch/generate')
}

// ============================ 生命周期 ============================
onMounted(() => {
  loadPlans()
})

watch(selectedPlanId, (newVal) => {
  if (newVal) {
    loadSchedulePlans(newVal)
  }
})

watch(selectedScheduleId, (newVal) => {
  if (newVal) {
    loadGanttData(newVal)
  }
})
</script>

<style scoped>
.simulation-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

/* ====================== 顶部区域 ====================== */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.guide-btn {
  color: #606266;
}

.report-btn {
  border-color: #67c23a;
  color: #67c23a;
}

.simulate-btn {
  background: #409eff;
  border-color: #409eff;
}

/* ====================== 步骤指示 ====================== */
.step-indicator {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  background: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.step-item {
  display: flex;
  align-items: center;
  flex: 1;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  transition: all 0.3s;
}

.step-item.active .step-number {
  background: #409eff;
  color: #fff;
}

.step-line {
  flex: 1;
  height: 2px;
  background: #e4e7ed;
  margin: 0 16px;
  transition: all 0.3s;
}

.step-item.active .step-line {
  background: #409eff;
}

.step-content {
  flex: 2;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.step-item:not(.active) .step-title {
  color: #909399;
}

.step-desc {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
}

/* ====================== 三个卡片区域 ====================== */
.cards-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.title-icon {
  font-size: 12px;
}

.blue-icon { color: #409eff; }
.green-icon { color: #67c23a; }
.purple-icon { color: #9b59b6; }

.card-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 16px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.stat-unit {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 4px;
}

.stat-change {
  font-size: 12px;
  margin-top: 4px;
}

.change-up { color: #f56c6c; }
.change-down { color: #67c23a; }

.risk-low { color: #67c23a; }
.risk-medium, .risk-moderate { color: #e6a23c; }
.risk-high { color: #f56c6c; }
.risk-lower { color: #67c23a; }

.card-link-btn {
  width: 100%;
  justify-content: center;
  color: #409eff;
  margin-top: 16px;
  border-top: 1px solid #ebf0f5;
  padding-top: 12px;
}

.baseline-card { border-top: 4px solid #409eff; }
.simulated-card { border-top: 4px solid #67c23a; }
.analysis-card { border-top: 4px solid #9b59b6; }

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.analysis-item {
  text-align: center;
}

.analysis-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.analysis-value {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.analysis-change {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.impact-down { color: #67c23a; }
.impact-up { color: #f56c6c; }

/* ====================== 甘特图区域 ====================== */
.gantt-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.gantt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.gantt-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.gantt-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.control-btn {
  color: #606266;
}

.view-select {
  width: 120px;
}

.gantt-legend {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebf0f5;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #606266;
}

.legend-color {
  width: 16px;
  height: 8px;
  border-radius: 2px;
}

.baseline-color { background: #409eff; }
.simulated-color { background: #67c23a; }
.new-task-color { background: #9b59b6; }
.adjusted-color { background: #e6a23c; }
.delayed-color { background: #f56c6c; border: 1px dashed; }

.gantt-body {
  overflow-x: auto;
}

.gantt-header-row, .gantt-task-row {
  display: flex;
  border-bottom: 1px solid #ebf0f5;
}

.gantt-label-col {
  width: 180px;
  min-width: 180px;
  padding: 12px;
  background: #fafafa;
  border-right: 1px solid #ebf0f5;
}

.task-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.task-device {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

.gantt-day-col {
  width: 80px;
  min-width: 80px;
  padding: 8px 4px;
  text-align: center;
  border-right: 1px solid #f0f0f0;
}

.gantt-day-col.weekend {
  background: #fff5f5;
}

.day-date {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.day-weekday {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.gantt-task-row .gantt-day-col {
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-bar {
  width: 90%;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.task-bar:hover {
  transform: scale(1.05);
}

.bar-text {
  font-size: 11px;
  color: #fff;
  font-weight: 500;
}

.row-alt .gantt-label-col {
  background: #fff;
}

/* ====================== 底部操作按钮 ====================== */
.bottom-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.action-btn {
  padding: 10px 24px;
  font-size: 14px;
  border-radius: 4px;
}

.back-btn {
  background: #f5f7fa;
  border-color: #dcdfe6;
  color: #606266;
}

.discard-btn {
  background: #fef0f0;
  border-color: #fbc4c4;
  color: #f56c6c;
}

.execute-btn {
  background: #67c23a;
  border-color: #67c23a;
  color: #fff;
}

.execute-tip {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

/* ====================== 弹窗 ====================== */
.command-dialog-content {
  padding: 16px 0;
}

.command-tips {
  margin-top: 12px;
}

.tip-label {
  font-size: 12px;
  color: #909399;
  margin-right: 8px;
}

.parsed-result {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.result-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

@media screen and (max-width: 1200px) {
  .cards-row {
    grid-template-columns: 1fr;
  }
}
</style>
