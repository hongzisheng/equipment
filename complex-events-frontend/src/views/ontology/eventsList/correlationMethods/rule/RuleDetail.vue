<script setup lang="ts">
import InsertButton from '@/views/ontology/eventsList/correlationMethods/rule/InsertButton.vue'
import { onMounted, reactive, watch } from 'vue'
import associateApi from '@/api/associateApi'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import { AssociateRule, execute_rule } from '@/views/ontology/eventsList/correlationMethods/rule/index'

// 表单数据
const ruleForm = reactive({
  title: '',
  details: '',
})

const props = defineProps<{
  currentRule: AssociateRule
}>()

onMounted(() => {
  ruleForm.title = props.currentRule.rule_title
  ruleForm.details = props.currentRule.rule_detail
})

const emits = defineEmits<{
  saveSuccess: [string]
}>()

function saveRule() {
  const updateOne: AssociateRule = {
    rule_title: ruleForm.title,
    rule_detail: ruleForm.details,
    rule_type: '自然语言描述',
  }
  associateApi
    .addOrUpdateRule(updateOne)
    .then((res) => {
      if (res.code === 20000) {
        ElMessage.success('保存成功')
        emits('saveSuccess', ruleForm.title)
      } else {
        ElMessage.error('保存失败')
      }
    })
    .catch((e) => {
      ElMessage.error('保存失败' + e)
    })
}
</script>
<template>
  <div class="container">
    <h2>{{ruleForm.title}}</h2>

    <el-form label-width="150px">
      <el-form-item label="规则名称" required>
        <el-input v-model="ruleForm.title" placeholder="请输入规则名称" />
      </el-form-item>

      <el-form-item class="detail-item" required>
        <template #label>
          <div class="detail-item-label">
            <span>自然语言</span>
            <span>规则描述</span>
          </div>
        </template>
        <div class="input-container">
          <el-input
            class="detail-input"
            v-model="ruleForm.details"
            type="textarea"
            :rows="3"
            placeholder="例如：事件A发生的事件发生在事件B之后，则AB两事件具有时间上的先后关系"
          />
          <InsertButton
            class="detail-input-insert-button"
            @selectedChanged="(n) => (ruleForm.details += `【${n}】`)"
          />
        </div>
      </el-form-item>
      <el-form-item>
        <div class="button-item">
          <el-button plain type="primary" @click="saveRule"> 保存 </el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<style lang="scss" scoped>
.container {
  height: 100%;
  width: 50%;
  margin: 0 auto;

  h2 {
    // 居中
    text-align: center;
  }

  .button-item {
    display: flex;
    justify-content: flex-end;
    width: 100%;
  }

  .detail-item {
    display: flex;
    width: 100%;

    &-label {
      display: flex;
      flex-direction: column;
      font-weight: bold;
    }

    .input-container {
      display: flex;
      justify-content: space-between;
      width: 100%;

      .detail-input {
        flex: 1; // 占据剩余空间
      }

      .detail-input-insert-button {
        margin-left: 2vw;
        width: 20%;
        flex-shrink: 0; // 防止收缩
      }
    }
  }
}
</style>
