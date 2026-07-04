<script setup>
/**
 * 本体定义界面的入口文件
 */

import { useOntologyStore } from '@/stores/ontologyStore'
import OntologySystem from '@/views/ontology/define/OntologySystem.vue'
import PromptTemplate from '@/views/ontology/define/PromptTemplate.vue'
import RelationConfig from '@/views/ontology/define/RelationConfig.vue'
import { ref, watch, onMounted, computed, onUnmounted } from 'vue'
import dataApi from '@/api/dataApi.js'
import { ElMessage } from 'element-plus'
import ontologyItemDisplay from './ontologyItemDisplay.vue'

const options = ref([])
const casOptions = ref([])
const selectedConfig = ref()
const selectedOntologyItem = ref('')
const dialogVisible = ref(false)
const newOntologyLabel = ref('')
const newOntologyValue = ref('')
const loading = ref(false)
const ontologyStore = useOntologyStore()

onMounted(async () => {
  options.value = ontologyStore.ontologyConfigurations;
});

const updateSelectedOntologyItem = (val) => {
  selectedOntologyItem.value = val
  console.log('父组件接收选中的本体项:', selectedOntologyItem.value)
}

onUnmounted(()=>{
  ontologyStore.resetState()
})

const handleReset = async () => {
  try {
    selectedConfig.value = '';
    dialogVisible.value = false;
    newOntologyLabel.value = '';
    newOntologyValue.value = '';
    await fetchOntologyConfigs();

    console.log('界面已重置并重新加载数据');

  } catch (error) {
    console.error('重置界面失败：', error);
  }
};

const handleSave = async () => {
  try {
    const ontology = ontologyStore.ontologyConfigurations
    const prompt = ontologyStore.ontologyPrompt
    const relation = ontologyStore.relations

    loading.value = true
    const response = await dataApi.postModifyOntologyData(ontology, prompt, relation);
    if (response.code === 20000) {
      ElMessage.success('所有修改已成功保存到后端');
      await ontologyStore.resetState();
    } else {
      // 后端返回非成功状态（如业务错误）
      ElMessage.error(`保存失败：${response.data?.message || '后端未返回明确原因'}`);
    }
  }
  catch (error) {
    console.error('保存修改失败：', error);
    ElMessage.error('保存修改失败。')
  }
  finally {
    loading.value = false;
  }
};


function handleConfirm() {
  options.value = JSON.parse(JSON.stringify(casOptions.value));
  ontologyStore.updateOntologyConfiguration(options.value, "label")
  dialogVisible.value = false
  newOntologyLabel.value = ''
  newOntologyValue.value = ''
}


function handleAddOntologyConfiguration() {
  dialogVisible.value = true
  casOptions.value = JSON.parse(JSON.stringify(options.value));
}

function handleUpdateLabel({ index, newLabel }) {
  casOptions.value[index].label = newLabel
  console.log("options", options.value)
}
function handleDelete(index) {
  casOptions.value.splice(index, 1)
  console.log("options", options.value)
}
function handleAdd() {
  casOptions.value.push({
    label: "",
    extract_fields_list: []
  })

  console.log("options", options.value)
}
watch(
  () => selectedConfig.value,
  (newVal, oldVal) => {
    console.log('watch selectedConfig变化：', '新值:', newVal, '旧值:', oldVal)
  },
  { immediate: true, deep: true }
)

</script>

<template>
  <div>
    <el-row class="content-row">
      <el-col :span="8" class="first-col">
        <div class="col-title">
          <span style="width: 30%;">事件动态本体</span>
          <el-select v-model="selectedConfig" class="config-selector" :loading="loading">
            <el-option v-for="item in options" :key="item.label" :label="item.label" :value="item.label" />
          </el-select>
          <el-button style="margin-left: 2vw;" @click="handleAddOntologyConfiguration">事件动态本体管理</el-button>
          <el-dialog v-model="dialogVisible" title="新增本体配置" width="30%">
            <div v-for="(item, index) in casOptions" :key="index">
              <ontologyItemDisplay :newOntologyLabelItem="item.label" :index="index" @update-label="handleUpdateLabel"
                @delete-item="handleDelete" />
            </div>
            <el-button @click="handleAdd">+</el-button>
            <template #footer>
              <el-button @click="dialogVisible = false">取消</el-button>
              <el-button type="primary" @click="handleConfirm">确认</el-button>
            </template>
          </el-dialog>
        </div>
        <el-divider></el-divider>

        <div class="ontology-system-container">
          <OntologySystem :selectedConfig="selectedConfig" @selectOntologyItem="updateSelectedOntologyItem" />
        </div>

        <div class="prompt-template-container">
          <PromptTemplate :selectedOntologyItem="selectedOntologyItem" />
        </div>
      </el-col>
      <el-col :span="16" class="second-col">
        <div class="col-title">
          <span>事件本体语义化关联配置</span>
        </div>
        <el-divider />
        <RelationConfig :selectedConfig="selectedConfig" />
      </el-col>
    </el-row>
    <el-row>
      <el-col :span="24">
        <el-divider />
      </el-col>
    </el-row>

    <el-row>
      <el-col :offset="21" :span="3">
        <el-button type="default" @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleSave">保存修改</el-button>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.content-row {
  height: 82vh;
  padding: 16px;
  box-sizing: border-box;

  .col-title {
    display: flex;
    align-items: center;
    height: 3vh;
    margin-bottom: 16px;
  }

  .first-col {
    height: 100%;
    border-right: #e3e3e3 1px solid;
    padding-right: 16px;
    box-sizing: border-box;

    .col-title {
      width: 90%;

      .config-selector {
        width: 50%;
        margin-left: 1vw;
      }
    }

    .ontology-system-container {
      height: 35%;
      margin-bottom: 24px;
      overflow-y: auto;
    }

    .prompt-template-container {
      height: calc(65% - 40px);
      overflow-y: auto;
    }
  }

  .second-col {
    height: 100%;
    padding-left: 16px;
    box-sizing: border-box;
  }

  .col-title {
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;
  }

  .col-title .el-button {
    margin-left: auto;
  }

  .config-selector {
    width: 200px;
  }
}
</style>
