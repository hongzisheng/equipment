<script setup>
// 全局引入本地 iconfont（文件位于 src/assets/iconfont/iconfont.css）
</script>

<template>
  <router-view />
</template>

<style>
@import url('./assets/iconfont/iconfont.css');

/* 禁止浏览器滚动 */
html, body {
  overflow: hidden;
  height: 100%;
}

/* 确保根元素也禁止滚动 */
#app {
  height: 100%;
  overflow: hidden;
}
</style>