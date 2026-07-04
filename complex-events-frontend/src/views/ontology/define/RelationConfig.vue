<script setup>
import { useOntologyStore } from '@/stores/ontologyStore.js'
import { onMounted, ref, watch } from 'vue'
import FieldRelationShow from '@/views/ontology/define/FieldRelationShow.vue'

const props = defineProps({
  selectedConfig: {
    type: String,
    default: () => ({}),
    required: false
  }
})

const options = ref([])
const selected = ref('')
const fieldSelectedList = ref([])
const searchInput = ref('')
const postSearchInput = ref('')
const ontologyStore = useOntologyStore()
/**
 * 从 selectedConfig.extract_fields_list 同步 fieldSelectedList
 * @param {Object} config
 */
const syncFieldSelectedList = (config) => {
  if (!config || !Array.isArray(config.extract_fields_list)) {
    fieldSelectedList.value = []
    // console.log('🔄 selectedConfig 无有效 extract_fields_list，fieldSelectedList 置空')
    return
  }
  // console.log('🔄 同步 selectedConfig.extract_fields_list 到 fieldSelectedList:', config.extract_fields_list)
  const fields = Array.from(
    new Set(
      config.extract_fields_list
        .map(item => item?.field)
        .filter(Boolean)
    )
  )

  fieldSelectedList.value = fields
  options.value = fields
  console.log('🔄 从 selectedConfig.extract_fields_list 同步字段：', fields)
}

/**
 * 获取本体系统选项，并同步 fieldSelectedList
 * @param {Object} currentConfig - 当前要使用的 selectedConfig
 */
const fetchOptions = (currentConfig = props.selectedConfig) => {
  try {
    const ex_list = ontologyStore.getAllOntoConfigs || [];
    const matchedConfig = ex_list.find(item => {
      return item?.label === currentConfig;
    });
    syncFieldSelectedList(matchedConfig);
  } catch (error) {
    console.error('❌ 获取本体系统选项失败：', error)
    syncFieldSelectedList(currentConfig)
  }
}

onMounted(() => {
  // ontologyStore.initData()

  fetchOptions()
})

watch(
  () => ontologyStore.ontologyConfigurations, // 监听Store中的本体配置列表
  (newConfigs, oldConfigs) => {
    if (JSON.stringify(newConfigs) === JSON.stringify(oldConfigs)) return;

    console.log('🔄 ontologyStore.ontologyConfigurations 变化，重新执行 fetchOptions');
    fetchOptions();
  },
  { deep: true, immediate: false }
)

watch(
  () => props.selectedConfig,
  (newConfig, oldConfig) => {
    if (JSON.stringify(newConfig) === JSON.stringify(oldConfig)) return;

    // console.log('🔄 props.selectedConfig 变化，重置选中状态');
    fetchOptions();
    if (!fieldSelectedList.value.includes(selected.value)) {
      selected.value = ''
      // console.log('🔄 原检索本体不在新字段列表中，已重置')
    }
  },
  { deep: true, immediate: true }
)

watch(
  () => fieldSelectedList.value,
  (newList) => {
    if (!newList.includes(selected.value)) {
      selected.value = ''
      // console.log('🔄 展示字段列表变化，重置检索本体选择')
    }
  }
)

const handleSearch = () => {
  if (!selected.value) {
    console.warn('⚠️  请先选择要检索的本体')
    return
  }
  postSearchInput.value = searchInput.value
  console.log(`🔍 触发检索：本体=${selected.value}，内容=${postSearchInput.value}`)
}
</script>

<template>
  <el-row :gutter="10" class="config-row">
    <el-col :span="3">
      <el-select v-model="selected" class="selector" placeholder="选择要检索的本体" :disabled="fieldSelectedList.length === 0">
        <el-option v-for="field in fieldSelectedList" :key="field" :value="field">
          {{ field }}
        </el-option>
      </el-select>
    </el-col>

    <el-col :span="5">
      <el-input class="input" placeholder="请输入检索内容" v-model="searchInput"></el-input>
    </el-col>

    <el-col :span="2">
      <el-button type="primary" @click="handleSearch">
        检索
      </el-button>
    </el-col>

    <el-col :offset="4" :span="10">
      <div class="field-selector">
        <label class="field-label">提取字段：</label>
        <el-select v-model="fieldSelectedList" class="field-select" multiple placeholder="提取字段列表">
          <el-option v-for="item in options" :key="item" :value="item" :label="item" />
          <el-option v-if="fieldSelectedList.length === 0" disabled value="">
            无提取字段（extract_fields_list 为空/无效）
          </el-option>
        </el-select>
      </div>
    </el-col>
  </el-row>

  <el-scrollbar class="details">
    <el-row v-if="fieldSelectedList.length > 0" v-for="(item, index) in fieldSelectedList"
      :key="`field-${index}-${item}`" :gutter="10" class="details-row">
      <FieldRelationShow :field-name="item" :config="fieldSelectedList"
        :search-text="postSearchInput" />
    </el-row>
    <el-empty v-else style="margin-top: 20vh" description="无提取字段可展示" />
  </el-scrollbar>
</template>

<style lang="scss" scoped>
.field-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.field-label {
  white-space: nowrap;
  color: #606266;
}

.field-select {
  flex: 1;
}

.config-row {
  height: auto;
  padding-bottom: 2vh;
  align-items: center;
}

.details {
  height: 80%;

  .details-row {
    width: 98%;
    padding: 20px;
    border-bottom: 1px solid #f2f2f2;

    &:last-child {
      border-bottom: none;
    }
  }
}

.selector,
.input {
  width: 100%;
}
</style>
