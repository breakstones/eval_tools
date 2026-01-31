import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/cases',
    },
    {
      path: '/cases',
      name: 'CaseManagement',
      component: () => import('@/views/CaseManagement.vue'),
    },
    {
      path: '/evaluation',
      name: 'Evaluation',
      component: () => import('@/views/Evaluation.vue'),
    },
    {
      path: '/models',
      name: 'ModelManagement',
      component: () => import('@/views/ModelManagement.vue'),
    },
    {
      path: '/evaluators',
      name: 'EvaluatorManagement',
      component: () => import('@/views/EvaluatorManagement.vue'),
    },
  ],
})

export default router
