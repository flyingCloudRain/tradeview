<template>
  <div class="trader-view">
    <el-card>
      <template #header>
        <span>游资-营业部映射</span>
      </template>

      <el-table :data="tableData" :loading="loading" stripe border>
        <el-table-column prop="name" label="游资名称" min-width="200" />
        <el-table-column prop="aka" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="营业部列表" min-width="400">
          <template #default="{ row }">
            <div class="branch-list">
              <div v-for="b in row.branches" :key="b.id" class="branch-item">
                <span>{{ b.institution_name }}</span>
                <span v-if="b.institution_code" class="code">({{ b.institution_code }})</span>
              </div>
              <div v-if="!row.branches || row.branches.length === 0" class="text-gray">暂无</div>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useTraderStore } from '@/stores/trader'

const traderStore = useTraderStore()

const tableData = computed(() => traderStore.list)
const loading = computed(() => traderStore.loading)

onMounted(() => {
  traderStore.fetchList()
})
</script>

<style scoped>
.trader-view {
  padding: 20px;
}
.branch-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
}
.branch-item .code {
  color: #909399;
  margin-left: 4px;
}
.text-gray {
  color: #909399;
}
</style>

