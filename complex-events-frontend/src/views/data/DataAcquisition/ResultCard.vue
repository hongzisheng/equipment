<script>
export default {
  name: 'ResultCard',
  props: {
    resultDataItem: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      dataFrom: '新浪来源',
      activeName: '文本',
    }
  },
  methods: {
  },
}
</script>

<template>
  <el-card class="result-card" shadow="never" style="max-width: 99%">
    <template #header>
      <div class="card-header">
        <span>
          <div class="text-clamp-1">{{ resultDataItem.title }}</div>
        </span>
      </div>
    </template>
    <el-tabs v-model="activeName" class="demo-tabs">
      <el-tab-pane label="事件关联文本数据" name="文本">
        <div class="text-clamp-2">{{ resultDataItem.details }}</div>
      </el-tab-pane>
      <el-tab-pane label="事件关联图片数据" name="图片">
        <div class="text-clamp-2">
          <div v-for="(img, idx) in resultDataItem.images" :key="idx" class="image-item">
            <a :href="img" target="_blank" rel="noopener">{{ img }}</a>
          </div>
          <div v-if="!resultDataItem.images || resultDataItem.images.length === 0" class="empty‑msg">
            无图片链接
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="事件关联视频数据" name="视频">
        <div class="text-clamp-2">
          <div v-for="(video, idx) in resultDataItem.video" :key="idx" class="image-item">
            <a :href="video" target="_blank" rel="noopener">{{ video }}</a>
          </div>
          <div v-if="!resultDataItem.video || resultDataItem.video.length === 0" class="empty‑msg">
            无视频链接
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="其他资源" name="其他资源">{{ resultDataItem.other_source }}</el-tab-pane>
    </el-tabs>
    <template #footer>
      <span>
        <div class="text-clamp-1">来源：{{ resultDataItem.link_url }}</div>
      </span>
    </template>
  </el-card>
</template>

<style lang="scss" scoped>
.result-card {
  transition: all 0.3s ease;
  border: 2px solid #e3e3e3;
  border-radius: 20px;
  cursor: pointer;

  &:hover {
    border-color: var(--my-system-primary-color); // 使用系统主题色
    border-width: 5px;
    // 阴影
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.1);
  }

  // 使用伪元素创建自定义分割线
  :deep(.el-card__header) {
    position: relative;
    border-bottom: none;
    padding: 18px 20px;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 20px;
      right: 20px;
      height: 1px;
      background-color: #ebeef5;
    }
  }

  // 使用伪元素创建自定义分割线
  :deep(.el-card__footer) {
    position: relative;
    border-top: none;
    padding: 18px 20px;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 20px;
      right: 20px;
      height: 1px;
      background-color: #ebeef5;
    }
  }
}

.text-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
}

.text-clamp-1 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
  text-overflow: ellipsis;

  white-space: normal;
}
</style>
