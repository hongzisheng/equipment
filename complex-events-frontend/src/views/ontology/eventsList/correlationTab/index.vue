<script setup lang="ts">
import { ref, useTemplateRef } from 'vue'
import ToSelectList from '@/views/ontology/eventsList/correlationTab/ToSelectList.vue'
import Details from '@/views/ontology/eventsList/correlationTab/Details.vue'
import MindMap from '@/views/ontology/eventsList/correlationTab/MindMap.vue'
import dataApi from '@/api/dataApi.js'
import fileApi from '@/api/fileApi'
import { OntologySystemData } from '@/views/ontology/ontologySystem'
import { ElMessage } from 'element-plus'
import { Connection, VideoPlay } from '@element-plus/icons-vue'
import CorrelationMethodSelected from '@/views/ontology/eventsList/correlationTab/CorrelationMethodSelected.vue'
import { Response } from '@/api'

const props = defineProps({
  selectedItems: {
    type: Array,
    default: () => [],
  },
})

const selectedRow = ref<OntologySystemData>({})
const eventLinks = ref([])
const mindMapRef = useTemplateRef('mindMapRef')
const methodRef = useTemplateRef<{ checkedMethods: string[]; ruleContent: string }>('methodRef')
const pairCandidate = ref([])
const saveLoading = ref(false)

function handleSelectionChanged(newRow: OntologySystemData) {
  if (!newRow) return
  selectedRow.value = newRow
  dataApi.getEventLink(newRow.reportId).then((res) => {
    eventLinks.value = res.data
  })
}

function dedupePairs(pairs) {
  const uniqueMap = new Map<string, string[]>()
  pairs.forEach((item) => {
    const key = `${item[0]}-${item[1]}`
    const methods = uniqueMap.get(key) || []
    item.slice(2).forEach((method) => {
      if (!methods.includes(method)) methods.push(method)
    })
    uniqueMap.set(key, methods)
  })
  return Array.from(uniqueMap.entries()).map(([key, methods]) => {
    const [mainId, candidateId] = key.split('-')
    return [mainId, candidateId, ...methods]
  })
}

async function handleAssociate() {
  const reportId = selectedRow.value?.reportId
  if (!reportId) {
    ElMessage.warning('请先选择事件')
    return
  }

  const candidates = []
  if (selectedRow.value.eventName) {
    const res = await fileApi.search(selectedRow.value.eventName, true)
    candidates.push(...res.data.map((id) => [reportId, id, 'keyword']))
  }

  pairCandidate.value = dedupePairs(candidates)
  if (pairCandidate.value.length === 0) {
    ElMessage.info('未找到候选关联事件')
  } else {
    ElMessage.success(`找到 ${pairCandidate.value.length} 条候选关联事件`)
  }
}


function refreshMindMap() {
  if (!selectedRow.value?.reportId) return
  dataApi.getEventLink(selectedRow.value.reportId).then((res: Response) => {
    eventLinks.value = res.data
    mindMapRef.value?.refresh()
  })
}
</script>

<template>
  <div>
    <el-row :gutter="50" class="content-row">
      <el-col :span="8" class="first-col">
        <div class="to-select-list-container">
          <ToSelectList
            :events-list-table-data="selectedItems"
            @handleSelectionChange="handleSelectionChanged"
          />
        </div>
        <div class="method-selected">
          <CorrelationMethodSelected ref="methodRef" />
        </div>

        <div class="details-container">
          <Details :row="selectedRow" ref="detailsRef" />
        </div>
      </el-col>
      <el-col :span="16" class="second-col">
        <MindMap :row="eventLinks" :main-event="selectedRow.eventName" ref="mindMapRef" />
      </el-col>
    </el-row>
    <div class="option-row">
      <div>
        <el-button type="primary" @click="handleAssociate">
          <el-icon><VideoPlay /></el-icon>开始关联
        </el-button>
        <el-button @click="refreshMindMap">刷新关联图</el-button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.content-row {
  height: 80vh;

  .first-col {
    height: 100%;

    .to-select-list-container {
      height: 47%;
      margin-bottom: 1vh;
    }

    .method-selected {
      height: 20%;
      margin-bottom: 1vh;
    }

    .details-container {
      height: 30%;
    }
  }

  .second-col {
    height: 100%;
    width: 50%;
  }
}

:deep(.el-icon) {
  margin-right: 5px;
}

.option-row {
  padding-top: 20px;
  height: 50px;
  width: 100%;
  display: flex;
  justify-content: flex-end;
}
</style>
