<template>
  <div class="main-layout">
    <!-- 侧边栏导航 -->
    <aside class="sidebar">
      <div class="logo">
        <h2>员工系统</h2>
      </div>
      
      <nav class="nav-menu">
        <div 
          v-for="item in menuItems" 
          :key="item.key"
          :class="['nav-item', { active: activeKey === item.key }]"
          @click="handleMenuClick(item)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.label }}</span>
        </div>
      </nav>
      
      <div class="user-info">
        <div class="user-avatar">
          <span>👤</span>
        </div>
        <div class="user-details">
          <div class="user-name">员工 {{ employeeId }}</div>
          <button @click="logout" class="logout-btn">退出登录</button>
        </div>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const employeeId = ref('')

const menuItems = [
  {
    key: 'schedule',
    label: '我的排程',
    icon: '📅',
    path: '/schedule'
  },
  {
    key: 'work-report',
    label: '工况反馈',
    icon: '📝',
    path: '/work-report'
  }
]

const activeKey = computed(() => {
  const pathMap = {
    '/schedule': 'schedule',
    '/work-report': 'work-report'
  }
  return pathMap[route.path] || 'schedule'
})

onMounted(() => {
  // 检查登录状态
  const isLoggedIn = localStorage.getItem('isLoggedIn')
  employeeId.value = localStorage.getItem('employeeId') || 'EMP001'
  
  if (!isLoggedIn) {
    router.push('/login')
  }
})

const handleMenuClick = (item) => {
  router.push(item.path)
}

const logout = () => {
  localStorage.removeItem('isLoggedIn')
  localStorage.removeItem('employeeId')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  display: flex;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #f5f5f5;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background-color: #ffffff;
  color: #333333;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
  border-right: 1px solid #e0e0e0;
}

.logo {
  padding: 1.5rem;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
}

.logo h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333333;
}

.nav-menu {
  flex: 1;
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 0.25rem 0.75rem;
  border-radius: 8px;
  color: #333333;
}

.nav-item:hover {
  background-color: #f5f5f5;
  transform: translateX(5px);
}

.nav-item.active {
  background-color: #e3f2fd;
  color: #1976d2;
  box-shadow: 0 4px 15px rgba(25, 118, 210, 0.2);
}

.nav-icon {
  font-size: 1.2rem;
  margin-right: 1rem;
  width: 24px;
  text-align: center;
}

.nav-text {
  font-size: 1rem;
  font-weight: 500;
}

.user-info {
  padding: 1.5rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  color: #333333;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
  font-size: 1.2rem;
  color: #666666;
}

.user-details {
  flex: 1;
}

.user-name {
  font-weight: 500;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #333333;
}

.logout-btn {
  background: #f5f5f5;
  color: #666666;
  border: 1px solid #ddd;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #e0e0e0;
  color: #333333;
  border-color: #bbb;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 70px;
  }
  
  .logo h2,
  .nav-text,
  .user-details {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 1rem;
  }
  
  .user-info {
    justify-content: center;
    padding: 1rem;
  }
  
  .user-avatar {
    margin-right: 0;
  }
}
</style>