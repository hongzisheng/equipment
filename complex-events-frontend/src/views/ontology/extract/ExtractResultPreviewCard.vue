<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import dataApi from '@/api/dataApi.js'
import { ExtractResult, formattedExtractResult } from '@/views/ontology/extract/index'
import { NOT_IMPL_WARN } from '@/views/ontology'
import OntologySelector from '@/commomComponents/OntologySelector.vue'
import { getLabelByProp } from '@/views/ontology/ontologySystem'

/**
 * 抽取结果预览
 */
defineOptions({
  name: 'ExtractResultPreview',
})
const selectedProp = ref([])

const view = ref('数据')
const props = withDefaults(defineProps<{
  selectedItems: object[]
  tableData: ExtractResult[]
}>(), {
  selectedItems: () => [],
  tableData: () => []
})

const isLocation = ref(false)

const tableDataList = ref<ExtractResult[]>([])

watch(() => props.tableData,
  (newValue) => {
    tableDataList.value = newValue
  },
  {
    deep: true,
    immediate: true
  }
)


async function handleEventLocation(row) {
  try {
    const res = await dataApi.getFindLngLat(row.place);
    if (!res.data || !Array.isArray(res.data)) {
      console.error("返回数据格式不正确", res.data);
      return;
    }

    const localList = res.data.map(item => {
      const localName = item.local;
      const coords = item.lng_lat && item.lng_lat.center;
      const lat_lng = coords
        ? `(${coords[0]},${coords[1]})`
        : '(?,?)';
      return { localName, lat_lng };
    });

    const str = localList.map(item => `${item.localName}：${item.lat_lng}`).join(' , ');
    console.log("tableDataList", tableDataList)
    const index = tableDataList.value.findIndex(item => item.place === row.place);
    if (index === -1) {
      console.warn("没找到对应行", row.place);
      return;
    }

    tableDataList.value[index] = {
      ...tableDataList.value[index],
      lng_lat: str
    };
    isLocation.value = true;

    console.log("定位结果字符串:", str);
  } catch (error) {
    console.error("获取经纬度出错:", error);
  }
}
</script>

<template>
  <el-card class="card-container">
    <template #header>
      <div class="title-box">
        <span>抽取结果预览</span>
        <span>事件要素抽取准确率≈88.35%</span>
      </div>
    </template>
    <div class="title">
      <div class="title-label">
        <label>展示的字段</label>
        <OntologySelector v-model="selectedProp" clearable multiple selected-prop />
      </div>
      <el-radio-group v-model="view">
        <el-radio-button label="数据" />
        <el-radio-button label="本体" />
      </el-radio-group>
    </div>
    <div class="table-container">
      <el-table height="100%" v-show="view === '数据'" :data="tableDataList" v-if="selectedProp.length > 0">
        <el-table-column type="selection"></el-table-column>
        <el-table-column v-for="prop in selectedProp" :label="getLabelByProp(prop)" :prop="prop"></el-table-column>
        <el-table-column label="经纬度坐标" v-if="isLocation">
          <template #default="scope">
            {{ scope.row['lng_lat'] }}
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button plain type="primary" @click="handleEventLocation(scope.row)">
              多模态特征<br />融合的事件定位
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-table height="100%" v-show="view === '本体'">
        <el-table-column type="selection"></el-table-column>
        <el-table-column label="头节点" />
        <el-table-column label="关系" />
        <el-table-column label="尾节点" />
        <el-table-column label="操作">
          <el-button plain type="primary" @click="NOT_IMPL_WARN">查看</el-button>
        </el-table-column>
      </el-table>
    </div>
  </el-card>
</template>

<style lang="scss" scoped>
.title-box{
  display: flex;
  justify-content: space-between;
}
.card-container {
  height: 100%;

  :deep(.el-card__body) {
    height: 90%;

    .title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      height: 5%;

      &-label {
        display: flex;
        align-items: center;

        .el-select {
          margin-left: 1vw;
          width: 20vw;
        }
      }
    }

    .table-container {
      margin-top: 1vh;
      height: 90%;

      .el-button {
        width: 100%;
        font-size: 1.2em;
        height: 4em;
      }
    }
  }
}
</style>
