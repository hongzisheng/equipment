import request from '@/utils/request'
import { AssociateRule } from '@/views/ontology/eventsList/correlationMethods/rule/index'

export default {
  getAllRules() {
    return request({
      url: '/associate/allRules',
      method: 'get',
    })
  },
  addOrUpdateRule(rule: AssociateRule) {
    return request({
      url: '/associate/addOrUpdateRule',
      method: 'post',
      data: rule,
    })
  },
  commonPerson(mainReportId: string) {
    return request({
      url: '/associate/filterCommonPerson',
      method: 'get',
      params: { mainReportId },
    })
  },
  commonOrganization(mainReportId: string) {
    return request({
      url: '/associate/filterCommonOrganization',
      method: 'get',
      params: { mainReportId },
    })
  },
  commonPlace(mainReportId: string) {
    return request({
      url: '/associate/filterCommonPlace',
      method: 'get',
      params: { mainReportId },
    })
  },
  linkAllRelInGraph() {
    return request({
      url: '/associate/linkInGraph',
      method: 'get',
    })
  },
}
