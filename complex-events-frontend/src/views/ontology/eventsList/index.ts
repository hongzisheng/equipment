import Rule from '@/views/ontology/eventsList/correlationMethods/rule/index.vue'
import TablesStructure from '@/views/ontology/eventsList/correlationMethods/tablesStructureDisplay/index.vue'
import GraphStructure from '@/views/ontology/eventsList/correlationMethods/subGraphDisplay/index.vue'
import { markRaw } from 'vue'

export const methodsList = [
  {
    name: '事件信息规则推理',
    value: 'rule',
    component: markRaw(Rule),
  },
  {
    name: '事件信息图结构推理',
    value: 'graph',
    component: markRaw(GraphStructure),
  },
  {
    name: '事件信息神经网络推理',
    value: 'neural',
    component: markRaw(TablesStructure),
  },
]
