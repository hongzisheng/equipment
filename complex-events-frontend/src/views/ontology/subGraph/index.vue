<script setup lang="ts">
import graphApi from '@/api/graphApi'
import { onMounted, ref, watch } from 'vue'
import Matrix from '@/views/ontology/subGraph/Matrix.vue'
import Embedding from '@/views/ontology/subGraph/Embedding.vue'
import { SubGraphEmbedding } from '@/views/ontology/subGraph/index'

const subGraphNames = ref([])

function listSubGraphs() {
  graphApi.listSubGraphs().then((res) => {
    subGraphNames.value = res.data
    activeName.value = subGraphNames.value[0]
  })
}

const activeName = ref('')
onMounted(() => {
  listSubGraphs()
})

const currentMatrixData = ref({})
const currentNodesData = ref([])
/**
 * "all_sub_graph_embedding": [
 *             {
 *                 "name": "\u624d\u80fd",
 *                 "reduced_embedding": [
 *                     0.12267869036306789,
 *                     -2.0888836804026048e-17
 *                 ]
 *             },
 *             {
 *                 "name": "\u4e91\u5357",
 *                 "reduced_embedding": [
 *                     -0.12267869036306783,
 *                     -2.0888836804026057e-17
 *                 ]
 *             }
 *         ],
 *
 */
const currentEmbeddings = ref<SubGraphEmbedding[]>([])

const loadData = (loadName: string) => {
  graphApi.loadSubGraphByName(loadName).then((res) => {
    currentMatrixData.value = res.data.adjacency_matrix
    currentNodesData.value = res.data.nodes_data
    currentEmbeddings.value = res.data.all_sub_graph_embedding
  })
}

watch(activeName, (newName) => {
  loadData(newName)
})
</script>

<template>
  <el-tabs tab-position="left" style="height: 100%" v-model="activeName">
    <el-tab-pane v-for="name in subGraphNames" :label="name" :name="name">
      <div v-if="activeName == name" class="tab-content">
        <Matrix
          class="matrix"
          :adjacency-matrix="currentMatrixData"
          :nodes-data="currentNodesData"
        />
        <el-divider class="divider" direction="vertical" />
        <Embedding
          class="embedding"
          :active-name="activeName"
          :nodes-data="currentNodesData"
          :embeddings="currentEmbeddings"
        />
      </div>
    </el-tab-pane>
  </el-tabs>
</template>

<style scoped lang="scss">
:deep(.el-tabs__header) {
  width: 10%;
  margin-right: 2vw !important;

  .el-tabs__nav-wrap {
    width: 100%;

    .el-tabs__nav {
      width: 100%;
    }
  }
}

:deep(.el-tabs__content) {
  height: 100%;

  .el-tab-pane {
    height: 100%;

    .tab-content {
      display: flex;
      width: 100%;
      height: 100%;

      .matrix {
        width: 40%;
        height: 100%;
      }
      .divider{
        width: 1%;
        height: 100%;
        margin-left: 2vw;
      }

      .embedding {
        width: 50%;
        height: 100%;
      }
    }
  }
}
</style>
