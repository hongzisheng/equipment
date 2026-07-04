<template>
  <el-card class="card">
    <el-text tag="b" size="large" class="title">区域统计</el-text>
    <el-scrollbar class="scrollbar" @end-reached="loadMore" :distance="50" >
      <el-row v-for="place in sortPlace" class="place-row">
        <el-col :span="4">
          <div class="single-line-container">
            <span class="adaptive-text">{{ place }}：</span>
          </div>
        </el-col>
        <el-col :span="2">
          <div class="single-line-container">
            <span class="adaptive-text">{{ sumKey(place) }}</span>
          </div>
        </el-col>
        <el-col :span="18">
          <TimeCount :data="format(place)" hidden-y-axis />
        </el-col>
      </el-row>
      <el-row class="loading-row">
        <div style="width: 100%;display: flex;justify-content: center;align-items: center">
          <span>正在加载更多数据</span>
          <el-icon class="is-loading"><Loading/></el-icon>
        </div>

      </el-row>
    </el-scrollbar>
  </el-card>
</template>

<script setup lang="ts">
import * as d3 from 'd3'
import { EVENT_PLACE_JSON_API } from '@/api/statisticApi'
import { computed, onMounted, ref } from 'vue'
import TimeCount from '@/views/analysis/map/bottomGraph/timeCount/TimeCount.vue'
import { Loading } from '@element-plus/icons-vue'

// 使用 ref 创建响应式数据
const eventPlaceCount = ref({})

const init = async () => {
  eventPlaceCount.value = await d3.json(EVENT_PLACE_JSON_API)
}

const loadMore = async () => {
  // 要多少个请求多少个，请求多5个
  eventPlaceCount.value = await d3.json(
    EVENT_PLACE_JSON_API + `?limit=${Object.keys(eventPlaceCount.value).length+5}`,
  )
}
// 格式化成timeCount组件接受的数据格式
function format(key: string): { _id: string; count: number }[] {
  const values = eventPlaceCount.value[key]
  return Object.keys(values).map((item) => {
    return {
      _id: item,
      count: values[item],
    }
  })
}

// 统计一个地点出现的总次数
function sumKey(key: string): number {
  const values = eventPlaceCount.value[key] || {}
  return Object.keys(values).reduce((acc, cur) => {
    return acc + (values[cur] || 0)
  }, 0)
}

const sortPlace = computed<string[]>(() => {
  const keys = Object.keys(eventPlaceCount.value)
  return keys.sort((a, b) => {
    return sumKey(b) - sumKey(a)
  })
})

onMounted(() => {
  init()
})
</script>

<style scoped lang="scss">
.card {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  .title {
    height: 5%; 
    width: 100%;
  }
  .scrollbar {
    height: 85%;
    width: 100%;
    :deep(.el-scrollbar__view) {
      height: 100%;
      .place-row {
        height: 30%;
        width: 100%;
      }
    }
  }
}

.single-line-container {
  display: flex;
  align-items: center;
  height: 100%;
}

.adaptive-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: clamp(5px, 1vw, 14px);
  flex: 1;
}
</style>
