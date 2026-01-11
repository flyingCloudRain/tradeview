<template>
  <el-container>
    <el-header class="app-header">
      <div class="header-content">
        <h1 class="app-title">交易复盘系统</h1>
        <NavMenu />
      </div>
    </el-header>
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
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
  height: auto;
}

.header-content {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.app-title {
  margin: 0;
  padding: 16px 20px;
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
}

.app-main {
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
  padding: 10px;
}
</style>

