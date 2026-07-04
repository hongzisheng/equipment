<template>
  <el-menu
    :default-active="$route.path"
    :unique-opened="false"
    collapse-transition
    router
    mode="horizontal"
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

<style scoped lang="scss"></style>
