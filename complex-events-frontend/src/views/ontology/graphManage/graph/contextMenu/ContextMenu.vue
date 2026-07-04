<template>
  <div class="menu-list menu-radius">
    <ul>
      <li @mouseenter="showSubMenu('expand')" @mouseleave="activeSubMenu = ''">
        <div class="have-sub-menu">
          <span> 展开节点 </span>
          <el-icon>
            <ArrowRight />
          </el-icon>
        </div>

        <ul v-if="activeSubMenu === 'expand'" class="sub-menu menu-radius">
          <li @click="expandNode">展开一层</li>
          <li v-if="rightNodeType === 'Event'" @click="expandCommonNodes('Person')">
            获取共同人物节点
          </li>
          <li v-if="rightNodeType === 'Event'" @click="expandCommonNodes('Organization')">
            获取共同组织节点
          </li>
        </ul>
      </li>
      <li @click="focusNode">聚焦节点</li>
      <li @click="hideNode">隐藏节点</li>
      <li @click="unlocked">取消锁定</li>
      <li @click="cancelContextMenu">取消</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import { useGraphStore } from '@/stores/graphStore.js'
import { storeToRefs } from 'pinia'
import { ArrowRight } from '@element-plus/icons-vue'

const activeSubMenu = ref('')
const showSubMenu = (menuName: string) => {
  activeSubMenu.value = menuName
}
const graphStore = useGraphStore()
const { locked, rightClickedNode, clickedNodes, nodesDataSet, edgesDataSet, contextMenuVisible } =
  storeToRefs(graphStore)

// 右键菜单选项的处理函数
const expandNode = () => {
  if (rightClickedNode.value) {
    graphStore.handleExpandNode(rightClickedNode.value)
    cancelContextMenu()
  }
}

const focusNode = inject<() => void>('focusNodeProvider')

const hideNode = () => {
  if (rightClickedNode.value) {
    nodesDataSet.value.remove(rightClickedNode.value)
    graphStore.getNodesDataSet()
    cancelContextMenu()
  }
}

const unlocked = () => {
  if (locked.value) {
    locked.value = false
  }
  graphStore.unlock()
}
const cancelContextMenu = () => {
  contextMenuVisible.value = false
}

const rightNodeType = computed(() => {
  const node = clickedNodes.value.find((n) => n.id == rightClickedNode.value)
  return node?.group ?? ''
})

function expandCommonNodes(commonNodeType: string) {
  if (rightClickedNode.value) {
    graphStore.handleExpandCommonNodes(commonNodeType, rightClickedNode.value)
    cancelContextMenu()
  }
}
</script>

<style scoped lang="scss">
.menu-list {
  padding: 5px 0;
}

.menu-radius {
  border-radius: 5px;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    padding: 8px 4px 16px 16px;
    cursor: pointer;
    min-height: 4vh;
    min-width: 120px;

    &:hover {
      background-color: #f5f5f5;
    }

    &:not(:last-child) {
      border-bottom: 1px solid #eee;
    }
  }
}

.sub-menu {
  position: absolute;
  left: 100%;
  top: 0;
  background: white;
  border: 1px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.have-sub-menu {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
