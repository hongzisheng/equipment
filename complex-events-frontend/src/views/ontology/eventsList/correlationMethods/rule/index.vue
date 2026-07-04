<script setup lang="ts">
import associateApi from '@/api/associateApi'
import { nextTick, onBeforeMount, ref } from 'vue'
import RuleDetail from '@/views/ontology/eventsList/correlationMethods/rule/RuleDetail.vue'
import { Plus } from '@element-plus/icons-vue'
import { AssociateRule } from '@/views/ontology/eventsList/correlationMethods/rule/index'

defineOptions({ name: 'Rule' })

const currentTabName = ref('')

const rules = ref<AssociateRule[]>([])

function init() {
  associateApi.getAllRules().then((res) => {
    rules.value = res.data
    currentTabName.value = rules.value[0].rule_title ?? ''
  })
}

onBeforeMount(() => {
  init()
})

function addRules() {
  const newTitle = '新建规则' + rules.value.length
  rules.value.push({
    rule_title: newTitle,
  })
  currentTabName.value = newTitle
}

const handleAfterSaveSuccess = (rule: AssociateRule, newTitle: string) => {
  rule.rule_title = newTitle
  nextTick(() => {
    currentTabName.value = newTitle
  })
}
const props = defineProps<{
  selectedItems: any[] // 根据实际类型调整
}>()
</script>

<template>
  <div class="rules-container">
    <el-scrollbar class="rule-scrollbar">
      <div v-for="rule in rules">
        <RuleDetail
          :current-rule="rule"
          @save-success="(title) => handleAfterSaveSuccess(rule, title)"
        />
        <el-divider />
      </div>
    </el-scrollbar>
  </div>
</template>

<style lang="scss" scoped>
.rules-container {
  width: 100%;
  height: 100%;
  .rule-scrollbar {
    width: 100%;
    height: 100%;
  }
}
</style>
