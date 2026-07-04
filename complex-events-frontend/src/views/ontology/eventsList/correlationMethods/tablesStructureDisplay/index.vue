<template>
  <div style="width: 100%; height: 100%">
    <div>
      <el-button @click="handleSelectionChanged">{{ selectedRow.eventName }}</el-button>
    </div>
    <el-table :data="eventLink" style="width: 100%; height: 90%">
      <el-table-column prop="mainEvent" label="头标签" />
      <el-table-column prop="relatedEvent" label="尾标签" />
      <el-table-column prop="relation.type" label="关系" />
      <el-table-column prop="relevantEventDetails.title" label="标题" />
      <el-table-column label="置信度">
        <template #default="{ row }">
          {{ row.relation.confidenceDegree ?? '无置信度' }}
        </template>
      </el-table-column>
      <el-table-column label="原因">
        <template #default="{ row }">
          {{ row.relation.reason ?? '无原因' }}
        </template>
      </el-table-column>
      <el-table-column label="规则">
        <template #default="{ row }">
          {{ row.user_rule ?? '无规则' }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import dataApi from '@/api/dataApi'
import { computed, ref } from 'vue'
import { OntologySystemData } from '@/views/ontology/ontologySystem'
import { EventLink } from '@/views/ontology/eventsList/correlationTab'
defineOptions({name:'TablesStructure'})
const props = defineProps({
  selectedItems: {
    type: Array<OntologySystemData>,
    default: () => [],
  },
})

const eventLink = ref<EventLink[]>([])
const selectedRow = computed<OntologySystemData | ''>(() => {
  if (props.selectedItems && props.selectedItems.length > 0) {
    return props.selectedItems[0]
  } else {
    return ''
  }
})

function handleSelectionChanged() {
  const newRow = selectedRow.value
  dataApi.getEventLink(newRow.reportId, false).then((res) => {
    eventLink.value = res.data
    console.log(res.data)
  })
}
</script>
<style scoped lang="scsss"></style>
