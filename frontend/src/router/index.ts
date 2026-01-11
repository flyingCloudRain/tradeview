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
    path: '/lhb',
    name: 'Lhb',
    component: () => import('@/views/Lhb/List.vue'),
    meta: { title: '龙虎榜' },
  },
  {
    path: '/lhb-institution',
    name: 'LhbInstitution',
    component: () => import('@/views/LhbHot/index.vue'),
    meta: { title: '机构榜' },
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
    component: () => import('@/views/FundFlow/index.vue'),
    meta: { title: '资金流' },
  },
  {
    path: '/trader',
    name: 'Trader',
    component: () => import('@/views/Trader/index.vue'),
    meta: { title: '游资映射' },
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '交易复盘系统'}`
  next()
})

export default router

