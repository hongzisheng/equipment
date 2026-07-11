<template>
  <div class="process-flow-mini">
    <div class="process-timeline-mini">
      <div
        v-for="(node, index) in sortedProcesses"
        :key="node.id"
        class="timeline-mini-item"
        :class="{
          'current-node': node.id === currentProcessId,
          'completed-node': node.status === 'completed',
          'rejected-node': node.status === 'rejected',
        }"
        @click="$emit('view-node', node)"
      >
        <div class="mini-left">
          <div
            v-if="index < sortedProcesses.length - 1"
            class="mini-line"
            :class="{ 'line-completed': node.status === 'completed' }"
          >
          </div>
          <div class="mini-dot" :class="`dot-${node.status}`">
            <el-icon v-if="node.status === 'completed'" size="10"><Select /></el-icon>
            <span v-else class="dot-index">{{ index + 1 }}</span>
          </div>
        </div>

        <div class="mini-content">
          <div class="mini-title">
            <span>{{ node.process_name }}</span>
            <el-tag v-if="node.is_milestone" size="small" type="warning" class="mini-milestone">里程碑</el-tag>
          </div>
          <div class="mini-status">
            <ProcessStatusTag :status="node.status" />
          </div>
          <div v-if="node.status === 'rejected' && node.approval_comments" class="mini-reject">
            驳回：{{ node.approval_comments }}
          </div>
          <div v-if="node.status === 'on_hold' && node.approval_comments" class="mini-on-hold">
            挂起：{{ node.approval_comments }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Select } from '@element-plus/icons-vue'
import ProcessStatusTag from './ProcessStatusTag.vue'
import { parseTimeToMinutes } from '../utils'

const props = defineProps({
  processes: {
    type: Array,
    default: () => []
  },
  equipmentId: {
    type: String,
    default: ''
  },
  currentProcessId: {
    type: [Number, String],
    default: null
  }
})

defineEmits(['view-node'])

const sortedProcesses = computed(() => {
  return props.processes
    .filter(p => p.equipment_id === props.equipmentId)
    .sort((a, b) => {
      const aTime = parseTimeToMinutes(a.scheduled_start_time)
      const bTime = parseTimeToMinutes(b.scheduled_start_time)
      return aTime - bTime
    })
})
</script>

<style scoped>
.process-flow-mini {
  background: #f8fbfd;
  border-radius: 8px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.process-timeline-mini {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-mini-item {
  display: flex;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  padding: 8px;
  border-radius: 6px;
}

.timeline-mini-item:hover {
  background: #eef2f6;
}

.timeline-mini-item.current-node {
  background: #e3f0fa;
  border: 1px solid #409eff;
}

.timeline-mini-item.completed-node {
  opacity: 0.8;
}

.timeline-mini-item.rejected-node {
  background: #fff5f5;
}

.mini-left {
  position: relative;
  width: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.mini-line {
  position: absolute;
  top: 22px;
  left: 50%;
  width: 1.5px;
  height: calc(100% + 12px);
  background: #cbd5e1;
  transform: translateX(-50%);
}

.mini-line.line-completed {
  background: #2c8e5c;
}

.mini-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
  z-index: 2;
}

.dot-completed {
  background: #2c8e5c;
}

.dot-current,
.dot-in_progress {
  background: #1f7a9c;
}

.dot-pending {
  background: #99aab9;
}

.dot-rejected {
  background: #c96b6b;
}

.dot-on_hold {
  background: #f59e0b;
}

.dot-index {
  font-size: 10px;
}

.mini-content {
  flex: 1;
  margin-left: 8px;
}

.mini-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1c3343;
  margin-bottom: 4px;
}

.mini-milestone {
  font-size: 8px;
  padding: 0 4px;
  height: 16px;
  line-height: 16px;
}

.mini-status {
  margin-bottom: 4px;
}

.mini-reject {
  font-size: 11px;
  color: #c96b6b;
  background: #fff5f5;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-on-hold {
  font-size: 11px;
  color: #d97706;
  background: #fffbeb;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>