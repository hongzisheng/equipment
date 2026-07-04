<script setup lang="ts">
import { defineProps, ref, watch, defineEmits } from 'vue'
import { Delete } from '@element-plus/icons-vue'

const props = defineProps({
  newOntologyLabelItem: {
    type: String,
    default: ''
  },
  index: {  
    type: Number,
    required: true
  }
})

const emit = defineEmits<{
  (e: 'update-label', payload: { index: number; newLabel: string }): void
  (e: 'delete-item', index: number): void
}>()

const newOntologyLabel = ref(props.newOntologyLabelItem)
watch(() => props.newOntologyLabelItem, (v) => {
  newOntologyLabel.value = v
})

function onLabelChange(val: string) {
  emit('update-label', { index: props.index, newLabel: val })
}

function deleteItem() {
  emit('delete-item', props.index)
}
</script>

<template>
  <el-form>
    <div class="box-container">
      <el-form-item label="名称">
        <el-input v-model="newOntologyLabel" @input="onLabelChange($event)" class="input-name" />
      </el-form-item>
      <el-button @click="deleteItem">
        <el-icon><Delete/></el-icon>
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.box-container{
    display: flex;
}
.input-name{
    width: 80%;
}
</style>
