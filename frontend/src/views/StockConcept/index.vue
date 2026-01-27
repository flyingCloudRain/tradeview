<template>
  <div class="stock-concept-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon class="title-icon"><Collection /></el-icon>
            <span>概念题材管理</span>
          </div>
          <el-button type="primary" :icon="Plus" @click="handleCreate">新增概念</el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 概念列表 -->
        <el-col :span="24">
          <el-card shadow="hover" class="concept-list-card">
            <template #header>
              <div class="filter-header">
                <div class="filter-left">
                  <el-input
                    v-model="filterForm.name"
                    placeholder="搜索概念名称"
                    clearable
                    @clear="loadTree"
                    @keyup.enter="loadTree"
                    class="search-input"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <el-select
                    v-model="filterForm.level"
                    placeholder="层级筛选"
                    clearable
                    @change="loadTree"
                    class="level-select"
                  >
                    <el-option label="一级" :value="1" />
                    <el-option label="二级" :value="2" />
                    <el-option label="三级" :value="3" />
                  </el-select>
                  <el-button type="primary" :icon="Search" @click="loadTree">查询</el-button>
                </div>
                <div class="filter-right">
                  <el-button-group>
                    <el-button :icon="ArrowDown" @click="expandAll" title="展开全部">展开</el-button>
                    <el-button :icon="ArrowUp" @click="collapseAll" title="折叠全部">折叠</el-button>
                  </el-button-group>
                </div>
              </div>
            </template>

            <div v-loading="loading" class="tree-container">
              <el-tree
                ref="conceptTreeRef"
                :data="conceptTreeData"
                :props="treeProps"
                :filter-node-method="filterTreeNode"
                :default-expand-all="defaultExpandAll"
                node-key="id"
                class="concept-list-tree"
                @node-expand="handleNodeExpand"
              >
                <template #default="{ node, data }">
                  <div class="tree-node-content" :data-is-stock="data._isStock">
                    <div class="node-info">
                      <span v-if="data._isStock" class="stock-icon">📈</span>
                      <span class="node-label" :class="`level-${data.level}`">{{ data.name }}</span>
                      <el-tag v-if="!data._isStock" :type="getLevelTagType(data.level)" size="small" class="node-tag" effect="plain">
                        {{ getLevelText(data.level) }}
                      </el-tag>
                      <span v-if="!data._isStock && data.code" class="node-code">
                        <el-icon><Document /></el-icon>
                        {{ data.code }}
                      </span>
                      <el-badge
                        v-if="!data._isStock && data.stock_count !== undefined && data.stock_count > 0"
                        :value="data.stock_count"
                        class="node-badge"
                        :max="99"
                      >
                        <span class="badge-label">个股</span>
                      </el-badge>
                    </div>
                    <div class="node-actions">
                      <el-button
                        v-if="!data._isStock && data.stock_count !== undefined && data.stock_count > 0"
                        size="small"
                        type="info"
                        :icon="data._stocksLoaded ? ArrowDown : ArrowRight"
                        link
                        :loading="data._loadingStocks"
                        @click.stop="handleToggleStocks(node, data)"
                        :title="data._stocksLoaded ? '折叠股票' : '展开股票'"
                      >
                        {{ data._stocksLoaded ? '折叠' : '展开' }}
                      </el-button>
                      <el-button
                        v-if="data.level < 3 && !data._isStock"
                        size="small"
                        type="success"
                        :icon="Plus"
                        link
                        @click.stop="handleCreateChild(data)"
                        title="新增子级"
                      >
                        子级
                      </el-button>
                      <el-button
                        v-if="data.level >= 2 && !data._isStock"
                        size="small"
                        type="warning"
                        :icon="Plus"
                        link
                        @click.stop="handleAddStock(data)"
                        title="添加个股"
                      >
                        个股
                      </el-button>
                      <el-button
                        v-if="!data._isStock"
                        size="small"
                        type="primary"
                        :icon="Edit"
                        link
                        @click.stop="handleEdit(data)"
                        title="编辑"
                      >
                        编辑
                      </el-button>
                      <el-button
                        v-if="!data._isStock"
                        size="small"
                        type="danger"
                        :icon="Delete"
                        link
                        @click.stop="handleDelete(data)"
                        title="删除"
                      >
                        删除
                      </el-button>
                    </div>
                  </div>
                </template>
              </el-tree>
              <el-empty
                v-if="!loading && conceptTreeData.length === 0"
                description="暂无概念数据"
                :image-size="120"
              >
                <el-button type="primary" @click="handleCreate">新增概念</el-button>
              </el-empty>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="650px"
      :close-on-click-modal="false"
      @close="resetForm"
      class="concept-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="概念名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入概念名称" />
        </el-form-item>
        <el-form-item label="概念代码" prop="code">
          <el-input v-model="form.code" placeholder="请输入概念代码（可选）" />
        </el-form-item>
        <el-form-item label="父概念" prop="parent_id">
          <el-popover
            placement="bottom-start"
            :width="400"
            trigger="click"
            v-model="parentTreeVisible"
          >
            <template #reference>
              <el-input
                :model-value="getParentConceptName(form.parent_id)"
                placeholder="点击选择父概念（不选则为一级概念）"
                readonly
                clearable
                @clear="handleClearParent"
                style="width: 100%"
              >
                <template #suffix>
                  <el-icon class="el-input__icon">
                    <ArrowDown />
                  </el-icon>
                </template>
              </el-input>
            </template>
            <div class="parent-tree-container">
              <el-input
                v-model="parentTreeFilter"
                placeholder="搜索概念名称"
                clearable
                style="margin-bottom: 10px"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-tree
                ref="parentTreeRef"
                :data="filteredParentTreeData"
                :props="treeProps"
                :filter-node-method="filterTreeNode"
                node-key="id"
                highlight-current
                :default-expand-all="true"
                @node-click="handleParentNodeClick"
                class="parent-select-tree"
              >
                <template #default="{ node, data }">
                  <div class="tree-node">
                    <span class="node-label">{{ data.name }}</span>
                    <el-tag :type="getLevelTagType(data.level)" size="small" class="node-tag">
                      {{ getLevelText(data.level) }}
                    </el-tag>
                  </div>
                </template>
              </el-tree>
            </div>
          </el-popover>
        </el-form-item>
        <el-form-item label="层级" prop="level">
          <el-input-number
            v-model="form.level"
            :min="1"
            :max="3"
            :disabled="true"
            style="width: 100%"
          />
          <div class="form-tip">层级将根据父概念自动计算</div>
        </el-form-item>
        <el-form-item label="排序顺序" prop="sort_order">
          <el-input-number
            v-model="form.sort_order"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入概念描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加个股对话框 -->
    <el-dialog
      v-model="addStockDialogVisible"
      :title="`添加个股 - ${selectedConcept?.name || ''}`"
      width="500px"
      :close-on-click-modal="false"
      @close="resetAddStockForm"
    >
      <el-form
        ref="addStockFormRef"
        :model="addStockForm"
        :rules="addStockRules"
        label-width="100px"
      >
        <el-form-item label="概念名称">
          <el-input :model-value="selectedConcept?.name" disabled />
        </el-form-item>
        <el-form-item label="股票名称" prop="stock_name">
          <el-input
            v-model="addStockForm.stock_name"
            placeholder="请输入股票名称"
            @keyup.enter="handleAddStockSubmit"
          />
        </el-form-item>
        <el-form-item>
          <div class="form-tip">提示：可以输入多个股票名称，用逗号或换行分隔</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addStockDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddStockSubmit" :loading="addingStock">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, ArrowUp, ArrowRight, Search, Edit, Delete, Plus, Collection, Document } from '@element-plus/icons-vue'
import { stockConceptApi, type StockConcept } from '@/api/stockConcept'

const loading = ref(false)
const conceptList = ref<StockConcept[]>([])
const conceptTreeData = ref<StockConcept[]>([])
const conceptTreeRef = ref()
const defaultExpandAll = ref(true)
const expandedStocksMap = ref<Map<number, boolean>>(new Map()) // 记录哪些概念已展开股票

const filterForm = reactive({
  name: '',
  level: undefined as number | undefined,
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增概念')
const formRef = ref()
const form = reactive<Partial<StockConcept>>({
  name: '',
  code: '',
  description: '',
  parent_id: undefined,
  level: 1,
  sort_order: 0,
})

const parentOptions = ref<StockConcept[]>([])
const parentTreeData = ref<StockConcept[]>([])
const parentTreeVisible = ref(false)
const parentTreeFilter = ref('')
const parentTreeRef = ref()

// 添加个股相关
const addStockDialogVisible = ref(false)
const selectedConcept = ref<StockConcept | null>(null)
const addStockFormRef = ref()
const addingStock = ref(false)
const addStockForm = reactive({
  stock_name: '',
})

const addStockRules = {
  stock_name: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
}

const treeProps = {
  children: 'children',
  label: 'name',
}

const rules = {
  name: [{ required: true, message: '请输入概念名称', trigger: 'blur' }],
}

// 收集需要排除的ID（当前编辑的概念及其所有子概念）
const getExcludeIds = (data: StockConcept[], targetId?: number): Set<number> => {
  const excludeIds = new Set<number>()
  if (!targetId) return excludeIds
  
  const findAndCollect = (items: StockConcept[]): boolean => {
    for (const item of items) {
      if (item.id === targetId) {
        // 找到目标节点，收集其所有子节点ID
        const collectDescendants = (node: StockConcept) => {
          excludeIds.add(node.id)
          if (node.children && node.children.length > 0) {
            node.children.forEach(collectDescendants)
          }
        }
        collectDescendants(item)
        return true
      }
      if (item.children && item.children.length > 0) {
        if (findAndCollect(item.children)) {
          return true
        }
      }
    }
    return false
  }
  
  findAndCollect(data)
  return excludeIds
}

// 过滤后的父概念树数据（排除三级概念和当前编辑的概念及其子概念）
const filteredParentTreeData = computed(() => {
  if (!parentTreeData.value || parentTreeData.value.length === 0) return []
  
  const excludeIds = getExcludeIds(parentTreeData.value, form.id)
  
  // 递归过滤树数据
  const filterTreeData = (data: StockConcept[]): StockConcept[] => {
    return data
      .filter((item) => {
        // 排除当前编辑的概念及其子概念
        if (excludeIds.has(item.id)) {
          return false
        }
        // 只保留一级和二级概念（三级不能作为父概念）
        return item.level < 3
      })
      .map((item) => {
        const filtered: StockConcept = { ...item }
        if (item.children && item.children.length > 0) {
          // 递归过滤子节点
          filtered.children = filterTreeData(item.children)
        }
        return filtered
      })
      .filter((item) => item !== null)
  }
  
  return filterTreeData(parentTreeData.value)
})

// 监听搜索框变化，过滤树节点
watch(parentTreeFilter, (val) => {
  parentTreeRef.value?.filter(val)
})

// 获取父概念名称
const getParentConceptName = (parentId?: number): string => {
  if (!parentId) return ''
  const findConcept = (data: StockConcept[]): StockConcept | null => {
    for (const item of data) {
      if (item.id === parentId) {
        return item
      }
      if (item.children && item.children.length > 0) {
        const found = findConcept(item.children)
        if (found) return found
      }
    }
    return null
  }
  const concept = findConcept(parentTreeData.value)
  return concept ? `${concept.name} (${getLevelText(concept.level)})` : ''
}

// 处理父概念节点点击
const handleParentNodeClick = (data: StockConcept) => {
  form.parent_id = data.id
  // 根据父概念的层级自动设置当前概念的层级
  form.level = data.level + 1
  parentTreeVisible.value = false
}

// 清除父概念
const handleClearParent = () => {
  form.parent_id = undefined
  form.level = 1
}

const getLevelText = (level: number) => {
  const map: Record<number, string> = { 1: '一级', 2: '二级', 3: '三级' }
  return map[level] || '未知'
}

const getLevelTagType = (level: number) => {
  const map: Record<number, string> = { 1: 'primary', 2: 'success', 3: 'warning' }
  return map[level] || ''
}

// 加载树形数据
const loadTree = async () => {
  loading.value = true
  try {
    // 加载完整的树形结构
    let treeData = await stockConceptApi.getTree(3)
    
    // 清理之前的股票展开状态
    expandedStocksMap.value.clear()
    
    // 递归清理股票节点和加载状态
    const cleanTreeData = (nodes: StockConcept[]): StockConcept[] => {
      return nodes.map(node => {
        const cleaned: StockConcept = { ...node }
        // 移除股票节点
        if (cleaned.children) {
          cleaned.children = cleaned.children.filter((child: any) => !child._isStock)
        }
        // 重置加载状态
        delete (cleaned as any)._stocksLoaded
        delete (cleaned as any)._loadingStocks
        // 递归处理子节点
        if (cleaned.children && cleaned.children.length > 0) {
          cleaned.children = cleanTreeData(cleaned.children)
        }
        return cleaned
      })
    }
    
    treeData = cleanTreeData(treeData)
    
    // 如果有名称搜索，过滤树数据
    if (filterForm.name) {
      treeData = filterTreeBySearch(treeData, filterForm.name)
    }
    
    // 如果有层级筛选，过滤树数据
    if (filterForm.level) {
      treeData = filterTreeByLevel(treeData, filterForm.level)
    }
    
    conceptTreeData.value = treeData
    
    // 应用搜索过滤
    if (filterForm.name && conceptTreeRef.value) {
      nextTick(() => {
        conceptTreeRef.value?.filter(filterForm.name)
      })
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 递归过滤树数据（按名称搜索）
const filterTreeBySearch = (data: StockConcept[], keyword: string): StockConcept[] => {
  if (!data || data.length === 0) return []
  
  const lowerKeyword = keyword.toLowerCase()
  
  return data
    .map((item) => {
      const matches = item.name.toLowerCase().includes(lowerKeyword)
      const filtered: StockConcept = { ...item }
      
      if (item.children && item.children.length > 0) {
        filtered.children = filterTreeBySearch(item.children, keyword)
        // 如果子节点有匹配的，也保留父节点
        if (filtered.children.length > 0) {
          return filtered
        }
      }
      
      return matches ? filtered : null as any
    })
    .filter((item) => item !== null)
}

// 递归过滤树数据（按层级）
const filterTreeByLevel = (data: StockConcept[], targetLevel: number): StockConcept[] => {
  if (!data || data.length === 0) return []
  
  return data
    .map((item) => {
      const filtered: StockConcept = { ...item }
      
      if (item.level === targetLevel) {
        // 如果当前节点匹配，保留但不包含子节点
        filtered.children = []
        return filtered
      } else if (item.level < targetLevel) {
        // 如果当前节点层级小于目标层级，递归过滤子节点
        if (item.children && item.children.length > 0) {
          filtered.children = filterTreeByLevel(item.children, targetLevel)
          // 如果子节点有匹配的，保留父节点
          if (filtered.children.length > 0) {
            return filtered
          }
        }
        return null as any
      } else {
        // 如果当前节点层级大于目标层级，不保留
        return null as any
      }
    })
    .filter((item) => item !== null)
}

// 树节点过滤方法（用于搜索）
const filterTreeNode = (value: string, data: StockConcept) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase())
}

// 展开全部
const expandAll = () => {
  defaultExpandAll.value = true
  nextTick(() => {
    if (conceptTreeRef.value) {
      const allKeys = getAllNodeKeys(conceptTreeData.value)
      conceptTreeRef.value.store.setExpandedKeys(allKeys)
    }
  })
}

// 折叠全部
const collapseAll = () => {
  defaultExpandAll.value = false
  if (conceptTreeRef.value) {
    conceptTreeRef.value.store.setExpandedKeys([])
  }
}

// 获取所有节点键
const getAllNodeKeys = (data: StockConcept[]): number[] => {
  const keys: number[] = []
  const traverse = (nodes: StockConcept[]) => {
    nodes.forEach((node) => {
      keys.push(node.id)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(data)
  return keys
}

// 保留原有的 loadList 方法用于兼容
const loadList = async () => {
  await loadTree()
}

const loadParentOptions = async () => {
  try {
    // 加载树形结构数据
    const treeData = await stockConceptApi.getTree(2) // 只加载到二级，因为三级不能作为父概念
    parentTreeData.value = treeData
    
    // 同时加载列表数据用于兼容
    const res = await stockConceptApi.getList({ page_size: 1000 })
    parentOptions.value = res.items.filter((c) => c.level < 3)
  } catch (error: any) {
    console.error('加载父概念选项失败', error)
    ElMessage.error('加载父概念列表失败')
  }
}

const handleCreate = () => {
  dialogTitle.value = '新增概念'
  resetForm()
  parentTreeVisible.value = false
  parentTreeFilter.value = ''
  dialogVisible.value = true
  loadParentOptions()
}

// 新增子级概念
const handleCreateChild = (parentConcept: StockConcept) => {
  dialogTitle.value = `新增子级概念 - ${parentConcept.name}`
  resetForm()
  // 自动设置父概念
  form.parent_id = parentConcept.id
  form.level = parentConcept.level + 1
  parentTreeVisible.value = false
  parentTreeFilter.value = ''
  dialogVisible.value = true
  loadParentOptions()
  // 设置树选中节点
  if (parentTreeRef.value) {
    nextTick(() => {
      parentTreeRef.value?.setCurrentKey(parentConcept.id)
    })
  }
}

// 添加个股到概念
const handleAddStock = (concept: StockConcept) => {
  selectedConcept.value = concept
  resetAddStockForm()
  addStockDialogVisible.value = true
}

const resetAddStockForm = () => {
  addStockForm.stock_name = ''
  addStockFormRef.value?.resetFields()
}

const handleAddStockSubmit = async () => {
  if (!addStockFormRef.value || !selectedConcept.value) return
  await addStockFormRef.value.validate()
  
  addingStock.value = true
  try {
    // 支持多个股票名称，用逗号或换行分隔
    const stockNames = addStockForm.stock_name
      .split(/[,\n]/)
      .map(name => name.trim())
      .filter(name => name.length > 0)
    
    if (stockNames.length === 0) {
      ElMessage.warning('请输入至少一个股票名称')
      return
    }
    
    // 逐个添加股票
    let successCount = 0
    let failCount = 0
    const errors: string[] = []
    
    for (const stockName of stockNames) {
      try {
        await stockConceptApi.addStockToConcept(selectedConcept.value.id, stockName)
        successCount++
      } catch (error: any) {
        failCount++
        errors.push(`${stockName}: ${error.message || '添加失败'}`)
      }
    }
    
    if (successCount > 0) {
      ElMessage.success(`成功添加 ${successCount} 个个股${failCount > 0 ? `，${failCount} 个失败` : ''}`)
      if (failCount > 0 && errors.length > 0) {
        console.error('添加失败详情:', errors)
      }
      addStockDialogVisible.value = false
      loadTree() // 重新加载树，更新stock_count
    } else {
      ElMessage.error('添加失败：' + (errors[0] || '未知错误'))
    }
  } catch (error: any) {
    ElMessage.error(error.message || '添加失败')
  } finally {
    addingStock.value = false
  }
}

const handleEdit = async (row: StockConcept) => {
  dialogTitle.value = '编辑概念'
  Object.assign(form, {
    id: row.id,
    name: row.name,
    code: row.code,
    description: row.description,
    parent_id: row.parent_id,
    level: row.level,
    sort_order: row.sort_order,
  })
  parentTreeVisible.value = false
  parentTreeFilter.value = ''
  dialogVisible.value = true
  await loadParentOptions()
  // 设置树选中节点
  if (form.parent_id && parentTreeRef.value) {
    nextTick(() => {
      parentTreeRef.value?.setCurrentKey(form.parent_id)
    })
  }
}

const handleDelete = async (row: StockConcept) => {
  try {
    // 检查是否有子概念
    const hasChildren = row.children && row.children.length > 0
    const message = hasChildren
      ? `确定要删除概念 "${row.name}" 吗？删除后其所有子概念也将被删除。`
      : `确定要删除概念 "${row.name}" 吗？`
    
    await ElMessageBox.confirm(
      message,
      '确认删除',
      {
        type: 'warning',
      }
    )
    await stockConceptApi.delete(row.id)
    ElMessage.success('删除成功')
    loadTree()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  try {
    // 准备提交数据，将空字符串转换为 undefined
    const submitData: Partial<StockConcept> = {
      ...form,
      code: form.code && form.code.trim() ? form.code.trim() : undefined,
      description: form.description && form.description.trim() ? form.description.trim() : undefined,
    }
    
    if (form.id) {
      await stockConceptApi.update(form.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await stockConceptApi.create(submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTree()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

const resetForm = () => {
  Object.assign(form, {
    id: undefined,
    name: '',
    code: '',
    description: '',
    parent_id: undefined,
    level: 1,
    sort_order: 0,
  })
  parentTreeVisible.value = false
  parentTreeFilter.value = ''
  formRef.value?.resetFields()
}

onMounted(() => {
  loadTree()
})

// 监听搜索框变化
watch(() => filterForm.name, (val) => {
  if (conceptTreeRef.value) {
    conceptTreeRef.value.filter(val)
  }
})

// 处理节点展开事件
const handleNodeExpand = (data: StockConcept) => {
  // 当节点展开时，如果该节点已加载股票，确保股票节点也展开
  if (data._stocksLoaded && data.children) {
    const stockNodes = data.children.filter((child: any) => child._isStock)
    if (stockNodes.length > 0) {
      nextTick(() => {
        const stockKeys = stockNodes.map((node: any) => node.id)
        conceptTreeRef.value?.store.setExpandedKeys([...conceptTreeRef.value.store.expandedKeys, ...stockKeys])
      })
    }
  }
}

// 切换股票展开/折叠
const handleToggleStocks = async (node: any, data: StockConcept) => {
  if (data._isStock) return // 如果是股票节点，不处理
  
  // 如果已经加载了股票，则折叠
  if (data._stocksLoaded) {
    collapseStocks(node, data)
  } else {
    // 否则加载并展开股票
    await loadAndExpandStocks(node, data)
  }
}

// 加载并展开股票列表
const loadAndExpandStocks = async (node: any, data: StockConcept) => {
  if (!data.id) return
  
  data._loadingStocks = true
  try {
    // 调用API获取股票列表
    const stocks = await stockConceptApi.getStocks(data.id, false) // 不包含子概念的股票
    
    if (stocks.length === 0) {
      ElMessage.info('该概念下暂无股票')
      data._loadingStocks = false
      return
    }
    
    // 创建股票节点（不设置children，避免显示展开图标）
    const stockNodes = stocks.map((stockName, index) => ({
      id: `stock_${data.id}_${index}`, // 使用唯一ID
      name: stockName,
      _isStock: true,
      level: (data.level || 3) + 1, // 股票节点层级比概念高一级
      stock_count: 0,
      // 不设置children，这样Element Plus就不会显示展开图标
    }))
    
    // 将股票节点添加到当前节点的children中
    if (!data.children) {
      data.children = []
    }
    
    // 先移除之前可能存在的股票节点
    data.children = data.children.filter((child: any) => !child._isStock)
    
    // 添加新的股票节点
    data.children.push(...stockNodes)
    
    // 标记为已加载
    data._stocksLoaded = true
    expandedStocksMap.value.set(data.id, true)
    
    // 展开当前节点（如果未展开）
    if (!node.expanded) {
      node.expanded = true
    }
    
    // 展开股票节点
    await nextTick()
    const stockKeys = stockNodes.map((n: any) => n.id)
    const currentExpandedKeys = conceptTreeRef.value?.store.expandedKeys || []
    conceptTreeRef.value?.store.setExpandedKeys([...currentExpandedKeys, data.id, ...stockKeys])
    
  } catch (error: any) {
    ElMessage.error(error.message || '加载股票列表失败')
  } finally {
    data._loadingStocks = false
  }
}

// 折叠股票列表
const collapseStocks = (node: any, data: StockConcept) => {
  if (!data.children || !data.id) return
  
  // 移除股票节点
  data.children = data.children.filter((child: any) => !child._isStock)
  
  // 标记为未加载
  data._stocksLoaded = false
  expandedStocksMap.value.delete(data.id)
  
  // 更新展开的keys，移除股票节点的keys
  if (conceptTreeRef.value) {
    const currentExpandedKeys = conceptTreeRef.value.store.expandedKeys || []
    const filteredKeys = currentExpandedKeys.filter((key: any) => !String(key).startsWith(`stock_${data.id}_`))
    conceptTreeRef.value.store.setExpandedKeys(filteredKeys)
  }
}
</script>

<style scoped lang="scss">
.stock-concept-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

:deep(.el-card) {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    
    .title-icon {
      font-size: 20px;
      color: #409eff;
    }
  }
}

.concept-list-card {
  :deep(.el-card__header) {
    background-color: #fafbfc;
    border-bottom: 1px solid #e4e7ed;
    padding: 16px 20px;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  
  .filter-left {
    display: flex;
    gap: 12px;
    align-items: center;
    flex: 1;
    min-width: 0;
    
    .search-input {
      width: 220px;
      flex-shrink: 0;
    }
    
    .level-select {
      width: 140px;
      flex-shrink: 0;
    }
  }
  
  .filter-right {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
  }
}

.tree-container {
  min-height: 400px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
  padding: 8px 0;
  border-radius: 4px;
  background-color: #fff;
  
  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
    
    &:hover {
      background: #a8a8a8;
    }
  }
}

.concept-list-tree {
  :deep(.el-tree-node__content) {
    height: 42px;
    padding: 0 8px;
    margin: 2px 0;
    border-radius: 4px;
    transition: all 0.2s;
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  :deep(.el-tree-node__expand-icon) {
    color: #606266;
    font-size: 14px;
  }
  
  .tree-node-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0 8px;
    flex: 1;

    .node-info {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 0;

      .node-label {
        font-weight: 500;
        font-size: 14px;
        color: #303133;
        flex-shrink: 0;
        transition: color 0.2s;
        
        &.level-1 {
          font-weight: 600;
          font-size: 15px;
          color: #303133;
        }
        
        &.level-2 {
          font-weight: 500;
          color: #606266;
        }
        
        &.level-3 {
          font-weight: 400;
          color: #909399;
        }
      }
      
      // 股票节点样式
      &[data-is-stock="true"] {
        .node-label {
          color: #606266;
          font-size: 13px;
          font-weight: 400;
        }
        
        .node-info {
          padding-left: 8px;
        }
      }
      
      :deep(.el-tree-node[data-is-stock="true"]) {
        .el-tree-node__content {
          height: 32px;
          padding-left: 24px !important;
        }
        
        .el-tree-node__expand-icon {
          display: none; // 隐藏股票节点的展开图标
        }
      }

      .node-tag {
        flex-shrink: 0;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 10px;
      }

      .node-code {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #909399;
        font-size: 12px;
        flex-shrink: 0;
        padding: 2px 8px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-icon {
          font-size: 12px;
        }
      }
      
      .stock-icon {
        font-size: 14px;
        margin-right: 4px;
        flex-shrink: 0;
      }

      .node-badge {
        flex-shrink: 0;
        
        .badge-label {
          font-size: 12px;
          color: #909399;
          margin-right: 4px;
        }
        
        :deep(.el-badge__content) {
          background-color: #409eff;
          border-color: #409eff;
          font-size: 11px;
          height: 18px;
          line-height: 18px;
          padding: 0 6px;
        }
      }
    }

    .node-actions {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
      opacity: 0;
      transition: opacity 0.2s;
      
      .el-button {
        padding: 4px 8px;
        font-size: 12px;
        
        // 新增子级按钮特殊样式
        &.el-button--success {
          color: #67c23a;
          
          &:hover {
            color: #85ce61;
            background-color: #f0f9ff;
          }
        }
      }
    }

    &:hover .node-actions {
      opacity: 1;
    }
  }
}

.concept-dialog {
  :deep(.el-dialog__header) {
    padding: 20px 20px 16px;
    border-bottom: 1px solid #e4e7ed;
    background-color: #fafbfc;
    
    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px 20px;
  }
  
  :deep(.el-form-item__label) {
    font-weight: 500;
    color: #606266;
  }
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
  line-height: 1.5;
}

.parent-tree-container {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafbfc;
  
  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
    
    &:hover {
      background: #a8a8a8;
    }
  }
}

.parent-select-tree {
  :deep(.el-tree-node__content) {
    height: 36px;
    padding: 0 8px;
    margin: 2px 0;
    border-radius: 4px;
    
    &:hover {
      background-color: #ecf5ff;
    }
  }
  
  .tree-node {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    width: 100%;

    .node-label {
      flex: 1;
      font-size: 14px;
      color: #303133;
    }

    .node-tag {
      margin-left: auto;
      flex-shrink: 0;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .filter-header {
    flex-direction: column;
    align-items: stretch;
    
    .filter-left {
      flex-direction: column;
      
      .search-input,
      .level-select {
        width: 100%;
      }
    }
    
    .filter-right {
      justify-content: flex-end;
    }
  }
  
  .tree-container {
    max-height: calc(100vh - 300px);
  }
  
  .node-info {
    flex-wrap: wrap;
    gap: 6px;
  }
}
</style>
