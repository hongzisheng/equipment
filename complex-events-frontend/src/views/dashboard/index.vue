<template>
  <div class="dashboard-container">
    <div class="dashboard-text">{{ name }}欢迎登录系统！</div>
  </div>
</template>

<script>
import { useUserStore } from '@/stores/user.js'

export default {
  name: 'Dashboard',
  computed: {
    name() {
      // 假设 user store 中有 name getter
      const userStore = useUserStore()
      return userStore.name
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard {
  &-container {
    margin: 30px;
  }
  &-text {
    font-size: 30px;
    line-height: 46px;
  }
}
</style>
