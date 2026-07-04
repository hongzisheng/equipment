<script>
import dataApi from '@/api/dataApi'
import { setCrawlUrlAndKeywords, getAssociatedData } from '@/views/data/DataSourceAcquisition/crawler.js'
import { ref } from 'vue';
const loading = ref(false);

export default {
  name: 'DataSourceAcquisition',
  data() {
    return {
      searchQuery: '',
      casSearchQuery: '',
      tableFilterQuery: '',
      default_search_keywords: [],
      dataList: [],
      loading,
      selectedItem: [],
      cas_keywords: ''
    }
  },
  computed: {
    filteredDataList() {
      const query = this.tableFilterQuery.trim().toLowerCase();
      if (!query) {
        return this.dataList;
      }
      return this.dataList.filter(item => {
        const titleMatch = item.title.toLowerCase().includes(query);
        const keywordMatch = item.keyword.toLowerCase().includes(query);
        const urlMatch = item.url.toLowerCase().includes(query);
        return titleMatch || keywordMatch || urlMatch;
      });
    }
  },
  mounted() {
    const default_keywords = getAssociatedData();
    if (default_keywords) {
      this.fetchData(default_keywords);
    }
  },
  methods: {
    async fetchData(keywords) {
      try {
        loading.value = true;
        const response = await dataApi.postConnectData(keywords);
        this.default_search_keywords = response.data.keywords;
        this.searchQuery = this.default_search_keywords.join(' ');
      } catch (error) {
        console.error('API调用失败:', error);
      } finally {
        loading.value = false;
      }
    },
    async handleSearch() {
      if (!this.searchQuery.trim()) {
        this.$message.warning('请输入搜索关键词');
        return;
      }

      try {
        loading.value = true;
        this.cas_keywords = this.searchQuery
        console.log('搜索关键词:', this.searchQuery);
        const res = await dataApi.postDataSource(this.searchQuery);

        if (res.code === 20000 && res.message === 'success') {
          this.dataList = res.data.results;
          this.$message.success(`搜索成功，找到 ${this.dataList.length} 个数据源`);
        } else {
          this.$message.error('搜索失败：' + (res.message || '未知错误'));
        }
      } catch (error) {
        console.error('搜索数据源出错:', error);
        this.$message.error('网络错误，搜索失败');
      } finally {
        loading.value = false;
      }
    },
    handleCrawl() {
      const urlAndKeyword = this.selectedItem.map(item => {
        return {
          url: item.url,
          keyword: item.keyword
        };
      });
      console.log(urlAndKeyword)
      setCrawlUrlAndKeywords(urlAndKeyword);
      this.$router.push('/data/acquisition');
    },
    handleRetrieval() {
      this.tableFilterQuery = this.casSearchQuery.trim();
    },
    handleSelectionChange(data) {
      this.selectedItem = data
    }
  }
}
</script>

<template>
  <el-row class="mt-4">

    <el-col :span="10" style="margin-right: 1%;">
      <div class="inline-wrapper">
        <span class="title-text" style="width: 20rem;">弱信息下的数据源发现</span>
        <el-input class="width-input" v-model="searchQuery" placeholder="输入关键词 …（';'间隔）"
          :input-style="{ width: '300px' }" />
      </div>
    </el-col>
    <el-col :span="1" style="margin-right: 7%;">
      <el-button @click="handleSearch" type="primary">搜索</el-button>
    </el-col>
    <span class="title-text" style="margin-right: 2%;">
      人机交互的数据源筛选
    </span>
    <el-col :span="5" style="align-items:center;">
      <el-input v-model="casSearchQuery" placeholder="请输入内容筛选表格数据（标题、关键词或链接）" style="width: 100%;" />
    </el-col>
    <el-col :span="1" style="margin-right: 8%;">
      <el-button @click="handleRetrieval" type="primary" style="margin-left: 20%;">筛选</el-button>
    </el-col>
  </el-row>

  <el-row v-loading="loading" class="mt-4">
    <el-col :span="24">
      <el-table :data="filteredDataList" style="width: 100%; height: 82vh;"
        :header-cell-style="{ 'text-align': 'center' }" :cell-style="{ 'text-align': 'center' }" max-height="700"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center"></el-table-column>
        <el-table-column prop="title" label="标题" :min-width="25"></el-table-column>
        <el-table-column label="关键词" :min-width="25">
          <template #default="{ row }">
            {{ cas_keywords }}
          </template>
        </el-table-column>
        <el-table-column prop="keyword" label="事件信息词语义扩展" :min-width="25">
          <template #default="{ row }">
            {{ row.keyword }}
          </template>
        </el-table-column>
        <el-table-column prop="url" label="数据源链接" :min-width="25">
          <template #default="{ row }">
            <a :href="row.url" target="_blank" style="color: #409eff; word-break: break-all;">
              {{ row.url }}
            </a>
          </template>
        </el-table-column>

      </el-table>
    </el-col>
  </el-row>
  <div class="box_between">
    <span v-if="filteredDataList.length>0">关联数据发现准确率≈84%  数据来源类型=4类  数据源数量≈3000个  支持关键词≈3</span>
    <el-button @click="handleCrawl()" type="success" style="width: 10em;height: 2em;">
      大规模动态数据获取
    </el-button>
  </div>
</template>

<style scoped lang="scss">
.box_between{
  width: 100%;
  margin-top: 10px;
  text-align: right;
  padding-right: 5vw;
  span{
    margin-right: 60%
  }
}

.mt-4 {
  margin-top: 16px;
  padding-left: 1%;
  padding-right: 1%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.title-text {
  align-items: center;
}

.wide-input {
  width: 300px;
  display: inline-block;

  :deep(.el-input__inner) {
    width: 100% !important;
  }
}

.inline-wrapper {
  display: flex;
  align-items: center;
}
</style>
