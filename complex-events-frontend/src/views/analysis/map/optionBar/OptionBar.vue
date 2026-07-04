<template>
  <div>
    <SearchBar class="search-bar" @markersUpdate="markersUpdate" />
    <el-radio-group class="map-layer-choose" v-model="mapLayer">
      <el-radio-button
        v-for="opt in mapLayerRadioOptions"
        :label="opt.label"
        :key="opt.value"
        :value="opt.value"
      />
    </el-radio-group>
    <!--  多功能操作按钮位置，根据配置动态生成     -->
    <component class="map-option-radio" :is="mapInteractiveRadioButtons" />
    <el-select class="place-selector" placeholder="筛选地区" v-model="placeSelectedValue" filterable clearable>
      <el-option v-for="plc in placesSelectOptions" :label="plc.label" :value="plc.value" />
    </el-select>
    <div class="date-picker">
      <el-date-picker
        v-model="dateRangePicker"
        value-format="YYYY-MM-DD"
        type="daterange"
        range-separator="到"
        start-placeholder="选择开始日期"
        end-placeholder="选择结束日期"
        size="default"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { mapLayerRadioOptions } from '@/views/analysis/map/map'
import { mapInteractiveRadioButtons } from '@/views/analysis/map/optionBar/mapInteractiveOption'
import SearchBar from '@/views/analysis/map/optionBar/SearchBar.vue'
import { useMapStore } from '@/stores/mapStore'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

const mapStore = useMapStore()
// 双向绑定mapStore中定义的值
const { mapLayer, dateRangePicker, placeSelectedValue } = storeToRefs(mapStore)

const markersUpdate = (coordinates: []) => {
  mapStore.coordinates.push(...coordinates)
}
const placesSelectOptions = computed(()=>mapStore.placesSelectedOptions)
</script>

<style scoped lang="scss">
.search-bar {
  width: 20vw;
}

.map-layer-choose {
  width: auto;
  margin-left: 2vw;
}

.map-option-radio {
  width: auto;
  margin-left: 2vw;
}

.place-selector {
  width: 10vw;
  margin-left: 2vw;
}

.date-picker {
  width: 10vw; /* 增加宽度 */
  margin-left: 2vw;
}
</style>
