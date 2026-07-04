<template>
  <div class="container" v-loading.fullscreen.lock="loading" element-loading-text="数据加载中...">
    <OptionBar class="option-bar" />
    <div id="map">
      <Map ref="mapRef" />
    </div>
    <div class="statistic-vis-card">
      <div class="title">
        <span>数据统计分析与可视化</span>
      </div>
      <div class="region-statistic-card">
        <RegionStatisticCard />
      </div>
      <div class="event-type-card">
        <EventTypeStatisticCard />
      </div>
    </div>

    <div class="relation-graph-card" v-if="false">
      <RegionRelationCard />
    </div>
    <div class="events-list-card">
      <EventsListCard />
    </div>
    <div class="bottom-graph">
      <BottomGraph />
    </div>
  </div>
</template>

<script setup lang="ts">
import Map from '@/views/analysis/map/Map.vue'
import OptionBar from '@/views/analysis/map/optionBar/OptionBar.vue'
import EventsListCard from '@/views/analysis/map/infoCard/EventsListCard.vue'
import RegionStatisticCard from '@/views/analysis/map/infoCard/RegionStatisticCard.vue'
import EventTypeStatisticCard from '@/views/analysis/map/infoCard/EventTypeStatisticCard.vue'
import RegionRelationCard from '@/views/analysis/map/infoCard/RegionRelationCard.vue'
import BottomGraph from '@/views/analysis/map/bottomGraph/index.vue'
import { computed, onBeforeMount, onMounted, useTemplateRef } from 'vue'
import { useMapStore } from '@/stores/mapStore'

const mapStore = useMapStore()
const mapRef = useTemplateRef('mapRef')
const loading = computed(() => mapStore.loading)
onMounted(() => {
  if (mapRef.value) {
    mapStore.setMapRef(mapRef.value)
  }
})
onBeforeMount(() => {
  // 默认设置分页
  mapStore.setUnlimitedFlag(false)
  mapStore.filter()
})
</script>

<style lang="scss" scoped>
.container {
  width: 96vw;

  #map {
    position: absolute;
    height: 95vh;
    width: 100vw;
    margin-top: -1vh;
    border-radius: 10px;
    z-index: 100;
  }

  .option-bar {
    position: absolute;
    display: flex;
    align-items: flex-start;
    z-index: 101;
    width: 95vw;
    top: 10vh;
    left: 4vw;
  }
  .statistic-vis-card {
    position: absolute;
    top: 15vh;
    left: 4vw;
    height: 60vh;
    width: 20vw;
    z-index: 101;
    background: rgb(255, 255, 255);
    opacity: 0.98;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    gap: 1vh;
    justify-content: space-between;
    padding: 1%;
    .title {
      width: 100%;
      height: 5%;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 1.3em;
      font-weight: bold;
      color: rgb(44, 44, 44);
    }

    .region-statistic-card {
      position: relative;
      width: 100%;
      height: 45%;
    }

    .event-type-card {
      position: relative;

      height: 45%;
      width: 100%;
    }

    .relation-graph-card {
      position: absolute;
      z-index: 101;
      top: 57vh;
      left: 4vw;
      height: 20vh;
      width: 20vw;
    }
  }

  .events-list-card {
    position: absolute;
    z-index: 101;
    top: 15vh;
    right: 4vw;
    width: 20vw;
    height: 60vh;
  }

  .bottom-graph {
    position: absolute;
    border-radius: 10px;
    z-index: 101;
    bottom: 0;
    height: 20vh;
    width: 100vw;
    // 添加一个阴影
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}
</style>
