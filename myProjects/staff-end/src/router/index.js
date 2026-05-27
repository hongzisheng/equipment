import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Schedule from '../views/Schedule.vue'
import WorkReport from '../views/WorkReport.vue'
import MainLayout from '../components/MainLayout.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/main',
    component: MainLayout,
    children: [
      {
        path: '/schedule',
        name: 'Schedule',
        component: Schedule
      },
      {
        path: '/work-report',
        name: 'WorkReport',
        component: WorkReport
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router