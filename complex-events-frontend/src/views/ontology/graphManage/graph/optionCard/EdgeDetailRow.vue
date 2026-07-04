<script setup lang="ts">
import nodeTypeTag from '@/views/ontology/graphManage/nodeTypeTag'
import { Check, Close, Delete, Edit } from '@element-plus/icons-vue'
import { useGraphStore } from '@/stores/graphStore'
import { computed, ref, watch } from 'vue'
import { NOT_IMPL_WARN } from '@/views/ontology'
import { Edge, handleEditEdge } from '@/views/ontology/graphManage/graph'
import graphApi from '@/api/graphApi'
import { ElMessage } from 'element-plus'
import SvgIcon from '@/components/SvgIcon/index.vue'

const graphStore = useGraphStore()
const clickedEdges = computed(() => graphStore.clickedEdges)
const findNode = graphStore.findNode

const deleteEdge = (edgeData: Edge) => {
  graphStore.enableLoading()
  graphApi
    .deleteEdge(edgeData.id)
    .then((res) => {
      if (res.code === 20000) {
        ElMessage.success('关系删除成功')
        // 在数据集中删除关系
        graphStore.deleteEdge(edgeData)
      } else {
        ElMessage.error('关系删除失败')
      }
    })
    .finally(() => {
      graphStore.disableLoading()
    })
}
const props = defineProps<{
  edgeId: string
}>()

const tmpEdge = ref<Edge>(null)
watch(
  clickedEdges,
  () => {
    tmpEdge.value = clickedEdges.value.find((edge) => edge.id === props.edgeId)
  },
  { immediate: true },
)

const renameMode = ref(false)
const tmpEdgeEditName = ref('')
watch(renameMode, (newValue) => {
  if (newValue) {
    tmpEdgeEditName.value = tmpEdge.value.name
  }
})

function handleUpdate() {
  tmpEdge.value.name = tmpEdgeEditName.value
  handleEditEdge(tmpEdge.value, () => {
    console.log('重命名的回调函数')
    renameMode.value = false
  },true)
}
</script>

<template>
  <el-row>
    <div class="edge-header">
      <span class="edge-index">{{ tmpEdge?.index }}</span>
      <div class="center-container">
        <Transition name="fade" mode="out-in">
          <div v-if="!renameMode" class="name-display transition-wrapper" key="display">
            关系：{{ tmpEdge?.name }}
          </div>
          <div v-else class="transition-wrapper" key="input">
            <el-input v-model="tmpEdgeEditName" class="name-input" />
          </div>
        </Transition>
      </div>
      <div class="button-container">
        <Transition name="fade" mode="out-in">
          <el-button
            type="text"
            class="action-button"
            @click="renameMode = true"
            v-if="!renameMode"
          >
            <SvgIcon icon-class="rename" />
          </el-button>
          <div v-else>
            <el-button type="text" class="action-button" @click="handleUpdate">
              <el-icon>
                <Check />
              </el-icon>
            </el-button>
            <el-button type="text" class="action-button" @click="renameMode = false">
              <el-icon>
                <Close />
              </el-icon>
            </el-button>
          </div>
        </Transition>
      </div>
    </div>
  </el-row>

  <el-row style="margin-top: 5px">
    <el-col :span="6">
      <span>源节点：</span>
    </el-col>
    <el-col :span="6">
      <component :is="nodeTypeTag(findNode(tmpEdge.from).group)" />
    </el-col>
    <el-col :span="12">
      <span>{{ findNode(tmpEdge.from).name }}</span>
    </el-col>
  </el-row>
  <el-row style="margin-top: 5px">
    <el-col :span="6">
      <span>目标节点：</span>
    </el-col>
    <el-col :span="6">
      <component :is="nodeTypeTag(findNode(tmpEdge.to).group)" />
    </el-col>
    <el-col :span="12">
      <span>{{ findNode(tmpEdge.to).name }}</span>
    </el-col>
  </el-row>
  <el-row>
    <el-col :offset="20" :span="4">
      <el-button type="text" @click="deleteEdge(tmpEdge)">
        <el-icon>
          <Delete />
        </el-icon>
      </el-button>
    </el-col>
  </el-row>
  <el-divider />
</template>

<style scoped lang="scss">
:deep(.el-divider--horizontal) {
  margin-top: 10px;
  margin-bottom: 10px;
}

.el-col {
  display: flex;
}

.edge-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
}

.edge-index {
  flex-shrink: 0;
}

.center-container {
  flex: 1;
  margin: 0 10px;
  min-width: 100px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 32px;

  .transition-wrapper {
    width: 50%; // 固定宽度
    height: 32px; // 固定高度
    display: flex;
    align-items: center;

    .name-display {
      width: 100%;
      padding: 1px 11px;
      box-sizing: border-box;
      text-align: right;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .name-input {
      width: 100%;
    }
  }
}

.button-container {
  flex-shrink: 0;
  display: flex;
  gap: 5px;
}

.action-button {
  padding: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
