<template>
  <div v-if="visible" class="custom-modal-overlay" @click="close">
    <div class="custom-modal" @click.stop>
      <div class="custom-modal-header">
        <span>{{ worker.name }} 的任务课表</span>
        <button @click="close" class="custom-modal-close">×</button>
      </div>
      <div class="custom-modal-body">
        <div class="schedule-table-container">
          <div class="pagination-controls" style="margin-bottom: 16px; display: flex; justify-content: center; align-items: center;">
            <el-button @click="prevWeek" :disabled="currentWeek <= 1">上一周</el-button>
            <span style="margin: 0 16px;">第 {{ currentWeek }} 周 / 共 {{ totalWeeks }} 周</span>
            <el-button @click="nextWeek" :disabled="currentWeek >= totalWeeks">下一周</el-button>
            <div style="margin-left: 20px;">
              <el-select
                v-model="selectedEquipment"
                placeholder="选择设备"
                clearable
                style="width: 200px; margin-right: 10px;"
                @change="currentWeek = 1"
              >
                <el-option
                  v-for="option in equipmentOptions"
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
            <div class="time-column-header">时间</div>
            <div
              v-for="day in 7"
              :key="day"
              class="day-column-header"
            >
              第{{ day }}天
            </div>

            <div class="time-column">
              <div
                v-for="(time, index) in timeSlots"
                :key="index"
                class="time-slot"
              >
                {{ time }}
              </div>
            </div>

            <div
              v-for="day in 7"
              :key="day"
              class="day-column"
            >
              <div
                v-for="(time, index) in timeSlots"
                :key="index"
                class="time-slot-bg"
              ></div>

              <div
                v-for="task in weeklyData[day]"
                :key="task.processId"
                class="task-item"
                :style="getTaskPositionStyle(task)"
                :title="`${task.task} (${task.startTimeFormatted} - ${getDisplayEndTime(task.endTimeFormatted)})`"
              >
                <div class="task-content">
                  <div class="task-name">{{ task.task }}</div>
                  <div class="task-device">{{ task.equipment || task.device }}</div>
                  <div class="task-time">{{ task.startTimeFormatted.split(' ')[1] }}-{{ getDisplayEndTime(task.endTimeFormatted).split(' ')[1] }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="custom-modal-footer">
        <el-button @click="close">关闭</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  extractDayFromFormattedTime,
  getTimeFromFormattedTime,
  getDisplayEndTimeCalendar,
  getTimeSlotIndex,
  getCalendarTaskPositionStyle
} from '../utils'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  worker: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const currentWeek = ref(1)
const selectedEquipment = ref('')

const timeSlots = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 19; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    slots.push(`${hour.toString().padStart(2, '0')}:30`)
  }
  slots.push('20:00')
  return slots
})

const weeklyData = computed(() => {
  if (!props.worker.tasks) return {}

  const tasksByDay = {}
  const startDay = (currentWeek.value - 1) * 7 + 1
  const endDay = currentWeek.value * 7

  props.worker.tasks.forEach(task => {
    if (selectedEquipment.value && task.equipment !== selectedEquipment.value) {
      return
    }

    const dayMatch = task.start_time.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      if (day >= startDay && day <= endDay) {
        const weekDay = day - startDay + 1
        if (!tasksByDay[weekDay]) {
          tasksByDay[weekDay] = []
        }
        const updatedTask = {
          task: task.task_name,
          equipment: task.equipment,
          startTimeFormatted: task.start_time,
          endTimeFormatted: task.end_time,
          processId: task.task_id
        }
        tasksByDay[weekDay].push(updatedTask)
      }
    }
  })

  return tasksByDay
})

const totalWeeks = computed(() => {
  if (!props.worker.tasks) return 1

  const days = props.worker.tasks.map(task => {
    const dayMatch = task.start_time.match(/第(\d+)天/)
    return dayMatch ? parseInt(dayMatch[1]) : 1
  })
  const maxDay = days.length > 0 ? Math.max(...days) : 0
  return Math.ceil(maxDay / 7) || 1
})

const equipmentOptions = computed(() => {
  if (!props.worker.tasks) return []

  const equipmentSet = new Set()
  props.worker.tasks.forEach(task => {
    if (task.equipment) {
      equipmentSet.add(task.equipment)
    }
  })

  return Array.from(equipmentSet).map(equipment => ({
    label: equipment,
    value: equipment
  }))
})

const prevWeek = () => {
  if (currentWeek.value > 1) {
    currentWeek.value--
  }
}

const nextWeek = () => {
  if (currentWeek.value < totalWeeks.value) {
    currentWeek.value++
  }
}

const goToWeek = (week) => {
  if (week >= 1 && week <= totalWeeks.value) {
    currentWeek.value = week
  }
}

const getDisplayEndTime = (endTimeFormatted) => {
  return getDisplayEndTimeCalendar(endTimeFormatted)
}

const getTaskPositionStyle = (task) => {
  return getCalendarTaskPositionStyle(task)
}

const close = () => {
  emit('close')
}

watch(() => props.visible, (val) => {
  console.log('WorkerCalendar visible changed:', val)
  console.log('Worker object:', props.worker)
  console.log('Worker tasks:', props.worker?.tasks)
  if (val) {
    currentWeek.value = 1
    selectedEquipment.value = ''
  }
})

onMounted(() => {
  console.log('WorkerCalendar component mounted')
})
</script>

<style scoped>
.custom-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.custom-modal {
  background-color: white;
  border-radius: 12px;
  width: 90%;
  max-width: 1200px;
  max-height: 85vh;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.custom-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.custom-modal-header span {
  font-size: 18px;
  font-weight: 600;
}

.custom-modal-close {
  background: none;
  border: none;
  font-size: 28px;
  color: white;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.custom-modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(85vh - 120px);
}

.custom-modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
}

.schedule-table-container {
  width: 100%;
  overflow: auto;
  max-height: calc(85vh - 180px);
}

.schedule-table-wrapper {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  grid-template-rows: 50px repeat(24, 50px);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  min-width: calc(80px + 7 * 150px);
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
  height: 50px;
  border-bottom: 1px solid var(--border-color);
}

.time-slot {
  padding: 5px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50px;
  box-sizing: border-box;
}

.task-item {
  position: absolute;
  left: 2px;
  right: 2px;
  color: white;
  border-radius: 4px;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  margin: 0;
}

.task-content {
  font-size: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 4px;
  box-sizing: border-box;
}

.task-name {
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: black;
  font-size: 12px;
}

.task-device,
.task-time {
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: black;
}

.pagination-controls {
  padding: 10px 0;
  text-align: center;
}

.dialog-footer {
  text-align: right;
}
</style>