<script>
import ResultCard from '@/views/data/DataAcquisition/ResultCard.vue'
import ResultCardContainer from '@/views/data/DataAcquisition/ResultCardContainer.vue'
import { getCrawlUrlAndKeywords } from '@/views/data/DataSourceAcquisition/crawler.js'
import dataApi from '@/api/dataApi.js'
import { ref } from 'vue';

const loading = ref(false);

export default {
  name: 'DefaultSource',
  components: { ResultCardContainer, ResultCard },
  data() {
    return {
      link_url_address: '',
      crawl_command: [],
      resultData: {},
      allResultData: [],
      loading,
      urlAndKeyword: [],
      selectedTemplateTitle: '',
      isLinkUrlVisible: true
    }
  },
  mounted() {
    this.fetchTemplateData()
    const crawllink_url = getCrawlUrlAndKeywords();
    if (crawllink_url) {
      // this.link_url_address = crawllink_url;
      this.isLinkUrlVisible = false
      this.urlAndKeyword = crawllink_url
      console.log('从共享存储获取的link_url:', crawllink_url);
    }
  },
  methods: {
    async startCrawl() {
      try {
        loading.value = true;
        let link = []
        if (this.urlAndKeyword && this.urlAndKeyword.length > 0) {
          link = this.urlAndKeyword.map(item => {
            return { keyword: item.keyword, url: item.url }
          });
        } else {
          if (!this.link_url_address) {
            throw new Error('URL 地址不能为空');
          } else {
            link = [{url:this.link_url_address,keyword:""}];
          }
        }
        const response = await dataApi.postSpiderData(link, this.selectedTemplateTitle);

        if (!response) {
          throw new Error('未收到响应');
        }

        const respData = response;
        if (!respData) {
          throw new Error('响应格式错误，data 字段不存在');
        }
        if (respData.code != 20000 && respData.message !== 'success') {
          const msg = respData.message || '爬取失败';
          this.$message.error(msg);
          return;
        }
        this.allResultData = respData.data.data;
        this.resultData = [this.allResultData[0].data]
        this.$message.success('爬取成功');

      } catch (err) {
        console.error('startCrawl 出错：', err);
        const msg = err.message || '请求失败，请稍后重试';
        this.$message.error(msg);
      } finally {
        loading.value = false;
      }
    },
    async fetchTemplateData() {
      try {
        loading.value = true
        const res = await dataApi.getTemplate()
        this.crawl_command = res.data.templateList
      }
      catch {
        this.$message.error("采集模板获取错误")
      }
      finally {
        loading.value = false
      }
    },
    selectUrl(url) {
      const AllData = this.allResultData
      const matchedItem = AllData.find(item => item.url === url);
      if (matchedItem) {
        this.resultData = [matchedItem.data];
      } else {
        this.resultData = [];
      }

      console.log(this.resultData)
    }

  }
}

</script>
<template>
  <div class="outer-wrapper">
    <el-row :gutter="20">
      <el-col :span="11">
        <el-card id="search" class="search-card" shadow="hover">

          <el-form label-width="auto">
            <el-form-item label="目标网址" v-if="isLinkUrlVisible">
              <el-input placeholder="请输入 link_url 地址" v-model="link_url_address" clearable />
            </el-form-item>

            <el-form-item label="爬取指令">
              <el-select v-model="selectedTemplateTitle" placeholder="请选择模板" style="width: 100%">
                <el-option v-for="(cmd, idx) in crawl_command" :key="idx" :label="cmd.templateTitle"
                  :value="cmd.templateTitle" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button v-loading.fullscreen.lock="loading" type="primary" @click="startCrawl" class="crawl-btn">
                动态数据自动解析
              </el-button>
            </el-form-item>

            <el-divider content-position="left" />
            <ul class="url-keyword-list">
              <li v-for="(item, index) in urlAndKeyword" :key="index" class="item" @click="selectUrl(item.url)">
                <div class="item-content">
                  <div class="url">
                    <el-icon color="#409EFF" size="16">
                      <Link />
                    </el-icon>
                    <span>{{ item.url }}</span>
                  </div>
                  <div class="keyword">
                    <el-tag type="success" size="small">{{ item.keyword }}</el-tag>
                  </div>
                </div>
              </li>
            </ul>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="13">
        <el-card id="result" class="result-list-container-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>爬取结果</span>
              <span style="color: gray;font-size: 0.8em;font-weight: normal;">动态数据识别准确率F1值≈85.54%</span>
            </div>
          </template>
          <ResultCardContainer :resultData="resultData" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Link } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
.outer-wrapper {
  padding: 15px;
  background-color: #f8f9fb;
  min-height: 100vh;
}

.search-card,
.result-list-container-card {
  height: 84vh;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  justify-content: space-between;
}

.url-keyword-list {
  list-style: none;
  padding: 0;
  margin: 0 0 10px;
  height: 50vh;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #dcdfe6;
    border-radius: 3px;
  }
}

.item {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background-color: #fff;
  margin-bottom: 10px;
  padding: 10px 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}

.url {
  color: #409EFF;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  word-break: break-all;
}

.keyword {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.crawl-btn {
  width: 100%;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
  }
}
</style>
