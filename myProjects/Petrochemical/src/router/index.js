import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
    }, 
    {
      path: '/main',
      name: 'MainLayout',
      component: () => import('../views/MainLayout.vue'),
      children: [
        {
          path: '/worker-import',
          name: 'WorkerImport',
          component: () => import('../views/WorkerImport.vue'),
        },
        // {
        //   path: '/worker-cert-management',
        //   name: 'WorkerCertManagement',
        //   component: () => import('../views/WorkerCertManagement.vue'),
        // },
        // {
        //   path: '/worker-assessment-records',
        //   name: 'WorkerAssessmentRecords',
        //   component: () => import('../views/WorkerAssessmentRecords.vue'),
        // },
        {
          path: '/device-import',
          name: 'DeviceImport',
          component: () => import('../views/DeviceImport.vue'),
        },
        // {
        //   path: '/device-type-management',
        //   name: 'DeviceTypeManagement',
        //   component: () => import('../views/DeviceTypeManagement.vue'),
        // },
        {
          path: '/material-import',
          name: 'MaterialImport',
          component: () => import('../views/MaterialImport.vue'),
        },
        {
          path: '/rule-import',
          name: 'RuleImport',
          component: () => import('../views/RuleImport.vue'),
        },
        {
          path: '/knowledge-structure-tree',
          name: 'KnowledgeStructureTree',
          component: () => import('../views/KnowledgeStructureTree.vue'),
        },
        {
          path: '/knowledge-extraction',
          name: 'KnowledgeExtraction',
          component: () => import('../views/KnowledgeExtraction.vue'),
        },
        {
          path: '/search-area',
          name: 'SearchArea',
          component: () => import('../views/SearchArea.vue'),
        },
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('../views/Home.vue'),
        },
        {
          path: '/gantt',
          name: 'Gantt',
          component: () => import('../views/GanttView.vue'),
        },
        {
          path: '/worker-management',
          name: 'WorkerManagement',
          component: () => import('../views/WorkerManagement.vue'),
        },
        {
          path: '/device-management',
          name: 'DeviceManagement',
          component: () => import('../views/DeviceManagement.vue'),
        },
        {
          path: '/task-management',
          name: 'TaskManagement',
          component: () => import('../views/TaskManagement.vue'),
        },
        {
          path: '/tool-management',
          name: 'ToolManagement',
          component: () => import('../views/ToolManagement.vue'),
        },
        {
          path: '/info-panel',
          name: 'InfoPanel',
          component: () => import('../views/InfoPanel.vue'),
        },
        {
          path: '/process-confirmation',
          name: 'ProcessConfirmation',
          component: () => import('../views/ProcessConfirmation.vue'),
        },
        {
          path: '/smart-qa',
          name: 'SmartQA',
          component: () => import('../views/SmartQA.vue'),
        }
      ]
    }
  ],
})

export default router