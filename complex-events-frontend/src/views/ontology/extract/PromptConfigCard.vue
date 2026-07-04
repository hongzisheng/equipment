<template>
  <el-card>
    <template #header>
      <label>多模态数据中的关键要素抽取</label>
    </template>
    <div class="forms">
      <el-form label-width="auto" class="form-container">
        <el-form-item label="本体约束下的数据体系">
          <div class="select-config-item">
            <el-select class="select-config-item-selector" placeholder="选择配置（需要先选择数据）" v-model="configName"
              disabled></el-select>
            <el-button plain round type="primary">
              <el-icon>
                <Plus />
              </el-icon>
              新建配置
            </el-button>
          </div>
        </el-form-item>

        <!-- <ElDivider/> -->
        <el-form-item label="多模态数据中的关键要素">
          <OntologyCheckboxRows v-model="formData.checkedItems" :one-row-display-num="4" class="checkbox-container" />
        </el-form-item>
        <el-form-item>
          <template #label>
            <div class="label-container">
              <span class="label-text">提 示 词</span>
              <el-select class="label-select" placeholder="选择模板"></el-select>
            </div>
          </template>
          <el-input :spellcheck="false" v-model="prompt" :rows="5" placeholder="请输入内容" type="textarea"></el-input>
        </el-form-item>
        <el-form-item>
          <template #label>
            <div class="label-container">
              <span class="label-text">特定类型事件的触发词识别</span>
              <el-button @click="addTrigger">
                <el-icon>
                  <Plus />
                </el-icon>
              </el-button>
            </div>

          </template>
          <div v-for="(value, index) in formData.triggerList" class="trigger-box-container">
            <div class="input-style">
              <el-input v-model="value.focusEventType" placeholder="事件类型" />
              <div class="connector"></div>
              <el-input v-model="value.tiaggerWords" placeholder="触发词" />
            </div>
            <el-button @click="deleteTrigger(index)" class="delete-button">
              <el-icon>
                <Delete />
              </el-icon>
            </el-button>
          </div>
        </el-form-item>
        <el-form-item class="switches-form-item">
          <div class="switches-container">
            <div class="switch-item">
              <label>事件关联多模态数据</label>
              <el-switch v-model="formData.isMultimodal" />
            </div>
            <div class="switch-item">
              <label>事件目标的轨迹数据获取</label>
              <el-switch v-model="formData.isPlaceCoordinate" />
            </div>
            <div class="switch-item">
              <label>事件关联数据的语义扩充</label>
              <el-switch v-model="formData.dataExtent" />
            </div>
          </div>
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <div class="option-buttons">
        <div>
          <el-button>
            <el-icon>
              <RefreshLeft />
            </el-icon>
            重置
          </el-button>
          <el-button type="primary" plain @click="emits('savePrompt', formData)">
            <el-icon>
              <Document />
            </el-icon>
            保存修改
          </el-button>
        </div>
        <div>
          <el-button type="primary" @click="emits('startExtract', prompt)"> 事件关联的属性信息识别 </el-button>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { Document, Plus, RefreshLeft, Delete } from '@element-plus/icons-vue'
import OntologyCheckboxRows from '@/commomComponents/OntologyCheckboxRows.vue'
import { computed, reactive, ref, watch } from 'vue'
import { useOntologyStore } from '@/stores/ontologyStore'
import { ElDivider, selectEmits } from 'element-plus'
import { Report } from '@/views/ontology/eventsList/correlationTab'

defineOptions({
  name: 'PromptConfig',
})

const prompt = ref('')
const checkedItems = ref([])
const props = defineProps<{
  selectedItems?: Report
}>()
const ontologyStore = useOntologyStore()

interface Trigger {
  focusEventType: string,
  tiaggerWords: string,
}

const formData = reactive<{
  promptConfig: string,
  prompt: string,
  checkedItems: string[],
  triggerList: Trigger[],
  isMultimodal: boolean,
  isPlaceCoordinate: boolean,
  dataExtent: boolean,
}>({
  promptConfig: '',
  prompt: '',
  checkedItems: [],
  triggerList: [{
    focusEventType: "商业活动",
    tiaggerWords: "开业",
  },
  {
    focusEventType: "",
    tiaggerWords: "",
  }],
  isMultimodal: false,
  isPlaceCoordinate: false,
  dataExtent: false,
})

function addTrigger() {
  formData.triggerList.push({
    focusEventType: "",
    tiaggerWords: "",
  })
}

function deleteTrigger(index) {
  formData.triggerList.splice(index, 1)
}

watch(
  () => props.selectedItems,
  () => {
    if (props.selectedItems) {
      const configFields = ontologyStore.getConfigFields(configName.value)
      formData.checkedItems = configFields.map((item) => item.field)
      const allPrompts = ontologyStore.getAllOntologyObject
      formData.prompt = ''
      configFields.forEach((config) => {
        const strategy = config.SelectedStrategy
        formData.prompt +=
          allPrompts
            .find((p) => p.label == config.field)
            .promptList.find((list) => Number(list.key) == strategy).prompt + '\n\n'
      })
    }
  },
)
const configName = computed(() => {
  return props.selectedItems?.config ?? ''
})

watch(() => formData.checkedItems,
  (newVal) => {
    const config = ontologyStore.ontologyConfigurations
    const ontologyPrompt = ontologyStore.ontologyPrompt
    const configIndex = config.findIndex((item) => item.label === configName.value)
    const configFields = config[configIndex]?.extract_fields_list || []
    const promptObject = {}
    newVal.forEach((field) => {
      const strategy = configFields.find((f) => f.field == field)?.SelectedStrategy??1
      const fieldItem = ontologyPrompt.find((p) => p.label == field)
      console.log('ptomptItemList', fieldItem)
      const fieldItemPromptText = fieldItem.promptList.find((list) => Number(list.key) == strategy)?.prompt ?? ""
      const promptKey = fieldItem.promptKey??fieldItem.prop
      promptObject[promptKey] = fieldItemPromptText
      // console.log('ptomptItemText', ptomptItemText)
    })
    prompt.value = "{\n" +
      Object.entries(promptObject)
        .map(([k, v]) => `  "${k}": ${v}`)
        .join(",\n") +
      "\n}";

  }
)

const emits = defineEmits(['savePrompt', 'startExtract'])
</script>

<style lang="scss" scoped>
.trigger-box-container {
  margin-top: 0.5em;
  display: flex;
  justify-content: space-between;
  align-content: center;
  width: 100%;
  gap: 10px;

  .input-style {
    width: 90%;
    display: flex;

    .el-input {
      width: 48%;
    }

    .connector {
      width: 4%;
      height: 1px;
      background-color: #ccc;
      margin: auto 0;
    }
  }



  .delete-button {
    margin-left: 0.2em;
  }
}

.label-container {
  display: flex;
  flex-direction: column;
  /* 垂直排列 */
  align-items: flex-end;
  gap: 5px;

  .label-text {
    font-weight: bold;
  }
}

.tiagger-dialog {
  width: 40%;
}

.label-select {
  width: 100px;
}

.select-config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  &-selector {
    width: 40%;
  }
}

.forms {
  height: 100%;
  width: 100%;
  display: block;

  .form-container {
    height: 90%;
    width: 100%;

    .recognition-trigger {
      width: 100%;
    }

    .switches-form-item {
      :deep(.el-form-item__content) {
        flex-wrap: wrap;
      }
    }

    .switches-container {
      display: flex;
      justify-content: space-between;
      width: 100%;
    }

    .switch-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.option-buttons {
  display: flex;
  justify-content: space-between;
  align-content: center;
  gap: 10px;
}

:deep(.el-card__header) {
  height: 10%;
  display: flex;
  align-content: center;
}

:deep(.el-card__body) {
  height: 80%;
}

:deep(.el-card__footer) {
  height: 10%;
  padding-top: calc(1%);
  padding-bottom: 0;
}
</style>
