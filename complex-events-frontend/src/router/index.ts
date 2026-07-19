import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import * as NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
import getPageTitle from '@/utils/get-page-title'
import { useUserStore } from '@/stores/user.js'
import { Component } from 'vue'

export type RouteItem = RouteRecordRaw & {
  path: string
  name?: string
  redirect?: string
  component?: Component
  hidden?: boolean
  meta?: {
    title: string
    icon?: string
    affix?: boolean
  }
  children?: RouteItem[]
}

const EmptyPage = () => import('@/views/empty/index.vue')

export const constantRoutes: RouteItem[] = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    hidden: true,
  },
  {
    path: '/register',
    component: () => import('@/views/register/index.vue'),
    hidden: true,
  },
  {
    path: '/404',
    component: EmptyPage,
    hidden: true,
  },
  {
    path: '/home',
    component: () => import('@/layout/index.vue'),
    hidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/worker/account/index.vue'),
        meta: { title: '首页' },
      },
    ],
  },
  {
    path: '/',
    redirect: '/home',
    component: () => import('@/layout/index.vue'),
    meta: { title: '首页', icon: 'home', affix: true },
},
  {
    path: '/worker',
    component: () => import('@/layout/index.vue'),
    redirect: '/worker/account',
    name: '工人管理',
    meta: { title: '工人管理', icon: 'worker' },
    children: [
      {
        path: '/worker/account',
        name: '工人台账',
        component: () => import('@/views/worker/account/index.vue'),
        meta: { title: '工人台账' },
      },
    ],
  },
  {
    path: '/equipment',
    component: () => import('@/layout/index.vue'),
    redirect: '/equipment/account',
    name: '设备管理',
    meta: { title: '设备管理', icon: 'equipment' },
    children: [
      {
        path: '/equipment/account',
        name: '设备台账',
        component: () => import('@/views/equipment/account/index.vue'),
        meta: { title: '设备台账' },
      },
    ],
  },
  {
    path: '/tools',
    component: () => import('@/layout/index.vue'),
    redirect: '/tools/account',
    name: '维修机具管理',
    meta: { title: '维修机具管理', icon: 'tools' },
    children: [
      {
        path: '/tools/account',
        name: '维修机具台账',
        component: () => import('@/views/tools/account/index.vue'),
        meta: { title: '维修机具台账' },
      },
    ],
  },
  {
    path: '/materials',
    component: () => import('@/layout/index.vue'),
    redirect: '/materials/account',
    name: '辅助材料管理',
    meta: { title: '辅助材料管理', icon: 'material' },
    children: [
      {
        path: '/materials/account',
        name: '辅助材料台账',
        component: () => import('@/views/materials/account/index.vue'),
        meta: { title: '辅助材料台账' },
      },
    ],
  },
  {
    path: '/rules',
    component: () => import('@/layout/index.vue'),
    redirect: '/rules/library',
    name: '规则管理',
    meta: { title: '规则管理', icon: 'rule' },
    children: [
      {
        path: '/rules/library',
        name: '规则库',
        component: () => import('@/views/rules/rulebase/index.vue'),
        meta: { title: '规则库' },
      },
      {
        path: '/rules/tree',
        name: '知识结构树',
        component: () => import('@/views/rules/structuretree/index.vue'),
        meta: { title: '知识结构树' },
      },
      {
        path: '/rules/extraction',
        name: '知识提取',
        component: () => import('@/views/rules/extraction/index.vue'),
        meta: { title: '知识提取' },
      },
      {
        path: '/rules/search',
        name: '搜索区',
        component: () => import('@/views/rules/search/index.vue'),
        meta: { title: '搜索区' },
      },
      {
        path: '/rules/file',
        name: '文件管理',
        component: () => import('@/views/rules/file/index.vue'),
        meta: { title: '文件管理' },
      },
    ],
  },
  {
    path: '/dispatch',
    component: () => import('@/layout/index.vue'),
    redirect: '/dispatch/worker',
    name: '调度数据管理',
    meta: { title: '调度数据管理', icon: 'dispatch' },
    children: [
      {
        path: '/dispatch/worker',
        name: '工人',
        component: () => import('@/views/scheduling/worker/index.vue'),
        meta: { title: '工人', icon: 'user' },
      },
      {
        path: '/dispatch/order',
        name: '工单',
        component: () => import('@/views/scheduling/order/index.vue'),
        meta: { title: '工单', icon: 'list' },
      },
      {
        path: '/dispatch/generate',
        name: '调度生成',
        component: () => import('@/views/scheduling/schedule/index.vue'),
        meta: { title: '调度生成', icon: 'calendar' },
      },
    ],
  },
  {
    path: '/maintenance-plan',
    component: () => import('@/layout/index.vue'),
    redirect: '/maintenance-plan/list',
    name: '检修计划管理',
    meta: { title: '检修计划管理' },
    children: [
      {
        path: '/maintenance-plan/list',
        name: '检修计划列表',
        component: () => import('@/views/maintenance-plan/index.vue'),
        meta: { title: '检修计划列表' },
      },
      {
        path: '/maintenance-plan/create',
        name: '新建检修计划',
        component: () => import('@/views/maintenance-plan/CreateOrEdit.vue'),
        meta: { title: '新建检修计划' },
        hidden: true,
      },
      {
        path: '/maintenance-plan/edit/:id',
        name: '编辑检修计划',
        component: () => import('@/views/maintenance-plan/CreateOrEdit.vue'),
        meta: { title: '编辑检修计划' },
        hidden: true,
      },
      {
        path: '/maintenance-plan/detail/:id',
        name: '检修计划详情',
        component: () => import('@/views/maintenance-plan/Detail.vue'),
        meta: { title: '检修计划详情' },
        hidden: true,
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layout/index.vue'),
    redirect: '/admin/flow',
    name: '后台管理',
    meta: { title: '后台管理', icon: 'admin' },
    children: [
      {
        path: '/admin/flow',
        name: '流程确认',
        component: () => import('@/views/ProcessConfirmation/index.vue'),
        meta: { title: '流程确认', icon: 'checked' },
      },
      {
        path: '/admin/dashboard',
        name: '信息面板',
        component: () => import('@/views/InfoPanel/index.vue'),
        meta: { title: '信息面板', icon: 'data-analysis' },
      },
    ],
  },
  {
    path: '/assistant',
    component: () => import('@/layout/index.vue'),
    redirect: '/assistant/qa',
    name: 'AI助手',
    meta: { title: 'AI助手', icon: 'assistant' },
    children: [
      {
        path: '/assistant/qa',
        name: '智能问答',
        component: () => import('@/views/SmartQA/index.vue'),
        meta: { title: '智能问答', icon: 'chat-dot-round' },
      },
    ],
  },
  {
    path: '/employee',
    component: () => import('@/views/employee/EmployeeLayout.vue'),
    redirect: '/employee/schedule',
    name: '员工端',
    meta: { title: '员工端', role: 'worker' },
    hidden: true,
    children: [
      {
        path: 'schedule',
        name: 'StaffSchedule',
        component: () => import('@/views/employee/Schedule.vue'),
        meta: { title: '我的排程', role: 'worker' },
      },
      {
        path: 'work-report',
        name: 'StaffWorkReport',
        component: () => import('@/views/employee/WorkReport.vue'),
        meta: { title: '工况反馈', role: 'worker' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    hidden: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes: constantRoutes,
})

NProgress.configure({ showSpinner: false })

const whiteList = ['/login', '/register']

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  document.title = getPageTitle(to.meta.title)
  const hasToken = getToken()
  const userStore = useUserStore()
  //开发者模式下跳过登录
  // if (import.meta.env.DEV) {
  //   next()
  //   NProgress.done()
  //   return
  // }
  if (hasToken) {
    if (to.path === '/login') {
      // 登录页始终放行，不拦截
      next()
      NProgress.done()
      return
    }
    // 确保用户信息已加载
    if (!userStore.name) {
      try {
        await userStore.getInfo()
      } catch (error) {
        await userStore.resetToken()
        console.error('error', error)
        next(`/login?redirect=${to.path}`)
        NProgress.done()
        return
      }
    }
    // 角色权限守卫
    const isWorker = userStore.role === 'worker'
    const isAdmin = userStore.role === 'admin'
    const isEmployeePath = to.path.startsWith('/employee')

    if (isWorker && !isEmployeePath) {
      // 员工只能访问员工端
      next('/employee/schedule')
      NProgress.done()
      return
    }
    if (isAdmin && isEmployeePath) {
      // 管理员不能访问员工端
      next('/home')
      NProgress.done()
      return
    }
    next()
  } else if (whiteList.includes(to.path)) {
    next()
  } else {
    next(`/login?redirect=${to.path}`)
    NProgress.done()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
