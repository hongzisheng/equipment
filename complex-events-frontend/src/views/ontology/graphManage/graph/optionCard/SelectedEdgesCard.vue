<template>
  <div class="card-container">
    <el-card class="card">
      <div class="header">
        <label> 选中边</label>
        <div class="option">
          <el-button type="text" @click="addEdge">
            <el-icon>
              <Plus />
            </el-icon>
          </el-button>
          <el-button type="text" @click="editEdge">
            <el-icon>
              <Edit />
            </el-icon>
          </el-button>
          <el-button type="text" @click="quit">
            <el-icon>
              <Close />
            </el-icon>
          </el-button>
        </div>
      </div>
      <el-scrollbar class="scrollbar" v-if="clickedEdges.length > 0">
        <ul class="list">
          <li v-for="edge in clickedEdges">
            <EdgeDetailRow :edge-id="edge.id" />
          </li>
        </ul>
      </el-scrollbar>
      <el-empty v-else description="选中节点或边查看更多信息" :image-size="80" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useGraphStore } from '@/stores/graphStore'
import { computed } from 'vue'
import { Close, Edit, Plus } from '@element-plus/icons-vue'
import EdgeDetailRow from '@/views/ontology/graphManage/graph/optionCard/EdgeDetailRow.vue'

const graphStore = useGraphStore()
const clickedEdges = computed(() => graphStore.clickedEdges)
/**
 * 相关操作的具体实现由图谱提供接口，自定义实现
 * @see /src/views/ontology/graphManage/index.ts - graphOptions - manipulation
 */
const addEdge = () => {
  graphStore.toggleAddEdgeMode()
}

const editEdge = () => {
  graphStore.toggleEditEdgeMode()
}

const quit = () => {
  graphStore.toggleDisableEditMode()
}

</script>

<style scoped lang="scss">
.card-container {
  height: 100%;
  width: 100%;

  .card {
    height: 100%;

    .header {
      height: 10%;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .scrollbar {
      height: 90%;

      .list {
        // 去掉无序列表的点
        list-style: none;
        padding: 0;
        li {
          height: auto;
        }
      }
    }
  }
}
:deep(.el-divider--horizontal) {
  margin-top: 10px;
  margin-bottom: 10px;
}
</style>
