import TablesStructure from '@/views/ontology/eventsList/correlationMethods/tablesStructureDisplay/index.vue'
import { markRaw } from 'vue'

export const methodsList = [
  {
    name: '事件信息神经网络推理',
    value: 'neural',
    component: markRaw(TablesStructure),
  },
]
