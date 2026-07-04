<template>
  <el-row :gutter="20" class="content-row">
    <el-col :span="6">
      <!--搜索行-->
      <el-row :gutter="10">
        <el-col :span="14">
          <el-input v-model="keywordSearch" placeholder="输入关键词进行搜索" clearable />
        </el-col>
        <el-col :span="6">
          <el-select v-model="nodeLimit" placeholder="节点数量限制">
            <el-option label="10节点" value="10"></el-option>
            <el-option label="25节点" value="25"></el-option>
            <el-option label="50节点" value="50"></el-option>
            <el-option label="100节点" value="100"></el-option>
            <el-option label="200节点" value="200"></el-option>
            <el-option label="500节点" value="500"></el-option>
            <el-option label="不限制节点数量" value="unlimited"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadData">检索</el-button>
        </el-col>
      </el-row>

      <!--节点信息行-->
      <el-row class="search-result-row">
        <SearchResultCard :nodes="nodes" :edges="edges" />
      </el-row>
      <!--选中操作行-->
      <SelectedNodesCard class="nodes-selected" />
      <SelectedEdgesCard class="edges-selected" />
    </el-col>
    <el-col :span="18">
      <div class="graph">
        <div class="graph-title">
          <span>基于图的事件关联要素可视化</span>
          <el-button type="primary" @click="hideAllEdges">事件与数据语义关联</el-button>
        </div>
        <div class="graph-container" v-loading="loading" element-loading-text="正在加载数据">
          <div class="graph-opts">
            <el-tooltip effect="light">
              <el-button text @click="forwardToCluster">
                <svg-icon icon-class="cluster" />
              </el-button>
              <template #content> 聚类</template>
            </el-tooltip>

            <el-tooltip effect="light" :visible="saveGraphTooltipVisible">
              <template #default>
                <el-button text @click="saveGraph">
                  <el-icon>
                    <SvgIcon icon-class="save" />
                  </el-icon>
                </el-button>
              </template>
              <template #content>
                <div style="display: flex; justify-content: space-between">
                  <el-text style="width: 40%">保存子图名称:</el-text>
                  <el-input v-model="saveName" style="margin-left: 10px; width: 60%" />
                </div>
                <div style="display: flex; justify-content: flex-end; margin-top: 10px">
                  <el-button type="default" @click="saveGraphTooltipVisible = false"
                    >取消</el-button
                  >
                  <el-button type="primary" @click="handleConfirmSaveGraph">确认</el-button>
                </div>
              </template>
            </el-tooltip>

            <el-tooltip effect="light">
              <template #default>
                <el-switch
                  v-model="locked"
                  size="large"
                  inline-prompt
                  :active-icon="Lock"
                  :inactive-icon="Unlock"
                />
              </template>
              <template #content>
                <el-text v-if="!locked">锁定布局</el-text>
                <el-text v-else>解锁布局</el-text>
              </template>
            </el-tooltip>
          </div>
          <KnowledgeGraph ref="graphRef" />
          <GraphLegend :clickedNodeGroup="clickedNodeGroup" :node-groups="nodeGroups" />
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import KnowledgeGraph from '@/views/ontology/graphManage/graph/KnowledgeGraph.vue'
import { computed, onMounted, provide, ref, useTemplateRef, watch } from 'vue'
import graphApi from '@/api/graphApi.js'
import GraphLegend from '@/views/ontology/graphManage/graph/GraphLegend.vue'
import SearchResultCard from '@/views/ontology/graphManage/SearchResultCard.vue'
import { Lock, Unlock } from '@element-plus/icons-vue'

import { useGraphStore } from '@/stores/graphStore'
import { storeToRefs } from 'pinia'
import SelectedNodesCard from '@/views/ontology/graphManage/graph/optionCard/SelectedNodesCard.vue'
import SelectedEdgesCard from '@/views/ontology/graphManage/graph/optionCard/SelectedEdgesCard.vue'
import SvgIcon from '@/components/SvgIcon/index.vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { Edge } from '@/views/ontology/graphManage/graph'

const keywordSearch = ref<string>('')
const nodeLimit = ref<string>('25')
const graphStore = useGraphStore()
// 从 store 中提取属性时保持其响应性
const { nodes, edges, locked, visRef } = storeToRefs(graphStore)
// 增量更新的时候锁定布局，避免画布节点抖动

/**
 * 加载数据
 * 根据关键词是否为空分别调用不同的方法
 *  - 为空： 调用latest方法获取最新一批数据
 *  - 不为空： 调用search方法搜索相关数据
 */
const loadData = () => {
  loading.value = true
  const isSearch = keywordSearch.value.trim() !== ''

  const apiCall = isSearch
    ? graphApi.searchGraphData(keywordSearch.value, nodeLimit.value)
    : graphApi.latestGraphData(nodeLimit.value)

  apiCall
    .then((res) => {
      if (res.data && res.data.nodes && res.data.edges) {
        nodes.value = res.data.nodes
        edges.value = res.data.edges.map((edge) => {
          return {
            ...edge,
            // 隐藏label
            label: '',
          }
        })
        // 进行更新
        getNodesDataSet()
        getEdgesDataSet()
      } else {
        console.warn('Invalid response structure:', res)
      }
    })
    .catch((error) => {
      console.error('Failed to fetch graphManage data:', error)
    })
    .finally(() => {
      loading.value = false
    })
}

const graphRef = useTemplateRef('graphRef')
onMounted(() => {
  loadData()
  visRef.value = graphRef.value
})

/**
 * 处理点击节点的事件，点击节点信息由网络图组件传过来
 */
const { clickedNodeGroup, clickedObjects, nodeGroups, loading } = storeToRefs(graphStore)

/**
 * 用于网络图展示的数据源
 */
const { getNodesDataSet, getEdgesDataSet } = graphStore
const saveGraphTooltipVisible = ref(false)
const saveName = ref('')

function saveGraph() {
  saveGraphTooltipVisible.value = !saveGraphTooltipVisible.value
}

function handleConfirmSaveGraph() {
  const saveNodes = nodes.value
  const saveEdges = edges.value.map((e) => {
    return {
      from: e.from,
      to: e.to,
    }
  })
  graphApi
    .saveSubGraph(saveName.value, saveNodes, saveEdges)
    .then((res) => {
      ElMessage.success('保存成功')
    })
    .catch((e) => {
      ElMessage.error('保存失败')
    })
    .finally(() => {
      saveGraphTooltipVisible.value = false
      saveName.value = ''
    })
}

const router = useRouter()

function forwardToCluster() {
  router.push('/ontology/cluster')
}

const tmpEdgesData = ref<Edge[]>([])
const hideAllEdges = () => {
  if (tmpEdgesData.value.length == 0) {
    // 点击隐藏
    tmpEdgesData.value = edges.value
    edges.value = []
    // 更新
    getEdgesDataSet()
  } else {
    // 点击恢复
    edges.value = tmpEdgesData.value

    tmpEdgesData.value = []
    getEdgesDataSet()
  }
}
</script>

<style scoped lang="scss">
.content-row {
  height: 90vh;
  width: 100%;
  padding-left: 1vw;
  .graph {
    height: 90vh;
    width: 100%;
    &-title {
      height: 5%;
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      span {
        font-weight: bold;
        font-size: 2rem;
        color: #4f4f4f;
      }
      :deep(.el-button) {
        height: 80%;
      }
    }
    &-container {
      height: 95%;
      width: 100%;
      position: relative;

      .graph-opts {
        position: absolute; /* 相对于父容器定位 */
        top: 10px; /* 距离顶部的距离 */
        left: 10px; /* 距离左侧的距离 */
        z-index: 1000; /* 确保图标在画布上方 */
      }
    }
  }

  .search-result-row {
    margin-top: 1vh;
    width: 100%;
    height: 30vh;
    padding-bottom: 2vh;
  }

  .nodes-selected {
    width: 100%;
    height: 15vh;
    margin-bottom: 20px;
    margin-top: 20px;
  }

  .edges-selected {
    height: 30vh;
    width: 100%;
  }
}

:deep(.el-tag--info) {
  --el-tag-border-color: transparent;
}

.el-button + .el-button {
  margin-left: 0 !important;
}
</style>
