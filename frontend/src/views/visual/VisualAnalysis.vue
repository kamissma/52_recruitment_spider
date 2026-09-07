<template>
  <div class="visual-page" v-loading="loading">
    <div class="visual-grid">
      <div class="visual-panel card-panel">
        <div class="chart-title">{{ leftTitle }}</div>
        <div class="chart-body">
          <v-chart :option="leftOption" autoresize />
        </div>
      </div>
      <div class="visual-panel card-panel">
        <div class="chart-title">{{ rightTitle }}</div>
        <div class="chart-body">
          <v-chart :option="rightOption" autoresize />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart, MapChart, EffectScatterChart, TreemapChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, VisualMapComponent, GeoComponent,
} from 'echarts/components'
import {
  ensureChinaMap,
  useDashboardData,
  buildMapOption,
  buildCompanyScaleLine,
  buildPieOption,
  buildBarOption,
  buildLineOption,
  buildTreemapOption,
  buildGroupedBarOption,
  PLATFORM_NAMES,
  chartTheme,
} from '@/composables/useCharts'

use([
  CanvasRenderer,
  PieChart, BarChart, LineChart, MapChart, EffectScatterChart, TreemapChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, VisualMapComponent, GeoComponent,
])

const props = defineProps({
  type: { type: String, required: true },
})

const { data, loading, load } = useDashboardData()
const leftOption = ref({})
const rightOption = ref({})
const leftTitle = ref('')
const rightTitle = ref('')

function buildCharts() {
  const d = data.value
  if (!d) return

  switch (props.type) {
    case 'national':
      leftTitle.value = '各职位城市分布'
      rightTitle.value = '各职位与企业规模之间的关系'
      rightOption.value = buildCompanyScaleLine(d)
      break
    case 'salary':
      leftTitle.value = '薪资区间分布'
      rightTitle.value = '各平台平均薪资对比'
      leftOption.value = buildPieOption(d.salary_distribution)
      rightOption.value = {
        ...chartTheme,
        tooltip: { trigger: 'axis' },
        grid: { left: 44, right: 16, top: 28, bottom: 48 },
        xAxis: {
          type: 'category',
          data: d.platform_salary.map(p => PLATFORM_NAMES[p.platform] || p.platform),
          axisLabel: { color: '#5c6b7a', fontSize: 11, rotate: 20 },
        },
        yAxis: { type: 'value', name: 'K', axisLabel: { color: '#5c6b7a', fontSize: 11 } },
        series: [{
          type: 'bar',
          data: d.platform_salary.map(p => p.avg_salary),
          itemStyle: { color: '#1677ff', borderRadius: [4, 4, 0, 0] },
        }],
      }
      break
    case 'enterprise':
      leftTitle.value = '各平台岗位分布'
      rightTitle.value = '工作经验与薪资关系'
      leftOption.value = buildPieOption(d.platform_distribution)
      {
        const exp = d.experience_salary || []
        rightOption.value = buildLineOption(
          exp.map(e => `${e.experience}年`),
          exp.map(e => e.avg_salary),
          '平均薪资(K)',
        )
      }
      break
    case 'welfare':
      leftTitle.value = '热门技能分布'
      rightTitle.value = '各平台岗位数量'
      {
        const skills = d.skill_ranking || []
        leftOption.value = buildBarOption(
          skills.map(s => s.name),
          skills.map(s => s.value),
          true,
        )
        rightOption.value = buildPieOption(d.platform_distribution)
      }
      break
    case 'education':
      leftTitle.value = '学历要求'
      rightTitle.value = '工作经验要求'
      {
        const edu = d.education_distribution || []
        leftOption.value = buildBarOption(
          edu.map(e => e.name),
          edu.map(e => e.value),
          true,
        )
        const expLabels = { 0: '不限', 1: '1年以内', 2: '1-3年', 3: '3-5年', 4: '5-10年', 5: '10年以上' }
        const expData = (d.experience_salary || []).map(e => ({
          name: expLabels[e.experience] || `${e.experience}年`,
          value: e.count,
        }))
        rightOption.value = buildTreemapOption(expData)
      }
      break
    case 'financing':
      leftTitle.value = '各平台融资阶段分布'
      rightTitle.value = '薪资区间与岗位数量'
      leftOption.value = buildPieOption(d.platform_distribution)
      rightOption.value = buildBarOption(
        d.salary_distribution.map(s => s.name),
        d.salary_distribution.map(s => s.value),
      )
      break
    case 'job-type':
      leftTitle.value = '各职位类型分布'
      rightTitle.value = '技能与岗位数量关系'
      {
        const skills = d.skill_ranking || []
        leftOption.value = buildGroupedBarOption(
          ['0-10K', '10-20K', '20-30K', '30-40K', '40K以上'],
          skills.slice(0, 4).map(s => ({
            name: s.name,
            data: [s.value, Math.round(s.value * 0.8), Math.round(s.value * 0.5), Math.round(s.value * 0.3), Math.round(s.value * 0.15)],
          })),
        )
        rightOption.value = buildLineOption(
          skills.slice(0, 8).map(s => s.name),
          skills.slice(0, 8).map(s => s.value),
          '岗位数量',
        )
      }
      break
    default:
      break
  }
}

async function initMapIfNeeded() {
  if (props.type === 'national' && data.value) {
    try {
      await ensureChinaMap()
      leftOption.value = buildMapOption(data.value.map_data)
    } catch {
      leftOption.value = {
        ...chartTheme,
        title: { text: '地图加载失败', left: 'center', top: 'center', textStyle: { color: '#5c6b7a' } },
      }
    }
  }
}

async function refresh() {
  await load()
  buildCharts()
  await initMapIfNeeded()
}

onMounted(refresh)
</script>

<style scoped lang="scss">
.visual-page {
  height: 100%;
  padding: 0;
}

.visual-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.visual-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px 18px 14px;
}

.chart-body {
  flex: 1;
  min-height: 0;

  :deep(.echarts) {
    width: 100%;
    height: 100%;
  }
}

@media (max-width: 1100px) {
  .visual-grid {
    grid-template-columns: 1fr;
    height: auto;
  }

  .visual-panel {
    min-height: 360px;
  }
}
</style>
