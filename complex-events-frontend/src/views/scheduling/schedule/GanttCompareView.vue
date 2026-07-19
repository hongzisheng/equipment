<template>
  <div class="gantt-compare-container" v-if="plan1 && plan2">
    <!-- 时间轴标尺 -->
    <div class="gantt-ruler-row">
      <div class="gantt-eq-col">设备 / 工序</div>
      <div class="gantt-bar-area">
        <div
          v-for="(tick, idx) in timeTicks"
          :key="idx"
          class="gantt-tick"
          :style="{ left: tick.percent + '%' }"
        >
          <div class="gantt-tick-line"></div>
          <div class="gantt-tick-label">{{ tick.label }}</div>
        </div>
      </div>
    </div>

    <!-- 方案 A 区域 -->
    <div class="gantt-plan-section">
      <div class="gantt-plan-header gantt-plan-header-a">
        方案 A：{{ plan1.schedule_name }}
        <span class="gantt-plan-meta">{{ overview1.total_tasks }} 任务 / {{ overview1.total_duration_days }} 天</span>
      </div>
      <div
        v-for="row in plan1Rows"
        :key="row.key"
        class="gantt-row"
        :class="{ 'gantt-row-diff': row.isDiff }"
      >
        <div class="gantt-eq-col">
          <div class="gantt-eq-name">{{ row.equipmentName }}</div>
          <div class="gantt-proc-name">{{ row.processName }}</div>
        </div>
        <div class="gantt-bar-area">
          <div
            v-if="row.task"
            class="gantt-bar gantt-bar-a"
            :style="{
              left: row.leftPercent + '%',
              width: row.widthPercent + '%'
            }"
            :title="`${row.task.start_time_formatted} ~ ${row.task.end_time_formatted}`"
          >
            <span class="gantt-bar-text">{{ row.task.duration_days }}天</span>
          </div>
          <div v-else class="gantt-empty">—</div>
        </div>
      </div>
    </div>

    <!-- 方案 B 区域 -->
    <div class="gantt-plan-section">
      <div class="gantt-plan-header gantt-plan-header-b">
        方案 B：{{ plan2.schedule_name }}
        <span class="gantt-plan-meta">{{ overview2.total_tasks }} 任务 / {{ overview2.total_duration_days }} 天</span>
      </div>
      <div
        v-for="row in plan2Rows"
        :key="row.key"
        class="gantt-row"
        :class="{ 'gantt-row-diff': row.isDiff }"
      >
        <div class="gantt-eq-col">
          <div class="gantt-eq-name">{{ row.equipmentName }}</div>
          <div class="gantt-proc-name">{{ row.processName }}</div>
        </div>
        <div class="gantt-bar-area">
          <div
            v-if="row.task"
            class="gantt-bar gantt-bar-b"
            :style="{
              left: row.leftPercent + '%',
              width: row.widthPercent + '%'
            }"
            :title="`${row.task.start_time_formatted} ~ ${row.task.end_time_formatted}`"
          >
            <span class="gantt-bar-text">{{ row.task.duration_days }}天</span>
          </div>
          <div v-else class="gantt-empty">—</div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="gantt-legend">
      <div class="legend-item">
        <span class="legend-bar legend-bar-a"></span>
        <span>方案 A 任务</span>
      </div>
      <div class="legend-item">
        <span class="legend-bar legend-bar-b"></span>
        <span>方案 B 任务</span>
      </div>
      <div class="legend-item">
        <span class="legend-bar legend-bar-diff"></span>
        <span>差异行（黄色背景）</span>
      </div>
      <div class="legend-item">
        <span>时间范围：{{ globalStartFormatted }} ~ {{ globalEndFormatted }}</span>
      </div>
    </div>
  </div>
  <div v-else class="gantt-compare-empty">暂无对比数据</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  plan1: { type: Object, default: null },
  plan2: { type: Object, default: null },
  overview1: { type: Object, default: () => ({}) },
  overview2: { type: Object, default: () => ({}) }
})

// 全局时间范围（取两个方案的最小开始和最大结束）
const globalStart = computed(() => {
  const s1 = props.overview1?.start_time
  const s2 = props.overview2?.start_time
  if (s1 == null && s2 == null) return 0
  if (s1 == null) return s2
  if (s2 == null) return s1
  return Math.min(s1, s2)
})

const globalEnd = computed(() => {
  const e1 = props.overview1?.end_time
  const e2 = props.overview2?.end_time
  if (e1 == null && e2 == null) return 1
  if (e1 == null) return e2
  if (e2 == null) return e1
  return Math.max(e1, e2)
})

const globalSpan = computed(() => {
  const span = globalEnd.value - globalStart.value
  return span > 0 ? span : 1
})

const globalStartFormatted = computed(() => props.overview1?.start_time_formatted || props.overview2?.start_time_formatted || '—')
const globalEndFormatted = computed(() => props.overview1?.end_time_formatted || props.overview2?.end_time_formatted || '—')

// 时间刻度（5等分）
const timeTicks = computed(() => {
  const ticks = []
  const n = 5
  for (let i = 0; i <= n; i++) {
    const t = globalStart.value + (globalSpan.value * i) / n
    const percent = (i * 100) / n
    // 格式化时间：尝试用方案中匹配的任务的 formatted 时间
    let label = ''
    const allTasks = [
      ...(props.plan1?.schedule_tasks || []),
      ...(props.plan2?.schedule_tasks || [])
    ]
    const matched = allTasks.find(t2 => Math.abs((t2.start_time || 0) - t) < globalSpan.value / n / 2)
    if (matched) {
      label = matched.start_time_formatted || ''
    } else {
      // 简易回退：用天数
      label = `T+${((t - globalStart.value)).toFixed(1)}天`
    }
    ticks.push({ percent, label })
  }
  return ticks
})

// 计算指定方案每行的位置信息，并标记差异
function buildPlanRows(plan, otherPlan) {
  const tasks = plan?.schedule_tasks || []
  // 对方的 key 集合，用于判断差异
  const otherKeys = new Set(
    (otherPlan?.schedule_tasks || []).map(t => `${t.equipment_id}|${t.process_id}`)
  )
  // 自己的 key 集合
  const myKeys = new Set(tasks.map(t => `${t.equipment_id}|${t.process_id}`))

  return tasks.map(t => {
    const key = `${t.equipment_id}|${t.process_id}`
    const inOther = otherKeys.has(key)
    // 差异判定：对方没有此任务，或者此任务在对方中存在但时间/工人不同
    let isDiff = false
    if (!inOther) {
      isDiff = true
    } else {
      const otherTask = (otherPlan?.schedule_tasks || []).find(
        t2 => t2.equipment_id === t.equipment_id && t2.process_id === t.process_id
      )
      if (otherTask && (
        otherTask.start_time !== t.start_time ||
        otherTask.end_time !== t.end_time
      )) {
        isDiff = true
      }
    }
    const leftPercent = ((t.start_time - globalStart.value) / globalSpan.value) * 100
    const widthPercent = Math.max(((t.end_time - t.start_time) / globalSpan.value) * 100, 1)
    return {
      key,
      task: t,
      equipmentName: t.equipment_name || t.equipment_id || '—',
      processName: t.process_name || '—',
      leftPercent: Math.max(0, Math.min(100, leftPercent)),
      widthPercent: Math.min(100 - leftPercent, widthPercent),
      isDiff
    }
  })
}

const plan1Rows = computed(() => buildPlanRows(props.plan1, props.plan2))
const plan2Rows = computed(() => buildPlanRows(props.plan2, props.plan1))
</script>

<style scoped>
.gantt-compare-container {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
}

.gantt-ruler-row {
  display: flex;
  height: 36px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  position: relative;
}
.gantt-eq-col {
  width: 200px;
  min-width: 200px;
  padding: 8px 12px;
  font-size: 13px;
  color: #606266;
  font-weight: 600;
  border-right: 1px solid #ebeef5;
  display: flex;
  align-items: center;
}
.gantt-bar-area {
  flex: 1;
  position: relative;
  min-height: 20px;
}

.gantt-tick {
  position: absolute;
  top: 0;
  bottom: 0;
}
.gantt-tick-line {
  width: 1px;
  height: 100%;
  background: #dcdfe6;
  margin-left: -0.5px;
}
.gantt-tick-label {
  position: absolute;
  top: 8px;
  left: 4px;
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
}

.gantt-plan-section {
  border-bottom: 1px solid #ebeef5;
}
.gantt-plan-header {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.gantt-plan-header-a {
  background: #409EFF;
}
.gantt-plan-header-b {
  background: #67C23A;
}
.gantt-plan-meta {
  font-weight: 400;
  font-size: 12px;
  opacity: 0.9;
}

.gantt-row {
  display: flex;
  height: 36px;
  border-bottom: 1px solid #f2f6fc;
  align-items: center;
}
.gantt-row:nth-child(even) {
  background: #fafbfc;
}
.gantt-row-diff {
  background: #fdf6ec !important;
}
.gantt-eq-name {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gantt-proc-name {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gantt-bar {
  position: absolute;
  top: 6px;
  height: 24px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  min-width: 4px;
  overflow: hidden;
}
.gantt-bar-a {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
}
.gantt-bar-b {
  background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
}
.gantt-bar-text {
  white-space: nowrap;
  padding: 0 4px;
}

.gantt-empty {
  width: 100%;
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
}

.gantt-legend {
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  border-top: 1px solid #ebeef5;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legend-bar {
  display: inline-block;
  width: 24px;
  height: 12px;
  border-radius: 2px;
}
.legend-bar-a {
  background: #409EFF;
}
.legend-bar-b {
  background: #67C23A;
}
.legend-bar-diff {
  background: #fdf6ec;
  border: 1px solid #E6A23C;
}

.gantt-compare-empty {
  padding: 40px;
  text-align: center;
  color: #909399;
}
</style>
