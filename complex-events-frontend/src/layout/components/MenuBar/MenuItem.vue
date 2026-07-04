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

<style scoped lang="scss"></style>
