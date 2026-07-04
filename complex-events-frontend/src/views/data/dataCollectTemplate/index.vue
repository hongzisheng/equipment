<template>
  <el-card class="template-card">
    <div class="title">
      <el-text tag="b">动态数据采集模板自动构建</el-text>
    </div>

    <div v-loading.fullscreen.lock="loading" class="form-wrapper">
      <el-form label-width="20%" size="medium" class="template-form">
        <el-form-item label="事件描述 / 示例网址" required>
          <el-input
            type="textarea"
            v-model="eventDescribeOrSample"
            :rows="4"
            placeholder="请输入事件描述或者示例网址"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleGenerate"
            :loading="loading"
            class="action-btn"
          >
            生成模板
          </el-button>
        </el-form-item>

        <el-form-item label="模板名">
          <el-input v-model="template.templateTitle" placeholder="为模板取一个名称" />
        </el-form-item>

        <el-form-item label="生成的模板内容">
          <el-input
            type="textarea"
            v-model="template.collectTemplate"
            :rows="8"
            placeholder="生成结果将显示在这里"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            @click="handleSave"
            :disabled="!template.collectTemplate"
            class="action-btn"
          >
            保存模板
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </el-card>
</template>

<script>
import dataApi from '@/api/dataApi'

export default {
  name: 'DataCollectTemplate',
  data() {
    return {
      eventDescribeOrSample: '',
      template: {
        collectTemplate: '',
        templateTitle: '',
      },
      loading: false,
    }
  },
  methods: {
    async handleGenerate() {
      const input = this.eventDescribeOrSample
      if (!input || !input.trim()) {
        this.$message.warning('请输入事件描述或示例网址')
        return
      }
      this.loading = true
      try {
        this.template.collectTemplate = ''
        const res = await dataApi.postDataCollectTemplate(input)
        this.template.collectTemplate = res.data.template
      } catch (err) {
        console.error('生成失败', err)
        this.$message.error('生成失败，请重试')
      } finally {
        this.loading = false
      }
    },
    handleSave() {
      const title = this.template.templateTitle
      if (!title || !title.trim()) {
        this.$message.warning('请输入模板名称')
        return
      }
      this.loading = true
      try {
        dataApi.postConfirmTemplate(this.template)
        this.$message.success('保存成功')
      } catch (err) {
        console.error('保存失败', err)
        this.$message.error('保存失败，请重试')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped lang="scss">
.template-card {
  width: 95%;
  max-width: 1200px;
  margin: 3vh auto;
  padding: 2%;
  min-height: 85vh;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  background: #fff;

  .title {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 2%;
    text-align: center;

    b {
      font-size: 2.2em;
      color: #333;
      letter-spacing: 1px;
    }
  }
}

.form-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
}

.template-form {
  width: 90%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;

  .el-form-item {
    margin-bottom: 1rem;
  }

  .el-input textarea {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    resize: vertical;
  }

  .action-btn {
    width: 40%;
    max-width: 200px;
    align-self: center;
    font-weight: 500;
    letter-spacing: 0.5px;
    border-radius: 12px;
  }
}

@media (max-width: 768px) {
  .template-form {
    width: 95%;
    label {
      width: 30% !important;
    }
    .action-btn {
      width: 80%;
      max-width: none;
    }
  }
}
</style>
