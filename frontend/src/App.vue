<template>
  <el-container class="app-container">
    <el-aside class="app-aside">
      <div class="app-logo">
        <h1 class="app-title">交易复盘系统</h1>
      </div>
      <NavMenu />
    </el-aside>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import NavMenu from '@/components/Layout/NavMenu.vue'
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: row;
}

.app-aside {
  width: 220px !important;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
}

.app-logo {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fff;
  flex-shrink: 0;
}

.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
  padding-bottom: 60px; /* 增加底部padding，确保分页组件不被截断 */
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  min-height: 0; /* 允许flex子元素缩小 */
  box-sizing: border-box;
}

/* 确保分页组件有足够的显示空间，并右对齐 */
:deep(.el-pagination) {
  margin-top: 20px;
  margin-bottom: 20px;
  padding: 10px 0;
  flex-shrink: 0; /* 防止分页组件被压缩 */
  display: flex;
  justify-content: flex-end;
}

/* 减少 el-card__header 的上下空白 */
:deep(.el-card__header) {
  --el-card-padding: 12px;
  padding: 12px !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-aside {
    width: 180px !important;
  }
  
  .app-title {
    font-size: 16px;
  }
}
</style>

