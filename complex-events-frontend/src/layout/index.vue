<template>
  <div class="menu-bar">
    <MenuBar />
  </div>

  <div class="main-container">
    <RouterView />
  </div>
</template>

<script setup>
import MenuBar from '@/layout/components/MenuBar/index.vue'
</script>

<style lang="scss" scoped>
.menu-bar {
  height: 5vh;
}

.main-container {
  height: 94vh;
  padding-top: 1vh;
}
</style>
