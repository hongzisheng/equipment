<template>
  <el-card class="card">
    <label>事件类型统计</label>
    <div v-for="countItem in data">
      <el-row>
        <el-col :span="6">
          <el-tooltip transition="">
            <template #default>
              <div class="single-line-container">
                <span class="adaptive-text">
                  {{ countItem.eventType }} :
                </span>
              </div>
            </template>
            <template #content>
              {{ countItem.eventType }}
            </template>
          </el-tooltip>
        </el-col>
        <el-col :span="2">
          <div class="single-line-container">
            <span class="adaptive-text">{{ countItem.count }} </span>
          </div>
        </el-col>
        <el-col :span="16">
          <div class="bar-col">
            <SingleBar :max-value="maxCount" :value="countItem.count" color="lightskyblue"/>
          </div>
        </el-col>
      </el-row>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import { EVENT_TYPE_JSON_API } from '@/api/statisticApi'
import { onMounted, ref, watch } from 'vue'
import SingleBar from '@/views/analysis/map/infoCard/SingleBar.vue'

interface CountItem {
  eventType: string
  count: number
}

const maxCount = ref(0)
const data = ref<CountItem[]>([])

async function initData() {
  data.value = await d3.json(EVENT_TYPE_JSON_API)
}

function processData() {
  // 获取数据中统计的最大值作为比例尺的100%
  data.value.forEach((item) => {
    maxCount.value = Math.max(maxCount.value, item.count)
  })
}

watch(() => data.value, processData, { deep: true })

onMounted(() => {
  initData()
})
</script>

<style scoped lang="scss">
.card {
  height: 100%;
  border-radius: 16px;
}

.single-line-container {
  display: flex;
  align-items: center;
  height: 100%;

  .adaptive-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: clamp(5px, 1vw, 14px);
    flex: 1;
  }
}

.bar-col {
  width: 100%;
  height: 100%;
}
</style>
