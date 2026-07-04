<script setup lang="ts">
import supportFileFormats from '@/views/data/DataManage/supportFileFormats'
</script>

<template>
  <div class="tags-line">
    <el-text class="tips-title">支持格式</el-text>
    <el-space>
      <el-tag
        v-for="supportFile in supportFileFormats"
        :key="supportFile.label"
        :style="{ 'background-color': supportFile.color, 'border-width': 0 }"
        effect="dark"
        round
      >
        {{ supportFile.label }}
      </el-tag>
    </el-space>
    <span class="data-type">支持的数据类型=14种</span>
  </div>
</template>
<style lang="scss" scoped>
.tags-line {
  display: flex;
  flex-direction: row; // 明确指定水平排列

  .tips-title {
    width: 5em;
    flex-shrink: 0; // 防止在空间不足时缩小
  }
  .data-type{
    font-size: 0.7em;
    margin-left: 1em;
    justify-content: center;
    align-content: center;
  }
}
</style>
