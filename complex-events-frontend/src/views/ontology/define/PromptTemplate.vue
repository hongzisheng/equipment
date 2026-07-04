<script>
/**
 * 选择不同的提示词模板：仅展示与selectedOntologyItem匹配的分类下的模板
 */

import { useOntologyStore } from '@/stores/ontologyStore'
import { ref, watch, onMounted } from 'vue'


export default {
  name: 'PromptTemplate',
  props: {
    selectedOntologyItem: {
      type: String,
      default: '',
      required: false
    }
  },
  computed: {
    filteredTemplates() {
      const targetCategory = this.options.find(
        category => category.label === this.selectedOntologyItem
      );

      return targetCategory ? targetCategory.promptList || [] : [];
    }
  },
  data() {
    return {
      options: [],
      selectedTemplate: '', // 存储选中模板的key
      // 错误2：Pinia未初始化实例（原直接用函数，改为先定义实例变量）
      ontologyStore: null,
      currentPrompt: '', // 存储当前选中模板的prompt内容
      loading: false,
      dialogVisible: false,
      newTemplateName: '', // 新增模板的名称（对应name字段）
      newTemplateKey: '', // 新增模板的键（对应key字段，需唯一）
      newTemplatePrompt: '' // 新增模板的提示词内容（对应prompt字段）
    }
  },
  watch: {
    // 监听本体切换，自动选中第一个模板
    selectedOntologyItem(newVal) {
      console.log('PromptTemplate 监听的新本体值：', newVal);
      // 确保模板数据已加载
      if (this.filteredTemplates.length > 0) {
        this.selectedTemplate = this.filteredTemplates[0].key;
        this.currentPrompt = this.filteredTemplates[0].prompt;
      } else {
        this.selectedTemplate = '';
        this.currentPrompt = '';
      }
    },
    // 监听模板列表变化，自动选中第一个（如新增模板后）
    filteredTemplates(newTemplates) {
      if (newTemplates.length > 0 && !newTemplates.some(t => t.key === this.selectedTemplate)) {
        this.selectedTemplate = newTemplates[0].key;
        this.currentPrompt = newTemplates[0].prompt;
      }
    }
  },
  mounted() {
    this.ontologyStore = useOntologyStore();
    this.fetchOntologyConfigs();
  },
  methods: {
    /**
     * 从后端获取本体模板数据
     */
    async fetchOntologyConfigs() {
      try {
        await this.ontologyStore.initData();
        this.options = [...this.ontologyStore.ontologyPrompt];
        // console.log('PromptTemplate 获取的本体模板数据:', this.options);
      } catch (error) {
        console.error('获取本体配置数据失败:', error);
        this.options = [];
      } finally {
        this.loading = false;
      }
    },

    /**
     * 切换模板时更新提示词内容
     */
    handleTemplateChange(templateKey) {
      const selected = this.filteredTemplates.find(tpl => tpl.key === templateKey);
      if (selected) {
        this.currentPrompt = selected.prompt;
      }
    },

    handlePromptChange() {
      if (!this.selectedTemplate || !this.selectedOntologyItem) return;

      const targetCategory = this.options.find(
        category => category.label === this.selectedOntologyItem
      );

      if (targetCategory && targetCategory.promptList && targetCategory.promptList.length) {
        const targetTemplate = targetCategory.promptList.find(
          tpl => tpl.key === this.selectedTemplate
        );

        if (targetTemplate) {
          if (targetTemplate.prompt !== this.currentPrompt) {
            targetTemplate.prompt = this.currentPrompt;
            this.ontologyStore.updateOntologyPromptOptions(this.options);
            console.log(`模板 ${this.selectedTemplate} 内容已更新`);
            this.$message.success('提示词内容已自动保存');
          }
        }
      }
    },

    handleAddStrategy() {
      this.newTemplateName = '';
      this.newTemplateKey = '';
      this.newTemplatePrompt = '';
      this.dialogVisible = true;
    },

    /**
     * 确认新增提示词模板
     */
    handleAddConfirm() {
      if (!this.selectedOntologyItem) {
        this.$message.warning('请先在本体体系中选择一个本体项（如“事件”“时间”）');
        return;
      }
      if (!this.newTemplateName || !this.newTemplateKey || !this.newTemplatePrompt) {
        this.$message.warning('模板名称、模板键、提示词内容均为必填项，请补充完整！');
        return;
      }
      this.options = [...this.ontologyStore.ontologyPrompt];
      const targetCategory = this.options.find(
        category => category.label === this.selectedOntologyItem
      );
      if (!targetCategory) {
        this.$message.error(`未找到“${this.selectedOntologyItem}”对应的本体分类，请刷新重试`);
        return;
      }

      // 3. 校验模板键唯一性
      const isKeyRepeat = targetCategory.promptList?.some(
        tpl => tpl.key === this.newTemplateKey
      ) || false;
      if (isKeyRepeat) {
        this.$message.warning(`当前本体下已存在“${this.newTemplateKey}”的模板键，请更换唯一键！`);
        return;
      }

      if (!targetCategory.promptList) {
        targetCategory.promptList = [];
      }
      targetCategory.promptList.push({
        name: this.newTemplateName,
        key: this.newTemplateKey,
        prompt: this.newTemplatePrompt
      });

      this.ontologyStore.updateOntologyPromptOptions(this.options);

      this.dialogVisible = false;
      this.$message.success('提示词模板新增成功！');

      this.selectedTemplate = this.newTemplateKey;
      this.currentPrompt = this.newTemplatePrompt;
    }
  }
};
</script>

<template>
  <div class="title">
    <span>提示词策略（当前本体：{{ selectedOntologyItem || '未选择' }}）</span>
    <el-button type="text" size="small" v-if="loading">加载中...</el-button>
    <el-button @click="handleAddStrategy" type="primary" :disabled="loading">新增策略</el-button>
  </div>

  <el-dialog v-model="dialogVisible" title="新增提示词模板" width="50%" :close-on-click-modal="false">
    <el-form label-width="120px">
      <el-form-item label="模板名称" required>
        <el-input v-model="newTemplateName" placeholder="如：核心事件提取策略" maxlength="50" :disabled="loading" />
      </el-form-item>
      <el-form-item label="模板键" required>
        <el-input v-model="newTemplateKey" placeholder="如：1 或 event-core（需唯一）" maxlength="30" :disabled="loading" />
      </el-form-item>
      <el-form-item label="提示词内容" required>
        <el-input v-model="newTemplatePrompt" type="textarea" :rows="4" placeholder="请输入该模板对应的提示词内容"
          :disabled="loading" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false" :disabled="loading">取消</el-button>
      <el-button type="primary" @click="handleAddConfirm" :disabled="loading">确认新增</el-button>
    </template>
  </el-dialog>

  <el-card class="system-card">
    <el-skeleton v-if="loading" :rows="5" class="mb-4" />

    <div v-else-if="!selectedOntologyItem" class="empty-tip">
      请先在本体体系中选择一个本体项（如“事件”“时间”）
    </div>

    <div v-else-if="filteredTemplates.length === 0" class="empty-tip">
      未找到“{{ selectedOntologyItem }}”对应的提示词模板，请点击“新增策略”创建
    </div>

    <el-radio-group v-else v-model="selectedTemplate" class="ratio-group-container" @change="handleTemplateChange">
      <div class="radio-grid">
        <div v-for="(template, index) in filteredTemplates" :key="template.key" class="radio-item">
          <el-radio-button :label="template.key" size="large" class="custom-radio-btn">
            {{ template.name }}
          </el-radio-button>
        </div>
      </div>
    </el-radio-group>

    <el-row v-if="!loading && filteredTemplates.length > 0" class="text-display-row" style="margin-top: 10px;">
      <el-col :span="24">
        <el-input v-model="currentPrompt" :rows="6" class="prompt-input" type="textarea" placeholder="提示词内容"
          :disabled="loading" @blur="handlePromptChange" />
      </el-col>
    </el-row>
  </el-card>
</template>

<style lang="scss" scoped>
/* 样式完全不变，保留原结构 */
.title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-bottom: 10px;
  gap: 10px;
}

.system-card {
  margin-top: 20px;
  height: 75%;
  padding: 5px;
  box-sizing: border-box;
}

.empty-tip {
  text-align: center;
  padding: 40px 0;
  color: #666;
  background-color: #fafafa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.radio-item {
  width: 100%;
}

.ratio-group-container {
  width: 100%;
  height: 120px;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box;
}

.radio-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  align-items: flex-start;
  align-content: flex-start;
  width: 100%;
}

.radio-col {
  margin-bottom: 10px;
}

.prompt-input {
  width: 100%;
  resize: none;
  border-color: #e6e6e6;
}

.ratio-group-container::-webkit-scrollbar {
  width: 6px;
}

.ratio-group-container::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
}

.el-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.custom-radio-btn {
  width: 100% !important;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
</style>
