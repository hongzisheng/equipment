<script setup>

</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
/* 重置默认样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: transparent;
  overflow: hidden; /* 防止页面滚动影响居中 */
}

#app {
  height: 100%;
  width: 100%;
}
</style>