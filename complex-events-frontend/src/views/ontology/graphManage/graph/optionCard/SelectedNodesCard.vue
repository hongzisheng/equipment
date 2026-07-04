<template>
  <div class="card-container">
    <el-card class="card">
      <div class="header">
        <label> 选中节点</label>
        <div class="option">
          <el-button type="text" @click="addNode">
            <el-icon>
              <Plus />
            </el-icon>
          </el-button>
          <el-button type="text" @click="quit">
            <el-icon>
              <Close />
            </el-icon>
          </el-button>
        </div>
      </div>
      <el-scrollbar class="scrollbar" v-if="clickedNodes.length > 0">
        <ul class="list">
          <li v-for="node in clickedNodes">
            <NodeDetailRow :nodeId="node.id" />
          </li>
        </ul>
      </el-scrollbar>
      <el-empty v-else description="选中节点查看更多信息" :image-size="50" />
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { useGraphStore } from '@/stores/graphStore'
import { computed } from 'vue'
import { Close, Plus } from '@element-plus/icons-vue'
import NodeDetailRow from '@/views/ontology/graphManage/graph/optionCard/NodeDetailRow.vue'

const graphStore = useGraphStore()
const clickedNodes = computed(() => graphStore.clickedNodes)

const addNode = () => {
  graphStore.toggleAddNodeMode()
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
      }
    }
  }
}

:deep(.el-divider--horizontal) {
  margin-top: 10px;
  margin-bottom: 10px;
}

:deep(.el-empty) {
  margin: 0;
  padding: 0;
  height: 50%;
  transform: translate(0, 50%);
}
</style>
