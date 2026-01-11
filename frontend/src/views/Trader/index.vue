<template>
  <div class="trader-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>游资机构</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增游资
          </el-button>
        </div>
      </template>

      <el-table :data="tableData" :loading="loading" stripe border>
        <el-table-column prop="name" label="游资名称" width="150" />
        <el-table-column prop="aka" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="营业部列表" min-width="400">
          <template #default="{ row }">
            <div class="branch-list">
              <el-tag
                v-for="b in row.branches"
                :key="b.id"
                class="branch-tag"
                closable
                @close="handleDeleteBranch(row, b)"
                @click="handleEditBranch(row, b)"
                style="cursor: pointer"
              >
                {{ b.institution_name }}
                <span v-if="b.institution_code" class="code">({{ b.institution_code }})</span>
              </el-tag>
              <el-button
                text
                type="primary"
                size="small"
                @click="handleAddBranch(row)"
              >
                <el-icon><Plus /></el-icon>
                添加机构
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 游资编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="游资名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入游资名称" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="aka">
          <el-input
            v-model="formData.aka"
            type="textarea"
            :rows="4"
            placeholder="请输入游资描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="关联机构">
          <div class="branch-input-list">
            <div v-for="(branch, index) in formData.branches" :key="index" class="branch-input-item">
              <el-input
                v-model="formData.branches[index]"
                placeholder="请输入机构名称"
                style="flex: 1"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeBranchInput(index)"
              />
            </div>
            <el-button type="primary" text @click="addBranchInput">
              <el-icon><Plus /></el-icon>
              添加机构
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 机构编辑对话框 -->
    <el-dialog
      v-model="branchDialogVisible"
      :title="branchDialogTitle"
      width="500px"
      @close="handleBranchDialogClose"
    >
      <el-form
        ref="branchFormRef"
        :model="branchFormData"
        :rules="branchFormRules"
        label-width="100px"
      >
        <el-form-item label="机构名称" prop="institution_name">
          <el-input
            v-model="branchFormData.institution_name"
            placeholder="请输入机构名称"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="机构代码" prop="institution_code">
          <el-input
            v-model="branchFormData.institution_code"
            placeholder="请输入机构代码（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="branchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBranchSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, reactive } from 'vue'
import { ElMessageBox, ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { useTraderStore } from '@/stores/trader'
import type { TraderItem, TraderBranch } from '@/api/trader'

const traderStore = useTraderStore()

const tableData = computed(() => traderStore.list)
const loading = computed(() => traderStore.loading)

// 游资对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增游资')
const isEdit = ref(false)
const currentTraderId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  name: '',
  aka: '',
  branches: [''] as string[],
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入游资名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' },
  ],
  aka: [
    { max: 1000, message: '最多 1000 个字符', trigger: 'blur' },
  ],
}

// 机构对话框
const branchDialogVisible = ref(false)
const branchDialogTitle = ref('添加机构')
const isBranchEdit = ref(false)
const currentTrader = ref<TraderItem | null>(null)
const currentBranchId = ref<number | null>(null)
const branchFormRef = ref<FormInstance>()

const branchFormData = reactive({
  institution_name: '',
  institution_code: '',
})

const branchFormRules: FormRules = {
  institution_name: [
    { required: true, message: '请输入机构名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' },
  ],
  institution_code: [
    { max: 50, message: '最多 50 个字符', trigger: 'blur' },
  ],
}

// 创建游资
const handleCreate = () => {
  dialogTitle.value = '新增游资'
  isEdit.value = false
  currentTraderId.value = null
  formData.name = ''
  formData.aka = ''
  formData.branches = ['']
  dialogVisible.value = true
}

// 编辑游资
const handleEdit = (row: TraderItem) => {
  dialogTitle.value = '编辑游资'
  isEdit.value = true
  currentTraderId.value = row.id
  formData.name = row.name
  formData.aka = row.aka || ''
  formData.branches = []
  dialogVisible.value = true
}

// 删除游资
const handleDelete = async (row: TraderItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除游资 "${row.name}" 吗？删除后将同时删除所有关联的机构。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await traderStore.deleteTrader(row.id)
  } catch (e) {
    // 用户取消
  }
}

// 添加机构
const handleAddBranch = (row: TraderItem) => {
  branchDialogTitle.value = '添加机构'
  isBranchEdit.value = false
  currentTrader.value = row
  currentBranchId.value = null
  branchFormData.institution_name = ''
  branchFormData.institution_code = ''
  branchDialogVisible.value = true
}

// 编辑机构
const handleEditBranch = (row: TraderItem, branch: TraderBranch) => {
  branchDialogTitle.value = '编辑机构'
  isBranchEdit.value = true
  currentTrader.value = row
  currentBranchId.value = branch.id
  branchFormData.institution_name = branch.institution_name
  branchFormData.institution_code = branch.institution_code || ''
  branchDialogVisible.value = true
}

// 删除机构
const handleDeleteBranch = async (row: TraderItem, branch: TraderBranch) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除机构 "${branch.institution_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await traderStore.deleteBranch(row.id, branch.id)
  } catch (e) {
    // 用户取消
  }
}

// 提交游资表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 过滤空字符串
      const branches = formData.branches.filter(b => b.trim())
      
      if (isEdit.value && currentTraderId.value) {
        await traderStore.updateTrader(currentTraderId.value, {
          name: formData.name,
          aka: formData.aka || undefined,
        })
      } else {
        await traderStore.createTrader({
          name: formData.name,
          aka: formData.aka || undefined,
          branches: branches,
        })
      }
      dialogVisible.value = false
    } catch (e) {
      // 错误已在store中处理
    } finally {
      submitting.value = false
    }
  })
}

// 提交机构表单
const handleBranchSubmit = async () => {
  if (!branchFormRef.value || !currentTrader.value) return
  
  await branchFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isBranchEdit.value && currentBranchId.value) {
        await traderStore.updateBranch(
          currentTrader.value.id,
          currentBranchId.value,
          {
            institution_name: branchFormData.institution_name,
            institution_code: branchFormData.institution_code || undefined,
          }
        )
      } else {
        await traderStore.addBranch(currentTrader.value.id, {
          institution_name: branchFormData.institution_name,
          institution_code: branchFormData.institution_code || undefined,
        })
      }
      branchDialogVisible.value = false
    } catch (e) {
      // 错误已在store中处理
    } finally {
      submitting.value = false
    }
  })
}

// 对话框关闭
const handleDialogClose = () => {
  formRef.value?.resetFields()
  formData.branches = ['']
}

const handleBranchDialogClose = () => {
  branchFormRef.value?.resetFields()
}

// 添加机构输入框
const addBranchInput = () => {
  formData.branches.push('')
}

// 删除机构输入框
const removeBranchInput = (index: number) => {
  formData.branches.splice(index, 1)
  if (formData.branches.length === 0) {
    formData.branches.push('')
  }
}

onMounted(() => {
  traderStore.fetchList()
})
</script>

<style scoped>
.trader-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.branch-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.branch-tag {
  margin-right: 4px;
}

.branch-tag .code {
  color: #909399;
  margin-left: 4px;
}

.text-gray {
  color: #909399;
}

.branch-input-list {
  width: 100%;
}

.branch-input-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>
