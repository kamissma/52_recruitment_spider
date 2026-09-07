<template>
  <div class="compare-wrap">
    <div class="compare-tip">
      正在对比 <b>{{ jobs.length }}</b> 条招聘数据，<span class="tip-hl">绿色加粗</span> 为平均薪资最高的一项
      <span v-if="maxDiff !== null">（与最高薪资最大差距 {{ maxDiff }}K）</span>
    </div>

    <el-table :data="rows" border class="compare-table">
      <el-table-column prop="label" label="对比项" width="110" fixed="left" />
      <el-table-column v-for="(job, i) in jobs" :key="i" min-width="180">
        <template #header>
          <div class="job-header">
            <el-tag :type="platformTagType(job.platform)" size="small" class="dark-tag">
              {{ platformName(job.platform) }}
            </el-tag>
            <div class="job-title" :title="job.title">{{ job.title }}</div>
            <div class="job-sub">{{ job.company || '未知公司' }}</div>
          </div>
        </template>
        <template #default="{ row }">
          <span :class="{ 'best-value': row.best === i }">{{ row.values[i] }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  jobs: { type: Array, default: () => [] },   // 待对比的岗位记录（2 条及以上）
  mode: { type: String, default: 'clean' },   // clean | raw
})

const PLATFORM_NAMES = { lagou: '拉勾网', liepin: '猎聘网', qcwy: '前程无忧', zhaopin: '智联招聘', boss: 'BOSS直聘' }
const platformName = (k) => PLATFORM_NAMES[k] || k
const platformTagType = (k) => ({ boss: '', zhaopin: 'success', lagou: 'warning', liepin: 'danger', qcwy: 'info' }[k] || 'info')

const EDU_LABELS = { 0: '不限', 1: '高中', 2: '大专', 3: '本科', 4: '硕士', 5: '博士' }

const dash = (v) => (v === null || v === undefined || v === '' ? '-' : v)

/** 平均薪资最高项下标（无有效数据则返回 null） */
const bestSalaryIndex = computed(() => {
  const avgs = props.jobs.map(j => Number(j.salary_avg))
  if (avgs.some(v => !Number.isFinite(v))) return null
  return avgs.indexOf(Math.max(...avgs))
})

/** 与最高平均薪资的最大差距（K） */
const maxDiff = computed(() => {
  if (props.mode !== 'clean') return null
  const avgs = props.jobs.map(j => Number(j.salary_avg)).filter(Number.isFinite)
  if (avgs.length < 2) return null
  return (Math.max(...avgs) - Math.min(...avgs)).toFixed(1)
})

const rows = computed(() => {
  const jobs = props.jobs
  if (!jobs.length) return []
  const best = bestSalaryIndex.value

  if (props.mode === 'raw') {
    return [
      { label: '城市', values: jobs.map(j => dash(j.city)) },
      { label: '薪资', values: jobs.map(j => dash(j.salary_raw)) },
      { label: '经验要求', values: jobs.map(j => dash(j.experience)) },
      { label: '学历要求', values: jobs.map(j => dash(j.education)) },
      { label: '技能', values: jobs.map(j => dash(j.skills)) },
      { label: '发布时间', values: jobs.map(j => dash(j.publish_time)) },
      { label: '采集时间', values: jobs.map(j => dash(j.crawl_time)) },
    ]
  }

  return [
    { label: '城市', values: jobs.map(j => dash(j.city)) },
    { label: '薪资范围(K)', values: jobs.map(j => j.salary_min && j.salary_max ? `${j.salary_min} ~ ${j.salary_max}` : '-') },
    {
      label: '平均薪资(K)',
      values: jobs.map((j, i) => {
        const v = j.salary_avg
        if (v === null || v === undefined) return '-'
        if (best !== null && i !== best) {
          const top = Math.max(...jobs.map(x => Number(x.salary_avg)).filter(Number.isFinite))
          if (Number.isFinite(Number(v))) return `${v}（↓${(top - Number(v)).toFixed(1)}）`
        }
        return `${v}`
      }),
      best,
    },
    { label: '经验要求(年)', values: jobs.map(j => j.experience_years ?? '不限') },
    { label: '学历要求', values: jobs.map(j => EDU_LABELS[j.education_level] ?? '未知') },
    { label: '技能数', values: jobs.map(j => j.skill_count ?? 0) },
    { label: '技能', values: jobs.map(j => dash(j.skills)) },
  ]
})
</script>

<style scoped lang="scss">
.compare-tip {
  margin-bottom: 12px;
  font-size: 13px;
  color: #666;

  .tip-hl {
    color: #009688;
    font-weight: 600;
  }
}

.compare-table {
  width: 100%;

  :deep(.job-header) {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    padding: 4px 0;

    .job-title {
      font-size: 13px;
      font-weight: 600;
      color: #303133;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .job-sub {
      font-size: 12px;
      color: #909399;
    }
  }

  :deep(.best-value) {
    color: #009688;
    font-weight: 700;
  }
}
</style>
