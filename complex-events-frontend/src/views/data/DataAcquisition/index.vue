<script setup lang="ts">
import DefaultSource from '@/views/data/DataAcquisition/DefaultSource.vue'
import LivePlayer from '@/views/data/DataAcquisition/LivePlayer.vue'

defineOptions({ name: 'DataAcquisition' })
</script>

<template>
  <el-tabs class="tabs">
    <el-tab-pane label="大规模动态数据获取">
      <DefaultSource />
    </el-tab-pane>
    <el-tab-pane label="流式数据处理识别" lazy>
      <LivePlayer />
    </el-tab-pane>
  </el-tabs>
</template>

<style scoped lang="scss">
.tabs{
  padding-left: 1vw;
  padding-right: 1vw;
  height: 100%;
  width: 100%;
}

</style>
