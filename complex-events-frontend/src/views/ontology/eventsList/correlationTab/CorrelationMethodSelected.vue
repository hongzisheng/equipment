<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { methodsList } from '@/views/ontology/eventsList/index.js'
import { TopLeft } from '@element-plus/icons-vue'

const NEURAL = 'neural'
const radioSelectedMethods = ref('')
watch(radioSelectedMethods, (newVal) => {
  if (newVal != '') {
    singleOrMixed.value = true
    if (newVal != NEURAL) {
      checkedMethods.value.push(newVal)
    }
  }
})
const checkedMethods = ref([NEURAL])
const ruleContent = ref('')
defineExpose({
  checkedMethods,
  ruleContent,
})

watch(checkedMethods, () => {
  if (!checkedMethods.value.includes(NEURAL)) {
    // 勾选基于规则的时候没有勾选神经网络
    checkedMethods.value.push(NEURAL)
  }
})

const unclickedMix = ref(true)
const singleOrMixed = ref(true)
watch(singleOrMixed, (newVal) => {
  if (!newVal) {
    // 关闭单选模式的时候,清空单选方法选择，防止干扰
    radioSelectedMethods.value = ''
  } else {
    // 关闭的时候打开混合推理的罩子遮住
    unclickedMix.value = true
  }
})
const mixedOrSingle = computed({
  get() {
    return !singleOrMixed.value
  },
  set(newValue) {
    singleOrMixed.value = !newValue
  },
})
</script>

<template>
  <el-card class="card-container">
    <div class="single">
      <div class="title">
        <el-text tag="b" size="large">事件关联信息智能推理</el-text>
        <el-switch v-model="singleOrMixed" />
        <el-text>事件信息推理准确率≥89%</el-text>
      </div>
      <el-radio-group v-model="radioSelectedMethods" class="row-radio-group">
        <el-tooltip
          effect="light"
          :disabled="radioSelectedMethods != 'rule' || method.value != 'rule'"
          :key="`${method.value}-${radioSelectedMethods}`"
          v-for="method in methodsList"
        >
          <el-radio-button :key="method.value" :label="method.value" class="radio-button-flex">
            {{ method.name }}
          </el-radio-button>
          <template #content>
            <el-form-item label="规则内容">
              <el-input v-model="ruleContent" />
            </el-form-item>
          </template>
        </el-tooltip>
      </el-radio-group>
    </div>

    <div class="mixed">
      <div class="title">
        <el-text tag="b" size="large"> 事件信息混合推理</el-text>
        <el-switch v-model="mixedOrSingle" />
      </div>
      <div class="row">
        <Transition name="fade" mode="out-in">
          <el-button
            class="row-button"
            v-if="unclickedMix"
            @click="
              () => {
                mixedOrSingle = true
                unclickedMix = !unclickedMix
              }
            "
          >
            混合规则推理
          </el-button>
          <el-checkbox-group v-model="checkedMethods" v-else class="checkbox-group-flex">
            <div class="checkbox-container">
              <div class="checkbox-item" v-for="method in methodsList" :key="method.value">
                <el-tooltip
                  effect="light"
                  :key="`${method.value}-${checkedMethods.includes('rule')}`"
                  :disabled="method.value !== 'rule' || !checkedMethods.includes('rule')"
                >
                  <el-checkbox-button :value="method.value">{{ method.name }}</el-checkbox-button>
                  <template #content>
                    <el-form-item label="规则内容">
                      <el-input v-model="ruleContent" />
                    </el-form-item>
                  </template>
                </el-tooltip>
              </div>
              <div class="checkbox-item-end">
                <el-button text @click="unclickedMix = !unclickedMix">
                  <el-icon>
                    <TopLeft />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </el-checkbox-group>
        </Transition>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.card-container {
  height: 100%;
  width: 100%;

  .single {
    width: 100%;
    margin-bottom: 20px;

    .row-radio-group {
      width: 100%;
      display: flex;

      .radio-button-flex {
        flex: 1;

        :deep(.el-radio-button__inner) {
          width: 100%;
          text-align: center;
        }
      }
    }
  }

  .mixed {
    width: 100%;

    .row {
      width: 100%;

      .row-button {
        width: 100%;
      }

      .checkbox-group-flex {
        width: 100%;

        .checkbox-container {
          display: flex;
          width: 100%;

          .checkbox-item {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;

            :deep(.el-checkbox-button) {
              width: 100%;

              .el-checkbox-button__inner {
                width: 90%;
              }
            }
          }

          .checkbox-item-end {
            flex: none;
          }
        }
      }
    }
  }
}
</style>
