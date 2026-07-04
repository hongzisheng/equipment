import { ElMessage } from 'element-plus'
import dataApi from '@/api/dataApi.js'
import { getAllRelations, useOntologyStore } from '@/stores/ontologyStore'

interface PromptItem {
  key: string
  name: string
  prompt: string
}

interface OntologySystemOption {
  label: string
  value: string
  field?: string
  promptList?: PromptItem[]
  // 节点类型
  type?: string
  // 映射到表格的时候的属性名
  prop?: string
  // 是否固定列
  fixed?: boolean
}

let ontologyOptionsCache: OntologySystemOption[] = []

export interface OntologySystemData {
  eventName: string
  eventType: string
  keywords:string
  triggerWords:string
  person: string
  role: string
  time: string
  place: string
  action: string
  // 人物相关的组织
  organization: string
  // 事件相关的组织
  organizations: string
  // 对应报告的id
  reportId: string
}

const options: OntologySystemOption[] = [
  {
    value: '事件',
    label: '事件',
    type: 'Event',
    prop: 'eventName',
    fixed: true,
  },
  {
    value: '人物',
    label: '人物',
    type: 'Person',
    prop: 'person',
  },
  {
    value: '角色',
    label: '角色',
    type: 'Role',
    prop: 'role',
  },
  {
    value: '行动',
    label: '行动',
    type: 'Action',
    prop: 'action',
  },
  {
    value: '时间',
    label: '时间',
    type: 'Time',
    prop: 'time',
  },
  {
    value: '地点',
    label: '地点',
    type: 'Place',
    prop: 'place',
  },
  {
    value: '组织',
    label: '组织',
    type: 'Organization',
    prop: 'organization',
  },
  {
    value: '新闻报道ID',
    label: '新闻报道ID',
    type: 'Report',
    prop: 'reportId',
  },
]
const store = useOntologyStore()

export function getOntologySystemOptions() {
  return store.getAllOntologyObject
}

export function getOntologyOptionsCache(): OntologySystemOption[] {
  return [...ontologyOptionsCache]
}

export function getLabelByProp(prop: string) {
  return getOntologySystemOptions().find((item) => item.prop === prop)?.label
}

export function getIdByLable(label:string){
  return getOntologySystemOptions().find((item) => item.label === label)?.prop
}

export interface Relation {
  source: string
  target: string
  type: string
}

export async function getRelation(
  sourceField: string,
  targetField: string,
): Promise<Relation | null> {
  return getAllRelations()
    .then((res) => {
      return res.find((item) => item.source === sourceField && item.target === targetField) || null
    })
    .catch(() => {
      return null
    })
}

let relationsCache: Relation[] = []

export function searchRelations(fieldName: string): Promise<Relation[]> {
  return getAllRelations().then((allRelations) => {
    const matchedRelations = allRelations.filter(
      (item) => item.source === fieldName || item.target === fieldName,
    )
    console.log(`✅ 筛选字段 ${fieldName} 的关系数据:', matchedRelations`)
    return matchedRelations
  })
}
