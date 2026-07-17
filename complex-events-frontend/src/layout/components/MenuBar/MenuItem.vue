<template>
  <el-sub-menu v-if="item.children" :index="item.path">
    <template #title>
      <svg-icon v-if="item.meta.icon" :icon-class="item.meta.icon" />
      <span>{{ item.meta.title }}</span>
    </template>
    <MenuItem v-for="item in item.children" :item="item" />
  </el-sub-menu>
  <el-menu-item v-else-if="!item.hidden" :index="item.path">
    <svg-icon v-if="item.meta.icon" :icon-class="item.meta.icon" />
    <span>{{ item.meta.title }}</span>
  </el-menu-item>
</template>

<script setup lang="ts">
import { RouteItem } from '@/router'

defineOptions({ name: 'MenuItem' })
defineProps<{
  item: RouteItem
}>()

</script>

<style scoped lang="scss">
/* 菜单项样式已统一迁移至 MenuBar/index.vue 的 .sidebar-menu :deep() 中，
   以避免 Vue 3 Fragment 组件中 :deep() 选择器无法匹配根元素的问题。 */
</style>
