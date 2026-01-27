import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard/index.vue'),
    meta: { title: '仪表盘' },
  },
  {
    path: '/lhb-institution',
    name: 'LhbInstitution',
    component: () => import('@/views/LhbHot/index.vue'),
    meta: { title: '龙虎榜' },
  },
  {
    path: '/zt-pool',
    name: 'ZtPool',
    component: () => import('@/views/ZtPool/index.vue'),
    meta: { title: '涨停池' },
  },
  {
    path: '/capital',
    name: 'Capital',
    component: () => import('@/views/Capital/index.vue'),
    meta: { title: '机构榜' },
  },
  {
    path: '/index',
    name: 'Index',
    component: () => import('@/views/Index/index.vue'),
    meta: { title: '大盘指数' },
  },
  {
    path: '/stock-fund-flow',
    name: 'StockFundFlow',
    component: () => import('@/views/StockFundFlow/index.vue'),
    meta: { title: '个股资金流' },
  },
  {
    path: '/concept-fund-flow',
    name: 'ConceptFundFlow',
    component: () => import('@/views/ConceptFundFlow/index.vue'),
    meta: { title: '概念资金流' },
  },
  {
    path: '/trading-calendar',
    name: 'TradingCalendar',
    component: () => import('@/views/TradingCalendar/index.vue'),
    meta: { title: '交易日历' },
  },
  {
    path: '/task',
    name: 'Task',
    component: () => import('@/views/Task/index.vue'),
    meta: { title: '任务管理' },
  },
  {
    path: '/stock-concept',
    name: 'StockConcept',
    component: () => import('@/views/StockConcept/index.vue'),
    meta: { title: '概念题材管理' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '交易复盘系统'}`
  
  // 如果访问交易日历页面但没有menu参数，默认跳转到calendar菜单
  if (to.path === '/trading-calendar' && !to.query.menu) {
    next({
      path: '/trading-calendar',
      query: { ...to.query, menu: 'calendar' }
    })
    return
  }
  
  next()
})

export default router

