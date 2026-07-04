<template>
  <el-card class="card">
    <div class="card-container">
      <div class="title">
        <span>事件的演化图构建</span>
      </div>
      <div class="mind-container" id="map" />
      <div class="node-detail">
        <p v-for="node in selectedNodes">{{ node.topic }}</p>
      </div>
      <div class="events-correlation">事件关联准确率≥83.6% 事件关系识别准确率≥87.35%</div>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
// https://github.com/SSShooter/mind-elixir-core
import MindElixir, { MindElixirData, MindElixirInstance, NodeObj } from 'mind-elixir'
import { onMounted, reactive, ref, watch } from 'vue'
import 'mind-elixir/style.css'
import { getLabelByProp } from '@/views/ontology/ontologySystem'
import { EventLink } from '@/views/ontology/eventsList/correlationTab/index'

const data = reactive<MindElixirData | null>(MindElixir.new('new topic'))

onMounted(() => {
  init()
})
// 方便外部调用实例
let mind: MindElixirInstance
const init = () => {
  /**
   * 创建一个mind-elixir实例
   */
  mind = new MindElixir({
    el: '#map', // 或 HTMLDivElement
    direction: MindElixir.RIGHT,
    draggable: true, // 默认 true
    toolBar: true, // 默认 true
    // nodeMenu: true, // 默认 true
    keypress: true, // 默认 true
    locale: 'zh_CN', // [zh_CN,zh_TW,en,ja,pt,ru] 等待 PRs
    overflowHidden: false, // 默认 false
    // mainLinkStyle: 2, // [1,2] 默认 1
    mouseSelectionButton: 0, // 0 为左键，2 为右键，默认 0
    contextMenu: {
      focus: false,
      link: false,
      extend: [
        {
          name: '自定义按钮',
          onclick: () => {
            alert('扩展菜单')
          },
        },
        {
          name: '节点编辑2',
          onclick: (e) => {
            console.log(e)
            alert('扩展菜单')
          },
        },
      ],
    },
  })

  mind.init(data)
  // 使用默认主题
  mind.changeTheme(MindElixir.THEME)
  mind.bus.addListener('selectNodes', (nodes) => {
    selectedNodes.value = nodes
  })
}

const props = withDefaults(defineProps<{
  row: Object
  mainEvent: string
}>(), {
  row: null,
  mainEvent: ''
})

// 根据新数据刷新 mind
const refresh = () => {
  if (!props.row || !props.mainEvent)
    return
  console.log('refresh', props.row)
  data.nodeData.topic = props.mainEvent
  // data.topic = MindElixir.new(props.mainEvent)
  // 清空孩子
  data.nodeData.children = []
  const mainID = data.nodeData.id
  let i = 0
  // 遍历ROW的key，value
  for (const key in props.row) {
    const node: NodeObj = {
      topic: key,
      id: i++ + 'id',
      // 默认折叠起来
      expanded: false,
      children: props.row[key].map((report: EventLink) => {
        return {
          topic: report.relevantEventDetails.title,
          children: [
            {
              id: i++ + 'childrenReportId',
              topic: report.relevantEventDetails.id,
            },
            {
              id: i++ + 'childrenLinkReason',
              topic: '原因：' + report.relation.reason,
              style: {
                // 节点样式
                // fontSize?: string
                // color?: string
                // background?: string
                fontWeight: 'bold',
              },
            },
            {
              id: i++ + 'confidence',
              topic: '可信度:' + report.relation.confidenceDegree,
              style: {
                fontWeight: 'bold',
              },
            },
          ],
          id: i++ + 'childrenId',
        }
      }),
    }
    // mind.addChild(MindElixir.E(mainID), node)
    data.nodeData.children.push(node)
  }
  mind.refresh(data)
  // 绘制完成之后居中显示
  mind.toCenter()
  console.log('refresh_', data)
}
watch(props, () => refresh(), { deep: true })
defineExpose({
  refresh,
})
const node = ref<string>('')
const selectedNodes = ref<NodeObj[]>([])
watch(selectedNodes, (newVal) => {
  console.log('watch', newVal)
})

const handleClicked = () => {
  // mind.selectNode(data.nodeData)
  // console.log(MindElixir.E(node.value))
}
const add: string[] = ['1', '2']
</script>

<style lang="scss" scoped>
.card {
  --border-radius: 16px;
  height: 100%;
  border-radius: var(--border-radius);

  .card-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .title {
      width: 100%;
      display: flex;
      justify-content: center;
      font-size: 2em;
      font-weight: bold;
      background: #4c4f69;
      color: white;
      border-top-left-radius: var(--border-radius);
      border-top-right-radius: var(--border-radius);
    }

    .mind-container {
      width: 100%;
      height: 90%;

      :deep(.map-container) {
        border-bottom-left-radius: var(--border-radius);
        border-bottom-right-radius: var(--border-radius);
      }
    }

    .node-detail {
      height: 10%;
    }

    .events-correlation {
      position: absolute;
      right: 4%;
      bottom: 1%;
    }
  }

}
</style>
