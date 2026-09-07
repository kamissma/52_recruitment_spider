<template>
  <div class="page-container job-compare-page">
    <!-- 数据来源与筛选 -->
    <div class="card-panel">
      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-label">数据来源</span>
          <el-radio-group v-model="mode" class="mode-radio">
            <el-radio-button value="clean">清洗数据</el-radio-button>
            <el-radio-button value="raw">原始数据</el-radio-button>
          </el-radio-group>
        </div>

        <div class="filter-item">
          <span class="filter-label">平台</span>
          <el-select v-model="filters.platform" placeholder="全部平台" clearable class="filter-control">
            <el-option v-for="p in platforms" :key="p.key" :label="p.name" :value="p.key" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">职位</span>
          <el-input v-model="filters.keyword" placeholder="请输入职位" clearable class="filter-control" />
        </div>

        <div class="filter-item">
          <span class="filter-label">公司名称</span>
          <el-input v-model="filters.company" placeholder="请输入公司名称" clearable class="filter-control" />
        </div>

        <div class="filter-item">
          <span class="filter-label">城市</span>
          <el-input v-model="filters.city" placeholder="请输入城市" clearable class="filter-control" />
        </div>

        <el-button class="btn-pill btn-search" round @click="searchNow">
          <el-icon><Search /></el-icon> 查询
        </el-button>
      </div>

      <div class="toolbar">
        <el-button class="btn-pill btn-compare" round :disabled="selectedJobs.length < 2" @click="startCompare">
          <el-icon><Switch /></el-icon> 开始对比（已选 {{ selectedJobs.length }}）
        </el-button>
        <el-button class="btn-pill btn-cancel" round :disabled="selectedJobs.length === 0" @click="clearSelection">
          <el-icon><CircleClose /></el-icon> 清空勾选
        </el-button>
        <span class="toolbar-tip">在表格中勾选 2 条及以上数据，点击「开始对比」查看下方对比结果</span>
        <div class="toolbar-spacer" />
      </div>

      <div class="table-wrapper">
        <!-- 清洗数据列 -->
        <el-table
          v-if="mode === 'clean'"
          ref="tableRef"
          :data="tableData"
          v-loading="loading"
          stripe
          row-key="id"
          style="width: 100%; min-width: 1150px"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="45" reserve-selection />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="platform" label="平台" width="100">
            <template #default="{ row }">
              <el-tag :type="platformTagType(row.platform)" size="small" class="dark-tag">
                {{ platformName(row.platform) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="岗位名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="company" label="公司" min-width="130" show-overflow-tooltip />
          <el-table-column prop="city" label="城市" width="80" show-overflow-tooltip />
          <el-table-column label="薪资(K)" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.salary_min && row.salary_max">{{ row.salary_min }} - {{ row.salary_max }}</span>
              <span v-else-if="row.salary_avg">{{ row.salary_avg }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="salary_avg" label="平均(K)" width="90">
            <template #default="{ row }">
              <span class="salary-highlight">{{ row.salary_avg || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="experience_years" label="经验(年)" width="90" />
          <el-table-column prop="education_level" label="学历" width="80">
            <template #default="{ row }">{{ eduLabel(row.education_level) }}</template>
          </el-table-column>
          <el-table-column prop="skill_count" label="技能数" width="80" />
          <el-table-column prop="clean_time" label="清洗时间" width="170" />
        </el-table>

        <!-- 原始数据列 -->
        <el-table
          v-else
          ref="tableRef"
          :data="tableData"
          v-loading="loading"
          stripe
          row-key="id"
          style="width: 100%; min-width: 1100px"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="45" reserve-selection />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="platform" label="平台" width="100">
            <template #default="{ row }">
              <el-tag :type="platformTagType(row.platform)" size="small" class="dark-tag">
                {{ platformName(row.platform) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="岗位名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="company" label="公司" min-width="130" show-overflow-tooltip />
          <el-table-column prop="city" label="城市" width="80" show-overflow-tooltip />
          <el-table-column prop="salary_raw" label="薪资" min-width="120" show-overflow-tooltip />
          <el-table-column prop="experience" label="经验" width="110" show-overflow-tooltip />
          <el-table-column prop="education" label="学历" width="110" show-overflow-tooltip />
          <el-table-column prop="skills" label="技能" min-width="160" show-overflow-tooltip />
          <el-table-column prop="crawl_time" label="采集时间" width="170" />
        </el-table>
      </div>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="searchNow"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- 对比结果 -->
    <div v-if="compareJobs.length >= 2" ref="comparePanelRef" class="card-panel compare-panel">
      <div class="panel-title">
        <el-icon><Switch /></el-icon> 对比结果（{{ compareJobs.length }} 条 · 来源：{{ compareMode === 'clean' ? '清洗数据' : '原始数据' }}）
      </div>
      <JobCompareTable :jobs="compareJobs" :mode="compareMode" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { getCleanJobs, getRawJobs, getPlatforms } from '@/api'
import JobCompareTable from '@/components/jobs/JobCompareTable.vue'

const PLATFORM_NAMES = { lagou: '拉勾网', liepin: '猎聘网', qcwy: '前程无忧', zhaopin: '智联招聘', boss: 'BOSS直聘' }
const platformName = (k) => PLATFORM_NAMES[k] || k
const platformTagType = (k) => ({ boss: '', zhaopin: 'success', lagou: 'warning', liepin: 'danger', qcwy: 'info' }[k] || 'info')
const EDU_LABELS = { 0: '不限', 1: '高中', 2: '大专', 3: '本科', 4: '硕士', 5: '博士' }
const eduLabel = (l) => EDU_LABELS[l] ?? '未知'

const mode = ref('clean')            // clean | raw
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const platforms = ref([])
const filters = ref({ platform: '', city: '', keyword: '', company: '' })
const selectedJobs = ref([])
const extraSelected = new Map()      // 跨页保留的选中池（key=id）：含翻页保留与跳转携带的行
const compareJobs = ref([])
const compareMode = ref('clean')
const tableRef = ref(null)
const comparePanelRef = ref(null)
let pendingRestore = []              // 从其他页面跳转携带的待恢复选中数据
let searchTimer = null

const isClean = () => mode.value === 'clean'

function buildQueryParams() {
  const params = { page: page.value, per_page: pageSize.value }
  if (filters.value.platform) params.platform = filters.value.platform
  if (filters.value.city) params.city = filters.value.city
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.company) params.company = filters.value.company
  return params
}

function loadData() {
  loading.value = true
  const request = isClean() ? getCleanJobs(buildQueryParams()) : getRawJobs(buildQueryParams())
  request.then(res => {
    tableData.value = res.data.items
    total.value = res.data.total
    if (pendingRestore.length) {
      for (const row of pendingRestore) extraSelected.set(row.id, row)
      restoreSelection(pendingRestore)
      if (pendingRestore.length >= 2) startCompare()
      pendingRestore = []
    }
  }).finally(() => { loading.value = false })
}

function searchNow() {
  page.value = 1
  loadData()
}

/** 按 id 恢复勾选（跨页跳转携带的数据） */
function restoreSelection(list) {
  const ids = new Set(list.map(j => j.id))
  for (const row of tableData.value) {
    if (ids.has(row.id)) tableRef.value?.toggleRowSelection(row, true)
  }
}

/** 合并当前页勾选与跨页保留的勾选（reserve-selection 翻页不丢） */
function handleSelectionChange(rows) {
  const currentIds = new Set(tableData.value.map(r => r.id))
  const map = new Map()
  for (const [id, row] of extraSelected) {
    if (!currentIds.has(id)) map.set(id, row)   // 不在当前页的行继续保留
  }
  for (const row of rows) map.set(row.id, row)  // 当前页以实际勾选状态为准
  selectedJobs.value = [...map.values()]
}

function startCompare() {
  if (selectedJobs.value.length < 2) {
    ElMessage.warning('请至少勾选 2 条数据')
    return
  }
  compareMode.value = mode.value
  compareJobs.value = [...selectedJobs.value]
  nextTick(() => comparePanelRef.value?.scrollIntoView({ behavior: 'smooth' }))
}

/** 一键清空所有勾选（含跨页保留的） */
function clearSelection() {
  extraSelected.clear()
  tableRef.value?.clearSelection()
  selectedJobs.value = []
}

// 切换数据来源：清空已选与对比结果，重新加载
watch(mode, () => {
  extraSelected.clear()
  selectedJobs.value = []
  compareJobs.value = []
  searchNow()
})

// 筛选条件变化：防抖自动查询
watch(
  filters,
  () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      loadData()
    }, 400)
  },
  { deep: true },
)

onMounted(() => {
  getPlatforms().then(res => { platforms.value = res.data })

  // 读取从「原始数据 / 数据清洗」页跳转携带的选中数据
  const preMode = sessionStorage.getItem('compare_mode')
  if (preMode) mode.value = preMode
  const pre = sessionStorage.getItem('compare_jobs')
  if (pre) {
    try { pendingRestore = JSON.parse(pre) || [] } catch { pendingRestore = [] }
    sessionStorage.removeItem('compare_jobs')
    sessionStorage.removeItem('compare_mode')
  }

  loadData()
})

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped lang="scss">
.job-compare-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 16px;
  margin-bottom: 12px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

.filter-control {
  width: 140px;
}

.mode-radio {
  :deep(.el-radio-button__inner) {
    padding: 7px 14px;
  }
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.toolbar-tip {
  font-size: 12px;
  color: #999;
}

.toolbar-spacer {
  flex: 1;
  min-width: 8px;
}

.table-wrapper {
  width: 100%;
  overflow: auto;
  max-height: calc(60vh);
  border: 1px solid #f0f0f0;
  border-radius: 4px;

  :deep(.el-table .cell) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.pagination {
  display: flex;
  justify-content: flex-start;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;

  :deep(.el-pagination) {
    flex-wrap: wrap;
    gap: 8px 0;
  }

  :deep(.el-pagination.is-background .el-pager li.is-active) {
    background-color: #009688 !important;
    color: #fff !important;
  }

  :deep(.el-pagination.is-background .el-pager li:hover) {
    color: #009688;
  }

  :deep(.el-pagination__total) {
    color: #666;
    font-size: 13px;
  }

  :deep(.el-pagination__sizes .el-select) {
    width: 110px;
  }

  :deep(.el-pagination__jump .el-pagination__editor) {
    width: 48px;
  }
}

.compare-panel {
  border-left: 3px solid #fa8c16;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.salary-highlight {
  color: #009688;
  font-weight: 600;
}
</style>
