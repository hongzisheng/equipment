<script>
import ResultCard from '@/views/data/DataAcquisition/ResultCard.vue'
import { setAssociatedData } from '@/views/data/DataSourceAcquisition/crawler.js'

export default {
  name: 'ResultCardContainer',
  components: { ResultCard },
  props: {
    resultData: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      selectedItem: null
    }
  },
  computed: {
    resultLength() {
      return this.resultData.length
    }
  },
  methods: {
    handleClick(item) {
      this.selectedItem = item
    },
    correlationCrawl() {
      console.log('要关联爬取的 item：', this.selectedItem)
      setAssociatedData({ "title": this.selectedItem["title"], "details": this.selectedItem["details"] })
      this.$router.push('/data/DataSourceAcquisition');
    }
  }
}
</script>

<template>
  <el-scrollbar class="result-list-container-scrollbar">
    <ul class="result-list">
      <li v-for="(o, idx) in resultData" :key="o.id != null ? o.id : idx" @click="handleClick(o)">
        <ResultCard :resultDataItem="o" />
      </li>
    </ul>
  </el-scrollbar>
  <div style="margin-top: 20px">结果数量：{{ resultLength }}</div>
  <el-divider style="margin-bottom: 5px; margin-top: 10px;" />
  <e-div style="margin-top: 20px">
    <div v-if="selectedItem">
      <div>详细信息：</div>
      <e-divider></e-divider>
      <el-card class="result-card" shadow="never" style="max-width: 99%">
        <template #header>
          <div class="card-header">
            <span>
              <div class="text-clamp-1">{{ selectedItem.title }}</div>
            </span>
          </div>
        </template>
        <el-tabs v-model="activeName" class="demo-tabs">
          <el-tab-pane label="事件关联文本数据" name="事件关联文本数据">
            <div class="text-clamp-3">{{ selectedItem.details }}</div>
          </el-tab-pane>
          <el-tab-pane label="事件关联图片数据" name="事件关联图片数据">
            <div class="text-clamp-1" style="height: 4vh;">
              <div v-for="(img, idx) in selectedItem.images" :key="idx" class="image-item">
                <a :href="img" target="_blank" rel="noopener">{{ img }}</a>
              </div>
              <div v-if="!selectedItem.images || selectedItem.images.length === 0" class="empty‑msg">
                无图片链接
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="事件关联视频数据" name="事件关联视频数据">
            <div class="text-clamp-1" style="height: 4vh;">
              <div v-for="(video, idx) in selectedItem.video" :key="idx" class="image-item">
                <a :href="video" target="_blank" rel="noopener">{{ video }}</a>
              </div>
              <div v-if="!selectedItem.video || selectedItem.video.length === 0" class="empty‑msg">
                无视频链接
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="其他资源" name="其他资源">{{ selectedItem.other_source }}</el-tab-pane>
        </el-tabs>
        <template #footer>
            <div>来源：<a :href="selectedItem.link_url">{{ selectedItem.link_url }}</a></div>
        </template>
      </el-card>
      <div class="crawl-btn-container">
        <el-button type="primary" class="crawl-btn" @click="correlationCrawl">
          关联爬取
        </el-button>
      </div>
    </div>
    <div v-else>
      <span>请选择一条记录查看详情</span>
    </div>
  </e-div>
</template>

<style lang="scss" scoped>
.result-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    margin-bottom: 10px;
    cursor: pointer;
  }
}

.result-card {
  margin-top: 10px;
}

.result-list-container-scrollbar {
  height: 33vh;
}

.crawl-btn-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.crawl-btn {
  background-color: #409eff;
  color: #fff;
  border: none;
}

.text-clamp-1,
.text-clamp-3 {
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}


.text-clamp-1 {
  white-space: nowrap;
  text-overflow: ellipsis;
}

.text-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 3;
  box-orient: vertical;
}
</style>
