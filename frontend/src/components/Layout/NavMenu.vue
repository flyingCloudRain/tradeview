<template>
  <el-menu
    :default-active="activeMenu"
    class="nav-menu"
    mode="horizontal"
    router
  >
    <el-menu-item index="/dashboard">
      <el-icon><Odometer /></el-icon>
      <span>仪表盘</span>
    </el-menu-item>
    <el-menu-item index="/lhb">
      <el-icon><Trophy /></el-icon>
      <span>龙虎榜</span>
    </el-menu-item>
    <el-menu-item index="/lhb-institution">
      <el-icon><User /></el-icon>
      <span>机构榜</span>
    </el-menu-item>
    <el-menu-item index="/zt-pool">
      <el-icon><TrendCharts /></el-icon>
      <span>涨停池</span>
    </el-menu-item>
    <el-menu-item index="/index">
      <el-icon><DataLine /></el-icon>
      <span>大盘指数</span>
    </el-menu-item>
    <el-menu-item index="/stock-fund-flow">
      <el-icon><Money /></el-icon>
      <span>资金流</span>
    </el-menu-item>
    <el-menu-item index="/trader">
      <el-icon><User /></el-icon>
      <span>机构映射</span>
    </el-menu-item>
    <el-menu-item index="/trading-calendar">
      <el-icon><Calendar /></el-icon>
      <span>交易日历</span>
    </el-menu-item>
    <el-menu-item index="/task">
      <el-icon><Setting /></el-icon>
      <span>任务管理</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Odometer,
  Trophy,
  TrendCharts,
  User,
  DataLine,
  Grid,
  Money,
  Calendar,
  Setting,
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.nav-menu {
  border-bottom: 1px solid #e4e7ed;
}
</style>

