<script setup lang="ts">
import { getOntologySystemOptions } from '@/views/ontology/ontologySystem'
import { string } from 'fast-glob/out/utils'
import { OntologyPromptOption } from '@/stores/ontologyStore'

const selected = defineModel()
const options = getOntologySystemOptions()
const props = withDefaults(
  defineProps<{
    placeholder?: string
    multiple?: boolean
    clearable?: boolean
    // 是否将值绑定成prop而不是label，默认情况下value=label
    selectedProp?: boolean
    // 哪些选项禁止选择
    disabledItems?: OntologyPromptOption[]
  }>(),
  {
    placeholder: '请选择',
    multiple: false,
    clearable: false,
    selectedProp: false,
    disabledItems: null,
  },
)
</script>

<template>
  <el-select
    v-model="selected"
    :placeholder="placeholder"
    :multiple="multiple"
    :clearable="clearable"
  >
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="selectedProp ? item.prop : item.value"
      :disabled="disabledItems!=null && disabledItems.some((i) => i.value == item.value)"
    >
    </el-option>
  </el-select>
</template>

<style scoped lang="scss"></style>
