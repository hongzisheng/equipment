<template>
  <div class="layout-container">
    <aside class="sidebar">
      <MenuBar />
    </aside>

    <main class="main-container">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import MenuBar from '@/layout/components/MenuBar/index.vue'
</script>

<style lang="scss" scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  min-width: 220px;
  background-color: var(--my-menu-bg-color, #001528);
  color: var(--my-menu-text-color, #bfcbd9);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
    overflow-y: auto;
  background: var(--my-page-bg-color, #f0f2f5);
}

.el-menu {
  height: 100%;
  border: none;
}
</style>
