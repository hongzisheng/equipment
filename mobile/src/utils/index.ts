import {getNextStatus, getNextStatusLabel, getStatusLabel, getStatusStyle, STATUS_SEQUENCE} from "@/utils/statusUtil";

export {
  getNextStatusLabel,
  getNextStatus,
  getStatusLabel,
  getStatusStyle,
  STATUS_SEQUENCE,
}
// 类型用 type 导出，避免产生运行时 import
export type {WorkOrderProcess, WorkOrder} from '@/utils/type'
export type { StatusStyle } from '@/utils/statusUtil'

export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
