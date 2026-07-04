<script setup lang="ts">
import { Node, Edge, nodeLegendMap } from '@/views/ontology/graphManage/graph'
import nodeTypeTag from './nodeTypeTag'
import { useGraphStore } from '@/stores/graphStore'

const props = defineProps<{
  nodes: Node[]
  edges: Edge[]
}>()


const findNode = useGraphStore().findNode
</script>

<template>
  <el-card class="card">
    <div class="card-header">
      <label>检索结果列表</label>
    </div>
    <el-scrollbar class="list-container">
      <ul class="search-result-list">
        <li v-for="row in nodes">
          <el-row>
            <el-col :span="8">
              <component :is="nodeTypeTag(row.group)" />
            </el-col>
            <el-col :span="16">
              {{ row.name }}
            </el-col>
          </el-row>
        </li>
        <li v-for="edge in edges">
          <el-row>
            <el-col :span="8">
              {{ edge.name }}
            </el-col>
            <el-col :span="8">
              <component :is="nodeTypeTag(findNode(edge.from)?.group, findNode(edge.from)?.name)" />
            </el-col>
            <el-col :span="8">
              <component :is="nodeTypeTag(findNode(edge.to)?.group, findNode(edge.to)?.name)" />
            </el-col>
          </el-row>
        </li>
      </ul>
    </el-scrollbar>
  </el-card>
</template>

<style scoped lang="scss">
.card {
  width: 100%;
  height: 30vh;

  &-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: calc(10% - 5px);
    margin-bottom: 5px;
  }

  .list-container {
    height: 90%;

    .search-result-list {
      width: 100%;

      // 去掉无序列表的点
      list-style: none;
      padding-inline-start: 5px;

      li {
        margin-bottom: 5px;
      }
    }
  }
}

:deep(.el-tag--info) {
  --el-tag-border-color: transparent;
}

:deep(.el-card__body){
  padding-top: 5px;
}
</style>
