<template>
  <el-menu
    :default-active="$route.path"
    :unique-opened="false"
    collapse-transition
    router
    mode="vertical"
    class="sidebar-menu"
  >
    <MenuItem v-for="item in routes" :key="item.path" :item="item" />
  </el-menu>
</template>

<script setup>
import { constantRoutes } from '@/router/index.ts'
import MenuItem from '@/layout/components/MenuBar/MenuItem.vue'

defineOptions({ name: 'MenuBar' })

const routes = constantRoutes.filter((route) => !route.hidden)
</script>

<style scoped lang="scss">
.sidebar-menu {
  height: 100%;
  overflow-y: auto;
}
</style>
