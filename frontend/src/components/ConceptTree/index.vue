<template>
  <el-tree
    :data="treeData"
    :props="treeProps"
    :default-expand-all="defaultExpandAll"
    :highlight-current="highlightCurrent"
    :node-key="nodeKey"
    @node-click="handleNodeClick"
    class="concept-tree"
  >
    <template #default="{ node, data }">
      <div class="tree-node">
        <span class="node-label">{{ data.name }}</span>
        <el-tag v-if="data.level" :type="getLevelTagType(data.level)" size="small" class="node-tag">
          {{ getLevelText(data.level) }}
        </el-tag>
        <span v-if="data.stock_count !== undefined" class="node-count">
          ({{ data.stock_count }})
        </span>
      </div>
    </template>
  </el-tree>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StockConcept } from '@/api/stockConcept'

interface Props {
  data?: StockConcept[]
  defaultExpandAll?: boolean
  highlightCurrent?: boolean
  nodeKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  defaultExpandAll: false,
  highlightCurrent: true,
  nodeKey: 'id',
})

const emit = defineEmits<{
  nodeClick: [data: StockConcept, node: any]
}>()

const treeProps = {
  children: 'children',
  label: 'name',
}

const treeData = computed(() => {
  return props.data || []
})

const getLevelText = (level: number) => {
  const map: Record<number, string> = { 1: '一级', 2: '二级', 3: '三级' }
  return map[level] || ''
}

const getLevelTagType = (level: number) => {
  const map: Record<number, string> = { 1: 'primary', 2: 'success', 3: 'warning' }
  return map[level] || ''
}

const handleNodeClick = (data: StockConcept, node: any) => {
  emit('nodeClick', data, node)
}
</script>

<style scoped lang="scss">
.concept-tree {
  .tree-node {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;

    .node-label {
      flex: 1;
    }

    .node-tag {
      margin-left: auto;
    }

    .node-count {
      color: #909399;
      font-size: 12px;
    }
  }
}
</style>
