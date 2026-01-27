<template>
  <div class="lhb-sidebar">
    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      @select="handleMenuSelect"
    >
      <!-- 机构交易统计 -->
      <el-menu-item index="statistics">
        <el-icon><DataAnalysis /></el-icon>
        <span>机构交易统计</span>
      </el-menu-item>

      <!-- 活跃营业部 -->
      <el-menu-item index="activeBranch">
        <el-icon><OfficeBuilding /></el-icon>
        <span>活跃营业部</span>
      </el-menu-item>

      <!-- 上榜个股 -->
      <el-menu-item index="stocks">
        <el-icon><Trophy /></el-icon>
        <span>上榜个股</span>
      </el-menu-item>

      <!-- 上榜个股机构明细 -->
      <el-menu-item index="detail">
        <el-icon><Document /></el-icon>
        <span>上榜个股机构明细</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  DataAnalysis,
  OfficeBuilding,
  Trophy,
  Document,
} from '@element-plus/icons-vue'

interface Props {
  modelValue: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'menu-change': [menu: { main: string; sub?: string }]
}>()

const activeMenu = ref(props.modelValue || 'statistics')

// 监听外部传入的值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    // 如果传入的是3级菜单（如 statistics-chart），提取2级菜单名
    const mainMenu = newVal.split('-')[0]
    activeMenu.value = mainMenu
  }
}, { immediate: true })

// 监听内部值变化，同步到外部
watch(activeMenu, (newVal) => {
  emit('update:modelValue', newVal)
  // 发送主菜单信息（没有子菜单，因为3级菜单用tabs显示）
  emit('menu-change', { main: newVal })
})

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
}
</script>

<style scoped lang="scss">
.lhb-sidebar {
  width: 220px;
  min-width: 220px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  height: 100%;
  overflow-y: auto;
  flex-shrink: 0;

  .sidebar-menu {
    border-right: none;
    height: 100%;
    background-color: transparent;

    // 菜单项
    :deep(.el-menu-item) {
      height: 40px;
      line-height: 40px;
      font-size: 14px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      margin: 0;
      padding: 0 16px !important;
      color: rgba(0, 0, 0, 0.85);
    }

    // 图标样式
    :deep(.el-icon) {
      margin-right: 12px;
      font-size: 16px;
      width: 16px;
      transition: all 0.2s ease;
    }

    // 菜单项悬停效果
    :deep(.el-menu-item) {
      &:hover {
        background-color: rgba(0, 0, 0, 0.06);
        color: rgba(0, 0, 0, 0.85);
      }
    }

    // 激活的菜单项 - Ant Design Pro 风格
    :deep(.el-menu-item.is-active) {
      background-color: #e6f7ff;
      color: #1890ff;
      font-weight: 500;
      position: relative;
      
      // 左侧蓝色指示条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background-color: #1890ff;
      }
      
      .el-icon {
        color: #1890ff;
      }
    }

    // 移除默认的边框
    :deep(.el-menu-item) {
      border-bottom: none;
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .lhb-sidebar {
    width: 180px;
    min-width: 180px;
  }
}
</style>
