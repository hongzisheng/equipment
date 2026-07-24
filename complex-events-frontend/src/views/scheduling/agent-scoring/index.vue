<template>
  <div class="scoring-container">
    <!-- ====================== 顶部区域 ====================== -->
    <div class="top-header">
      <div class="header-left">
        <h1 class="page-title">多智能体协同评分</h1>
        <p class="page-subtitle">基于多智能体协同评估结果，综合计算当前方案的协同得分</p>
      </div>
      <div class="header-right">
        <el-button type="primary" class="regenerate-btn" :loading="regenerating" @click="handleRegenerate">
          <el-icon><Refresh /></el-icon>重新生成
        </el-button>
      </div>
    </div>

    <!-- ====================== 统计卡片 ====================== -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap blue-icon">
          <el-icon><Calendar /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">预计完成时间</div>
          <div class="stat-value-wrap">
            <span class="stat-value">{{ evaluationData?.summary?.estimated_days || 6 }}</span>
            <span class="stat-unit">天</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap orange-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">检修任务</div>
          <div class="stat-value-wrap">
            <span class="stat-value">{{ evaluationData?.summary?.tasks_count || 28 }}</span>
            <span class="stat-unit">项</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap green-icon">
          <el-icon><Checked /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">方案稳定性</div>
          <div class="stat-value-wrap">
            <span class="stat-value">{{ evaluationData?.summary?.stability || '高' }}</span>
            <span class="stability-tag">高稳定</span>
          </div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap purple-icon">
          <el-icon><DataLine /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">资源利用率</div>
          <div class="stat-value-wrap">
            <span class="stat-value">{{ evaluationData?.summary?.resource_utilization || 91 }}</span>
            <span class="stat-unit">%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ====================== 主内容区域 ====================== -->
    <div class="main-content">
      <!-- 左侧：综合得分 -->
      <el-card class="score-card" shadow="never">
        <div class="card-header">
          <span class="card-title">当前方案综合得分</span>
        </div>
        
        <div class="score-display">
          <div class="score-circle">
            <svg viewBox="0 0 120 120" class="circle-svg">
              <circle
                cx="60"
                cy="60"
                r="50"
                fill="none"
                stroke="#ebf5ff"
                stroke-width="8"
              />
              <circle
                cx="60"
                cy="60"
                r="50"
                fill="none"
                stroke="#409eff"
                stroke-width="8"
                :stroke-dasharray="`${(overallScore / 100) * 314} 314`"
                stroke-linecap="round"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="score-inner">
              <div class="score-number">{{ overallScore }}</div>
              <div class="score-total">/ 100</div>
              <div :class="['score-grade', `grade-${gradeColor}`]">
                {{ evaluationData?.overall_score?.grade || '优秀' }}
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 右侧：权重设置 + 智能体评分 -->
      <el-card class="weights-card" shadow="never">
        <div class="card-header">
          <span class="card-title">评分权重设置</span>
          <el-icon class="card-settings"><Setting /></el-icon>
        </div>
        
        <div class="weights-grid">
          <div class="weight-item">
            <div class="weight-header">
              <div class="weight-icon safety-icon">⚖</div>
              <span class="weight-name">安全权重</span>
            </div>
            <el-slider
              v-model="localWeights.safety"
              :min="0"
              :max="100"
              :disabled="true"
              class="weight-slider"
            />
            <div class="weight-value">{{ localWeights.safety }}%</div>
          </div>
          <div class="weight-item">
            <div class="weight-header">
              <div class="weight-icon cost-icon">💰</div>
              <span class="weight-name">成本权重</span>
            </div>
            <el-slider
              v-model="localWeights.cost"
              :min="0"
              :max="100"
              :disabled="true"
              class="weight-slider"
            />
            <div class="weight-value">{{ localWeights.cost }}%</div>
          </div>
          <div class="weight-item">
            <div class="weight-header">
              <div class="weight-icon duration-icon">⏱</div>
              <span class="weight-name">工期权重</span>
            </div>
            <el-slider
              v-model="localWeights.duration"
              :min="0"
              :max="100"
              :disabled="true"
              class="weight-slider"
            />
            <div class="weight-value">{{ localWeights.duration }}%</div>
          </div>
          <div class="weight-item">
            <div class="weight-header">
              <div class="weight-icon personnel-icon">👤</div>
              <span class="weight-name">人员权重</span>
            </div>
            <el-slider
              v-model="localWeights.personnel"
              :min="0"
              :max="100"
              :disabled="true"
              class="weight-slider"
            />
            <div class="weight-value">{{ localWeights.personnel }}%</div>
          </div>
        </div>

        <div class="weights-tip">权重总和必须为 100%</div>

        <div class="agents-section">
          <div class="section-title">智能体评分贡献</div>
          <div class="agent-list">
            <div v-for="agent in agentScores" :key="agent.id" class="agent-item">
              <div class="agent-header">
                <span :class="['agent-dot', agent.color]" style="background: v-bind(agent.color)"></span>
                <span class="agent-name">{{ agent.name }}</span>
                <span class="agent-score">{{ agent.score }} / {{ agent.max_score }}</span>
              </div>
              <div class="agent-bar-wrap">
                <div 
                  class="agent-bar" 
                  :style="{ width: `${(agent.score / agent.max_score) * 100}%`, background: agent.color }"
                ></div>
              </div>
              <div class="agent-reason">{{ agent.reason }}</div>
              <div v-if="agent.suggestions?.length" class="agent-suggestions">
                <div v-for="(suggestion, idx) in agent.suggestions.slice(0, 2)" :key="idx" class="suggestion-item">
                  <el-icon><CircleCheck /></el-icon>{{ suggestion }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- ====================== 底部操作区 ====================== -->
    <div class="bottom-section">
      <el-button 
        type="primary" 
        size="large" 
        class="regenerate-main-btn"
        :loading="regenerating"
        @click="handleRegenerate"
      >
        <el-icon><Refresh /></el-icon>重新生成方案
      </el-button>
      <div class="regenerate-desc">重新生成将基于相同目标和模型，生成新的调度方案</div>
      
      <div class="confirm-bar">
        <div class="confirm-icon">
          <el-icon><WarningFilled /></el-icon>
        </div>
        <span class="confirm-text">重新生成将覆盖当前方案，是否保存当前方案？</span>
        <el-button type="default" class="confirm-btn discard-btn" @click="discardPlan">
          否，放弃保存
        </el-button>
        <el-button type="primary" class="confirm-btn save-btn" @click="savePlan">
          是，保存方案
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Calendar, Document, Checked, DataLine,
  Setting, CircleCheck, WarningFilled
} from '@element-plus/icons-vue'

const router = useRouter()

const evaluationData = ref(null)
const agentScores = ref([])
const regenerating = ref(false)

const localWeights = ref({
  safety: 40,
  cost: 25,
  duration: 20,
  personnel: 15
})

const overallScore = computed(() => {
  if (!agentScores.value.length) return 86
  return Math.round(agentScores.value.reduce((sum, a) => sum + a.score * a.weight / 100, 0))
})

const gradeColor = computed(() => {
  const score = overallScore.value
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'medium'
  return 'low'
})

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

async function loadEvaluationData() {
  try {
    const res = await apiFetch('/api/evaluation-data')
    evaluationData.value = res.data
    if (res.data?.weights) {
      localWeights.value = { ...res.data.weights }
    }
  } catch (e) {
    ElMessage.error('加载评估数据失败')
  }
}

async function loadAgentScores() {
  try {
    const res = await apiFetch('/api/agent-scores')
    agentScores.value = res.data.agents
  } catch (e) {
    ElMessage.error('加载智能体评分失败')
  }
}

async function handleRegenerate() {
  await ElMessageBox.confirm(
    '确认重新生成方案？重新生成将覆盖当前方案。',
    '确认重新生成',
    { type: 'warning' }
  )
  
  regenerating.value = true
  try {
    const res = await apiFetch('/api/regenerate', {
      method: 'POST',
      body: JSON.stringify({
        plan_id: evaluationData.value?.plan_info?.id
      })
    })
    ElMessage.success(res.message)
    loadEvaluationData()
    loadAgentScores()
  } catch (e) {
    ElMessage.error('重新生成方案失败')
  } finally {
    regenerating.value = false
  }
}

async function savePlan() {
  try {
    const res = await apiFetch('/api/save-plan', {
      method: 'POST',
      body: JSON.stringify({
        schedule_id: evaluationData.value?.schedule_info?.id
      })
    })
    ElMessage.success(res.message)
    await handleRegenerate()
  } catch (e) {
    ElMessage.error('保存方案失败')
  }
}

async function discardPlan() {
  try {
    const res = await apiFetch('/api/discard-plan', {
      method: 'POST',
      body: JSON.stringify({
        schedule_id: evaluationData.value?.schedule_info?.id
      })
    })
    ElMessage.success(res.message)
    await handleRegenerate()
  } catch (e) {
    ElMessage.error('放弃方案失败')
  }
}

onMounted(() => {
  loadEvaluationData()
  loadAgentScores()
})
</script>

<style scoped>
.scoring-container {
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

.regenerate-btn {
  background: #409eff;
  border-color: #409eff;
}

/* ====================== 统计卡片 ====================== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.blue-icon { background: #ecf5ff; color: #409eff; }
.orange-icon { background: #fdf6ec; color: #e6a23c; }
.green-icon { background: #f0f9eb; color: #67c23a; }
.purple-icon { background: #faf5ff; color: #9b59b6; }

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value-wrap {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-unit {
  font-size: 14px;
  color: #909399;
}

.stability-tag {
  font-size: 12px;
  color: #67c23a;
  background: #f0f9eb;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

/* ====================== 主内容区域 ====================== */
.main-content {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 20px;
  margin-bottom: 20px;
}

.score-card, .weights-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebf0f5;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-settings {
  color: #909399;
  font-size: 16px;
}

/* 综合得分 */
.score-display {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
}

.score-circle {
  position: relative;
  width: 200px;
  height: 200px;
}

.circle-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
  color: #303133;
}

.score-total {
  font-size: 16px;
  color: #909399;
}

.score-grade {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.grade-excellent {
  background: #f0f9eb;
  color: #67c23a;
}

.grade-good {
  background: #ecf5ff;
  color: #409eff;
}

.grade-medium {
  background: #fdf6ec;
  color: #e6a23c;
}

.grade-low {
  background: #fef0f0;
  color: #f56c6c;
}

/* 权重设置 */
.weights-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 16px;
}

.weight-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.weight-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.weight-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.weight-name {
  font-size: 13px;
  color: #606266;
}

.weight-slider {
  margin: 8px 0;
}

.weight-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  text-align: right;
}

.weights-tip {
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebf0f5;
}

/* 智能体评分 */
.agents-section {
  margin-top: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.agent-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.agent-name {
  font-size: 13px;
  color: #606266;
}

.agent-score {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.agent-bar-wrap {
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.agent-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.agent-reason {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.agent-suggestions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
}

/* ====================== 底部操作区 ====================== */
.bottom-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.regenerate-main-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  background: #409eff;
  border-color: #409eff;
}

.regenerate-desc {
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 8px;
}

.confirm-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebf0f5;
}

.confirm-icon {
  color: #e6a23c;
  font-size: 16px;
}

.confirm-text {
  font-size: 13px;
  color: #606266;
}

.confirm-btn {
  padding: 8px 20px;
  font-size: 13px;
}

.discard-btn {
  background: #f5f7fa;
  border-color: #dcdfe6;
  color: #606266;
}

.save-btn {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

@media screen and (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .main-content {
    grid-template-columns: 1fr;
  }
  .weights-grid {
    grid-template-columns: 1fr;
  }
}
</style>
