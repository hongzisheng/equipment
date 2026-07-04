<script setup>
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router'
import dataApi from '@/api/dataApi.js';
import {setCrawlUrlAndKeywords } from '@/views/data/DataSourceAcquisition/crawler.js'
const props = defineProps({ eventData: Object });
const router = useRouter()
const loading = ref(false);
const dataList = ref([]);

async function fetchCorrectionData() {
    try {
        loading.value = true;
        const response = await dataApi.postCorrentionSearch({
            "标题": props.eventData.eventName,
            "事件": props.eventData.action
        });

        if (response.data && response.data.results) {
            dataList.value = response.data.results;
        } else {
            dataList.value = [];
        }

        console.log('Correction Data:', dataList.value);
    } catch (error) {
        console.error('Error fetching correction data:', error);
        dataList.value = [];
    } finally {
        loading.value = false;
    }
}

function handleCrawl(url, keyword) {
    console.log('待爬取的数据源URL:', url)
    setCrawlUrlAndKeywords([{url:url,keyword:keyword}])
    router.push('/data/acquisition')
}

watch(
    () => props.eventData,
    async (newVal, oldVal) => {
        if (newVal !== oldVal) {
            await fetchCorrectionData();
            console.log("Updated dataList:", dataList.value);
        }
    },
    {
        immediate: true,
        deep: true
    }
);
</script>

<template>
    <h4>事件详情</h4>
    <el-divider />
    <div class="detail_box">
        <div>
            <p>标题：{{ eventData.eventName }}</p>
            <p>任务：{{ eventData.person }}</p>
            <p>角色：{{ eventData.role }}</p>
            <p>组织：{{ eventData.organization }}</p>
            <p>时间：{{ eventData.time }}</p>
            <p>地点：{{ eventData.place }}</p>
            <p>行动：{{ eventData.action }}</p>
            <p>相关机构：{{ eventData.organizations }}</p>
        </div>
    </div>

    <div>
        <h4>基于语义的事件数据动态发现</h4>
        <el-divider />
        <div v-loading="loading" style="margin-top: 20px;">
            <el-table :data="dataList" style="width: 100%;" :header-cell-style="{ 'text-align': 'center' }"
                :cell-style="{ 'text-align': 'center' }">
                <el-table-column prop="title" label="标题" :min-width="25"></el-table-column>
                <el-table-column prop="keyword" label="关键词" :min-width="25">
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
                <el-table-column label="操作" :min-width="25">
                    <template #default="{ row }">
                        <el-button @click="handleCrawl(row.url, row.keyword)" type="success" size="mini">
                            爬取
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>
    </div>
</template>

<style scoped>
.el-divider {
    margin-top: 6px;
}

.detail_box {
    padding-left: 12px;
    height: 45vh;
    overflow-y: auto;
    border-radius: 5px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table_container {
    height: 30vh;
    overflow-y: auto;
}
</style>
