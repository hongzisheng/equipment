import { OntologySystemData } from '@/views/ontology/ontologySystem'

export interface Person {
  personName: string
  role: string
  organization: string
}

export interface ExtractResultAction {
  actionName: string
  relatedOrganization: string
  relatedPerson: string
  relatedPlace: string
}

export interface ExtractResult {
  // 事件名称
  eventName: string
  // 事件类型
  eventType: string
  // 事件关键词（话题的语义扩充）
  keywords: string
  // 触发词 (事件的触发词)
  triggerWords: string
  // 对应的新闻报道id
  id: string
  // 组织数组（来源于相关人物）
  organization?: string[]
  // 组织字符串
  organizations: string
  // 人物数组
  person: Person[]
  // 地点字符串
  places: string
  time: string
  actions: ExtractResultAction[]
}

/**
 * 把提取出的结果格式化成表格能够展示的格式
 * @param extractResult 待格式化的对象(类型来源于数据库)
 * @returns 表格展示对象
 */
export function formattedExtractResult(extractResult: ExtractResult): OntologySystemData {
  return {
    eventName: extractResult?.eventName??'',
    eventType: extractResult?.eventType??'',
    keywords: extractResult?.keywords??'',
    triggerWords: extractResult?.triggerWords??'',
    person: extractResult?.person.map((item) => item.personName).join(',\n')??"",
    role: extractResult?.person.map((item) => item.role).join(',\n')??'',
    organization: extractResult?.person.map((item) => item.organization).join(',\n')??'',
    time: extractResult?.time??'',
    place: extractResult?.places??'',
    action: extractResult?.actions.map((item) => item.actionName).join(',\n')??'',
    organizations: extractResult?.organizations??'',
    reportId: extractResult?.id??'',
  }
}

/**
 * 实时输出流
 * id作为tab的标题内容
 * content作为tab的内容
 */
export interface OutputStream{
  id:string
  content:string
}
