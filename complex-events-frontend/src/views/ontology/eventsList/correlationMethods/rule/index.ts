// 来自于mongodb数据存储结构
import { NOT_IMPL_WARN } from '@/views/ontology'
import associateApi from '@/api/associateApi'
import { ElMessage } from 'element-plus'

export interface AssociateRule {
  rule_title: string
  rule_type?: string
  rule_detail?: string
}

