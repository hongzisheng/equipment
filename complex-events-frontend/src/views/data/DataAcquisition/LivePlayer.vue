<template>
  <div class="container">
    <el-row :gutter="10">
      <el-col :span="18">
        <el-input
          v-model="hlsUrl"
          placeholder="请输入 HLS 地址，例如：http://1.2.3.4/hls/mystream.m3u8"
        />
      </el-col>
      <el-col :span="6">
        <el-button type="primary" @click="start"> 开始接收流</el-button>
        <el-button type="danger" @click="destroyPlayer"> 停止接收</el-button>
      </el-col>
      
    </el-row>

    <video
      v-show="videoShow"
      ref="videoRef"
      controls
      autoplay
      muted
      width="960"
      height="540"
      style="border: 1px solid #ccc; background: #000; margin-top: 20px"
    />
    <el-text v-show="videoShow">流式数据处理时延≈0.18s</el-text>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import Hls from 'hls.js'
import { ElMessage } from 'element-plus'
import streamingApi from '@/api/streamingApi'

const hlsUrl = ref('http://localhost:8889/hls/mystream.m3u8') // 用户输入的 HLS 地址
const videoRef = ref<HTMLVideoElement | null>(null)
let hlsInstance: Hls | null = null

// 安全销毁当前播放器
function destroyPlayer() {
  videoShow.value = false
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
  if (videoRef.value) {
    videoRef.value.src = ''
    videoRef.value.load() // 重置 video 元素
  }
  streamingApi.stopRecording()
}

const videoShow = ref(false)

// 开始播放
async function start() {
  const url = hlsUrl.value.trim()
  if (!url) {
    ElMessage.error('请输入有效的 HLS 地址')
    return
  }

  // 先销毁旧的播放器
  destroyPlayer()

  videoShow.value = true
  await nextTick()
  const video = videoRef.value
  if (!video) return

  if (Hls.isSupported()) {
    streamingApi.startRecording()
    hlsInstance = new Hls()
    hlsInstance.loadSource(url) // ✅ 传 .value
    hlsInstance.attachMedia(video)
    hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
      video.play().catch((e) => {
        console.warn('Autoplay blocked:', e)
        ElMessage.warning('自动播放被阻止，请手动点击播放')
      })
    })
    hlsInstance.on(Hls.Events.ERROR, (event, data) => {
      console.error('HLS Error:', data)
      streamingApi.stopRecording()

      ElMessage.error('播放失败，请检查地址是否正确')
    })
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari 原生支持
    video.src = url // ✅ 直接赋值字符串
    video.load()
    streamingApi.startRecording()

    video.addEventListener('loadedmetadata', () => {
      video.play().catch((e) => {
        console.warn('Autoplay blocked:', e)
        ElMessage.warning('自动播放被阻止，请手动点击播放')
      })
    })
  } else {
    ElMessage.error('当前浏览器不支持 HLS 播放')
  }
}

// 组件卸载时清理
onUnmounted(() => {
  destroyPlayer()
})
</script>

<style scoped>
.container {
  font-family: Arial, sans-serif;
  text-align: center;
  padding: 20px;
}
</style>
