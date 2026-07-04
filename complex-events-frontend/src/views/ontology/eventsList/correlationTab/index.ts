export interface Report {
  id: string
  title: string
  date: string
  link_url: string
  topic: string
  details: string
  resources: string[]
  // 本体抽取配置，只在前端展示的时候会使用到
  config?: string
}

export interface EventLink {
  // 主事件
  mainEvent: string
  // 关联事件
  relatedEvent: string
  relation: {
    // 后事件
    after: string
    // 先事件
    prior: string
    // 关系类型
    type: string
    // 置信度
    confidenceDegree: number
    // 关系原因
    reason: string
  }
  // 关联事件的详情，是一个报告对象
  relevantEventDetails: Report
}

/**
 * 根据关联类型进行聚合
 * @param eventLinks 待聚合的列表
 * @returns 返回一个字典，key是关系类型，value是该关系类型的事件列表
 */
export function typeGroupReduce(eventLinks: EventLink[]) {
  return eventLinks.reduce((acc, item) => {
    const type = item.relation.type
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(item)
    return acc
  }, {})
}

/**
 * 根据包含的规则。得到规则输入的提示词
 * @param rules 规则包含
 * @param containsRule
 * @param rulesContent
 */
export function getRulesPrompt(
  rules: string[],
  containsRule: boolean = false,
  rulesContent: string = '',
) {
  const res = []
  if (rules.includes('graph')) {
    const graphRulePrompt =
      '基于图结构：这两个事件之间可能存在相同人物，相同地点，相同组织等在图结构上相似的地方'
    res.push(graphRulePrompt)
  }
  if (rules.includes('embedding')) {
    const embeddingRulePrompt =
      '基于嵌入：这两个事件之间可能存在相似的语义，相似的语义表示两个事件之间可能存在相似的语义'
    res.push(embeddingRulePrompt)
  }
  if (containsRule) {
    res.push(rulesContent)
  }
  return res.join(',\n')
}
