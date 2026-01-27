<template>
  <el-menu
    :default-active="activeMenu"
    class="nav-menu"
    mode="vertical"
    router
    :default-openeds="defaultOpeneds"
    unique-opened
    @open="handleSubMenuOpen"
    @close="handleSubMenuClose"
    @select="handleMenuSelect"
  >
    <el-menu-item index="/dashboard">
      <el-icon><Odometer /></el-icon>
      <span>仪表盘</span>
    </el-menu-item>
    <el-menu-item index="/index">
      <el-icon><DataLine /></el-icon>
      <span>大盘指数</span>
    </el-menu-item>
    <!-- 资金流 - 2级菜单 -->
    <el-sub-menu index="fund-flow">
      <template #title>
        <el-icon><Money /></el-icon>
        <span>资金流</span>
      </template>
      <el-menu-item index="/stock-fund-flow">
        <el-icon><Money /></el-icon>
        <span>个股资金流</span>
      </el-menu-item>
      <el-menu-item index="/concept-fund-flow">
        <el-icon><Money /></el-icon>
        <span>概念资金流</span>
      </el-menu-item>
    </el-sub-menu>
    <el-menu-item index="/zt-pool">
      <el-icon><TrendCharts /></el-icon>
      <span>涨停榜</span>
    </el-menu-item>
    <!-- 龙虎榜 - 2级菜单 -->
    <el-sub-menu index="lhb">
      <template #title>
        <el-icon><User /></el-icon>
        <span>龙虎榜</span>
      </template>
      <el-menu-item index="/lhb-institution?menu=statistics">
        <el-icon><DataAnalysis /></el-icon>
        <span>机构交易统计</span>
      </el-menu-item>
      <el-menu-item index="/lhb-institution?menu=activeBranch">
        <el-icon><OfficeBuilding /></el-icon>
        <span>活跃营业部</span>
      </el-menu-item>
      <el-menu-item index="/lhb-institution?menu=stocks">
        <el-icon><Trophy /></el-icon>
        <span>上榜个股</span>
      </el-menu-item>
      <el-menu-item index="/lhb-institution?menu=detail">
        <el-icon><Document /></el-icon>
        <span>上榜个股机构明细</span>
      </el-menu-item>
    </el-sub-menu>
    <!-- 交易日历 - 2级菜单 -->
    <el-sub-menu index="trading-calendar">
      <template #title>
        <el-icon><Calendar /></el-icon>
        <span>交易日历</span>
      </template>
      <el-menu-item index="/trading-calendar?menu=calendar">
        <el-icon><Calendar /></el-icon>
        <span>交易日历</span>
      </el-menu-item>
      <el-menu-item index="/trading-calendar?menu=my-calendar">
        <el-icon><User /></el-icon>
        <span>我的日历</span>
      </el-menu-item>
    </el-sub-menu>
    <el-menu-item index="/stock-concept">
      <el-icon><Grid /></el-icon>
      <span>概念题材</span>
    </el-menu-item>
    <el-menu-item index="/task">
      <el-icon><Setting /></el-icon>
      <span>任务管理</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer,
  TrendCharts,
  User,
  DataLine,
  Grid,
  Money,
  Calendar,
  Setting,
  DataAnalysis,
  OfficeBuilding,
  Trophy,
  Document,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => {
  // 对于龙虎榜页面，需要包含查询参数来正确激活对应的菜单项
  if (route.path === '/lhb-institution' && route.query.menu) {
    return `${route.path}?menu=${route.query.menu}`
  }
  // 对于交易日历页面，需要包含查询参数来正确激活对应的菜单项
  if (route.path === '/trading-calendar' && route.query.menu) {
    return `${route.path}?menu=${route.query.menu}`
  }
  return route.path
})

// 处理菜单选择，确保查询参数被正确传递
const handleMenuSelect = (index: string) => {
  // 如果包含查询参数，使用编程式导航
  if (index.includes('?')) {
    const [path, queryString] = index.split('?')
    const params = new URLSearchParams(queryString)
    const query: Record<string, string> = {}
    params.forEach((value, key) => {
      query[key] = value
    })
    router.push({ path, query })
  }
}

const defaultOpeneds = ref<string[]>([])

// 根据当前路由自动展开对应的父菜单
watch(activeMenu, (path) => {
  if (path.startsWith('/lhb')) {
    if (!defaultOpeneds.value.includes('lhb')) {
      defaultOpeneds.value = ['lhb']
    }
  } else if (path.startsWith('/trading-calendar')) {
    if (!defaultOpeneds.value.includes('trading-calendar')) {
      defaultOpeneds.value = ['trading-calendar']
    }
  } else if (path.startsWith('/stock-fund-flow') || path.startsWith('/concept-fund-flow')) {
    if (!defaultOpeneds.value.includes('fund-flow')) {
      defaultOpeneds.value = ['fund-flow']
    }
  } else {
    // 如果不在相关页面，可以收起菜单
    const lhbIdx = defaultOpeneds.value.indexOf('lhb')
    if (lhbIdx > -1) {
      defaultOpeneds.value.splice(lhbIdx, 1)
    }
    const tradingCalendarIdx = defaultOpeneds.value.indexOf('trading-calendar')
    if (tradingCalendarIdx > -1) {
      defaultOpeneds.value.splice(tradingCalendarIdx, 1)
    }
    const fundFlowIdx = defaultOpeneds.value.indexOf('fund-flow')
    if (fundFlowIdx > -1) {
      defaultOpeneds.value.splice(fundFlowIdx, 1)
    }
  }
}, { immediate: true })

// 手风琴模式：打开子菜单时，只保留当前打开的菜单
const handleSubMenuOpen = (index: string) => {
  defaultOpeneds.value = [index]
}

const handleSubMenuClose = (index: string) => {
  const idx = defaultOpeneds.value.indexOf(index)
  if (idx > -1) {
    defaultOpeneds.value.splice(idx, 1)
  }
}
</script>

<style scoped lang="scss">
.nav-menu {
  border-right: none;
  height: calc(100vh - 80px);
  overflow-y: auto;

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    height: 50px;
    line-height: 50px;
    font-size: 14px;
  }

  :deep(.el-icon) {
    margin-right: 8px;
    font-size: 18px;
  }

  :deep(.el-menu-item.is-active) {
    background-color: #ecf5ff;
    color: #409eff;
  }

  :deep(.el-sub-menu.is-active .el-sub-menu__title) {
    color: #409eff;
  }

  // 子菜单展开箭头 - 确保箭头始终显示
  :deep(.el-sub-menu__icon-arrow) {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin: 0;
  }

  // 默认状态：箭头向右（▶）
  :deep(.el-sub-menu:not(.is-opened) > .el-sub-menu__title .el-sub-menu__icon-arrow) {
    transform: translateY(-50%) rotate(0deg);
  }

  // 展开状态：箭头向下（▼）
  :deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
    transform: translateY(-50%) rotate(90deg);
    color: rgba(0, 0, 0, 0.85);
  }

  // 确保子菜单标题有相对定位，以便箭头绝对定位
  :deep(.el-sub-menu__title) {
    position: relative;
    padding-right: 40px !important;
  }

  // 子菜单项样式
  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 50px !important;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-menu {
    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      height: 44px;
      line-height: 44px;
      font-size: 13px;
    }

    :deep(.el-icon) {
      font-size: 16px;
    }
  }
}
</style>

