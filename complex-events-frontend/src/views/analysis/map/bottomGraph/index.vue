<script setup lang="ts">
import TimeCount from '@/views/analysis/map/bottomGraph/timeCount/TimeCount.vue'
import EventTimeLine from '@/views/analysis/map/bottomGraph/eventTimeLine/EventTimeLine.vue'

defineOptions({ name: 'BottomGraph' })
</script>

<template>
  <el-tabs type="card" class="tabs">
    <el-tab-pane label="复杂事件演化过程可视化" class="story-line" lazy>
      <EventTimeLine />
    </el-tab-pane>
    <el-tab-pane label="时间统计图" class="time-count" lazy>
      <TimeCount />
    </el-tab-pane>
    <!--    <el-tab-pane label="时序网络图">-->
    <!--      <div style="height: 100%">2222222</div>-->
    <!--    </el-tab-pane>-->
  </el-tabs>
</template>

<style scoped lang="scss">
:deep(.el-tabs__item) {
  background-color: white;
  border-top-right-radius: 8px;
  border-top-left-radius: 8px;
  font-weight: bold; // 添加这行来设置字体加粗
  //border: 2px  solid !important; // 使用 !important 确保覆盖
}

:deep(.el-tabs__header) {
  margin: 0;
}

:deep(.el-tabs__content) {
  background-color: white;
  height: 10vh;
}

// tabs 右对齐
:deep(.el-tabs__nav-wrap) {
  display: flex;
  justify-content: flex-end;
}

.tabs {
  height: 100%;
  width: 100%;

  .time-count {
    height: 100%;
    width: auto;
    overflow-x: scroll;
    overflow-y: hidden;
  }

  .story-line {
    height: 100%;
    width: 100%;
    overflow-x: scroll;
    overflow-y: hidden;
  }
}
</style>
