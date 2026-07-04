<template>
  <div class="state">
    <div style="font-weight: bold; font-size: 1.5em">系统状态监控</div>
    <el-button type="primary" @click="restart()">一键重启</el-button>
  </div>
  <div class="dashboard-container">
    <el-row :gutter="10" style="margin: 3vh 0 0 0; width: 100%">
      <!-- 内存信息 -->
      <el-col :span="8">
        <div class="cpu-gpu-container">
          <el-card class="info-card">
            <div class="card-title">内存信息</div>
            <div ref="memoryChartRef" class="chart"></div>
          </el-card>
        </div>
      </el-col>

      <el-col :span="8">
        <div class="cpu-gpu-container">
          <!-- CPU 仪表盘 -->
          <el-card class="info-card">
            <div class="card-title">CPU 信息</div>
            <div ref="cpuChartRef" class="chart"></div>
          </el-card>
        </div>
      </el-col>

      <el-col :span="8">
        <div class="cpu-gpu-container">
          <!-- GPU 仪表盘 -->
          <el-card class="info-card">
            <div class="card-title">GPU 信息</div>
            <div ref="gpuChartRef" class="chart"></div>
          </el-card>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="10" style="margin: 1vh 0 0 0; width: 100%">
      <el-col :span="8">
        <div class="temp-chart-container" style="height: 54vh">
          <el-card>
            <div class="card-title">内存趋势</div>
            <div ref="memoryPercentChartRef" class="chart_fold" style="height: 48vh"></div>
          </el-card>
        </div>
      </el-col>
      <el-col :span="16" style="height: 100%">
        <el-row :gutter="10" style="width: 100%; height: 50%">
          <el-col :span="12">
            <div class="temp-chart-container" style="width: 100%">
              <el-card>
                <div class="temp-chart-container-card-container">
                  <div class="card-title">CPU 使用频率</div>
                  <div ref="cpuTempChartRef" class="chart_fold" />
                </div>
              </el-card>
            </div>
          </el-col>
          <el-col :span="12">
            <!-- CPU / GPU 温度曲线 -->
            <div class="temp-chart-container" style="width: 100%; margin-left: 0.4vw">
              <el-card>
                <div class="temp-chart-container-card-container">
                  <div class="card-title">GPU 温度趋势</div>
                  <div ref="gpuTempChartRef" class="chart_fold"></div>
                </div>
              </el-card>
            </div>
          </el-col>
        </el-row>

        <el-row style="height: 50%; overflow-y: auto; margin-top: 2.5vh; width: 100%">
          <el-card
            style="
              height: 100%;
              width: 100%;
              margin-top: 1em;
              padding-top: 1em;
              padding-left: 1em;
              padding-bottom: 2%;
            "
          >
            <div class="card-title" style="text-align: center">冷热数据存储</div>
            <div style="display: flex">
              <!-- MongoDB 未抽取 -->
              <el-card shadow="hover" class="el-card-database">
                <div class="statistic-card-container">
                  <div class="text-num">
                    {{ `${data.MongoDBUnExtract}/${data.MongoDBExtract}` }}
                  </div>
                  <div class="box-t">
                    <img :src="MongoDB" alt="MongoDB Logo" class="img-icon" />
                    <span class="text-title">MongoDB</span>
                  </div>
                </div>
              </el-card>

              <!-- redis -->
              <el-card shadow="hover" class="el-card-database">
                <div class="statistic-card-container">
                  <div class="text-num">
                    {{ data.redis }}
                  </div>
                  <div class="box-t">
                    <img :src="Redis" alt="Redis Logo" class="img-icon" />
                    <span class="text-title">Redis</span>
                  </div>
                </div>
              </el-card>

              <!-- MySql -->
              <el-card shadow="hover" class="el-card-database">
                <div class="statistic-card-container">
                  <div class="text-num">
                    {{ data.Users }}
                  </div>
                  <div class="box-t">
                    <img :src="MySql" alt="MySql Logo" class="img-icon" />
                    <span class="text-title">MySql</span>
                  </div>
                </div>
              </el-card>

              <!-- ChromaDB -->
              <el-card shadow="hover" class="el-card-database">
                <div class="statistic-card-container">
                  <div class="text-num">
                    {{ data.ChromaDB }}
                  </div>
                  <div class="box-t">
                    <img :src="ChromaDB" alt="ChromaDB Logo" class="img-icon" />
                    <span class="text-title">ChromaDB</span>
                  </div>
                </div>
              </el-card>

              <!-- Neo4j -->
              <el-card shadow="hover" class="el-card-database">
                <div class="statistic-card-container">
                  <div class="text-num">
                    {{ data.neo4j_count }}
                  </div>
                  <div class="box-t">
                    <img :src="Neo4j" alt="Neo4j Logo" class="img-icon" />
                    <span class="text-title">Neo4j</span>
                  </div>
                </div>
              </el-card>
            </div>
          </el-card>
        </el-row>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getPerformanceData } from '@/views/sys/sys'
import type { PerformanceData } from '@/views/sys/sys'
import systemApi from '@/api/systemApi'
import MongoDB from '@/icons/ico/MongoDB.ico'
import Redis from '@/icons/ico/redis.ico'
import Neo4j from '@/icons/ico/neoj.ico'
import MySql from '@/icons/ico/mysql.ico'
import ChromaDB from '@/icons/ico/ChromaDB.png'
import { io } from 'socket.io-client'
defineOptions({ name: 'MenuBar' })

function restart() {
  systemApi
    .postRestartSystem()
    .then(() => {
      alert('重启命令已发送，请稍等片刻后重新登录系统！')
    })
    .catch((error) => {
      console.error('重启系统失败:', error)
      alert('重启系统失败，请稍后再试！')
    })
}

// ========================== 性能数据 ==========================
const data = ref<PerformanceData>({
  MongoDBUnExtract: 0,
  MongoDBExtract: 0,
  redis: 1,
  Users: 0,
  ChromaDB: 0,
  cpu_freq: 0,
  cpu_usage: 0,
  gpu_temp: 0,
  gpu_usage: 0,
  neo4j_count: 0,
  memory_usage: 0,
  memory_percent: [],
})

let timer: number | null = null
// 创建SocketIO连接
const socket = io(import.meta.env.VITE_APP_BASE_API)

async function fetch() {
  try {
    // 发送请求
    socket.emit('get_performance_data')

    socket.on('success', function (response) {
      const res = response.data
      data.value = res
      updateTempCharts(res.cpu_freq, res.gpu_temp)
    })
    socket.on('error', function (error) {
      console.error(error)
    })
  } catch (e) {
    console.error('获取性能数据失败:', e)
  }
}

// ========================== ECharts 初始化 ==========================
const cpuChartRef = ref<HTMLDivElement | null>(null)
const gpuChartRef = ref<HTMLDivElement | null>(null)
const memoryChartRef = ref<HTMLDivElement | null>(null)
const cpuTempChartRef = ref<HTMLDivElement | null>(null)
const gpuTempChartRef = ref<HTMLDivElement | null>(null)
const memoryPercentChartRef = ref<HTMLDivElement | null>(null)

let memoryPercentChart: echarts.ECharts | null = null
let cpuChart: echarts.ECharts | null = null
let gpuChart: echarts.ECharts | null = null
let memoryChart: echarts.ECharts | null = null
let cpuTempChart: echarts.ECharts | null = null
let gpuTempChart: echarts.ECharts | null = null

// --- 仪表盘配置 ---
function createGaugeOption(value: number, label: string) {
  return {
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        progress: { show: true, width: 15 },
        axisLine: {
          lineStyle: {
            width: 15,
            color: [
              [0.3, '#67e0e3'],
              [0.7, '#37a2da'],
              [1, '#fd666d'],
            ],
          },
        },
        detail: {
          valueAnimation: true,
          fontSize: 18,
          offsetCenter: [0, '70%'],
          formatter: (v: number) => `${v.toFixed(1)}%`,
        },
        title: { offsetCenter: [0, '90%'], text: label },
        data: [{ value }],
      },
    ],
  }
}

// --- 折线温度图配置 ---
function createLineOption(dates: string[], values: number[], label: string, index: number = 0) {
  const unit = index == 0 ? 'GHz' : '℃'
  const yAxisCommonOpts = {
    type: 'value',
    axisLabel: {
      formatter: '{value} ' + unit,
    },
  }
  return {
    tooltip: {
      trigger: 'axis',
      formatter: function (params: any) {
        // params 是一个数组，如果只有一条线，取 params[0]
        const data = params[0]
        return `${data.seriesName}: ${data.value} ${unit}`
      },
    },
    grid: { left: '0%', right: '0%', top: '10%', bottom: '10%' },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis:
      index == 0
        ? {
            min: 0.5,
            max: 4,
            interval: 0.5,
            ...yAxisCommonOpts,
          }
        : {
            interval: 5,
            min: 30,
            max: 60,
            ...yAxisCommonOpts,
          },
    visualMap: {
      show: false,
      type: 'continuous',
      min: 0,
      max: 100,
      seriesIndex: 0,
    },
    series: [
      {
        name: label,
        type: 'line',
        showSymbol: false,
        data: values,
        lineStyle: { width: 2, color: index == 0 ? '#37a2da' : '#fd666d' },
        areaStyle: {
          color:
            index == 0
              ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#37a2da' },
                  { offset: 1, color: '#ffffff' },
                ])
              : new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#fd666d' },
                  { offset: 1, color: '#ffffff' },
                ]),
        },
      },
    ],
  }
}

//内存扇形图
function createMemoryPieOption(data: { memory_percent: number; name: string }[]) {
  return {
    title: {
      text: '',
      left: 'center',
      top: 5,
      textStyle: { fontSize: 16 },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} %',
    },
    legend: {
      bottom: 0,
      left: 'center',
      type: 'scroll',
      textStyle: { fontSize: 12 },
    },
    series: [
      {
        name: 'Memory Usage',
        type: 'pie',
        radius: [50, 150],
        center: ['50%', '50%'],
        roseType: 'area',
        itemStyle: { borderRadius: 5 },
        data: data.map((item) => ({ value: item.memory_percent, name: item.name })),
      },
    ],
  }
}

// --- 存储温度历史 ---
const cpuTempHistory = ref<{ time: string; value: number }[]>([])
const gpuTempHistory = ref<{ time: string; value: number }[]>([])

function updateTempCharts(cpuTemp: number, gpuTemp: number) {
  const now = new Date().toLocaleTimeString().split(':').slice(0, 3).join(':')
  cpuTempHistory.value.push({ time: now, value: cpuTemp })
  gpuTempHistory.value.push({ time: now, value: gpuTemp })

  if (cpuTempHistory.value.length > 20) cpuTempHistory.value.shift()
  if (gpuTempHistory.value.length > 20) gpuTempHistory.value.shift()

  const cpuDates = cpuTempHistory.value.map((i) => i.time)
  const gpuDates = gpuTempHistory.value.map((i) => i.time)
  const cpuValues = cpuTempHistory.value.map((i) => i.value)
  const gpuValues = gpuTempHistory.value.map((i) => i.value)

  cpuTempChart?.setOption(createLineOption(cpuDates, cpuValues, 'CPU 频率', 0))
  gpuTempChart?.setOption(createLineOption(gpuDates, gpuValues, 'GPU 温度', 1))
}

// --- 生命周期 ---
onMounted(() => {
  fetch()
  timer = window.setInterval(fetch, 3000)

  // 初始化仪表盘
  cpuChart = echarts.init(cpuChartRef.value!)
  gpuChart = echarts.init(gpuChartRef.value!)
  memoryChart = echarts.init(memoryChartRef.value!)
  memoryPercentChart = echarts.init(memoryPercentChartRef.value!)
  cpuChart.setOption(createGaugeOption(0, 'CPU 使用率'))
  gpuChart.setOption(createGaugeOption(0, 'GPU 使用率'))
  memoryChart.setOption(createGaugeOption(0, '内存使用率'))
  memoryPercentChart.setOption(createMemoryPieOption([]))
  // 初始化温度折线图
  cpuTempChart = echarts.init(cpuTempChartRef.value!)
  gpuTempChart = echarts.init(gpuTempChartRef.value!)
  cpuTempChart.setOption(createLineOption([], [], 'CPU 温度'))
  gpuTempChart.setOption(createLineOption([], [], 'GPU 温度'))
  window.addEventListener('resize', () => {
    cpuChart?.resize()
    gpuChart?.resize()
    memoryChart?.resize()
    cpuTempChart?.resize()
    gpuTempChart?.resize()
    memoryPercentChart?.resize()
  })
})

watch(
  () => [data.value.cpu_usage, data.value.gpu_usage, data.value.memory_usage],
  ([cpuUsage, gpuUsage, memoryUsage]) => {
    cpuChart?.setOption({ series: [{ data: [{ value: cpuUsage }] }] })
    gpuChart?.setOption({ series: [{ data: [{ value: gpuUsage }] }] })
    memoryChart?.setOption({ series: [{ data: [{ value: memoryUsage }] }] })
    memoryPercentChart?.setOption(
      createMemoryPieOption(
        data.value.memory_percent as { memory_percent: number; name: string }[],
      ),
    )
  },
)

onUnmounted(() => {
  if (timer) clearInterval(timer)
  cpuChart?.dispose()
  gpuChart?.dispose()
  memoryChart?.dispose()
  memoryPercentChart?.dispose()
  cpuTempChart?.dispose()
  gpuTempChart?.dispose()
  socket.close()
})
</script>

<style scoped lang="scss">
.text-title {
  font-size: 1.2em;
  color: #555;
}

.box-t {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 8%;
}

.text-num {
  font-weight: bold;
  font-size: 2.5em;
  color: #409eff;
  // margin-top: 0.4em;
}

.img-icon {
  width: 2vh;
  height: 2vh;
  margin-right: 0.3em;
}

.state {
  display: flex;
  position: absolute;
  margin-top: -1vh;
  width: 100%;
  height: 3em;
  background: linear-gradient(to right, #1776ff 1%, #6dabff 1%, #ffffff 100%);

  top: 70px;
  justify-content: space-between;
  padding: 5px 20px;
  color: white;
}

.dashboard-container {
  padding: 20px;
  text-align: center;
  background-color: #f8f5f5;
}

.el-card-database {
  width: 15vw;
  height: 14vh;
  margin-top: 1.5vh;
  margin-right: 1vw;
  // padding-bottom: 2%;
  display: flex;
  /* 开启弹性布局 */
  justify-content: bottom;
  /* 水平居中 */
  align-items: center;

  /* 垂直居中 */
  .statistic-card-container {
    align-items: center;
    height: 100%;
    justify-content: center;
    display: flex;
    flex-flow: column;
  }
}

.dataCol {
  margin: 0px;
}

.card-title {
  font-weight: bold;
  font-size: 18px;
  // margin-bottom: 10px;
  color: #333;
}

.card-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60px;
}

.chart {
  width: 100%;
  height: 250px;
}

.chart_fold {
  width: 95%;
  height: 24vh;
  margin: 0px;
  padding: 0px;
}

.cpu-gpu-container {
  /* overflow: hidden; */
  /* display: flex; */
  /* justify-content: space-between; */
  /* align-items: center; */
  :deep(.el-card__body) {
    border-bottom: #f5f7fa solid 10px;
  }
}

.info-card {
  text-align: center;
  width: 100%;
  overflow: hidden;
}

.temp-chart-container {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  height: 100%;

  &-card-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-flow: column;
    justify-content: center;
    align-items: center;
    padding: calc(1%) calc(1%) calc(1%) calc(1%);
  }
}

.temp-chart-container .el-card {
  width: 100%;
}

:deep(.el-card__body) {
  padding: 0;
  overflow: hidden;
}
</style>
