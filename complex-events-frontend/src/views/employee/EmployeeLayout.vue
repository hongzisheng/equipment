<template>
  <div class="employee-layout">
    <!-- 顶部导航栏 - 与管理员端保持一致的风格 -->
    <el-header class="main-header">
      <div class="brand">
        <img src="/logo.png" alt="系统图标" class="sys-logo" />
        <div class="sys-title-group">
          <span class="title-zh">石化设备大检修调度系统</span>
          <span class="title-en">PETROCHEMICAL EQUIPMENT MAINTENANCE SYSTEM</span>
        </div>
      </div>

      <div class="header-actions">
        <el-tag type="warning" size="small" class="role-tag">员工端</el-tag>
        <el-dropdown trigger="click">
          <el-button>
            <el-icon class="mr4"><User /></el-icon>
            {{ userStore.name || '员工' }}
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
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-header">员工工作台</div>
        <el-menu
          :default-active="activeMenu"
          :router="true"
          background-color="var(--my-menu-bg-color, #2b3243)"
          text-color="var(--my-menu-text-color, #a6b0c3)"
          active-text-color="#ffffff"
        >
          <el-menu-item index="/employee/schedule">
            <el-icon><Calendar /></el-icon>
            <span>我的排程</span>
          </el-menu-item>
          <el-menu-item index="/employee/work-report">
            <el-icon><Document /></el-icon>
            <span>工况反馈</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 主内容区域 -->
      <main class="main-container">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import { User, ArrowDown, Calendar, Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const handleLogout = () => {
  userStore.logout().then(() => {
    router.push('/login')
  }).catch(() => {
    userStore.resetToken().then(() => {
      router.push('/login')
    })
  })
}
</script>

<style lang="scss" scoped>
.employee-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
  overflow: hidden;
}

/* ============================================
   顶部导航栏（与管理员端一致）
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
  min-width: 240px;
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
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  height: 100%;
  background-color: var(--my-menu-bg-color, #2b3243);
  color: var(--my-menu-text-color, #a6b0c3);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  z-index: 99;
  display: flex;
  flex-direction: column;

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

.sidebar-header {
  padding: 20px 20px 12px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
}

.el-menu {
  border-right: none;
  flex: 1;
}

.main-container {
  flex: 1;
  overflow-y: auto;
  height: 100%;
  background-color: #f0f2f5;
  background-image: radial-gradient(#d1d5db 1px, transparent 1px);
  background-size: 24px 24px;
  padding: 24px;

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

/* ============================================
   头部右侧操作区
   ============================================ */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-tag {
  font-size: 12px;
}

.mr4 {
  margin-right: 4px;
}

.ml4 {
  margin-left: 4px;
}
</style>
