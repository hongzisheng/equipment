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
    redirect: '/data/upload',
    component: () => import('@/layout/index.vue'),
    meta: { title: '首页', icon: 'home', affix: true },
  },
  {
    path: '/data',
    component: () => import('@/layout/index.vue'),
    redirect: '/data/upload',
    name: '数据管理',
    meta: { title: '数据管理', icon: 'data' },
    children: [
      {
        path: '/data/upload',
        name: '数据上传',
        component: () => import('@/views/data/DataManage/index.vue'),
        meta: { title: '数据上传', icon: 'table' },
      },
      {
        path: '/data/dataCollectTemplate',
        name: '动态数据采集模板自动构建',
        component: EmptyPage,
        meta: { title: '动态数据采集模板自动构建', icon: 'tree' },
      },
      {
        path: '/data/DataSourceAcquisition',
        name: '弱信息下的数据源获取',
        component: EmptyPage,
        meta: { title: '弱信息下的数据源获取', icon: 'tree' },
      },
      {
        path: '/data/acquisition',
        name: '数据获取',
        component: EmptyPage,
        meta: { title: '数据获取', icon: 'tree' },
      },
    ],
  },
  {
    path: '/ontology',
    component: () => import('@/layout/index.vue'),
    redirect: '/ontology/list',
    name: '本体管理',
    meta: { title: '本体管理', icon: 'ontology' },
    children: [
      {
        path: '/ontology/define',
        name: '本体定义',
        component: EmptyPage,
        meta: { title: '本体定义', icon: 'table' },
      },
      {
        path: '/ontology/extract',
        name: '事件本体批量生成',
        component: EmptyPage,
        meta: { title: '事件本体批量生成', icon: 'extract' },
      },
      {
        path: '/ontology/list',
        name: '事件列表',
        component: () => import('@/views/ontology/eventsList/index.vue'),
        meta: { title: '事件列表', icon: 'list' },
      },
      {
        path: '/ontology/graphManage',
        name: '基于图的事件关联要素可视化',
        component: () => import('@/views/ontology/graphManage/index.vue'),
        meta: { title: '基于图的事件关联要素可视化', icon: 'knowledgeGraph' },
      },
      {
        path: '/ontology/cluster',
        name: '图聚类',
        component: EmptyPage,
        meta: { title: '图聚类', icon: 'cluster' },
      },
      {
        path: '/ontology/subGraph',
        name: '子图管理',
        component: EmptyPage,
        meta: { title: '子图管理', icon: 'subGraph' },
      },
    ],
  },
  {
    path: '/analysis',
    component: () => import('@/layout/index.vue'),
    redirect: '/analysis/map',
    name: '事件分析',
    meta: { title: '事件分析', icon: 'analysis' },
    children: [
      {
        path: '/analysis/map',
        name: '地理信息结合的事件可视化',
        component: EmptyPage,
        meta: { title: '地理信息结合的事件可视化', icon: 'map' },
      },
      {
        path: '/analysis/association',
        name: '关联分析',
        component: EmptyPage,
        meta: { title: '关联分析', icon: 'associate' },
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
