<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <el-header class="main-header">
      <div class="brand">
        <img src="/logo.png" alt="系统图标" class="sys-logo" />
        <div class="sys-title-group">
          <span class="title-zh">石化设备大检修调度系统</span>
          <span class="title-en">PETROCHEMICAL EQUIPMENT MAINTENANCE SYSTEM</span>
        </div>
      </div>

      <div class="header-actions">
        <!-- 人员退出 -->
        <el-dropdown trigger="click">
          <el-button>
            <el-icon class="mr4"><User /></el-icon>
            {{ userStore.name || 'Admin' }}
            <el-icon class="ml4"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <div class="layout-container">
      <aside class="sidebar">
        <MenuBar />
      </aside>

      <main class="main-container">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import MenuBar from '@/layout/components/MenuBar/index.vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import { User, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  userStore.logout().then(() => {
    router.push('/login')
  }).catch(() => {
    // fallback: reset token and redirect
    userStore.resetToken().then(() => {
      router.push('/login')
    })
  })
}
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
  overflow: hidden;
}

/* ============================================
   顶部导航栏
   ============================================ */
.main-header {
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  z-index: 1000;
}

.brand {
  display: flex;
  align-items: center;
  height: 100%;
  gap: 12px;
  min-width: var(--my-sidebar-width, 240px);
  justify-content: flex-start;
  white-space: nowrap;
}

.sys-logo {
  height: 38px;
  width: 38px;
  object-fit: contain;
  flex-shrink: 0;
}

.sys-title-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title-zh {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(90deg, #1d4ed8, #3b82f6);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.title-en {
  font-size: 9px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.2px;
  line-height: 1;
  margin-top: 2px;
  font-family: 'Arial', sans-serif;
  white-space: nowrap;
}

/* ============================================
   侧边栏 + 内容区
   ============================================ */
.layout-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: var(--my-sidebar-width, 240px);
  min-width: var(--my-sidebar-width, 240px);
  background-color: var(--my-menu-bg-color, #2b3243);
  color: var(--my-menu-text-color, #a6b0c3);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  z-index: 99;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.main-container {
  flex: 1;
  overflow-y: auto;
  background-color: #f0f2f5;
  background-image: radial-gradient(#d1d5db 1px, transparent 1px);
  background-size: 24px 24px;
  padding: 24px;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.el-menu {
  height: 100%;
  border: none;
}

/* ============================================
   头部右侧操作区
   ============================================ */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mx8 {
  margin-left: 8px;
  margin-right: 8px;
}

.mr4 {
  margin-right: 4px;
}

.ml4 {
  margin-left: 4px;
}
</style>
