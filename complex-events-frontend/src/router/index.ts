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
    path: '/404',
    component: EmptyPage,
    hidden: true,
  },
  {
    path: '/',
    redirect: '/worker/account',
    component: () => import('@/layout/index.vue'),
    meta: { title: '首页', icon: 'home', affix: true },
  },
  {
    path: '/worker',
    component: () => import('@/layout/index.vue'),
    redirect: '/worker/account',
    name: '工人管理',
    meta: { title: '工人管理' },
    children: [
      {
        path: '/worker/account',
        name: '工人台账',
        component: EmptyPage,
        meta: { title: '工人台账' },
      },
    ],
  },
  {
    path: '/equipment',
    component: () => import('@/layout/index.vue'),
    redirect: '/equipment/account',
    name: '设备管理',
    meta: { title: '设备管理' },
    children: [
      {
        path: '/equipment/account',
        name: '设备台账',
        component: EmptyPage,
        meta: { title: '设备台账' },
      },
    ],
  },
  {
    path: '/tools',
    component: () => import('@/layout/index.vue'),
    redirect: '/tools/account',
    name: '维修机具管理',
    meta: { title: '维修机具管理' },
    children: [
      {
        path: '/tools/account',
        name: '维修机具台账',
        component: EmptyPage,
        meta: { title: '维修机具台账' },
      },
    ],
  },
  {
    path: '/materials',
    component: () => import('@/layout/index.vue'),
    redirect: '/materials/account',
    name: '辅助材料管理',
    meta: { title: '辅助材料管理' },
    children: [
      {
        path: '/materials/account',
        name: '辅助材料台账',
        component: EmptyPage,
        meta: { title: '辅助材料台账' },
      },
    ],
  },
  {
    path: '/rules',
    component: () => import('@/layout/index.vue'),
    redirect: '/rules/library',
    name: '规则管理',
    meta: { title: '规则管理' },
    children: [
      {
        path: '/rules/library',
        name: '规则库',
        component: EmptyPage,
        meta: { title: '规则库' },
      },
      {
        path: '/rules/tree',
        name: '知识结构树',
        component: EmptyPage,
        meta: { title: '知识结构树' },
      },
      {
        path: '/rules/extraction',
        name: '知识提取',
        component: EmptyPage,
        meta: { title: '知识提取' },
      },
      {
        path: '/rules/search',
        name: '搜索区',
        component: EmptyPage,
        meta: { title: '搜索区' },
      },
    ],
  },
  {
    path: '/dispatch',
    component: () => import('@/layout/index.vue'),
    redirect: '/dispatch/worker',
    name: '调度数据管理',
    meta: { title: '调度数据管理' },
    children: [
      {
        path: '/dispatch/worker',
        name: '工人',
        component: () => import('@/views/SchedulingDataManagement/worker.vue'),
        meta: { title: '工人' },
      },
      {
        path: '/dispatch/equipment',
        name: '设备',
        component: EmptyPage,
        meta: { title: '设备' },
      },
      {
        path: '/dispatch/order',
        name: '工单',
        component: EmptyPage,
        meta: { title: '工单' },
      },
      {
        path: '/dispatch/generate',
        name: '调度生成',
        component: EmptyPage,
        meta: { title: '调度生成' },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layout/index.vue'),
    redirect: '/admin/flow',
    name: '后台管理',
    meta: { title: '后台管理' },
    children: [
      {
        path: '/admin/flow',
        name: '流程确认',
        component: EmptyPage,
        meta: { title: '流程确认' },
      },
      {
        path: '/admin/dashboard',
        name: '信息面板',
        component: EmptyPage,
        meta: { title: '信息面板' },
      },
      {
        path: '/admin/assistant',
        name: 'AI助手',
        component: EmptyPage,
        meta: { title: 'AI助手' },
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

const whiteList = ['/login']

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  document.title = getPageTitle(to.meta.title)
  const hasToken = getToken()
  const userStore = useUserStore()
  if (hasToken) {
    if (to.path === '/login') {
      next({ path: '/' })
      NProgress.done()
    } else if (userStore.name) {
      next()
    } else {
      try {
        await userStore.getInfo()
        next()
      } catch (error) {
        await userStore.resetToken()
        console.error('error', error)
        next(`/login?redirect=${to.path}`)
        NProgress.done()
      }
    }
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
