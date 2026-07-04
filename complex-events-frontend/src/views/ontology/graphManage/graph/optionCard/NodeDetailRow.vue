<script setup lang="ts">
import nodeTypeTag from '@/views/ontology/graphManage/nodeTypeTag'
import { Check, Close, Delete, Edit } from '@element-plus/icons-vue'
import NodeTypeSelector from '@/views/ontology/graphManage/graph/edit/NodeTypeSelector.vue'
import { tmpNode } from '@/views/ontology/graphManage/graph'
import { NOT_IMPL_WARN } from '@/views/ontology'
import { computed, onMounted, ref, watch } from 'vue'
import { useGraphStore } from '@/stores/graphStore'
import { ElMessageBox, ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import graphApi from '@/api/graphApi'

const editMode = ref<boolean>(false)
const editNode = (info) => {
  editMode.value = true
}

const props = defineProps<{
  nodeId: string
}>()
const graphStore = useGraphStore()
const { loading } = storeToRefs(graphStore)
const clickedNodes = computed(() => graphStore.clickedNodes)
const tmpNode = ref(null)
watch(
  clickedNodes,
  () => {
    const node = clickedNodes.value.find((n) => n.id == props.nodeId)
    // 创建节点的深拷贝副本
    if (node) tmpNode.value = JSON.parse(JSON.stringify(node))
  },
  {
    immediate: true,
  },
)

const deleteNode = (node) => {
  ElMessageBox.confirm('确定要删除这个节点吗？', 'Warning', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      console.log('info', node)
      loading.value = true
      graphApi
        .deleteNode(node.id)
        .then((res) => {
          if (res.code === 20000) {
            ElMessage.success('节点删除成功')
            // 在数据集中删除节点
            graphStore.deleteNode(node)
          } else {
            ElMessage.error('节点删除失败')
          }
        })
        .finally(() => {
          loading.value = false
          graphStore.handleNodeClick([])
          graphStore.selectNodes([])
        })
    })
    .catch(() => {
      ElMessage({
        type: 'info',
        message: '取消删除',
      })
    })
}

const check = (node) => {
  console.log('完成修改', node)
  loading.value = true
  editMode.value = false
  tmpNode.value = node
  graphApi
    .updateNode(node.id, node.name, node.group)
    .then((res) => {
      if (res.code == 20000) {
        ElMessage.success('节点修改成功')
        graphStore.updateNode(node)
      } else {
        ElMessage.error('节点修改失败')
        // 还原
        tmpNode.value = clickedNodes.value.find((n) => n.id == props.nodeId)
      }
    })
    .finally(() => {
      loading.value = false
      graphStore.focus(node.id)
    })
}

function cancelEdit() {
  editMode.value = false
  // 重新从原始数据创建副本
  const node = clickedNodes.value.find((n) => n.id == props.nodeId)
  if (node) {
    tmpNode.value = JSON.parse(JSON.stringify(node))
  }
}
</script>

<template>
  <el-row>
    <el-col :span="8">
      <component v-show="!editMode" :is="nodeTypeTag(tmpNode.group)" />
      <NodeTypeSelector v-show="editMode" v-model="tmpNode.group" />
    </el-col>
    <el-col :span="12">
      <span v-show="!editMode" class="node-name">
        {{ tmpNode.name }}
      </span>
      <el-input v-show="editMode" v-model="tmpNode.name" />
    </el-col>
    <el-col :span="4">
      <el-button v-if="editMode" type="text" @click="check(tmpNode)">
        <el-icon>
          <Check />
        </el-icon>
      </el-button>
      <el-button v-if="editMode" type="text" @click="cancelEdit">
        <el-icon>
          <Close />
        </el-icon>
      </el-button>
      <el-button type="text" v-if="!editMode" @click="editNode(tmpNode)">
        <el-icon>
          <Edit />
        </el-icon>
      </el-button>
      <el-button type="text" v-if="!editMode" @click="deleteNode(tmpNode)">
        <el-icon>
          <Delete />
        </el-icon>
      </el-button>
    </el-col>
  </el-row>
</template>

<style scoped lang="scss">
.node-name {
  word-wrap: break-word;
  word-break: break-all;
  white-space: normal;
}
</style>
