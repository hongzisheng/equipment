<template>
  <el-tag :type="tagType" size="small" effect="light" :class="tagClass">
    {{ statusText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusTagType, getStatusText } from '../utils'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  class: {
    type: String,
    default: ''
  }
})

const tagType = computed(() => getStatusTagType(props.status))
const statusText = computed(() => getStatusText(props.status))
const tagClass = computed(() => props.class)
</script>

<style scoped>
</style>