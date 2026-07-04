<script setup lang="ts">
import ListViewCard from '@/views/analysis/association/listView/index.vue'
import EventsListCard from '@/views/analysis/map/infoCard/EventsListCard.vue'
import { computed, onMounted, ref } from 'vue'
import GMap from '@/views/analysis/association/gMap/GMap.vue'
import { useMapStore } from '@/stores/mapStore'

const selectedTab = ref('List View')
const mapStore = useMapStore()
onMounted(async () => {
  mapStore.setUnlimitedFlag(true)
  await mapStore.filter()
})
</script>

<template>
  <el-row class="main-row">
    <el-col :span="8" class="first-col">
      <div class="events-table">
        <EventsListCard pagination-hidden />
      </div>
    </el-col>
    <el-col :span="16" class="second-col">
      <el-tabs v-model="selectedTab" class="tabs">
        <el-tab-pane label="List View" name="List View" class="list-view" lazy>
          <ListViewCard />
        </el-tab-pane>
        <el-tab-pane label="GMap" class="map-card-row" lazy>
          <GMap />
        </el-tab-pane>
      </el-tabs>
    </el-col>
  </el-row>
</template>

<style scoped lang="scss">
.main-row {
  height: 100%;
  width: 100%;
  padding-top: 1vh;

  .first-col {
    height: 100%;
    width: 100%;
    padding-left: 1vw;
    padding-right: 0.5vw;

    .events-table {
      //padding-bottom: 2%;
      height: 100%;
      width: 100%;
      border: none;
    }
  }

  .second-col {
    height: 100%;
    width: 100%;
    padding-left: 0.5vw;
    padding-right: 1vw;

    .tabs {
      height: 100%;
      width: 100%;

      .list-view {
        height: 100%;
        width: 100%;
      }
    }
  }
}

:deep(.map-card-row .el-card__body) {
  padding: 0;
  border-radius: 10px;
}

:deep(.events-card-row .events-card > .el-card__body) {
  padding-left: 0;
  padding-right: 0;
  padding-top: 10px;
}
</style>
