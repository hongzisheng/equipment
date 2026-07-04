<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useMapStore } from '@/stores/mapStore'
import { storeToRefs } from 'pinia'

const mapStore = useMapStore()
const { searchText } = storeToRefs(mapStore)
const tmpText = ref('')
</script>

<template>
  <div class="bar">
    <div class="search">
      <el-input
        v-model="tmpText"
        placeholder="请输入内容"
        class="search-input"
        @keydown.enter="searchText = tmpText"
        @clear="searchText = tmpText"
        clearable
      >
        <template #append>
          <el-button type="primary" @click="searchText = tmpText">搜索</el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<style scoped lang="scss">
.bar {
  height: 5vh;
  width: 100%;
  display: block;
  z-index: 1000;
  padding-left: 5px;
  padding-right: 5px;

  .search {
    height: 3vh;
    width: 100%;
    display: flex;
    justify-content: space-between;

    .search-input {
      width: 100%;
    }
  }
}

.result {
  padding-top: 1vh;
  left: 4vw;
  width: 100%;
  height: 20vh;

  &-card {
    width: calc(20vw * 0.9);
  }
}
</style>
