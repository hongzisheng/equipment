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
  border-right: none !important;
  padding: 16px 0;
  background-color: transparent !important;

  /* ============================================
     一级菜单（sub-menu title）
     ============================================ */
  :deep(.el-sub-menu__title) {
    font-size: 16px;
    font-weight: 500;
    height: 54px;
    line-height: 54px;
    padding: 0 40px !important;
    margin: 4px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease;
    text-align: center;
    color: #a6b0c3 !important;

    &:hover {
      background-color: #3b4255 !important;
      color: #ffffff !important;
    }
  }

  /* ============================================
     所有菜单项基础样式（含顶层如"首页"）
     ============================================ */
  :deep(.el-menu-item) {
    font-size: 16px;
    font-weight: 500;
    height: 54px;
    line-height: 54px;
    padding: 0 40px !important;
    margin: 4px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease;
    text-align: center;
    color: #a6b0c3 !important;
    width: auto;
    box-sizing: border-box;
    border: none;

    // hover 状态
    &:hover:not(.is-active) {
      background-color: #3b4255 !important;
      color: #ffffff !important;
    }

    // 激活状态
    &.is-active {
      background-color: #3b82f6 !important;
      color: #ffffff !important;
      font-weight: 600;
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
    }
  }

  /* ============================================
     二级菜单项覆盖（el-sub-menu 内部），增加缩进
     ============================================ */
  :deep(.el-sub-menu .el-menu-item) {
    font-size: 14px;
    font-weight: normal;
    height: 48px;
    line-height: 48px;
    padding: 0 20px 0 60px !important;
    text-align: left;
  }

  /* ============================================
     嵌套子菜单背景透明
     ============================================ */
  :deep(.el-menu) {
    background-color: transparent !important;
  }

  /* ============================================
     子菜单展开箭头
     ============================================ */
  :deep(.el-sub-menu__icon-arrow) {
    transition: transform 0.3s !important;
    right: 20px !important;
  }

  /* ============================================
     菜单内图标样式
     ============================================ */
  :deep(.el-sub-menu__title .svg-icon),
  :deep(.el-menu-item .svg-icon) {
    margin-right: 8px;
    font-size: 18px;
  }
}
</style>
