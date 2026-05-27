<template>
  <div class="main-layout">
    <!-- 头部 -->
    <el-header class="main-header">
      <div class="brand">
        <img src="/logo.png" alt="系统图标" class="sys-logo" />
        <div class="sys-title-group">
          <span class="title-zh">石化设备大检修调度系统</span>
          <span class="title-en">PETROCHEMICAL EQUIPMENT MAINTENANCE SYSTEM</span>
        </div>
      </div>
      <div class="header-actions">
        <!-- 消息通知 -->
        <el-badge :value="unreadCount" :hidden="!unreadCount" class="mx8">
          <el-button @click="openNotify" circle>
            <el-icon><Bell /></el-icon>
          </el-button>
        </el-badge>

        <!-- 人员登录 / 退出 -->
        <el-dropdown trigger="click">
          <el-button>
            <el-icon class="mr4"><User /></el-icon>
            Admin
            <el-icon class="ml4"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="!isLogin" @click="login">登录</el-dropdown-item>
              <el-dropdown-item v-else @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <div class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="main-sider">
        <el-menu
          :default-active="activeMenu"
          class="main-menu"
          @select="handleMenuSelect"
        >
          <el-sub-menu index="worker-info-management">
            <template #title>
              <el-icon><UserFilled /></el-icon>
              <span>工人管理</span>
            </template>
            <el-menu-item index="worker-data-import">
            
              <span>工人台账</span>
            </el-menu-item>
            <!--
            <el-menu-item index="worker-cert-management">
             
              <span>证件管理</span>
            </el-menu-item>
            <el-menu-item index="worker-assessment-records">
            
              <span>考核记录</span>
            </el-menu-item>
            -->
          </el-sub-menu>
          
          <el-sub-menu index="device-info-management">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>设备管理</span>
            </template>
            <el-menu-item index="device-data-import">
             
              <span>设备台账</span>
            </el-menu-item>
            <!--
            <el-menu-item index="device-type-management">
            
              <span>设备类型管理</span>
            </el-menu-item>
            -->
          </el-sub-menu>
          
          <el-sub-menu index="tool-info-management">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>维修机具管理</span>
            </template>
            <el-menu-item index="tool-data-management">
             
              <span>维修机具台账</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="material-info-management">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>辅助材料管理</span>
            </template>
            <el-menu-item index="material-data-import">
            
              <span>辅助材料台账</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="rule-info-management">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>规则管理</span>
            </template>
            <el-menu-item index="rule-data-import">
       
              <span>规则库</span>
            </el-menu-item>
            <el-menu-item index="knowledge-structure-tree">

              <span>知识结构树</span>
            </el-menu-item>
            <el-menu-item index="knowledge-extraction">
              
              <span>知识提取</span>
            </el-menu-item>
            <!-- 新增：搜索区菜单项 -->
            <el-menu-item index="search-area">
              
              <span>搜索区</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="schedule-data-management">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>调度数据管理</span>
            </template>
            <el-menu-item index="worker-management">
              <el-icon><User /></el-icon>
              <span>工人</span>
            </el-menu-item>
            <el-menu-item index="device-management">
              <el-icon><Monitor /></el-icon>
              <span>设备</span>
            </el-menu-item>
            <el-menu-item index="task-management">
              <el-icon><List /></el-icon>
              <span>工单</span>
            </el-menu-item>
            <el-menu-item index="dashboard">
              <el-icon><Calendar /></el-icon>
              <span>调度生成</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 数据管理 -->
          <el-sub-menu index="data-management">
            <template #title>
              <el-icon><Histogram /></el-icon>
              <span>后台管理</span>
            </template>
            <el-menu-item index="process-confirmation">
              <el-icon><Checked /></el-icon>
              <span>流程确认</span>
            </el-menu-item>
            <el-menu-item index="info-panel">
              <el-icon><DataAnalysis /></el-icon>
              <span>信息面板</span>
            </el-menu-item>
            
          </el-sub-menu>
          
          <!-- AI助手 -->
          <el-sub-menu index="ai-assistant">
            <template #title>
              <el-icon><ChatLineRound /></el-icon>
              <span>AI助手</span>
            </template>
            <el-menu-item index="smart-qa">
              <el-icon><ChatDotRound /></el-icon>
              <span>智能问答</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 主体内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Bell, 
  User, 
  UserFilled,
  ArrowDown, 
  Upload, 
  Monitor, 
  Cpu,
  Document, 
  DataLine, 
  List, 
  Calendar, 
  Histogram,
  Box,
  Tools,
  DataAnalysis,
  ChatLineRound,
  ChatDotRound,
  Checked
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const unreadCount = ref(0)
const isLogin = ref(true)

const activeMenu = computed(() => {
  const map = {
    '/worker-import': 'worker-data-import',
    // '/worker-cert-management': 'worker-cert-management',
    // '/worker-assessment-records': 'worker-assessment-records',
    '/device-import': 'device-data-import',
    // '/device-type-management': 'device-type-management',
    '/material-import': 'material-data-import',
    '/rule-import': 'rule-data-import',
    '/knowledge-structure-tree': 'knowledge-structure-tree',
    '/knowledge-extraction': 'knowledge-extraction',
    // 新增：搜索区路由映射
    '/search-area': 'search-area',
    '/dashboard': 'dashboard',
    '/gantt': 'gant',
    '/worker-management': 'worker-management',
    '/device-management': 'device-management',
    '/task-management': 'task-management',
    '/tool-management': 'tool-data-management',
    '/info-panel': 'info-panel',
    '/process-confirmation': 'process-confirmation',
    '/smart-qa': 'smart-qa'
  }
  return map[route.path] || 'dashboard'
})

const handleMenuSelect = (index) => {
  const map = {
    'worker-data-import': '/worker-import',
    // 'worker-cert-management': '/worker-cert-management',
    // 'worker-assessment-records': '/worker-assessment-records',
    'device-data-import': '/device-import',
    // 'device-type-management': '/device-type-management',
    'material-data-import': '/material-import',
    'rule-data-import': '/rule-import',
    'knowledge-structure-tree': '/knowledge-structure-tree',
    'knowledge-extraction': '/knowledge-extraction',
    // 新增：搜索区菜单点击映射
    'search-area': '/search-area',
    'dashboard': '/dashboard',
    'gant': '/gantt',
    'worker-management': '/worker-management',
    'device-management': '/device-management',
    'task-management': '/task-management',
    'tool-data-management': '/tool-management',
    'info-panel': '/info-panel',
    'process-confirmation': '/process-confirmation',
    'smart-qa': '/smart-qa'
  }
  
  if (map[index]) {
    router.push(map[index])
  }
}

const openNotify = () => {
  // 打开通知逻辑
}

const login = () => {
  // 登录逻辑
}

const logout = () => {
  // 退出登录逻辑
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
  overflow: hidden;
}

.main-header {
  background: #ffffff;
  /* 移除底边框，改用完全的阴影来分隔，避免和侧边栏的颜色碰撞 */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  position: relative; /* 在 Flex-column 中无需 sticky，用 relative 确保 z-index 层级即可 */
  z-index: 1000;
}

.brand {
  display: flex;
  align-items: center;
  height: 100%;
  gap: 12px; /* 控制图标和文字的间距 */
  min-width: 240px; /* 保证至少能和侧边栏对齐 */
  justify-content: flex-start;
  white-space: nowrap; /* 确保文字不换行 */
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
  width: auto; /* 移除固定宽度，让内容自然撑开 */
}

.title-zh {
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 2px; /* 调整中文间距 */
  background: linear-gradient(90deg, #1d4ed8, #3b82f6); /* 改为纯蓝色渐变：深蓝到亮蓝 */
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  text-align: left; /* 恢复左对齐 */
}

.title-en {
  font-size: 9px; /* 恢复英文大小 */
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.2px; /* 给英文一点点间距，使其看起来更舒展，且正好和中文总长度匹配 */
  line-height: 1;
  margin-top: 2px;
  font-family: 'Arial', sans-serif;
  white-space: nowrap;
}

.layout-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.main-sider {
  background: #2b3243; /* 将黑色调浅一点 */
  width: 240px;
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08); /* 调浅阴影 */
  transition: width 0.3s ease;
  z-index: 99; /* 保证在 header 之下，content 之上 */
}

.main-menu {
  border-right: none;
  height: 100%;
  padding: 16px 0;
  background-color: transparent;
}

/* 一级菜单：文字居中，整体居中布局 */
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
}

/* 二级菜单：稍靠右，与一级菜单形成层级差 */
:deep(.el-menu-item) {
  margin: 4px 12px 4px 12px !important;
  border: none;
  height: 48px;
  line-height: 48px;
  font-size: 14px;
  padding: 0 20px 0 60px !important; 
  border-radius: 8px !important;
  transition: all 0.2s ease;
  text-align: left;
  color: #a6b0c3 !important;
}

/* 选中状态优化 */
:deep(.el-menu-item.is-active) {
  background-color: #3b82f6 !important;
  color: #ffffff !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

/* 交互效果 */
:deep(.el-menu-item:hover:not(.is-active)) {
  background-color: #3b4255 !important;
  color: #ffffff !important;
}

:deep(.el-sub-menu__title:hover) {
  background-color: #3b4255 !important;
  color: #ffffff !important;
}

/* 修复子菜单展开时的背景色问题 */
:deep(.el-menu) {
  background-color: transparent !important;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  background-color: #f0f2f5;
  background-image: radial-gradient(#d1d5db 1px, transparent 1px);
  background-size: 24px 24px;
}

/* AI助手子菜单样式优化 */
:deep(.el-sub-menu__icon-arrow) {
  transition: transform 0.3s !important;
  right: 20px !important;
}

:deep(.el-menu-item) {
  width: auto;
  box-sizing: border-box;
}

/* 优雅的自定义滚动条 */
.main-sider::-webkit-scrollbar,
.main-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.main-sider::-webkit-scrollbar-thumb,
.main-content::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
}
.main-sider::-webkit-scrollbar-track,
.main-content::-webkit-scrollbar-track {
  background: transparent;
}
</style>