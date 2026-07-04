<script setup lang="ts">
import { useOntologyStore } from '@/stores/ontologyStore'
import { computed } from 'vue'

const ontologyStore = useOntologyStore()
const configOpts = computed(() => {
  return ontologyStore.ontologyConfigurations
})
const selected = defineModel()
</script>

<template>
  <div class="selector-container">
    <el-select v-model="selected" clearable>
      <el-option
        v-for="item in configOpts"
        :key="item.label"
        :label="item.label"
        :value="item.label"
      />
    </el-select>
  </div>
</template>

<style scoped lang="scss">
.selector-container {
  width: 100%;
  height: 100%;
}
</style>
